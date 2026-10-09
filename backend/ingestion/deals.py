"""Fondasi daftar deal asli. Bima memperluas ingest seluruh sumber."""
import csv
from datetime import date
from pathlib import Path
from backend.contracts import DealSummary

DATA_DIR = Path(__file__).resolve().parents[2] / 'dataset_kasirnusa'
SNAPSHOT_DATE = date(2026, 10, 1)

def list_deals() -> list[DealSummary]:
    with (DATA_DIR / 'crm_accounts.csv').open(encoding='utf-8-sig', newline='') as f:
        accounts = {r['account_id']: r for r in csv.DictReader(f)}
    with (DATA_DIR / 'crm_deals.csv').open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    return [DealSummary(
        deal_id=r['deal_id'], account_id=r['account_id'],
        account_name=accounts[r['account_id']]['nama'], stage=r['stage'],
        stage_age_days=(SNAPSHOT_DATE - date.fromisoformat(r['stage_sejak'])).days,
        annual_value=int(r['nilai_tahunan']), owner_id=r['owner_id'],
    ) for r in rows if r['status'] == 'Terbuka' and accounts[r['account_id']]['tipe'] == 'prospek']

