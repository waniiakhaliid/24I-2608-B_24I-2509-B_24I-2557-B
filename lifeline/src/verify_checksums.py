import hashlib, sys
from pathlib import Path

DATA = Path("data")

def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()

bad = 0
for line in (DATA / "CHECKSUMS.txt").read_text().splitlines():
    parts = line.split()
    if len(parts) < 2:
        continue
    expected, name = parts[0].lower(), parts[-1].lstrip("*")
    path = DATA / name
    if not path.exists():
        print(f"MISSING  {name}"); bad += 1; continue
    ok = sha256(path) == expected
    print(f"{'OK     ' if ok else 'MISMATCH'}  {name}")
    bad += not ok

sys.exit(1 if bad else 0)