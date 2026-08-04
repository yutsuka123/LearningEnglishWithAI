# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for QUALITY-ENGINEERING / OVERSEAS-SUPPLIER
DEFECT INVESTIGATION English, authored by Claude.

Focus (フレーズ集の手薄な領域を補強): 海外の仕入先・委託工場に出張して不具合を
調査する品質・信頼性エンジニア向けの、専門的かつ外交的な英語。症状と発生条件
の説明、現地での再現試験、ロット追跡、材料・設備・工程・作業者(4M)の変化点確認、
「発生原因(occurrence cause)」と「流出原因(escape cause)」の切り分け、暫定対策
と恒久対策の合意、相手が提示した根本原因の根拠を尋ねる質問、角を立てずに根本
原因の説明に異論を唱える表現、責任追及の応酬にしない交渉の進め方、ログ・写真・
再現条件の証拠要求、そして現場での設備デバッグ(配線・設定確認、エラー条件の
確認、現場で許可される変更範囲の確認、安全上の理由での作業中断)を体系的に
カバーする。日常会話の「相槌」や「オンライン会議」とは異なる、製造業の品質
保証・監査に特有の定型表現。

丁寧度や外交的配慮の度合いが分かるよう、日本語訳に〔注〕を付した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_quality_supplier.py
      python scripts/add_quality_supplier.py --missing-words   # report only

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "品質調査・海外サプライヤー対応": [
        # --- 症状・発生条件の説明 ---
        ("Let me walk you through the symptom we're seeing.", "症状について順を追ってご説明します。"),
        ("The defect doesn't occur on every unit — it's intermittent.", "この不具合は全個体で発生するわけではなく、断続的です。"),
        ("It only appears under a specific combination of conditions.", "特定の条件が重なったときにのみ発生します。"),
        ("The failure rate is roughly one in five hundred units.", "不良率はおよそ500個に1個の割合です。"),
        ("Could you tell us exactly when the symptom tends to appear?", "症状が現れやすいタイミングを正確に教えていただけますか。"),
        ("It tends to show up only after the unit has been running for a while.", "しばらく稼働させた後に症状が出る傾向があります。"),
        # --- 現地再現 ---
        ("We'd like to try reproducing the defect here, on your line.", "御社のラインでこの不具合を再現してみたいと思います。"),
        ("Can we attempt to reproduce the same failure mode on-site today?", "本日、この場で同じ故障モードを再現してみてもよろしいですか。"),
        ("We were able to reproduce it under these specific conditions.", "この特定条件下で再現することができました。"),
        ("We haven't been able to reproduce it yet, even under the same conditions.", "同じ条件下でも、まだ再現できておりません。"),
        ("Could we run a few more cycles to see if it reproduces?", "再現するかどうか、もう数サイクル動かしてみてもよろしいですか。"),
        ("What exact conditions do we need to replicate to trigger the failure?", "故障を引き起こすには、どの条件を正確に再現する必要がありますか。"),
        # --- ロット追跡 ---
        ("Can you trace this lot back to the production date and shift?", "このロットの製造日とシフトまで遡って特定していただけますか。"),
        ("We'll need the lot number and the exact date of manufacture.", "ロット番号と正確な製造日を教えていただく必要があります。"),
        ("Is this defect confined to a single lot, or spread across several?", "この不具合は単一ロットに限られていますか、それとも複数ロットにまたがっていますか。"),
        ("Let's check whether all the affected units share the same lot number.", "不具合品がすべて同じロット番号かどうか確認しましょう。"),
        ("How many units were produced in the suspect lot?", "疑わしいロットでは何個生産されましたか。"),
        # --- 4M変化点確認（材料・設備・人・方法） ---
        ("Was there any change in the raw material or the material supplier around that time?", "その時期に、原材料や材料の仕入先に変更はありましたか。"),
        ("Did any process parameters change before this lot was produced?", "このロットが生産される前に、工程条件に変更はありましたか。"),
        ("Was there any equipment maintenance or a tooling change recently?", "最近、設備のメンテナンスや治工具の交換はありましたか。"),
        ("Were any new or newly trained operators working this line?", "このラインで新しく配属・訓練されたオペレーターはいましたか。"),
        ("Let's go through the 4M changes one by one — material, machine, man, and method.", "材料・設備・人・方法の4M変化点を一つずつ確認しましょう。"),
        # --- 発生原因と流出原因の切り分け ---
        ("We need to separate two things: why the defect occurred, and why it wasn't caught.", "不具合が発生した原因と、それが検出されなかった原因を分けて考える必要があります。〔occurrence causeとescape causeを区別する視点〕"),
        ("What's the occurrence cause — why did this happen in the first place?", "そもそもこれがなぜ発生したのか、発生原因は何でしょうか。"),
        ("What's the escape cause — why didn't your inspection catch it?", "御社の検査でなぜ検出できなかったのか、流出原因は何でしょうか。"),
        ("Even after we fix the occurrence cause, we still need to address why it escaped inspection.", "発生原因を直しても、検査をすり抜けた原因への対策は別途必要です。"),
        ("Was this failure mode within the detection capability of your current inspection method?", "この故障モードは現行の検査方法で検出可能な範囲内でしたか。"),
        ("Was the inspection standard simply not designed to catch this, or was the inspection skipped?", "検査基準がこの不具合を想定していなかったのか、それとも検査自体が省略されたのか、どちらでしょうか。"),
        # --- 暫定対策と恒久対策 ---
        ("Let's agree on an interim countermeasure first, then work toward the permanent fix.", "まず暫定対策で合意し、その後恒久対策に取り組みましょう。"),
        ("What containment action is in place for units already shipped?", "既に出荷済みの製品に対する流出防止処置は何でしょうか。"),
        ("Is this sorting a permanent solution, or just a stop-gap measure?", "この選別は恒久対策ですか、それとも一時しのぎでしょうか。"),
        ("We'll need one-hundred-percent inspection until the permanent countermeasure is validated.", "恒久対策の妥当性が確認されるまでは、全数検査をお願いします。"),
        ("When do you expect to have the permanent countermeasure implemented?", "恒久対策はいつ実施される見込みですか。"),
        ("Let's define the exit criteria before we lift the containment.", "流出防止処置を解除する前に、解除基準を明確にしておきましょう。"),
        # --- 根拠を尋ねる ---
        ("Could you walk us through the evidence behind this root cause?", "その根本原因に至った根拠を説明していただけますか。"),
        ("What data supports this conclusion?", "この結論を裏付けるデータは何でしょうか。"),
        ("Has this root cause been confirmed through an actual reproduction test?", "この根本原因は実際の再現試験で確認されていますか。"),
        ("Is this based on analysis, or is it still a hypothesis at this stage?", "これは分析に基づくものですか、それともまだ仮説の段階でしょうか。"),
        ("Could you share the fishbone diagram or the five-why analysis behind this?", "この結論に至った特性要因図や5whys分析を共有していただけますか。"),
        # --- やんわりした反論の切り出し ---
        ("I follow the logic, but I'm not fully convinced this explains all the failures.", "論理は理解できますが、これで全ての不具合を説明できるとは確信が持てません。〔かなり丁寧な反論の切り出し〕"),
        ("That's a reasonable hypothesis, but could there be another contributing factor?", "妥当な仮説だとは思いますが、他に寄与要因はないでしょうか。"),
        ("I'd like to understand this a little more before we agree on the root cause.", "根本原因について合意する前に、もう少し理解を深めたいと思います。〔即断せず時間を稼ぐ婉曲表現〕"),
        ("With respect, this explanation doesn't quite match what we observed on our side.", "恐れ入りますが、この説明は弊社側で確認した内容と少し一致しません。〔丁寧だが明確な反論〕"),
        ("I'm not saying this is wrong, but let's stress-test the theory a little more.", "これが間違っているというわけではありませんが、もう少しこの仮説を検証してみましょう。〔否定を避けた婉曲な反論〕"),
        ("Is it possible this is a contributing factor rather than the root cause itself?", "これは根本原因そのものというより、寄与要因の一つという可能性はありませんか。"),
        # --- 非難合戦にしない交渉 ---
        ("Our goal here isn't to assign blame, it's to prevent recurrence.", "ここでの目的は責任追及ではなく、再発防止です。〔議論の目的を明示して対立を避ける〕"),
        ("Let's focus on the facts rather than on who's responsible.", "誰の責任かではなく、事実に焦点を当てましょう。"),
        ("We understand this may have been outside your direct control.", "これは御社の直接的な管理範囲外だった可能性があると理解しています。〔相手の面子に配慮した表現〕"),
        ("Let's keep this constructive and focus on the corrective action.", "建設的に進め、是正処置に焦点を当てましょう。"),
        ("I understand this puts you in a difficult position, but we do need a firm commitment date.", "難しい立場だと理解していますが、確約いただける期限が必要です。〔配慮しつつも要求は明確に保つ〕"),
        # --- 証拠・記録の要求 ---
        ("Could you provide the process log for the day this lot was produced?", "このロットが生産された日の工程ログを提供していただけますか。"),
        ("Can you send us the inspection records for the suspect lot?", "疑わしいロットの検査記録を送っていただけますか。"),
        ("We'd like copies of the photos taken during your failure analysis.", "御社の故障解析時に撮影された写真のコピーをいただきたいです。"),
        ("Please document the exact reproduction conditions in writing.", "再現条件を正確に文書化してください。"),
        ("Could we get the raw data rather than just a summarized report?", "要約されたレポートだけでなく、生データもいただけますか。"),
    ],
    "現場設備デバッグ・安全確認": [
        # --- 配線・設定確認 ---
        ("Let's check the wiring before we touch any of the software settings.", "ソフトの設定に触れる前に、配線を確認しましょう。"),
        ("Is this connector fully seated?", "このコネクタはきちんと差し込まれていますか。"),
        ("Is this parameter within the allowed range?", "このパラメータは許容範囲内に収まっていますか。"),
        ("We noticed this setting doesn't match the standard work document.", "この設定が標準作業書の内容と一致していないことに気づきました。"),
        # --- エラー条件・ログ確認 ---
        ("What conditions trigger this alarm?", "このアラームが発生する条件は何ですか。"),
        ("Could you show us the error log on the controller?", "コントローラーのエラーログを見せていただけますか。"),
        ("Let's isolate the variable — run it once with the guard on, and once with it off.", "変数を切り分けましょう。カバーを付けた状態と外した状態で一度ずつ動かします。"),
        # --- 現場で許可される変更の範囲 ---
        ("What changes are we allowed to make on-site today?", "本日、現場で行ってよい変更の範囲を教えてください。"),
        ("We shouldn't change the process parameters without your engineer's approval.", "御社エンジニアの承認なしに工程条件を変更すべきではありません。"),
        ("Could we get a copy of the electrical schematic before we open the panel?", "パネルを開ける前に、電気配線図のコピーをいただけますか。"),
        ("Please reset the equipment to the standard settings before we start.", "開始前に設備を標準設定にリセットしてください。"),
        # --- 安全のための中断 ---
        ("Let's stop here — this looks like a safety issue.", "ここで一旦止めましょう、安全上の問題がありそうです。〔安全最優先、強めの中断指示〕"),
        ("Please lock out the equipment before we open the panel.", "パネルを開ける前に設備をロックアウトしてください。"),
        ("Is it safe to run this in manual mode?", "手動モードで動かしても安全ですか。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("root cause", "根本原因", "名詞", "We need to identify the root cause of this defect.", "品質工学", "700"),
    ("countermeasure", "対策", "名詞", "What countermeasure do you propose for this issue?", "品質工学", "700"),
    ("traceability", "トレーサビリティ・追跡可能性", "名詞", "Lot traceability let us narrow down the cause quickly.", "品質工学", "800"),
    ("nonconformance", "不適合", "名詞", "This part is a nonconformance to the drawing.", "品質工学", "900"),
    ("deviation", "逸脱・変則", "名詞", "Was there a process deviation on that shift?", "品質工学", "800"),
    ("containment", "流出防止・封じ込め", "名詞", "We put a containment action in place immediately.", "品質工学", "800"),
    ("reproducibility", "再現性", "名詞", "The reproducibility of this failure is quite low.", "品質工学", "900"),
    ("intermittent", "断続的な", "形容詞", "It's an intermittent failure, not a hard failure.", "品質工学", "800"),
    ("recurrence", "再発", "名詞", "Our main goal is to prevent recurrence.", "品質工学", "800"),
    ("mitigate", "軽減する・緩和する", "動詞", "This action should mitigate the risk of recurrence.", "品質工学", "800"),
    ("outsource", "外部委託する", "動詞", "This process is outsourced to a local supplier.", "製造", "700"),
    ("workmanship", "作業の出来・技量", "名詞", "The defect looks like a workmanship issue, not a design issue.", "製造", "800"),
    ("batch", "ロット・バッチ", "名詞", "Let's inspect the rest of this batch.", "製造", "600"),
    ("anomaly", "異常値・異常", "名詞", "We spotted an anomaly in the temperature log.", "品質工学", "800"),
    ("corrective action", "是正処置", "名詞", "Please submit your corrective action plan by Friday.", "品質工学", "800"),
    ("discrepancy", "食い違い・不一致", "名詞", "There's a discrepancy between the spec and the measured value.", "品質工学", "800"),
    ("audit", "監査する", "動詞", "We're here to audit your quality process.", "品質工学", "700"),
    ("supplier", "仕入先・サプライヤー", "名詞", "We visited the supplier's factory to investigate the defect.", "製造", "600"),
]


# --- insertion --------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "from", "by", "as", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "may", "might", "must", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "this", "that", "these", "those", "here", "there", "what", "when",
    "where", "who", "how", "why", "not", "no", "yes", "so", "up", "out", "off",
    "down", "let", "lets", "please", "thanks", "thank", "ok", "okay", "im",
    "ill", "id", "ive", "dont", "cant", "wont", "isnt", "thats", "whats",
    "very", "just", "too", "more", "some", "any", "all", "one", "two", "get",
    "got", "go", "going", "like", "want", "need", "make", "made", "take",
    "see", "now", "today", "tonight", "good", "well", "back", "about", "over",
    "into", "than", "then", "again", "really", "much", "many", "wish", "mind",
    "could", "would", "shall", "rather", "ever", "way", "everyone", "everybody",
    "minute", "minutes", "second", "seconds", "little", "bit", "few", "keep",
    "sorry", "still", "afterward", "instead", "else", "same", "time", "next",
}


def _content_words(phrases: list[tuple[str, str]]) -> set[str]:
    out: set[str] = set()
    for en, _ in phrases:
        for tok in _WORD_RE.findall(en.lower()):
            w = tok.strip("'-")
            if len(w) >= 4 and w not in _STOP:
                out.add(w)
    return out


def report_missing() -> None:
    """Print content words used in the new phrases that are not yet in `words`
    and not covered by the WORDS list above (authoring aid)."""
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in WORDS}
    all_phrases = [p for lst in PHRASES_BY_SCENE.values() for p in lst]
    missing = sorted(
        w for w in _content_words(all_phrases)
        if w not in existing and w not in covered
    )
    print(f"missing content words ({len(missing)}):")
    print(", ".join(missing))


def main() -> int:
    if "--missing-words" in sys.argv:
        report_missing()
        return 0

    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            w_existing.add(en.lower())
            w_added += 1

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
              "words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
