"""Reproduce the pinned vocabulary from an existing KhmerEasyTools checkout.

No download, model or new corpus is needed. Example:
python scripts/import_vocabulary.py --ket-checkout ../khmereasytools --check
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ket-checkout", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    base = ROOT / "data" / "vocabulary"
    try:
        manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
        words = set()
        for component in manifest["components"]:
            raw = (args.ket_checkout / component["path"]).read_bytes()
            entries = raw.decode("utf-8").splitlines()
            if (hashlib.sha256(raw).hexdigest() != component["sha256"]
                    or len(entries) != component["entries"]):
                raise ValueError(f'Pinned source differs: {component["path"]}')
            words.update(entries)
        raw = ("\n".join(sorted(words)) + "\n").encode("utf-8")
        if (len(words) != manifest["entries"]
                or hashlib.sha256(raw).hexdigest() != manifest["output_sha256"]):
            raise ValueError("Merged vocabulary differs from its manifest")
        output = base / manifest["output_file"]
        if args.check:
            if output.read_bytes() != raw:
                raise ValueError("Committed vocabulary differs from its pinned components")
        else:
            output.write_bytes(raw)
        print(f"Verified {len(words)} vocabulary entries from the pinned components")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
