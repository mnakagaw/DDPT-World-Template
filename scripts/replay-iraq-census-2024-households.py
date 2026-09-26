"""Create a new Iraq r2 candidate from a read-only r1 project and official PDFs."""

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


BASE_SHA256 = "28049edc8582b37f58b176ebc9ed8ff64b71f7bc33669b98c43b8d281b39c7e1"
MATCHES = ["الصعوبات", "مصادر الكهرباء", "مصادر الماء", "اخر شهادة",
           "الالتحاق", "سكان_فئات", "مصدر مياه الشرب"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", required=True, type=Path,
                        help="existing Iraq r1 candidate; read-only")
    parser.add_argument("--out", required=True, type=Path,
                        help="new candidate within this repository worktree")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    source = args.source_project.resolve(strict=True)
    out = args.out.resolve()
    if out.exists() or out == root or root not in out.parents or source == out or out in source.parents:
        raise ValueError("Output must be a new directory inside this worktree, apart from the source")
    source_dataset = source / "data/dashboard.json"
    if hashlib.sha256(source_dataset.read_bytes()).hexdigest() != BASE_SHA256:
        raise ValueError("The source candidate is not the pinned 2026-09-26 Iraq r1 dataset")
    print(f"Copying read-only baseline to {out}", flush=True)
    shutil.copytree(source, out)
    python = sys.executable
    commands = [
        [python, str(root / "scripts/collect-iraq-census-2024-catalogue.py"),
         "--out", str(out / "raw"), *[arg for term in MATCHES for arg in ("--match", term)]],
        [python, str(root / "scripts/import-iraq-census-2024-household-tables.py"),
         "--project", str(out)],
        ["node", str(root / "scripts/validate-country.mjs"), "--project", str(out)],
        ["node", str(root / "scripts/build-country.mjs"), "--project", str(out)],
        ["node", str(root / "scripts/verify-iraq-census-2024-household-output.mjs"),
         "--project", str(out)],
    ]
    for command in commands:
        print(f"Running {Path(command[1]).name}", flush=True)
        subprocess.run(command, cwd=root, check=True)
    print(f"Replayed: {out}", flush=True)


if __name__ == "__main__":
    main()
