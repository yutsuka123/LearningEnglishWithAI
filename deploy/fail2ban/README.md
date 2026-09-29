# eigo 用 fail2ban(2026-09-26作成・2026-09-29改訂)

study.nyangailab.com へのスキャン・総当たり・過剰アクセスを、Caddy のアクセスログ(JSON)から検知して遮断する。
**誤って正規ユーザーを止めないこと**を最優先に設計してあり、最初は「BAN しない(dryrun)」で運用して判定内容を確認する。
実IP・ホスト名・鍵パスはここに書かない(VPS 上で実行時に取得する)。

**2026-09-29 オーナー方針変更**: 「明確に悪意があるとわかるもの」だけ実際に BAN し、それ以外は検知だけしてアプリの
管理画面(ログ→アクセス制限)で「候補」として様子見する方式に変更。`install.sh ban` を実行しても、
eigo-loginflood/eigo-loginfail は**常に dryrun のまま**(install.sh の引数に関わらず)で、実際の遮断は行わない。
どちらのモードでも、判定のたびにアプリへ通知が届き(`FAIL2BAN_NOTIFY_TOKEN`で認証)、管理画面の一覧に出る。
実際に遮断された行(eigo-probe/eigo-ratelimited)は、管理画面の「今すぐ解除」ボタンからも解除できる(ホスト側の
cron `eigo-f2b-unban-poller` が1分以内に反映)。

## しくみ
| jail | 検知するもの | しきい値 | BAN 時間 | 信頼IPの免除 | 実際に遮断するか |
|---|---|---|---|---|---|
| eigo-probe | 存在しないはずの URL(`/wp-login.php`・`/.env`・`/.git/`・phpMyAdmin 等)を叩く(status 307/4xx・クエリ文字列は見ない) | 10分に3回 | 12時間 | **しない**(許可リストのみ) | `install.sh` の引数どおり(ban 指定で実遮断) |
| eigo-loginflood | `/login` への短時間の大量 GET | 5分に60回 | 3時間 | する | **常にしない**(候補のみ・2026-09-29〜) |
| eigo-loginfail | ログイン失敗(401/403)の連続 | 10分に12回 | 1時間 | する | **常にしない**(候補のみ・2026-09-29〜) |
| eigo-ratelimited | アプリのレート制限(429)に当たり続ける(`/api/words`・`/api/phrases` の429は数えない) | 10分に60回 | 1時間 | する | `install.sh` の引数どおり(ban 指定で実遮断) |

**採用しなかったもの**: 404 の連発(404 の 95% は `/favicon.ico` で、正規ユーザーも踏むため)・全リクエスト数(ページ表示だけで1分に数十件になり、実ユーザーと区別できない)。

## 誤 BAN を防ぐ仕組み
1. **dryrun 運用**: 最初は BAN せず、「BAN したはず」の判定とその根拠(時刻・メソッド・URI・status・UA)だけを `/var/log/eigo-f2b-audit.log` に残す。
2. **信頼 IP**: 「**アカウント作成から2日以上経ったユーザー**が直近30日にログインに成功した IP」は無視する(アプリの DB を読み取り専用で参照・10分ごとに更新・`/var/lib/eigo-f2b/trusted.txt`・root専用)。
   誰でもその場で登録してログインできるため、単に「ログイン成功」を条件にすると、スキャナーが登録→ログインの2リクエストで免除になれてしまう
   (敵対的レビュー指摘)。アカウント年齢を条件に加えて塞いだ。**それでも「登録して2日待つ」攻撃者は通る**(既知の限界)ので、
   探索(eigo-probe)だけは信頼IPでも免除しない。DBが読めないときは前回の一覧を残し、失敗を監査ログに記録する。
3. **許可リスト** `/etc/fail2ban/eigo-allowlist.txt`: 運営者が手で書く IP/CIDR は全 jail で無視する(自宅・職場・監視サービス等)。
4. **検索・広告・SNS のクローラー**(Googlebot・AdsBot・bingbot 等)は UA を名乗る限りカウントしない(広告の審査・検索流入を損なわないため)。
5. ローカル・Docker・プライベート帯は無視する。判定スクリプト内の失敗(ファイルが読めない等)は「BAN しない」側に倒す
   (ただし python3 が無い等でスクリプト自体が起動できない場合、fail2ban は「無視しない」扱いになる。install.sh が python3 と実行権限を保証する)。
6. **事前検証**: `tools/simulate.py` で 2026-06〜09 の実ログ(約12万件)に同じしきい値を当て、**信頼 IP で守られずに BAN された実ユーザーは0件**だった。
   ただし本番の信頼IPは「アカウント2日以上」とやや狭いので、この再現は保護の上限側(実ユーザーが引っかかる頻度の目安として読むこと)。
   信頼 IP の除外が無い場合は `/login` 連続で実ユーザー11 IP、429 で1 IP を誤 BAN していた=この除外が必須。
7. ローカルで fail2ban 本体を起動し、疑似ログで「スキャナーは判定・信頼 IP は(probe以外)無視・クローラーはカウントされず・通常ユーザーと
   しきい値未満は無反応・許可リストは免除」を確認済み。

## 既知の限界(誤BAN・効果の両面)
- **共有 IP(学校・職場・携帯回線)**: 多人数が1つの IP を共有する環境で、ログイン実績の無い正規の訪問者が同時に多数アクセスすると、loginflood
  (5分に60回)などに達する可能性がある(実ログでは0件。広告で「教室で使う」流入が増えたら見直す)。
