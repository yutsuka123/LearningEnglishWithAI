# ruff: noqa: E501  (data-heavy seed script)
"""Add aerospace / sports / music / disease-name / legal-procedure vocabulary
with examples. Authored by Claude — no app/OpenAI API calls. Levels are set to
a placeholder here and finalized by scripts/relevel.py (fine scale).

Run:  python scripts/add_genres2.py   (then run scripts/relevel.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS_BY_DOMAIN: dict[str, list[tuple[str, str, str]]] = {
    "航空・宇宙": [
        ("altitude", "高度", "The plane climbed to a high altitude."),
        ("cockpit", "操縦室・コックピット", "The pilot sat in the cockpit."),
        ("fuselage", "機体・胴体", "The fuselage was damaged in the storm."),
        ("aileron", "補助翼", "The ailerons control the plane's roll."),
        ("runway", "滑走路", "The jet sped down the runway."),
        ("hangar", "格納庫", "The plane was towed into the hangar."),
        ("turbine", "タービン", "The turbine spins at high speed."),
        ("thrust", "推力", "The engines produce enormous thrust."),
        ("propulsion", "推進", "Ion propulsion is used in deep space."),
        ("aerodynamics", "空気力学", "Aerodynamics affects fuel efficiency."),
        ("jet engine", "ジェットエンジン", "A jet engine sucks in air."),
        ("supersonic", "超音速の", "The fighter flew at supersonic speed."),
        ("autopilot", "自動操縦", "The pilot switched on the autopilot."),
        ("turbulence", "乱気流", "We hit turbulence over the mountains."),
        ("satellite", "衛星", "The satellite orbits the earth."),
        ("orbit", "軌道", "The capsule entered orbit."),
        ("trajectory", "弾道・軌道", "Engineers plotted the rocket's trajectory."),
        ("reentry", "大気圏再突入", "Reentry generates intense heat."),
        ("telemetry", "遠隔測定(テレメトリ)", "Telemetry data streamed to mission control."),
        ("booster", "ブースター(補助ロケット)", "The booster separated after launch."),
        ("capsule", "宇宙カプセル", "The capsule splashed down in the ocean."),
        ("astronaut", "宇宙飛行士", "The astronaut floated in zero gravity."),
        ("cosmonaut", "宇宙飛行士(ロシア)", "The cosmonaut returned from the station."),
        ("spacewalk", "船外活動", "The crew performed a spacewalk."),
        ("docking", "ドッキング", "The docking with the station succeeded."),
        ("escape velocity", "脱出速度", "A rocket must reach escape velocity."),
        ("launch pad", "発射台", "The rocket stood on the launch pad."),
        ("rover", "探査車(ローバー)", "The rover explored the Martian surface."),
        ("probe", "探査機", "The probe sent back images of Saturn."),
        ("control tower", "管制塔", "The control tower cleared us for takeoff."),
    ],
    "スポーツ": [
        ("referee", "審判・レフェリー", "The referee blew the whistle."),
        ("umpire", "(野球などの)審判", "The umpire called him out."),
        ("coach", "コーチ・監督", "The coach encouraged the team."),
        ("athlete", "運動選手", "The athlete trained every day."),
        ("stadium", "スタジアム・競技場", "The stadium was packed with fans."),
        ("tournament", "トーナメント・大会", "She won the tennis tournament."),
        ("championship", "選手権", "They reached the championship final."),
        ("marathon", "マラソン", "He finished the marathon in three hours."),
        ("sprint", "短距離走・全力疾走", "She won the 100-meter sprint."),
        ("gymnastics", "体操", "Gymnastics requires great balance."),
        ("defense", "守備・ディフェンス", "Their defense was very strong."),
        ("offense", "攻撃・オフェンス", "The team has a powerful offense."),
        ("penalty", "ペナルティ・反則の罰", "He scored from the penalty spot."),
        ("foul", "反則・ファウル", "The referee called a foul."),
        ("dribble", "ドリブルする", "He dribbled past two defenders."),
        ("serve", "サーブ(する)", "Her serve was too fast to return."),
        ("racket", "ラケット", "He swung the racket hard."),
        ("jersey", "ユニフォーム", "She wore the team jersey."),
        ("medal", "メダル", "He won a gold medal."),
        ("podium", "表彰台", "The winner stood on the podium."),
        ("rookie", "新人選手", "The rookie scored on his debut."),
        ("veteran", "ベテラン選手", "The veteran led the young team."),
        ("opponent", "対戦相手", "He studied his opponent's style."),
        ("substitute", "交代選手", "The coach sent in a substitute."),
        ("spectator", "観客", "The spectators cheered loudly."),
        ("relay race", "リレー競走", "Our team won the relay race."),
        ("knockout", "ノックアウト", "He won by a knockout."),
        ("doping", "ドーピング", "The runner was banned for doping."),
        ("halftime", "ハーフタイム", "They were ahead at halftime."),
        ("lineup", "先発メンバー", "The coach announced the lineup."),
    ],
    "音楽": [
        ("rhythm", "リズム", "She clapped to the rhythm."),
        ("harmony", "ハーモニー・和声", "Their voices blended in harmony."),
        ("tempo", "テンポ", "The conductor set a fast tempo."),
        ("chord", "和音・コード", "He played a minor chord."),
        ("beat", "拍・ビート", "The drum keeps the beat."),
        ("lyrics", "歌詞", "The lyrics are very moving."),
        ("chorus", "コーラス・サビ", "Everyone sang the chorus."),
        ("verse", "(歌の)節・詩", "The second verse is slower."),
        ("symphony", "交響曲", "The orchestra played a symphony."),
        ("concerto", "協奏曲", "She performed a piano concerto."),
        ("sonata", "ソナタ", "He practiced a Beethoven sonata."),
        ("opera", "オペラ", "We watched an Italian opera."),
        ("genre", "ジャンル", "Jazz is my favorite music genre."),
        ("instrument", "楽器", "The violin is a string instrument."),
        ("guitar", "ギター", "He strummed the guitar."),
        ("violin", "バイオリン", "She plays the violin beautifully."),
        ("drum", "ドラム・太鼓", "He beat the drum steadily."),
        ("flute", "フルート", "The flute has a clear tone."),
        ("trumpet", "トランペット", "He played a trumpet solo."),
        ("saxophone", "サクソフォン", "The saxophone led the jazz tune."),
        ("improvise", "即興で演奏する", "Jazz musicians often improvise."),
        ("pitch", "音の高さ・ピッチ", "She sang slightly off pitch."),
        ("octave", "オクターブ", "He sang an octave higher."),
        ("soundtrack", "サウンドトラック", "The movie soundtrack is famous."),
        ("vocalist", "ボーカリスト", "The vocalist hit every note."),
        ("ensemble", "アンサンブル・合奏", "The ensemble played in perfect time."),
        ("composer", "作曲家", "Mozart was a great composer."),
        ("audition", "オーディション", "She passed the choir audition."),
        ("encore", "アンコール", "The crowd demanded an encore."),
        ("performance", "演奏・公演", "Their performance got a standing ovation."),
    ],
    "病名": [
        ("cancer", "癌", "Early detection of cancer saves lives."),
        ("diabetes", "糖尿病", "He manages his diabetes with diet."),
        ("asthma", "喘息", "Her asthma gets worse in spring."),
        ("pneumonia", "肺炎", "He was hospitalized with pneumonia."),
        ("influenza", "インフルエンザ", "Influenza spreads quickly in winter."),
        ("stroke", "脳卒中", "A stroke can cause paralysis."),
        ("heart attack", "心臓発作", "He survived a heart attack."),
        ("hypertension", "高血圧(症)", "Hypertension often has no symptoms."),
        ("allergy", "アレルギー", "She has a severe nut allergy."),
        ("migraine", "偏頭痛", "A migraine kept her in bed."),
        ("arthritis", "関節炎", "Arthritis stiffens his joints."),
        ("anemia", "貧血", "Anemia made her feel tired."),
        ("hepatitis", "肝炎", "Hepatitis affects the liver."),
        ("tuberculosis", "結核", "Tuberculosis attacks the lungs."),
        ("dementia", "認知症", "Her grandmother has dementia."),
        ("depression", "うつ病", "He is being treated for depression."),
        ("insomnia", "不眠症", "Insomnia left him exhausted."),
        ("obesity", "肥満", "Obesity raises the risk of diabetes."),
        ("ulcer", "潰瘍", "Stress can cause a stomach ulcer."),
        ("diarrhea", "下痢", "The infection caused diarrhea."),
        ("constipation", "便秘", "Fiber helps relieve constipation."),
        ("infection", "感染(症)", "The wound developed an infection."),
        ("tumor", "腫瘍", "The tumor was benign."),
        ("concussion", "脳震盪", "He suffered a concussion in the game."),
        ("food poisoning", "食中毒", "The seafood gave him food poisoning."),
        ("dehydration", "脱水症", "Dehydration is dangerous in summer."),
        ("epidemic", "流行病", "The flu epidemic closed the schools."),
        ("pandemic", "パンデミック・世界的流行", "The pandemic changed daily life."),
        ("measles", "はしか", "Measles is a contagious disease."),
        ("chickenpox", "水ぼうそう", "Most children recover from chickenpox."),
    ],
    "法律手続き": [
        ("lawsuit", "訴訟", "She filed a lawsuit against the company."),
        ("plaintiff", "原告", "The plaintiff demanded compensation."),
        ("defendant", "被告", "The defendant pleaded not guilty."),
        ("prosecutor", "検察官", "The prosecutor presented the evidence."),
        ("attorney", "弁護士", "He hired an attorney to defend him."),
        ("testimony", "証言", "Her testimony convinced the jury."),
        ("verdict", "評決", "The jury reached a guilty verdict."),
        ("sentence", "判決・刑", "The judge handed down a harsh sentence."),
        ("appeal", "上訴・控訴", "They filed an appeal against the ruling."),
        ("jury", "陪審", "The jury deliberated for hours."),
        ("trial", "裁判・公判", "The trial lasted three weeks."),
        ("hearing", "審理・公聴会", "The hearing was held on Monday."),
        ("indictment", "起訴", "The grand jury returned an indictment."),
        ("plea", "答弁・申し立て", "He entered a guilty plea."),
        ("settlement", "和解", "They reached an out-of-court settlement."),
        ("subpoena", "召喚状", "The court issued a subpoena."),
        ("deposition", "証言録取", "The witness gave a deposition."),
        ("litigation", "訴訟(手続き)", "The dispute ended in litigation."),
        ("jurisdiction", "管轄(権)", "The case is outside our jurisdiction."),
        ("warrant", "令状", "Police obtained a search warrant."),
        ("acquittal", "無罪判決", "The acquittal surprised everyone."),
        ("conviction", "有罪判決", "His conviction was overturned on appeal."),
        ("damages", "損害賠償(金)", "The court awarded heavy damages."),
        ("injunction", "差止命令", "The judge granted an injunction."),
        ("mediation", "調停", "They settled through mediation."),
        ("arbitration", "仲裁", "The contract requires arbitration."),
        ("statute", "制定法・法令", "The statute was passed last year."),
        ("liability", "法的責任・賠償責任", "The company admitted liability."),
        ("custody", "(身柄の)拘束・親権", "He was taken into custody."),
        ("court order", "裁判所命令", "She violated a court order."),
    ],
}


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
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

    print(f"words: +{w_added} (skipped {w_skipped})  {per_domain}")
    with db() as conn:
        print("totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
