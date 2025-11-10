"""
Export SHA256 hashes for files under media/, static/, templates/ to scan_reports/file_hashes.csv
Usage: python scripts/export_file_hashes.py
"""
import hashlib
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET_DIRS = [ROOT / 'media', ROOT / 'static', ROOT / 'templates']
OUT_DIR = ROOT / 'scan_reports'
OUT_DIR.mkdir(exist_ok=True)
OUT_FILE = OUT_DIR / 'file_hashes.csv'

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

rows = []
for td in TARGET_DIRS:
    if not td.exists():
        continue
    for p in td.rglob('*'):
        if p.is_file():
            try:
                rows.append((str(p.relative_to(ROOT)), sha256_of_file(p)))
            except Exception as e:
                rows.append((str(p.relative_to(ROOT)), f'ERROR: {e}'))

with OUT_FILE.open('w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['path', 'sha256'])
    for r in rows:
        writer.writerow(r)

print(f'Wrote {len(rows)} entries to {OUT_FILE}')
