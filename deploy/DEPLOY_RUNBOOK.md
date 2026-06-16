# study.nyangailab.com デプロイ手順（準備済・実行は後日）

> 2026-06-16 作成。**ailab(n8n) に一切影響を与えない**ことを最優先にした手順。
> 原則: **既存物は触らず「追加」だけ**／**ポート非公開**／**Caddyは reload(無瞬断)**。
> DNS は設定済（`study → A → 153.121.51.195`）。実行はユーザー合図後。

## 0. 安全設計の要点（なぜ ailab に影響しないか）
- 別 compose ファイル(`docker-compose.study.yml`)で**独立コンテナ** `eigo-app` を
  追加するだけ。AIpoc の compose・n8n・postgres は**編集も再起動もしない**。
- eigo-app は**ホストにポートを公開しない**（Caddy 経由のみ＝直アクセス不可）。
- Caddy は**新規 vhost ブロックを追記**して **reload**（再起動でなく graceful）。
  ailab のブロックは不変＝ailab は無瞬断で動き続ける。
- `mem_limit: 512m` で 2GB VPS のメモリを n8n から奪わない。
- DB は SQLite（postgres と無関係）＝ロック競合なし。
- ロールバックは `down` ＋ Caddy ブロック削除 ＋ reload で完全復帰（ailab無関係）。

## 1. 事前確認（VPS 上・読み取りのみ・無影響）★AIpoc共有の確認項目
```bash
sudo ss -tlnp                  # ★使用中ポート確認。5678=n8n。8001 等の空きを選ぶ
docker ps                      # aipoc-n8n / aipoc-postgres / owners-app 等を確認
systemctl status caddy         # Caddy がホスト常駐か（/etc/caddy/Caddyfile 前提）
docker ps | grep -i caddy      # ↑でなければ Caddy が Docker か確認
sudo ls -l /etc/caddy/Caddyfile  # ★Caddy 設定の場所と既存ブロック書式を確認
df -h ; free -m                # ★ディスク/メモリ余裕（音声 ~0.8GB + 512m + swap）
```
→ 確認結果に合わせて修正:
- `docker-compose.study.yml` の公開ポート `127.0.0.1:8001`（空きポートに）と
  `volumes` のホストパス（`/home/USER/eigo/data`）。
- `Caddyfile.study.snippet` の `reverse_proxy 127.0.0.1:8001` をポートに一致。

> AIpoc 非干渉の厳守事項: aipoc-n8n / aipoc-postgres / owners-app / n8n暗号鍵 /
> _secrets/ / ailab.nyangailab.com / /aipoc/ 配下 / Caddyfile の AIpoc ブロックは
> **読み取りすらせず触らない**。新規 inbound ポートは開けない（127.0.0.1 のみ＝
> FW変更不要）。万一 FW 変更が要る事態なら **事前に AIpoc 側へ連絡**。

## 2. コード配置
```bash
# 本リポジトリを VPS に clone（または rsync）。docs/ data/ は gitignore のため
# 別途転送（下記3）。コードのみで可。
git clone <repo> ~/eigo-app   # もしくは rsync -a（.git/.venv/data/docs 除外）
```

## 3. データ転送（ローカル → VPS）★最重要
ローカルの `data/`（vocabulary.db ＋ audio 約0.8GB）を VPS の bind 先へ。
```bash
# ローカルPCで実行（VPSのホストパスへ rsync）
rsync -avz --progress \
  /Users/ytsuka/mydata/src/LearningEnglishWithAI/data/ \
  USER@153.121.51.195:/home/USER/eigo/data/
# 含まれるもの: vocabulary.db（移行済・詳細キャッシュ込）, audio/（mp3 27,660）
# 除外してよいもの: *.pre-multiuser.*.db バックアップ, build_*.out ログ
```

