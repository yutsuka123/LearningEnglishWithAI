# ruff: noqa: E501
"""アニメ/ゲーム・Discord/SF/TRPG・ボードゲームのオタク趣味語彙増強(2026-09-13・authored by Claude)。
前回セッションでドラフトした約112語がセッションスクラッチパッドのみに保存され、
セッション終了とともに失われたため、このセッションで再ドラフトしたもの。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table
(既存15,000語超に対してチェック済み。whale/toxic/crunch/alignment等は同一綴りの
既存語と意味が異なるため、pottery script の "mold (ceramics)" 方式に倣い
括弧で領域を明示した見出し語にして衝突を回避している)。

Run:  python scripts/add_niche_otaku_topup_2026_09_13.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # ===== アニメ (42語) =====
    ("waifu", "自分にとって理想の女性キャラクターであるかのように強い愛着を注ぐ、アニメやゲームの女性キャラクターを指すインターネットスラング。", "名詞", "He jokingly called the character his waifu and collected every figure of her he could find.", "アニメ", "750"),
    ("husbando", "「waifu」の男性版で、自分にとって理想の男性であるかのように強い愛着を注ぐ、アニメやゲームの男性キャラクターを指すインターネットスラング。", "名詞", "She proudly declared the stoic swordsman to be her husbando.", "アニメ", "750"),
    ("isekai", "現代日本などの主人公が事故死や召喚によって異世界へ転移・転生し、そこで冒険する物語類型を指すジャンル名。", "名詞", "In this isekai series, an office worker is hit by a truck and reborn as a prince in a fantasy kingdom.", "アニメ", "600"),
    ("tsundere", "最初はそっけない態度やきつい言葉で相手に接するが、次第に本当は好意や優しさを持っていることが明らかになっていくキャラクター類型。", "名詞", "The tsundere heroine insisted she didn't care about him, even while secretly making him lunch every day.", "アニメ", "650"),
    ("kuudere", "普段は感情を表に出さず冷静沈着に振る舞うが、内面には他人への思いやりや優しさを秘めているキャラクター類型。", "名詞", "The kuudere classmate rarely smiled, but she always quietly helped anyone who was struggling.", "アニメ", "700"),
    ("yandere", "表面上は相手に深い愛情を示す一方で、その愛情ゆえに嫉妬や執着から異常な、時に暴力的な行動に走ることがあるキャラクター類型。", "名詞", "The yandere character's sweet smile turned unsettling the moment anyone got too close to her crush.", "アニメ", "750"),
    ("dandere", "普段は人見知りで無口だが、心を許した相手や慣れた状況では素直に気持ちを表すようになるキャラクター類型。", "名詞", "As a dandere, he barely spoke to strangers, but he chatted happily once his new friend broke the ice.", "アニメ", "700"),
    ("moe", "主にキャラクターの可愛らしさや弱さ、健気さなどに対してファンが抱く、庇護欲を伴う強い愛おしさの感情、またはそれを引き出すような要素・作風を指す語。", "名詞", "Fans praised the show's moe art style, which made even minor characters feel adorable.", "アニメ", "700"),
    ("chuunibyou", "直訳は「中二病」で、自分には秘めた特別な力や過去があると思い込み、大げさで芝居がかった言動を取る(主に思春期の)人物像、またはそれを面白おかしく描く作品類型。", "名詞", "The chuunibyou protagonist insisted his eyepatch sealed away a demonic power.", "アニメ", "750"),
    ("seiyuu", "日本のアニメ・ゲーム業界で活動する声優を指す語。ファンの間では英語の「voice actor」よりも日本のアニメ文化に特化した文脈でこの語が好んで使われる。", "名詞", "Fans lined up for hours to get an autograph from their favorite seiyuu at the convention.", "アニメ", "600"),
    ("sakuga", "特定のカットやシーンにおいて、作画スタッフが力を入れて描いた、とりわけ滑らかで質の高い作画・動きを指すファン用語。", "名詞", "Fans replayed the fight scene repeatedly, marveling at the sakuga during the final showdown.", "アニメ", "800"),
    ("OTP", "「one true pairing」の略で、あるファンが数あるカップリングの中で最も好み、最も「本命」だと考える2人の組み合わせを指す語。", "名詞", "She has shipped the same OTP since her very first anime convention.", "アニメ", "700"),
    ("Mary Sue", "欠点がほとんどなく、あらゆる面で理想化・完璧に描かれた(しばしば作者の願望が投影された)フィクション上の登場人物を指し、しばしば人物造形の粗さを批判する意味で使われる語。", "名詞", "Critics complained that the new character felt like a Mary Sue who could do no wrong.", "アニメ", "750"),
    ("BL", "「Boys' Love」の略で、男性同士の恋愛関係を描いた、主に女性読者・視聴者を対象とするマンガ・アニメのジャンル。", "名詞", "The bookstore has an entire shelf dedicated to BL manga.", "アニメ", "650"),
    ("yuri", "女性同士の恋愛関係を描いたマンガ・アニメのジャンルを指す語。", "名詞", "The convention panel discussed the growing popularity of yuri series among Western fans.", "アニメ", "650"),
    ("shounen", "主に少年・若い男性読者を対象とした、アクションや友情・成長をテーマに据えることが多いマンガ・アニメのジャンル区分。", "名詞", "The story follows a classic shounen formula: a young hero training to become the strongest fighter.", "アニメ", "550"),
    ("shoujo", "主に少女・若い女性読者を対象とした、恋愛や人間関係の機微を中心に描くことが多いマンガ・アニメのジャンル区分。", "名詞", "This shoujo series focuses on the heroine's slow-burn romance with her childhood friend.", "アニメ", "550"),
    ("seinen", "主に成人男性読者を対象とした、より複雑なテーマや成熟した表現を扱うことも多いマンガ・アニメのジャンル区分。", "名詞", "The seinen manga tackles morally gray themes that wouldn't appear in a typical shounen title.", "アニメ", "650"),
    ("josei", "主に成人女性読者を対象とした、恋愛や仕事、日常生活をより現実的に描くことが多いマンガ・アニメのジャンル区分。", "名詞", "Josei manga often portrays the everyday struggles of adult women more realistically than shoujo does.", "アニメ", "650"),
    ("slice of life", "劇的な事件よりも登場人物の日常生活の細やかな出来事や人間関係を中心に描く物語のジャンル。", "名詞", "Instead of a dramatic plot, the slice of life anime simply follows the characters' daily routines at school.", "アニメ", "550"),
    ("iyashikei", "「癒し系」の意で、穏やかで安らぎを与えるような雰囲気を持ち、視聴者を癒すことを主眼に置いた作品類型。", "名詞", "After a stressful week, she liked to unwind with an iyashikei show about a quiet countryside cafe.", "アニメ", "750"),
    ("harem", "一人の主人公(多くは男性)を中心に、複数の異性キャラクターが恋愛的な好意を寄せる状況を描く作品ジャンル。", "名詞", "In this harem comedy, the shy protagonist is somehow adored by every girl in his class.", "アニメ", "600"),
    ("reverse harem", "一人の女性主人公を中心に、複数の男性キャラクターが恋愛的な好意を寄せる状況を描く、ハーレムものの女性主人公版のジャンル。", "名詞", "The reverse harem game lets players choose which of the five love interests to pursue.", "アニメ", "650"),
    ("magical girl", "多くは少女である主人公が、変身することで魔法の力を得て戦ったり問題を解決したりする物語のジャンル。", "名詞", "The magical girl transforms into her powered-up form whenever a new monster appears.", "アニメ", "600"),
    ("mecha", "巨大なロボットや人が搭乗して操縦する機械兵器を主題として描く作品ジャンル。", "名詞", "The mecha anime is famous for its detailed battles between giant piloted robots.", "アニメ", "600"),
    ("bishounen", "中性的で華やかな美しさを持つ、若い美男子として描かれるキャラクター類型。", "名詞", "The manga is filled with elegant bishounen characters with long flowing hair.", "アニメ", "700"),
    ("bishoujo", "非常に整った可愛らしい容姿を持つ、若い美少女として描かれるキャラクター類型。", "名詞", "The visual novel is centered around several bishoujo characters the player can befriend.", "アニメ", "700"),
    ("cel animation", "透明なセルロイド(セル画)に手描きで彩色し、それを背景画の上に重ねて撮影する伝統的なアニメーション制作技法。現在は多くがデジタル作画に置き換わっている。", "名詞", "Older fans still feel nostalgic for the distinct look of cel animation from the 1980s and '90s.", "アニメ", "750"),
    ("in-between", "アニメーションにおいて、動きの要となる原画(キーフレーム)と原画の間を滑らかにつなぐために描かれる中割りの絵、またはその工程。", "名詞", "Junior animators are often assigned to draw the in-betweens under a senior artist's key animation.", "アニメ", "800"),
    ("key animation", "シーンの重要な動き・ポーズを決定づける原画を描く工程で、通常は経験豊富なアニメーターが担当し、その後に中割り(in-between)が描き足される。", "名詞", "The veteran animator was credited for the key animation in the episode's climactic battle.", "アニメ", "800"),
    ("opening theme", "アニメ各話の冒頭に流れる主題歌と、それに合わせた映像のことで、しばしば「OP」と略される。", "名詞", "Fans immediately recognized the show from just the first few notes of its opening theme.", "アニメ", "550"),
    ("ending theme", "アニメ各話の終わりに流れる主題歌と、それに合わせた映像のことで、しばしば「ED」と略される。", "名詞", "The ending theme's melancholic melody perfectly matched the episode's bittersweet conclusion.", "アニメ", "550"),
    ("light novel", "主にティーン・若年層向けに書かれた、比較的短くマンガ風のイラストが多数挿入される日本の小説形式で、しばしばアニメ化される。", "名詞", "The anime is based on a best-selling light novel series with over a dozen volumes.", "アニメ", "600"),
    ("doujinshi", "既存の作品を題材にすることも多い、ファン自身が自費出版する非公式の同人誌・マンガで、主に同人即売会で販売される。", "名詞", "She sold her doujinshi based on her favorite series at the convention's artist alley.", "アニメ", "700"),
    ("fan art", "公式のライセンスを受けていない、ファンが自主的に制作する既存キャラクターや作品を題材にした絵。", "名詞", "The artist posted a piece of fan art depicting her favorite two characters together.", "アニメ", "500"),
    ("fanfiction", "既存の作品の登場人物や世界観を借りて、ファンが公式の許可なく執筆する二次創作の小説。", "名詞", "He has written over a hundred chapters of fanfiction exploring an alternate ending to the series.", "アニメ", "600"),
    ("sub", "「subtitled」の略で、声は原語のまま字幕を付けたバージョンの作品を指し、声を吹き替えた「dub」と対比される。", "名詞", "He prefers watching anime in sub rather than dub to hear the original Japanese performances.", "アニメ", "550"),
    ("OVA", "「original video animation」の略で、テレビ放送や劇場公開を経ずに、ビデオソフトとして直接発売されるアニメ作品。", "名詞", "The extra story arc was never broadcast on TV and was instead released as an OVA.", "アニメ", "700"),
    ("ONA", "「original net animation」の略で、テレビ放送を経ずにインターネット配信を前提として直接公開されるアニメ作品。", "名詞", "The studio released the short series as an ONA exclusively on a streaming platform.", "アニメ", "750"),
    ("shipping", "特定の2人のキャラクターが恋愛関係にあることを望んだり、その組み合わせを応援したりするファンの行為。", "名詞", "Fans have been shipping the two rival characters together since the very first season.", "アニメ", "650"),
    ("cour", "日本のテレビアニメ業界で使われる、およそ3か月(1クール)を単位とする放送期間の呼び方で、作品の長さを「2クール」のように表す際に用いられる。", "名詞", "The series was originally planned as a single cour but was extended to two cours due to its popularity.", "アニメ", "800"),
    ("recap episode", "新しい展開を進めず、これまでの回想映像を中心に構成して物語を振り返る回のこと。", "名詞", "Fans were disappointed to find that the tenth episode was just a recap episode with no new footage.", "アニメ", "600"),

    # ===== ゲーム・Discordの英語 (30語) =====
    ("metroidvania", "『メトロイド』と『悪魔城ドラキュラ』に由来する名称で、広大な一つのマップを、新しい能力を獲得しながら非線形に探索していくアクションアドベンチャーゲームのジャンル。", "名詞", "The indie game is a metroidvania where you gain new abilities that let you revisit earlier areas.", "ゲーム・Discordの英語", "750"),
    ("soulslike", "フロム・ソフトウェアの『ダークソウル』シリーズを手本とした、高い難易度と丁寧な戦闘、少ないチュートリアルを特徴とするアクションRPGのジャンル・作風。", "名詞", "Critics called the new title a soulslike thanks to its punishing bosses and stamina-based combat.", "ゲーム・Discordの英語", "800"),
    ("battle royale", "多数のプレイヤーが縮小していくマップの中で戦い、最後まで生き残った一人(またはチーム)が勝者となる対戦ゲームのジャンル。", "名詞", "A hundred players parachute onto the island at the start of every battle royale match.", "ゲーム・Discordの英語", "650"),
    ("tier list", "キャラクターや武器、戦術などを強さの序列に応じてS・A・Bのような等級(ティア)に分類した一覧表。", "名詞", "According to the latest tier list, that character has fallen from S-rank to B-rank after the balance patch.", "ゲーム・Discordの英語", "700"),
    ("gacha", "カプセルトイの自動販売機になぞらえた仕組みで、現実のお金やゲーム内通貨を使い、ランダムにキャラクターやアイテムを入手できる課金システム。", "名詞", "She spent all her saved-up currency trying to pull the new character from the gacha.", "ゲーム・Discordの英語", "700"),
    ("whale (gaming)", "基本プレイ無料のゲームに対して、通常のプレイヤーよりも極端に多額の実際のお金を課金するプレイヤーを指すスラング。", "名詞", "A single whale can generate more revenue for the game than thousands of free players combined.", "ゲーム・Discordの英語", "750"),
    ("MMR", "「matchmaking rating」の略で、プレイヤーの実力を数値化し、近い実力同士の対戦相手を組み合わせるために使われる評価値。", "名詞", "Winning ranked matches gradually increased his MMR, matching him against tougher opponents.", "ゲーム・Discordの英語", "700"),
    ("frame data", "格闘ゲームにおいて、ある技が発生してからヒットし、動作から復帰するまでにかかる正確なフレーム数の数値情報で、上級者が戦略を練るために参照する。", "名詞", "Competitive players memorize frame data to know exactly which moves are safe to punish.", "ゲーム・Discordの英語", "800"),
    ("esports", "観客やスポンサー、賞金を伴い、プロとしても行われる組織的な対戦型ビデオゲームの競技全般を指す語。", "名詞", "The esports tournament filled an entire arena with fans cheering for their favorite teams.", "ゲーム・Discordの英語", "600"),
    ("LAN party", "複数のプレイヤーが各自のパソコンを持ち寄り、同じ場所でローカルネットワークを組んで一緒に対戦ゲームを楽しむ集まり。", "名詞", "Before online gaming became common, friends would host a LAN party to play together in one room.", "ゲーム・Discordの英語", "600"),
    ("hotfix", "重大な不具合を修正するために、通常の大型パッチのサイクルを待たずに緊急で配信される小規模な更新。", "名詞", "The developers pushed out a hotfix within hours after the exploit was discovered.", "ゲーム・Discordの英語", "700"),
    ("loot box", "購入することで、ランダムに選ばれたゲーム内アイテムが手に入る仕組みの入れ物で、一部からギャンブルに近いと批判されることもある。", "名詞", "The game was criticized for selling loot boxes that gave players a random chance at rare weapons.", "ゲーム・Discordの英語", "700"),
    ("pay-to-win", "実際にお金を課金したプレイヤーが、そうでないプレイヤーに対して大きな競技上の優位を得られるようなゲームの仕組みを指す形容表現。", "形容詞", "Fans complained that the sequel had become far more pay-to-win than the original game.", "ゲーム・Discordの英語", "700"),
    ("free-to-play", "購入せずに遊ぶことができ、追加のコンテンツなどは任意で課金できるようになっているゲームの形態を指す形容表現。", "形容詞", "The free-to-play game earns its revenue almost entirely from optional cosmetic purchases.", "ゲーム・Discordの英語", "600"),
    ("toxic (gaming)", "チームメイトや対戦相手に対する、暴言や非協力的な態度など敵意ある・スポーツマンシップに欠ける振る舞いを指すゲーマー用語。", "形容詞", "He muted the chat because one player kept being toxic toward the rest of the team.", "ゲーム・Discordの英語", "700"),
    ("rubberbanding", "通信の遅延を補正するために、プレイヤーやオブジェクトの位置が突然巻き戻ったように見える現象を、ゴムひもに引き戻されるさまにたとえた表現。", "名詞", "His car appeared to teleport backward due to rubberbanding caused by a poor connection.", "ゲーム・Discordの英語", "800"),
    ("hitbox", "ゲーム内でキャラクターや物体の衝突・攻撃判定を行うために設定された、目に見えない境界領域。", "名詞", "The sword's hitbox extended slightly beyond the visible blade, surprising the opponent.", "ゲーム・Discordの英語", "750"),
    ("hurtbox", "攻撃判定を持つ「hitbox」とは区別して、キャラクターが実際に攻撃を受けてダメージを負う範囲を示す、目に見えない境界領域。", "名詞", "Crouching shrinks the character's hurtbox, letting certain high attacks whiff harmlessly overhead.", "ゲーム・Discordの英語", "800"),
    ("spectator mode", "自らは対戦に参加せず、進行中の試合を観戦できるモードで、大会中継などでよく使われる。", "名詞", "Eliminated players can switch to spectator mode to keep watching how the match ends.", "ゲーム・Discordの英語", "600"),
    ("paywall", "料金を支払わない限り、コンテンツや機能へのアクセスを制限する仕組み。", "名詞", "The best weapons in the game were locked behind a paywall, frustrating free players.", "ゲーム・Discordの英語", "650"),
    ("season pass", "決められた期間にわたり、今後配信される追加コンテンツや報酬をまとめて入手できる購入型のパス。", "名詞", "Buying the season pass in advance guarantees access to every future expansion.", "ゲーム・Discordの英語", "650"),
    ("battle pass", "期間限定のシーズン中にプレイすることで段階的に報酬を解除していく仕組みで、全ての報酬を得るには通常購入が必要となる。", "名詞", "She grinded daily challenges to level up her battle pass before the season ended.", "ゲーム・Discordの英語", "650"),
    ("cross-play", "PCと家庭用ゲーム機など、異なるプラットフォームのプレイヤー同士が同じ試合で一緒に遊べる機能。", "名詞", "Thanks to cross-play, PC and console players can now team up in the same lobby.", "ゲーム・Discordの英語", "650"),
    ("slash command", "Discordなどのチャットプラットフォームで、スラッシュ(/)から始まる文字列を入力してBotを操作したり動作を実行したりするコマンド。", "名詞", "Typing the slash command /mute instantly silenced the noisy bot in the channel.", "ゲーム・Discordの英語", "600"),
    ("rage quit", "怒りや苛立ちから、特に敗北や不運な出来事の後に、突然ゲームを途中で投げ出してやめてしまうこと。", "動詞", "After losing his fourth match in a row, he rage quit and slammed his controller down.", "ゲーム・Discordの英語", "700"),
    ("aimbot", "プレイヤーの武器を自動的に敵に照準させ、不当に有利にする不正行為用のソフトウェア。", "名詞", "The player was banned after an anti-cheat system detected he was using an aimbot.", "ゲーム・Discordの英語", "750"),
    ("wallhack", "本来なら壁などの障害物に遮られて見えないはずの相手の位置を透視できるようにする不正行為用のソフトウェア。", "名詞", "With a wallhack enabled, the cheater always knew exactly where enemies were hiding.", "ゲーム・Discordの英語", "750"),
    ("elo", "元々チェス向けに開発された評価方式で、対戦相手との勝敗結果をもとにプレイヤーの相対的な実力を数値化するレーティングシステム。", "名詞", "Winning against a higher-rated opponent boosted his elo more than beating a weaker one.", "ゲーム・Discordの英語", "750"),
    ("LFG", "「looking for group」の略で、特定の目的のために一緒に遊ぶ仲間を募集する際に使われる呼びかけ。", "名詞", "He posted \"LFG for tonight's raid, need one more healer\" in the Discord server.", "ゲーム・Discordの英語", "600"),
    ("deathmatch", "プレイヤー同士が自由に戦い、制限時間やスコアの上限までに最も多く敵を倒した者が勝者となる対戦モード。", "名詞", "The free-for-all deathmatch mode pits every player against everyone else at once.", "ゲーム・Discordの英語", "600"),

    # ===== SF (22語) =====
    ("space opera", "科学的な厳密さよりも、壮大な冒険やロマンス、英雄的な戦いなど物語性・スペクタクルを重視する、宇宙を舞台にしたSFのサブジャンル。", "名詞", "The saga is a classic space opera, complete with galactic empires, star battles, and a chosen hero.", "SF", "650"),
    ("hard science fiction", "科学的な正確さや、実現しうる技術・物理法則の描写を重視するSFのサブジャンル。", "名詞", "As hard science fiction, the novel meticulously calculates the fuel requirements for interstellar travel.", "SF", "750"),
    ("soft science fiction", "厳密な科学的描写よりも、社会・心理・哲学的なテーマを重視するSFのサブジャンル。", "名詞", "Rather than focus on technical accuracy, the soft science fiction story explores how the colonists' society evolves.", "SF", "750"),
    ("grimdark", "希望がほとんど残されておらず、暴力や道徳的な曖昧さが常態化している、陰惨で救いのない作品世界を指す形容・分類語。", "名詞", "The setting is famously grimdark, where every faction is corrupt and no one truly wins.", "SF", "800"),
    ("biopunk", "サイバーパンクの技術面をコンピューターではなく生命科学に置き換えた、遺伝子操作やバイオテクノロジーとその社会的な負の側面を主題とするSFのサブジャンル。", "名詞", "The biopunk thriller centers on black-market gene hackers who splice DNA in illegal back-alley labs.", "SF", "850"),
    ("solarpunk", "再生可能エネルギーや生態系との共生によって環境問題が克服された、楽観的な未来社会を描くSFのサブジャンル・運動。", "名詞", "The solarpunk illustration depicts a city where solar panels and gardens cover every rooftop.", "SF", "800"),
    ("ansible", "アーシュラ・K・ル=グウィンが考案した架空の通信装置で、どれほど距離が離れていても光速の制限を受けずに瞬時に情報をやり取りできるとされる。", "名詞", "Thanks to the ansible, the fleet commander could speak with headquarters light-years away with no delay.", "SF", "850"),
    ("Kardashev scale", "文明がどれだけのエネルギーを利用できるかによって、惑星規模・恒星規模・銀河規模の段階に分類する、ニコライ・カルダシェフが提唱した仮説的な尺度。", "名詞", "On the Kardashev scale, humanity is still far from even becoming a full Type I civilization.", "SF", "850"),
    ("cosmic horror", "人類が広大で理解しがたく、無関心な宇宙的存在の前ではいかに無力かを描く、H・P・ラヴクラフトと結び付けられるホラーのサブジャンル。", "名詞", "The cosmic horror story ends with the protagonist realizing humanity was never anything more than an afterthought to the ancient beings.", "SF", "800"),
    ("steampunk", "蒸気機関を動力とする、ヴィクトリア朝風の美意識をまとったレトロフューチャーな技術を描くSFのサブジャンル。", "名詞", "The steampunk city is filled with brass airships and steam-powered mechanical contraptions.", "SF", "650"),
    ("dieselpunk", "第一次・第二次世界大戦の頃のディーゼル機関の時代の美意識や技術を土台に、空想的な要素を組み合わせたSFのサブジャンル。", "名詞", "The dieselpunk setting combines 1940s-style fighter planes with fantastical energy weapons.", "SF", "800"),
    ("climate fiction", "気候変動とそれが社会に及ぼす影響を主題とするジャンルで、「cli-fi」とも呼ばれる。", "名詞", "The climate fiction novel imagines a coastal city struggling to survive after decades of rising sea levels.", "SF", "700"),
    ("multiverse", "私たちの宇宙と並行して、無数かもしれない別の宇宙が同時に存在するとする仮説的な集合体。", "名詞", "In the multiverse, there could be a version of you living a completely different life.", "SF", "650"),
    ("FTL travel", "「faster-than-light travel」の略で、光速を超えて移動する架空の手段全般を指し、恒星間を舞台にした物語を成立させるためによく用いられる設定。", "名詞", "Without some form of FTL travel, reaching even the nearest star system would take generations.", "SF", "700"),
    ("planetary romance", "科学的な厳密さよりも探検やロマンスを重視して、しばしば未開の異星を舞台に冒険を描くSFのサブジャンル。", "名詞", "The planetary romance follows an adventurer exploring the jungles of a primitive alien world.", "SF", "850"),
    ("weird fiction", "ホラー・ファンタジー・SFの要素を融合させ、奇妙で不可解な感覚を呼び起こすことを目指すジャンルで、後のコズミックホラーにも影響を与えた。", "名詞", "Early weird fiction blurred the line between science fiction and horror long before cosmic horror became its own genre.", "SF", "850"),
    ("uplift", "高度な文明が遺伝子操作や技術的介入によって、別の種の知能を意図的に向上させ知性を持たせるSFのトロープ。", "名詞", "In the novel, humanity uses genetic uplift to grant dolphins and apes human-level intelligence.", "SF", "850"),
    ("space western", "アメリカ西部劇のフロンティアの町やアウトロー、ガンマンといった要素を、宇宙を舞台にしたSF設定に置き換えたサブジャンル。", "名詞", "The show is a space western where bounty hunters chase outlaws across the edges of settled space.", "SF", "750"),
    ("megastructure", "ダイソン球や軌道エレベーターのように、惑星や恒星規模に達するほど巨大な人工構造物の総称。", "名詞", "The alien megastructure was so vast that it dwarfed every planet in the system.", "SF", "800"),
    ("ringworld", "恒星を取り巻く巨大な輪の形をした仮説的な巨大構造物で、ラリー・ニーヴンの同名小説によって広く知られるようになった。", "名詞", "The explorers landed on the inner surface of the ringworld, which curved endlessly toward the horizon.", "SF", "850"),
    ("psionics", "純粋な魔法ではなく、擬似科学的な仕組みによって説明・行使されるとされる、テレパシーや念動力などの架空の超能力全般。", "名詞", "The soldier's psionics let her read enemy thoughts from a distance and crush objects with her mind.", "SF", "800"),
    ("xenobiology", "地球外生命体の生物学的な性質を研究する、仮説上の学問分野。", "名詞", "The crew's xenobiology team studied the alien organism's unusual cellular structure.", "SF", "850"),

    # ===== TRPG・ボードゲーム (18語) =====
    ("rules lawyer", "自分に有利になるようルールの解釈をめぐって議論しがちで、時にグループの他のメンバーを苛立たせるプレイヤーを指す語。", "名詞", "The rules lawyer at the table spent ten minutes arguing that his character should get an extra bonus.", "TRPG・ボードゲーム", "750"),
    ("session zero", "本格的なキャンペーンを始める前に行う準備の場で、扱う内容の範囲や雰囲気について合意し、キャラクターを一緒に作成したりするための顔合わせ回。", "名詞", "During session zero, the group agreed on which themes were off-limits before creating their characters.", "TRPG・ボードゲーム", "700"),
    ("X-card", "プレイヤーが理由を説明することなく、特定の場面や話題を止めたり飛ばしたりしてほしいと合図するために、「X」と書かれたカードを掲げたり叩いたりする安全ツール。", "名詞", "She tapped the X-card to signal that the scene had crossed a line she wasn't comfortable with.", "TRPG・ボードゲーム", "750"),
    ("murder hobo", "法や結果をほとんど気にせず、行く先々で暴力によって問題を解決しながら放浪するプレイヤーキャラクターを、ユーモラスに指す語。", "名詞", "His character had become such a murder hobo that the party was banned from three towns.", "TRPG・ボードゲーム", "750"),
    ("splatbook", "TRPGのシステムにおいて、特定のクラスや種族、テーマを掘り下げて拡張する追加のルールブック。", "名詞", "The new splatbook adds a dozen fresh subclasses focused entirely on wilderness survival.", "TRPG・ボードゲーム", "750"),
    ("dice pool", "単一の合計値を出すのではなく、複数のダイスをまとめて振り、一定の目以上が出た数を成功として数えるゲームの仕組み。", "名詞", "Instead of rolling one die and adding modifiers, this system uses a dice pool where sixes count as successes.", "TRPG・ボードゲーム", "700"),
    ("crunch (TRPG)", "ゲームシステムがどれだけ詳細で数値的に複雑なルールを持っているかを表す度合いで、物語的な雰囲気を指す「fluff」と対比される。", "名詞", "The rulebook is famous for its heavy crunch, with pages of detailed combat modifiers.", "TRPG・ボードゲーム", "800"),
    ("fluff (TRPG)", "ゲームの機械的なルール(「crunch」)とは対照的に、世界観や設定、物語的な雰囲気を伝える説明文・背景設定。", "名詞", "She skimmed past the fluff describing the kingdom's history to get to the actual character rules.", "TRPG・ボードゲーム", "800"),
    ("area control", "プレイヤーがボード上の領地を奪い合い、確保することで得点や優位を得るボードゲームの仕組み。", "名詞", "The board game revolves around area control, as players fight to hold the most regions by the end of the round.", "TRPG・ボードゲーム", "750"),
    ("push your luck", "現在得ている利益をあきらめて手を引くか、それともさらに大きな見返りを狙ってリスクを取り続けるかを繰り返し選ぶ、ゲームの仕組み・ジャンル。", "名詞", "The push your luck mechanic tempts players to draw one more card, even though busting means losing everything.", "TRPG・ボードゲーム", "750"),
    ("social deduction", "プレイヤー同士の会話や推理を通じて、正体を隠した裏切り者や特殊な役職を見つけ出すことを目的とするゲームのジャンル。", "名詞", "In this social deduction game, players must debate and vote to identify who among them is secretly the traitor.", "TRPG・ボードゲーム", "700"),
    ("legacy game", "ボードに書き込んだりカードを破いたりすることで、複数回のプレイを通じて盤面やルールが恒久的に変化していく、キャンペーン形式のボードゲーム。", "名詞", "In the legacy game, the players permanently sealed off a region of the map after their disastrous third session.", "TRPG・ボードゲーム", "750"),
    ("asymmetric game", "全プレイヤーが同一のルールに従うのではなく、それぞれ異なる能力や目標、開始条件を持つゲーム。", "名詞", "The asymmetric game gives one player overwhelming power, while the others must cooperate just to survive.", "TRPG・ボードゲーム", "750"),
    ("GM screen", "ゲームマスターの手元にあるメモやダイスの出目をプレイヤーから隠しつつ、プレイヤー側からは参照用の表が見えるように置く、折りたたみ式のついたて。", "名詞", "He kept the encounter notes hidden behind the GM screen so the players couldn't peek at what was coming.", "TRPG・ボードゲーム", "650"),
    ("total party kill (TPK)", "「TPK」と略される、パーティーの全プレイヤーキャラクターが死亡してしまう出来事で、多くの場合キャンペーンの終了や大きな展開の変更を招く。", "名詞", "A single ambush led to a total party kill, forcing the group to start a brand-new campaign.", "TRPG・ボードゲーム", "750"),
    ("natural 20", "20面ダイスを使うゲームにおいて、修正値を加える前のダイス自体の出目が20であることを指し、多くの場合自動的な決定的成功として扱われる。", "名詞", "He rolled a natural 20 on his attack, landing a critical hit that finished off the dragon.", "TRPG・ボードゲーム", "650"),
    ("alignment (TRPG)", "『ダンジョンズ&ドラゴンズ』などで特に使われる、キャラクターの道徳的・倫理的な傾向(秩序と善、混沌と悪など)を表す特性。", "名詞", "Her character's alignment was lawful good, so she refused to lie even to save herself.", "TRPG・ボードゲーム", "600"),
    ("player agency", "プレイヤーの選択がストーリーや結果にどれだけ実質的な影響を与えるかという度合いで、あらかじめ決められた筋書きに沿って進める「レールローディング」と対比される。", "名詞", "The sandbox campaign was praised for giving players real agency instead of railroading them down one path.", "TRPG・ボードゲーム", "750"),
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
