# study.nyangailab.com デプロイ手順（準備済・実行は後日）

> **作業機のプラットフォーム別ファイル（2026-08-21〜）**
> 作業機が macOS と Windows の2系統になったため、実行系スクリプトを分離した。
> 自分の環境に対応する方を使うこと。**片方を変更したら必ずもう片方も揃える。**
>
> | | macOS/Linux | Windows |
> |---|---|---|
> | コード同期 | `deploy/macos/sync_code.sh` | `deploy/windows/sync_code.ps1` |
> | 接続設定テンプレ | `deploy/macos/deploy_target.example.sh` | `deploy/windows/deploy_target.example.ps1` |
> | 実値の置き場所（gitignore） | `docs/deploy_target.local.sh` | `docs/deploy_target.local.ps1` |
>
> `deploy/` 直下の `docker-compose.study.yml` / `Caddyfile.study.snippet` /
> `.env.study.example` / 本ファイルは**両環境共通**。
>
> Windows版は rsync が標準に無いため **WSL(Ubuntu) の rsync を呼ぶラッパー**。
> また CLAUDE.md の「`--delete` は必ず dry-run で確認してから」を構造的に
> 強制するため、**既定が dry-run**（実行は `-Execute` を明示）。Mac版は従来
> どおり即実行なので挙動が異なる点に注意。

> 2026-06-16 作成。**ailab(n8n) に一切影響を与えない**ことを最優先にした手順。
> 原則: **既存物は触らず「追加」だけ**／**ポート非公開**／**Caddyは reload(無瞬断)**。
> DNS は設定済（`study → A → <VPS_IP>`）。実行はユーザー合図後。

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

**macOS/Linux 作業機**
```bash
# ローカルPCで実行（VPSのホストパスへ rsync）
rsync -avz --progress \
  <REPO_ROOT>/data/ \
  USER@<VPS_IP>:/home/USER/eigo/data/
# 含まれるもの: vocabulary.db（移行済・詳細キャッシュ込）, audio/（mp3 27,660）
# 除外してよいもの: *.pre-multiuser.*.db バックアップ, build_*.out ログ
```

**Windows 作業機**（rsync が無いので WSL の rsync を使う。`\` は `/mnt/c/...` に変換）
```powershell
wsl -d Ubuntu -- rsync -avz --progress `
  "$(wsl wslpath -a "$PWD\data")/" `
  "USER@<VPS_IP>:/home/USER/eigo/data/"
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

## 11. 再起動を減らす運用 / 予約デプロイ（2026-08-22〜）

**再起動が要らない更新**（DBやdata/だけを変えるもの）は、いつやってもよい:
- 単語・フレーズ・訳・詳細の修正（保守スクリプトを `docker cp` → `docker exec`）
- メンテナンス予定の変更（管理画面から。`app_state` に入るだけ）
- リリースノートの差し替え（`data/release_notes.json` を `docker cp` するだけ。
  置けばリポジトリ同梱版より優先される）

**再起動が要る更新**（`app/`・`static/`・`templates/`・`.env.study`）は、
定期メンテナンス枠（既定: **毎週月曜 03:00〜03:30 JST**）にまとめる。
`deploy/scheduled_deploy.sh` を使うと予告した時刻に自動で反映できる。

```bash
# 1) VPS に置く（sync_code.* は deploy/ を同期しないので個別に転送する）
scp deploy/scheduled_deploy.sh <VPS>:~/eigo/deploy/scheduled_deploy.sh
ssh <VPS> 'chmod +x ~/eigo/deploy/scheduled_deploy.sh'

# 2) cron に登録（VPS上で crontab -e）
#    */5 * * * * /home/<user>/eigo/deploy/scheduled_deploy.sh #       >> /home/<user>/eigo/data/scheduled_deploy_cron.log 2>&1

# 3) 作業機で先にコードを同期しておく（このスクリプトはコードを取りに行かない）
.\deploy\windows\sync_code.ps1            # dry-run
.\deploy\windows\sync_code.ps1 -Execute

# 4) 予約を入れる（管理画面「バージョン情報」→ メンテナンス予定 →
#    臨時メンテナンス →「この時刻に自動デプロイする」でも可）
ssh <VPS> 'echo "{\"run_at\":\"2026-08-25 03:00\",\"note\":\"ver1.2.10\"}"   > ~/eigo/data/deploy_request.json'
```

スクリプトの動き: DBバックアップ → 現行イメージを `eigo-app:prev` に退避 →
`up -d --build` → ヘルスチェック（最大60秒）→ **失敗したら自動で
`eigo-app:prev` に戻して起動し直す**。結果は `data/deploy_log.jsonl` に
追記され、管理画面のメンテナンス欄にも「前回の実行」として表示される。

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
- [ ] `deploy/scheduled_deploy.sh` を配置 + cron 登録（予約デプロイを使う場合）
