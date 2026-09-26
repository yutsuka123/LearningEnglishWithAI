"""原語音声(VOICEVOX)の読みを、別系統の辞書で自己照合する(2026-09-26)。

`gen_native_audio_voicevox.py`が作った`manifest.json`の各語について、VOICEVOX(OpenJTalk辞書)の読みを
  ① UniDic(fugashi+unidic-lite)  ② Sudachi(sudachipy+sudachidict_core)  ③ 語の綴り(romaji・manifestのenglish)
と照合し、一致しない語だけを人が(または調べて)判定できるように一覧にする。アクセントはUniDicの型(aType)と参考比較する。
  - 3つの辞書は系統が違う(OpenJTalk=NAIST-jdic系・UniDic・Sudachi)ので、読みが偶然そろって間違う確率は低い。
  - 不一致は「VOICEVOXの誤読」だけでなく「UniDic/Sudachiが一般語として読んだだけ(七五三=ナナゴサン・常磐色=ジョウバンイロ等)」も多い。
    判定は人が行い、誤読なら`native_audio_overrides_*.json`に`speak`/`kana`を足して`gen_native_audio_voicevox.py --merge --only`で作り直す。
使い方(開発用の依存は本番には不要): pip install fugashi unidic-lite sudachipy sudachidict_core pykakasi
    python scripts/check_native_readings.py --manifest <dir>/manifest.json --out <dir>/reading_check.html
"""
from __future__ import annotations

import argparse
import html
import json
import re
import warnings

warnings.filterwarnings("ignore")


def kata(s: str) -> str:
    return "".join(chr(ord(c) + 96) if "ぁ" <= c <= "ゖ" else c for c in s)


def mora_count(k: str) -> int:
    return len([c for c in k if c not in "ャュョァィゥェォ"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True, help="確認用HTMLの出力先")
    a = ap.parse_args()
    import fugashi
    import pykakasi
    from sudachipy import dictionary, tokenizer

    words = json.load(open(a.manifest, encoding="utf-8"))["words"]
    tagger = fugashi.Tagger()
    sud = dictionary.Dictionary().create()
    kks = pykakasi.kakasi()

    def romaji(s: str) -> str:
        return "".join(x["hepburn"] for x in kks.convert(kata(s)))

    def norm(r: str) -> str:   # 長音・濁点の表記ゆれを吸収して比較する(比較専用)
        r = r.lower()
        for x, y in (("ō", "o"), ("ô", "o"), ("ū", "u"), ("û", "u"), ("ē", "e"), ("ā", "a"), ("ī", "i")):
            r = r.replace(x, y)
        r = re.sub(r"[^a-z]", "", r)
        for x, y in (("ou", "o"), ("oo", "o"), ("uu", "u"), ("ee", "e"), ("ei", "e"), ("aa", "a"), ("ii", "i")):
            r = r.replace(x, y)
        return (r.replace("wo", "o").replace("dz", "z").replace("zu", "z").replace("du", "z").replace("ji", "z")
                .replace("di", "z").replace("nn", "n").replace("mb", "nb").replace("mp", "np"))

    rows = []
    for wid, v in sorted(words.items(), key=lambda x: int(x[0])):
        text, vv, en = v["text"], v["reading"], v["english"]
        toks = list(tagger(text))
        pron = kata("".join((t.feature.pron if t.feature.pron not in (None, "*") else t.surface) for t in toks))
        kana = kata("".join((t.feature.kana if getattr(t.feature, "kana", None) not in (None, "*") else t.surface) for t in toks))
        sr = kata("".join(m.reading_form() for m in sud.tokenize(text, tokenizer.Tokenizer.SplitMode.C)))
        n_vv = norm(romaji(vv))
        n_dict = [norm(romaji(x)) for x in (pron, kana, sr)]
        n_en = norm(re.sub(r"[^A-Za-z]", "", re.sub(r"\(.*?\)", "", en)))
        agree_dict = n_vv in n_dict
        agree_en = bool(n_en) and (n_vv == n_en or n_en in n_vv or n_vv in n_en)
        # アクセント(参考): 1語・1句の語だけUniDicの型と比べる。型: 0=平板・n=n拍目の後で下がる。
        acc = None
        if len(toks) == 1 and " / " not in v["accent"]:
            atypes = {int(x) for x in re.findall(r"\d+", str(toks[0].feature.aType))} if getattr(toks[0].feature, "aType", None) else set()
            k = v["reading"]
            m = mora_count(k)
            nucleus = mora_count(v["accent"].split("↓")[0]) if "↓" in v["accent"] else 0
            if atypes:
                acc = (nucleus in atypes) or (nucleus == 0 and (m in atypes)) or (nucleus == m and 0 in atypes)
        rows.append(dict(id=wid, english=en, text=text, vv=vv, accent=v["accent"], unidic=pron, sudachi=sr,
                         agree_dict=agree_dict, agree_en=agree_en, acc=acc, atype=str(toks[0].feature.aType) if len(toks) == 1 else "-"))
    order = lambda r: (r["agree_dict"] and r["agree_en"], r["agree_dict"] or r["agree_en"])
    rows.sort(key=lambda r: (order(r), int(r["id"])))
    both = sum(1 for r in rows if r["agree_dict"] and r["agree_en"])
    accd = [r for r in rows if r["acc"] is False]
    acck = [r for r in rows if r["acc"] is not None]
    print(f"全{len(rows)}語: 辞書・綴りとも一致={both} / 要確認={len(rows) - both}")
    print(f"アクセント(参考・1語1句{len(acck)}語): UniDicの型と一致={len(acck) - len(accd)} / 不一致={len(accd)}")
    body = []
    for r in rows:
        st = "✅辞書+綴り一致" if (r["agree_dict"] and r["agree_en"]) else ("△辞書のみ一致" if r["agree_dict"] else ("△綴りのみ一致" if r["agree_en"] else "❓どちらも不一致"))
        ac = "" if r["acc"] is None else ("✅" if r["acc"] else "△UniDicと違う(型 " + r["atype"] + ")")
        body.append(f"<tr><td>{r['id']}</td><td>{html.escape(r['english'])}</td><td>{html.escape(r['text'])}</td><td>{html.escape(r['vv'])}</td>"
                    f"<td>{html.escape(r['unidic'])}</td><td>{html.escape(r['sudachi'])}</td><td>{st}</td><td>{html.escape(r['accent'])}</td><td>{ac}</td></tr>")
    open(a.out, "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><title>原語音声の読みの自己照合</title>'
        "<style>body{font-family:system-ui,sans-serif;margin:16px}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:3px 6px}th{background:#f3f3f3}</style>"
        f"<h1>原語音声の読みの自己照合({len(rows)}語)</h1><p>VOICEVOXの読みを、UniDic・Sudachi・語の綴りと照合。要確認の語が上に来ます。"
        "長音は「ショオグン(=しょうぐん)」のようにオ/ウ/エ等で表示されます。アクセントは参考(UniDicの型との比較・1語1句のみ)。</p>"
        "<table><tr><th>ID</th><th>english</th><th>原語表記</th><th>VOICEVOXの読み</th><th>UniDic</th><th>Sudachi</th><th>読みの照合</th><th>アクセント(VOICEVOX)</th><th>アクセント参考</th></tr>"
        + "\n".join(body) + "</table>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
