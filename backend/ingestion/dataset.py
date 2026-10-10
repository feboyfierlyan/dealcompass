"""Load the source tables with typed values and traceable original rows.

Decision CSV is canonical; the accompanying XLSX is only a copy, not a table.
Snapshot filtering is deliberately left to consumers of this dataset.
"""

import csv
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[2] / 'dataset_kasirnusa'
SNAPSHOT_DATE = date(2026, 10, 1)

# Key order is also source order for inventory and for the individual tables.
TABLE_KEYS: dict[str, tuple[str, ...]] = {
    'crm_accounts.csv': ('account_id',),
    'crm_contacts.csv': ('contact_id',),
    'contact_employment_history.csv': ('contact_id', 'organisasi', 'mulai'),
    'crm_deals.csv': ('deal_id',),
    'employees.csv': ('employee_id',),
    'interactions.jsonl': ('interaction_id',),
    'outlets.csv': ('outlet_id',),
    'product_usage_daily.csv': ('tanggal', 'outlet_id'),
    'feature_usage_monthly.csv': ('bulan', 'account_id', 'feature_id'),
    'support_tickets.csv': ('ticket_id',),
    'bugs.csv': ('bug_id',),
    'releases.csv': ('versi',),
    'features.csv': ('feature_id',),
    'contracts_billing.csv': ('contract_id',),
    'decision_log.csv': ('decision_id',),
}

INTEGER_COLUMNS = frozenset({
    'jumlah_outlet', 'nps_terakhir', 'outlet', 'nilai_tahunan',
    'jumlah_transaksi', 'transaksi_offline_tersinkron', 'pengguna_aktif',
    'outlet_kontrak', 'batas_outlet_paket', 'harga_per_outlet_bulan',
    'keterlambatan_bayar_12bln',
})
DATE_COLUMNS = frozenset({
    'tanggal', 'tanggal_rilis', 'tanggal_renewal', 'stage_sejak',
    'dibuat', 'diselesaikan', 'mulai', 'selesai',
})
DATE_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}\Z')
MONTH_PATTERN = re.compile(r'\d{4}-\d{2}\Z')
INTEGER_PATTERN = re.compile(r'[+-]?\d+\Z')


@dataclass(slots=True)
class SourceRecord:
    source_file: str
    source_id: str
    line: int
    raw: dict[str, str]
    values: dict[str, object]


@dataclass(slots=True)
class Dataset:
    tables: dict[str, list[SourceRecord]]
    by_id: dict[str, dict[str, SourceRecord]]
    columns: dict[str, list[str]]
    key_fields: dict[str, tuple[str, ...]]
    source_files: dict[str, str]

    def query(self, filename: str, **filters: object) -> list[SourceRecord]:
        return [record for record in self.tables[filename]
                if all(record.values[field] == value for field, value in filters.items())]

    def inventory(self) -> list[dict]:
        return [
            {'source_file': self.source_files[filename],
             'count': len(rows), 'columns': self.columns[filename],
             'key_fields': list(self.key_fields[filename])}
            for filename, rows in self.tables.items()
        ]


def normalize_row(raw: dict[str, str], filename: str = '', line: int = 0) -> dict[str, object]:
    """Normalize one source row without modifying its original string values."""
    values: dict[str, object] = {}
    for column, original in raw.items():
        if not isinstance(original, str):
            raise ValueError(f'{filename}:{line}: {column}: expected string, got {original!r}')
        value = original.strip()
        if not value:
            values[column] = None
        elif column in ('email', 'dari', 'ke'):
            values[column] = value.lower()
        elif column.endswith('_id') or column in {'account_id_saat_ini', 'diminta_oleh', 'diputuskan_oleh', 'fitur_dijanjikan'}:
            values[column] = value.upper()
        elif column == 'peserta':
            values[column] = ';'.join(part.strip().upper() for part in value.split(';') if part.strip())
        elif column in DATE_COLUMNS:
            try:
                if not DATE_PATTERN.fullmatch(value):
                    raise ValueError('expected YYYY-MM-DD')
                values[column] = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f'{filename}:{line}: {column}: invalid date {original!r}') from exc
        elif column == 'bulan':
            try:
                if not MONTH_PATTERN.fullmatch(value):
                    raise ValueError('expected YYYY-MM')
                date.fromisoformat(f'{value}-01')
            except ValueError as exc:
                raise ValueError(f'{filename}:{line}: {column}: invalid month {original!r}') from exc
            values[column] = value
        elif column in INTEGER_COLUMNS and not (column == 'batas_outlet_paket' and value == 'tanpa batas'):
            if not INTEGER_PATTERN.fullmatch(value):
                raise ValueError(f'{filename}:{line}: {column}: invalid integer {original!r}')
            values[column] = int(value)
        elif column == 'diskon_pct':
            try:
                values[column] = Decimal(value)
                if not values[column].is_finite():
                    raise InvalidOperation
            except InvalidOperation as exc:
                raise ValueError(f'{filename}:{line}: {column}: invalid percentage {original!r}') from exc
        else:
            values[column] = value
    return values


