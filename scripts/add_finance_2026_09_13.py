# ruff: noqa: E501
"""金融新ドメイン(2026-09-13・authored by Claude)。銀行・金融/投資・市場/
企業金融/個人金融/フィンテック/リスク・規制の6サブテーマで約122語を追加。

背景: 前回セッションでも同様の草案(約122語)を作成したが、セッション
スクラッチパッドにのみ保存され、セッション終了時に失われた。本ファイルは
その再作成であり、実リポジトリ配下に保存することで作業を確実に残す。

除外語(既存語との重複として意図的に除外・DB内で確認済み):
dividend, equity, debt, bankruptcy, arbitrage, central bank, bull market,
bear market, liquidity, market capitalization, short selling, margin call,
moral hazard, IPO(initial public offering (ipo)として既存), stock split,
commodity, collateral, mortgage, leverage, escrow, fiduciary duty, overdraft,
checking account, debit card, cryptocurrency, blockchain,
NPV(net present value (npv)として既存), IRR(internal rate of return (irr)として既存),
WACC(weighted average cost of capital (wacc)として既存),
LBO(leveraged buyout (lbo)として既存), capital structure

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_finance_2026_09_13.py
(このスクリプトは他の並行ドラフトとのクロスチェック後にまとめて実行する
想定のため、ドラフト作成時点ではまだ実行しない。)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 銀行・金融 (17: "bank"は既存語(多義語ドメイン)と重複のため除外) ---
    ("retail banking", "企業向けではなく、一般の個人顧客を対象とした預金・融資・決済などの銀行業務。", "名詞", "Retail banking focuses on everyday services like checking accounts and personal loans for individual customers.", "金融", "650"),
    ("commercial bank", "預金の受け入れと企業・個人への貸付を主な業務とする、一般的な銀行。投資銀行とは業務内容が区別される。", "名詞", "The company took out a business loan from a commercial bank to expand its factory.", "金融", "650"),
    ("investment bank", "企業の株式・債券の発行支援や、合併・買収の助言など、資金調達や大型の金融取引を専門に扱う金融機関。", "名詞", "The investment bank advised the two companies throughout their merger negotiations.", "金融", "700"),
    ("savings account", "利息を得ることを主な目的として、日常的な引き出しよりも貯蓄のために資金を預けておく銀行口座。", "名詞", "He transfers a portion of his paycheck into a savings account every month.", "金融", "600"),
    ("correspondent bank", "別の国や地域にある銀行に代わって、送金や決済などの業務を代行する提携先の銀行。国際送金網でよく使われる。", "名詞", "The Japanese bank used a correspondent bank in New York to process the dollar-denominated wire transfer.", "金融", "850"),
    ("shadow banking", "ヘッジファンドやノンバンク型の貸金業者など、通常の銀行規制を受けずに信用仲介を行う金融機関や仕組みの総称。", "名詞", "Regulators worried that risks were building up in the shadow banking sector, outside their usual oversight.", "金融", "850"),
    ("bank run", "銀行の支払能力に対する不安から、預金者が一斉に預金を引き出そうとする現象。", "名詞", "Rumors about the bank's finances triggered a bank run, with customers lining up to withdraw their savings.", "金融", "800"),
    ("deposit insurance", "銀行が破綻した場合に備え、預金者の預金を一定額まで公的機関が保証する制度。", "名詞", "Thanks to deposit insurance, customers didn't lose their savings even after the bank failed.", "金融", "750"),
    ("Federal Reserve", "アメリカの中央銀行制度。金利の誘導や通貨供給量の調整などを通じて金融政策を運営する。", "名詞", "The Federal Reserve raised interest rates to help slow down inflation.", "金融", "750"),
    ("quantitative easing", "中央銀行が国債などの資産を大量に買い入れ、市場に資金を供給することで景気を刺激する非伝統的な金融政策。", "名詞", "The central bank turned to quantitative easing after interest rates were already near zero.", "金融", "850"),
    ("discount rate", "中央銀行が民間銀行に資金を貸し出す際に適用する金利。金融政策の代表的な手段の一つ。", "名詞", "When the central bank lowers the discount rate, it becomes cheaper for banks to borrow money.", "金融", "800"),
    ("federal funds rate", "アメリカの銀行同士が中央銀行に預けている準備金を一晩だけ貸し借りする際に適用される金利。金融政策の主要な指標。", "名詞", "Markets closely watch every change in the federal funds rate for signs of the central bank's next move.", "金融", "800"),
    ("prime rate", "銀行が信用度の高い優良企業向けの貸付に適用する、基準となる優遇金利。", "名詞", "Because the company had an excellent credit history, the bank offered it a loan at the prime rate.", "金融", "750"),
    ("reserve requirement", "銀行が受け入れた預金のうち、貸し出しに回さず中央銀行などに準備金として保有しておくよう義務付けられた割合。", "名詞", "By raising the reserve requirement, the central bank forced banks to hold more cash and lend out less.", "金融", "800"),
    ("money market account", "普通預金より高い利息が付く一方で、小切手の振り出しなど一定の流動性も保てる預金口座。", "名詞", "She keeps her emergency savings in a money market account because it pays more interest than a regular savings account.", "金融", "700"),
    ("certificate of deposit", "一定期間資金を引き出さないことを条件に、通常の預金より高い利息を受け取れる定期預金商品。", "名詞", "He locked his savings into a one-year certificate of deposit to earn a higher interest rate.", "金融", "700"),
    ("wire transfer", "銀行間のネットワークを通じて、口座から口座へ電子的に資金を送金すること。", "名詞", "She arranged a wire transfer to pay the overseas supplier directly from her business account.", "金融", "650"),
    # --- 投資・市場 (34) ---
    ("stock market", "株式が売買される市場全体を指す言葉。証券取引所での取引に加え、広く株式投資を取り巻く市場環境も含む。", "名詞", "The stock market rallied after the company reported better-than-expected earnings.", "金融", "600"),
    ("portfolio", "投資家が保有する株式・債券・その他の資産の組み合わせ全体。", "名詞", "Her investment portfolio includes a mix of stocks, bonds, and real estate.", "金融", "650"),
    ("diversification", "値動きの異なる複数の資産に分散して投資することで、全体としてのリスクを抑えようとする手法。", "名詞", "Diversification across different industries helped cushion her portfolio when one sector declined.", "金融", "700"),
    ("mutual fund", "多数の投資家から集めた資金をまとめ、専門の運用会社が株式や債券などに分散して投資・運用する金融商品。", "名詞", "He invests a fixed amount every month in a mutual fund that holds a broad mix of stocks.", "金融", "650"),
    ("index fund", "日経平均株価やS&P500など特定の株価指数と連動する運用成績を目指す投資信託。個別銘柄を選ぶより低コストで市場全体に投資できる。", "名詞", "Because index funds simply track the market, they usually charge much lower fees than actively managed funds.", "金融", "700"),
    ("hedge fund", "富裕層や機関投資家など限られた投資家から資金を集め、空売りやデリバティブなど幅広い手法を用いて積極的な運用を行う私募の投資ファンド。", "名詞", "The hedge fund used complex trading strategies that ordinary mutual funds are not allowed to use.", "金融", "800"),
    ("exchange-traded fund", "株価指数などに連動するよう設計されながら、株式と同じように取引所でリアルタイムに売買できる投資信託。ETFとも呼ばれる。", "名詞", "She bought shares of an exchange-traded fund that tracks the technology sector.", "金融", "750"),
    ("private equity", "証券取引所に上場していない企業の株式に投資し、経営改善などを通じて企業価値を高めた後に売却して利益を得る投資形態、またはそれを行う投資会社。", "名詞", "The private equity firm bought a controlling stake in the struggling manufacturer and restructured its operations.", "金融", "800"),
    ("venture capital", "高い成長性が見込まれる未上場のスタートアップ企業に対し、株式と引き換えに資金を提供する投資形態。", "名詞", "The startup raised its first round of venture capital to help build its product.", "金融", "750"),
    ("angel investor", "創業間もないスタートアップに対し、自身の資産から個人的に資金を提供する富裕な個人投資家。", "名詞", "An angel investor provided the seed money that let the two founders quit their jobs and build a prototype.", "金融", "750"),
    ("broker", "顧客に代わって株式や債券などの売買を仲介し、手数料を受け取る個人や会社。", "名詞", "She called her broker to place an order to buy shares before the market closed.", "金融", "650"),
    ("brokerage", "顧客の注文を仲介して株式や債券などの売買を行う証券会社、またはその事業そのもの。", "名詞", "He opened an account with an online brokerage to start trading stocks himself.", "金融", "650"),
    ("underwriting", "証券会社などが、新たに発行される株式や債券を発行体から一括して買い取り、投資家に販売する引き受け業務。", "名詞", "The bank handled the underwriting of the company's new bond issue, guaranteeing it would sell the entire offering.", "金融", "800"),
    ("prospectus", "株式や投資信託などの新規募集にあたり、事業内容やリスクなどを投資家に開示するために作成される説明書類。", "名詞", "Before investing, she carefully read the fund's prospectus to understand its fees and risks.", "金融", "800"),
    ("initial coin offering", "企業やプロジェクトが、独自に発行する暗号資産(トークン)を投資家に販売して資金を調達する方法。", "名詞", "The startup raised millions of dollars through an initial coin offering before it had even launched a product.", "金融", "800"),
    ("secondary offering", "株式が既に上場した後、企業や既存株主が追加の株式を新たに市場で売り出すこと。", "名詞", "The company arranged a secondary offering to raise additional funds after its shares had risen in value.", "金融", "800"),
    ("market order", "価格を指定せず、その時点の市場価格ですぐに売買を成立させることを指示する注文方法。", "名詞", "He placed a market order to sell his shares immediately at whatever price the market offered.", "金融", "700"),
    ("limit order", "指定した価格以下で買う、または指定した価格以上で売るという条件を付けて出す注文方法。", "名詞", "She set a limit order to buy the stock only if its price dropped below $50.", "金融", "700"),
    ("volatility", "資産の価格が短期間にどれだけ大きく変動するかを示す度合い。", "名詞", "The stock's price swung wildly, reflecting the high volatility of the tech sector that week.", "金融", "750"),
    ("blue chip stock", "長年にわたり安定した業績と信頼性を持つ、大企業の株式。", "名詞", "Retirees often prefer blue chip stocks because their dividends and prices tend to be relatively stable.", "金融", "700"),
    ("coupon rate", "債券の額面金額に対して、発行体が保有者に定期的に支払う利息の割合。", "名詞", "The bond has a coupon rate of 4%, meaning it pays $40 a year for every $1,000 of face value.", "金融", "800"),
    ("maturity", "債券などの金融商品において、元本が返済されるべき満期の日。", "名詞", "The bond reaches maturity in ten years, at which point the issuer must repay the full face value.", "金融", "700"),
    ("treasury bond", "国が財政資金を調達するために発行する、長期の債券。信用度が高く安全な投資先とされる。", "名詞", "Investors often turn to treasury bonds when they want a safer place to park their money.", "金融", "700"),
    ("municipal bond", "地方自治体が、公共事業などの資金を調達するために発行する債券。", "名詞", "The city issued municipal bonds to fund the construction of a new bridge.", "金融", "750"),
    ("credit rating", "企業や国などの発行体が債務を期限通りに返済する能力を、第三者機関が評価し記号で示したもの。", "名詞", "The country's credit rating was downgraded after concerns grew about its ability to repay its debt.", "金融", "750"),
    ("futures contract", "将来のある時点で、特定の商品や金融資産をあらかじめ決めた価格で売買することを約束する契約。", "名詞", "The farmer used a futures contract to lock in today's price for the wheat he would harvest months later.", "金融", "800"),
    ("options contract", "将来の一定期間内に、特定の資産をあらかじめ決めた価格で売買する権利(ただし義務ではない)を売買する契約。", "名詞", "She bought an options contract that gave her the right, but not the obligation, to buy the stock at a fixed price.", "金融", "800"),
    ("call option", "あらかじめ定めた価格で原資産を買う権利を与える金融派生商品。", "名詞", "He purchased a call option, betting that the stock's price would rise above the strike price before it expired.", "金融", "800"),
    ("put option", "あらかじめ定めた価格で原資産を売る権利を与える金融派生商品。", "名詞", "She bought a put option as insurance in case the stock price fell sharply.", "金融", "800"),
    ("speculation", "短期的な価格変動から利益を得ることを目的として、リスクを取って資産を売買すること。", "名詞", "Rampant speculation drove the stock's price far above what the company's earnings could justify.", "金融", "700"),
    ("day trading", "同じ取引日のうちに株式などを売買し、翌日まで持ち越さずに利益を狙う短期的な取引手法。", "名詞", "He quit his job to try day trading full time, buying and selling stocks within the same session.", "金融", "700"),
    ("technical analysis", "企業の業績ではなく、過去の価格や取引量の推移をグラフ化して将来の値動きを予測しようとする分析手法。", "名詞", "Using technical analysis, she studied the stock's chart patterns to decide when to buy.", "金融", "750"),
    ("fundamental analysis", "企業の財務諸表や業界動向などを調べ、その企業の本質的な価値を評価しようとする分析手法。", "名詞", "He relies on fundamental analysis, studying a company's earnings and debt before deciding to invest.", "金融", "750"),
    ("dividend yield", "株価に対して、1年間に支払われる配当金の割合を示す指標。", "名詞", "The utility company's stock is popular among income investors because of its high dividend yield.", "金融", "750"),
    # --- 企業金融 (32) ---
    ("balance sheet", "ある時点における企業の資産・負債・純資産の状況を一覧にした財務諸表。貸借対照表。", "名詞", "The company's balance sheet showed more assets than liabilities, indicating a strong financial position.", "金融", "650"),
    ("income statement", "一定期間における企業の収益・費用・利益をまとめた財務諸表。損益計算書。", "名詞", "The income statement revealed that revenue had grown, but rising costs had squeezed profits.", "金融", "650"),
    ("cash flow statement", "一定期間における企業の現金の流入と流出を、営業・投資・財務の活動別にまとめた財務諸表。", "名詞", "The cash flow statement showed that the company was generating solid cash from its core operations.", "金融", "700"),
    ("retained earnings", "企業が稼いだ利益のうち、株主への配当として支払わずに社内に留保した部分の累積額。", "名詞", "Instead of paying a dividend, the company used its retained earnings to fund new research projects.", "金融", "750"),
    ("working capital", "企業の流動資産から流動負債を差し引いた額。日常の事業運営に必要な資金の余裕を示す。", "名詞", "The company needed more working capital to cover payroll while waiting for customers to pay their invoices.", "金融", "700"),
    ("accounts receivable", "商品やサービスを販売した企業が、顧客からまだ受け取っていない代金の債権。", "名詞", "The company's accounts receivable grew because several large customers were slow to pay their invoices.", "金融", "700"),
    ("accounts payable", "企業が仕入先などに対して、まだ支払っていない代金の債務。", "名詞", "The firm's accounts payable increased as it delayed payments to suppliers to conserve cash.", "金融", "700"),
    ("amortization", "無形資産の取得費用や借入金の元本を、一定の期間にわたって少しずつ費用や返済として計上していくこと。", "名詞", "The patent's cost is spread out through amortization over its expected useful life of ten years.", "金融", "750"),
    ("goodwill", "企業を買収する際に、対象企業の純資産の時価を上回って支払われた金額。ブランド力や顧客基盤などの目に見えない価値を反映するとされる。", "名詞", "The acquiring company recorded a large amount of goodwill because it paid well above the target's book value.", "金融", "800"),
    ("valuation", "企業や資産が持つ経済的な価値を、財務データなどに基づいて評価すること、またはその評価額。", "名詞", "Investors debated whether the startup's billion-dollar valuation was justified by its actual revenue.", "金融", "700"),
    ("shareholder equity", "企業の総資産から総負債を差し引いた、株主に帰属する純資産の額。", "名詞", "Shareholder equity grew steadily as the company reinvested its profits year after year.", "金融", "750"),
    ("stock buyback", "企業が市場に流通する自社の株式を買い戻すこと。発行済み株式数を減らし、一株当たりの価値を高める効果がある。", "名詞", "The company announced a stock buyback, using its excess cash to purchase shares from the open market.", "金融", "750"),
    ("hostile takeover", "買収対象企業の経営陣の同意を得ないまま、株式の取得などを通じて経営権を握ろうとする買収。", "名詞", "The board rejected the offer, fearing it was the opening move of a hostile takeover.", "金融", "800"),
    ("book value", "企業の資産から負債を差し引いた、会計上の帳簿に基づく純資産の価値。", "名詞", "The stock traded well below its book value, making some investors see it as undervalued.", "金融", "750"),
    ("price-to-earnings ratio", "株価を一株当たり利益で割って算出する、株式の割高・割安を判断するための代表的な指標。", "名詞", "A high price-to-earnings ratio suggested that investors expected the company's profits to keep growing rapidly.", "金融", "800"),
    ("corporate bond", "企業が事業資金を調達するために発行する債券。", "名詞", "The company issued a corporate bond to raise funds for building a new factory.", "金融", "700"),
    ("junk bond", "信用格付けが低く、債務不履行のリスクが比較的高いとされる代わりに高い利回りを提供する債券。", "名詞", "The struggling airline could only raise money by issuing junk bonds with a high interest rate.", "金融", "800"),
    ("earnings per share", "企業の純利益を発行済み株式数で割って算出する、株式一株当たりの利益額。", "名詞", "Earnings per share rose even though total profit stayed flat, because the company had bought back shares.", "金融", "750"),
    ("operating margin", "売上高に対する営業利益の割合。本業でどれだけ効率的に利益を生み出しているかを示す。", "名詞", "The company's operating margin improved after it cut costs in its manufacturing process.", "金融", "800"),
    ("capital expenditure", "工場や設備など、長期にわたって使用する資産を取得・整備するために支出する費用。", "名詞", "The airline's capital expenditure this year went mostly toward purchasing new fuel-efficient planes.", "金融", "800"),
    ("spin-off", "企業が事業の一部門を切り離し、独立した新たな会社として設立すること。", "名詞", "The conglomerate created a spin-off for its slower-growing division so investors could value each business separately.", "金融", "800"),
    ("divestiture", "企業が保有する事業や資産の一部を売却したり手放したりすること。", "名詞", "The company announced the divestiture of its overseas retail chain to focus on its core business.", "金融", "850"),
    ("recapitalization", "企業が負債と株式の構成比率を見直すなど、資本構成を組み替えること。", "名詞", "The struggling firm underwent a recapitalization, converting much of its debt into equity to survive.", "金融", "850"),
    ("treasury stock", "企業が発行した後に自ら買い戻し、まだ再発行や消却をせずに保有している自社株式。", "名詞", "Shares held as treasury stock don't carry voting rights or receive dividends.", "金融", "850"),
    ("par value", "株式や債券の券面に記載された名目上の価格。市場での実際の取引価格とは異なる。", "名詞", "The stock has a par value of just one cent per share, far below its actual trading price.", "金融", "800"),
    ("outstanding shares", "現在、投資家によって保有されている、企業が発行済みの株式の総数。自己株式(金庫株)は通常含まれない。", "名詞", "The company's earnings per share are calculated by dividing net income by its outstanding shares.", "金融", "750"),
    ("credit facility", "銀行などの金融機関が企業に対して、必要な時に一定の限度額まで借り入れられるよう事前に用意しておく融資の枠組み。", "名詞", "The company arranged a credit facility with its bank so it could draw on funds whenever cash flow tightened.", "金融", "800"),
    ("revolving credit facility", "一定の限度額の範囲内であれば、企業が何度でも借り入れと返済を繰り返すことができる融資の仕組み。", "名詞", "The retailer relies on a revolving credit facility to manage cash flow during the slow season between holidays.", "金融", "850"),
    ("syndicated loan", "一行だけでは引き受けきれないほど巨額の融資を、複数の銀行が団を組んで共同で提供する貸付。", "名詞", "A group of banks provided a syndicated loan to finance the company's multibillion-dollar acquisition.", "金融", "850"),
    ("convertible bond", "あらかじめ定めた条件のもとで、保有者の判断により発行企業の株式に転換できる権利が付いた債券。", "名詞", "Investors liked the convertible bond because it offered steady interest with the option to convert into stock later.", "金融", "800"),
    ("preferred stock", "普通株よりも配当や倒産時の残余財産の分配で優先される一方、通常は議決権を持たない株式。", "名詞", "Preferred stock pays a fixed dividend and is paid out before common stockholders if the company is liquidated.", "金融", "750"),
    ("common stock", "株主総会での議決権を持つ、企業の最も基本的な株式の種類。", "名詞", "As a holder of common stock, she was entitled to vote at the company's annual shareholder meeting.", "金融", "650"),
    # --- 個人金融 (21) ---
    ("personal finance", "個人や家計における収入・支出・貯蓄・投資などのお金の管理全般。", "名詞", "She took an online course on personal finance to learn how to budget and save more effectively.", "金融", "600"),
    ("budgeting", "収入と支出の計画を立て、お金の使い道を管理すること。", "名詞", "Careful budgeting helped the young couple save enough for a down payment on their first apartment.", "金融", "600"),
    ("net worth", "個人が保有する資産の総額から負債の総額を差し引いた、実質的な財産の額。", "名詞", "His net worth grew steadily as he paid down his mortgage and his investments gained value.", "金融", "650"),
    ("emergency fund", "失業や病気など予期しない出費に備えて、あらかじめ確保しておく現金の蓄え。", "名詞", "Financial advisors often recommend keeping three to six months of expenses in an emergency fund.", "金融", "600"),
    ("retirement account", "老後の生活資金を準備するために、税制上の優遇を受けながら積み立てる専用の口座。", "名詞", "He contributes a portion of every paycheck to his retirement account.", "金融", "650"),
    ("individual retirement account", "アメリカで個人が任意で開設し、税制上の優遇を受けながら老後資金を積み立てられる退職口座。", "名詞", "She opened an individual retirement account to supplement the pension from her employer.", "金融", "700"),
    ("compound interest", "元金だけでなく、それまでに発生した利息にもさらに利息が付いていく仕組み。長期的には資産を大きく増やす効果を持つ。", "名詞", "Thanks to compound interest, even a small amount saved in her twenties grew substantially by retirement.", "金融", "650"),
    ("simple interest", "元金に対してのみ利息が計算され、発生した利息には追加の利息が付かない仕組み。", "名詞", "The short-term loan charged simple interest, calculated only on the original amount borrowed.", "金融", "650"),
    ("credit score", "個人の借入や返済の履歴などをもとに算出される、信用力を表す数値。", "名詞", "A high credit score helped her qualify for a mortgage with a lower interest rate.", "金融", "600"),
    ("credit history", "個人がこれまでにどのように借入をし、返済してきたかについての記録。", "名詞", "Because he had no credit history, the bank asked for a co-signer on his first loan.", "金融", "600"),
    ("credit limit", "クレジットカードや融資枠において、借り入れることができる金額の上限。", "名詞", "She kept her spending well below her credit limit to maintain a healthy credit score.", "金融", "600"),
    ("installment loan", "借りた金額を、決まった回数・金額の分割払いで返済していく融資の形態。", "名詞", "He financed the car with an installment loan, paying a fixed amount every month for five years.", "金融", "650"),
    ("amortization schedule", "ローンの各返済回について、元金と利息の内訳、残高の推移を示した一覧表。", "名詞", "The amortization schedule showed that most of her early mortgage payments went toward interest rather than principal.", "金融", "750"),
    ("annual percentage rate", "手数料なども含めた、借入にかかる実質的な年間コストを示す割合。ローン商品を比較する際の目安として使われる。", "名詞", "She compared several credit cards by looking at their annual percentage rate before applying.", "金融", "700"),
    ("refinance", "既存の借入を、より有利な金利や条件の新たな借入に組み替えること。", "動詞", "Falling interest rates prompted many homeowners to refinance their mortgages.", "金融", "700"),
    ("subprime lending", "信用力が低いとされる借り手に対して、通常より高い金利で行われる融資。", "名詞", "Subprime lending expanded rapidly before the financial crisis, as lenders offered loans to riskier borrowers.", "金融", "800"),
    ("foreclosure", "住宅ローンなどの返済が長期間滞った借り手から、貸し手が担保となっている不動産を法的手続きを経て差し押さえ、売却すること。", "名詞", "After missing payments for months, the family faced foreclosure and eventually lost their home.", "金融", "800"),
    ("payday loan", "次の給料日までのつなぎとして、短期間かつ高金利で借りる小口の融資。", "名詞", "Struggling to cover an unexpected bill, she took out a payday loan even though the interest rate was steep.", "金融", "700"),
    ("peer-to-peer lending", "銀行を介さず、インターネット上のプラットフォームを通じて個人同士が直接資金を貸し借りする仕組み。", "名詞", "Instead of going to a bank, he borrowed the money through a peer-to-peer lending platform.", "金融", "750"),
    ("crowdfunding", "インターネットを通じて不特定多数の人から少額ずつ資金を集める資金調達の方法。", "名詞", "The inventor raised enough money through crowdfunding to start manufacturing her product.", "金融", "650"),
    ("pension fund", "従業員や加入者の退職後の年金給付に充てるため、掛け金を積み立てて運用する基金。", "名詞", "The pension fund invests contributions from thousands of workers in stocks, bonds, and real estate.", "金融", "700"),
    ("annuity", "保険会社などに一定の金額を支払う代わりに、契約に基づいて将来一定期間にわたり定期的な給付を受け取る金融商品。", "名詞", "He purchased an annuity to guarantee himself a steady stream of income throughout retirement.", "金融", "800"),
    # --- フィンテック (7) ---
    ("mobile banking", "スマートフォンなどの携帯端末上のアプリを通じて、残高照会や送金などの銀行取引を行うサービス。", "名詞", "Mobile banking lets her check her account balance and pay bills without visiting a branch.", "金融", "600"),
    ("digital wallet", "クレジットカード情報や電子マネーなどをスマートフォン上に保存し、支払いに利用できるようにしたアプリやサービス。", "名詞", "He stores his credit card information in a digital wallet so he can pay just by tapping his phone.", "金融", "600"),
    ("peer-to-peer payment", "スマートフォンアプリなどを通じて、個人が銀行を介さず直接他の個人に送金できる仕組み。", "名詞", "She used a peer-to-peer payment app to split the dinner bill with her friends instantly.", "金融", "650"),
    ("robo-advisor", "アルゴリズムを用いて、投資家のリスク許容度や目標に応じた資産運用の助言や運用そのものを自動的に行うオンラインサービス。", "名詞", "Instead of hiring a financial planner, he let a robo-advisor automatically manage his investment portfolio.", "金融", "700"),
    ("insurtech", "テクノロジーを活用して、保険商品の設計や販売、保険金請求の処理などを効率化・革新する動きや企業。", "名詞", "The insurtech startup used an app and sensors to offer car insurance priced by how safely people actually drove.", "金融", "750"),
    ("regtech", "テクノロジーを活用して、金融機関が規制への対応やコンプライアンス業務を効率的に行えるようにする技術やサービス。", "名詞", "The bank adopted regtech software to automatically flag suspicious transactions for anti-money-laundering compliance.", "金融", "800"),
    ("open banking", "顧客の同意のもとで、銀行が保有する口座情報などを外部の企業とAPIを通じて共有する仕組み。", "名詞", "Open banking allows a budgeting app to securely pull transaction data from several of her bank accounts at once.", "金融", "800"),
    # --- リスク・規制 (10) ---
    ("systemic risk", "ある金融機関や市場の問題が連鎖的に広がり、金融システム全体の安定を脅かすリスク。", "名詞", "Regulators worried that the failure of one large bank could pose a systemic risk to the entire financial system.", "金融", "850"),
    ("credit risk", "貸し手が、借り手による元本や利息の支払いが滞ったり行われなかったりする可能性から負うリスク。", "名詞", "The bank charged a higher interest rate to compensate for the borrower's greater credit risk.", "金融", "750"),
    ("counterparty risk", "取引の相手方が契約上の義務を履行できなくなることによって生じるリスク。", "名詞", "Before entering the derivatives contract, the firm carefully assessed the counterparty risk posed by the other party.", "金融", "850"),
    ("stress test", "深刻な景気後退や市場の混乱などを想定し、金融機関がその状況でも十分な資本を維持できるかを検証する審査。", "名詞", "The bank passed the regulator's stress test, showing it could withstand a severe economic downturn.", "金融", "800"),
    ("too big to fail", "金融機関の規模や他機関との結びつきが大きすぎるため、破綻すると金融システム全体に深刻な影響を及ぼすと見なされる状態。政府による救済が正当化される根拠として使われることが多い。", "名詞", "Critics argued that some banks had become too big to fail, forcing the government to bail them out during the crisis.", "金融", "850"),
    ("capital adequacy ratio", "銀行が抱えるリスクに対して、どれだけの自己資本を保有しているかを示す指標。金融システムの健全性を測る規制上の基準として使われる。", "名詞", "Regulators require banks to maintain a minimum capital adequacy ratio to ensure they can absorb unexpected losses.", "金融", "900"),
    ("Basel accords", "国際決済銀行のバーゼル銀行監督委員会が策定した、銀行の自己資本比率などに関する国際的な規制の枠組み。", "名詞", "Banks around the world adjusted their risk management practices to comply with the Basel accords.", "金融", "900"),
    ("insider trading", "一般に公開されていない重要な内部情報を利用して、株式などの売買を行う違法な行為。", "名詞", "The executive was charged with insider trading after selling his shares just before the bad news became public.", "金融", "800"),
    ("money laundering", "犯罪などで得た不正な資金の出どころを分からなくするため、複数の取引を経由させて合法な資金であるかのように見せかける行為。", "名詞", "The bank was fined heavily for failing to detect a money laundering scheme running through its accounts.", "金融", "800"),
    ("regulatory compliance", "金融機関などが、法律や監督当局が定める規則・基準を遵守すること。", "名詞", "The firm hired additional staff to strengthen its regulatory compliance after the new rules took effect.", "金融", "800"),
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
