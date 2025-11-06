#!/usr/bin/env python3
"""
Aggregate all per-day JSONs in data/wordlists/ into a single curated list.
Outputs:
  - data/wordlists/sb_master.json  (metadata + words[])
  - data/wordlists/sb_master.txt   (one word per line)
"""

import json
from pathlib import Path

IN_DIR  = Path("data/wordlists")
OUT_JSON = IN_DIR / "sb_master.json"
OUT_TXT  = IN_DIR / "sb_master.txt"

def main():
    if not IN_DIR.exists():
        print("data/wordlists not found.")
        return

    words_set = set()
    count_files = 0

    for p in sorted(IN_DIR.glob("*.json")):
        if p.name in ("sb_master.json",):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            for w in data.get("words", []):
                # normalize to lowercase letters only
                lw = w.strip().lower()
                if lw.isalpha() and len(lw) >= 4:
                    words_set.add(lw)
            count_files += 1
        except Exception as e:
            print(f"skip {p.name}: {e}")

    words = sorted(words_set)
    payload = {
        "source": "sbsolver union across daily answers",
        "files_merged": count_files,
        "unique_count": len(words),
        "words": words,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_TXT.write_text("\n".join(words) + "\n", encoding="utf-8")

    print(f"[ok] merged {count_files} files")
    print(f"[ok] unique words: {len(words)}")
    print(f"[ok] wrote {OUT_JSON}")
    print(f"[ok] wrote {OUT_TXT}")

if __name__ == "__main__":
    main()
