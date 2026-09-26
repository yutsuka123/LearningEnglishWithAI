"""日本語由来語の「原語の音声」(詳細plusの中身)をVOICEVOXで生成する(2026-09-26・docs/DESIGN.md §9.8)。

- 対象: `scripts/data/origin_lang_ja_2026_09_26.json`(293語)と、`apply_ja_origin_pronunciation_2026_09_26.py`のTABLE(33語)の和集合のうち、
  原語表記(漢字・かな)がある語。読みは**原語表記をVOICEVOXの辞書でそのまま読ませる**(アクセントも辞書)。辞書が外れた語だけ
  `scripts/data/native_audio_overrides_2026_09_26.json`で上書きする(かな/別の声)。
- 声: 男=剣崎雌雄(id21)・女=波音リツ(id9)。**クレジット「VOICEVOX:キャラ名」が必須**(manifestの`credit`に入れ、画面に出す)。
- **VOICEVOX本体・モデル(VVM)は再配布禁止**なので、このスクリプトは手元(開発機)で動かし、サーバーへ送るのは生成したmp3+manifestだけ。
- 出力: `<out>/w{語ID}_{male|female}_{原語表記のハッシュ10桁}.mp3`・`<out>/manifest.json`・`<out>/review.html`(読みの確認用)。
  manifestには語の英語綴りと原語表記も入れる(サーバーが「IDが指す語が変わっていないか」を照合するため・音声誤配信事故の再発防止)。
- 使い方(VOICEVOX Coreのpython wheel・onnxruntime・辞書(open_jtalk_dic*)・VVM(3.vvm/4.vvm等)を`--voicevox-dir`に置いた状態で):
    python scripts/gen_native_audio_voicevox.py --voicevox-dir <dir> --out <出力dir> [--only sake,sushi]
  外部への通信・APIキーは使わない(費用0)。
"""
from __future__ import annotations

import argparse
import ast
import glob
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MALE = {"id": 21, "name": "剣崎雌雄"}
FEMALE = {"id": 9, "name": "波音リツ"}
VVM_NUMBERS = (0, 2, 3, 4, 6, 9, 15)  # 上の声(+上書きで使う別の声)を含むモデル


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def load_words() -> dict[int, dict]:
    """{語ID: {english, text}}。JSON(293語)+TABLE(33語)。両方にある語は原語表記が一致していること。"""
    words: dict[int, dict] = {}
    for x in json.loads((ROOT / "scripts/data/origin_lang_ja_2026_09_26.json").read_text(encoding="utf-8")):
        if x.get("native_text"):
            words[x["id"]] = {"english": x["english"], "text": x["native_text"]}
    src = (ROOT / "scripts/apply_ja_origin_pronunciation_2026_09_26.py").read_text(encoding="utf-8")
    m = re.search(r"^TABLE\s*(?::[^=]+)?=\s*(\{.*?^\})", src, re.S | re.M)
    table = ast.literal_eval(m.group(1))
    for wid, (english, _ipa, ja_text) in table.items():
        if not ja_text:
            continue
        if wid in words and words[wid]["text"] != ja_text:
            raise SystemExit(f"原語表記が食い違う: id={wid} {english} {words[wid]['text']!r} vs {ja_text!r}")
        words[wid] = {"english": english, "text": ja_text}
    return words


def accent_str(q) -> str:
    out = []
    for ap in q.accent_phrases:
        ms = [m.text for m in ap.moras]
        out.append("".join(ms[: ap.accent]) + "↓" + "".join(ms[ap.accent:]) if ap.accent < len(ms) else "".join(ms) + "→")
    return " / ".join(out)


