"""Bounded, isolated dataset imports. No archive extraction or original-data writes."""
import csv
import io
import json
import os
import re
import secrets
import shutil
import threading
import time
import zipfile
from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from backend.ingestion.dataset import DATA_DIR, TABLE_KEYS, load_dataset
from backend.ingestion.scope import workspace

router = APIRouter()
MAX_BYTES = 2_000_000
TTL = 24 * 3600
_lock = threading.Lock()


def root():
    return Path(os.environ.get('DEALCOMPASS_UPLOAD_DIR', '.local/uploads')).resolve()


def schemas():
    out = {}
    for filename in TABLE_KEYS:
        with (DATA_DIR / filename).open(encoding='utf-8-sig') as f:
            out[filename] = list(json.loads(f.readline())) if filename.endswith('.jsonl') else next(csv.reader(f))
    return out


def template():
    return {'name': 'Northstar sales', 'snapshot_date': '2026-10-10', 'tables': {
        'crm_accounts.csv': [{'account_id': 'ACME01', 'nama': 'Northstar Retail', 'tipe': 'prospek', 'industri': 'Retail', 'jumlah_outlet': '8', 'account_owner_id': 'SELLER01', 'champion_contact_id': 'BUYER01'}],
        'employees.csv': [{'employee_id': 'SELLER01', 'nama': 'Alex Morgan', 'jabatan': 'Sales Executive', 'email': 'alex@example.com'}],
        'crm_contacts.csv': [{'contact_id': 'BUYER01', 'nama': 'Jamie Lee', 'email': 'jamie@example.com', 'account_id_saat_ini': 'ACME01', 'jabatan_saat_ini': 'Procurement Manager'}],
        'crm_deals.csv': [{'deal_id': 'OPP01', 'account_id': 'ACME01', 'tipe': 'baru', 'stage': 'Negosiasi', 'stage_sejak': '2026-10-01', 'dibuat': '2026-09-01', 'owner_id': 'SELLER01', 'outlet': '8', 'nilai_tahunan': '33600000', 'status': 'Terbuka'}],
        'interactions.jsonl': [{'interaction_id': 'CALL01', 'tanggal': '2026-10-08', 'tipe': 'email', 'account_id': 'ACME01', 'dari': 'jamie@example.com', 'ke': 'alex@example.com', 'peserta': 'BUYER01;SELLER01', 'subjek': 'Contract discussion', 'isi': 'Kami meminta diskon 15% sebelum tanda tangan kontrak. Belum ada persetujuan.'}],
    }}


def read_workspace(token):
    if not re.fullmatch(r'[a-f0-9]{48}', token or ''):
        raise HTTPException(404, 'Upload workspace not found. Return to the demo or upload again.')
    path = root() / token
    if not path.is_dir():
        raise HTTPException(404, 'Upload workspace expired. Upload your file again.')
    try:
        meta = json.loads((path / 'manifest.json').read_text())
    except (OSError, ValueError):
        raise HTTPException(404, 'Upload workspace unavailable. Upload your file again.') from None
    if time.time() - meta['created_at'] > TTL:
        raise HTTPException(404, 'Upload workspace expired. Upload your file again.')
    return {**meta, 'path': str(path)}


def parse_package(raw, is_zip):
    if not is_zip:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('Expected a JSON object. Download the example template.')
        return value
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        allowed = set(TABLE_KEYS) | {'manifest.json'}
        if len(members) > 16 or len({m.filename for m in members}) != len(members):
            raise ValueError('ZIP must contain unique CSV/JSONL files at its root and manifest.json.')
        if any(m.filename not in allowed or m.is_dir() for m in members):
            raise ValueError('Unsupported ZIP entry. Use the file names in the template; no folders.')
        if sum(m.file_size for m in members) > 8_000_000:
            raise ValueError('Uncompressed ZIP is too large (8 MB maximum).')
        if 'manifest.json' not in archive.namelist():
            raise ValueError('ZIP needs manifest.json with name and snapshot_date.')
        value = json.loads(archive.read('manifest.json'))
        tables = {}
        for m in members:
            if m.filename == 'manifest.json': continue
            text = archive.read(m).decode('utf-8-sig')
            tables[m.filename] = [json.loads(l) for l in text.splitlines() if l.strip()] if m.filename.endswith('.jsonl') else list(csv.DictReader(io.StringIO(text)))
        return {**value, 'tables': tables}


