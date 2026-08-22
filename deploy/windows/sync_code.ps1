# 本番VPS(study.nyangailab.com)へアプリのコードだけを同期する。【Windows用】
#
# macOS/Linux 版 deploy/macos/sync_code.sh の Windows 移植。
# 同期対象(allowlist)・--delete の挙動・deploy/ を対象外にする安全設計は
# Mac版と完全に同一。両者を変更するときは必ず両方を揃えること。
#
# 2026-08-13: リポジトリ全体を rsync --delete で丸ごとミラーしていたため、
# ローカルに存在しない(=gitignore対象で意図的にVPSにしか無い)
# deploy/.env.study が「余分なファイル」として削除される事故が起きた。
# 再発防止のため、同期対象を明示的に列挙する(allowlist)方式にしてある。
# deploy/ ディレクトリ自体を同期対象に含めないので、deploy/.env.study
# には構造的に触れられない。
#
# 【Windows固有の事情】
# Windowsには rsync が無く、Git Bash にも同梱されていない。そのため
# WSL(Ubuntu)の rsync を呼び出すラッパー方式にしている。scp/tar では
# --delete 相当の差分削除ができず、Mac版と挙動が変わってしまうため。
#
# 前提条件:
#   - WSL に Ubuntu ディストリが入っており、rsync と ssh が使えること
#     （未導入なら: wsl -d Ubuntu -- sudo apt-get install -y rsync）
#   - 秘密鍵が LF 改行であること（CRLFだと OpenSSH が invalid format で拒否）
#     ※本スクリプトが WSL へ複製する際に自動で LF 化するので、Windows 側の
#       鍵が CRLF でも動く。
#
# 使い方:
#   1. deploy\windows\deploy_target.example.ps1 を docs\deploy_target.local.ps1
#      にコピーして実値を埋める（docs\ は .gitignore 対象＝コミットされない）。
#   2. .\deploy\windows\sync_code.ps1            # ← 既定は dry-run（確認のみ）
#   3. .\deploy\windows\sync_code.ps1 -Execute   # ← 実際に同期
#
#   CLAUDE.md の「rsync --delete は必ず dry-run で削除対象を確認してから」
#   というルールを構造的に強制するため、既定を dry-run にしてある
#   （Mac版は従来どおり即実行なので、挙動の違いに注意）。
#
# deploy\docker-compose.study.yml や Caddyfile.study.snippet 等 deploy 配下の
# 設定ファイルを更新したい場合は、このスクリプトでは同期せず個別に1ファイル
# ずつ転送すること（--delete はディレクトリ丸ごとには絶対に使わない）。

