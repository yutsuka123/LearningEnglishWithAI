# ruff: noqa: E501
"""日本語由来語34語の発音を「英語風IPAが主・日本語式IPAは原語欄」に整える(2026-09-26・docs/DESIGN.md §9.8 段階(b-1))。

背景: 色名(-iro系)・将棋用語・Zen・八百万の神などの`detail.pronunciation`が、日本語式の音素記号(ɯ ɾ ɕ ʑ ɸ)や
ローマ字を/…/で囲んだもの(`/ai iro/`・`/sente/`)になっていた。オーナー決定(2026-09-25): 主表示は「英語話者が
読む音」の英語風IPA(=音声と一致させる)にし、日本語式は`native`(原語)欄へ移す。
英語風IPAは、既存の本番音声(ash/nova・learn)を綴りを伏せてgpt-audio-1.5に聞かせた読み(各3票・2026-09-26)から決めた。

書き換える内容(words.detail のJSONの、下記キーだけ。他は保持する):
  pronunciation   : 英語風IPA(下のTABLE)
  origin_lang     : "ja"
  origin_lang_name: "日本語"
  native          : {"text": 原語表記(漢字), "ipa": 日本語式IPA(元の値を継承), "romaji": 綴り}

使い方(テーブル単位・wordsだけ・他のテーブルには触れない):
  python scripts/apply_ja_origin_pronunciation_2026_09_26.py            # dry-run(既定・何も書かない)
  python scripts/apply_ja_origin_pronunciation_2026_09_26.py --apply    # 反映(直前に元のdetailをバックアップJSONへ保存)
  python scripts/apply_ja_origin_pronunciation_2026_09_26.py --rollback <バックアップJSON>   # 元に戻す
本番では deploy/macos/run_script_on_vps.sh 経由で実行し、実行前後にwords件数が変わらないことを確認すること
(CLAUDE.md「本番DBは丸ごと上書きしない」)。IDだけでなく英語綴りも一致した行だけを更新する(IDのずれによる誤更新の防止)。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# id: (english, 英語風IPA, 原語表記)
TABLE: dict[int, tuple[str, str, str]] = {
    16369: ("ai-iro", "/ˈaɪ ˌiːroʊ/", "藍色"),
    16370: ("kurenai", "/ˈkuːrɛnaɪ/", "紅"),
    16371: ("sakura-iro", "/ˈsɑːkuːrɑː ˌiːroʊ/", "桜色"),
    16372: ("nadeshiko-iro", "/nɑːˈdɛʃikoʊ ˌiːroʊ/", "撫子色"),
    16373: ("yamabuki-iro", "/jɑːmɑːˈbuːki iːˈroʊ/", "山吹色"),
    16374: ("moegi-iro", "/moʊˈɛɡi ˌiːroʊ/", "萌葱色"),
    16375: ("asagi-iro", "/ɑːˈsɑːɡi ˌiːroʊ/", "浅葱色"),
    16376: ("akane-iro", "/ɑːˈkɑːneɪ ˌiːroʊ/", "茜色"),
    16377: ("shu-iro", "/ˈʃuː ˌiːroʊ/", "朱色"),
    16378: ("gunjo-iro", "/ˈɡʌndʒoʊ ˌiːroʊ/", "群青色"),
    16379: ("ruri-iro", "/ˈruːri ˌiːroʊ/", "瑠璃色"),
    16380: ("wakakusa-iro", "/wɑːkɑːˈkuːsɑː ˌiːroʊ/", "若草色"),
    16381: ("uguisu-iro", "/uːˈɡwiːsuː ˌiːroʊ/", "鶯色"),
    16382: ("edo-murasaki", "/ˈɛdoʊ mʊrɑːˈsɑːki/", "江戸紫"),
    16383: ("kyo-murasaki", "/ˈkjoʊ mʊrɑːˈsɑːki/", "京紫"),
    16384: ("kinari-iro", "/kiːˈnɑːri ˌiːroʊ/", "生成り色"),
    16385: ("toki-iro", "/ˈtoʊki ˌiːroʊ/", "鴇色"),
    16386: ("ama-iro", "/ˈɑːmɑː ˌiːroʊ/", "亜麻色"),
    16387: ("fuji-iro", "/ˈfuːdʒi ˌiːroʊ/", "藤色"),
    16388: ("sora-iro", "/ˈsoʊrɑː ˌiːroʊ/", "空色"),
    16389: ("kuchiba-iro", "/ˈkuːtʃibɑː ˌiːroʊ/", "朽葉色"),
    16390: ("tokiwa-iro", "/toʊˈkiːwɑː ˌiːroʊ/", "常磐色"),
    16391: ("koki-hi", "/koʊˈki hi/", "濃緋"),
    16392: ("sango-iro", "/ˈsɑːnɡoʊ ˌiːroʊ/", "珊瑚色"),
    16393: ("karashi-iro", "/kɑːˈrɑːʃi ˌiːroʊ/", "からし色"),
    16394: ("azuki-iro", "/ɑːˈzuːki ˌiːroʊ/", "小豆色"),
    8678: ("tokin", "/ˈtoʊkɪn/", "と金"),
    8681: ("sente", "/ˈsɛnteɪ/", "先手"),
    8682: ("gote", "/ˈɡoʊteɪ/", "後手"),
    8683: ("tsumeshogi", "/suːˈmeɪ ˈʃoʊɡi/", "詰将棋"),
    8684: ("kifu", "/ˈkiːfuː/", "棋譜"),
    11882: ("yaoyorozu no kami", "/ˌjɑːoʊ joʊˈroʊzu noʊ ˈkɑːmi/", "八百万の神"),
    11892: ("Zen", "/zɛn/", "禅"),
}

# 日本語式IPAで元の値が足りない/ローマ字風の語の補正(それ以外は元の値をそのままnative.ipaに継承する)。
NATIVE_IPA_OVERRIDE = {11892: "/zeɴ/", 8681: "/sente/", 8682: "/ɡote/"}


def native_ipa_from(old: str, wid: int) -> str:
    """元のpronunciation(日本語式・またはローマ字風)から、原語欄に置く日本語式IPAを作る。"""
    if wid in NATIVE_IPA_OVERRIDE:
        return NATIVE_IPA_OVERRIDE[wid]
    ipa = old.split("（")[0].strip()      # 「/…/（日本語…に由来）」型の注記は落とす
    core = ipa.strip("/")
    if core.endswith(" iro"):
        core = core[: -len(" iro")] + " iɾo"  # 色名の「いろ」は日本語では弾き音
    return "/" + core + "/"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="実際に書き込む(既定はdry-run)")
    ap.add_argument("--rollback", metavar="BACKUP_JSON", help="バックアップJSONから元のdetailに戻す")
    ap.add_argument("--backup-dir", default="data", help="バックアップJSONの保存先(既定 data/)")
    args = ap.parse_args()

    if args.rollback:
        rows = json.loads(Path(args.rollback).read_text(encoding="utf-8"))
        with db() as conn:
            n0 = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
            for r in rows:
                conn.execute(
                    "UPDATE words SET detail = ? WHERE id = ? AND english = ?",
                    (r["detail"], r["id"], r["english"]))
            conn.commit()
            n1 = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        print(f"ロールバック: {len(rows)}語のdetailを戻しました(words件数 {n0}→{n1})")
        return 0

    plan, backup, skipped = [], [], []
    with db() as conn:
        n_words = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        for wid, (english, new_ipa, ja_text) in TABLE.items():
            row = conn.execute("SELECT id, english, detail FROM words WHERE id = ?", (wid,)).fetchone()
            if not row or row["english"] != english:
                skipped.append((wid, english, "IDまたは綴りが一致しない(未更新)"))
                continue
            try:
                d = json.loads(row["detail"] or "")
            except Exception:
                skipped.append((wid, english, "detailが無い/不正(未更新)"))
                continue
            old = (d.get("pronunciation") or "").strip()
            if d.get("native") and old == new_ipa:
                skipped.append((wid, english, "反映済み"))
                continue
            nd = dict(d)
            nd["pronunciation"] = new_ipa
            nd["origin_lang"] = "ja"
            nd["origin_lang_name"] = "日本語"
            keep_native = d.get("native") or {}
            nd["native"] = {
                "text": keep_native.get("text") or ja_text,
                "ipa": keep_native.get("ipa") or native_ipa_from(old, wid),
                "romaji": keep_native.get("romaji") or english,
            }
            plan.append((wid, english, old, new_ipa, nd))
            backup.append({"id": wid, "english": english, "detail": row["detail"]})

        for wid, english, old, new_ipa, nd in plan:
            print(f"  {wid:>6} {english:<18} {old:<34} → {new_ipa:<36} 原語IPA={nd['native']['ipa']}")
        for wid, english, why in skipped:
            print(f"  {wid:>6} {english:<18} スキップ: {why}")
        print(f"\n更新対象 {len(plan)}語 / スキップ {len(skipped)}語 / words件数 {n_words}")
        if not args.apply:
            print("dry-runです(何も書いていません)。反映するには --apply を付けてください。")
            return 0
        if not plan:
            return 0
        bdir = Path(args.backup_dir)
        bdir.mkdir(parents=True, exist_ok=True)
        bpath = bdir / f"backup_ja_pronunciation_{time.strftime('%Y%m%d_%H%M%S')}.json"
        bpath.write_text(json.dumps(backup, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"バックアップ: {bpath}")
        for wid, english, _old, _new, nd in plan:
            conn.execute("UPDATE words SET detail = ? WHERE id = ? AND english = ?",
                         (json.dumps(nd, ensure_ascii=False), wid, english))
        conn.commit()
        n_after = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    print(f"反映しました: {len(plan)}語(words件数 {n_words}→{n_after}・変わっていないこと)。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
