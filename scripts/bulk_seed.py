"""One-off bulk seeding: import a pasted word list, then generate curated
category vocabulary via the running app's AI endpoints.

Run while the server is up:  python scripts/bulk_seed.py
"""

from __future__ import annotations

import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"


def post(path: str, body: dict, timeout: int = 600) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=60) as r:
        return json.load(r)


def import_file(path: str) -> None:
    text = open(path, encoding="utf-8").read()
    # Split into chunks so each request's AI work stays manageable.
    lines = [ln for ln in text.splitlines() if ln.strip()]
    chunk = 60
    total_added = 0
    for i in range(0, len(lines), chunk):
        part = "\n".join(lines[i:i + chunk])
        r = post("/api/words/import",
                 {"text": part, "generate_examples": True})
        total_added += r.get("added", 0)
        print(f"  import {i + chunk}/{len(lines)}: "
              f"added={r.get('added')} skipped={r.get('skipped')}", flush=True)
    print(f"import done: +{total_added}", flush=True)


# (focus, target count)
CATEGORIES = [
    ("英語圏の一般教養（文化・歴史・科学・芸術・社会・宗教）", 300),
    ("日常英会話でよく使う動詞・形容詞・口語表現", 200),
    ("IT・ソフトウェア開発・組み込み開発・ビルド/ビルドエラーの専門用語", 100),
    ("ビジネス・オフィス・会議・契約で頻出の語", 100),
    ("ニュース英語（政治・経済・軍事）の頻出語", 200),
    ("英文学・聖書の引用・シェークスピア・歴史・名言に出る語", 200),
    ("日常生活の基本語（家事・買い物・天気・家族）", 100),
    ("英語圏の子供は知っているが日本の学校では習いにくい基本語", 100),
    ("外国人観光客から道や場所を尋ねられる場面で使う語", 100),
    ("ホテル・入国管理・レストラン注文・非常時・警察・救急・病院・薬局の語",
     300),
]


def gen_category(focus: str, target: int) -> None:
    added = 0
    rounds = (target + 29) // 30
    for _ in range(rounds):
        try:
            r = post("/api/learn/generate-items",
                     {"kind": "word", "count": 30, "focus": focus})
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {focus[:20]}: {exc}", flush=True)
            continue
        if not r.get("ok"):
            print(f"  ! {focus[:20]}: {r.get('error')}", flush=True)
            break
        added += len(r.get("added", []))
        print(f"  {focus[:24]}: +{len(r.get('added', []))} "
              f"(total {added})", flush=True)
    print(f"category done: {focus[:24]} +{added}", flush=True)


def main() -> None:
    print("== start ==", flush=True)
    print("words before:", get("/api/words/stats")["total"], flush=True)
    import_file("/tmp/list732.txt")
    for focus, target in CATEGORIES:
        gen_category(focus, target)
    print("words after:", get("/api/words/stats")["total"], flush=True)
    print("== done ==", flush=True)


if __name__ == "__main__":
    sys.exit(main())
