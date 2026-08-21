# deploy\windows\sync_code.ps1 が読み込む接続設定のテンプレート。【Windows用】
# 実値は docs\deploy_target.local.ps1 にコピーして設定する
# （docs\ は .gitignore 対象なのでコミットされない）。
#
# macOS/Linux 版は deploy/macos/deploy_target.example.sh を使うこと。

# 秘密鍵は Windows 側のパスで指定する（スクリプトが WSL 側へ LF化して複製する）。
# CRLF 改行の鍵は OpenSSH に拒否されるが、スクリプト側で正規化するので
# ここでは改行コードを気にしなくてよい。
$VPS_SSH_KEY = "$env:USERPROFILE\.ssh\<your_ssh_key>"
$VPS_HOST    = "<user>@<VPS_IP>"
$VPS_APP_DIR = "/home/<user>/eigo"
