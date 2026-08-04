# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""New "DIY・工具" word domain + top-up of the existing "DIY・工具" phrase
scene, authored by Claude (2026-08-04・ユーザー要望:
「diy工具 フレーズと単語充実。プラスドライバーはあるがマイナスドライバーが
フレーズにない。六角レンチ 六角穴付きボルト レンチ モンキーレンチ スパナ
他とくに単語充実。フレーズはホームセンターで買い物や加工をお願いする用語
など」).

既存の 機械工学 domain には bolt/clamp/drill/hammer/nail/pliers/saw/
screwdriver/screw/wrench のような総称的な工具語は既にあるが、具体的な
工具名・金物名(マイナスドライバー、六角レンチ、六角穴付きボルト、
モンキーレンチ、トルクレンチ、コンビネーションレンチ、集成材・ドライ
ウォールなどの資材名)は手薄だった。それらを新規 domain='DIY・工具' として
追加する。また既存の phrases scene='DIY・工具'(12件)は基本的なDIY作業の
指示文のみで、ホームセンター店員に加工・レンタル・調色・取り付けなどを
依頼する場面別の言い回しが無かったため、そこを補強する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
against the live words/phrases tables before insertion.

Run:  python scripts/add_diy_tools.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- ドライバー類 ---
    ("flathead screwdriver", "マイナスドライバー", "名詞", "I need a flathead screwdriver to open this old paint can.", "DIY・工具", "450"),
    ("slotted screwdriver", "マイナスドライバー(規格名)", "名詞", "The screw has a single slot, so use a slotted screwdriver, not a Phillips.", "DIY・工具", "650"),
    ("Phillips screwdriver", "プラスドライバー", "名詞", "Most furniture kits only come with a small Phillips screwdriver.", "DIY・工具", "450"),
    # --- 六角系 ---
    ("hex key", "六角レンチ・六角キー(アレンキー)", "名詞", "You'll need a 4mm hex key to assemble this bookshelf.", "DIY・工具", "500"),
    ("Allen wrench set", "六角レンチセット", "名詞", "This Allen wrench set covers everything from 1.5mm to 10mm.", "DIY・工具", "600"),
    ("hex socket head bolt", "六角穴付きボルト", "名詞", "The bike frame is held together with hex socket head bolts.", "DIY・工具", "750"),
    # --- レンチ類 ---
    ("monkey wrench", "モンキーレンチ", "名詞", "The plumber grabbed a monkey wrench to loosen the old pipe fitting.", "DIY・工具", "500"),
    ("adjustable wrench", "自在スパナ・アジャスタブルレンチ", "名詞", "Slide the jaw of the adjustable wrench to fit the nut exactly.", "DIY・工具", "550"),
    ("socket wrench", "ソケットレンチ", "名詞", "A socket wrench is faster than a regular wrench for lug nuts.", "DIY・工具", "650"),
    ("torque wrench", "トルクレンチ", "名詞", "Use a torque wrench so you don't overtighten the head bolts.", "DIY・工具", "750"),
    ("combination wrench", "コンビネーションレンチ", "名詞", "A combination wrench has an open end on one side and a box end on the other.", "DIY・工具", "700"),
    ("ratchet", "ラチェット(工具)", "名詞", "The ratchet lets you turn the bolt without lifting the socket off each time.", "DIY・工具", "650"),
    ("pipe wrench", "パイプレンチ", "名詞", "He clamped the pipe wrench onto the fitting and gave it a firm twist.", "DIY・工具", "700"),
    ("locking pliers", "ロッキングプライヤー(バイスグリップ)", "名詞", "Locking pliers can clamp onto a bolt and hold it in place on their own.", "DIY・工具", "750"),
    ("socket set", "ソケットセット", "名詞", "This socket set has both metric and imperial sizes.", "DIY・工具", "700"),
    # --- 切る・削る ---
    ("box cutter", "カッター(段ボール用)", "名詞", "Use a box cutter to open the shipping cartons.", "DIY・工具", "450"),
    ("jigsaw", "ジグソー(電動工具)", "名詞", "A jigsaw is great for cutting curved shapes out of plywood.", "DIY・工具", "650"),
    ("circular saw", "丸ノコ", "名詞", "He used a circular saw to cut the board down to length.", "DIY・工具", "650"),
    ("hacksaw", "弓のこ", "名詞", "Cut through the metal pipe with a hacksaw.", "DIY・工具", "600"),
    ("coping saw", "糸のこ(曲線切り用)", "名詞", "Use a coping saw for the tight curves in the molding.", "DIY・工具", "750"),
    ("sander", "サンダー(電動工具)", "名詞", "The sander made quick work of the rough tabletop.", "DIY・工具", "600"),
    # --- 打つ・締める・固定する ---
    ("mallet", "木づち・ゴムハンマー", "名詞", "Tap the chisel gently with a mallet, not a metal hammer.", "DIY・工具", "550"),
    ("rubber mallet", "ゴムハンマー", "名詞", "Use a rubber mallet to knock the tile into place without cracking it.", "DIY・工具", "600"),
    ("vise", "万力", "名詞", "Clamp the workpiece in a vise before you start filing it.", "DIY・工具", "600"),
    ("C-clamp", "Cクランプ", "名詞", "Hold the two boards together with a C-clamp while the glue dries.", "DIY・工具", "650"),
    ("nail gun", "釘打ち機(エア工具)", "名詞", "A nail gun speeds up framing work a lot compared to a hammer.", "DIY・工具", "750"),
    ("staple gun", "タッカー(ホッチキス式工具)", "名詞", "Use a staple gun to attach the fabric to the frame.", "DIY・工具", "650"),
    ("sawhorse", "作業馬(ソーホース)", "名詞", "Set the plank across two sawhorses before you cut it.", "DIY・工具", "650"),
    # --- 塗装・接着・仕上げ ---
    ("caulking gun", "コーキングガン", "名詞", "Load the tube into the caulking gun before you seal the window frame.", "DIY・工具", "650"),
    ("wood glue", "木工用接着剤", "名詞", "Wood glue holds better than nails for this kind of joint.", "DIY・工具", "500"),
    ("paint roller", "ペイントローラー", "名詞", "A paint roller covers a wall much faster than a brush.", "DIY・工具", "500"),
    ("paint tray", "ペイントトレー", "名詞", "Pour the paint into the paint tray before you load the roller.", "DIY・工具", "500"),
    ("primer (paint)", "下塗り剤・プライマー(塗装用)", "名詞", "Apply a coat of primer before you paint over the bare wood.", "DIY・工具", "600"),
    ("wood stain", "ウッドステイン(木材用着色剤)", "名詞", "This wood stain brings out the grain without hiding it.", "DIY・工具", "600"),
    ("putty knife", "パテベラ", "名詞", "Smooth the filler into the crack with a putty knife.", "DIY・工具", "650"),
    # --- 資材 ---
    ("plywood", "合板・ベニヤ板", "名詞", "We built the shelves out of half-inch plywood.", "DIY・工具", "550"),
    ("drywall", "石膏ボード", "名詞", "Screw the drywall into the studs every 30 centimeters or so.", "DIY・工具", "600"),
    ("2x4", "ツーバイフォー材", "名詞", "The frame is built from standard 2x4 lumber.", "DIY・工具", "600"),
    ("wall stud", "間柱(壁の下地材)", "名詞", "Find a wall stud with a stud finder before you hang anything heavy.", "DIY・工具", "650"),
    # --- ねじ・ボルト・金物 ---
    ("wood screw", "木ねじ", "名詞", "Wood screws have a coarser thread than machine screws.", "DIY・工具", "500"),
    ("machine screw", "機械ねじ", "名詞", "Machine screws thread into a matching nut or a tapped hole.", "DIY・工具", "650"),
    ("self-tapping screw", "タッピングねじ", "名詞", "A self-tapping screw cuts its own threads as you drive it in.", "DIY・工具", "750"),
    ("anchor bolt", "アンカーボルト", "名詞", "The shelving unit is fixed to the concrete floor with anchor bolts.", "DIY・工具", "800"),
    ("wall anchor", "壁用アンカー", "名詞", "Use a wall anchor if you're driving the screw into hollow drywall.", "DIY・工具", "750"),
    ("duct tape", "ダクトテープ・粘着補修テープ", "名詞", "He held the hose together with duct tape until the new part arrived.", "DIY・工具", "450"),
    ("zip tie", "結束バンド", "名詞", "Bundle the cables together with a zip tie.", "DIY・工具", "500"),
    ("wire stripper", "ワイヤーストリッパー", "名詞", "Use a wire stripper to remove the insulation without nicking the wire.", "DIY・工具", "700"),
    # --- 電動工具・電源 ---
    ("cordless drill", "コードレスドリル", "名詞", "A cordless drill is much easier to use up on a ladder.", "DIY・工具", "550"),
    ("drill bit set", "ドリルビットセット", "名詞", "This drill bit set has sizes for both wood and metal.", "DIY・工具", "600"),
    ("impact driver", "インパクトドライバー", "名詞", "An impact driver delivers more torque than a regular drill for long screws.", "DIY・工具", "700"),
    ("extension cord", "延長コード", "名詞", "Run an extension cord out to the garage for the saw.", "DIY・工具", "450"),
    ("power strip", "電源タップ", "名詞", "Plug the charger and the lamp into the power strip.", "DIY・工具", "450"),
    # --- 安全・保護具 ---
    ("safety glasses", "安全ゴーグル・保護メガネ", "名詞", "Always wear safety glasses when you're using the grinder.", "DIY・工具", "450"),
    ("dust mask", "防じんマスク", "名詞", "Put on a dust mask before you start sanding.", "DIY・工具", "500"),
    # --- 測定 ---
    ("laser level", "レーザー水準器", "名詞", "A laser level makes it much easier to hang a row of frames evenly.", "DIY・工具", "800"),
]