def to_mp3(wav: bytes, path: str) -> None:
    tmp = tempfile.mktemp(suffix=".wav")
    Path(tmp).write_bytes(wav)
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-ac", "1", "-b:a", "64k", path], check=True)
    finally:
        os.unlink(tmp)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voicevox-dir", required=True, help="onnxruntime/・dict/・models/vvms/ を含むディレクトリ")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="", help="カンマ区切りのenglish(動作確認用・一部だけ作り直すとき)")
    ap.add_argument("--merge", action="store_true", help="出力先の既存manifest.jsonに、今回作った語だけを差し替えて残りは保つ(--onlyと併用)")
    a = ap.parse_args()
    from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

    D = a.voicevox_dir
    ort = Onnxruntime.load_once(filename=glob.glob(f"{D}/onnxruntime/lib/*.dylib")[0])
    syn = Synthesizer(ort, OpenJtalk(glob.glob(f"{D}/dict/open_jtalk_dic*")[0]))
    for n in VVM_NUMBERS:
        with VoiceModelFile.open(f"{D}/models/vvms/{n}.vvm") as m:
            syn.load_voice_model(m)

    ov = json.loads((ROOT / "scripts/data/native_audio_overrides_2026_09_26.json").read_text(encoding="utf-8"))["overrides"]
    words = load_words()
    only = {s.strip() for s in a.only.split(",") if s.strip()}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"format": 1, "generated": time.strftime("%Y-%m-%d %H:%M:%S"), "words": {}}
    mpath = out / "manifest.json"
    if a.merge and mpath.exists():
        manifest["words"] = {k: v for k, v in json.loads(mpath.read_text(encoding="utf-8")).get("words", {}).items()
                             if int(k) in words}   # 対象から外れた語(除外した語)のエントリは落とす
    errors = []
    for wid in sorted(words):
        w = words[wid]
        if only and w["english"] not in only:
            continue
        o = ov.get(w["english"], {})
        h = text_hash(w["text"])
        entry = {"english": w["english"], "text": w["text"]}
        reading = accent = ""
        for sex, base in (("male", MALE), ("female", FEMALE)):
            v = o.get(f"{sex}_voice") or base
            try:
                q = (syn.create_audio_query_from_kana(o["kana"], v["id"]) if o.get("kana")
                     else syn.create_audio_query(o.get("speak") or w["text"], v["id"]))
                fn = f"w{wid}_{sex}_{h}.mp3"
                to_mp3(syn.synthesis(q, v["id"]), str(out / fn))
            except Exception as e:  # 1語の失敗で全体を止めない(一覧に出す)
                errors.append((wid, w["english"], sex, repr(e)))
                continue
            entry[sex] = {"file": fn, "credit": f"VOICEVOX:{v['name']}"}
            if sex == "male":
                reading, accent = "".join(m.text for p in q.accent_phrases for m in p.moras), accent_str(q)
        entry["reading"], entry["accent"] = reading, accent
        if "male" in entry and "female" in entry:
            manifest["words"][str(wid)] = entry
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    rows = []
    for wid_s, e in sorted(manifest["words"].items(), key=lambda x: int(x[0])):
        mark = "★上書き" if e["english"] in ov else ""
        cells = "".join(
            f'<td><audio controls preload="none" src="{e[sex]["file"]}"></audio><br><small>{html.escape(e[sex]["credit"])}</small></td>'
            for sex in ("male", "female"))
        rows.append(f"<tr><td>{wid_s}</td><td>{html.escape(e['english'])}</td><td>{html.escape(e['text'])}</td>"
                    f"<td>{html.escape(e['reading'])}</td><td>{html.escape(e['accent'])}</td><td>{mark}</td>{cells}</tr>")
    (out / "review.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>原語音声の読み確認</title>'
        "<style>body{font-family:system-ui,sans-serif;margin:16px}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:3px 6px}th{background:#f3f3f3}audio{height:28px;width:170px}</style>"
        f"<h1>原語音声の読み確認({len(manifest['words'])}語)</h1><p>「読み」が日本語として合っているか(特に固有名・人名・難読)を確認。アクセントは辞書のまま(★は上書き)。</p>"
        "<table><tr><th>ID</th><th>english</th><th>原語表記</th><th>VOICEVOXの読み</th><th>アクセント(↓下がる/→平板)</th><th></th><th>男</th><th>女</th></tr>"
        + "\n".join(rows) + "</table>", encoding="utf-8")
    print(f"生成/更新: {len(only) or len(manifest['words'])}語(manifest計{len(manifest['words'])}語) / 失敗: {len(errors)}件")
    for e in errors:
        print("  失敗", e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
