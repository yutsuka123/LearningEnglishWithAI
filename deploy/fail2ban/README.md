# eigo 用 fail2ban(2026-09-26)

study.nyangailab.com へのスキャン・総当たり・過剰アクセスを、Caddy のアクセスログ(JSON)から検知して遮断する。
**誤って正規ユーザーを止めないこと**を最優先に設計してあり、最初は「BAN しない(dryrun)」で運用して判定内容を確認する。
実IP・ホスト名・鍵パスはここに書かない(VPS 上で実行時に取得する)。

## しくみ
| jail | 検知するもの | しきい値 | BAN 時間 |
|---|---|---|---|
| eigo-probe | 存在しないはずの URL(`/wp-login.php`・`/.env`・`/.git/`・phpMyAdmin 等)を叩く | 10分に3回 | 12時間 |
| eigo-loginflood | `/login` への短時間の大量 GET | 5分に40回 | 6時間 |
| eigo-loginfail | ログイン失敗(401/403)の連続 | 10分に12回 | 1時間 |
| eigo-ratelimited | アプリのレート制限(429)に当たり続ける | 10分に60回 | 1時間 |

**採用しなかったもの**: 404 の連発(404 の 95% は `/favicon.ico` で、正規ユーザーも踏むため)・全リクエスト数(ページ表示だけで1分に数十件になり、実ユーザーと区別できない)。

## 誤 BAN を防ぐ仕組み
1. **dryrun 運用**: 最初は BAN せず、「BAN したはず」の判定とその根拠(時刻・メソッド・URI・status・UA)だけを `/var/log/eigo-f2b-audit.log` に残す。
2. **信頼 IP**: 直近30日に**ログイン成功**した IP は無視する(`eigo-f2b-trusted-refresh` が10分ごとに更新・登録成功は含めない=スキャナーが登録して抜け道にするのを防ぐ)。
3. **許可リスト** `/etc/fail2ban/eigo-allowlist.txt`: 運営者が手で書く IP/CIDR は無視する(自宅・職場・監視サービス等)。
4. **検索・広告・SNS のクローラー**(Googlebot・AdsBot・bingbot 等)は UA を名乗る限りカウントしない(広告の審査・検索流入を損なわないため)。
5. ローカル・Docker・プライベート帯は無視する。判定に失敗した場合は「BAN しない」側に倒す。
6. **事前検証**: `tools/simulate.py` で 2026-06〜09 の実ログ(約12万件)に同じしきい値を当て、**信頼 IP で守られずに BAN された実ユーザーは0件**だった。信頼 IP の除外が無い場合は `/login` 連続で実ユーザー11 IP、429 で1 IP を誤 BAN していた=この除外が必須。
7. ローカルで fail2ban 本体を起動し、疑似ログで「スキャナーは判定・信頼 IP は無視・クローラーはカウントされず・通常ユーザーは無反応」を確認済み。

## 導入・運用(VPS 上で root)
```
sudo bash install.sh            # dryrun で導入(既定)。何度実行しても安全。設定テストに失敗したら jail を外して中止する
sudo bash review.sh             # 判定の確認(IP は短縮ハッシュ表示)。--raw で生IP
sudo bash install.sh ban        # 実 BAN に切替(dryrun で数日見て、誤判定が無いと確認してから)。自己テスト付き
sudo bash uninstall.sh          # jail を外す(BAN 中の IP は全て解除)。--purge で配置ファイルも削除
```
- **BAN の効く場所**: Caddy は Docker の公開ポート(80/443)で動いているため、通常の `INPUT` ではなく `DOCKER-USER` チェーンで遮断する。
  同じ VPS の他サイト(同じ Caddy 配下)にも、その IP からのアクセスは届かなくなる(80/443 のみ・他のポートには影響しない)。
- **個別解除**: `sudo fail2ban-client set <jail> unbanip <ip>` / 恒久的に除外するなら許可リストへ追記(再起動不要)。
- **緊急停止**: `sudo bash uninstall.sh`(jail を外して reload=即時に全解除)。
- **IPv6**: 実ログで 0 件のため未対応(必要になったら nftables 系のアクションを検討)。
- **実BANへの切替の目安**: dryrun を 3〜7 日運用し、`review.sh` で(a)判定された IP が全てスキャナー/攻撃らしいこと(b)運営者・テスト・広告の審査元が混ざっていないこと(c)件数が想定内(実ログ換算で 1日あたり数件〜十数件)を確認する。
- ログ: `/var/log/eigo-f2b-audit.log`(判定と根拠・8世代)/`/var/log/fail2ban.log`(fail2ban 本体の Found/Ban/Ignore)。