PHRASES: list[tuple[str, str]] = [
    ("Do you have a flathead screwdriver?", "マイナスドライバーはありますか？"),
    ("Could you cut this board to 90 centimeters?", "この板を90センチにカットしていただけますか？"),
    ("Can you cut this pipe to length?", "このパイプを必要な長さに切っていただけますか？"),
    ("Could you cut this glass to fit the frame?", "このガラスを枠に合うようにカットしていただけますか？"),
    ("What kind of wood is this?", "これは何の木材ですか？"),
    ("Is this plywood or solid wood?", "これは合板ですか、それとも無垢材ですか？"),
    ("Which screw size should I use for this?", "これにはどのサイズのねじを使えばいいですか？"),
    ("What size bolt do I need for this hole?", "この穴にはどのサイズのボルトが必要ですか？"),
    ("Which aisle has the plumbing supplies?", "配管用品はどの通路にありますか？"),
    ("Where can I find the paint section?", "塗料売り場はどこですか？"),
    ("Do you rent out power tools here?", "こちらでは電動工具のレンタルをしていますか？"),
    ("How much does it cost to rent a drill for a day?", "ドリルを1日レンタルするといくらですか？"),
    ("What's your return policy on power tools?", "電動工具の返品ポリシーを教えてください。"),
    ("Can I return this if it doesn't work?", "動作しなかった場合、これは返品できますか？"),
    ("Could you mix this paint to match this sample?", "このサンプルに合わせてペンキを調色していただけますか？"),
    ("Do you have this color in a smaller can?", "この色はもっと小さい缶でありますか？"),
    ("Is this bolt metric or imperial?", "このボルトはミリ規格ですか、インチ規格ですか？"),
    ("I need metric screws, not imperial ones.", "インチ規格ではなくミリ規格のねじが必要です。"),
    ("Can you price match this to another store?", "他店の価格に合わせていただけますか？"),
    ("Do you have this item in stock?", "この商品の在庫はありますか？"),
    ("When will this be back in stock?", "これはいつ再入荷しますか？"),
    ("Do you offer installation service for this?", "これの取り付けサービスはありますか？"),
    ("Could someone install this for me?", "どなたかこれを取り付けていただけますか？"),
    ("Do you have a torque wrench I could borrow?", "トルクレンチをお借りできますか？"),
    ("Which wall anchor works best for drywall?", "石膏ボードにはどの壁用アンカーが最適ですか？"),
    ("Can you recommend a wood stain for outdoor use?", "屋外用のウッドステインでおすすめはありますか？"),
    ("Could you show me where the hex keys are?", "六角レンチの場所を教えていただけますか？"),
    ("I need a longer extension cord for this.", "これにはもっと長い延長コードが必要です。"),
    ("Do you sell lumber in 2x4s?", "2x4材は販売していますか？"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, 'DIY・工具')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
