# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated words & phrases for BOARD/ACTION SPORTS and RAP MUSIC,
authored by Claude.

Focus (フレーズ集・単語集の手薄な領域を補強):
1) ボード・アクションスポーツ: サーフィン、スケートボード、ストリートスポーツ
   （BMX、ブレイクダンス、パルクール）の実用語彙・スラング。
2) ラップ・ヒップホップ音楽の専門語彙（一般的な音楽ジャンル語とは別立て）。

重複回避の方針:
- "hip-hop" は既存（音楽ドメイン, 400）のため再追加しない。
- "hook" は既存（音楽ドメイン, 600, フック=印象的な部分）のため、ラップ文脈の
  hook は追加しない。
- "sample (audio)" は既存（音楽ドメイン, 650）のためラップの sample は追加しない。
- "verse" は既存（音楽ドメイン, 550）のため再追加しない。
- "beat" は既存（音楽ドメイン, 500, 拍・ビート）のため、ラップの「トラック」の
  意味では "instrumental" を採用。
- "tide" は既存（船舶ドメイン, 550）、"wheel" は複合語のみ既存のため単独では
  未登録 — サーフィンの tide は再追加しない。
- "deck"（船舶）, "rail"（鉄道）, "grind"（コーヒー）, "bail"（法律）,
  "freeze"（IT）は既存の同綴り語と意味が異なるため "(skateboarding)" /
  "(breaking)" 等の修飾語で衝突を回避。
