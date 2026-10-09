"""Verifikasi handoff dan pembagian file; jalankan dari root repo."""
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADINGS = (
    'Task dan status', 'Branch dan commit', 'File dan fungsi',
    'Kontrak dan dependency', 'Cara menjalankan', 'Pengujian aktual',
    'Fixture dan keterbatasan', 'Blocker', 'Tugas berikutnya', 'Update WIB',
)
OWNED = {
    'BOY': ('frontend/',),
    'BIMA': ('backend/ingestion/', 'backend/graph/', 'backend/api/', 'backend/main.py', 'tests/bima/'),
    'ICAL': ('backend/decision/', 'backend/integrations/', 'evaluation/', 'tests/ical/'),
}
SHARED = {'frontend/package.json', 'frontend/package-lock.json'}

def validate_note(text: str) -> list[str]:
    lines = text.splitlines()
    errors = []
    for heading in HEADINGS:
        marker = f'## {heading}'
        if marker not in lines:
            errors.append(f'Heading wajib tidak ada: {marker}')
            continue
        start = lines.index(marker) + 1
        stop = next((i for i in range(start, len(lines)) if lines[i].startswith('## ')), len(lines))
        if not '\n'.join(lines[start:stop]).strip():
            errors.append(f'Isi heading kosong: {marker}')
    return errors

def role_for(branch: str) -> str:
    prefix = branch.split('/', 1)[0].upper()
    if '/' not in branch or prefix not in (*OWNED, 'MAIN'):
        raise ValueError('Branch harus boy/*, bima/*, ical/* atau main/*.')
    return prefix

def validate_changes(paths: list[str], branch: str, read_text) -> list[str]:
    role = role_for(branch)
    note = f'docs/handoffs/{role}.md'
    errors = []
    if note not in paths:
        errors.append(f'WAJIB memperbarui {note} bersama PR ini.')
    else:
        try:
            errors.extend(validate_note(read_text(note)))
        except FileNotFoundError:
            errors.append(f'Catatan tidak boleh dihapus: {note}')
    for p in paths:
        if p.startswith('dataset_kasirnusa/'):
            errors.append(f'Dataset sumber harus tetap asli: {p}')
        if role == 'MAIN':
            continue
        allowed = p == note or any(p.startswith(a) if a.endswith('/') else p == a for a in OWNED[role])
        if not allowed or p in SHARED:
            errors.append(f'Perubahan di luar kepemilikan {role}; koordinasikan Main: {p}')
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true', help='Validasi isi seluruh catatan tanpa diff')
    parser.add_argument('--base')
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--branch')
    args = parser.parse_args()
    errors = []
    if args.all:
        for role in ('MAIN', 'BOY', 'BIMA', 'ICAL'):
            p = ROOT / f'docs/handoffs/{role}.md'
            try:
                errors.extend(f'{role}: {e}' for e in validate_note(p.read_text()))
            except FileNotFoundError:
                errors.append(f'Catatan hilang: {p.relative_to(ROOT)}')
    else:
        if not args.base or not args.branch:
            parser.error('Gunakan --all atau --base <ref> --head <ref> --branch <nama>')
        result = subprocess.run(['git', 'diff', '--name-only', f'{args.base}...{args.head}'], cwd=ROOT, check=True, capture_output=True, text=True)
        try:
            errors = validate_changes(result.stdout.splitlines(), args.branch, lambda p: (ROOT / p).read_text())
        except ValueError as e:
            errors.append(str(e))
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print('Handoff valid. Main tetap memverifikasi kebenaran laporan dan integrasi.')

if __name__ == '__main__':
    main()

