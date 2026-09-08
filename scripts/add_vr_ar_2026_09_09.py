# ruff: noqa: E501
"""VR・AR新ドメイン(2026-09-09・authored by Claude)。ユーザー提起「VR AR XR」。既存フィジカルAI(埋め込みAI/ロボティクス)とは別軸の、没入型/空間コンピューティングの消費者・業務用途語彙を新設。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_vr_ar_2026_09_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("virtual reality", "仮想現実(バーチャルリアリティ)。コンピューターが生成した3次元空間を、専用のヘッドセットなどを通じて実際にその場にいるかのように体験できる技術。VR。", "名詞", "She put on the headset and stepped into a virtual reality where she could walk through ancient Rome.", "VR・AR", "400"),
    ("augmented reality", "拡張現実(オーグメンテッドリアリティ)。カメラ映像や透過型ディスプレイを通して見た現実の風景に、コンピューターが生成した画像や情報を重ねて表示する技術。AR。", "名詞", "The AR app overlaid navigation arrows directly onto the live camera view of the street.", "VR・AR", "420"),
    ("extended reality", "拡張現実の総称(XR)。VR・AR・MRなど、現実と仮想を融合させる技術全般を包括して指す上位概念。", "名詞", "Industry conferences now use the umbrella term \"extended reality\" to cover VR, AR, and everything in between.", "VR・AR", "550"),
    ("mixed reality", "複合現実(ミックスドリアリティ)。現実の物体と仮想のデジタルオブジェクトが、単に重なるだけでなく互いの位置関係を認識し合いながら共存・相互作用する技術。MR。", "名詞", "In mixed reality, a virtual character can walk behind your real couch and appear to be blocked by it.", "VR・AR", "580"),
    ("spatial computing", "空間コンピューティング。現実の3次元空間を認識・理解し、その空間内にデジタル情報やオブジェクトを配置して操作できるようにするコンピューティングの考え方・技術。", "名詞", "Spatial computing lets you place a virtual monitor on your real desk and it stays there even as you move around.", "VR・AR", "650"),
    ("immersive", "没入感のある、周囲を包み込むような。ユーザーの視覚・聴覚などを覆い、その世界に入り込んだように感じさせる様子を表す形容詞。", "形容詞", "The game's 360-degree sound design makes the experience remarkably immersive.", "VR・AR", "450"),
    ("immersion", "没入感。ユーザーが仮想環境に視覚・聴覚などの感覚を包み込まれ、その世界に入り込んでいると感じる度合いや状態。", "名詞", "Higher resolution displays and wider fields of view increase the sense of immersion in VR.", "VR・AR", "500"),
    ("presence", "プレゼンス。仮想環境の中にいるとき、頭では作り物だと分かっていても心理的・身体的に「本当にそこにいる」と感じてしまう主観的な感覚。臨場感。", "名詞", "Even though he knew it was a simulation, the height of the virtual cliff triggered a genuine sense of presence and made his legs shake.", "VR・AR", "750"),
    ("head-mounted display", "ヘッドマウントディスプレイ(HMD)。頭部に装着し、目の前に映像を表示する表示装置の総称。VR・ARゴーグルやヘッドセットの中核技術。", "名詞", "Early head-mounted displays were so heavy they had to be suspended from the ceiling.", "VR・AR", "500"),
    ("VR headset", "VRヘッドセット。ディスプレイやセンサーを内蔵し、頭に装着してVR体験をするための機器。単体で動作するスタンドアロン型と、PCやスマホに接続するタイプがある。", "名詞", "Standalone VR headsets don't need to be tethered to a PC or console.", "VR・AR", "420"),
    ("AR glasses", "ARグラス。眼鏡型の形状をした、拡張現実の映像を表示するデバイス。レンズ越しに現実の風景を見ながら、その上に情報や画像を重ねて表示する。", "名詞", "AR glasses can display turn-by-turn directions right in your field of view as you walk.", "VR・AR", "480"),
    ("smart glasses", "スマートグラス。カメラやディスプレイ、通信機能などを備えた眼鏡型のウェアラブル機器。ARグラスより広く、通知表示やカメラ撮影など汎用的な機能を持つものも含む総称。", "名詞", "Some smart glasses can record video and take photos hands-free with a simple voice command.", "VR・AR", "460"),
    ("VR controller", "VRコントローラー。手に持って使用し、位置や動き、ボタン操作をVR空間内に反映させるための入力デバイス。", "名詞", "She squeezed the trigger on her VR controller to pick up the virtual object.", "VR・AR", "450"),
    ("haptic glove", "ハプティックグローブ。手袋型の触覚デバイス。振動や抵抗力(フォースフィードバック)を指先や手のひらに伝えることで、仮想の物体に触れているかのような感覚を再現する。", "名詞", "The haptic glove applied resistance to her fingers as she gripped the virtual ball, so it felt like it had real weight.", "VR・AR", "700"),
    ("depth sensor", "深度センサー。カメラの前にある物体や空間までの距離(奥行き)を測定するセンサー。ARで現実空間の形状を把握し、仮想物体を正しく配置・遮蔽するために使われる。", "名詞", "The phone's depth sensor lets the AR app figure out how far away the table is so it can place a virtual lamp on top of it convincingly.", "VR・AR", "650"),
    ("inside-out tracking", "インサイドアウトトラッキング。ヘッドセット自体に搭載されたカメラで周囲の環境を撮影・解析し、外部センサーなしで自分の位置や向きを把握する追跡方式。", "名詞", "Inside-out tracking lets you use the headset anywhere in the room without installing external sensors on the walls.", "VR・AR", "800"),
    ("outside-in tracking", "アウトサイドイントラッキング。部屋の壁や天井などに設置した外部センサー(ベースステーションやカメラ)で、ヘッドセットやコントローラーの位置を外側から追跡する方式。", "名詞", "Outside-in tracking generally offers very high precision but requires setting up external sensors around the room.", "VR・AR", "800"),
    ("hand tracking", "ハンドトラッキング。カメラやセンサーで手や指の位置・形状をリアルタイムに検出し、コントローラーを持たずに手の動きだけでVR・AR空間を操作する技術。", "名詞", "With hand tracking enabled, she could pinch her fingers together in midair to select a menu item.", "VR・AR", "650"),
    ("eye tracking", "アイトラッキング。センサーで眼球の動きを検知し、ユーザーがどこを見ているか(視線の方向)をリアルタイムに把握する技術。", "名詞", "Eye tracking lets the headset know exactly which menu item you're looking at so you can select it just by blinking.", "VR・AR", "620"),
    ("gesture recognition", "ジェスチャー認識。手や体の動き・形といった身振りをカメラやセンサーで検出し、コマンドとして解釈する技術。", "名詞", "The system's gesture recognition let users swipe through photos by simply waving a hand in the air.", "VR・AR", "600"),
    ("positional tracking", "位置トラッキング。ヘッドセットやコントローラーが3次元空間内のどこにあるか(前後・左右・上下の移動)を検出する技術。回転だけを検知する方式と区別される。", "名詞", "Without positional tracking, leaning forward to peek around a corner wouldn't move your view at all.", "VR・AR", "750"),
    ("6DOF", "6自由度(シックスディーオーエフ)。前後・左右・上下の並進運動3種と、ピッチ・ヨー・ロールの回転運動3種、合計6種類の動きすべてを検知・反映できることを表す語。", "名詞", "A 6DOF headset lets you physically walk around a virtual object and view it from any angle, not just turn your head.", "VR・AR", "880"),
    ("field of view", "視野角(フィールドオブビュー)。ヘッドセットを装着したときに、一度に見ることができる映像の角度の範囲。数値が大きいほど周辺視野まで画像で覆われ、没入感が高まる。", "名詞", "A wider field of view makes VR feel less like looking through a pair of binoculars.", "VR・AR", "620"),
    ("room-scale", "ルームスケールの。プレイヤーが実際の部屋の中を数メートル歩き回りながら体験できる規模のVRを表す形容詞。座ったままや立ったままの体験と対比される。", "形容詞", "Room-scale VR lets you physically duck under a virtual beam or step around a virtual obstacle.", "VR・AR", "600"),
    ("passthrough", "パススルー。VRヘッドセットに内蔵されたカメラの映像を装着中に表示し、ヘッドセットを外さなくても周囲の実際の様子を確認できるようにする機能。", "名詞", "She used passthrough to check if her cat had wandered into the room while she was playing a VR game.", "VR・AR", "700"),
    ("motion-to-photon latency", "モーショントゥフォトンレイテンシ。頭や手を動かしてから、その動きが反映された映像が画面に表示されるまでの遅延時間。この遅延が大きいほどVR酔いを引き起こしやすいとされる。", "名詞", "Developers aim to keep motion-to-photon latency under about 20 milliseconds to avoid making users feel sick.", "VR・AR", "900"),
    ("VR sickness", "VR酔い(シミュレーターシックネス)。VR映像を見て体は静止しているのに視覚的には動いているように感じることで生じる、めまいや吐き気などの不快な症状。", "名詞", "Smooth locomotion in VR games can trigger VR sickness in users who are sensitive to the mismatch between visual and physical motion.", "VR・AR", "550"),
    ("vergence-accommodation conflict", "輻輳調節矛盾(ふくそうちょうせつむじゅん)。多くのVR・ARディスプレイでは、両目の視線を寄せる距離(輻輳距離)と、目の焦点を合わせる距離(調節距離)が一致しないため生じる、目の疲労や違和感の原因とされる現象。", "名詞", "The vergence-accommodation conflict is considered one of the main causes of eye strain during long VR sessions.", "VR・AR", "950"),
    ("spatial audio", "空間オーディオ。音源の方向や距離、部屋の反響などを再現し、音が3次元空間のどこから聞こえているかを立体的に感じさせる音響技術。", "名詞", "Spatial audio made the virtual bird sound like it was chirping just above and behind her left shoulder.", "VR・AR", "650"),
    ("virtual world", "仮想世界。コンピューター上に作られた、ユーザーがアバターなどを通じて探索・交流できる持続的な3次元空間。", "名詞", "Thousands of users log into the virtual world every day to socialize, attend events, and build things together.", "VR・AR", "480"),
    ("social VR", "ソーシャルVR。複数のユーザーがそれぞれのアバターを通じて同じ仮想空間に集まり、会話や交流を行うことに重点を置いたVRサービスの総称。", "名詞", "In social VR spaces, friends who live on opposite sides of the world can hang out together as if they were in the same room.", "VR・AR", "550"),
    ("VR arcade", "VRアーケード。個人で機材を揃えなくても、店舗に設置された高性能なVR機器を使って体験できる施設・業態。", "名詞", "The VR arcade downtown lets you rent a headset and play free-roam games in a large open space.", "VR・AR", "500"),
    ("locomotion", "ロコモーション。VR空間内でアバターやプレイヤー視点を移動させる方法や仕組みの総称。瞬間的に移動先を指定してワープする「テレポート」方式や、コントローラーで滑らかに歩く「スムーズロコモーション」方式などがある。", "名詞", "Teleport-based locomotion is popular because it causes far less VR sickness than smooth locomotion.", "VR・AR", "700"),
    ("volumetric video", "ボリュメトリックビデオ。多数のカメラで人物や物体をあらゆる角度から同時に撮影し、それらを3次元データとして再構成した動画。視聴者は視点を自由に変えながら見ることができる。", "名詞", "The concert was captured as volumetric video, so fans wearing VR headsets could walk around the performer on stage.", "VR・AR", "850"),
    ("360-degree video", "360度動画。複数の広角カメラで全方位を同時に撮影し、視聴者が視線の向きを自由に変えながら見られるようにした映像。", "名詞", "She watched a 360-degree video of the coral reef and could look up, down, or behind her just by turning her head.", "VR・AR", "550"),
    ("photogrammetry", "フォトグラメトリ(写真測量法)。多数の写真を様々な角度から撮影し、それらを解析して物体や空間の立体的な3Dモデルを作り出す技術。", "名詞", "The team used photogrammetry to turn hundreds of overlapping photos of the ancient ruins into a detailed 3D model.", "VR・AR", "850"),
    ("spatial mapping", "空間マッピング。センサーやカメラで周囲の実空間の形状を読み取り、壁・床・家具などの3次元的な構造データ(メッシュなど)として構築すること。", "名詞", "Spatial mapping lets the AR headset know that there's a real table in front of you so a virtual character can walk around it instead of through it.", "VR・AR", "780"),
    ("AR cloud", "ARクラウド。現実世界の詳細な3次元地図情報をクラウド上に蓄積・共有し、複数のユーザーやデバイスが同じ場所に紐づいたAR情報を共通して参照・体験できるようにする仕組みの構想。", "名詞", "With an AR cloud, one person could leave a virtual note stuck to a lamppost and a friend walking by later could see it in the same spot.", "VR・AR", "800"),
    ("spatial anchor", "スペーシャルアンカー。現実空間内の特定の位置に仮想オブジェクトの座標を固定・記憶させておく仕組み。アプリを終了して再度起動しても、同じ場所に表示され続ける。", "名詞", "She placed a spatial anchor on her desk so the virtual sticky note would still be there the next time she opened the app.", "VR・AR", "780"),
    ("marker-based AR", "マーカー型AR。QRコードのような模様やあらかじめ登録した特定の画像(マーカー)をカメラで認識し、その位置を基準に仮想の映像を表示する方式のAR。", "名詞", "Marker-based AR apps ask you to point your camera at a printed marker before the 3D model appears on top of it.", "VR・AR", "700"),
    ("markerless AR", "マーカーレス型AR。専用のマーカーを使わず、カメラ映像から床や壁などの平面・特徴点を自動的に検出して、その場に仮想オブジェクトを表示する方式のAR。", "名詞", "Markerless AR lets you place a virtual sofa on any flat floor the camera detects, without printing out a special marker first.", "VR・AR", "750"),
    ("occlusion", "オクルージョン。ARにおいて、現実の物体が仮想オブジェクトより手前にある場合に、その部分を正しく隠して表示する処理。これが無いと仮想物体が常に手前に透けて見えてしまう。", "名詞", "Without proper occlusion, a virtual character standing behind a real chair would incorrectly appear to float in front of it.", "VR・AR", "850"),
    ("overlay", "オーバーレイ。現実の映像や風景の上に、文字・画像・3Dオブジェクトなどのデジタル情報を重ねて表示すること、またはその重ねられた情報自体。", "名詞", "The AR navigation app adds a simple arrow overlay onto the live camera view to show which way to turn.", "VR・AR", "550"),
    ("see-through display", "シースルーディスプレイ(透過型ディスプレイ)。レンズ越しに現実の景色をそのまま見ながら、その上に映像を重ねて表示できるディスプレイ。光学的にレンズを透過させる方式(光学シースルー)と、カメラ映像に合成して表示する方式(ビデオシースルー)がある。", "名詞", "AR glasses with a see-through display let you keep eye contact with the person in front of you while still seeing floating notifications.", "VR・AR", "700"),
    ("stereoscopic display", "立体視ディスプレイ(ステレオスコピックディスプレイ)。左目と右目にそれぞれわずかに視点の異なる映像を独立して表示することで、奥行きのある立体的な映像として知覚させる表示方式。", "名詞", "VR headsets use a stereoscopic display, showing a slightly different image to each eye to create the illusion of depth.", "VR・AR", "750"),
    ("foveated rendering", "フォービエイテッドレンダリング。アイトラッキングなどで検出した視線の中心(中心窩で見ている部分)だけを高精細に描画し、視野の周辺部分は解像度を落として処理負荷を軽減する描画技術。", "名詞", "Foveated rendering lets the headset save processing power by rendering the edges of your vision in lower detail than the center.", "VR・AR", "900"),
    ("holographic display", "ホログラフィックディスプレイ。特殊な光学技術によって、専用の眼鏡をかけなくても空間に立体的な映像を映し出す、あるいはそのように見せる表示装置。", "名詞", "In the demo, a holographic display projected a spinning 3D model of the product that visitors could walk around without wearing any headset.", "VR・AR", "650"),
    ("VR training", "VRトレーニング。VR技術を用いて、危険な状況や高コストな設備を伴う作業を安全かつ繰り返し練習できるようにした研修・訓練の手法。", "名詞", "Airlines use VR training to let pilots practice emergency procedures without the cost and risk of a real aircraft.", "VR・AR", "500"),
    ("VR exposure therapy", "VR曝露療法(バーチャルリアリティエクスポージャーセラピー)。恐怖症やPTSDなどの治療で、患者が恐れる状況をVR空間で安全にコントロールしながら疑似体験させ、徐々に慣れさせていく心理療法。", "名詞", "In VR exposure therapy, a patient afraid of flying can experience a realistic virtual flight from the safety of a therapist's office.", "VR・AR", "650"),
    ("virtual tourism", "バーチャル観光(バーチャルツーリズム)。実際にその場所へ行かなくても、VRや360度動画などを通じて遠隔地の観光地や文化財を疑似的に訪れ体験すること。", "名詞", "Virtual tourism lets people who can't travel due to health or cost explore places like the pyramids of Giza from home.", "VR・AR", "500"),
]


def main() -> None:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
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
        print(f"inserted={inserted} skipped={skipped}")


if __name__ == "__main__":
    main()