- "flow" と "battle" はストリートスポーツとラップの両方で使う語のため、
  それぞれ "(parkour)" / "(rap)"、"(dance)" / "battle rap" で区別。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_surf_skate_street.py
      python scripts/add_surf_skate_street.py --missing-words   # report only

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
    "サーフィン・スケートボード": [
        # --- サーフィン ---
        ("Are the waves any good today?", "今日の波はどう？"),
        ("Let's paddle out before it gets crowded.", "混む前にパドルアウトしよう。"),
        ("I totally wiped out on that last wave.", "さっきの波で思いっきりワイプアウトしちゃった。"),
        ("You caught a great wave out there!", "あそこですごくいい波に乗ってたね！"),
        ("Duck dive under this one!", "この波、ダックダイブでくぐって！"),
        ("He got barreled on that wave.", "彼はあの波でチューブに入ったよ。"),
        ("The swell is picking up this afternoon.", "午後にはうねりが強くなってきてるね。"),
        ("Watch out for the rip current near the pier.", "桟橋の近くの離岸流に気をつけて。"),
        ("Don't forget to wax your board before you go out.", "出る前にボードにワックスを塗るのを忘れずに。"),
        ("My leash snapped right in the middle of the set.", "セットの真っ最中にリーシュが切れちゃった。"),
        ("Are you riding a longboard or a shortboard today?", "今日はロングボード？それともショートボード？"),
        ("That guy dropped in on me — total surf etiquette fail.", "あの人、割り込んできた。サーフマナー違反だよ。"),
        ("It's a beginner-friendly beach break, perfect for groms.", "ここは初心者向けのビーチブレイクで、キッズにもぴったり。"),
        ("The point break here works best on a big swell.", "ここのポイントブレイクは大きいうねりの時が最高。"),
        # --- スケートボード ---
        ("Nice ollie! You're really getting the hang of it.", "いいオーリー！だいぶ上達してきたね。"),
        ("Can you land a kickflip yet?", "もうキックフリップは決められる？"),
        ("He grinded the whole length of that rail.", "彼はあのレールを端から端までグラインドした。"),
        ("I need new wheels — these are totally worn down.", "新しいウィールが必要だ。これはもうすり減っちゃってる。"),
        ("The grip tape on my deck is peeling off.", "デッキのグリップテープが剥がれてきてる。"),
        ("Let's hit the half-pipe before it gets too crowded.", "混む前にハーフパイプに行こう。"),
        ("He's more into vert skating than street skating.", "彼はストリートよりヴァートスケートの方が好きだ。"),
        ("I totally bailed on that landing.", "あの着地、完全に転んじゃった。"),
        ("That was a pretty sketchy landing, but you stuck it.", "かなり危なっかしい着地だったけど、決めきったね。"),
        ("Is there a good skate park around here?", "この辺りにいいスケートパークはある？"),
        ("Check your trucks — they look a little loose.", "トラック、ちょっと緩んでるみたいだから確認して。"),
    ],
    "ストリートスポーツ": [
        # --- BMX ---
        ("He pulled off a clean bunny hop over the curb.", "彼は縁石をきれいなバニーホップで飛び越えた。"),
        ("Can you hold a manual all the way down this street?", "この通り、最後までマニュアルでいける？"),
        ("We're heading to the dirt jumps this weekend.", "今週末はダートジャンプに行くよ。"),
        ("She's really good at flatland tricks.", "彼女はフラットランドのトリックがすごく上手い。"),
        # --- ブレイクダンス ---
        ("He's one of the best b-boys in the local scene.", "彼はこの地域のシーンで屈指のB-boyだよ。"),
        ("That power move was insane!", "あのパワームーブ、すごすぎた！"),
        ("She held that freeze for like ten seconds.", "彼女はあのフリーズを10秒くらいキープしてた。"),
        ("His footwork is incredibly fast and clean.", "彼のフットワークは驚くほど速くて正確だ。"),
        ("They're battling in the final round tonight.", "彼らは今夜の決勝ラウンドでバトルする。"),
        ("Everyone jumped into the cypher after the show.", "ショーの後、みんなでサイファーに加わった。"),
        ("He threw in a windmill to finish his set.", "彼はセットの締めにウィンドミルを入れた。"),
        # --- パルクール ---
        ("He vaulted over the wall without even slowing down.", "彼は速度を落とすことなく壁をヴォルトで越えた。"),
        ("Can you actually wall run up that high?", "本当にあの高さまでウォールランできるの？"),
        ("That precision jump onto the ledge looked terrifying.", "あの縁への精密ジャンプ、見てて怖かった。"),
        ("She did a cat leap between the two rooftops.", "彼女は二つの屋根の間をキャットリープで渡った。"),
        ("His flow through the whole course was amazing.", "コース全体を通した彼の動きの流れは見事だった。"),
        ("He's been training as a traceur for years.", "彼は何年もトレーサーとして訓練を積んでいる。"),
    ],
    "ラップ・ヒップホップ": [
        ("He wrote the whole verse in one night.", "彼はそのヴァースを一晩で書き上げた。"),
        ("That's a killer bar right there.", "そこ、めちゃくちゃいいバーだね。"),
        ("Her flow is so smooth over that beat.", "そのビートに乗った彼女のフロウは本当になめらかだ。"),
        ("He killed it doing a freestyle rap in the cypher.", "彼はサイファーの中でフリースタイルラップを見事に決めた。"),
        ("That punchline caught everyone off guard.", "そのパンチラインはみんなの意表を突いた。"),
        ("His wordplay is on another level.", "彼の言葉遊びは次元が違う。"),
        ("She dropped a new mixtape last week.", "彼女は先週新しいミックステープをリリースした。"),
        ("The producer sent over a few instrumentals to choose from.", "プロデューサーが選べるようにいくつかインストを送ってきた。"),
        ("His rhyme scheme in that verse is really intricate.", "あのヴァースの韻の構成は本当に緻密だ。"),
        ("Those ad-libs in the background make the track pop.", "バックのアドリブがトラックを引き立てている。"),
        ("They dropped a diss track aimed at their old label.", "彼らは元レーベルに向けたディストラックを出した。"),
        ("He's considered one of the best battle rappers out there.", "彼は最高のバトルラッパーの一人とされている。"),
        ("She performed a spoken word piece before the show.", "彼女はショーの前にスポークンワードを披露した。"),
        ("His delivery is so laid-back it almost feels conversational.", "彼のデリバリーはとてもリラックスしていて、まるで会話みたいに聞こえる。"),
        ("The whole crowd was rapping along to every bar.", "会場全体が一節一節を一緒にラップしていた。"),
    ],
}

