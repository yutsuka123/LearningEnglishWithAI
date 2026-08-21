# deploy/sync_code.sh が読み込む接続設定のテンプレート。
# 実値は docs/deploy_target.local.sh にコピーして設定する
# （docs/ は .gitignore 対象なのでコミットされない）。
export VPS_SSH_KEY=~/.ssh/<your_ssh_key>
export VPS_HOST=<user>@<VPS_IP>
export VPS_APP_DIR=/home/<user>/eigo