def import_package(raw, is_zip, allow_jev):
    selected = None
    try:
        payload = parse_package(raw, is_zip)
        when = date.fromisoformat(payload['snapshot_date'])
        name = payload.get('name', 'Uploaded workspace')
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60:
            raise ValueError('Workspace name must be 1–60 characters.')
        tables = payload['tables']; known = schemas()
        if not isinstance(tables, dict) or set(tables) - set(known):
            raise ValueError('Unsupported table. Download the JSON template for accepted file names.')
        if not all(isinstance(rows, list) for rows in tables.values()) or sum(map(len, tables.values())) > 2000:
            raise ValueError('Maximum 2,000 rows per workspace.')
        with _lock:
            base = root(); base.mkdir(parents=True, exist_ok=True, mode=0o700)
            for old in base.iterdir():
                if old.is_dir() and re.fullmatch(r'[a-f0-9]{48}', old.name) and time.time()-old.stat().st_mtime > TTL:
                    shutil.rmtree(old)
            if len(list(base.iterdir())) >= 40:
                raise HTTPException(429, 'Upload storage is full. Try again after older workspaces expire.')
            token = secrets.token_hex(24); selected = base/token; selected.mkdir(mode=0o700)
        for filename, headers in known.items():
            rows = []
            for i, row in enumerate(tables.get(filename, []), 1):
                if not isinstance(row, dict) or set(row) - set(headers):
                    raise ValueError(f'{filename}, row {i}: unrecognized columns.')
                if any(not isinstance(v, (str, int)) or isinstance(v, bool) or len(str(v)) > 20000 for v in row.values()):
                    raise ValueError(f'{filename}, row {i}: values must be text/numbers up to 20,000 characters.')
                rows.append({h: str(row.get(h, '')) for h in headers})
            with (selected/filename).open('w', encoding='utf-8', newline='') as f:
                if filename.endswith('.jsonl'):
                    for row in rows: f.write(json.dumps(row,ensure_ascii=False)+'\n')
                else:
                    writer=csv.DictWriter(f,fieldnames=headers);writer.writeheader();writer.writerows(rows)
        ds = load_dataset(selected)
        accounts=ds.by_id['crm_accounts.csv']; employees=ds.by_id['employees.csv']
        deals=ds.tables['crm_deals.csv']
        open_deals = [r for r in deals if r.values['status'] == 'Terbuka']
        if not 1 <= len(open_deals) <= 20: raise ValueError('Provide 1–20 open deals; historical closed deals are optional.')
        for row in deals:
            v=row.values
            if v['account_id'] not in accounts or v['owner_id'] not in employees:
                raise ValueError('Every deal needs a matching account_id and employee owner_id.')
            if v['status'] not in ('Terbuka','Menang','Kalah') or (v['status']=='Terbuka' and v['stage'] not in ('Lead','Discovery','Demo','Proposal','Negosiasi')):
                raise ValueError('Open deals only: status Terbuka; stage Lead, Discovery, Demo, Proposal or Negosiasi.')
            if v['status']=='Terbuka' and accounts[v['account_id']].values['tipe'] != 'prospek': raise ValueError('Deal accounts need tipe=prospek.')
            if not isinstance(v['nilai_tahunan'],int) or v['nilai_tahunan'] < 0 or not isinstance(v['outlet'],int) or v['outlet'] < 1:
                raise ValueError('Deal annual value must be non-negative IDR; outlet must be a positive integer.')
            if not isinstance(v['dibuat'],date) or not isinstance(v['stage_sejak'],date) or not v['dibuat'] <= v['stage_sejak'] <= when:
                raise ValueError('Deal dates must satisfy dibuat <= stage_sejak <= snapshot_date.')
        if len({r.values['account_id'] for r in open_deals}) != len(open_deals): raise ValueError('Use one open deal per account in this version.')
        # Enforce entity IDs unique across types; the graph uses a shared node namespace.
        entity_tables = ['crm_accounts.csv','crm_contacts.csv','crm_deals.csv','employees.csv','interactions.jsonl','decision_log.csv','support_tickets.csv','features.csv','bugs.csv','outlets.csv','contracts_billing.csv']
        ids=[r.source_id for f in entity_tables for r in ds.tables[f]]
        if len(ids)!=len(set(ids)): raise ValueError('Entity IDs must be unique across tables.')
        for filename, rows in ds.tables.items():
            for row in rows:
                for field,target in [('account_id',accounts),('account_id_saat_ini',accounts)]:
                    if row.values.get(field) and row.values[field] not in target: raise ValueError(f'{filename}: unresolved {field}.')
        meta={'name':name.strip(),'snapshot_date':when.isoformat(),'allow_jev':bool(allow_jev),'created_at':time.time()}
        (selected/'manifest.json').write_text(json.dumps(meta))
        state=workspace.set({**meta,'path':str(selected)})
        try:
            from backend.api.phase3 import pipeline_priorities
            priorities=pipeline_priorities()  # Full graph, diagnostics, rules, and provenance validation; no paid calls.
        finally: workspace.reset(state)
        present=[f for f,rows in ds.tables.items() if rows]
        warnings=[]
        if not ds.tables['decision_log.csv']:warnings.append('No decision history: precedent comparisons will be limited.')
        if not ds.tables['interactions.jsonl']:warnings.append('No conversations: recommendations may require discovery.')
        if any(r.values['nilai_tahunan'] != r.values['outlet'] * 350000 * 12 for r in open_deals):
            warnings.append('Some CRM values differ from KasirNusa list pricing. Standard-price scenarios are not your quoted deal value.')
        warnings.append('KasirNusa policy applies: IDR 350,000 per outlet/month; discounts above 10% require VP Sales approval. Existing sales rules and IDR value thresholds apply. Uploading data does not train a new model.')
        return {'workspace_id':token,**meta,'deal_count':len(priorities['items']),'source_count':len(present),'sources':present,'warnings':warnings,'expires_in_hours':24}
    except HTTPException as e:
        if selected: shutil.rmtree(selected,ignore_errors=True)
        if e.status_code==429:raise
        raise HTTPException(422,'The data could not produce a consistent graph and ranking. Check the template and references.') from None
    except (ValueError,KeyError,TypeError,UnicodeError,zipfile.BadZipFile,csv.Error,OverflowError) as e:
        if selected:shutil.rmtree(selected,ignore_errors=True)
        # Structural errors only; never echo raw cells or private uploaded transcript values.
        message=str(e) if isinstance(e,ValueError) and not isinstance(e,json.JSONDecodeError) else 'Invalid package. Check the JSON/ZIP template, dates, and required fields.'
        if len(message)>200 or 'expected string' in message or 'invalid ' in message.lower(): message='Invalid data value. Check date, number, ID, and template formats.'
        raise HTTPException(422,message) from None


@router.get('/api/import/template')
def download_template():
    return JSONResponse(template(),headers={'Content-Disposition':'attachment; filename="dealcompass-example.json"'})


@router.post('/api/import')
async def upload(request: Request, allow_jev: bool=False):
    raw=bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw)>MAX_BYTES:raise HTTPException(413,'File too large. Maximum upload is 2 MB.')
    return await run_in_threadpool(import_package,bytes(raw),request.headers.get('content-type','').startswith('application/zip'),allow_jev)


@router.get('/api/import/template.zip')
def download_csv_template():
    data=template(); output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json',json.dumps({k:data[k] for k in ('name','snapshot_date')}))
        for filename,headers in schemas().items():
            rows=[{h:str(r.get(h,'')) for h in headers} for r in data['tables'].get(filename,[])]
            if filename.endswith('.jsonl'):
                text=''.join(json.dumps(r)+'\n' for r in rows)
            else:
                stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=headers);writer.writeheader();writer.writerows(rows);text=stream.getvalue()
            z.writestr(filename,text)
    return Response(output.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="dealcompass-csv-kit.zip"'})
