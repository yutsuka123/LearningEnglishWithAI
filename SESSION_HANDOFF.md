# セッション引継ぎメモ（2026-07-01）

新しいセッション／別ツールでも作業を継続できるように、本日の作業結果と運用の要点をまとめる。

## 本日やったこと（要約）
- **語彙 +255語 / フレーズ +200** を17分野で追加（電気/電子/無線/法律/政治/経済/経営/DIY/
  ロボット/家電/航空/気象/地学/原子力/家事/インターネット）。domain は既存カテゴリに寄せた。
- **detail 生成の改善**：`build_details.py` が `database is locked` を多発 → **1語ごとコミット**で解消。
  プロンプトに **pronunciation(IPA)/example_ja** を追加、**origin(接頭辞/語根分解)・trivia(著名人/
  聖書/哲学/技術/名言/書籍との関連)** を強化。アプリの on-demand 版 `app/routers/vocabulary.py`
  の word_detail プロンプトも同期。
- **TOEIC 50点刻み化**：`vocabulary.py` の `LEVEL_ORDER` に 350/450/…/950 を追加。
  新規語を手動補正後、**全4008語を AI で 50点再レベリング**（`scripts/relevel_all_20260701.py`）。
- **音声**：`build_audio.py --all --native`（ash/nova・通常/native）で新規語見出し＋例文＋新規
  フレーズ＋既存欠落分を生成（本番 audio 30,993 ファイル）。
- **既存 3753 語のリッチ化**：`scripts/enrich_details_20260701.py` で「崩さず」= 意味/例文/派生は
  保持し **origin/trivia のみ差し替え、IPA不足時のみ補完**。
- **本番反映（2回）**：CP1（新規行 import＋音声 rsync＋コード配置＋再ビルド）、CP2（全語 level/detail
  更新）。**本番の users/ai_usage/進捗は毎回保持**。
- **study.nyangailab.com 復旧**：ecopy(WordPress)展開時に共有 Caddyfile から study ブロックが消失
  → 再追記＋`docker restart aipoc-web` で復旧。

## 本番環境（サクラVPS）
- ホスト: `ubuntu@153.121.51.195` / **SSH鍵: `~/.ssh/sakura_vps_ed25519`**（既定名でないので `-i` 必須）
- アプリ: docker コンテナ `eigo-app`、コードは **git管理外・rsync配置** の `/home/ubuntu/eigo`、
  compose は `/home/ubuntu/eigo/deploy/docker-compose.study.yml`（COPYビルド）。
- データ: `/home/ubuntu/eigo/data`（`vocabulary.db` と `audio/`。audioはファイル配信）。
- 逆プロキシ: 共有 Caddy コンテナ `aipoc-web`（AIpoc管理）。設定 `/home/ubuntu/AIpoc/sakura-web/Caddyfile`。
  `admin off` のため reload 不可 → 反映は `docker restart aipoc-web`（ailab/ecopy が数秒瞬断）。

## 反映の鉄則（重要）
- **本番 `vocabulary.db` を丸ごと上書き（rsync）しない。** users/ai_usage/進捗が消える。
- 内容反映は **選択的に**：新規行は id 保持で INSERT、既存更新は該当列（level/detail 等）だけ UPDATE。
- 音声は `rsync -az --ignore-existing data/audio/ …:/home/ubuntu/eigo/data/audio/`（追加のみ）。
- コード更新は `scp` → `docker compose -f docker-compose.study.yml up -d --build`（eigo-app のみ・ailab無影響）。
- Caddy の study ブロックは AIpoc の再展開で再び消える恐れ → 消えたら
  `deploy/Caddyfile.study.snippet` を Caddyfile に再追記して aipoc-web 再起動。AIpoc へは共有連絡済み。

## 主なスクリプト
- `scripts/seed_domains_20260701.py` … 分野別の語彙シード（重複回避）
- `scripts/build_details.py` … detail(IPA/語義/語源/豆知識) 生成（未生成分のみ・再実行安全）
- `scripts/fix_levels_20260701.py` … 新規語の50点level手動補正表
- `scripts/relevel_all_20260701.py` … 全語をAIで50点再レベリング（バッチ）
- `scripts/enrich_details_20260701.py` … 既存detailを崩さずリッチ化（origin/triviaのみ）
- `scripts/build_audio.py` … 音声生成（`--all --native --voices ash,nova`）

## 未了・次の予定
- **追加コンテンツ（要望・あとで）**：(1)気象予報士関連 (2)駅/バス/公共アナウンス
  (3)登山/キャンプ/ハイキング/散歩/海遊び/遊園地。フレーズ追加に伴い支え単語も追加。
  既存カテゴリに寄せ、50点level・IPA/語源/豆知識・音声まで通す。手順は上記スクリプト群を踏襲。
- 既存語 detail は本日リッチ化済み。今後さらに `--force` 相当で磨く場合も同方式。

## 現在の規模
- 単語 4008 / フレーズ 1736 / 音声 30,993 ファイル / level は50点刻み（範囲外=禁止用語90は据置）。
