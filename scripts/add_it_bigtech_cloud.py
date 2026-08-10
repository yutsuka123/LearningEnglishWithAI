# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add big-tech-industry / cloud-service / data-center vocabulary to the
existing "IT" domain, authored by Claude (2026-08-10・ユーザー要望:
「産業にITを入れて、GAFAMや巨大テック関係の用語、クラウド/SaaS/PaaS等の
サービス用語、データセンター用語」)。taxonomy.py側でIT domainは大分類
「IT・情報」から「産業」へ移動済み(このファイルは中身の語彙追加のみ担当)。

事前にDBを確認した結果、`SaaS`/`PaaS`/`IaaS`/`load balancer`/`uptime`は
既に`ソフトウェア工学`ドメインに存在するため対象外(重複追加しない)。
「GAFAM」等の実在の企業名は使わず、巨大テック企業を指す一般的な語
(hyperscaler, tech giant, Big Tech等)に留めた。

対象語彙: 巨大テック企業を語る一般語(hyperscaler, tech giant, Big Tech,
platform economy, walled garden, vendor lock-in, antitrust, ecosystem
lock-in, network effect, data monopoly, gatekeeper(規制文脈))、クラウド
サービス関連(cloud provider, cloud computing, multi-cloud, hybrid cloud,
on-premises, cloud migration, cloud-native, serverless computing,
managed service)、データセンター用語(data center, server farm, server
rack, cooling system(データセンター文脈)、colocation, uptime
guarantee(既存uptimeとは別語として)、redundant power supply,
disaster recovery site)、配信・ネットワーク(content delivery network
(CDN)、edge computing、edge server、bandwidth(既存の可能性要確認)、
latency(既存の可能性要確認のため対象外予定))。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_it_bigtech_cloud.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 巨大テック企業を語る一般語 ---
    ("hyperscaler", "ハイパースケーラー(巨大クラウド事業者)", "名詞", "Only a handful of hyperscalers operate at that scale globally.", "IT", "800"),
    ("tech giant", "テック大手・巨大テック企業", "名詞", "The tech giant announced a new data privacy policy.", "IT", "550"),
    ("Big Tech", "ビッグテック(巨大IT企業群の総称)", "名詞", "Regulators are increasing scrutiny of Big Tech.", "IT", "600"),
    ("platform economy", "プラットフォーム経済", "名詞", "The platform economy has reshaped how people find work.", "IT", "750"),
    ("walled garden", "ウォールドガーデン(閉じた囲い込みエコシステム)", "名詞", "Critics say the app store operates as a walled garden.", "IT", "800"),
    ("vendor lock-in", "ベンダーロックイン(特定業者への依存)", "名詞", "Switching clouds later can be hard because of vendor lock-in.", "IT", "800"),
    ("antitrust", "独占禁止(の)", "形容詞", "The company is facing an antitrust investigation.", "IT", "800"),
    ("network effect", "ネットワーク効果", "名詞", "The platform's value grows through a strong network effect.", "IT", "800"),
    ("data monopoly", "データの独占", "名詞", "Some lawmakers worry about a data monopoly forming.", "IT", "850"),
    ("gatekeeper (platform)", "ゲートキーパー(規制対象の大規模プラットフォーム)", "名詞", "The regulation applies to companies designated as gatekeepers.", "IT", "850"),
    # --- クラウドサービス関連 ---
    ("cloud provider", "クラウド事業者", "名詞", "We compared pricing across three major cloud providers.", "IT", "550"),
    ("cloud computing", "クラウドコンピューティング", "名詞", "Cloud computing lets you rent servers instead of owning them.", "IT", "500"),
    ("multi-cloud", "マルチクラウド(複数事業者の併用)", "名詞", "Our multi-cloud setup avoids depending on a single provider.", "IT", "750"),
    ("hybrid cloud", "ハイブリッドクラウド", "名詞", "The bank runs a hybrid cloud that mixes on-premises and cloud servers.", "IT", "750"),
    ("on-premises", "オンプレミス(自社設備での運用)", "形容詞", "Some sensitive workloads still run on-premises.", "IT", "700"),
    ("cloud migration", "クラウド移行", "名詞", "The company is in the middle of a cloud migration project.", "IT", "700"),
    ("cloud-native", "クラウドネイティブ", "形容詞", "The app was designed to be cloud-native from the start.", "IT", "750"),
    ("serverless computing", "サーバーレスコンピューティング", "名詞", "Serverless computing charges you only for what you actually use.", "IT", "800"),
    ("managed service", "マネージドサービス", "名詞", "We switched to a managed service so we no longer patch servers ourselves.", "IT", "700"),
    # --- データセンター用語 ---
    ("data center", "データセンター", "名詞", "The company built a new data center to handle growing traffic.", "IT", "500"),
    ("server farm", "サーバーファーム", "名詞", "The server farm consumes a huge amount of electricity.", "IT", "650"),
    ("server rack", "サーバーラック", "名詞", "Each server rack holds dozens of machines.", "IT", "550"),
    ("colocation", "コロケーション(サーバー預かりサービス)", "名詞", "We rent space at a colocation facility instead of building our own data center.", "IT", "800"),
    ("uptime guarantee", "稼働率保証(SLA)", "名詞", "The contract includes a 99.9% uptime guarantee.", "IT", "750"),
    ("redundant power supply", "冗長電源(バックアップ電源)", "名詞", "The data center relies on a redundant power supply in case of an outage.", "IT", "800"),
    ("disaster recovery site", "災害復旧サイト(バックアップ拠点)", "名詞", "Data is mirrored to a disaster recovery site in another region.", "IT", "800"),
    ("cooling system (data center)", "冷却システム(データセンターの)", "名詞", "The cooling system keeps the servers from overheating.", "IT", "600"),
    # --- 配信・ネットワーク ---
    ("content delivery network (CDN)", "コンテンツ配信ネットワーク(CDN)", "名詞", "The CDN caches content closer to users to reduce delay.", "IT", "700"),
    ("edge computing", "エッジコンピューティング", "名詞", "Edge computing processes data closer to where it's generated.", "IT", "800"),
    ("edge server", "エッジサーバー", "名詞", "The edge server responds faster because it's physically closer.", "IT", "750"),
]