[CmdletBinding()]
param(
    # 指定すると実際に同期する。未指定なら --dry-run で削除/転送対象の確認のみ。
    [switch]$Execute,
    # 使用する WSL ディストリ名。
    [string]$WslDistro = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'

# wsl.exe は引数中のバックスラッシュを食ってしまう（"C:" + 円記号 + "dir" が
# "C:dir" になる）。
# そのため Windows パスの変換に wslpath を使わず PowerShell 側で行い、
# WSL に渡すコマンド文字列にもバックスラッシュを一切含めない。
# （`tr -d '\r'` のような指定は `tr -d 'r'` に化けて大惨事になる）
function ConvertTo-WslPath([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    if ($full -notmatch '^[A-Za-z]:') { throw "ドライブレターから始まるパスが必要です: $Path" }
    $drive = $full.Substring(0, 1).ToLower()
    return '/mnt/' + $drive + ($full.Substring(2) -replace '\\', '/')
}

function Invoke-Wsl([string]$Command) {
    if ($Command -match '\\') { throw "内部エラー: WSLへ渡すコマンドにバックスラッシュが含まれています" }
    & wsl -d $WslDistro -- bash -lc $Command
}

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot   = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$TargetConf = Join-Path $RepoRoot 'docs\deploy_target.local.ps1'

if (-not (Test-Path $TargetConf)) {
    Write-Error @"
$TargetConf が見つかりません。
deploy\windows\deploy_target.example.ps1 を参考に作成してください。
"@
}
. $TargetConf

foreach ($v in 'VPS_SSH_KEY', 'VPS_HOST', 'VPS_APP_DIR') {
    if (-not (Get-Variable -Name $v -ValueOnly -ErrorAction SilentlyContinue)) {
        Write-Error "$v が未設定です（docs\deploy_target.local.ps1 を確認）"
    }
}

# --- WSL の前提確認 -------------------------------------------------------
Invoke-Wsl 'command -v rsync >/dev/null' | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "WSL($WslDistro) に rsync がありません。`n  wsl -d $WslDistro -- sudo apt-get install -y rsync"
}

# --- 秘密鍵を WSL 側へ配置（LF化 + chmod 600） ----------------------------
# /mnt/c 上のファイルはパーミッションが緩く ssh が
# 「UNPROTECTED PRIVATE KEY FILE」で拒否するため、WSLのホームに複製する。
# CR の除去は（バックスラッシュを避けるため）PowerShell 側で行う。
if (-not (Test-Path $VPS_SSH_KEY)) { Write-Error "秘密鍵が見つかりません: $VPS_SSH_KEY" }
$KeyName = Split-Path $VPS_SSH_KEY -Leaf
$keyText = [System.Text.Encoding]::ASCII.GetString(
    [System.IO.File]::ReadAllBytes($VPS_SSH_KEY)) -replace "`r`n", "`n"
if (-not $keyText.EndsWith("`n")) { $keyText += "`n" }

$TmpKey = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
[System.IO.File]::WriteAllBytes($TmpKey, [System.Text.Encoding]::ASCII.GetBytes($keyText))
try {
    $tmpWsl = ConvertTo-WslPath $TmpKey
    $WslKey = "`$HOME/.ssh/$KeyName"
    Invoke-Wsl "set -e; mkdir -p ~/.ssh; chmod 700 ~/.ssh; cp '$tmpWsl' $WslKey; chmod 600 $WslKey; ssh-keygen -y -f $WslKey >/dev/null"
    if ($LASTEXITCODE -ne 0) { Write-Error 'WSL側への鍵の配置に失敗しました（鍵の形式を確認してください）' }
} finally {
    Remove-Item -LiteralPath $TmpKey -Force -ErrorAction SilentlyContinue
}

# --- 同期対象は明示的に列挙(allowlist) ------------------------------------
# deploy/・docs/・data/・.env 等は意図的に対象外（deploy/.env.study を守るため。
# Dockerfile が実際に COPY している範囲に合わせてある）。
$SyncItems = @('app', 'static', 'templates', 'scripts', 'run.py',
               'requirements.txt', 'Dockerfile', 'CHANGELOG.md',
               'release_notes.json')

$DryRunFlag = if ($Execute) { '' } else { '--dry-run ' }
if (-not $Execute) {
    Write-Host '*** DRY-RUN モード（実際には転送・削除しません） ***' -ForegroundColor Yellow
    Write-Host '    実行するには -Execute を付けてください。' -ForegroundColor Yellow
    Write-Host ''
}
Write-Host "同期先: ${VPS_HOST}:${VPS_APP_DIR}/"

foreach ($item in $SyncItems) {
    $local = Join-Path $RepoRoot $item
    if (-not (Test-Path $local)) {
        Write-Warning "$item が見つからないためスキップします"
        continue
    }
    Write-Host "→ 同期中: $item"
    $localWsl = ConvertTo-WslPath $local
    # 末尾スラッシュを付けない＝ディレクトリ自体を転送先に置く（Mac版と同一）
    $rsync = "rsync -avz --delete ${DryRunFlag}" +
             "--exclude=__pycache__/ --exclude=*.pyc " +
             "-e ""ssh -i $WslKey -o StrictHostKeyChecking=accept-new"" " +
             "'$localWsl' '${VPS_HOST}:${VPS_APP_DIR}/'"
    Invoke-Wsl $rsync
    if ($LASTEXITCODE -ne 0) { Write-Error "$item の同期に失敗しました" }
}

Write-Host ''
if ($Execute) {
    Write-Host 'コード同期完了。反映するには VPS 上で以下を実行してください:'
    Write-Host "  cd $VPS_APP_DIR && docker compose -f deploy/docker-compose.study.yml up -d --build"
} else {
    Write-Host 'dry-run 完了。上の "deleting" 行に想定外のファイルが無いことを確認し、'
    Write-Host '問題なければ -Execute を付けて再実行してください。'
}