## 4. env 準備（秘密はVPSのみ）
```bash
cp deploy/.env.study.example deploy/.env.study   # VPS上で
# 編集して値を設定:
#   OPENAI_API_KEY=...    MULTIUSER=1   COOKIE_SECURE=1
#   SESSION_SECRET=$(python -c "import secrets;print(secrets.token_hex(32))")
#   RATE_LIMIT_PER_MIN=300   AI_DAILY_COST_CAP_USD=35.5
chmod 600 deploy/.env.study
```

## 5. 起動（ailab 無関係）
```bash
cd ~/eigo-app/deploy
docker compose -f docker-compose.study.yml up -d --build
docker compose -f docker-compose.study.yml ps        # healthy 確認
docker compose -f docker-compose.study.yml logs -f    # 起動ログ
# 内部疎通（ホスト公開していないのでコンテナ内/網内から）
docker exec eigo-app python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/api/health').read())"
```

## 6. Caddy に study を追加（追記＋reload・ailab不変）
```bash
# 既存 /etc/caddy/Caddyfile に Caddyfile.study.snippet の study ブロックを「追記」。
#   ※ ailab / /aipoc/ のブロックは絶対に編集しない。新規ブロックを足すだけ。
sudo nano /etc/caddy/Caddyfile      # 末尾に study ブロックを貼り付け
# 検証 → graceful reload（無瞬断・ailab無影響）。ホスト常駐 Caddy の場合:
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy         # または: sudo caddy reload --config /etc/caddy/Caddyfile
#   Caddy が Docker コンテナの場合: docker exec <caddy> caddy reload --config /etc/caddy/Caddyfile
```
→ Caddy が study.nyangailab.com の Let's Encrypt 証明書を自動取得。
   reload 後、ailab.nyangailab.com が従来どおり応答することを必ず確認（手順8）。

## 7. 管理者・ユーザー作成（MULTIUSER=1 ＝ ログイン必須）
```bash
docker exec -it eigo-app python scripts/admin.py list
docker exec -it eigo-app python scripts/admin.py create <admin名> \
  --password '<強いパス>' --role admin
docker exec -it eigo-app python scripts/admin.py create <知人> \
  --password '<パス>' --daily 5 --monthly 50 --balance 500
```

## 8. 公開後の動作確認
- ブラウザで `https://study.nyangailab.com/` → /login にリダイレクト → ログイン。
- `https://ailab.nyangailab.com/` が**従来どおり**動くことを必ず確認（無影響検証）。
- 学習・音声再生・会話を一通り。💰コスト/残高表示。
- 3回連続ログイン失敗→5分ロック（429）を確認。

## 9. ロールバック（完全復帰・ailab無関係）
```bash
docker compose -f docker-compose.study.yml down       # eigo-app 撤去
# Caddyfile から study ブロックを削除 → caddy reload
docker exec <caddy_container> caddy reload --config /etc/caddy/Caddyfile
# data/ はホストに残る（再開時そのまま使える）
```

## 10. 運用（堅牢性）
- バックアップ: `data/vocabulary.db` を定期的にVPS外へ（cron + rsync/scp）。音声は再生成可。
- 監視: `docker stats eigo-app`（メモリ）/ `df -h`（ディスク）/ ヘルスチェック。
- 自動再起動: `restart: unless-stopped`＋healthcheck で異常時も復帰。
- 更新: コード更新は `up -d --build`、Caddy/n8n は無関係。
- セキュリティ詳細は docs/DEPLOY_COHOST.md §7。

## チェックリスト
- [ ] VPS で網名・Caddy 構成・空き容量を確認（手順1）
- [ ] compose の network 名 / data ホストパスを実環境に修正
- [ ] data/ を rsync（DB＋音声）
- [ ] .env.study 設定（SESSION_SECRET 必須・OPENAI_API_KEY・MULTIUSER=1）
- [ ] eigo-app 起動・healthy 確認
- [ ] Caddy に study ブロック追記 → reload（ailab 不変を確認）
- [ ] 管理者/ユーザー作成
- [ ] study 動作確認 ＋ **ailab 無影響を確認**
- [ ] バックアップ cron 設定
