# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a brand-new domain covering POLITICS & GOVERNMENT vocabulary, authored
by Claude (2026-08-04・ユーザー要望:「政治もあっていいね 英単語、フレーズ
英単語はたとえば議場、」).

既存語彙には政治・統治の専門ドメインが一切存在しなかった(domain='法律' が
法律・訴訟手続き用語をカバーしているのみ)。本スクリプトはユーザー例示の
「議場」(legislative chamber) を起点に、議会機構・選挙制度・統治機構/立法
手続き・外交・政治一般語彙、および後続要望で追加された国家元首/指導者の
呼称・政党/政治スペクトラム・汚職語彙・憲法関連の司法用語・国家/国民性の
概念・比較政治学的な政治体制/イデオロギー用語を、新規 domain='政治' として
追加する。フレーズは新規 scene='政治・行政の英語' として追加する。

【中立性について・重要】
このアプリは一般向け語学学習アプリであり、政治的に偏った内容や特定の実在
の政治家・実在の論争的な時事問題への言及は避け、「比較政治学の教科書用語
集」のような、統治の仕組み・手続きを説明する記述的な語彙に限定している。
以下の2点は、当初の中立性方針(実在の国名・実在の政治家・実在の政党名を
出さない)と、追加要望の一部が直接矛盾したため、安全側に倒して調整した:

  1) 実在の政党名(例: "Republican Party" / "Democratic Party")は追加して
     いない。代わりに ruling party / opposition party / political party /
     two-party system / multi-party system / one-party state という、どの
     国にも特定されない制度語彙で対応した。実在政党名が本当に必要であれば
     別途ユーザーに明示確認のうえ追加する。
  2) "paramount leader" (国家主席) や "supreme leader" のように、特定の
     現実の国(中国/イラン・北朝鮮など)の指導者呼称として要望されたものは、
     語彙としては採用したが、日本語訳・例文からは実在国名を意図的に外し、
     「一部の政治体制で用いられる指導者呼称」という制度としての定義のみに
     とどめている。英語として単独では成立しない "state chairman" は追加
     していない。
  3) イデオロギー/政治体制語彙(communism, socialism, capitalism, dictator-
     ship 等)は、価値判断を含まない辞書的な定義のみとし、実在の国がどの
     体制に該当するかには一切言及していない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
independently against the `words` and `phrases` tables. A dedup pass against
the live DB (7100+ words / 4400+ phrases, including the newer domain='法律'
additions from add_legal_studies.py) confirmed these exact strings already
exist elsewhere and are intentionally OMITTED here to avoid duplicates:
parliament, congress, cabinet, constituency, ballot, incumbent, candidate,
amendment, veto, referendum, lobbying, bureaucracy, embassy, treaty, summit,
approval rating, legislation, constitution, statute, ratify, sovereignty,
committee, vote, government, political, democracy, republic, president,
mayor, council, law, policy, coalition, monarchy, scandal.

Run:  python scripts/add_politics_government.py
仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "政治"
SCENE = "政治・行政の英語"

# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 議場・議会機構 ---
    ("legislative chamber", "議場(議事堂の議場)", "名詞", "Reporters were not allowed inside the legislative chamber during the vote.", DOMAIN, "700"),
    ("assembly hall", "議事堂・集会場", "名詞", "The assembly hall was full for the opening ceremony of the new session.", DOMAIN, "600"),
    ("senate", "上院", "名詞", "The senate voted to send the bill back to committee.", DOMAIN, "550"),
    ("house of representatives", "下院", "名詞", "The house of representatives passed the budget bill yesterday.", DOMAIN, "600"),
    ("prime minister", "首相", "名詞", "The prime minister addressed the nation on television.", DOMAIN, "500"),
    ("head of state", "国家元首", "名詞", "The president serves as the country's head of state.", DOMAIN, "650"),
    ("speaker of the house", "議長(下院議長)", "名詞", "The speaker of the house called the session to order.", DOMAIN, "750"),
    ("quorum", "定足数", "名詞", "The meeting could not proceed because there was no quorum.", DOMAIN, "800"),
    ("plenary session", "本会議", "名詞", "The proposal will be debated at the next plenary session.", DOMAIN, "800"),
    ("committee hearing", "委員会公聴会", "名詞", "Several experts testified at the committee hearing.", DOMAIN, "650"),
    ("filibuster", "フィリバスター(議事妨害)", "名詞", "The senator staged a filibuster to delay the vote.", DOMAIN, "850"),
    ("floor vote", "本会議での採決", "名詞", "The bill is scheduled for a floor vote next Tuesday.", DOMAIN, "700"),
    ("roll call vote", "記名投票(点呼採決)", "名詞", "Each member's vote was recorded in the roll call vote.", DOMAIN, "750"),
    ("bicameral legislature", "二院制議会", "名詞", "Many countries have a bicameral legislature with an upper and lower house.", DOMAIN, "850"),
    ("unicameral legislature", "一院制議会", "名詞", "Some smaller countries prefer a unicameral legislature for simplicity.", DOMAIN, "850"),
    # --- 選挙・民主主義 ---
    ("general election", "総選挙", "名詞", "A general election will be held early next year.", DOMAIN, "550"),
    ("by-election", "補欠選挙", "名詞", "A by-election was called after the seat became vacant.", DOMAIN, "700"),
    ("electoral district", "選挙区", "名詞", "Each electoral district elects one representative.", DOMAIN, "650"),
    ("absentee ballot", "不在者投票", "名詞", "She submitted an absentee ballot because she was traveling abroad.", DOMAIN, "700"),
    ("voter turnout", "投票率", "名詞", "Voter turnout was lower than in the previous election.", DOMAIN, "600"),
    ("primary election", "予備選挙", "名詞", "The party will choose its candidate in a primary election.", DOMAIN, "650"),
    ("exit poll", "出口調査", "名詞", "The exit poll suggested a close result.", DOMAIN, "700"),
    ("electoral college", "選挙人団", "名詞", "The winner is decided by the electoral college, not the popular vote alone.", DOMAIN, "800"),
    ("proportional representation", "比例代表制", "名詞", "Under proportional representation, seats are allocated according to each party's share of the vote.", DOMAIN, "850"),
    ("first-past-the-post", "小選挙区制(単純多数決制)", "名詞", "In a first-past-the-post system, the candidate with the most votes wins the seat.", DOMAIN, "900"),
    ("term limit", "任期制限", "名詞", "The constitution sets a term limit of two terms for the president.", DOMAIN, "650"),
    ("campaign platform", "選挙公約・政策綱領", "名詞", "The candidate outlined her campaign platform at the rally.", DOMAIN, "700"),
    ("swing state", "激戦州(選挙結果が読めない地域)", "名詞", "Candidates spend much of their time campaigning in swing states.", DOMAIN, "750"),
    ("marginal seat", "接戦選挙区", "名詞", "The party focused its resources on a handful of marginal seats.", DOMAIN, "800"),
    ("gerrymandering", "恣意的な選挙区割り(ゲリマンダリング)", "名詞", "Critics accused the redistricting plan of gerrymandering.", DOMAIN, "900"),
    ("coalition government", "連立政権", "名詞", "No single party won a majority, so they formed a coalition government.", DOMAIN, "750"),
    ("minority government", "少数与党政権", "名詞", "The minority government relies on support from smaller parties to pass bills.", DOMAIN, "800"),
    ("no-confidence vote", "不信任決議(投票)", "名詞", "The opposition called for a no-confidence vote against the cabinet.", DOMAIN, "800"),
    ("dissolve parliament", "議会を解散する", "動詞句", "The prime minister decided to dissolve parliament and call an early election.", DOMAIN, "750"),
    ("dissolution", "解散", "名詞", "The dissolution of parliament triggered a new election within sixty days.", DOMAIN, "750"),
    ("election", "選挙", "名詞", "The election is scheduled for the first Sunday of next month.", DOMAIN, "450"),
    # --- 統治機構・立法過程 ---
    ("executive branch", "行政府", "名詞", "The executive branch is responsible for enforcing the laws.", DOMAIN, "600"),
    ("legislative branch", "立法府", "名詞", "The legislative branch is made up of the two houses of parliament.", DOMAIN, "600"),
    ("judicial branch", "司法府", "名詞", "The judicial branch interprets the law and settles disputes.", DOMAIN, "600"),
    ("separation of powers", "三権分立", "名詞", "Separation of powers keeps any single branch from becoming too powerful.", DOMAIN, "700"),
    ("checks and balances", "抑制と均衡(チェック・アンド・バランス)", "名詞", "Checks and balances allow each branch to limit the power of the others.", DOMAIN, "700"),
    ("bill", "法案", "名詞", "The bill must pass both houses before it becomes law.", DOMAIN, "500"),
    ("override a veto", "拒否権を覆す", "動詞句", "The legislature needed a two-thirds majority to override a veto.", DOMAIN, "750"),
    ("enact a law", "法律を制定する", "動詞句", "It took two years for the assembly to enact a law addressing the issue.", DOMAIN, "650"),
    ("repeal a law", "法律を廃止する", "動詞句", "Lawmakers voted to repeal a law that was no longer considered necessary.", DOMAIN, "700"),
    ("plebiscite", "国民投票(プレビシット)", "名詞", "A plebiscite was held to decide the territory's future status.", DOMAIN, "850"),
    ("lobbyist", "ロビイスト", "名詞", "The lobbyist met with several lawmakers to discuss the proposal.", DOMAIN, "650"),
    ("think tank", "シンクタンク", "名詞", "The report was published by an independent think tank.", DOMAIN, "700"),
    ("civil service", "公務員制度", "名詞", "She has worked in the civil service for over twenty years.", DOMAIN, "650"),
    ("federalism", "連邦制", "名詞", "Federalism divides power between a central government and regional governments.", DOMAIN, "800"),
    ("devolution", "権限移譲(地方分権化)", "名詞", "Devolution gave the regional assembly control over local education policy.", DOMAIN, "850"),
    ("local government", "地方自治体・地方政府", "名詞", "Local government is responsible for services like waste collection and libraries.", DOMAIN, "500"),
    ("municipal government", "市町村政府・自治体政府", "名詞", "The municipal government announced a new recycling program.", DOMAIN, "550"),
    ("first reading", "第一読会", "名詞", "The bill passed its first reading without debate.", DOMAIN, "800"),
    ("second reading", "第二読会", "名詞", "The bill will face detailed scrutiny at its second reading.", DOMAIN, "800"),
    ("third reading", "第三読会", "名詞", "The final vote takes place after the third reading.", DOMAIN, "800"),
    ("legislative session", "立法会期", "名詞", "Several important bills were passed during this legislative session.", DOMAIN, "700"),
    ("sunset clause", "日没条項(時限失効条項)", "名詞", "The law includes a sunset clause that ends it automatically after five years.", DOMAIN, "900"),
    ("rider", "付帯条項(法案に付加される条項)", "名詞", "A rider was attached to the budget bill at the last minute.", DOMAIN, "850"),
    ("private member's bill", "議員提出法案", "名詞", "The reform began as a private member's bill rather than a government proposal.", DOMAIN, "900"),
    ("standing committee", "常任委員会", "名詞", "The proposal was referred to a standing committee for review.", DOMAIN, "800"),
    ("select committee", "特別委員会", "名詞", "A select committee was formed to investigate the matter.", DOMAIN, "800"),
    # --- 外交・国際関係 ---
    ("diplomat", "外交官", "名詞", "The diplomat was posted to the embassy for three years.", DOMAIN, "550"),
    ("bilateral talks", "二国間協議", "名詞", "The two governments held bilateral talks on trade.", DOMAIN, "700"),
    ("multilateral agreement", "多国間協定", "名詞", "Several countries signed the multilateral agreement on environmental standards.", DOMAIN, "800"),
    ("sanctions", "制裁(措置)", "名詞", "The organization imposed sanctions in response to the violation.", DOMAIN, "700"),
    ("foreign policy", "外交政策", "名詞", "Foreign policy decisions often require approval from the legislature.", DOMAIN, "600"),
    ("head of delegation", "代表団長", "名詞", "The head of delegation presented the country's position at the summit.", DOMAIN, "750"),
    ("state visit", "公式訪問(国賓訪問)", "名詞", "The king's state visit included a meeting with local business leaders.", DOMAIN, "650"),
    # --- 政治一般 ---
    ("constituent", "有権者・選挙区民", "名詞", "The representative held a meeting to hear from her constituents.", DOMAIN, "700"),
    ("grassroots movement", "草の根運動", "名詞", "The campaign began as a grassroots movement among local residents.", DOMAIN, "650"),
    ("political spectrum", "政治的スペクトラム(思想の分布)", "名詞", "Parties are often placed somewhere along the political spectrum.", DOMAIN, "750"),
    ("bipartisan", "超党派の", "形容詞", "The bill received bipartisan support in the assembly.", DOMAIN, "750"),
    ("partisan", "党派的な・特定の党派を支持する", "形容詞", "The debate quickly became partisan rather than focused on facts.", DOMAIN, "700"),
    ("public opinion poll", "世論調査", "名詞", "A public opinion poll showed mixed views on the proposal.", DOMAIN, "600"),
    ("political rally", "政治集会", "名詞", "Thousands attended the political rally in the town square.", DOMAIN, "600"),
    ("manifesto", "政党綱領・声明書", "名詞", "The party published its manifesto ahead of the election.", DOMAIN, "700"),
    # --- 国家元首・指導者の呼称(比較政治学・特定国には言及しない中立表現) ---
    ("monarch", "君主", "名詞", "The monarch's role is largely ceremonial in many modern constitutions.", DOMAIN, "600"),
    ("paramount leader", "最高指導者(公式の役職名によらず事実上の最高権力を持つ人物の呼称)", "名詞", "Historians debate how much real authority a paramount leader holds compared with elected officials.", DOMAIN, "850"),
    ("supreme leader", "最高指導者(一部の政治体制で用いられる国家最高権威の称号)", "名詞", "In some political systems, the supreme leader holds authority above elected officials.", DOMAIN, "850"),
    # --- 政党・政治スペクトラム(実在政党名は使わない一般的な制度語彙) ---
    ("ruling party", "与党", "名詞", "The ruling party introduced a new budget proposal this week.", DOMAIN, "600"),
    ("opposition party", "野党", "名詞", "The opposition party criticized the plan during the debate.", DOMAIN, "600"),
    ("political party", "政党", "名詞", "Voters can choose from several political parties on the ballot.", DOMAIN, "500"),
    ("two-party system", "二大政党制", "名詞", "In a two-party system, two major parties usually dominate elections.", DOMAIN, "750"),
    ("multi-party system", "多党制", "名詞", "A multi-party system often leads to coalition governments.", DOMAIN, "800"),
    ("one-party state", "一党制国家", "名詞", "In a one-party state, only one party is legally allowed to hold power.", DOMAIN, "850"),
    ("Republican Party", "共和党(アメリカの二大政党の一つ)", "固有名詞", "The Republican Party is one of the two major political parties in the United States.", DOMAIN, "600"),
    ("Democratic Party", "民主党(アメリカの二大政党の一つ)", "固有名詞", "The Democratic Party is one of the two major political parties in the United States.", DOMAIN, "600"),
    ("right-wing", "右派の", "形容詞", "The right-wing faction of the party opposed the reform.", DOMAIN, "750"),
    ("left-wing", "左派の", "形容詞", "The left-wing faction called for greater social spending.", DOMAIN, "750"),
    ("centrist", "中道派(の人)", "名詞", "The centrist candidate tried to appeal to voters on both sides.", DOMAIN, "750"),
    # --- 汚職・腐敗 ---
    ("political corruption", "政治腐敗", "名詞", "The report examined political corruption in local government contracts.", DOMAIN, "750"),
    ("cronyism", "縁故主義", "名詞", "Critics accused the administration of cronyism in its appointments.", DOMAIN, "850"),
    ("embezzlement of public funds", "公金横領", "名詞", "He was charged with embezzlement of public funds.", DOMAIN, "900"),
    ("anti-corruption law", "汚職防止法", "名詞", "The new anti-corruption law requires officials to declare their assets.", DOMAIN, "800"),
    ("conflict of interest", "利益相反", "名詞", "The official recused herself to avoid a conflict of interest.", DOMAIN, "700"),
    # --- 司法(憲法関連) ---
    ("judicial review", "司法審査", "名詞", "The court used judicial review to strike down the regulation.", DOMAIN, "850"),
    ("constitutional court", "憲法裁判所", "名詞", "The constitutional court ruled that the law violated the constitution.", DOMAIN, "850"),
    ("supreme court", "最高裁判所", "名詞", "The case was eventually appealed to the supreme court.", DOMAIN, "650"),
    ("judicial independence", "司法の独立", "名詞", "Judicial independence means judges can rule without political interference.", DOMAIN, "800"),
    ("impeachment", "弾劾", "名詞", "The assembly began impeachment proceedings against the official.", DOMAIN, "800"),
    ("impeachment trial", "弾劾裁判", "名詞", "The impeachment trial lasted several weeks.", DOMAIN, "850"),
    # --- 国家・国民性の概念 ---
    ("nation-state", "国民国家", "名詞", "The modern nation-state emerged as the dominant form of political organization.", DOMAIN, "800"),
    ("statehood", "国家としての地位", "名詞", "The territory has long sought full statehood.", DOMAIN, "850"),
    ("nationhood", "国家性・国民としての一体性", "名詞", "The ceremony celebrated fifty years of nationhood.", DOMAIN, "850"),
    ("national identity", "国民的アイデンティティ", "名詞", "Language and history both shape a country's national identity.", DOMAIN, "700"),
    ("citizenship", "市民権・国籍", "名詞", "She applied for citizenship after living in the country for ten years.", DOMAIN, "600"),
    ("stateless", "無国籍の", "形容詞", "A stateless person is not recognized as a citizen by any country.", DOMAIN, "850"),
    ("failed state", "破綻国家", "名詞", "Analysts warned that ongoing conflict could turn the region into a failed state.", DOMAIN, "850"),
    ("rogue state", "ならず者国家(国際規範に反すると見なされる国家を指す語)", "名詞", "The term rogue state is sometimes used to describe a government seen as defying international norms.", DOMAIN, "900"),
    ("autonomous region", "自治区", "名詞", "The autonomous region has its own local assembly.", DOMAIN, "800"),
    ("self-determination", "自己決定権(民族自決)", "名詞", "The principle of self-determination allows a people to choose their own political status.", DOMAIN, "850"),
    # --- 政治体制・イデオロギー(価値判断を含まない比較政治学的な定義) ---
    ("direct democracy", "直接民主制", "名詞", "In a direct democracy, citizens vote directly on laws rather than through representatives.", DOMAIN, "800"),
    ("representative democracy", "代議制民主主義", "名詞", "Most large countries use a representative democracy rather than a direct democracy.", DOMAIN, "750"),
    ("socialism", "社会主義", "名詞", "Socialism generally favors greater public ownership and control of key industries.", DOMAIN, "700"),
    ("dictatorship", "独裁政治(体制)", "名詞", "Under a dictatorship, power is concentrated in a single leader without regular elections.", DOMAIN, "700"),
    ("authoritarianism", "権威主義", "名詞", "Authoritarianism limits political freedoms while allowing some economic activity.", DOMAIN, "800"),
    ("totalitarianism", "全体主義", "名詞", "Totalitarianism seeks to control nearly every aspect of public and private life.", DOMAIN, "850"),
    ("communism", "共産主義", "名詞", "Communism calls for common ownership of the means of production and a classless society.", DOMAIN, "700"),
    ("capitalism", "資本主義", "名詞", "Capitalism is based on private ownership and free markets.", DOMAIN, "650"),
    ("anarchism", "アナーキズム(無政府主義)", "名詞", "Anarchism argues that formal government structures are unnecessary or harmful.", DOMAIN, "850"),
    ("constitutional monarchy", "立憲君主制", "名詞", "In a constitutional monarchy, the monarch's powers are limited by a constitution.", DOMAIN, "800"),
    ("absolute monarchy", "絶対君主制", "名詞", "In an absolute monarchy, the ruler holds power that is not limited by a constitution.", DOMAIN, "800"),
    ("theocracy", "神権政治", "名詞", "In a theocracy, religious leaders hold direct political authority.", DOMAIN, "850"),
    ("oligarchy", "寡頭政治", "名詞", "An oligarchy is a system in which power rests with a small group of people.", DOMAIN, "850"),
    ("populism", "ポピュリズム(大衆迎合主義)", "名詞", "Populism often appeals directly to ordinary people against established elites.", DOMAIN, "800"),
]