def _source_file(data_dir: Path, filename: str) -> str:
    root = Path(__file__).resolve().parents[2]
    try:
        directory = data_dir.resolve().relative_to(root).as_posix()
    except ValueError:
        directory = data_dir.name
    return f'{directory}/{filename}'


def load_dataset(data_dir: Path = DATA_DIR) -> Dataset:
    """Load every CSV/JSONL row, raising with filename and line on invalid data."""
    tables: dict[str, list[SourceRecord]] = {}
    by_id: dict[str, dict[str, SourceRecord]] = {}
    columns: dict[str, list[str]] = {}
    source_files: dict[str, str] = {}

    for filename, key_fields in TABLE_KEYS.items():
        path = data_dir / filename
        source_file = _source_file(data_dir, filename)
        records: list[SourceRecord] = []
        index: dict[str, SourceRecord] = {}
        with path.open(encoding='utf-8-sig', newline='') as stream:
            if filename.endswith('.jsonl'):
                headers: list[str] = []
                def source_rows():
                    for line, text in enumerate(stream, start=1):
                        try:
                            row = json.loads(text)
                        except json.JSONDecodeError as exc:
                            raise ValueError(f'{source_file}:{line}: invalid JSON: {exc.msg}') from exc
                        if not isinstance(row, dict):
                            raise ValueError(f'{source_file}:{line}: expected JSON object')
                        if not headers:
                            headers.extend(row)
                        elif set(row) != set(headers):
                            raise ValueError(f'{source_file}:{line}: JSON fields differ from first row')
                        yield line, row
            else:
                reader = csv.reader(stream, strict=True)
                try:
                    headers = next(reader)
                except StopIteration as exc:
                    raise ValueError(f'{source_file}:1: missing CSV header') from exc
                except csv.Error as exc:
                    raise ValueError(f'{source_file}:1: invalid CSV header: {exc}') from exc
                if len(set(headers)) != len(headers) or not headers or any(not field for field in headers):
                    raise ValueError(f'{source_file}:1: invalid CSV header')
                def source_rows():
                    while True:
                        line = reader.line_num + 1
                        try:
                            cells = next(reader)
                        except StopIteration:
                            break
                        except csv.Error as exc:
                            raise ValueError(f'{source_file}:{line}: invalid CSV: {exc}') from exc
                        if len(cells) != len(headers):
                            raise ValueError(f'{source_file}:{line}: malformed CSV row')
                        yield line, dict(zip(headers, cells))
            missing = set(key_fields) - set(headers) if filename.endswith('.csv') else set()
            if missing:
                raise ValueError(f'{source_file}:1: missing key columns {sorted(missing)}')
            for line, raw in source_rows():
                values = normalize_row(raw, source_file, line)
                try:
                    parts = [values[field] for field in key_fields]
                except KeyError as exc:
                    raise ValueError(f'{source_file}:{line}: missing key column {exc.args[0]}') from exc
                if any(part is None for part in parts):
                    raise ValueError(f'{source_file}:{line}: empty key {key_fields}')
                source_id = '|'.join(str(part.isoformat() if isinstance(part, date) else part) for part in parts)
                if source_id in index:
                    raise ValueError(f'{source_file}:{line}: duplicate key {source_id!r} (first at line {index[source_id].line})')
                record = SourceRecord(source_file, source_id, line, raw, values)
                records.append(record)
                index[source_id] = record
        tables[filename] = records
        by_id[filename] = index
        columns[filename] = headers
        source_files[filename] = source_file
    return Dataset(tables, by_id, columns, TABLE_KEYS, source_files)


@lru_cache(maxsize=8)
def _cached_dataset(path: Path) -> Dataset:
    """Process-wide source snapshot; call get_dataset.cache_clear() for fixtures."""
    return load_dataset(path)


def get_dataset() -> Dataset:
    from backend.ingestion.scope import data_path
    return _cached_dataset(data_path() or DATA_DIR)

get_dataset.cache_clear = _cached_dataset.cache_clear