PHRASES: list[tuple[str, str]] = [
    ("Which cloud provider are we using for this project?", "このプロジェクトではどのクラウド事業者を使っていますか？"),
    ("We're planning a cloud migration next quarter.", "来四半期にクラウド移行を計画しています。"),
    ("Let's go serverless for this feature to save on cost.", "コスト削減のためこの機能はサーバーレスにしましょう。"),
    ("Our data is backed up to a disaster recovery site.", "データは災害復旧サイトにバックアップされています。"),
    ("The data center lost power for a few minutes.", "データセンターが数分間停電しました。"),
    ("We avoid vendor lock-in by staying multi-cloud.", "マルチクラウドにすることでベンダーロックインを避けています。"),
    ("Regulators are looking closely at Big Tech's market power.", "規制当局はビッグテックの市場支配力を注視しています。"),
    ("This app store really is a walled garden.", "このアプリストアは本当に閉じたエコシステムですね。"),
    ("Our uptime guarantee is 99.9% under the contract.", "契約上の稼働率保証は99.9%です。"),
    ("The CDN should reduce load times for overseas users.", "CDNのおかげで海外ユーザーの読み込み時間が短くなるはずです。"),
    ("We're moving some workloads to edge computing.", "一部の処理をエッジコンピューティングに移行しています。"),
    ("How many hyperscalers actually compete in this market?", "この市場で実際に競争しているハイパースケーラーはいくつありますか？"),
    ("The colocation facility handles power and cooling for us.", "コロケーション施設が電源と冷却を管理してくれています。"),
    ("Antitrust regulators fined the company last year.", "独占禁止法の規制当局が昨年その企業に罰金を科しました。"),
    ("We keep some systems on-premises for compliance reasons.", "コンプライアンス上の理由で一部のシステムはオンプレミスのままです。"),
    ("The platform benefits from a strong network effect.", "そのプラットフォームは強力なネットワーク効果の恩恵を受けています。"),
    ("Let's check the server rack temperature.", "サーバーラックの温度を確認しましょう。"),
    ("A hybrid cloud gives us more flexibility.", "ハイブリッドクラウドの方が柔軟性が高いです。"),
    ("We chose a managed service to reduce operational overhead.", "運用負荷を減らすためマネージドサービスを選びました。"),
    ("The redundant power supply kicked in during the outage.", "停電の際に冗長電源が作動しました。"),
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
                "VALUES (?, ?, 'IT・ビルド/エラー')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