# --- phrases: (english, japanese), all under SCENE --------------------------

PHRASES: list[tuple[str, str]] = [
    ("The bill passed its second reading.", "法案は第二読会を通過した。"),
    ("The vote was carried by a narrow margin.", "採決は僅差で可決された。"),
    ("The committee will hold public hearings next week.", "委員会は来週、公聴会を開く予定です。"),
    ("Turnout was higher than expected this election.", "今回の選挙は予想より投票率が高かった。"),
    ("The coalition fell apart after the no-confidence vote.", "不信任決議の後、連立政権は崩壊した。"),
    ("She's running for a second term.", "彼女は二期目に向けて立候補している。"),
    ("The amendment failed to reach the required majority.", "修正案は必要な過半数に届かなかった。"),
    ("Could you explain how the electoral college works?", "選挙人団の仕組みを説明していただけますか？"),
    ("The parliament was dissolved ahead of schedule.", "議会は予定より早く解散された。"),
    ("The treaty still needs to be ratified.", "その条約はまだ批准される必要がある。"),
    ("The new law goes into effect next month.", "新しい法律は来月施行される。"),
    ("The bill was referred to a standing committee.", "法案は常任委員会に付託された。"),
    ("He was elected by a landslide.", "彼は圧倒的な差で当選した。"),
    ("The opposition party called for an emergency debate.", "野党は緊急討議を要求した。"),
    ("Voters head to the polls on Sunday.", "有権者は日曜日に投票に向かう。"),
    ("The prime minister survived the no-confidence vote.", "首相は不信任決議を乗り切った。"),
    ("The candidate conceded defeat shortly after midnight.", "候補者は深夜過ぎに敗北を認めた。"),
    ("Ballots are still being counted in several districts.", "いくつかの選挙区ではまだ開票作業が続いている。"),
    ("The government reshuffled the cabinet last week.", "政府は先週、内閣改造を行った。"),
    ("The bill needs a two-thirds majority to pass.", "その法案の可決には3分の2の賛成が必要だ。"),
    ("The president has the power to veto legislation.", "大統領には法案を拒否する権限がある。"),
    ("The senator filibustered for over ten hours.", "その上院議員は10時間以上フィリバスターを行った。"),
    ("Local elections tend to have lower turnout.", "地方選挙は一般に投票率が低い傾向にある。"),
    ("The court ruled the law unconstitutional.", "裁判所はその法律を違憲と判断した。"),
    ("The delegation arrived for the summit this morning.", "代表団は今朝、首脳会談のために到着した。"),
    ("Lawmakers are debating the budget bill this week.", "議員たちは今週、予算法案について議論している。"),
    ("The referendum result will be announced tomorrow.", "国民投票の結果は明日発表される。"),
    ("Public support for the reform has grown steadily.", "改革への世論の支持は着実に高まっている。"),
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

        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        ph_added = ph_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                (en, ja, SCENE),
            )
            ph_existing.add(en.lower())
            ph_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
