# ruff: noqa: E501  (data-heavy seed script: long phrase lines are fine)
"""「会話ニッチシーン追加」(scripts/add_conversation_niches.py)で新規シーン化を
見送った5件について、ユーザーから改めて「件数少なくてもよいので追加して
ほしい」との回答があったため(2026-09-08)、既存の近縁シーンに少量ずつ
追記するバッチ。新規シーン名は作らず、既存シーンにそのまま追加する。

投入前に各シーンの既存フレーズ全件をSELECTし、内容・文言が重複しないこと
を確認済み(詳細はdocs/TODO.md参照)。

対象5シーン(既存シーンへの追記、目安5〜10件ずつ):
  1. やんわり断る英語 (+8)
     「角を立てない断り方」の追加ケース: お金の貸し借り、忠告への婉曲的な
     不同意、過度な世話への遠慮、食事の勧めを断る、送迎の申し出を断る、
     役割を辞退する、シフト交代を断るなど、既存29件に無かった場面。
  2. クレーム・抗議の英語 (+7)
     消費者側の視点で、既存42件が薄かった具体的な場面(レストランの
     注文違い・冷めた料理、ホテルの未清掃、配送の未着・破損、長時間の
     保留、折り返し連絡が無い)を追加。
  3. TRPG・ボードゲーム英語 (+8)
     セッション中の実況的なやり取り: クリティカル成功/失敗、呪文詠唱、
     ダメージロール、判定の提案、ロールプレイ中のセリフ、ルール確認休憩
     など、既存29件がカバーしていなかった場面。
  4. アマチュア無線の交信 (+8・WebSearchで事実確認済み)
     QTH(所在地)・QRO(高出力)・QSB(フェージング)・DX(遠距離局)・
     POTA(Parks on the Air)・88(親しい間柄でのサインオフ)を追加。
     いずれも実在するQ符号・用語で、WebSearchで裏取り済み:
       - QTH = "What is your location?" (hamradioprep.com等)
       - QRO = high power (QRPの対義語)
       - QSB = signal fading
       - DX  = distant station (telegraphic shorthand for "distance")
       - POTA = Parks on the Air、activator/hunterの役割がある賞制度
       - 88 = "love and kisses"、73より親密な間柄(夫婦・親しい友人)の
         サインオフとして使われる
     また「over and out」は実際には矛盾した誤用(over=応答待ち,
     out=交信終了で、本来同時に使わない)という事実も、誤用への注意喚起
     として1件追加(Hollywood由来の誤解であり、訓練を受けた運用者は
     使わないという裏取り済みの事実)。
  5. アニメ・海外ファン文化 (+8)
     「アニメ考察トーク」寄りの表現(伏線・象徴・再解釈・テーマの深読み
     など)を追加。既存の25件は感想・実況寄りの表現が中心だったため、
     より分析的な言い回しを補強する。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased).

Run:  python scripts/add_conversation_niches_addendum.py

仕上げ:
  python scripts/relevel_phrases.py
  python scripts/import_phrase_details.py \
      scripts/data/conversation_niches_addendum_details.json
  python scripts/build_audio.py --words 0 --phrases 60
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "やんわり断る英語": [
        ("I don't feel comfortable lending money, even to friends.", "申し訳ないけど、友人であってもお金の貸し借りはしたくないんだ。"),
        ("I'd rather not get involved in this one, if that's okay.", "できればこの件には関わりたくないのですが、よろしいでしょうか。"),
        ("I appreciate the suggestion, but I think I'll do it my own way.", "ご提案はありがたいのですが、自分のやり方でやろうと思います。"),
        ("That's really kind, but I couldn't possibly impose on you like that.", "お気持ちはありがたいのですが、そこまでお世話になるわけにはいきません。"),
        ("I'm full, thanks, but it was delicious.", "もうお腹いっぱいです、ありがとう、とても美味しかったです。"),
        ("Thanks for offering a ride, but I've already got a way home.", "送っていただけるとのことでありがとうございます、でも帰る手段はもう確保しています。"),
        ("I don't think I'm the right fit for that role, but I appreciate you thinking of me.", "その役目には自分は向いていないと思いますが、声をかけていただきありがとうございます。"),
        ("I'd prefer not to switch shifts this time, sorry.", "今回はシフトの交代はご遠慮したいです、すみません。"),
    ],
    "クレーム・抗議の英語": [
        ("This isn't what I ordered.", "これは注文したものと違います。"),
        ("My food came out cold.", "料理が冷めた状態で出てきました。"),
        ("The room wasn't cleaned before we checked in.", "チェックイン前に部屋が掃除されていませんでした。"),
        ("My package never arrived, even though it shows as delivered.", "配達済みと表示されているのに、荷物が届いていません。"),
        ("The item arrived damaged.", "商品が破損した状態で届きました。"),
        ("I've been on hold for over twenty minutes.", "もう20分以上保留にされています。"),
        ("Nobody got back to me like you said they would.", "折り返し連絡すると言われたのに、誰からも連絡がありませんでした。"),
    ],
    "TRPG・ボードゲーム英語": [
        ("Natural twenty! Critical hit!", "ナチュラル20！クリティカルヒットだ！"),
        ("That's a critical fail, unfortunately.", "残念ながらクリティカルフェイルです。"),
        ("I cast fireball on the group of goblins.", "ゴブリンの群れにファイアーボールを唱えます。"),
        ("Roll for damage.", "ダメージロールをしてください。"),
        ("Can I make an insight check to see if he's lying?", "彼が嘘をついているか、〈看破〉判定をしてもいいですか。"),
        ("Let's narrate this out instead of rolling for it.", "ここはロールせずに描写で進めましょう。"),
        ("In character, I'd say something like this...", "キャラクターとして言うなら、こんな感じかな…"),
        ("Let's take five to look up that rule.", "そのルールを調べるために5分休憩しましょう。"),
    ],
    "アマチュア無線の交信": [
        ("What's your QTH?", "QTH(所在地)はどちらですか。"),
        ("My QTH is just outside Denver, Colorado.", "私のQTHはコロラド州デンバー郊外です。"),
        ("I need to run QRO tonight to punch through this noise.", "今夜はこのノイズを突破するためQRO(高出力)で運用する必要があります。"),
        ("You're fading in and out — a bit of QSB tonight.", "信号が出たり消えたりしていますね、今夜は少しQSB(フェージング)があります。"),
        ("Please don't say 'over and out' — pick one or the other.", "「over and out」は言わないでください、どちらか一方にしてください。"),
        ("That's a DX station, all the way from New Zealand.", "あれはDX局(遠距離局)ですね、ニュージーランドからです。"),
        ("I'm heading out to activate a park for POTA this weekend.", "今週末、POTA(パークス・オン・ジ・エア)のため公園から運用してきます。"),
        ("88 to you and the family — talk again soon.", "あなたとご家族に88(愛を込めて)、また話しましょう。"),
    ],
    "アニメ・海外ファン文化": [
        ("The foreshadowing in the first episode was so subtle, I missed it completely.", "第1話の伏線があまりに巧妙で、完全に見逃してた。"),
        ("This arc is loaded with symbolism if you look closely.", "よく見ると、この編は象徴表現だらけだね。"),
        ("I think this theme is more nuanced than people give it credit for.", "このテーマ、みんなが思っているより奥が深いと思う。"),
        ("The way they handled that moral dilemma was genuinely thought-provoking.", "あの倫理的ジレンマの描き方、本当に考えさせられた。"),
        ("On rewatch, so many small details make sense now.", "見返すと、細かい部分の意味が今になって分かる。"),
        ("This episode recontextualizes everything we thought we knew.", "このエピソードで、これまでの前提が全部覆される。"),
        ("The visual metaphor in that scene was incredible.", "あのシーンの視覚的な比喩表現は素晴らしかった。"),
        ("I don't think the pacing issues undercut the character work, honestly.", "正直、テンポの問題がキャラクター描写の良さを損なっているとは思わない。"),
    ],
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

        added = skipped = 0
        per_scene: dict[str, int] = {}
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in existing:
                    skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                existing.add(en.lower())
                added += 1
                per_scene[scene] = per_scene.get(scene, 0) + 1
        conn.commit()

    print(f"phrases: +{added} (skipped {skipped})")
    for scene, n in per_scene.items():
        print(f"  {scene}: +{n}")
    with db() as conn:
        print("total phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
