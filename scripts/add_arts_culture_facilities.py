# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""芸術用語(舞台/工芸/舞踊/映画/メディアアート、新設)＋大衆文化(新設)＋
美術・博物館(既存拡張)＋動物園・植物園(新設), authored by Claude
(2026-08-05・ユーザー要望:「芸術用語（舞台、工芸、舞踊、映画、メディア
アート他）大衆文化　博物館　美術館　動物園　植物園」＋「質は落とさない
ように、段階的に実装ください」).

既存の「美術・博物館」(43語)は美術館運営・絵画技法が中心だったため、劇場/
映画製作/舞踊/陶芸等の実演芸術・工芸を「芸術」として新設。動物園と植物園は
既存の「動物」「植物」ドメインとは別に、**施設・運営としての語彙**
(飼育員/展示/温室管理等)として新設した。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_arts_culture_facilities.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

ARTS = "芸術"
POPCULTURE = "大衆文化"
MUSEUM = "美術・博物館"
ZOOGARDEN = "動物園・植物園"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 芸術: 舞台 ---
    ("playwright", "劇作家", "名詞", "The playwright rewrote the final scene just days before opening night.", ARTS, "700"),
    ("stage direction", "舞台指示・演出", "名詞", "The stage direction called for the lights to dim slowly.", ARTS, "700"),
    ("understudy", "代役", "名詞", "The understudy went on stage when the lead actor fell ill.", ARTS, "750"),
    ("rehearsal", "リハーサル", "名詞", "The cast held a full rehearsal the night before the premiere.", ARTS, "550"),
    ("proscenium", "プロセニアム（額縁舞台）", "名詞", "The proscenium frames the stage like a picture for the audience.", ARTS, "900"),
    ("set design", "舞台美術・セットデザイン", "名詞", "The set design transformed the small stage into a sprawling castle.", ARTS, "700"),
    ("curtain call", "カーテンコール", "名詞", "The audience gave a standing ovation during the curtain call.", ARTS, "650"),
    # --- 芸術: 工芸(陶芸中心) ---
    ("ceramics", "陶芸・セラミックス", "名詞", "She has studied ceramics for over a decade under a master potter.", ARTS, "650"),
    ("kiln", "窯", "名詞", "The pottery is fired in a kiln at extremely high temperatures.", ARTS, "700"),
    ("glazing (pottery)", "釉薬掛け", "名詞", "Glazing gives the finished pottery its shine and color.", ARTS, "750"),
    ("potter's wheel", "ろくろ", "名詞", "She centered the clay carefully before starting the potter's wheel.", ARTS, "700"),
    ("throwing (pottery)", "ろくろ挽き", "名詞", "Throwing a bowl takes years of practice to master.", ARTS, "800"),
    ("woodworking", "木工", "名詞", "He took up woodworking as a way to relax after retirement.", ARTS, "600"),
    ("weaving", "織物・機織り", "名詞", "Weaving by hand can take weeks to finish a single piece of cloth.", ARTS, "650"),
    ("lacquerware", "漆器", "名詞", "Lacquerware is coated in many thin layers to build its deep shine.", ARTS, "800"),
    # --- 芸術: 舞踊 ---
    ("choreography", "振付", "名詞", "The choreography combined ballet with modern dance techniques.", ARTS, "750"),
    ("choreographer", "振付師", "名詞", "The choreographer spent months preparing the new production.", ARTS, "750"),
    ("ballet", "バレエ", "名詞", "She has trained in ballet since she was five years old.", ARTS, "550"),
    ("pirouette", "ピルエット（回転）", "名詞", "The dancer completed three pirouettes without losing her balance.", ARTS, "850"),
    ("contemporary dance", "コンテンポラリーダンス", "名詞", "Contemporary dance often breaks away from the strict rules of classical ballet.", ARTS, "750"),
    ("folk dance", "民族舞踊", "名詞", "The festival featured a traditional folk dance passed down for generations.", ARTS, "650"),
    # --- 芸術: 映画 ---
    ("film director", "映画監督", "名詞", "The film director insisted on shooting the scene at sunrise.", ARTS, "600"),
    ("cinematography", "撮影技法", "名詞", "The film won an award for its stunning cinematography.", ARTS, "800"),
    ("screenwriter", "脚本家", "名詞", "The screenwriter spent two years developing the story.", ARTS, "700"),
    ("storyboard", "絵コンテ", "名詞", "The director sketched a storyboard for every scene before filming began.", ARTS, "700"),
    ("editing (film)", "編集（映像の）", "名詞", "Editing can completely change the pacing and mood of a film.", ARTS, "650"),
    ("visual effects (VFX)", "視覚効果（VFX）", "名詞", "The visual effects team created the entire alien city digitally.", ARTS, "750"),
    ("film score", "映画音楽・サウンドトラック", "名詞", "The film score builds tension long before anything happens on screen.", ARTS, "700"),
    ("box office", "興行収入", "名詞", "The movie topped the box office for three weeks in a row.", ARTS, "650"),
    # --- 芸術: メディアアート ---
    ("media art", "メディアアート", "名詞", "Media art uses technology like projection and sensors as its medium.", ARTS, "800"),
    ("interactive installation", "インタラクティブ・インスタレーション", "名詞", "The interactive installation responded to the movement of visitors in the room.", ARTS, "850"),
    ("projection mapping", "プロジェクションマッピング", "名詞", "Projection mapping turned the entire building facade into a moving canvas.", ARTS, "850"),
    ("generative art", "ジェネラティブアート", "名詞", "Generative art is created by an algorithm rather than drawn by hand.", ARTS, "850"),
    # --- 大衆文化 ---
    ("pop culture", "大衆文化・ポップカルチャー", "名詞", "The show became a huge part of pop culture almost overnight.", POPCULTURE, "600"),
    ("subculture", "サブカルチャー", "名詞", "The city has a thriving skateboarding subculture.", POPCULTURE, "700"),
    ("fandom", "ファンダム", "名詞", "The show's fandom organizes conventions all over the world.", POPCULTURE, "650"),
    ("viral trend", "バイラルトレンド", "名詞", "The dance became a viral trend within just a few days.", POPCULTURE, "650"),
    ("internet meme", "インターネットミーム", "名詞", "The photo turned into an internet meme almost instantly.", POPCULTURE, "600"),
    ("celebrity culture", "セレブ文化", "名詞", "Celebrity culture has changed a lot since the rise of social media.", POPCULTURE, "700"),
    ("cult following", "カルト的な人気", "名詞", "The low-budget film built a cult following years after it flopped in theaters.", POPCULTURE, "800"),
    ("mainstream (culture)", "主流・メインストリーム", "名詞", "The genre finally broke into the mainstream after years underground.", POPCULTURE, "700"),
    ("nostalgia trend", "ノスタルジア・トレンド", "名詞", "The nostalgia trend brought back fashion styles from decades ago.", POPCULTURE, "750"),
    # --- 美術・博物館（既存ドメインに追加） ---
    ("art restoration", "美術品の修復", "名詞", "Art restoration slowly removed centuries of grime from the painting.", MUSEUM, "800"),
    ("provenance", "来歴・出所（美術品の）", "名詞", "The painting's provenance was traced back through five previous owners.", MUSEUM, "900"),
    ("art dealer", "美術商", "名詞", "The art dealer helped the museum acquire the rare sculpture.", MUSEUM, "700"),
    ("private collection", "個人コレクション", "名詞", "The painting had been hidden in a private collection for decades.", MUSEUM, "700"),
    ("art auction", "美術品競売", "名詞", "The painting sold for a record price at the art auction.", MUSEUM, "650"),
    ("kinetic sculpture", "動く彫刻・キネティックアート", "名詞", "The kinetic sculpture slowly rotated in the museum's entrance hall.", MUSEUM, "850"),
    ("triptych", "三連画", "名詞", "The triptych tells a single story across three connected panels.", MUSEUM, "900"),
    # --- 動物園・植物園（新設） ---
    ("zookeeper", "動物園の飼育員", "名詞", "The zookeeper feeds the elephants the same time every morning.", ZOOGARDEN, "600"),
    ("animal enclosure", "動物の展示スペース・飼育場", "名詞", "The new animal enclosure gives the tigers much more room to roam.", ZOOGARDEN, "700"),
    ("captive breeding", "飼育下繁殖", "名詞", "Captive breeding programs have helped bring several species back from the edge of extinction.", ZOOGARDEN, "850"),
    ("enrichment (animal)", "エンリッチメント（動物福祉）", "名詞", "Enrichment activities keep zoo animals mentally stimulated throughout the day.", ZOOGARDEN, "850"),
    ("petting zoo", "ふれあい動物園", "名詞", "Kids lined up to feed the goats at the petting zoo.", ZOOGARDEN, "550"),
    ("aquarium tank", "水槽（水族館の）", "名詞", "The massive aquarium tank holds thousands of fish and a few sharks.", ZOOGARDEN, "650"),
    ("conservation program", "保全プログラム", "名詞", "The zoo runs a conservation program for endangered frogs.", ZOOGARDEN, "750"),
    ("botanical collection", "植物コレクション", "名詞", "The garden's botanical collection includes plants from every continent.", ZOOGARDEN, "800"),
    ("glasshouse", "温室（ガラス張りの）", "名詞", "The glasshouse keeps tropical plants warm even in winter.", ZOOGARDEN, "700"),
    ("horticulturist", "園芸家・植物栽培の専門家", "名詞", "A horticulturist carefully tends every plant in the botanical garden.", ZOOGARDEN, "750"),
    ("exhibit signage", "展示解説板", "名詞", "The exhibit signage explains where each animal comes from.", ZOOGARDEN, "700"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