- **BAN は同じ Caddy 配下の他サイトにも及ぶ**: Caddy は Docker の公開ポート(80/443)で動いているため `DOCKER-USER` チェーンで遮断する。
  同じ VPS の他サイト(同じ Caddy 配下のプロジェクト)にも、その IP からのアクセスは届かなくなる(80/443 のみ・他のポートには影響しない)。
  **実 BAN に切り替える前に、相乗り先の運営者へこの影響範囲を共有すること。**
- **`install.sh`は最後に`systemctl restart fail2ban`でサービス全体を再起動する**(2026-09-29判明: `fail2ban-client reload`だと
  jailのアクション一覧に新しいアクションが増える変更を反映しないサイレントな不具合があったため)。設定テスト(`fail2ban-client -t`)を
  先に通すので壊れる可能性は低いが、他プロジェクトの jail(sshd 等)も含めて数秒間 fail2ban が止まる(監視が止まるだけで、
  保護対象のサービス自体には影響しない)。他プロジェクトの jail 設定に問題があれば導入が止まる(それ自体は安全側)。
  再起動のたびに、その時点でBAN中だった全IPのunban→ban記録がアプリへ再送されるため、管理画面には同じIPの行が
  複数回出ることがある(55秒以内の重複は自動で除外される)。
- **Caddy の JSON ログの形式(キー順)に依存**する。Caddy の更新で形式が変わると、無音で検知が0になる。`install.sh` の「実ログに何行マッチするか」と
  `review.sh` で件数を確認すること。
- **IPv6** は実ログで 0 件のため未対応(必要になったら nftables 系のアクションを検討)。
- **fail2ban が Docker より先に起動すると `DOCKER-USER` が無く BAN アクションの起動に失敗しうる**(推測)。実 BAN に切り替えるときは
  systemd の drop-in(`After=docker.service`)を入れることを推奨する(この導入スクリプトは systemd の設定は変更しない)。
  **2026-09-29に本番へ導入済み**: `/etc/systemd/system/fail2ban.service.d/after-docker.conf`(`[Unit]` に
  `After=docker.service` と `Wants=docker.service`)+ `systemctl daemon-reload`(fail2ban自体は再起動していない)。
  VPSを作り直す・別のVPSに入れる場合は同じ drop-in を入れること(`install.sh` は入れない)。

## 導入・運用(VPS 上で root)
`deploy/` は通常の同期(`sync_code.sh`)の対象外なので、手元から手動で転送する(追加のみ・`--delete` なし):
```
rsync -a deploy/fail2ban/ eigo-vps:/tmp/eigo-f2b-src/
ssh eigo-vps 'sudo bash /tmp/eigo-f2b-src/install.sh dryrun'   # dryrun で導入(既定)。何度実行しても安全
ssh eigo-vps 'rm -rf /tmp/eigo-f2b-src'                        # 転送した一時ファイルの削除
```
```
sudo bash install.sh            # dryrun で導入。設定テスト・途中の失敗時は自動で eigo の jail を外して中止する
sudo bash review.sh             # 判定の確認(IP は短縮ハッシュ表示)。--raw で生IP
sudo bash install.sh ban        # 実 BAN に切替(下の手順で確認してから)。自己テスト付き
sudo bash uninstall.sh          # jail を外す(BAN 中の IP は全て解除)。--purge で配置ファイルも削除
```
- **個別解除**: `sudo fail2ban-client set <jail> unbanip <ip>` / 恒久的に除外するなら許可リストへ追記(再起動不要)。
- **緊急停止**: `sudo bash uninstall.sh`(jail を外して reload=即時に全解除)。
- **実BANへの切替の手順(eigo-probe/eigo-ratelimitedのみ・2026-09-29〜)**: dryrun を 3〜7 日運用し、`review.sh` で(a)判定された IP が全てスキャナー/攻撃らしいこと(b)運営者・テスト・広告の審査元が
  混ざっていないこと(c)件数が想定内(実ログ換算で 1日あたり数件〜十数件)(d)「最後の信頼IP更新」が新しいことを確認する。
  切替後は、**自分の携帯回線(Wi-Fi を切った状態)で1回だけ実際に遮断される**ことを確認する:
  `sudo fail2ban-client set eigo-probe banip <その回線の現在のIP>` → 携帯からサイトが開けないこと → `unbanip` で解除。
  eigo-loginflood/eigo-loginfail はこの手順の対象外(2026-09-29オーナー方針で常にdryrunに固定済み)。
- **通知トークンの設定**: `FAIL2BAN_NOTIFY_TOKEN`(アプリの`.env.study`に`openssl rand -hex 32`等で追記→**コンテナを
  再作成**(`docker restart`では反映されない)→`install.sh`実行)。未設定でもfail2ban自体は今まで通り動く
  (アプリへの通知だけが無効になり、`/var/log/eigo-f2b-audit.log`への記録は変わらず続く)。
- ログ: `/var/log/eigo-f2b-audit.log`(判定と根拠・8世代)/`/var/log/fail2ban.log`(fail2ban 本体の Found/Ban/Ignore)。
  監査ログに Cookie・クエリ文字列(gclid 等)は出さない(パスとUA60字のみ)。
