"""17分野の英単語・フレーズ追加シード（2026-07-01）。

指定分野（電気工学/電子工学/法律/政治/経済学/経営/DIY工具/インターネット/
ロボット工学/家電/航空工学/航空(管制・乗務)/気象/地学/原子力工学/無線/家事）の
実用語彙を追加する。domain は既存カテゴリに寄せる方針（下表）。

  電気工学・電子工学・無線 → 電気電子
  法律 → 法律 / 政治 → ニュース / 経済学 → 経済学 / 経営 → ビジネス
  DIY工具・ロボット工学 → 機械工学 / インターネット → IT / 家電 → 家電
  航空工学・航空(管制/乗務) → 航空・宇宙 / 気象・地学 → 地学
  原子力工学 → 物理 / 家事 → 生活

再実行安全: 既存 english（小文字比較）と一致する語/フレーズはスキップする。
words.detail は空のまま挿入し、後段 build_details.py で AI 生成する。

使い方:
  python scripts/seed_domains_20260701.py            # 挿入
  python scripts/seed_domains_20260701.py --dry-run  # 件数だけ確認
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, part_of_speech, example, level, domain)
WORDS: list[tuple[str, str, str, str, str, str]] = []
# (english, japanese, scene)
PHRASES: list[tuple[str, str, str]] = []


def W(domain, level, rows):
    for en, ja, pos, ex in rows:
        WORDS.append((en, ja, pos, ex, level, domain))


def P(scene, rows):
    for en, ja in rows:
        PHRASES.append((en, ja, scene))


# ─────────────────────────────────────────────────────────────
# 電気工学（→ 電気電子）
# ─────────────────────────────────────────────────────────────
W("電気電子", "800", [
    ("voltage", "電圧", "名詞", "The voltage across the resistor is 5 volts."),
    ("current", "電流", "名詞", "A large current flows through the coil."),
    ("resistance", "抵抗", "名詞", "Copper has low electrical resistance."),
    ("capacitor", "コンデンサ", "名詞", "The capacitor stores electric charge."),
    ("inductor", "インダクタ・コイル", "名詞", "An inductor opposes changes in current."),
    ("alternating current", "交流", "名詞", "Household outlets supply alternating current."),
    ("direct current", "直流", "名詞", "Batteries provide direct current."),
    ("circuit breaker", "遮断器・ブレーカー", "名詞", "The circuit breaker tripped during the surge."),
    ("grounding", "接地・アース", "名詞", "Proper grounding prevents electric shock."),
    ("transformer", "変圧器", "名詞", "The transformer steps down the voltage."),
    ("conductor", "導体", "名詞", "Metals are good conductors of electricity."),
    ("insulator", "絶縁体", "名詞", "Rubber is used as an insulator."),
    ("power grid", "送電網", "名詞", "A blackout hit the regional power grid."),
    ("watt", "ワット", "名詞", "The bulb consumes sixty watts."),
    ("frequency", "周波数", "名詞", "The mains frequency is fifty hertz."),
    ("short circuit", "短絡・ショート", "名詞", "A short circuit caused the fire."),
    ("load", "負荷", "名詞", "The generator runs under heavy load."),
    ("phase", "位相・相", "名詞", "The three-phase supply feeds the motor."),
    ("rectifier", "整流器", "名詞", "A rectifier converts AC to DC."),
    ("switchgear", "開閉装置", "名詞", "The substation houses the switchgear."),
    ("terminal", "端子", "名詞", "Connect the wire to the positive terminal."),
    ("wiring", "配線", "名詞", "Faulty wiring is a common hazard."),
    ("amplifier", "増幅器", "名詞", "The amplifier boosts the weak signal."),
    ("electrode", "電極", "名詞", "The electrode is coated with platinum."),
    ("power outage", "停電", "名詞", "The storm caused a power outage."),
])
P("電気・電子", [
    ("Turn off the breaker before you touch the wiring.", "配線に触れる前にブレーカーを切って。"),
    ("Make sure the device is properly grounded.", "機器がきちんと接地されているか確認して。"),
    ("The voltage reading looks too high.", "電圧の値が高すぎるようだ。"),
    ("We had a power outage last night.", "昨夜停電があった。"),
    ("This cable can't handle that much current.", "このケーブルはその電流には耐えられない。"),
    ("Check whether the fuse has blown.", "ヒューズが切れていないか確認して。"),
    ("The transformer is overheating.", "変圧器が過熱している。"),
    ("Don't touch it — it's still live.", "触らないで、まだ通電している。"),
    ("Measure the resistance with a multimeter.", "テスターで抵抗を測って。"),
    ("The circuit keeps tripping.", "回路が何度も遮断される。"),
    ("Replace the capacitor; it's swollen.", "コンデンサが膨らんでいるから交換して。"),
    ("Route the wires away from the heat source.", "配線は熱源から離して通して。"),
])

# ─────────────────────────────────────────────────────────────
# 電子工学（→ 電気電子）
# ─────────────────────────────────────────────────────────────
W("電気電子", "800", [
    ("semiconductor", "半導体", "名詞", "Silicon is the most common semiconductor."),
    ("transistor", "トランジスタ", "名詞", "A transistor can switch or amplify signals."),
    ("diode", "ダイオード", "名詞", "A diode lets current flow in one direction."),
    ("integrated circuit", "集積回路", "名詞", "The chip is a complex integrated circuit."),
    ("printed circuit board", "プリント基板", "名詞", "Components are soldered onto the printed circuit board."),
    ("microcontroller", "マイコン", "名詞", "The robot is driven by a microcontroller."),
    ("oscilloscope", "オシロスコープ", "名詞", "We viewed the waveform on an oscilloscope."),
    ("soldering", "はんだ付け", "名詞", "Soldering joins the component to the board."),
    ("signal", "信号", "名詞", "The sensor outputs an analog signal."),
    ("analog", "アナログ", "形容詞", "This is an analog audio signal."),
    ("digital", "デジタル", "形容詞", "The data is stored in digital form."),
    ("gate", "ゲート・論理素子", "名詞", "An AND gate outputs one only when both inputs are one."),
    ("op-amp", "オペアンプ", "名詞", "The op-amp amplifies the difference between inputs."),
    ("firmware", "ファームウェア", "名詞", "We flashed new firmware onto the chip."),
    ("bandwidth", "帯域幅", "名詞", "The amplifier has a wide bandwidth."),
    ("noise", "ノイズ・雑音", "名詞", "Shielding reduces electrical noise."),
    ("waveform", "波形", "名詞", "The waveform is a clean sine wave."),
    ("sensor", "センサー", "名詞", "The temperature sensor reads 25 degrees."),
    ("actuator", "アクチュエータ", "名詞", "The actuator moves the valve."),
    ("logic circuit", "論理回路", "名詞", "The logic circuit implements the truth table."),
    ("clock", "クロック", "名詞", "The processor runs at a 3-gigahertz clock."),
    ("register", "レジスタ", "名詞", "The value is stored in a register."),
    ("bit", "ビット", "名詞", "Each bit is either zero or one."),
    ("power supply", "電源", "名詞", "A regulated power supply feeds the board."),
    ("solder joint", "はんだ接合部", "名詞", "A cracked solder joint caused the fault."),
])
P("電気・電子", [
    ("The chip is drawing too much power.", "そのチップは電力を食いすぎている。"),
    ("Flash the latest firmware to the board.", "基板に最新のファームを書き込んで。"),
    ("Probe the signal at pin three.", "3番ピンで信号を当たって。"),
    ("There's too much noise on this line.", "この線はノイズが多すぎる。"),
    ("The solder joint looks cold.", "はんだがうまく乗っていないようだ。"),
    ("Double-check the polarity of the diode.", "ダイオードの向きをもう一度確認して。"),
    ("The microcontroller keeps resetting.", "マイコンが何度もリセットする。"),
    ("Scope the output and check the waveform.", "出力をオシロで見て波形を確認して。"),
    ("This pin is floating; add a pull-up resistor.", "このピンは浮いているからプルアップ抵抗を足して。"),
    ("The board won't boot after the update.", "更新後に基板が起動しない。"),
    ("Ground the shield to reduce interference.", "干渉を減らすためシールドを接地して。"),
    ("Read the datasheet before wiring it up.", "配線する前にデータシートを読んで。"),
])

# ─────────────────────────────────────────────────────────────
# 無線（→ 電気電子）
# ─────────────────────────────────────────────────────────────
W("電気電子", "900", [
    ("antenna", "アンテナ", "名詞", "A longer antenna improves reception."),
    ("wavelength", "波長", "名詞", "The wavelength depends on the frequency."),
    ("modulation", "変調", "名詞", "FM stands for frequency modulation."),
    ("transmitter", "送信機", "名詞", "The transmitter broadcasts on 145 megahertz."),
    ("receiver", "受信機", "名詞", "The receiver picks up a weak signal."),
    ("bandwidth allocation", "周波数割当", "名詞", "Regulators handle bandwidth allocation."),
    ("call sign", "コールサイン", "名詞", "Every ham operator has a call sign."),
    ("interference", "混信・干渉", "名詞", "Interference garbled the transmission."),
    ("gain", "利得・ゲイン", "名詞", "A directional antenna has high gain."),
    ("propagation", "電波伝搬", "名詞", "Radio propagation varies with the ionosphere."),
    ("repeater", "中継局・レピータ", "名詞", "The repeater extends the radio's range."),
    ("squelch", "スケルチ", "名詞", "Adjust the squelch to cut background hiss."),
    ("bandpass filter", "帯域通過フィルタ", "名詞", "A bandpass filter isolates the channel."),
    ("carrier wave", "搬送波", "名詞", "The signal rides on a carrier wave."),
    ("dipole", "ダイポール", "名詞", "A dipole is a simple half-wave antenna."),
    ("spectrum", "周波数スペクトル", "名詞", "The radio spectrum is a scarce resource."),
    ("amateur radio", "アマチュア無線", "名詞", "He got his amateur radio license."),
    ("signal strength", "電波強度", "名詞", "Signal strength drops behind the hill."),
    ("frequency band", "周波数帯", "名詞", "This device uses the 2.4-gigahertz band."),
    ("static", "空電・雑音", "名詞", "Static drowned out the voice."),
    ("relay station", "リレー局", "名詞", "Messages pass through a relay station."),
    ("duplex", "複信・二重通信", "名詞", "The link operates in full duplex."),
    ("encoding", "符号化", "名詞", "Digital encoding reduces errors."),
    ("handheld transceiver", "ハンディ機", "名詞", "She carries a handheld transceiver on hikes."),
    ("line of sight", "見通し", "名詞", "VHF radio needs a line of sight."),
])
P("無線", [
    ("Do you copy? Over.", "聞こえますか、どうぞ。"),
    ("You're breaking up.", "電波が途切れている。"),
    ("Switch to channel nine.", "9チャンネルに切り替えて。"),
    ("What's your call sign?", "コールサインは？"),
    ("There's a lot of interference here.", "ここは混信がひどい。"),
    ("Increase the squelch to cut the static.", "雑音を消すためスケルチを上げて。"),
    ("The repeater is down for maintenance.", "中継局は保守で停止中だ。"),
    ("I read you loud and clear.", "はっきり受信できている。"),
    ("We lost the signal behind the mountain.", "山の陰で信号が切れた。"),
    ("Adjust the antenna for better reception.", "受信を良くするためアンテナを調整して。"),
    ("Say again, I missed that.", "もう一度言って、聞き逃した。"),
    ("Standing by on this frequency.", "この周波数で待機している。"),
])

# ─────────────────────────────────────────────────────────────
# 法律（→ 法律）
# ─────────────────────────────────────────────────────────────
W("法律", "800", [
    ("plaintiff", "原告", "名詞", "The plaintiff filed a lawsuit for damages."),
    ("defendant", "被告", "名詞", "The defendant pleaded not guilty."),
    ("verdict", "評決", "名詞", "The jury reached a unanimous verdict."),
    ("testimony", "証言", "名詞", "Her testimony contradicted the report."),
    ("jurisdiction", "管轄権", "名詞", "The court has no jurisdiction over the case."),
    ("liability", "法的責任・賠償責任", "名詞", "The company denied any liability."),
    ("plea", "答弁・申し立て", "名詞", "He entered a guilty plea."),
    ("subpoena", "召喚状", "名詞", "The witness was served a subpoena."),
    ("injunction", "差止命令", "名詞", "The judge granted a temporary injunction."),
    ("statute", "制定法", "名詞", "The act became a federal statute."),
    ("precedent", "判例", "名詞", "The ruling set a legal precedent."),
    ("indictment", "起訴", "名詞", "A grand jury handed down an indictment."),
    ("acquittal", "無罪判決", "名詞", "The trial ended in an acquittal."),
    ("appeal", "上訴", "名詞", "They filed an appeal against the ruling."),
    ("settlement", "和解", "名詞", "The parties reached an out-of-court settlement."),
    ("breach of contract", "契約違反", "名詞", "The supplier is in breach of contract."),
    ("negligence", "過失", "名詞", "The accident was caused by negligence."),
    ("damages", "損害賠償", "名詞", "The court awarded punitive damages."),
    ("bail", "保釈金", "名詞", "The suspect was released on bail."),
    ("attorney", "弁護士", "名詞", "Her attorney advised her to stay silent."),
    ("prosecutor", "検察官", "名詞", "The prosecutor presented the evidence."),
    ("warrant", "令状", "名詞", "Police obtained a search warrant."),
    ("clause", "条項", "名詞", "Read the confidentiality clause carefully."),
    ("intellectual property", "知的財産", "名詞", "The patent protects their intellectual property."),
    ("due process", "適正手続き", "名詞", "Everyone is entitled to due process."),
])
P("法律", [
    ("I'd like to consult a lawyer first.", "まず弁護士に相談したい。"),
    ("You have the right to remain silent.", "あなたには黙秘権がある。"),
    ("Please read the contract carefully before signing.", "署名前に契約書をよく読んでください。"),
    ("We intend to file a lawsuit.", "訴訟を起こすつもりだ。"),
    ("That clause is not legally binding.", "その条項は法的拘束力がない。"),
    ("The case was settled out of court.", "その件は示談で解決した。"),
    ("He was found guilty on all charges.", "彼は全ての罪状で有罪となった。"),
    ("Do I need a witness for this?", "これには証人が必要ですか？"),
    ("They are suing us for breach of contract.", "契約違反で訴えられている。"),
    ("The judge dismissed the case.", "裁判官はその訴えを却下した。"),
    ("This agreement is subject to Japanese law.", "本契約は日本法に準拠する。"),
    ("You could be held liable for the damage.", "その損害の責任を問われる可能性がある。"),
])

# ─────────────────────────────────────────────────────────────
# 政治（→ ニュース）
# ─────────────────────────────────────────────────────────────
W("ニュース", "800", [
    ("legislation", "法案・立法", "名詞", "The legislation passed by a narrow margin."),
    ("parliament", "議会", "名詞", "Parliament debated the budget for hours."),
    ("constituency", "選挙区", "名詞", "She won her constituency by a landslide."),
    ("referendum", "国民投票", "名詞", "The referendum decided the nation's future."),
    ("coalition", "連立", "名詞", "The parties formed a governing coalition."),
    ("cabinet", "内閣", "名詞", "The prime minister reshuffled the cabinet."),
    ("ballot", "投票・投票用紙", "名詞", "Voters cast their ballots by noon."),
    ("incumbent", "現職", "名詞", "The incumbent lost to a newcomer."),
    ("diplomacy", "外交", "名詞", "The crisis was resolved through diplomacy."),
    ("sanction", "制裁", "名詞", "The council imposed economic sanctions."),
    ("sovereignty", "主権", "名詞", "The treaty respects national sovereignty."),
    ("veto", "拒否権", "名詞", "The president vetoed the bill."),
    ("amendment", "修正条項", "名詞", "The constitutional amendment was ratified."),
    ("opposition", "野党", "名詞", "The opposition demanded an inquiry."),
    ("turnout", "投票率", "名詞", "Voter turnout was unusually high."),
    ("policy", "政策", "名詞", "The new policy targets inflation."),
    ("caucus", "党員集会", "名詞", "The party held its nominating caucus."),
    ("lobbying", "ロビー活動", "名詞", "Lobbying influenced the final vote."),
    ("democracy", "民主主義", "名詞", "A free press is vital to democracy."),
    ("bureaucracy", "官僚制", "名詞", "Reform aims to shrink the bureaucracy."),
    ("election campaign", "選挙運動", "名詞", "The election campaign lasted six weeks."),
    ("summit", "首脳会談", "名詞", "Leaders met at the climate summit."),
    ("treaty", "条約", "名詞", "Both nations signed the trade treaty."),
    ("approval rating", "支持率", "名詞", "His approval rating fell below forty percent."),
    ("regime", "政権・体制", "名詞", "The regime suppressed the protests."),
])
P("政治・ニュース", [
    ("The bill was passed by a narrow margin.", "その法案は僅差で可決された。"),
    ("Voter turnout was higher than expected.", "投票率は予想より高かった。"),
    ("The prime minister announced a cabinet reshuffle.", "首相は内閣改造を発表した。"),
    ("The two countries agreed to a ceasefire.", "両国は停戦に合意した。"),
    ("The opposition strongly criticized the policy.", "野党はその政策を強く批判した。"),
    ("Sanctions will take effect next month.", "制裁は来月発効する。"),
    ("He is running for re-election.", "彼は再選を目指して立候補している。"),
    ("The summit ended without an agreement.", "首脳会談は合意なしに終わった。"),
    ("Polls suggest a close race.", "世論調査は接戦を示している。"),
    ("The government pledged to cut taxes.", "政府は減税を約束した。"),
    ("Protesters demanded the leader's resignation.", "デモ隊は指導者の辞任を要求した。"),
    ("The treaty must be ratified by parliament.", "条約は議会の批准が必要だ。"),
])

# ─────────────────────────────────────────────────────────────
# 経済学（→ 経済学）
# ─────────────────────────────────────────────────────────────
W("経済学", "800", [
    ("inflation", "インフレ", "名詞", "Rising energy prices fueled inflation."),
    ("deflation", "デフレ", "名詞", "Prolonged deflation hurts the economy."),
    ("recession", "景気後退", "名詞", "The country slipped into a recession."),
    ("gross domestic product", "国内総生産", "名詞", "Gross domestic product grew by two percent."),
    ("supply and demand", "需給", "名詞", "Prices are set by supply and demand."),
    ("interest rate", "金利", "名詞", "The central bank raised the interest rate."),
    ("monetary policy", "金融政策", "名詞", "Monetary policy aims to curb inflation."),
    ("fiscal policy", "財政政策", "名詞", "Fiscal policy uses taxes and spending."),
    ("unemployment rate", "失業率", "名詞", "The unemployment rate fell to three percent."),
    ("exchange rate", "為替レート", "名詞", "A weak exchange rate boosts exports."),
    ("trade deficit", "貿易赤字", "名詞", "The trade deficit widened this quarter."),
    ("subsidy", "補助金", "名詞", "The government offered a farming subsidy."),
    ("tariff", "関税", "名詞", "New tariffs raised the price of imports."),
    ("stimulus", "景気刺激策", "名詞", "The stimulus package supported small firms."),
    ("productivity", "生産性", "名詞", "Automation improved factory productivity."),
    ("commodity", "商品・一次産品", "名詞", "Oil is a globally traded commodity."),
    ("equilibrium", "均衡", "名詞", "The market reached a price equilibrium."),
    ("purchasing power", "購買力", "名詞", "Inflation erodes purchasing power."),
    ("capital", "資本", "名詞", "The startup needs more capital to grow."),
    ("liquidity", "流動性", "名詞", "The bank maintains high liquidity."),
    ("depreciation", "減価・下落", "名詞", "Currency depreciation raised import costs."),
    ("macroeconomics", "マクロ経済学", "名詞", "Macroeconomics studies the whole economy."),
    ("household spending", "家計支出", "名詞", "Household spending drives demand."),
    ("bond", "債券", "名詞", "Investors bought government bonds."),
    ("stagnation", "停滞", "名詞", "The economy faces long-term stagnation."),
])
P("経済・ビジネス", [
    ("The central bank hiked interest rates again.", "中央銀行は再び利上げした。"),
    ("Inflation is eating into household budgets.", "インフレが家計を圧迫している。"),
    ("The economy is heading into a recession.", "景気は後退局面に入りつつある。"),
    ("A weaker yen helps exporters.", "円安は輸出企業に有利だ。"),
    ("Consumer spending has slowed down.", "個人消費が鈍化している。"),
    ("They announced a stimulus package.", "景気刺激策が発表された。"),
    ("Unemployment hit a record low.", "失業率が過去最低を記録した。"),
    ("Prices are rising faster than wages.", "物価が賃金より速く上がっている。"),
    ("The market corrected sharply today.", "市場は今日急落した。"),
    ("Higher tariffs will raise consumer prices.", "関税引き上げは物価を押し上げる。"),
    ("The GDP figures beat expectations.", "GDPの数字は予想を上回った。"),
    ("Investors are worried about liquidity.", "投資家は流動性を懸念している。"),
])

# ─────────────────────────────────────────────────────────────
# 経営（→ ビジネス）
# ─────────────────────────────────────────────────────────────
W("ビジネス", "700", [
    ("stakeholder", "利害関係者", "名詞", "We must align every stakeholder's interests."),
    ("revenue stream", "収益源", "名詞", "Subscriptions became our main revenue stream."),
    ("profit margin", "利益率", "名詞", "The new line has a thin profit margin."),
    ("cash flow", "資金繰り・キャッシュフロー", "名詞", "Poor cash flow threatens small businesses."),
    ("scalability", "拡張性", "名詞", "Investors love the model's scalability."),
    ("procurement", "調達", "名詞", "Procurement negotiated a better price."),
    ("overhead", "間接費", "名詞", "Remote work cut our office overhead."),
    ("benchmark", "基準・指標", "名詞", "We benchmark against industry leaders."),
    ("turnover", "離職率・売上高", "名詞", "High staff turnover raises training costs."),
    ("merger", "合併", "名詞", "The merger created a market leader."),
    ("acquisition", "買収", "名詞", "The acquisition expanded their portfolio."),
    ("outsourcing", "外部委託", "名詞", "Outsourcing support lowered costs."),
    ("KPI", "重要業績評価指標", "名詞", "Each team tracks its own KPI."),
    ("supply chain", "サプライチェーン", "名詞", "The pandemic disrupted the supply chain."),
    ("incentive", "報奨・動機付け", "名詞", "Bonuses act as a performance incentive."),
    ("delegation", "権限委譲", "名詞", "Good delegation frees the manager's time."),
    ("forecast", "予測", "名詞", "The sales forecast looks optimistic."),
    ("onboarding", "受け入れ・研修", "名詞", "A smooth onboarding retains new hires."),
    ("restructuring", "組織再編", "名詞", "Restructuring reduced three layers of management."),
    ("compliance", "法令順守", "名詞", "Compliance training is mandatory."),
    ("due diligence", "デューデリジェンス", "名詞", "They did due diligence before the deal."),
    ("bottleneck", "ボトルネック", "名詞", "Approval is the main bottleneck."),
    ("milestone", "節目・マイルストーン", "名詞", "We hit an important project milestone."),
    ("liquidity crunch", "資金逼迫", "名詞", "A liquidity crunch forced layoffs."),
    ("market share", "市場シェア", "名詞", "They gained market share last year."),
])
P("経済・ビジネス", [
    ("Let's align on the quarterly targets.", "四半期目標について認識を合わせよう。"),
    ("We need to improve our cash flow.", "資金繰りを改善する必要がある。"),
    ("Who is the stakeholder for this project?", "この案件の責任者は誰ですか？"),
    ("Let's circle back on this next week.", "この件は来週改めて話そう。"),
    ("Can you send me the sales forecast?", "売上予測を送ってもらえますか？"),
    ("We're behind on this milestone.", "この節目に対して遅れている。"),
    ("Let's take this offline.", "この件は別途話しましょう。"),
    ("The bottleneck is in the approval process.", "ボトルネックは承認プロセスにある。"),
    ("We should benchmark against competitors.", "競合と比較評価すべきだ。"),
    ("Let's delegate this to the team lead.", "これはチームリーダーに任せよう。"),
    ("The merger is still under due diligence.", "合併はまだ精査中だ。"),
    ("Our margins are getting squeezed.", "利益率が圧迫されている。"),
])

# ─────────────────────────────────────────────────────────────
# DIY・工具（→ 機械工学）
# ─────────────────────────────────────────────────────────────
W("機械工学", "600", [
    ("screwdriver", "ドライバー", "名詞", "Use a Phillips screwdriver for this screw."),
    ("wrench", "レンチ・スパナ", "名詞", "Tighten the bolt with a wrench."),
    ("pliers", "ペンチ", "名詞", "Grip the wire with the pliers."),
    ("hammer", "ハンマー・金づち", "名詞", "Drive the nail in with a hammer."),
    ("drill", "ドリル・電動ドリル", "名詞", "Drill a pilot hole first."),
    ("sandpaper", "紙やすり", "名詞", "Smooth the edge with sandpaper."),
    ("level", "水準器", "名詞", "Check the shelf with a level."),
    ("tape measure", "巻尺・メジャー", "名詞", "Measure twice with the tape measure."),
    ("nail", "釘", "名詞", "Hammer the nail flush with the surface."),
    ("bolt", "ボルト", "名詞", "The bolt threads into the nut."),
    ("nut", "ナット", "名詞", "Tighten the nut clockwise."),
    ("washer", "ワッシャー・座金", "名詞", "Add a washer under the bolt head."),
    ("chisel", "のみ", "名詞", "Carve the groove with a chisel."),
    ("clamp", "クランプ・締め具", "名詞", "Hold the boards with a clamp while gluing."),
    ("saw", "のこぎり", "名詞", "Cut the plank with a hand saw."),
    ("utility knife", "カッターナイフ", "名詞", "Score the cardboard with a utility knife."),
    ("adhesive", "接着剤", "名詞", "Apply adhesive to both surfaces."),
    ("stud finder", "下地探知器", "名詞", "Use a stud finder before drilling the wall."),
    ("power tool", "電動工具", "名詞", "Always wear goggles with a power tool."),
    ("workbench", "作業台", "名詞", "Clamp the piece to the workbench."),
    ("hinge", "蝶番", "名詞", "Screw the hinge onto the door frame."),
    ("bracket", "金具・ブラケット", "名詞", "Mount the shelf on an L-shaped bracket."),
    ("grout", "目地材", "名詞", "Fill the tile gaps with grout."),
    ("caulk", "コーキング材", "名詞", "Seal the gap around the sink with caulk."),
    ("varnish", "ニス", "名詞", "Apply two coats of varnish to the wood."),
])
P("DIY・工具", [
    ("Do you have a Phillips screwdriver?", "プラスドライバーある？"),
    ("Measure twice, cut once.", "二度測って一度で切る。"),
    ("Drill a pilot hole before the screw.", "ねじの前に下穴を開けて。"),
    ("Hold it steady while I tighten the bolt.", "ボルトを締めるから押さえていて。"),
    ("Sand it down until it's smooth.", "滑らかになるまでやすりをかけて。"),
    ("Wear goggles when you use the saw.", "のこぎりを使うときはゴーグルを着けて。"),
    ("This bolt is stripped.", "このボルトはなめてしまっている。"),
    ("Make sure the shelf is level.", "棚が水平か確認して。"),
    ("Let the glue set overnight.", "接着剤は一晩置いて固めて。"),
    ("Find a stud before you hang it.", "掛ける前に壁の下地を探して。"),
    ("Seal the gap with caulk.", "隙間をコーキングで埋めて。"),
    ("Turn off the power before you wire it.", "配線する前に電源を切って。"),
])

# ─────────────────────────────────────────────────────────────
# ロボット工学（→ 機械工学）
# ─────────────────────────────────────────────────────────────
W("機械工学", "900", [
    ("actuator", "アクチュエータ", "名詞", "Each joint is driven by an actuator."),
    ("servo motor", "サーボモーター", "名詞", "The arm uses a precise servo motor."),
    ("kinematics", "運動学", "名詞", "Inverse kinematics computes joint angles."),
    ("degrees of freedom", "自由度", "名詞", "The arm has six degrees of freedom."),
    ("end effector", "エンドエフェクタ", "名詞", "The end effector is a gripper."),
    ("gripper", "グリッパー・把持部", "名詞", "The gripper picks up small parts."),
    ("feedback loop", "フィードバックループ", "名詞", "A feedback loop stabilizes the motion."),
    ("gyroscope", "ジャイロスコープ", "名詞", "The gyroscope keeps the robot balanced."),
    ("lidar", "ライダー", "名詞", "Lidar maps the surrounding obstacles."),
    ("odometry", "オドメトリ", "名詞", "Odometry estimates the robot's position."),
    ("torque", "トルク", "名詞", "The motor delivers high torque at low speed."),
    ("trajectory", "軌道", "名詞", "The planner computes a smooth trajectory."),
    ("payload", "可搬重量・積載", "名詞", "The robot's payload is five kilograms."),
    ("autonomous", "自律的な", "形容詞", "An autonomous robot navigates on its own."),
    ("manipulator", "マニピュレータ・ロボットアーム", "名詞", "The manipulator welds the car body."),
    ("calibration", "較正・キャリブレーション", "名詞", "Sensor calibration reduces drift."),
    ("path planning", "経路計画", "名詞", "Path planning avoids collisions."),
    ("encoder", "エンコーダ", "名詞", "The encoder measures the shaft angle."),
    ("swarm", "群れ・スウォーム", "名詞", "The drones fly in a coordinated swarm."),
    ("teleoperation", "遠隔操作", "名詞", "Teleoperation controls the robot remotely."),
    ("degrees per second", "毎秒角度", "名詞", "The joint rotates at ninety degrees per second."),
    ("obstacle avoidance", "障害物回避", "名詞", "Obstacle avoidance keeps it from crashing."),
    ("humanoid", "人型ロボット", "名詞", "The humanoid walks on two legs."),
    ("actuation", "駆動", "名詞", "Hydraulic actuation gives strong force."),
    ("controller", "制御器・コントローラ", "名詞", "The PID controller tunes the response."),
])
P("ロボット", [
    ("Calibrate the sensors before you start.", "始める前にセンサーを較正して。"),
    ("The arm needs more torque for this load.", "この荷にはもっとトルクが要る。"),
    ("The robot lost track of its position.", "ロボットが自己位置を見失った。"),
    ("Set the gripper to close slowly.", "グリッパーをゆっくり閉じるように設定して。"),
    ("Run the path planner again.", "経路計画をもう一度実行して。"),
    ("The feedback loop is unstable.", "フィードバック制御が不安定だ。"),
    ("Switch to teleoperation mode.", "遠隔操作モードに切り替えて。"),
    ("It keeps bumping into obstacles.", "障害物に何度もぶつかる。"),
    ("Reduce the joint speed for safety.", "安全のため関節の速度を落として。"),
    ("The encoder reading is drifting.", "エンコーダの値がずれてきている。"),
    ("Emergency stop — hit the red button.", "緊急停止、赤いボタンを押して。"),
    ("The battery is too low to continue.", "バッテリーが低すぎて続行できない。"),
])

# ─────────────────────────────────────────────────────────────
# インターネット（→ IT）
# ─────────────────────────────────────────────────────────────
W("IT", "600", [
    ("bandwidth", "帯域・通信速度", "名詞", "Streaming video eats a lot of bandwidth."),
    ("router", "ルーター", "名詞", "Restart the router if the Wi-Fi drops."),
    ("firewall", "ファイアウォール", "名詞", "The firewall blocks suspicious traffic."),
    ("latency", "遅延・レイテンシ", "名詞", "High latency makes online games laggy."),
    ("IP address", "IPアドレス", "名詞", "Every device has a unique IP address."),
    ("domain name", "ドメイン名", "名詞", "We registered a new domain name."),
    ("encryption", "暗号化", "名詞", "Encryption protects your data in transit."),
    ("cache", "キャッシュ", "名詞", "Clear the cache if the page won't load."),
    ("cookie", "クッキー", "名詞", "The site stores a cookie in your browser."),
    ("packet", "パケット", "名詞", "Data is split into small packets."),
    ("protocol", "プロトコル", "名詞", "HTTPS is a secure web protocol."),
    ("upload", "アップロード", "動詞", "It took an hour to upload the video."),
    ("download", "ダウンロード", "動詞", "Download the file before you go offline."),
    ("server", "サーバー", "名詞", "The server is down for maintenance."),
    ("browser", "ブラウザ", "名詞", "Open the link in a different browser."),
    ("phishing", "フィッシング詐欺", "名詞", "The email was a phishing attempt."),
    ("malware", "マルウェア", "名詞", "Antivirus software removes malware."),
    ("streaming", "ストリーミング", "名詞", "Streaming replaced physical media."),
    ("cloud storage", "クラウドストレージ", "名詞", "Back up your photos to cloud storage."),
    ("broadband", "ブロードバンド", "名詞", "Fiber broadband is very fast."),
    ("hotspot", "アクセスポイント・ホットスポット", "名詞", "I turned my phone into a hotspot."),
    ("two-factor authentication", "二段階認証", "名詞", "Enable two-factor authentication for safety."),
    ("VPN", "仮想専用線・VPN", "名詞", "A VPN hides your IP address."),
    ("bandwidth throttling", "帯域制限", "名詞", "The provider uses bandwidth throttling."),
    ("data breach", "情報漏えい", "名詞", "The data breach exposed millions of accounts."),
])
P("インターネット", [
    ("The Wi-Fi keeps dropping.", "Wi-Fiが何度も切れる。"),
    ("Try restarting the router.", "ルーターを再起動してみて。"),
    ("The page won't load.", "ページが読み込めない。"),
    ("Clear your browser cache.", "ブラウザのキャッシュを消して。"),
    ("The connection is really slow today.", "今日は接続がとても遅い。"),
    ("Did you get the verification code?", "認証コードは届いた？"),
    ("That link looks like phishing — don't click it.", "そのリンクはフィッシングっぽいから押さないで。"),
    ("Log in with two-factor authentication.", "二段階認証でログインして。"),
    ("The server seems to be down.", "サーバーが落ちているようだ。"),
    ("Upload it to the shared drive.", "共有ドライブにアップして。"),
    ("Turn on the VPN before you connect.", "接続する前にVPNをオンにして。"),
    ("Change your password after the breach.", "情報漏えいの後はパスワードを変えて。"),
])

# ─────────────────────────────────────────────────────────────
# 家電（→ 家電）
# ─────────────────────────────────────────────────────────────
W("家電", "500", [
    ("refrigerator", "冷蔵庫", "名詞", "Put the milk back in the refrigerator."),
    ("microwave oven", "電子レンジ", "名詞", "Heat it in the microwave oven for a minute."),
    ("washing machine", "洗濯機", "名詞", "The washing machine is on a spin cycle."),
    ("dishwasher", "食洗機", "名詞", "Load the plates into the dishwasher."),
    ("vacuum cleaner", "掃除機", "名詞", "Run the vacuum cleaner over the carpet."),
    ("air conditioner", "エアコン", "名詞", "Set the air conditioner to 26 degrees."),
    ("rice cooker", "炊飯器", "名詞", "The rice cooker beeps when it's done."),
    ("kettle", "電気ケトル", "名詞", "Boil some water in the kettle."),
    ("toaster", "トースター", "名詞", "Pop the bread into the toaster."),
    ("hair dryer", "ドライヤー", "名詞", "The hair dryer has a cool setting."),
    ("humidifier", "加湿器", "名詞", "Run the humidifier in winter."),
    ("dehumidifier", "除湿機", "名詞", "A dehumidifier prevents mold."),
    ("air purifier", "空気清浄機", "名詞", "The air purifier removes pollen."),
    ("thermostat", "サーモスタット・温度調節器", "名詞", "Lower the thermostat at night."),
    ("remote control", "リモコン", "名詞", "I can't find the remote control."),
    ("appliance", "家電製品", "名詞", "This appliance is energy-efficient."),
    ("power cord", "電源コード", "名詞", "The power cord is frayed."),
    ("outlet", "コンセント", "名詞", "Plug it into the wall outlet."),
    ("battery charger", "充電器", "名詞", "Leave it on the battery charger overnight."),
    ("induction cooktop", "IH調理器", "名詞", "The induction cooktop heats up fast."),
    ("energy efficiency", "省エネ性能", "名詞", "Check the energy efficiency label."),
    ("standby power", "待機電力", "名詞", "Unplug it to save standby power."),
    ("timer", "タイマー", "名詞", "Set the timer for thirty minutes."),
    ("warranty", "保証", "名詞", "The appliance has a two-year warranty."),
    ("filter", "フィルター", "名詞", "Clean the filter once a month."),
])
P("家電", [
    ("The fridge isn't cooling properly.", "冷蔵庫がちゃんと冷えない。"),
    ("Can you set the air conditioner to 26?", "エアコンを26度にしてくれる？"),
    ("The washing machine won't drain.", "洗濯機が排水しない。"),
    ("Did you unplug the iron?", "アイロンのコンセント抜いた？"),
    ("The remote needs new batteries.", "リモコンの電池が切れてる。"),
    ("Clean the air purifier filter.", "空気清浄機のフィルターを掃除して。"),
    ("It's making a strange noise.", "変な音がしている。"),
    ("Is this covered by the warranty?", "これは保証の対象ですか？"),
    ("Turn off the appliance before cleaning it.", "掃除の前に電源を切って。"),
    ("The microwave stopped working.", "電子レンジが動かなくなった。"),
    ("Set the rice cooker for six o'clock.", "炊飯器を6時にセットして。"),
    ("Unplug it to save standby power.", "待機電力を減らすためコンセントを抜いて。"),
])

# ─────────────────────────────────────────────────────────────
# 航空工学（→ 航空・宇宙）
# ─────────────────────────────────────────────────────────────
W("航空・宇宙", "900", [
    ("lift", "揚力", "名詞", "Wings generate lift as speed increases."),
    ("drag", "抗力", "名詞", "A streamlined shape reduces drag."),
    ("thrust", "推力", "名詞", "The engines produce enormous thrust."),
    ("angle of attack", "迎え角", "名詞", "A high angle of attack can cause a stall."),
    ("aerodynamics", "空気力学", "名詞", "Aerodynamics shapes the wing's profile."),
    ("fuselage", "胴体", "名詞", "The fuselage houses the passengers."),
    ("stall", "失速", "名詞", "The aircraft stalled at low speed."),
    ("altitude", "高度", "名詞", "We're cruising at 35,000 feet altitude."),
    ("airfoil", "翼型", "名詞", "The airfoil is curved on top."),
    ("turbine", "タービン", "名詞", "The jet turbine spins at high speed."),
    ("propulsion", "推進", "名詞", "Jet propulsion moves the aircraft forward."),
    ("payload", "搭載重量", "名詞", "The rocket's payload is a satellite."),
    ("aileron", "補助翼・エルロン", "名詞", "Ailerons control the roll of the plane."),
    ("rudder", "方向舵", "名詞", "The rudder controls the yaw."),
    ("landing gear", "着陸装置", "名詞", "Lower the landing gear before approach."),
    ("cabin pressure", "客室与圧", "名詞", "Cabin pressure is maintained at altitude."),
    ("airframe", "機体構造", "名詞", "The airframe is made of composites."),
    ("supersonic", "超音速の", "形容詞", "The jet can fly at supersonic speed."),
    ("thermal protection", "耐熱防護", "名詞", "Thermal protection shields reentry vehicles."),
    ("avionics", "航空電子機器", "名詞", "Modern avionics automate navigation."),
    ("winglet", "ウイングレット", "名詞", "Winglets improve fuel efficiency."),
    ("bank angle", "バンク角", "名詞", "The pilot increased the bank angle."),
    ("cruising speed", "巡航速度", "名詞", "The cruising speed is 900 kilometers per hour."),
    ("jet engine", "ジェットエンジン", "名詞", "The jet engine burns kerosene."),
    ("flight envelope", "飛行包絡線", "名詞", "Stay within the flight envelope."),
])
P("航空・機内", [
    ("We are now cruising at thirty-five thousand feet.", "現在高度3万5千フィートで巡航中です。"),
    ("Please fasten your seatbelt.", "シートベルトをお締めください。"),
    ("We are experiencing some turbulence.", "只今、揺れが生じています。"),
    ("The landing gear is down and locked.", "着陸装置は下がり固定されました。"),
    ("Prepare the cabin for landing.", "着陸に備えて客室を整えてください。"),
    ("We're beginning our descent.", "降下を開始します。"),
    ("Return your seat to the upright position.", "座席を元の位置にお戻しください。"),
    ("There's a slight delay due to weather.", "天候のため少し遅れています。"),
    ("The captain has turned on the seatbelt sign.", "機長がベルト着用サインを点灯しました。"),
    ("We expect a smooth flight today.", "本日は順調な飛行を見込んでいます。"),
    ("Cabin crew, please be seated.", "客室乗務員は着席してください。"),
    ("Thank you for flying with us.", "ご搭乗ありがとうございました。"),
])

# ─────────────────────────────────────────────────────────────
# 航空（管制・乗務）（→ 航空・宇宙）
# ─────────────────────────────────────────────────────────────
W("航空・宇宙", "800", [
    ("air traffic control", "航空管制", "名詞", "Air traffic control cleared us for takeoff."),
    ("clearance", "許可・クリアランス", "名詞", "Request clearance for landing."),
    ("runway", "滑走路", "名詞", "The plane taxied onto the runway."),
    ("taxiway", "誘導路", "名詞", "Follow the taxiway to gate five."),
    ("holding pattern", "待機旋回", "名詞", "We entered a holding pattern above the airport."),
    ("callsign", "コールサイン", "名詞", "State your callsign and altitude."),
    ("heading", "機首方位", "名詞", "Turn to heading two seven zero."),
    ("approach", "進入", "名詞", "The aircraft is on final approach."),
    ("go-around", "着陸復行・ゴーアラウンド", "名詞", "The pilot executed a go-around."),
    ("flight level", "フライトレベル", "名詞", "Climb to flight level three three zero."),
    ("transponder", "トランスポンダ", "名詞", "Set the transponder code to seven thousand."),
    ("boarding pass", "搭乗券", "名詞", "Have your boarding pass ready."),
    ("cockpit", "操縦室", "名詞", "The crew ran the checklist in the cockpit."),
    ("purser", "客室責任者・パーサー", "名詞", "The purser briefed the cabin crew."),
    ("cabin crew", "客室乗務員", "名詞", "The cabin crew served the meals."),
    ("jet bridge", "搭乗橋", "名詞", "Passengers boarded via the jet bridge."),
    ("turbulence", "乱気流", "名詞", "Severe turbulence shook the cabin."),
    ("emergency exit", "非常口", "名詞", "Locate your nearest emergency exit."),
    ("layover", "乗り継ぎ滞在", "名詞", "We have a two-hour layover in Seoul."),
    ("standby", "キャンセル待ち", "名詞", "She flew standby to catch an earlier flight."),
    ("apron", "駐機場・エプロン", "名詞", "Ground crew work on the apron."),
    ("de-icing", "除氷", "名詞", "The plane underwent de-icing before takeoff."),
    ("pushback", "プッシュバック", "名詞", "The tug started the pushback from the gate."),
    ("crosswind", "横風", "名詞", "A strong crosswind complicated the landing."),
    ("touchdown", "接地", "名詞", "The touchdown was smooth despite the wind."),
])
P("航空・機内", [
    ("Tower, requesting permission to take off.", "タワー、離陸許可を要請します。"),
    ("Cleared for takeoff, runway two four.", "滑走路24、離陸を許可します。"),
    ("We are holding short of the runway.", "滑走路手前で待機しています。"),
    ("Roger, climbing to flight level three three zero.", "了解、FL330へ上昇します。"),
    ("Please have your boarding pass and ID ready.", "搭乗券と身分証をご用意ください。"),
    ("Boarding will begin in ten minutes.", "搭乗は10分後に始まります。"),
    ("Could I get an aisle seat, please?", "通路側の席をお願いできますか？"),
    ("Is this flight on time?", "この便は定刻通りですか？"),
    ("We missed our connecting flight.", "乗り継ぎ便に乗り遅れました。"),
    ("Please stow your bag under the seat.", "手荷物は座席の下にお入れください。"),
    ("The gate has been changed to B12.", "搭乗口がB12に変更されました。"),
    ("Would you like something to drink?", "お飲み物はいかがですか？"),
])

# ─────────────────────────────────────────────────────────────
# 気象（→ 地学）
# ─────────────────────────────────────────────────────────────
W("地学", "700", [
    ("atmospheric pressure", "気圧", "名詞", "Low atmospheric pressure often brings rain."),
    ("cold front", "寒冷前線", "名詞", "A cold front will pass through tonight."),
    ("humidity", "湿度", "名詞", "High humidity makes it feel hotter."),
    ("precipitation", "降水", "名詞", "Heavy precipitation is expected tomorrow."),
    ("forecast", "予報", "名詞", "The forecast calls for clear skies."),
    ("typhoon", "台風", "名詞", "A powerful typhoon is approaching Kyushu."),
    ("cyclone", "低気圧・サイクロン", "名詞", "The cyclone brought destructive winds."),
    ("cumulonimbus", "積乱雲", "名詞", "Cumulonimbus clouds signal a thunderstorm."),
    ("dew point", "露点", "名詞", "Fog forms when the temperature nears the dew point."),
    ("air mass", "気団", "名詞", "A warm air mass raised the temperature."),
    ("jet stream", "偏西風・ジェット気流", "名詞", "The jet stream steers weather systems."),
    ("barometer", "気圧計", "名詞", "The barometer is falling rapidly."),
    ("gust", "突風", "名詞", "A sudden gust knocked over the umbrella."),
    ("drought", "干ばつ", "名詞", "The region suffered a long drought."),
    ("frost", "霜", "名詞", "Frost damaged the young crops."),
    ("visibility", "視程", "名詞", "Dense fog reduced visibility to 50 meters."),
    ("heat wave", "熱波", "名詞", "A heat wave gripped the city for a week."),
    ("hail", "ひょう", "名詞", "Large hail dented several cars."),
    ("wind chill", "体感温度", "名詞", "The wind chill made it feel below zero."),
    ("meteorology", "気象学", "名詞", "Meteorology predicts weather patterns."),
    ("low-pressure system", "低気圧", "名詞", "A low-pressure system is developing offshore."),
    ("thunderstorm", "雷雨", "名詞", "The thunderstorm knocked out the power."),
    ("overcast", "曇天の", "形容詞", "The sky was overcast all day."),
    ("evaporation", "蒸発", "名詞", "Evaporation cools the ocean surface."),
    ("climate", "気候", "名詞", "The region has a mild climate."),
])
P("気象", [
    ("What's the forecast for tomorrow?", "明日の天気予報は？"),
    ("A typhoon is heading our way.", "台風がこちらに向かっている。"),
    ("It's going to rain heavily this afternoon.", "午後は大雨になりそうだ。"),
    ("Better take an umbrella just in case.", "念のため傘を持って行った方がいい。"),
    ("The humidity is unbearable today.", "今日は湿気がひどい。"),
    ("Visibility is poor because of the fog.", "霧で視界が悪い。"),
    ("A heat wave is expected next week.", "来週は熱波が予想される。"),
    ("The temperature will drop sharply tonight.", "今夜は急に冷え込む。"),
    ("Strong winds are forecast along the coast.", "沿岸部で強風が予報されている。"),
    ("It cleared up in the afternoon.", "午後には晴れた。"),
    ("There's a chance of thunderstorms.", "雷雨の可能性がある。"),
    ("The roads may freeze overnight.", "夜間に道路が凍結するかもしれない。"),
])

# ─────────────────────────────────────────────────────────────
# 地学（→ 地学）
# ─────────────────────────────────────────────────────────────
W("地学", "800", [
    ("tectonic plate", "プレート", "名詞", "Earthquakes occur where tectonic plates meet."),
    ("seismic wave", "地震波", "名詞", "Seismic waves travel through the earth."),
    ("magma", "マグマ", "名詞", "Magma rises through cracks in the crust."),
    ("erosion", "浸食", "名詞", "Erosion carved the deep canyon."),
    ("sediment", "堆積物", "名詞", "Layers of sediment formed the rock."),
    ("fault line", "断層", "名詞", "The city sits on an active fault line."),
    ("crust", "地殻", "名詞", "The earth's crust is relatively thin."),
    ("mantle", "マントル", "名詞", "The mantle lies beneath the crust."),
    ("epicenter", "震央", "名詞", "The epicenter was 20 kilometers offshore."),
    ("volcanic eruption", "火山噴火", "名詞", "The volcanic eruption spewed ash for days."),
    ("mineral", "鉱物", "名詞", "Quartz is a common mineral."),
    ("strata", "地層", "名詞", "The cliff reveals colorful rock strata."),
    ("glacier", "氷河", "名詞", "The glacier is retreating each year."),
    ("geothermal", "地熱の", "形容詞", "Iceland uses geothermal energy widely."),
    ("aquifer", "帯水層", "名詞", "The town draws water from an aquifer."),
    ("subduction", "沈み込み", "名詞", "Subduction pushes one plate beneath another."),
    ("weathering", "風化", "名詞", "Weathering breaks rock into soil."),
    ("fossil", "化石", "名詞", "They found a dinosaur fossil in the cliff."),
    ("lava", "溶岩", "名詞", "Lava flowed down the mountainside."),
    ("magnitude", "マグニチュード", "名詞", "The quake had a magnitude of seven."),
    ("landslide", "地滑り", "名詞", "Heavy rain triggered a landslide."),
    ("plateau", "台地・高原", "名詞", "The village sits on a high plateau."),
    ("continental drift", "大陸移動", "名詞", "Continental drift reshaped the map over ages."),
    ("bedrock", "岩盤", "名詞", "The foundation rests on solid bedrock."),
    ("topography", "地形", "名詞", "The rugged topography slowed the survey."),
])
P("地学", [
    ("An earthquake just struck offshore.", "沖合で地震が起きた。"),
    ("The volcano is showing signs of activity.", "火山に活動の兆候が出ている。"),
    ("Heavy rain could trigger a landslide.", "大雨で地滑りが起きるかもしれない。"),
    ("The river has eroded the bank.", "川が岸を浸食している。"),
    ("They drilled down to the bedrock.", "岩盤まで掘り下げた。"),
    ("This area sits on an active fault.", "この地域は活断層の上にある。"),
    ("We found fossils in these rock layers.", "この地層から化石が見つかった。"),
    ("The glacier has retreated a lot.", "氷河がかなり後退した。"),
    ("Geothermal heat warms the springs.", "地熱が温泉を温めている。"),
    ("The quake measured six in magnitude.", "地震の規模はマグニチュード6だった。"),
    ("Aftershocks may continue for days.", "余震が数日続くかもしれない。"),
    ("The soil here is rich in minerals.", "ここの土は鉱物が豊富だ。"),
])

# ─────────────────────────────────────────────────────────────
# 原子力工学（→ 物理）
# ─────────────────────────────────────────────────────────────
W("物理", "900", [
    ("nuclear reactor", "原子炉", "名詞", "The nuclear reactor generates steam for turbines."),
    ("fission", "核分裂", "名詞", "Nuclear fission splits heavy atoms."),
    ("fusion", "核融合", "名詞", "Fusion powers the sun."),
    ("radiation", "放射線", "名詞", "Workers monitor radiation levels closely."),
    ("isotope", "同位体", "名詞", "Uranium-235 is a fissile isotope."),
    ("coolant", "冷却材", "名詞", "Water serves as the reactor's coolant."),
    ("control rod", "制御棒", "名詞", "Control rods absorb neutrons to slow the reaction."),
    ("chain reaction", "連鎖反応", "名詞", "A chain reaction sustains the fission process."),
    ("enrichment", "濃縮", "名詞", "Uranium enrichment increases the fissile content."),
    ("meltdown", "炉心溶融", "名詞", "Loss of coolant can cause a meltdown."),
    ("half-life", "半減期", "名詞", "This isotope has a half-life of 30 years."),
    ("shielding", "遮蔽", "名詞", "Lead shielding blocks gamma rays."),
    ("reactor core", "炉心", "名詞", "The reactor core holds the fuel rods."),
    ("neutron", "中性子", "名詞", "A neutron triggers the fission."),
    ("decay", "崩壊", "名詞", "Radioactive decay releases energy."),
    ("containment vessel", "格納容器", "名詞", "The containment vessel prevents leaks."),
    ("dosimeter", "線量計", "名詞", "Each worker carries a dosimeter."),
    ("criticality", "臨界", "名詞", "The reactor reached criticality safely."),
    ("spent fuel", "使用済み燃料", "名詞", "Spent fuel is stored in cooling pools."),
    ("moderator", "減速材", "名詞", "The moderator slows the neutrons."),
    ("gamma ray", "ガンマ線", "名詞", "Gamma rays require heavy shielding."),
    ("contamination", "汚染", "名詞", "They checked the site for contamination."),
    ("decommissioning", "廃炉", "名詞", "Decommissioning the plant takes decades."),
    ("radioactive waste", "放射性廃棄物", "名詞", "Radioactive waste needs long-term storage."),
    ("thermal power", "熱出力", "名詞", "The reactor's thermal power is 3 gigawatts."),
])
P("原子力", [
    ("Radiation levels are within safe limits.", "放射線量は安全な範囲内だ。"),
    ("Insert the control rods to slow the reaction.", "反応を抑えるため制御棒を挿入して。"),
    ("The coolant pump has failed.", "冷却材ポンプが故障した。"),
    ("We need to shut down the reactor.", "原子炉を停止する必要がある。"),
    ("Everyone must wear a dosimeter here.", "ここでは全員線量計を着けること。"),
    ("The containment vessel is holding.", "格納容器は保たれている。"),
    ("Check the area for contamination.", "その区域の汚染を確認して。"),
    ("Spent fuel goes to the cooling pool.", "使用済み燃料は冷却プールへ運ぶ。"),
    ("Stay behind the shielding.", "遮蔽の後ろにいて。"),
    ("The reactor reached criticality on schedule.", "原子炉は予定通り臨界に達した。"),
    ("Evacuate if the alarm sounds.", "警報が鳴ったら避難して。"),
    ("Decommissioning will take many years.", "廃炉には何年もかかる。"),
])

# ─────────────────────────────────────────────────────────────
# 家事（→ 生活）
# ─────────────────────────────────────────────────────────────
W("生活", "400", [
    ("laundry", "洗濯物", "名詞", "I need to do the laundry today."),
    ("chores", "家事", "名詞", "We split the household chores."),
    ("sweep", "掃く", "動詞", "Please sweep the kitchen floor."),
    ("mop", "モップがけする", "動詞", "Mop the floor after you sweep it."),
    ("dust", "ほこりを払う", "動詞", "Dust the shelves once a week."),
    ("scrub", "こすり洗いする", "動詞", "Scrub the pot to remove the stains."),
    ("rinse", "すすぐ", "動詞", "Rinse the dishes under running water."),
    ("wipe", "拭く", "動詞", "Wipe the counter with a damp cloth."),
    ("fold", "たたむ", "動詞", "Fold the towels and put them away."),
    ("iron", "アイロンをかける", "動詞", "I need to iron this shirt."),
    ("detergent", "洗剤", "名詞", "Add one scoop of detergent."),
    ("stain", "しみ・汚れ", "名詞", "This stain won't come out."),
    ("trash", "ごみ", "名詞", "Take out the trash tonight."),
    ("recycling", "リサイクル・資源ごみ", "名詞", "Sort the recycling by type."),
    ("tidy up", "片付ける", "動詞", "Let's tidy up before the guests arrive."),
    ("declutter", "整理して物を減らす", "動詞", "We decluttered the whole closet."),
    ("vacuum", "掃除機をかける", "動詞", "Vacuum the living room carpet."),
    ("hang out", "干す", "動詞", "Hang out the washing to dry."),
    ("leftovers", "残り物", "名詞", "We'll eat the leftovers tomorrow."),
    ("groceries", "食料品", "名詞", "I'll pick up some groceries on the way."),
    ("dishcloth", "ふきん", "名詞", "Wring out the dishcloth."),
    ("clothesline", "物干し", "名詞", "Peg the socks on the clothesline."),
    ("spring cleaning", "大掃除", "名詞", "We do spring cleaning every March."),
    ("errand", "用事・使い", "名詞", "I have a few errands to run."),
    ("household", "家庭・世帯", "名詞", "Running a household takes real effort."),
])
P("家事", [
    ("Can you take out the trash?", "ごみを出してくれる？"),
    ("I'll do the dishes if you cook.", "料理してくれるなら私が皿を洗う。"),
    ("Don't forget to hang out the laundry.", "洗濯物を干すのを忘れないで。"),
    ("The floor needs a good vacuum.", "床はしっかり掃除機をかけないと。"),
    ("Let's tidy up before they arrive.", "来る前に片付けよう。"),
    ("This stain won't come out.", "この汚れが落ちない。"),
    ("Whose turn is it to cook tonight?", "今夜の料理は誰の番？"),
    ("Could you fold the towels?", "タオルをたたんでくれる？"),
    ("I'll run to the store for groceries.", "食料品を買いに店へ行ってくる。"),
    ("Wipe the table after dinner.", "夕食のあとテーブルを拭いて。"),
    ("We should declutter the closet.", "クローゼットを整理した方がいい。"),
    ("Add more detergent to the wash.", "洗濯にもう少し洗剤を足して。"),
])


# ─────────────────────────────────────────────────────────────
# 挿入
# ─────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="件数だけ表示して挿入しない")
    args = ap.parse_args()

    with db() as conn:
        have_w = {r[0].strip().lower()
                  for r in conn.execute("SELECT english FROM words")}
        have_p = {r[0].strip().lower()
                  for r in conn.execute("SELECT english FROM phrases")}

        new_w = [w for w in WORDS if w[0].strip().lower() not in have_w]
        # シード内の重複(同一 english)も1件に圧縮
        seen = set()
        uniq_w = []
        for w in new_w:
            k = w[0].strip().lower()
            if k in seen:
                continue
            seen.add(k)
            uniq_w.append(w)

        new_p = []
        seen_p = set()
        for p in PHRASES:
            k = p[0].strip().lower()
            if k in have_p or k in seen_p:
                continue
            seen_p.add(k)
            new_p.append(p)

        print(f"WORDS  : 定義 {len(WORDS)} / 新規 {len(uniq_w)} "
              f"(既存重複 {len(WORDS) - len(uniq_w)})")
        print(f"PHRASES: 定義 {len(PHRASES)} / 新規 {len(new_p)} "
              f"(既存重複 {len(PHRASES) - len(new_p)})")
        # domain 別内訳
        by_dom: dict[str, int] = {}
        for w in uniq_w:
            by_dom[w[5]] = by_dom.get(w[5], 0) + 1
        for d, n in sorted(by_dom.items(), key=lambda x: -x[1]):
            print(f"   {d}: {n}")

        if args.dry_run:
            print("[dry-run] 挿入しません。")
            return 0

        conn.executemany(
            "INSERT INTO words (english, japanese, part_of_speech, example, "
            "level, domain) VALUES (?, ?, ?, ?, ?, ?)", uniq_w,
        )
        conn.executemany(
            "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
            new_p,
        )
        print(f"挿入完了: words +{len(uniq_w)} / phrases +{len(new_p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
