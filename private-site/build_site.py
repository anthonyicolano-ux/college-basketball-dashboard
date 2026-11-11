"""Copy only allowlisted static demo assets to the protected hosting directory."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
out = Path(__file__).resolve().parent / 'site'
if out.exists():
    shutil.rmtree(out)
allowed = [
    'index.html','players.html','matchups.html',
    'assets/app.js','assets/style.css',
    'data/teams.json','data/players.json','data/demo-schedule.json','data/refresh-status.json',
]
for name in allowed:
    source = root / name
    if not source.is_file():
        raise FileNotFoundError(name)
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source,target)
print('Prepared protected hosting assets using fictional demo data only.')
