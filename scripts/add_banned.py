# ruff: noqa: E501  (data-heavy seed script)
"""Add awareness-only "禁止用語" (strong profanity / slurs) and a safe
"和製英語・誤用注意" set, authored by Claude — no app/OpenAI API calls.

Policy: this is for COMPREHENSION & AVOIDANCE (movies, accidental offense),
never encouragement. Slurs are written in censored form with a clear "never
use" warning. Common profanity is included with its meaning and a strong
caution. Banned items carry scene '禁止用語（注意喚起）' (phrases) or
domain '禁止用語' (words) so the UI toggle can hide them from view and quizzes.

Run:  python scripts/add_banned.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

BANNED_SCENE = "禁止用語（注意喚起）"
WASEI_SCENE = "和製英語・誤用注意"
BANNED_DOMAIN = "禁止用語"

# --- banned phrases (toggle-hidden by default) ------------------------------
# Movie/drama expressions that are vulgar or aggressive. Translations include a
# 〔...〕 caution so the learner understands the register and the danger.

PHRASES_BANNED: list[tuple[str, str]] = [
    ("What the fuck?", "一体何なんだ？〔最強クラスの罵り。極めて下品。公の場で厳禁〕"),
    ("Fuck you.", "くたばれ。〔最大級の侮辱。絶対に使わない〕"),
    ("Fuck off.", "失せろ。〔強い侮辱・拒絶。下品〕"),
    ("Shut the fuck up.", "黙れ。〔非常に攻撃的。喧嘩沙汰になる〕"),
    ("That's bullshit.", "でたらめだ。〔下品な俗語。フォーマルでは厳禁〕"),
    ("Holy shit!", "うわ、まじか！〔驚きの下品な俗語〕"),
    ("Oh shit.", "しまった／くそ。〔下品。改まった場では避ける〕"),
    ("I don't give a shit.", "知ったことか。〔無関心を乱暴に表す。下品〕"),
    ("You're a piece of shit.", "お前は人間のクズだ。〔重い侮辱〕"),
    ("Son of a bitch.", "この野郎／くそったれ。〔強い罵り。映画頻出だが侮辱〕"),
    ("You bitch.", "この性悪女。〔女性への強い侮辱語。極めて失礼〕"),
    ("Kiss my ass.", "ふざけるな／お断りだ。〔挑発的・下品〕"),
    ("Get your ass over here.", "さっさと来い。〔乱暴・下品〕"),
    ("What a dick.", "最低なやつだ。〔侮辱・下品〕"),
    ("Don't be an asshole.", "嫌なやつになるな。〔侮辱・下品〕"),
    ("Piss off.", "失せろ。〔英国系の下品な拒絶〕"),
    ("You piss me off.", "お前にはむかつく。〔下品・攻撃的〕"),
    ("Screw you.", "くたばれ。〔下品な侮辱〕"),
    ("Go to hell.", "地獄に落ちろ。〔強い呪いの言葉〕"),
    ("Damn it!", "くそっ！〔軽めの罵り。Godがらみで冒涜的。フォーマルでは避ける〕"),
    ("Goddamn it.", "ちくしょう。〔Godを使う冒涜的表現。信心深い人に不快〕"),
    ("Damn you.", "お前なんか。〔呪い気味の強い表現〕"),
    ("Get the hell out of here.", "とっとと出て行け。〔乱暴〕"),
    ("Bite me.", "うるさい／ほっとけ。〔挑発的スラング〕"),
    ("Bastard.", "畜生／くそ野郎。〔侮辱語〕"),
    ("You're full of crap.", "お前の言うことはでたらめだ。〔下品な俗語〕"),
    ("That sucks ass.", "最悪だ。〔強調した下品な俗語〕"),
    ("Frigging hell.", "ったく、もう。〔fucking の婉曲だが粗野〕"),
    ("Shut your mouth.", "黙れ。〔乱暴・攻撃的〕"),
    ("Don't fuck with me.", "なめるなよ。〔脅し・最も下品〕"),
    # Slurs — CENSORED, listed only so learners recognize & never use them.
    ("Never say the N-word (n*****).", "黒人への最悪の差別語。〔絶対に口にしない。歴史的に深く傷つける〕"),
    ("Avoid the F-slur (f*****).", "同性愛者への差別語。〔使用厳禁。深く侮辱する〕"),
    ('Don\'t call someone "retarded".', "知的障害を指す差別語。〔現在は強い侮辱。使わない〕"),
    ('"Jap" is a slur for Japanese.', "日本人への蔑称。〔Japanese と言う。Jap は侮辱〕"),
]

# --- safe but important: 和製英語 / dangerous misuse / pronunciation traps ---
# These are NOT offensive themselves, so they stay visible (normal scene).

PHRASES_WASEI: list[tuple[str, str]] = [
    ("I work part-time.", "「アルバイト」は独語由来の和製語。英語は part-time job。"),
    ("My laptop is broken.", "「ノートパソコン」は和製。英語は laptop。"),
    ("I'd like to file a complaint.", "「クレーム」は complaint。claim は『主張する』の意。"),
    ("She is slim.", "体型は slim/slender。「スマート(smart)」は英語では『賢い』。"),
    ("I'm so excited!", "「テンションが高い」は和製。英語は excited/energetic。tension は緊張。"),
    ("He cheated on the test.", "「カンニング」は和製。英語は cheating。cunning は『ずる賢い』。"),
    ("That's a huge mansion.", "mansion は『豪邸』。日本のマンションは apartment/condo。"),
    ("Don't be so naive.", "英語の naive は『世間知らず』で失礼になり得る。ナイーブ(繊細)とは別。"),
    ("It's custom-made.", "「オーダーメイド」は和製。英語は custom-made/made-to-order。"),
    ("Where is the restroom?", "「トイレ」は restroom が上品。toilet は便器寄り、WCは古い。"),
    ("Oh my goodness!", "「Oh my God」は信心深い人に不快なことも。goodness/gosh が無難。"),
    ("Please have a seat.", "sit と seat の母音に注意。短すぎると下品語に聞こえることがある。"),
    ("Let's go to the beach.", "beach の長母音に注意。短いと bitch に聞こえてしまう。"),
    ("I'd like some rice.", "rice と lice(シラミ)。R と L の区別に注意。"),
    ("Could I get a fork?", "fork の発音に注意。母音/ r が崩れると下品語に近づく。"),
    ("I can do it myself.", "can't の t を落とすと can と紛れ、肯定否定を誤解されやすい。"),
    ("He is an elite runner.", "「エリート」は ee-LEET の発音。日本語読みでは通じにくい。"),
    ("This service is free.", "「フリーサイズ」は和製→one-size-fits-all。free は『無料・自由』。"),
    ("I'll have a coffee.", "「モーニングサービス」は和製。英語は breakfast set など。"),
    ("She is pregnant.", "妊娠は pregnant。『ドンマイ(don't mind)』も和製で英語では不自然。"),
    ("Let me give you a high five!", "ハイタッチは和製。英語は high five。"),
    ("I drive an automatic car.", "「ハンドル」は steering wheel。handle は『取っ手・扱う』。"),
    ("Plug it into the outlet.", "「コンセント」は和製。英語は outlet/socket。"),
    ("He's a baseball player.", "「ナイター」は和製。英語は night game。"),
    ("Take a photo.", "「ピント」は focus。「シャッターチャンス」も和製。"),
]

# --- banned words (domain '禁止用語', toggle-hidden) -------------------------

WORDS_BANNED: list[tuple[str, str, str, str]] = [
    ("damn", "(罵り)くそっ／ひどい", "Damn it! 〔軽い罵り。冒涜的でフォーマルでは避ける〕"),
    ("hell", "(罵りで)一体／くそ", "What the hell? 〔いらだち。丁寧な場では不適切〕"),
    ("crap", "くそ・がらくた", "That's a load of crap. 〔下品な俗語〕"),
    ("shit", "(俗)くそ", "Oh shit. 〔強い下品語。改まった場で厳禁〕"),
    ("ass", "尻／(侮辱)最低なやつ", "He's a pain in the ass. 〔下品〕"),
    ("asshole", "(侮辱)最低なやつ", "Don't be an asshole. 〔強い侮辱・下品〕"),
    ("bitch", "(侮辱)性悪な女／文句を言う", "Stop bitching. 〔極めて失礼。女性への侮辱〕"),
    ("bastard", "(侮辱)くそ野郎", "You bastard! 〔強い侮辱語〕"),
    ("bullshit", "でたらめ・たわごと", "That's bullshit. 〔下品な俗語〕"),
    ("dick", "(俗)男性器／嫌なやつ", "Stop being a dick. 〔下品・侮辱〕"),
    ("prick", "(俗・侮辱)嫌なやつ", "What a prick. 〔下品・侮辱〕"),
    ("jerk", "(侮辱)嫌なやつ", "He's such a jerk. 〔軽めの侮辱だが失礼〕"),
    ("moron", "(侮辱)まぬけ", "Don't be a moron. 〔侮辱〕"),
    ("idiot", "(侮辱)ばか", "You idiot! 〔相手を傷つける侮辱〕"),
    ("piss", "(俗)小便／激怒させる", "You piss me off. 〔下品・攻撃的〕"),
    ("screw", "(俗)くたばれ等の罵りに使う", "Screw it. 〔下品な用法〕"),
    ("damn it", "(罵り)くそっ", "Damn it, I missed the train. 〔冒涜的〕"),
    ("goddamn", "(強調・罵り)いまいましい", "This goddamn machine. 〔Godを使う冒涜的表現〕"),
    ("slut", "(侮辱)ふしだらな女", "—（女性への強い侮辱語。〔絶対に使わない〕）", ),
    ("whore", "(侮辱)売春婦／ののしり", "—（極めて侮辱的。〔絶対に使わない〕）"),
    ("fuck", "(最も強い俗語)罵り全般", "—（英語最強のタブー語。〔まず使わない。意味の理解のみ〕）"),
    ("freaking", "(婉曲)いまいましい", "It's freaking cold. 〔fucking の婉曲。粗野〕"),
    ("the N-word (n*****)", "黒人への最悪の差別語(伏字)", "—（〔絶対に口にしない差別語〕）"),
    ("the F-slur (f*****)", "同性愛者への差別語(伏字)", "—（〔使用厳禁の差別語〕）"),
    ("retard", "(差別)知的障害者への蔑称", "—（〔現在は強い侮辱。使わない〕）"),
    ("Jap", "(蔑称)日本人への侮辱語", "Say 'Japanese', not 'Jap'. 〔Jap は蔑称〕"),
]


def main() -> int:
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
        for scene, items in (
            (BANNED_SCENE, PHRASES_BANNED),
            (WASEI_SCENE, PHRASES_WASEI),
        ):
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
        for row in WORDS_BANNED:
            en, ja, ex = row[0], row[1], row[2]
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, "", ex, BANNED_DOMAIN, "700"),
            )
            w_existing.add(en.lower())
            w_added += 1

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print(
            "禁止フレーズ:",
            conn.execute(
                "SELECT COUNT(*) FROM phrases WHERE scene LIKE '禁止%'"
            ).fetchone()[0],
            "/ 禁止単語:",
            conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain = ?", (BANNED_DOMAIN,)
            ).fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
