# ruff: noqa: E501  (data-heavy seed script)
"""Add religion (Christianity/Judaism/Islam/Buddhism) + philosophy + IT
(build/errors, web/embedded/frontend/backend) + AI-prompting + management
vocabulary & phrases. Authored by Claude — no app/OpenAI API calls.

All words carry an example. Religion & philosophy phrases include quotations.

Run:  python scripts/add_more.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, example) per word domain.
WORDS_BY_DOMAIN: dict[str, list[tuple[str, str, str]]] = {
    "宗教": [
        # general
        ("faith", "信仰", "She kept her faith through hard times."),
        ("worship", "礼拝・崇拝", "They gather to worship every week."),
        ("ritual", "儀式", "The ceremony follows an ancient ritual."),
        ("deity", "神・神格", "Each temple honors a different deity."),
        ("divine", "神聖な・神の", "They believe in divine providence."),
        ("soul", "魂", "He prayed for the souls of the dead."),
        ("afterlife", "来世", "Many religions teach an afterlife."),
        ("doctrine", "教義", "The doctrine guides their daily life."),
        ("theology", "神学", "He studied theology at university."),
        ("clergy", "聖職者", "The clergy led the congregation in prayer."),
        ("monastery", "修道院", "Monks live and pray in the monastery."),
        ("pilgrimage", "巡礼", "They made a pilgrimage to the holy city."),
        ("blessing", "祝福", "The priest gave them a blessing."),
        ("sacred", "神聖な", "This mountain is sacred to them."),
        ("congregation", "会衆", "The congregation sang together."),
        # Christianity
        ("gospel", "福音", "He preached the gospel to the crowd."),
        ("salvation", "救済", "They seek salvation through faith."),
        ("sin", "罪", "He confessed his sins to the priest."),
        ("grace", "恩寵", "We are saved by grace."),
        ("resurrection", "復活", "Easter celebrates the resurrection."),
        ("trinity", "三位一体", "The Trinity is central to Christian belief."),
        ("baptism", "洗礼", "The baby received baptism."),
        ("communion", "聖餐", "They took communion at the altar."),
        ("crucifixion", "磔刑", "The crucifixion is depicted in the painting."),
        ("redemption", "贖罪", "The story is about sin and redemption."),
        ("parable", "たとえ話", "Jesus taught in parables."),
        ("apostle", "使徒", "Peter was one of the twelve apostles."),
        ("disciple", "弟子", "He became a disciple of the teacher."),
        ("prophet", "預言者", "The prophet warned the people."),
        ("commandment", "戒律", "There are ten commandments."),
        ("repentance", "悔い改め", "He showed true repentance."),
        ("psalm", "詩篇", "She read a psalm aloud."),
        ("covenant", "契約・聖約", "God made a covenant with his people."),
        ("messiah", "救世主", "They awaited the coming of the messiah."),
        ("mercy", "慈悲", "He begged for mercy."),
        # Judaism
        ("Torah", "トーラー(律法)", "The Torah is read in the synagogue."),
        ("synagogue", "シナゴーグ", "They pray at the synagogue."),
        ("rabbi", "ラビ", "The rabbi explained the text."),
        ("Sabbath", "安息日", "No work is done on the Sabbath."),
        ("kosher", "コーシャ(適正な食物)", "This restaurant serves kosher food."),
        ("Passover", "過越の祭り", "Passover commemorates the exodus."),
        ("Talmud", "タルムード", "Scholars debate the Talmud."),
        ("Yom Kippur", "ヨム・キプル(贖罪の日)", "Jews fast on Yom Kippur."),
        ("menorah", "メノラー(燭台)", "They lit the menorah."),
        # Islam
        ("Quran", "コーラン", "He recited verses from the Quran."),
        ("mosque", "モスク", "They pray five times a day at the mosque."),
        ("imam", "イマーム", "The imam led the prayer."),
        ("Ramadan", "ラマダン(断食月)", "Muslims fast during Ramadan."),
        ("pilgrim", "巡礼者", "Millions of pilgrims travel to Mecca."),
        ("halal", "ハラル(許された)", "He only eats halal meat."),
        ("Allah", "アッラー(神)", "They worship Allah."),
        ("fasting", "断食", "Fasting teaches self-discipline."),
        ("alms", "喜捨・施し", "Giving alms is a religious duty."),
        ("Mecca", "メッカ", "Mecca is the holiest city in Islam."),
        # Buddhism
        ("enlightenment", "悟り", "The Buddha attained enlightenment."),
        ("karma", "業(カルマ)", "They believe good karma brings good results."),
        ("nirvana", "涅槃", "Nirvana is freedom from suffering."),
        ("reincarnation", "輪廻・転生", "Some religions teach reincarnation."),
        ("meditation", "瞑想", "Meditation calms the mind."),
        ("monk", "僧・修道士", "The monk lives a simple life."),
        ("sutra", "経典・経", "The monk chanted a sutra."),
        ("dharma", "法(ダルマ)", "He follows the dharma."),
        ("compassion", "慈悲", "Buddhism teaches compassion for all beings."),
        ("mindfulness", "マインドフルネス", "Mindfulness reduces stress."),
        ("impermanence", "無常", "Buddhism stresses the impermanence of life."),
    ],
    "哲学": [
        ("metaphysics", "形而上学", "Metaphysics asks what reality is."),
        ("epistemology", "認識論", "Epistemology studies how we know things."),
        ("ethics", "倫理学", "Ethics examines right and wrong."),
        ("logic", "論理学", "Logic is the study of valid reasoning."),
        ("aesthetics", "美学", "Aesthetics concerns the nature of beauty."),
        ("ontology", "存在論", "Ontology asks what exists."),
        ("existentialism", "実存主義", "Existentialism stresses personal freedom."),
        ("rationalism", "合理主義", "Rationalism trusts reason over experience."),
        ("empiricism", "経験主義", "Empiricism bases knowledge on experience."),
        ("idealism", "観念論", "Idealism holds that reality is mental."),
        ("materialism", "唯物論", "Materialism says only matter exists."),
        ("nihilism", "虚無主義", "Nihilism denies inherent meaning."),
        ("stoicism", "ストア哲学", "Stoicism teaches calm acceptance."),
        ("determinism", "決定論", "Determinism denies true free will."),
        ("free will", "自由意志", "Do we really have free will?"),
        ("dualism", "二元論", "Mind-body dualism separates the two."),
        ("dialectic", "弁証法", "Hegel is known for his dialectic."),
        ("syllogism", "三段論法", "A syllogism has two premises."),
        ("premise", "前提", "The argument rests on a false premise."),
        ("deduction", "演繹", "Deduction moves from general to specific."),
        ("induction", "帰納", "Induction generalizes from examples."),
        ("paradox", "逆説・パラドックス", "The statement is a logical paradox."),
        ("morality", "道徳", "They debated the basis of morality."),
        ("consciousness", "意識", "Consciousness is hard to explain."),
        ("phenomenology", "現象学", "Phenomenology studies lived experience."),
        ("utilitarianism", "功利主義", "Utilitarianism seeks the greatest good."),
        ("skepticism", "懐疑論", "Skepticism doubts all certainty."),
        ("axiom", "公理", "Geometry begins from axioms."),
        ("fallacy", "誤謬", "That argument contains a fallacy."),
        ("subjective", "主観的な", "Beauty is a subjective judgment."),
        ("objective", "客観的な", "Science aims to be objective."),
    ],
    "IT": [
        ("compile", "コンパイルする", "The code won't compile."),
        ("compiler", "コンパイラ", "The compiler reported an error."),
        ("runtime", "実行時", "The error occurs at runtime."),
        ("dependency", "依存関係", "Install the missing dependency."),
        ("repository", "リポジトリ", "Clone the repository first."),
        ("commit", "コミット(する)", "Commit your changes before pushing."),
        ("merge", "マージ(する)", "Merge the feature branch into main."),
        ("branch", "ブランチ", "Create a new branch for the fix."),
        ("deploy", "デプロイする", "We deploy every Friday."),
        ("container", "コンテナ", "The app runs in a container."),
        ("framework", "フレームワーク", "We use a web framework."),
        ("library", "ライブラリ", "Import the library at the top."),
        ("endpoint", "エンドポイント", "Call the login endpoint."),
        ("frontend", "フロントエンド", "She works on the frontend."),
        ("backend", "バックエンド", "The backend handles the data."),
        ("query", "クエリ・問い合わせ", "Optimize the database query."),
        ("cache", "キャッシュ", "Clear the cache and reload."),
        ("latency", "遅延・レイテンシ", "Network latency slowed the app."),
        ("middleware", "ミドルウェア", "Add authentication middleware."),
        ("microservice", "マイクロサービス", "Each microservice runs independently."),
        ("refactor", "リファクタリングする", "Let's refactor this function."),
        ("debug", "デバッグする", "I spent hours debugging the issue."),
        ("breakpoint", "ブレークポイント", "Set a breakpoint on line 10."),
        ("stack trace", "スタックトレース", "Read the stack trace for clues."),
        ("exception", "例外", "Catch the exception and log it."),
        ("recursion", "再帰", "The function uses recursion."),
        ("algorithm", "アルゴリズム", "This sorting algorithm is fast."),
        ("asynchronous", "非同期の", "The call is asynchronous."),
        ("thread", "スレッド", "The task runs on a separate thread."),
        ("concurrency", "並行性", "Concurrency bugs are hard to find."),
        ("deadlock", "デッドロック", "Two threads caused a deadlock."),
        ("encryption", "暗号化", "Use encryption for sensitive data."),
        ("authentication", "認証", "Authentication failed."),
        ("token", "トークン", "The access token expired."),
        ("payload", "ペイロード", "The request payload was too large."),
        ("schema", "スキーマ", "Update the database schema."),
        ("migration", "マイグレーション", "Run the database migration."),
        ("rollback", "ロールバック", "Roll back to the previous version."),
        ("scalability", "拡張性", "Design for scalability from the start."),
        ("kernel", "カーネル", "The driver runs in the kernel."),
        ("interrupt", "割り込み", "The timer triggers an interrupt."),
        ("embedded", "組み込みの", "He develops embedded systems."),
        ("real-time", "リアルタイムの", "The sensor needs a real-time response."),
        ("bootloader", "ブートローダ", "The bootloader starts the firmware."),
        ("baud rate", "ボーレート(通信速度)", "Set the baud rate to 9600."),
        ("responsive", "レスポンシブな", "The site is responsive on mobile."),
        ("viewport", "ビューポート", "Set the viewport meta tag."),
        ("lint", "静的解析する(リント)", "Lint the code before committing."),
        ("rebuild", "再ビルドする", "Rebuild the project from scratch."),
    ],
    "管理": [
        ("schedule", "予定・スケジュール", "Check your schedule for Monday."),
        ("reschedule", "予定を変更する(リスケ)", "Can we reschedule to Thursday?"),
        ("milestone", "マイルストーン", "We hit our first milestone."),
        ("priority", "優先度", "Set the priority to high."),
        ("resource", "リソース・資源", "We lack the resources to finish."),
        ("allocation", "割り当て", "Review the budget allocation."),
        ("stakeholder", "利害関係者", "Keep the stakeholders informed."),
        ("deliverable", "成果物", "The deliverable is due Friday."),
        ("scope", "範囲・スコープ", "That's outside the project scope."),
        ("forecast", "予測・見込み", "The sales forecast looks strong."),
        ("backlog", "バックログ・残作業", "Our backlog keeps growing."),
        ("workflow", "ワークフロー・作業の流れ", "We streamlined the workflow."),
        ("bottleneck", "ボトルネック・隘路", "Testing is the bottleneck."),
        ("headcount", "人員数", "We need to increase headcount."),
        ("onboarding", "受け入れ・新人研修", "Onboarding takes about a week."),
        ("delegate", "委任する", "Delegate the task to your team."),
        ("escalate", "(上位に)報告・対応引き上げ", "Escalate the issue to your manager."),
        ("retrospective", "振り返り", "We hold a retrospective each sprint."),
        ("kickoff", "開始・キックオフ", "The project kickoff is tomorrow."),
        ("contingency", "不測の事態への備え", "We need a contingency plan."),
        ("capacity", "処理能力・余力", "The team is at full capacity."),
        ("turnaround", "対応時間・好転", "We need a quick turnaround."),
        ("agenda", "議題・予定", "Send the agenda before the meeting."),
        ("deadline", "締め切り", "We can't miss the deadline."),
        ("overtime", "残業", "He worked overtime all week."),
        ("metrics", "評価指標", "Track the key metrics weekly."),
        ("alignment", "認識合わせ・整合", "We need alignment on goals."),
        ("status update", "進捗報告", "Give me a quick status update."),
        ("workload", "仕事量", "Her workload is too heavy."),
        ("oversight", "監督・統括", "He provides project oversight."),
    ],
}

# Phrases (with quotations for religion / philosophy).
PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "キリスト教": [
        ("Love your neighbor as yourself.", "隣人を自分のように愛しなさい。〔聖書・マタイ〕"),
        ("The Lord is my shepherd; I shall not want.", "主は私の羊飼い。私は乏しいことがない。〔詩篇23〕"),
        ("Ask, and it shall be given you.", "求めよ、さらば与えられん。〔マタイ〕"),
        ("Father, forgive them, for they know not what they do.", "父よ、彼らをお赦しください。自分が何をしているか分からないのです。〔ルカ〕"),
        ("I am the way, the truth, and the life.", "私は道であり、真理であり、命である。〔ヨハネ〕"),
        ("Let any one of you who is without sin cast the first stone.", "あなたがたの中で罪のない者が、まず石を投げなさい。〔ヨハネ〕"),
        ("Faith as small as a mustard seed can move mountains.", "からし種ほどの信仰があれば山も動かせる。〔マタイ〕"),
        ("For God so loved the world.", "神は世を深く愛された。〔ヨハネ3:16〕"),
        ("Peace be with you.", "あなたに平安がありますように。"),
        ("Give us this day our daily bread.", "日ごとの糧を、今日もお与えください。〔主の祈り〕"),
        ("Thy will be done.", "み心が行われますように。〔主の祈り〕"),
        ("Blessed are the peacemakers.", "平和をつくる者は幸いである。〔山上の垂訓〕"),
        ("Do unto others as you would have them do unto you.", "人にしてほしいことを、人にもしなさい(黄金律)。〔ルカ〕"),
        ("Love is patient, love is kind.", "愛は忍耐強く、愛は親切である。〔コリント〕"),
        ("Amen.", "アーメン(まことに、そうでありますように)。"),
    ],
    "ユダヤ教": [
        ("Shalom.", "シャローム(平和を／こんにちは・さようなら)。"),
        ("Hear, O Israel: the Lord our God, the Lord is one.", "聞け、イスラエルよ。我らの神、主は唯一の主である。〔シェマ・申命記〕"),
        ("Next year in Jerusalem.", "来年こそエルサレムで。〔過越の結びの言葉〕"),
        ("Tikkun olam — repairing the world.", "世界を修復する(ティクン・オラム)。〔ユダヤ思想〕"),
        ("L'chaim! To life!", "ラハイム！人生に乾杯！"),
        ("Mazel tov!", "おめでとう！(幸運を)。"),
        ("Let my people go.", "我が民を去らせよ。〔出エジプト記〕"),
        ("Justice, justice shall you pursue.", "正義を、正義を追い求めよ。〔申命記〕"),
        ("Remember the Sabbath day, to keep it holy.", "安息日を覚えて、これを聖なる日とせよ。〔十戒〕"),
        ("Who is wise? One who learns from everyone.", "賢者とは誰か。すべての人から学ぶ者。〔ミシュナ〕"),
        ("If I am not for myself, who will be for me?", "自分が自分のためでなければ、誰が自分のためになろう。〔ヒレル〕"),
        ("Whoever saves one life saves the world entire.", "一つの命を救う者は、全世界を救う。〔タルムード〕"),
    ],
    "イスラム教": [
        ("Assalamu alaikum.", "あなたに平安あれ(挨拶)。"),
        ("Insha'Allah — God willing.", "神が望むなら(きっと)。"),
        ("Alhamdulillah — Praise be to God.", "神に称えあれ(感謝のことば)。"),
        ("Allahu akbar — God is the greatest.", "神は偉大なり。"),
        ("Bismillah — In the name of God.", "神の御名において(始める時に)。"),
        ("There is no god but God.", "神のほかに神はなし。〔信仰告白(シャハーダ)〕"),
        ("Seek knowledge from the cradle to the grave.", "揺りかごから墓場まで知を求めよ。〔ハディース〕"),
        ("The ink of the scholar is more sacred than the blood of the martyr.", "学者のインクは殉教者の血より尊い。〔ハディース〕"),
        ("Paradise lies at the feet of mothers.", "楽園は母の足元にある。〔ハディース〕"),
        ("Ramadan Mubarak.", "良いラマダンを(ラマダンおめでとう)。"),
        ("God does not burden a soul beyond what it can bear.", "神は人が耐えられぬ重荷を負わせない。〔コーラン〕"),
        ("The strong person is the one who controls his anger.", "強い者とは怒りを抑える者だ。〔ハディース〕"),
    ],
    "仏教": [
        ("All life involves suffering.", "一切は苦である(一切皆苦)。〔四諦〕"),
        ("Attachment is the root of suffering.", "執着は苦の根源である。〔仏教〕"),
        ("Peace comes from within. Do not seek it without.", "平安は内から来る。外に求めるな。〔ブッダ〕"),
        ("What we think, we become.", "我々は思うものになる。〔法句経〕"),
        ("Hatred does not cease by hatred, but only by love.", "憎しみは憎しみによって止まず、ただ愛によって止む。〔法句経〕"),
        ("Three things cannot be long hidden: the sun, the moon, and the truth.", "長くは隠せぬものが三つある。太陽、月、そして真実。〔ブッダ〕"),
        ("Be a lamp unto yourself.", "自らを灯火とせよ(自灯明)。〔ブッダ最後の教え〕"),
        ("This too shall pass.", "これもまた過ぎ去る(諸行無常)。"),
        ("May all beings be happy.", "一切の生きとし生けるものが幸せでありますように。〔慈悲の祈り〕"),
        ("Holding on to anger is like grasping a hot coal.", "怒りを抱くのは熱い炭を握るようなものだ。〔ブッダ〕"),
        ("The mind is everything. What you think you become.", "心がすべてだ。思うものに我々はなる。〔ブッダ〕"),
        ("Nirvana is the end of suffering.", "涅槃とは苦の終わりである。"),
    ],
    "哲学": [
        ("Man is the measure of all things.", "人間は万物の尺度である。〔プロタゴラス〕"),
        ("God is dead.", "神は死んだ。〔ニーチェ〕"),
        ("I know that I know nothing.", "私は自分が何も知らないと知っている(無知の知)。〔ソクラテス〕"),
        ("He who has a why to live can bear almost any how.", "なぜ生きるかを持つ者は、ほぼどんな状況にも耐えられる。〔ニーチェ〕"),
        ("Whereof one cannot speak, thereof one must be silent.", "語りえぬものについては、沈黙せねばならない。〔ウィトゲンシュタイン〕"),
        ("Hell is other people.", "地獄とは他人のことだ。〔サルトル〕"),
        ("Existence precedes essence.", "実存は本質に先立つ。〔サルトル〕"),
        ("We are condemned to be free.", "我々は自由の刑に処されている。〔サルトル〕"),
        ("One cannot step into the same river twice.", "人は同じ川に二度入ることはできない。〔ヘラクレイトス〕"),
        ("Happiness is the meaning and the purpose of life.", "幸福こそ人生の意味であり目的である。〔アリストテレス〕"),
        ("The owl of Minerva spreads its wings at dusk.", "ミネルヴァのフクロウは黄昏に飛び立つ。〔ヘーゲル〕"),
        ("Liberty consists in doing what one desires.", "自由とは欲することをなしうることにある。〔J.S.ミル〕"),
        ("Knowledge is power.", "知は力なり。〔フランシス・ベーコン〕"),
        ("The life of man is solitary, poor, nasty, brutish, and short.", "人間の生は孤独で貧しく、険悪で残忍で短い。〔ホッブズ〕"),
        ("To do is to be.", "なすことが、あることだ。〔哲学の警句〕"),
    ],
    "IT・ビルド/エラー": [
        ("The build failed.", "ビルドが失敗しました。"),
        ("The build succeeded.", "ビルドに成功しました。"),
        ("It works on my machine.", "私の環境では動くのですが。"),
        ("There's a syntax error on line 42.", "42行目に構文エラーがあります。"),
        ("Undefined reference to 'main'.", "'main'への未定義参照です。"),
        ("Segmentation fault (core dumped).", "セグメンテーション違反(コアダンプ)。"),
        ("Null pointer exception.", "ヌルポインタ例外です。"),
        ("Index out of bounds.", "配列の範囲外参照です。"),
        ("Module not found.", "モジュールが見つかりません。"),
        ("There's a missing dependency.", "依存関係が不足しています。"),
        ("There's a version conflict in the dependencies.", "依存関係のバージョン競合です。"),
        ("The tests are failing.", "テストが失敗しています。"),
        ("All tests passed.", "全テストが通りました。"),
        ("It throws an exception at runtime.", "実行時に例外が発生します。"),
        ("The server returned a 500 error.", "サーバーが500エラーを返しました。"),
        ("404 — page not found.", "404、ページが見つかりません。"),
        ("The endpoint is timing out.", "エンドポイントがタイムアウトしています。"),
        ("Permission denied.", "権限がありません(アクセス拒否)。"),
        ("Out of memory.", "メモリ不足です。"),
        ("Stack overflow.", "スタックオーバーフローです。"),
        ("The merge has conflicts.", "マージに競合があります。"),
        ("Please resolve the merge conflict.", "マージ競合を解消してください。"),
        ("Push your changes to the branch.", "変更をブランチにプッシュしてください。"),
        ("Pull the latest changes first.", "まず最新の変更をプルしてください。"),
        ("Let's roll back the deployment.", "デプロイをロールバックしましょう。"),
        ("Clear the cache and rebuild.", "キャッシュを消して再ビルドしてください。"),
        ("Check the logs for details.", "詳細はログを確認してください。"),
        ("It works in development but not in production.", "開発環境では動きますが本番では動きません。"),
        ("Try restarting the server.", "サーバーを再起動してみてください。"),
        ("This API is deprecated.", "このAPIは非推奨です。"),
        ("Increase the timeout value.", "タイムアウト値を大きくしてください。"),
        ("The container won't start.", "コンテナが起動しません。"),
        ("The function returns undefined.", "関数がundefinedを返します。"),
        ("It's a type mismatch error.", "型の不一致エラーです。"),
        ("The page won't render.", "ページが描画されません。"),
        ("The CI pipeline is broken.", "CIパイプラインが壊れています。"),
    ],
    "AI指示": [
        ("Summarize this in three bullet points.", "これを3つの箇条書きで要約して。"),
        ("Explain it like I'm five.", "5歳児にも分かるように説明して。"),
        ("Translate this into natural English.", "これを自然な英語に訳して。"),
        ("Proofread this and fix any mistakes.", "これを校正して誤りを直して。"),
        ("Make it more concise.", "もっと簡潔にして。"),
        ("Make it sound more formal.", "もっとフォーマルな表現にして。"),
        ("Give me a few concrete examples.", "具体例をいくつか挙げて。"),
        ("Rewrite it in a friendly tone.", "親しみやすい口調で書き直して。"),
        ("Walk me through it step by step.", "順を追って説明して。"),
        ("Keep it under 100 words.", "100語以内にして。"),
        ("List the pros and cons.", "長所と短所を挙げて。"),
        ("Continue from where you left off.", "続きから書いて。"),
        ("Cite your sources.", "出典を示して。"),
        ("Double-check your answer.", "答えを再確認して。"),
        ("Act as an expert in this field.", "この分野の専門家として答えて。"),
    ],
    "管理・進行": [
        ("Let's reschedule the meeting.", "会議をリスケしましょう。"),
        ("Can we push the deadline?", "締め切りを延ばせますか？"),
        ("Let's prioritize the backlog.", "バックログに優先順位をつけましょう。"),
        ("What's the status of the project?", "プロジェクトの進捗はどうですか？"),
        ("Let's set a milestone for next week.", "来週のマイルストーンを設定しましょう。"),
        ("Who's the point of contact?", "窓口は誰ですか？"),
        ("Let's delegate this task.", "このタスクを誰かに任せましょう。"),
        ("I'll escalate this to management.", "これを上(管理層)に上げます。"),
        ("Let's do a quick status update.", "手短に進捗共有をしましょう。"),
        ("We need to manage expectations.", "期待値を調整する必要があります。"),
        ("Let's align on priorities.", "優先順位をすり合わせましょう。"),
        ("Could you send a follow-up email?", "フォローのメールを送ってもらえますか？"),
        ("Let's schedule a kickoff meeting.", "キックオフ会議を設定しましょう。"),
        ("The deadline has been moved up.", "締め切りが前倒しになりました。"),
        ("Let's allocate more resources.", "リソースをもっと割り当てましょう。"),
        ("We're over budget.", "予算を超過しています。"),
        ("Let's hold a retrospective.", "振り返り(レトロ)をしましょう。"),
        ("Let's break this into smaller tasks.", "これを小さなタスクに分けましょう。"),
        ("Keep the stakeholders in the loop.", "関係者に共有し続けてください。"),
        ("Let's circle back on this next week.", "この件は来週また話しましょう。"),
    ],
}


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

        w_added = w_skipped = 0
        per_domain: dict[str, int] = {}
        for domain, items in WORDS_BY_DOMAIN.items():
            for en, ja, ex in items:
                if en.lower() in w_existing:
                    conn.execute(
                        "UPDATE words SET example = ? "
                        "WHERE LOWER(english) = LOWER(?) AND COALESCE(example, '') = ''",
                        (ex, en),
                    )
                    w_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, domain, "700"),
                )
                w_existing.add(en.lower())
                w_added += 1
                per_domain[domain] = per_domain.get(domain, 0) + 1

        ph_added = ph_skipped = 0
        per_scene: dict[str, int] = {}
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1
                per_scene[scene] = per_scene.get(scene, 0) + 1

    print(f"words:   +{w_added} (skipped {w_skipped})  {per_domain}")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})  {per_scene}")
    with db() as conn:
        empty = conn.execute(
            "SELECT COUNT(*) FROM words WHERE COALESCE(example, '') = ''"
        ).fetchone()[0]
        print(
            "totals -> phrases:",
            conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
            "words:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
            "/ words without example:", empty,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
