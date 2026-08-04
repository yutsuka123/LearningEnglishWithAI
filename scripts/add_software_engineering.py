# ruff: noqa: E501  (data-heavy seed script: long word/example lines are fine)
"""Grow the thin "ソフトウェア工学" domain (7件) with 100+ new words, authored
by Claude (2026-08-04・ユーザー要望:「ソフトウェア工学すくないかも 英単語で
最低+30、目標+100はほしいかも」+「略語集でもいいかも 略語集（ソフトウェア）」)。

既存の7件（data structure / encapsulation / inheritance / polymorphism /
abstraction / throughput / immutable）や、既存の IT ドメイン(181件: algorithm,
backend, frontend, cache, compiler, debug, deploy, framework, microservice,
refactor, repository, thread, unit test, deadlock 等)とは重複しない語を、
以下の領域で幅広く追加する:

  1. 設計原則・デザインパターン (singleton/factory/observer pattern, DI,
     SOLID, DRY/KISS/YAGNI, coupling/cohesion, technical debt, ...)
  2. テスト (integration/regression test, TDD, BDD, mocking, flaky test, ...)
  3. アーキテクチャ (monolith, event-driven, DDD, load balancer, sharding,
     race condition, mutex, garbage collection, static/dynamic typing, ...)
  4. 開発プロセス (agile, scrum, sprint, code review, feature flag, CI/CD,
     canary release, observability, SLA, uptime/downtime, ...)
  5. バージョン管理 (branch, commit, cherry-pick, rebase, semantic
     versioning, ...)
  6. 略語集(ソフトウェア) — API/SDK/ORM/CRUD/REST/JWT/OAuth/SSO/CI・CD/MVC/
     MVP/MVVM/ACID/CAP定理/IaaS/PaaS/SaaS/IDE/CLI/GUI/LTS/UAT/RPC/gRPC/SDLC
     を、english=略語そのもの、japanese=正式名称+意味、で見出し語として追加。

同じ綴りが別ドメインに別語義で既に存在するもの(coupling=鉄道の連結器、
sprint=陸上の短距離走、branch/commit=ビジネスの支店・約束する、
REST=音楽の休符、ACID=化学の酸、telemetry=航空宇宙のテレメトリ)は、
english見出し語を "coupling (software)" のように既存の曖昧さ回避パターン
(例: "salt (compound)", "satellite (moon)")に倣って区別している。なお
deadlock は IT ドメインに同一概念で既に存在するため追加していない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
against the entire words table (not just this domain).

Run:  python scripts/add_software_engineering.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "ソフトウェア工学"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 設計原則・デザインパターン ---
    ("singleton pattern", "シングルトンパターン", "名詞", "The singleton pattern ensures a class has only one instance throughout the application.", DOMAIN, "700"),
    ("factory pattern", "ファクトリーパターン", "名詞", "We used the factory pattern to create objects without hard-coding their exact class.", DOMAIN, "700"),
    ("observer pattern", "オブザーバーパターン", "名詞", "The observer pattern lets multiple objects react automatically when another object's state changes.", DOMAIN, "750"),
    ("dependency injection", "依存性注入(DI)", "名詞", "Dependency injection makes it much easier to swap in a fake implementation during testing.", DOMAIN, "750"),
    ("SOLID principles", "SOLID原則", "名詞", "Following the SOLID principles helps keep a large codebase maintainable as it grows.", DOMAIN, "800"),
    ("single responsibility principle", "単一責任の原則", "名詞", "The single responsibility principle says a class should have only one reason to change.", DOMAIN, "800"),
    ("open-closed principle", "オープン・クローズドの原則", "名詞", "The open-closed principle means code should be open for extension but closed for modification.", DOMAIN, "800"),
    ("DRY principle", "DRY原則(重複排除の原則)", "名詞", "The DRY principle reminds us not to copy the same validation logic into three different files.", DOMAIN, "700"),
    ("KISS principle", "KISS原則(単純さを保つ原則)", "名詞", "The KISS principle encourages a simple solution over a clever but hard-to-follow one.", DOMAIN, "700"),
    ("YAGNI", "YAGNI(今必要な機能だけを作るという原則)", "名詞", "YAGNI reminds the team not to build configuration options nobody has actually asked for.", DOMAIN, "750"),
    ("separation of concerns", "関心の分離", "名詞", "Separation of concerns keeps the UI code independent from the business logic underneath it.", DOMAIN, "750"),
    ("loose coupling", "疎結合", "名詞", "Loose coupling between the services makes it easier to deploy and scale them independently.", DOMAIN, "750"),
    ("tight coupling", "密結合", "名詞", "Tight coupling between the two modules made it risky to change either one on its own.", DOMAIN, "750"),
    ("cohesion", "凝集度", "名詞", "High cohesion means each module focuses on a single, well-defined responsibility.", DOMAIN, "800"),
    ("coupling (software)", "結合度(ソフトウェア設計)", "名詞", "We measured coupling between modules to decide where to draw the new service boundary.", DOMAIN, "800"),
    ("code smell", "コードの臭い(改善が必要な兆候)", "名詞", "A long parameter list is a classic code smell worth refactoring.", DOMAIN, "700"),
    ("boilerplate code", "ボイラープレートコード(定型的なコード)", "名詞", "The framework generates a lot of boilerplate code just to scaffold a new project.", DOMAIN, "700"),
    ("technical debt", "技術的負債", "名詞", "We took on some technical debt to hit the deadline, but we'll pay it down next quarter.", DOMAIN, "700"),
    ("legacy code", "レガシーコード(旧来のコード)", "名詞", "Nobody wants to touch that legacy code without a solid test suite in place first.", DOMAIN, "650"),
    ("premature optimization", "早すぎる最適化", "名詞", "Premature optimization can waste time speeding up code that was never actually a bottleneck.", DOMAIN, "800"),
    # --- テスト ---
    ("integration test", "結合テスト", "名詞", "The integration tests confirm that the API and the database work together correctly.", DOMAIN, "700"),
    ("regression test", "回帰テスト", "名詞", "We run regression tests before every release to catch features that broke unexpectedly.", DOMAIN, "700"),
    ("test coverage", "テストカバレッジ", "名詞", "Test coverage for this module is only 40%, so we should add more test cases.", DOMAIN, "700"),
    ("test-driven development", "テスト駆動開発(TDD)", "名詞", "In test-driven development, you write a failing test before you write the code to pass it.", DOMAIN, "750"),
    ("behavior-driven development", "ふるまい駆動開発(BDD)", "名詞", "Behavior-driven development describes features in plain language that both engineers and stakeholders can read.", DOMAIN, "800"),
    ("mocking", "モック化", "名詞", "Mocking the external payment API lets us test the checkout logic without making real charges.", DOMAIN, "700"),
    ("stub", "スタブ(仮の実装)", "名詞", "We added a stub for the recommendation service until the real integration is finished.", DOMAIN, "700"),
    ("mutation testing", "ミューテーションテスト", "名詞", "Mutation testing checks whether your tests actually catch small, deliberate changes to the code.", DOMAIN, "850"),
    ("smoke test", "スモークテスト(簡易動作確認)", "名詞", "Run a quick smoke test right after deployment to make sure nothing obvious is broken.", DOMAIN, "700"),
    ("end-to-end test", "E2Eテスト(全体を通したテスト)", "名詞", "The end-to-end test simulates a real user signing up and completing a purchase.", DOMAIN, "750"),
    ("flaky test", "不安定なテスト(フレーキーテスト)", "名詞", "That flaky test fails about once every ten runs for no obvious reason.", DOMAIN, "700"),
    ("test fixture", "テストフィクスチャ(テスト用の準備データ)", "名詞", "The test fixture creates a sample user account before each test case runs.", DOMAIN, "750"),
    ("assertion", "アサーション(検証文)", "名詞", "The assertion checks that the returned value matches exactly what we expected.", DOMAIN, "650"),
    # --- アーキテクチャ ---
    ("monolith", "モノリス(一枚岩型のシステム)", "名詞", "The old monolith handled everything from billing to notifications in a single codebase.", DOMAIN, "750"),
    ("event-driven architecture", "イベント駆動アーキテクチャ", "名詞", "In an event-driven architecture, services react to events instead of calling each other directly.", DOMAIN, "850"),
    ("domain-driven design", "ドメイン駆動設計(DDD)", "名詞", "Domain-driven design encourages the code to mirror the language the business actually uses.", DOMAIN, "850"),
    ("clean architecture", "クリーンアーキテクチャ", "名詞", "Clean architecture keeps the core business rules independent of the framework and the database.", DOMAIN, "850"),
    ("layered architecture", "レイヤードアーキテクチャ(階層型アーキテクチャ)", "名詞", "The layered architecture separates presentation, business logic, and data access into distinct layers.", DOMAIN, "800"),
    ("service-oriented architecture", "サービス指向アーキテクチャ(SOA)", "名詞", "Service-oriented architecture was popular before microservices became the more common term.", DOMAIN, "850"),
    ("API gateway", "APIゲートウェイ", "名詞", "The API gateway routes each incoming request to the right microservice.", DOMAIN, "800"),
    ("message queue", "メッセージキュー", "名詞", "We put the job on a message queue so it can be processed asynchronously.", DOMAIN, "750"),
    ("publish-subscribe", "パブリッシュ・サブスクライブ(Pub/Subモデル)", "名詞", "The publish-subscribe pattern lets one service broadcast events to many subscribers at once.", DOMAIN, "800"),
    ("load balancer", "ロードバランサー", "名詞", "The load balancer distributes incoming traffic across several backend servers.", DOMAIN, "700"),
    ("horizontal scaling", "水平スケーリング", "名詞", "Horizontal scaling means adding more servers instead of making one server bigger.", DOMAIN, "750"),
    ("vertical scaling", "垂直スケーリング", "名詞", "Vertical scaling has a limit — eventually you can't add any more CPU or memory to one box.", DOMAIN, "750"),
    ("sharding", "シャーディング(データ分割)", "名詞", "Sharding splits the database across multiple machines so it can handle more traffic.", DOMAIN, "800"),
    ("eventual consistency", "結果整合性", "名詞", "With eventual consistency, all replicas will agree on the data eventually, but not instantly.", DOMAIN, "850"),
    ("idempotency", "冪等性", "名詞", "Idempotency means calling the same API twice has the same effect as calling it once.", DOMAIN, "850"),
    ("race condition", "競合状態(レースコンディション)", "名詞", "A race condition can occur when two threads update the same variable at the same time.", DOMAIN, "750"),
    ("mutex", "ミューテックス(排他制御)", "名詞", "The mutex prevents two threads from writing to the shared resource at the same time.", DOMAIN, "800"),
    ("semaphore", "セマフォ(同時実行数の制御)", "名詞", "The semaphore limits how many threads can access the connection pool at once.", DOMAIN, "850"),
    ("thread safety", "スレッドセーフ性", "名詞", "We reviewed the code for thread safety before enabling concurrent access.", DOMAIN, "800"),
    ("garbage collection", "ガベージコレクション(自動メモリ管理)", "名詞", "Garbage collection automatically frees memory that the program no longer needs.", DOMAIN, "700"),
    ("memory leak", "メモリリーク", "名詞", "A memory leak in the background worker was slowly using up all the available RAM.", DOMAIN, "700"),
    ("stack overflow", "スタックオーバーフロー", "名詞", "Infinite recursion without a base case will eventually cause a stack overflow.", DOMAIN, "700"),
    ("static typing", "静的型付け", "名詞", "Static typing catches many type errors at compile time instead of at runtime.", DOMAIN, "750"),
    ("dynamic typing", "動的型付け", "名詞", "Dynamic typing lets a variable change type at runtime, which is flexible but a bit riskier.", DOMAIN, "750"),
    ("type safety", "型安全性", "名詞", "Type safety helps prevent bugs where a function receives an argument of the wrong type.", DOMAIN, "750"),
    # --- 開発プロセス ---
    ("agile methodology", "アジャイル手法", "名詞", "Our team adopted agile methodology to ship smaller changes more frequently.", DOMAIN, "700"),
    ("scrum", "スクラム", "名詞", "In scrum, the team plans its work in short, fixed-length sprints.", DOMAIN, "700"),
    ("sprint (agile)", "スプリント(アジャイル開発の反復期間)", "名詞", "We committed to finishing three stories by the end of this sprint.", DOMAIN, "650"),
    ("product backlog", "プロダクトバックログ", "名詞", "The product owner prioritizes new requests at the top of the product backlog.", DOMAIN, "750"),
    ("kanban board", "かんばんボード", "名詞", "The kanban board shows every task as it moves from 'to do' to 'done'.", DOMAIN, "650"),
    ("waterfall model", "ウォーターフォールモデル", "名詞", "The waterfall model completes each phase, like design and testing, in strict sequence.", DOMAIN, "700"),
    ("code review", "コードレビュー", "名詞", "Every pull request needs at least one code review before it can be merged.", DOMAIN, "650"),
    ("pull request", "プルリクエスト", "名詞", "Could you open a pull request once you're done with the changes?", DOMAIN, "600"),
    ("pair programming", "ペアプログラミング", "名詞", "Pair programming helped the new hire learn the codebase much faster than reading docs alone.", DOMAIN, "700"),
    ("monorepo", "モノレポ(単一リポジトリでの一元管理)", "名詞", "We moved all our services into a single monorepo to simplify dependency management.", DOMAIN, "800"),
    ("feature flag", "フィーチャーフラグ(機能フラグ)", "名詞", "We rolled out the new checkout flow behind a feature flag so we could disable it instantly.", DOMAIN, "750"),
    ("canary release", "カナリアリリース", "名詞", "A canary release sends the new version to a small percentage of users before a full rollout.", DOMAIN, "850"),
    ("blue-green deployment", "ブルーグリーンデプロイメント", "名詞", "Blue-green deployment lets us switch traffic to the new version instantly if something goes wrong.", DOMAIN, "850"),
    ("continuous integration", "継続的インテグレーション(CI)", "名詞", "Continuous integration runs the full test suite automatically every time someone pushes code.", DOMAIN, "750"),
    ("continuous delivery", "継続的デリバリー(CD)", "名詞", "Continuous delivery means every change that passes the tests is ready to ship at any time.", DOMAIN, "800"),
    ("build pipeline", "ビルドパイプライン", "名詞", "The build pipeline compiles, tests, and packages the app in just a few minutes.", DOMAIN, "750"),
    ("observability", "オブザーバビリティ(可観測性)", "名詞", "Good observability makes it much easier to figure out why production suddenly got slow.", DOMAIN, "850"),
    ("telemetry (software)", "テレメトリ(利用状況・性能データ)", "名詞", "We added telemetry to track how long each request takes once the app is in production.", DOMAIN, "800"),
    ("service level agreement (SLA)", "サービスレベル契約(SLA)", "名詞", "Our service level agreement promises 99.9% uptime to every customer.", DOMAIN, "850"),
    ("uptime", "稼働時間・アップタイム", "名詞", "The service has maintained 99.99% uptime over the past year.", DOMAIN, "650"),
    ("downtime", "ダウンタイム・停止時間", "名詞", "We scheduled the migration during a period of low traffic to minimize downtime.", DOMAIN, "650"),
    # --- バージョン管理 ---
    ("branch (git)", "ブランチ(Git)", "名詞", "Create a new branch before you start working on the fix.", DOMAIN, "550"),
    ("commit (git)", "コミット(Git)", "名詞", "Each commit should represent one logical, self-contained change.", DOMAIN, "550"),
    ("cherry-pick", "チェリーピック(特定コミットの取り込み)", "名詞", "We cherry-picked the bug fix onto the release branch without merging everything else.", DOMAIN, "750"),
    ("rebase", "リベース", "名詞", "Rebase your branch onto main before opening the pull request.", DOMAIN, "700"),
    ("merge conflict", "マージコンフリクト(競合)", "名詞", "Git flagged a merge conflict because both of us edited the same line.", DOMAIN, "650"),
    ("git blame", "git blame(変更履歴を追跡するコマンド)", "名詞", "I ran git blame to find out who added this line and when.", DOMAIN, "700"),
    ("changelog", "変更履歴(チェンジログ)", "名詞", "Don't forget to update the changelog before tagging the release.", DOMAIN, "650"),
    ("semantic versioning", "セマンティックバージョニング(SemVer)", "名詞", "Semantic versioning tells you whether an update is safe just by reading the version number.", DOMAIN, "800"),
    # --- 略語集(ソフトウェア) ---
    ("API", "API（Application Programming Interface）— アプリケーション同士が機能やデータをやり取りするための取り決め", "名詞", "We expose a public API so other teams can integrate with our service.", DOMAIN, "700"),
    ("SDK", "SDK（Software Development Kit）— 特定のプラットフォーム向けにアプリを開発するためのツール一式", "名詞", "Download the SDK to start building apps for this platform.", DOMAIN, "700"),
    ("ORM", "ORM（Object-Relational Mapping）— オブジェクトとリレーショナルDBのデータを対応付ける仕組み", "名詞", "The ORM lets us query the database using ordinary objects instead of raw SQL.", DOMAIN, "800"),
    ("CRUD", "CRUD（Create, Read, Update, Delete）— データ操作の基本4種類の頭文字", "名詞", "This admin panel just performs basic CRUD operations on the user table.", DOMAIN, "750"),
    ("REST (API)", "REST（Representational State Transfer）— HTTPを使ったWeb APIの設計スタイル", "名詞", "Our REST API returns a JSON response for every endpoint.", DOMAIN, "750"),
    ("JWT", "JWT（JSON Web Token）— 認証情報を安全にやり取りするためのトークン形式", "名詞", "The server issues a JWT as soon as the user logs in successfully.", DOMAIN, "800"),
    ("OAuth", "OAuth（Open Authorization）— パスワードを渡さずに第三者アプリへアクセス権限を委任する仕組み", "名詞", "We use OAuth so users can sign in with their existing Google account.", DOMAIN, "750"),
    ("SSO", "SSO（Single Sign-On）— 一度のログインで複数サービスを利用できる仕組み", "名詞", "With SSO enabled, employees only need to log in once to reach all our internal tools.", DOMAIN, "750"),
    ("CI/CD", "CI/CD（Continuous Integration / Continuous Delivery）— コードの統合とリリースを自動化する開発手法", "名詞", "Our CI/CD pipeline automatically deploys to staging after every merge to main.", DOMAIN, "750"),
    ("MVC", "MVC（Model-View-Controller）— データ・表示・制御ロジックを分離する設計パターン", "名詞", "The framework follows the MVC pattern to keep the code organized.", DOMAIN, "750"),
    ("MVP", "MVP（Model-View-Presenter）— UIロジックを分離する設計パターン。「実用最小限の製品」を指すビジネス用語のMVPとは別の意味なので文脈に注意", "名詞", "In the MVP pattern, the presenter handles all the logic between the view and the model.", DOMAIN, "800"),
    ("MVVM", "MVVM（Model-View-ViewModel）— ビューとロジックをデータバインディングで結びつける設計パターン", "名詞", "MVVM works especially well with frameworks that support two-way data binding.", DOMAIN, "850"),
    ("ACID (database)", "ACID（Atomicity, Consistency, Isolation, Durability）— データベーストランザクションが満たすべき4つの性質", "名詞", "A properly ACID-compliant database won't leave your data half-updated if a transaction fails.", DOMAIN, "850"),
    ("CAP theorem", "CAP定理（Consistency, Availability, Partition tolerance）— 分散システムはこの3つを同時には満たせないという定理", "名詞", "The CAP theorem explains why we had to choose availability over strict consistency here.", DOMAIN, "900"),
    ("IaaS", "IaaS（Infrastructure as a Service）— サーバーやネットワークなどのインフラをクラウドで提供する形態", "名詞", "We rent virtual machines from an IaaS provider instead of running our own servers.", DOMAIN, "800"),
    ("PaaS", "PaaS（Platform as a Service）— アプリの実行環境をクラウドで提供する形態", "名詞", "The PaaS handles scaling and patching, so we can focus on writing code.", DOMAIN, "800"),
    ("SaaS", "SaaS（Software as a Service）— ソフトウェアをインターネット経由で提供する形態", "名詞", "Most of the tools our team uses are SaaS products billed monthly per user.", DOMAIN, "750"),
    ("IDE", "IDE（Integrated Development Environment）— コード編集・実行・デバッグを一体化した開発環境", "名詞", "This IDE highlights syntax errors as soon as you type them.", DOMAIN, "700"),
    ("CLI", "CLI（Command Line Interface）— コマンドを入力して操作するインターフェース", "名詞", "You can manage the whole deployment from the CLI without touching the web console.", DOMAIN, "700"),
    ("GUI", "GUI（Graphical User Interface）— アイコンやウィンドウなど視覚的な要素で操作するインターフェース", "名詞", "Some engineers prefer the CLI, while others rely on the GUI.", DOMAIN, "700"),
    ("LTS", "LTS（Long-Term Support）— 長期間セキュリティ更新などのサポートが提供されるバージョン", "名詞", "We always deploy on the LTS version to avoid unexpected breaking changes.", DOMAIN, "800"),
    ("UAT", "UAT（User Acceptance Testing）— 実際の利用者が要件を満たしているか確認する最終テスト段階", "名詞", "The client is running UAT this week before we can release to production.", DOMAIN, "850"),
    ("RPC", "RPC（Remote Procedure Call）— ネットワーク越しに別のプロセスの関数を呼び出す仕組み", "名詞", "The two services communicate over RPC instead of a REST API.", DOMAIN, "800"),
    ("gRPC", "gRPC（Googleが開発したRPCフレームワーク）— Protocol Buffersを使った高速な通信フレームワーク", "名詞", "We switched from REST to gRPC to cut down on latency between internal services.", DOMAIN, "850"),
    ("SDLC", "SDLC（Software Development Life Cycle）— 要件定義から保守までのソフトウェア開発全体の工程", "名詞", "Testing is just one phase of the overall SDLC.", DOMAIN, "850"),
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
