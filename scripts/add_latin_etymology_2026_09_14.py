# ruff: noqa: E501
"""語源(ラテン語)新ドメイン(2026-09-14・authored by Claude)。
英単語の中でもラテン語の語源が意外・面白いものだけを選んで集めた
初回バッチ(53語)。docs/TODO.md記載の2026-09-13ユーザー提起の
企画「語源(特にラテン語)をテーマにした語彙拡充」の第一弾。

選定方針:
- 「いかにもラテン語」に見える語(aquarium等)ではなく、日常的に使う
  のに語源を知らない人が多い語を優先(例: salary/salarium=塩代)。
- 全語源をEtymonline (etymonline.com)でWebFetch照合済み。俗説と
  判明した語(genuine「膝の上での認知」説、sincere「without wax」説、
  sabotage「木靴」説等)は候補から除外。testifyは「証人」線のみ扱い、
  睾丸(testis)との関連への言及はEtymonlineが"groundless modern
  inventions"と明記しているため意図的に含めていない。
- 既存DB(16,391語)との重複を個別に確認して除外(salad, company,
  muscle, disaster, candidate, calculate, vaccine, focus,
  hospitality等、想定より多数の「いかにもラテン語」語が既存だった)。

No app / OpenAI API calls — hand-written, inserted directly into
SQLite. Duplicates skipped by english (lowercased) against the
full live `words` table.

Run:  python scripts/add_latin_etymology_2026_09_14.py
(このスクリプトは人間のレビュー後に実行する想定のため、
ドラフト作成時点ではまだ実行しない。)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 塩(sal)から生まれた語 (2) ---
    ('salary', '雇用主から従業員へ、通常は月単位など定期的に支払われる給与。時給ではなく一定期間ごとに支払われる報酬を指すことが多い。', '名詞', 'She negotiated a higher salary before accepting the job offer.', '語源(ラテン語)', '500'),
    ('sausage', '刻んだ、または挽いた肉に香辛料などで味付けし、腸などの皮に詰めた食品。', '名詞', 'The chef grilled sausages for the outdoor barbecue party.', '語源(ラテン語)', '500'),
    # --- 「見る」videre/specere系 (3) ---
    ('envy', '他人が持っているものや才能を、うらやましく思う気持ち。', '名詞', "She couldn't hide her envy when her colleague got the promotion instead of her.", '語源(ラテン語)', '500'),
    ('visa', '外国への入国や滞在を許可する、公的機関による証明・査証。', '名詞', 'You need a visa to work legally in this country.', '語源(ラテン語)', '500'),
    ('despise', '強い軽蔑の気持ちを持って、見下すように嫌うこと。', '動詞', 'He despised dishonesty in any form, especially in business dealings.', '語源(ラテン語)', '700'),
    # --- 「跳ぶ」salire系 (2) ---
    ('insult', '相手を侮辱する、無礼な言動で傷つけること。', '動詞', "He didn't mean to insult his colleague, but his comment came across as rude.", '語源(ラテン語)', '500'),
    ('salient', '他と比べて際立って目立つ、顕著な様子。', '形容詞', "Let's focus on the most salient points of the report.", '語源(ラテン語)', '800'),
    # --- 「運ぶ」ferre系 (3) ---
    ('translate', 'ある言語を別の言語に置き換えること。転じて、あるものを別の形式に変換すること。', '動詞', 'This app can translate spoken English into Japanese instantly.', '語源(ラテン語)', '500'),
    ('suffer', '苦痛や損害などを経験する、耐え忍ぶこと。', '動詞', 'Small businesses suffered greatly during the economic downturn.', '語源(ラテン語)', '500'),
    ('confer', '意見を交換するために話し合うこと。または、称号や権利などを正式に与えること。', '動詞', 'The lawyers conferred with their client before entering the courtroom.', '語源(ラテン語)', '700'),
    # --- 「向ける」vertere系 (4) ---
    ('advertise', '商品やサービスなどを広く知らせ、宣伝すること。', '動詞', 'The company plans to advertise its new smartphone on social media.', '語源(ラテン語)', '500'),
    ('controversy', '意見が鋭く対立する、激しい論争や物議。', '名詞', 'The new policy sparked controversy among employees and shareholders alike.', '語源(ラテン語)', '700'),
    ('avert', '危険や好ましくない事態を未然に防ぐ、または目や顔をそらすこと。', '動詞', 'Quick action by the crew helped avert a major accident.', '語源(ラテン語)', '750'),
    ('divert', '本来の進路や方向、注意などを別のほうへそらすこと。', '動詞', 'The airline had to divert the flight to a nearby airport due to bad weather.', '語源(ラテン語)', '700'),
    # --- 「つかむ」capere系 (3) ---
    ('occupy', '場所や時間、地位などを占めること。または軍隊などが領土を占領すること。', '動詞', 'The marketing department occupies the entire third floor of the building.', '語源(ラテン語)', '600'),
    ('deceive', '人をだます、欺くこと。', '動詞', "The salesman deceived customers by hiding the product's defects.", '語源(ラテン語)', '600'),
    ('susceptible', '影響や作用を受けやすい、感染しやすい様子。', '形容詞', 'Elderly people are more susceptible to complications from the flu.', '語源(ラテン語)', '800'),
    # --- 「書く」scribere系 (3) ---
    ('prescribe', '医師が薬や治療法を指示すること。または、規則やルールを定めること。', '動詞', 'The doctor prescribed antibiotics for her throat infection.', '語源(ラテン語)', '700'),
    ('postscript', '手紙や文書の本文を書き終えた後に付け加える一文。追伸。', '名詞', 'In the postscript, she added a quick note about the upcoming holiday.', '語源(ラテン語)', '700'),
    ('manuscript', '手書きされた文書。または、出版前の原稿。', '名詞', 'The publisher received hundreds of manuscripts from aspiring authors last year.', '語源(ラテン語)', '700'),
    # --- 「量る・吊るす」pendere系 (2) ---
    ('suspend', '一時的に活動や効力を止めること。または、物を高い位置からぶら下げること。', '動詞', 'The airline suspended flights to the region due to safety concerns.', '語源(ラテン語)', '700'),
    ('pension', '退職後や高齢になった人に対して、定期的に支払われる年金。', '名詞', 'He plans to retire early and live on his pension.', '語源(ラテン語)', '600'),
    # --- 「証言する」testis系 (2) ---
    ('protest', '不満や反対の意思を公に強く表明すること。', '動詞', 'Local residents protested against the construction of the new highway.', '語源(ラテン語)', '500'),
    ('testify', '証言する、事実を裏付ける証拠として述べること。', '動詞', 'The witness was called to testify in court about what she had seen.', '語源(ラテン語)', '700'),
    # --- 「警告する」monere系 (2) ---
    ('money', '商品やサービスの取引に使われる、貨幣や紙幣などの支払い手段。', '名詞', 'She saved enough money to travel around Europe for a month.', '語源(ラテン語)', '400'),
    ('premonition', '何か悪いことが起こりそうだという、事前の予感や虫の知らせ。', '名詞', 'She had a strange premonition that something was wrong before she got the call.', '語源(ラテン語)', '800'),
    # --- 鳥占い・ローマの宗教儀礼系 (4) ---
    ('sinister', '邪悪な、不吉な、何か悪いことが起こりそうな雰囲気を持つ様子。', '形容詞', 'There was something sinister about the way he avoided answering the question.', '語源(ラテン語)', '700'),
    ('dexterity', '手先や体の動きが機敏で器用であること。転じて、物事を巧みに処理する能力。', '名詞', 'Surgeons need great manual dexterity to perform such delicate operations.', '語源(ラテン語)', '800'),
    ('inaugurate', '正式な儀式を行って(役職に)就任させる、または(建物・制度などを)開始・発足させること。', '動詞', 'The new president will be inaugurated next January.', '語源(ラテン語)', '800'),
    ('desire', '何かを強く望む、切望すること。', '動詞', 'Many young professionals desire more flexibility in their working hours.', '語源(ラテン語)', '500'),
    # --- ローマの制度・娯楽・風習系 (6) ---
    ('decimate', '多数のものや人を大幅に減らす、壊滅的な被害を与えること。', '動詞', 'The economic crisis decimated small businesses across the region.', '語源(ラテン語)', '800'),
    ('sinecure', 'ほとんど職務や責任を伴わないのに、報酬や地位だけが得られる仕事や役職。', '名詞', 'Critics called the newly created position a sinecure with no real responsibilities.', '語源(ラテン語)', '900'),
    ('ovation', '熱狂的な拍手喝采。特にスタンディングオベーションのような、大勢が総立ちで送る称賛。', '名詞', 'The singer received a standing ovation at the end of her concert.', '語源(ラテン語)', '750'),
    ('circus', '曲芸や動物の芸などを見せる、移動式の娯楽興行。または、円形の競技場・広場。', '名詞', 'The children were thrilled to watch the acrobats perform at the circus.', '語源(ラテン語)', '400'),
    ('arena', 'スポーツの試合やコンサートなどが行われる、観客席に囲まれた競技場・会場。転じて、活動や競争が行われる分野。', '名詞', 'The new arena can seat up to twenty thousand spectators for basketball games.', '語源(ラテン語)', '500'),
    ('cereal', '小麦や米、とうもろこしなど、食用となる穀物。または、それを加工した朝食用の食品。', '名詞', 'He usually eats a bowl of cereal with milk for breakfast.', '語源(ラテン語)', '400'),
    # --- その他の単独語源 (17) ---
    ('companion', '行動や時間を共にする相手、仲間。旅・生活・趣味などを一緒にする人を指すことが多い。', '名詞', 'The elderly man adopted a dog to be his companion after retirement.', '語源(ラテン語)', '500'),
    ('incandescent', '熱せられて白く光り輝いている様子。転じて、感情や才能などが強烈で目もくらむほどであることを表す。', '形容詞', 'The old incandescent light bulbs waste a lot of energy as heat.', '語源(ラテン語)', '800'),
    ('fascinate', '強く興味を引きつけ、目が離せないほど夢中にさせること。', '動詞', 'The lecture on ancient Roman history fascinated the entire audience.', '語源(ラテン語)', '600'),
    ('trivial', '取るに足らない、些細でどうでもいいと感じられる様子。', '形容詞', "Don't waste the meeting arguing over such a trivial detail.", '語源(ラテン語)', '600'),
    ('adult', '成長し切った人、成人。十分に成熟した状態にあることを指す。', '名詞', 'This amusement park charges a different admission fee for adults and children.', '語源(ラテン語)', '400'),
    ('hostile', '敵意を持った、対立的で好戦的な様子。', '形容詞', 'The two companies have a hostile relationship due to a long-standing lawsuit.', '語源(ラテン語)', '600'),
    ('curriculum', '学校や大学などで体系的に組まれた、学習内容や科目の全体的な計画。', '名詞', 'The university revised its curriculum to include more practical training.', '語源(ラテン語)', '700'),
    ('courier', '手紙や荷物などを届ける配達人、急使。', '名詞', 'The company uses a courier service to deliver important documents overnight.', '語源(ラテン語)', '600'),
    ('compromise', '対立する双方が互いに譲歩し合って成立させる合意、妥協案。', '名詞', 'After hours of negotiation, both sides finally reached a compromise.', '語源(ラテン語)', '700'),
    ('amateur', '職業としてではなく、趣味や愛好として物事に取り組む人。素人、愛好家。', '名詞', 'She is an amateur photographer who sells her work on weekends only.', '語源(ラテン語)', '600'),
    ('cancel', '予定や契約などを取り消すこと。線を引いて無効にすることから。', '動詞', 'We had to cancel the meeting because half the team was out sick.', '語源(ラテン語)', '400'),
    ('explode', '爆発する、激しい音を立てて破裂すること。転じて、感情などが急に爆発すること。', '動詞', 'The old boiler exploded, causing significant damage to the factory.', '語源(ラテン語)', '500'),
    ('applaud', '拍手をして称賛すること。転じて、行為や決定などを称賛し支持すること。', '動詞', 'The audience applauded loudly when the pianist finished her performance.', '語源(ラテン語)', '600'),
    ('entertain', '人を楽しませる、もてなすこと。または、考えや提案などを心にとどめて検討すること。', '動詞', 'The comedian entertained the crowd with his witty jokes.', '語源(ラテン語)', '500'),
    ('pecuniary', '金銭に関する、金銭上の。', '形容詞', 'The lawsuit resulted in significant pecuniary damages for the company.', '語源(ラテン語)', '850'),
    ('abundant', '十分すぎるほど豊富にある、あり余るほどの様子。', '形容詞', 'The region has abundant natural resources, including oil and natural gas.', '語源(ラテン語)', '600'),
    ('inundate', '大量のもので圧倒する、押し寄せられること。本来は「水浸しにする」の意味。', '動詞', 'The customer service team was inundated with complaints after the system failure.', '語源(ラテン語)', '750'),
]


def main() -> None:
    with db() as conn:
        existing = set()
        for r in conn.execute("SELECT english FROM words").fetchall():
            existing.add(r["english"].lower())
        inserted = 0
        skipped = 0
        for english, japanese, pos, example, domain, level in WORDS:
            if english.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (english, japanese, pos, example, domain, level),
            )
            existing.add(english.lower())
            inserted += 1
        print("inserted=" + str(inserted) + " skipped=" + str(skipped))


if __name__ == "__main__":
    main()
