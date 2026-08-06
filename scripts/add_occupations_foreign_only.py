# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add occupations that are common in Europe/North America but rarely (or
not) seen as professions in modern Japan, authored by Claude
(2026-08-06・ユーザー要望: 「現代の欧米圏には存在するが、現代日本には
あまり見られない・馴染みのない職業」を domain='職業' に約25〜30語追加).

既存の domain='職業'(53件)は actuary / bartender / beekeeper /
firefighter / surveyor など、日欧米問わず一般的な職業や、伝統工芸系の
職業(blacksmith, cooper, tanner, wheelwright など)が中心だった。

このスクリプトはそこに、アメリカ・ヨーロッパの社会制度・文化に根差した
ために、日本ではほぼ見られない・職業として確立していない語彙を追加する:

- 宗教関連の専業聖職者(pastor, priest) — 日本では専業として一般的でない
- 保釈金制度に伴う職業(bail bondsman, bounty hunter, repo man) —
  そもそも日本に同等の制度がない
- 私立探偵(private investigator)・訴訟社会特有の職業(personal injury
  lawyer, process server) — 日本では制度・慣習が大きく異なる
- 広大な国立公園・牧場文化に伴う職業(park ranger, cattle rancher,
  game warden, crop duster pilot, rodeo clown)
- 郡(county)単位の自治制度に伴う職業(county sheriff)
- 不動産売買の慣習に伴う職業(home inspector)
- 自動車社会特有の職業(tow truck driver, repo man)
- ツアー文化・エンタメ業界特有の職業(roadie, stuntman, talent agent,
  televangelist, casino dealer, valet parking attendant)
- 個人主義的なキャリア支援文化(life coach)
- 州によってはオンライン認定だけで誰でもなれる結婚式の司式者
  (wedding officiant)

domain は既存の '職業' に統一(全て名詞)。level は
["300-","300","350","400","450","500","550","600","650","700","750",
"800","850","900","950","990","990+"] のスケールに沿って 500〜800 の
範囲で付与した。example は米・英・独など、その職業が実際に見られる
国・地域が伝わるよう具体的な地名(Texas, Montana, Yellowstone, Las
Vegas, Kansas, Beverly Hills, Berlin, Rome など)を含めた。

事前に既存DB(words ~8300件)を domain 横断で全件チェックし、rabbi /
imam(宗教)、lifeguard / ski patrol(アウトドア・レジャー)、
sommelier(料理)、notary public(法律)、lobbyist(政治)が既に別
domain に存在することを確認済み。これらは意味的に重複するためこの
リストから除外している。また domain='職業' 内の既存53語(undertaker
など)とも重複しないことを確認済み。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_foreign_only.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("rodeo clown", "ロデオクラウン(落馬した乗り手を牛から守る道化師役)", "名詞", "The rodeo clown distracted the bull so the fallen cowboy could escape safely, a common sight at rodeos across Texas.", "職業", "600"),
    ("cattle rancher", "牧場経営者(牛の放牧・畜産を営む)", "名詞", "Her family has worked as cattle ranchers on the same land in Montana for four generations.", "職業", "600"),
    ("bounty hunter", "バウンティハンター(保釈中に逃亡した被告人を捕らえ報奨金を得る)", "名詞", "In several U.S. states, a licensed bounty hunter can track down and arrest a bail jumper.", "職業", "700"),
    ("private investigator", "私立探偵", "名詞", "He hired a private investigator to look into the insurance claim, a common practice in the United States.", "職業", "650"),
    ("pastor", "教会の牧師(プロテスタント教会)", "名詞", "The pastor delivers a sermon every Sunday morning at the local Baptist church.", "職業", "600"),
    ("priest", "司祭(カトリック教会などの聖職者)", "名詞", "A Catholic priest in Rome hears confessions every afternoon.", "職業", "550"),
    ("county sheriff", "郡保安官", "名詞", "The county sheriff and his deputies patrol the rural areas outside the city limits.", "職業", "700"),
    ("home inspector", "住宅検査士(売買前に建物の状態を点検する)", "名詞", "Before closing on the house, the buyers hired a home inspector to check the roof and foundation.", "職業", "700"),
    ("personal injury lawyer", "個人傷害専門弁護士", "名詞", "After the car accident, she consulted a personal injury lawyer whose billboard she'd seen along the highway.", "職業", "750"),
    ("summer camp counselor", "サマーキャンプ指導員", "名詞", "Many American teenagers spend their summer working as a camp counselor at a lakeside camp.", "職業", "600"),
    ("park ranger", "国立公園レンジャー", "名詞", "A park ranger at Yellowstone warned the tourists to stay away from the bison.", "職業", "600"),
    ("roadie", "ツアースタッフ(バンドの機材運搬・設営を担当)", "名詞", "The roadies loaded the amplifiers onto the tour bus after the concert in Berlin.", "職業", "650"),
    ("stuntman", "スタントマン", "名詞", "The stuntman performed the dangerous car chase scene instead of the lead actor.", "職業", "550"),
    ("casino dealer", "カジノディーラー", "名詞", "The casino dealer shuffled the cards at the blackjack table in Las Vegas.", "職業", "600"),
    ("crop duster pilot", "農薬散布パイロット", "名詞", "A crop duster pilot flew low over the wheat fields of Kansas, spraying pesticide.", "職業", "750"),
    ("repo man", "車両回収代行人(ローン滞納車を回収する)", "名詞", "The repo man towed away the truck after the owner missed three loan payments.", "職業", "800"),
    ("bail bondsman", "保釈保証人", "名詞", "Her brother called a bail bondsman to post bail so he could get out of the county jail.", "職業", "800"),
    ("chimney sweep", "煙突掃除人", "名詞", "In parts of England, a chimney sweep still climbs onto the roof to clean out the soot.", "職業", "650"),
    ("life coach", "ライフコーチ", "名詞", "She hired a life coach to help her set career goals and build better habits.", "職業", "600"),
    ("televangelist", "テレビ伝道師", "名詞", "The televangelist preached to millions of viewers on Sunday morning television.", "職業", "800"),
    ("wedding officiant", "結婚式の司式者(州によっては一般人もオンライン認定でなれる)", "名詞", "In many U.S. states, a friend can become an ordained wedding officiant online and legally marry the couple.", "職業", "750"),
    ("game warden", "野生生物監視員(密猟の取り締まりなどを行う)", "名詞", "The game warden fined the hunters for shooting deer outside the legal season.", "職業", "750"),
    ("tow truck driver", "レッカー車運転手", "名詞", "The tow truck driver hooked up the stalled car on the interstate and pulled it to the shop.", "職業", "550"),
    ("valet parking attendant", "バレットパーキング係", "名詞", "The valet parking attendant parked our car in front of the restaurant in Beverly Hills.", "職業", "600"),
    ("process server", "訴訟関係文書の送達人", "名詞", "A process server delivered the lawsuit papers directly to the defendant's front door.", "職業", "800"),
    ("mortgage loan officer", "住宅ローン融資担当者", "名詞", "The mortgage loan officer at the bank helped them calculate their monthly payments.", "職業", "700"),
    ("talent agent", "芸能エージェント(俳優等の仕事獲得を代行する)", "名詞", "Her talent agent in Los Angeles negotiated the contract for the new film role.", "職業", "700"),
]


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
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

    print(f"words:   +{w_added} (skipped {w_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