PHRASES_BY_SCENE["サーフィン・スケートボード"].extend([
    ("The wind is offshore this morning, so the waves should be clean.", "今朝はオフショアの風だから、波がきれいなはずだよ。"),
    ("This ramp has really smooth coping for grinds.", "このランプはグラインドしやすい、なめらかなコーピングだね。"),
])
PHRASES_BY_SCENE["ストリートスポーツ"].append(
    ("Their crew has been battling together for years.", "彼らのクルーは何年も一緒にバトルを重ねてきた。"),
)
PHRASES_BY_SCENE["ラップ・ヒップホップ"].append(
    ("He signed a record deal after that mixtape blew up.", "あのミックステープがバズった後、彼はレコード契約を結んだ。"),
)


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- サーフィン ---
    ("surfboard", "サーフボード", "名詞", "He carried his surfboard down to the beach.", "アウトドア・レジャー", "350"),
    ("surfing", "サーフィン", "名詞", "She goes surfing every weekend in summer.", "アウトドア・レジャー", "300"),
    ("wave", "波", "名詞", "The surfers were waiting for the next wave.", "アウトドア・レジャー", "300"),
    ("wipeout", "ワイプアウト（波に飲まれて落ちること）", "名詞", "That was the biggest wipeout I've seen all day.", "アウトドア・レジャー", "600"),
    ("paddle out", "パドルアウトする（沖に漕ぎ出す）", "動詞句", "We paddled out before sunrise to beat the crowd.", "アウトドア・レジャー", "700"),
    ("duck dive", "ダックダイブする（板ごと波の下をくぐる）", "動詞句", "You need to duck dive under bigger sets like that.", "アウトドア・レジャー", "800"),
    ("barrel", "チューブ・バレル（巻いた波の筒状部分）", "名詞", "He got completely covered up inside the barrel.", "アウトドア・レジャー", "800"),
    ("point break", "ポイントブレイク（岬の先などで割れる波）", "名詞", "This point break can produce really long rides.", "アウトドア・レジャー", "800"),
    ("beach break", "ビーチブレイク（砂浜沿いで割れる波）", "名詞", "Beach breaks tend to change with the sand each season.", "アウトドア・レジャー", "800"),
    ("swell", "うねり", "名詞", "A big swell is expected to hit the coast this weekend.", "アウトドア・レジャー", "700"),
    ("rip current", "離岸流", "名詞", "Lifeguards warned swimmers about a strong rip current.", "アウトドア・レジャー", "700"),
    ("wetsuit", "ウェットスーツ", "名詞", "You'll need a wetsuit if the water's this cold.", "アウトドア・レジャー", "500"),
    ("surf wax", "サーフワックス（ボードの滑り止め）", "名詞", "Rub some surf wax on the deck before you paddle out.", "アウトドア・レジャー", "700"),
    ("leash", "リーシュコード（足とボードをつなぐひも）", "名詞", "Always attach your leash before entering the water.", "アウトドア・レジャー", "600"),
    ("longboard", "ロングボード", "名詞", "Longboards are generally easier for beginners to balance on.", "アウトドア・レジャー", "600"),
    ("shortboard", "ショートボード", "名詞", "Shortboards allow for tighter, faster turns.", "アウトドア・レジャー", "600"),
    ("grom", "グロム（若手・初心者サーファーの俗称）", "名詞", "That kid is a total grom, but he's got real talent.", "アウトドア・レジャー", "900"),
    ("surf etiquette", "サーフマナー（波の優先順位などのルール）", "名詞", "Learning surf etiquette will keep you out of trouble in the lineup.", "アウトドア・レジャー", "850"),
    ("right of way (surfing)", "優先権（波に乗る権利）", "名詞", "The surfer closest to the peak has the right of way.", "アウトドア・レジャー", "850"),
    ("fin (surfing)", "フィン（サーフボード底面のひれ）", "名詞", "He replaced the fin after it snapped on a rock.", "アウトドア・レジャー", "700"),
    ("lineup (surfing)", "ラインナップ（波待ちする沖の位置）", "名詞", "There were already a dozen surfers in the lineup.", "アウトドア・レジャー", "850"),
    ("peak (surfing)", "ピーク（波が最初に崩れ始める場所）", "名詞", "Position yourself near the peak to catch the best waves.", "アウトドア・レジャー", "800"),
    ("offshore wind", "オフショアウインド（陸から海へ吹き、波をきれいに整える風）", "名詞", "Offshore wind in the morning makes the waves really clean.", "アウトドア・レジャー", "800"),
    ("onshore wind", "オンショアウインド（海から陸へ吹き、波を崩しやすい風）", "名詞", "Onshore wind usually makes the surf messy and choppy.", "アウトドア・レジャー", "800"),
    ("board shorts", "ボードショーツ（サーフィン用の短パン）", "名詞", "He always surfs in a pair of board shorts, even in winter.", "アウトドア・レジャー", "500"),
    ("stoked", "すごく興奮した・テンションが上がった", "形容詞", "I'm so stoked for the swell coming this weekend.", "アウトドア・レジャー", "800"),
    ("closeout", "クローズアウト（波が一斉に崩れてしまうこと）", "名詞", "The whole wave closed out before he could get a turn in.", "アウトドア・レジャー", "900"),
    ("kook", "コック（未熟なサーファーを指す俗語、やや見下した表現）", "名詞", "Don't paddle out there if you don't know what you're doing — you'll just look like a kook.", "アウトドア・レジャー", "950"),
    # --- スケートボード ---
    ("skateboard", "スケートボード", "名詞", "He got a new skateboard for his birthday.", "アウトドア・レジャー", "350"),
    ("skateboarding", "スケートボード（競技・活動としての）", "名詞", "Skateboarding became an Olympic sport in 2020.", "アウトドア・レジャー", "400"),
    ("deck (skateboard)", "デッキ（スケートボードの板部分）", "名詞", "The deck cracked after landing that big drop.", "アウトドア・レジャー", "650"),
    ("trucks", "トラック（デッキとウィールをつなぐ金具）", "名詞", "Tighten the trucks if the board feels too wobbly.", "アウトドア・レジャー", "700"),
    ("wheels", "ウィール（スケートボードの車輪）", "名詞", "Softer wheels give you a smoother ride on rough streets.", "アウトドア・レジャー", "500"),
    ("grip tape", "グリップテープ", "名詞", "The grip tape helps your shoes stick to the deck.", "アウトドア・レジャー", "700"),
    ("ollie", "オーリー（板を跳ね上げるジャンプ技）", "名詞", "The ollie is usually the first trick beginners learn.", "アウトドア・レジャー", "700"),
    ("kickflip", "キックフリップ（板を蹴って一回転させる技）", "名詞", "It took him months to land a clean kickflip.", "アウトドア・レジャー", "750"),
    ("grind (skateboarding)", "グラインドする（レールなどを板で滑る）", "動詞", "He can grind that whole handrail without falling.", "アウトドア・レジャー", "750"),
    ("rail (skateboarding)", "レール（グラインドする手すりや縁）", "名詞", "They set up a metal rail in the middle of the park.", "アウトドア・レジャー", "700"),
    ("ramp", "ランプ（斜面状の設備）", "名詞", "Skaters were lined up to drop into the ramp.", "アウトドア・レジャー", "500"),
    ("half-pipe", "ハーフパイプ", "名詞", "Pros were pulling off huge airs on the half-pipe.", "アウトドア・レジャー", "700"),
    ("vert skating", "ヴァートスケート（垂直系のスケート）", "名詞", "Vert skating requires a lot more air time than street skating.", "アウトドア・レジャー", "850"),
    ("street skating", "ストリートスケート", "名詞", "He prefers street skating over park sessions.", "アウトドア・レジャー", "700"),
    ("bail (skateboarding)", "転倒する・技を中断して逃げる", "動詞", "He had to bail halfway through the trick.", "アウトドア・レジャー", "700"),
    ("sketchy", "危なっかしい・不安定な", "形容詞", "That landing looked really sketchy but he pulled it off.", "アウトドア・レジャー", "750"),
    ("skate park", "スケートパーク", "名詞", "The city just opened a brand-new skate park downtown.", "アウトドア・レジャー", "500"),
    ("coping", "コーピング（ランプの縁の金属パイプ部分）", "名詞", "He slid smoothly across the coping.", "アウトドア・レジャー", "900"),
    ("board slide", "ボードスライド（デッキの底でレールを滑る技）", "名詞", "She landed a clean board slide down the handrail.", "アウトドア・レジャー", "800"),
    ("carve (skateboarding)", "カーブする（弧を描くように滑る）", "動詞", "He likes to carve around the bowl before trying any tricks.", "アウトドア・レジャー", "750"),
    ("tre flip", "トレフリップ（板を縦横両方に回転させる技）", "名詞", "Landing a tre flip down a set of stairs takes serious skill.", "アウトドア・レジャー", "950"),
    ("flatground", "フラットグラウンド（平らな路面でのトリック走行）", "名詞", "He practices most of his flatground tricks in a parking lot.", "アウトドア・レジャー", "850"),
    ("session (skateboarding)", "セッション（スケートで集まって滑る時間）", "名詞", "We had a great session at the park after school.", "アウトドア・レジャー", "700"),
    # --- ストリートスポーツ（BMX） ---
    ("BMX", "BMX（バイクモトクロス）", "名詞", "He's been riding BMX since he was seven.", "アウトドア・レジャー", "500"),
    ("bunny hop", "バニーホップ（両輪を同時に跳ばせる技）", "名詞", "A bunny hop lets you clear curbs and small gaps.", "アウトドア・レジャー", "800"),
    ("manual (BMX)", "マニュアル（前輪を上げて走る技）", "名詞", "Holding a manual for a long distance takes real balance.", "アウトドア・レジャー", "850"),
    ("dirt jump", "ダートジャンプ（土の坂を使ったジャンプ）", "名詞", "The dirt jump track has three big jumps in a row.", "アウトドア・レジャー", "800"),
    ("flatland", "フラットランド（平地でのトリック走行）", "名詞", "Flatland riding is all about balance and control, not speed.", "アウトドア・レジャー", "900"),
    ("tailwhip", "テールウィップ（バイクの後部を回転させる技）", "名詞", "He nailed a tailwhip off the last jump.", "アウトドア・レジャー", "900"),
    ("peg (BMX)", "ペグ（グラインド用にホイールへ付ける棒）", "名詞", "He grinds rails using the pegs on his back wheel.", "アウトドア・レジャー", "850"),
    # --- ブレイクダンス ---
    ("b-boy", "B-boy（男性のブレイクダンサー）", "名詞", "He's been a b-boy since middle school.", "アウトドア・レジャー", "850"),
    ("b-girl", "B-girl（女性のブレイクダンサー）", "名詞", "She's one of the top b-girls in the country.", "アウトドア・レジャー", "850"),
    ("power move", "パワームーブ（勢いや回転を使う大技）", "名詞", "His power moves always get the crowd hyped.", "アウトドア・レジャー", "850"),
    ("freeze (breaking)", "フリーズ（静止のポーズ技）", "名詞", "She finished her set with a perfectly balanced freeze.", "アウトドア・レジャー", "850"),
    ("footwork", "フットワーク（足さばきの技）", "名詞", "His footwork combos are incredibly fast.", "アウトドア・レジャー", "750"),
    ("battle (dance)", "バトル（ダンスの対戦形式）", "名詞", "The two crews faced off in a one-on-one battle.", "アウトドア・レジャー", "700"),
    ("cypher", "サイファー（円になって即興で踊る集まり）", "名詞", "Dancers took turns showing off in the cypher.", "アウトドア・レジャー", "900"),
    ("windmill", "ウィンドミル（体を回転させる技）", "名詞", "He can do a windmill for almost ten full rotations.", "アウトドア・レジャー", "800"),
    ("toprock", "トップロック（床に下りる前の立った状態の足さばき）", "名詞", "His toprock always sets the tone before he drops to the floor.", "アウトドア・レジャー", "900"),
    ("six-step", "シックスステップ（基本的な床の足さばきパターン）", "名詞", "Beginners usually learn the six-step before anything else.", "アウトドア・レジャー", "900"),
    ("crew (dance)", "クルー（ダンスチーム）", "名詞", "Their crew has been battling together for over a decade.", "アウトドア・レジャー", "700"),
    # --- パルクール ---
    ("parkour", "パルクール", "名詞", "Parkour is all about moving efficiently through obstacles.", "アウトドア・レジャー", "700"),
    ("vault", "ヴォルト（障害物を手で越える動作）", "名詞", "He cleared the railing with a quick vault.", "アウトドア・レジャー", "800"),
    ("wall run", "ウォールラン（壁を走って上る動作）", "名詞", "The wall run took him almost to the second-floor window.", "アウトドア・レジャー", "850"),
    ("precision jump", "プレシジョンジャンプ（正確に着地する跳躍）", "名詞", "That precision jump onto the narrow ledge was impressive.", "アウトドア・レジャー", "900"),
    ("cat leap", "キャットリープ（両手両足で着地する跳躍）", "名詞", "He landed the gap with a controlled cat leap.", "アウトドア・レジャー", "900"),
    ("flow (parkour)", "フロー（動きの流れるような連続性）", "名詞", "Her flow through the whole route looked effortless.", "アウトドア・レジャー", "800"),
    ("traceur", "トレーサー（パルクールの実践者）", "名詞", "He trains with a small group of traceurs every weekend.", "アウトドア・レジャー", "950"),
    ("tic-tac", "ティックタック（壁を軽く蹴って方向転換する動き）", "名詞", "He used a tic-tac off the wall to clear the gap.", "アウトドア・レジャー", "900"),
    ("kong vault", "コングヴォルト（両手をつき足から先に飛び越える技）", "名詞", "He cleared the bench with a smooth kong vault.", "アウトドア・レジャー", "950"),
    ("obstacle course", "障害物コース", "名詞", "The gym set up an obstacle course for parkour practice.", "アウトドア・レジャー", "600"),
    ("roll (parkour)", "ロール（着地の衝撃を逃がす受け身）", "名詞", "Always roll out of a big landing to protect your knees.", "アウトドア・レジャー", "800"),
    # --- ラップ・ヒップホップ ---
    ("bar (rap)", "バー（ラップの一小節・一行）", "名詞", "That last bar of his verse was clever.", "音楽", "800"),
    ("flow (rap)", "フロー（ラップのリズムの乗せ方）", "名詞", "His flow fits the beat perfectly.", "音楽", "750"),
    ("freestyle rap", "フリースタイルラップ（即興のラップ）", "名詞", "He can freestyle rap about almost anything you throw at him.", "音楽", "700"),
    ("punchline (rap)", "パンチライン（強い印象を残す一節）", "名詞", "That punchline had the whole room laughing.", "音楽", "900"),
    ("wordplay", "言葉遊び", "名詞", "Her wordplay is full of clever double meanings.", "音楽", "800"),
    ("mixtape", "ミックステープ（非公式にリリースする音源集）", "名詞", "He built his fan base off a series of free mixtapes.", "音楽", "700"),
    ("instrumental", "インスト（ボーカルなしの伴奏トラック）", "名詞", "The producer leaked the instrumental before the song dropped.", "音楽", "700"),
    ("rhyme scheme", "韻の構成・押韻パターン", "名詞", "The song's rhyme scheme changes completely in the second verse.", "音楽", "850"),
    ("ad-lib", "アドリブ（バックで挟む掛け声・合いの手）", "名詞", "The ad-libs in the background give the track extra energy.", "音楽", "800"),
    ("diss track", "ディストラック（相手を批判する曲）", "名詞", "The rapper released a diss track aimed at his rival.", "音楽", "800"),
    ("battle rap", "バトルラップ（対戦形式のラップ）", "名詞", "Battle rap requires quick thinking as much as skill on the mic.", "音楽", "800"),
    ("spoken word", "スポークンワード（詩の朗読的パフォーマンス）", "名詞", "She performed a spoken word piece about her hometown.", "音楽", "800"),
    ("delivery (vocal)", "デリバリー（歌唱・ラップの語り口）", "名詞", "His delivery is calm, but every word lands hard.", "音楽", "800"),
    ("hype man", "ハイプマン（ステージ上で盛り上げ役を務める人）", "名詞", "The hype man kept the crowd energized between songs.", "音楽", "800"),
    ("co-sign", "お墨付き（有名アーティストによる後押し）", "名詞", "That co-sign from a major artist changed his career overnight.", "音楽", "900"),
    ("trap (music)", "トラップ（重いベースとハイハットが特徴のサブジャンル）", "名詞", "Trap became one of the most popular subgenres of hip-hop.", "音楽", "700"),
    ("record deal", "レコード契約", "名詞", "She finally signed a record deal after years of independent releases.", "音楽", "650"),
    ("ghostwriter", "ゴーストライター（他人名義で歌詞を書く人）", "名詞", "Rumor has it he uses a ghostwriter for some of his hits.", "音楽", "800"),
    ("cadence (rap)", "ケイデンス（ラップの語りのリズム・抑揚）", "名詞", "His cadence shifts dramatically between the verse and the hook.", "音楽", "850"),
    ("punch-in", "パンチイン（一行ずつ録り直す録音手法）", "名詞", "They recorded the whole verse punch-in, line by line.", "音楽", "850"),
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
    "could", "would", "shall", "rather", "ever", "way", "one's", "off",
    "before", "later", "earlier", "second", "gist", "point", "way", "say",
    "saying", "sure", "understand", "following", "pick", "leave", "there",
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
