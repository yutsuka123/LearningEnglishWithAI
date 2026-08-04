# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for ONLINE MEETINGS / VIDEO CALLS, authored by
Claude.

Focus (フレーズ集の手薄な領域を補強): リモートワークで日常的に使う
オンライン会議・ビデオ通話の英語。入室/開始、音声・映像トラブル、画面共有、
ミュート、発言がかぶった時の対応、録画、終了、日程調整、チャット機能など。
既存の「ビジネス」「電話」シーンとは重ならない、ビデオ会議特有の定型表現を
体系的に強化する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_video_calls.py
      python scripts/add_video_calls.py --missing-words   # report only

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
    "オンライン会議・ビデオ通話": [
        # --- 入室・開始 ---
        ("Can everyone hear me okay?", "皆さん、私の声聞こえていますか？"),
        ("Let's give it a minute for everyone to join.", "皆さんが入室するまで少し待ちましょう。"),
        ("I think we're still waiting on a couple of people.", "まだ数名お待ちしている状況です。"),
        ("Shall we get started?", "そろそろ始めましょうか。"),
        ("Thanks everyone for joining today.", "本日はご参加ありがとうございます。"),
        ("Let's do a quick round of introductions.", "簡単に自己紹介をしましょう。"),
        ("I'll be recording this session, is that okay with everyone?", "本セッションを録画しますが、皆さんよろしいですか？"),
        # --- 音声・映像トラブル ---
        ("You're on mute.", "ミュートになっていますよ。"),
        ("Sorry, you're on mute.", "すみません、ミュートのままです。"),
        ("I think you're muted.", "ミュートになっているかもしれません。"),
        ("Could you unmute yourself?", "ミュートを解除していただけますか？"),
        ("Your audio is cutting out.", "音声が途切れています。"),
        ("You're breaking up a little.", "少し声が途切れ途切れです。"),
        ("The connection is really slow today.", "今日は接続がかなり遅いですね。"),
        ("I can't hear you very well.", "あまりよく聞こえません。"),
        ("Could you speak a bit louder?", "もう少し大きな声でお願いできますか？"),
        ("There's an echo on the line.", "音声がハウリングしています。"),
        ("Let me try turning my camera off to fix the connection.", "接続改善のためカメラをオフにしてみます。"),
        ("I'll try rejoining the meeting.", "会議に入り直してみます。"),
        ("Can you see my video?", "私の映像は見えていますか？"),
        ("Your video is frozen.", "映像がフリーズしています。"),
        ("Let's switch to audio only.", "音声のみに切り替えましょう。"),
        # --- 画面共有 ---
        ("Can everyone see my screen?", "皆さん、私の画面は見えていますか？"),
        ("Let me share my screen.", "画面を共有しますね。"),
        ("I'll stop sharing now.", "共有を止めますね。"),
        ("Could you zoom in a bit? It's hard to read.", "少し拡大していただけますか？読みづらいです。"),
        ("You're sharing the wrong window.", "共有している画面が違いますよ。"),
        ("I can only see a blank screen.", "こちらには何も表示されていません。"),
        ("Could you share your screen instead?", "代わりにあなたの画面を共有していただけますか？"),
        # --- 発言・進行 ---
        ("Sorry, go ahead.", "すみません、どうぞ続けてください。〔発言がかぶった時〕"),
        ("Sorry, we spoke at the same time.", "すみません、同時に話してしまいました。"),
        ("You go first.", "先にどうぞ。"),
        ("I'll let you finish your thought.", "お話を続けてください。"),
        ("Could I jump in for a second?", "少しよろしいでしょうか。〔割り込んで発言〕"),
        ("I'll pop my question in the chat.", "質問はチャットに書きますね。"),
        ("Let's take that offline.", "その話は会議の外で個別にしましょう。〔本題からそれた時〕"),
        ("Can we park that for now and come back to it later?", "それは一旦保留にして後で戻りましょう。"),
        ("I'll drop the link in the chat.", "リンクはチャットに貼っておきますね。"),
        ("Could you put that in the chat?", "それをチャットに書いていただけますか？"),
        ("I see a question in the chat from Alex.", "チャットにAlexさんから質問が来ています。"),
        ("Let's keep an eye on the time.", "時間を意識して進めましょう。"),
        ("We're running a bit over time.", "少し時間を超過しています。"),
        # --- 終了・録画・日程 ---
        ("I think that covers everything for today.", "本日はこれで以上かと思います。"),
        ("Let's wrap up here.", "この辺りで締めましょう。"),
        ("I'll send out the recording afterward.", "後ほど録画を共有します。"),
        ("I'll follow up with the meeting notes.", "議事録を後で送ります。"),
        ("Thanks everyone, see you next time.", "皆さんありがとうございました、また次回。"),
        ("Could we reschedule this meeting?", "この会議の日程を変更できますか？"),
        ("Does this time work for everyone?", "この時間で皆さん大丈夫ですか？"),
        ("I'll send a calendar invite.", "カレンダーの招待を送ります。"),
        ("Something's come up, can we push this back 15 minutes?", "急用ができたので15分遅らせられますか？"),
        ("I might be a few minutes late to the call.", "会議に数分遅れるかもしれません。"),
        ("Can we keep this meeting to 30 minutes?", "この会議は30分に収められますか？"),
        # --- 参加できない・接続に問題がある時 ---
        ("I'm having trouble joining the meeting.", "会議に入れなくて困っています。"),
        ("The link doesn't seem to be working.", "リンクがうまく機能していないようです。"),
        ("Could you resend the meeting link?", "会議のリンクを再送していただけますか？"),
        ("I'll dial in by phone instead.", "代わりに電話で参加します。"),
        ("My wifi keeps dropping.", "Wi-Fiが何度も切れます。"),
        ("Let me switch to my phone's hotspot.", "スマホのテザリングに切り替えます。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("mute", "ミュートにする・消音", "動詞", "Please mute yourself when not speaking.", "IT", "500"),
    ("unmute", "ミュートを解除する", "動詞", "Could you unmute yourself?", "IT", "500"),
    ("freeze", "フリーズする・固まる", "動詞", "The video keeps freezing.", "IT", "500"),
    ("lag", "遅延・ラグ", "名詞", "There's a lot of lag on this call.", "IT", "600"),
    ("bandwidth", "帯域幅・通信容量", "名詞", "Low bandwidth is causing the issue.", "IT", "700"),
    ("hotspot", "テザリング・ホットスポット", "名詞", "I'll use my phone's hotspot.", "IT", "600"),
    ("reschedule", "予定を変更する", "動詞", "Could we reschedule the call?", "ビジネス", "600"),
    ("attendee", "出席者・参加者", "名詞", "There are ten attendees today.", "ビジネス", "600"),
    ("facilitator", "進行役・ファシリテーター", "名詞", "She's the facilitator for this meeting.", "ビジネス", "700"),
    ("agenda", "議題・議事日程", "名詞", "Let's go through the agenda.", "ビジネス", "500"),
    ("breakout room", "分科会用の小部屋(ブレイクアウトルーム)", "名詞", "We'll split into breakout rooms.", "IT", "700"),
    ("dial in", "電話で会議に参加する", "動詞", "I'll dial in from my car.", "ビジネス", "600"),
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
