# 本番VPS上のeigo-appコンテナ内でscripts/配下のPythonスクリプトを実行する。
# 【Windows用】macOS/Linux版 deploy/macos/run_script_on_vps.sh のWindows移植。
# コンテンツ反映(add_*.py・import_details.py等)は必ずテーブル単位のSQL
# スクリプト経由で行い、DBファイルそのものを転送しないというルール
# (CLAUDE.md参照)を、実行面から支援するラッパー。
#
# 前提: 事前に .\deploy\windows\sync_code.ps1 -Execute でコード
# (scripts/含む)を同期済みであること。WSL経由でsshを呼ぶ点はsync_code.ps1
# と同じ(前提条件・鍵のLF化handling含め同一)。
#
# 使い方:
#   .\deploy\windows\run_script_on_vps.ps1 scripts/add_latin_etymology_2026_09_14.py
#   .\deploy\windows\run_script_on_vps.ps1 scripts/import_details.py `
#       scripts/add_latin_etymology_2026_09_14_details.json

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs,
    [string]$WslDistro = 'Ubuntu',
    [string]$Container = 'eigo-app'
)

$ErrorActionPreference = 'Stop'

function Invoke-Wsl([string]$Command) {
    if ($Command -match '\\') { throw "内部エラー: WSLへ渡すコマンドにバックスラッシュが含まれています" }
    & wsl -d $WslDistro -- bash -lc $Command
}

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot   = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$TargetConf = Join-Path $RepoRoot 'docs\deploy_target.local.ps1'

if (-not (Test-Path $TargetConf)) {
    Write-Error "$TargetConf が見つかりません。deploy\windows\deploy_target.example.ps1 を参考に作成してください。"
}
. $TargetConf
foreach ($v in 'VPS_SSH_KEY', 'VPS_HOST', 'VPS_APP_DIR') {
    if (-not (Get-Variable -Name $v -ValueOnly -ErrorAction SilentlyContinue)) {
        Write-Error "$v が未設定です（docs\deploy_target.local.ps1 を確認）"
    }
}

if (-not (Test-Path $VPS_SSH_KEY)) { Write-Error "秘密鍵が見つかりません: $VPS_SSH_KEY" }
$KeyName = Split-Path $VPS_SSH_KEY -Leaf
$keyText = [System.Text.Encoding]::ASCII.GetString(
    [System.IO.File]::ReadAllBytes($VPS_SSH_KEY)) -replace "`r`n", "`n"
if (-not $keyText.EndsWith("`n")) { $keyText += "`n" }
$TmpKey = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
[System.IO.File]::WriteAllBytes($TmpKey, [System.Text.Encoding]::ASCII.GetBytes($keyText))
try {
    $tmpWsl = & wsl -d $WslDistro -- wslpath -a ($TmpKey -replace '\\', '/')
    $WslKey = "`$HOME/.ssh/$KeyName"
    Invoke-Wsl "set -e; mkdir -p ~/.ssh; chmod 700 ~/.ssh; cp '$tmpWsl' $WslKey; chmod 600 $WslKey; ssh-keygen -y -f $WslKey >/dev/null"
    if ($LASTEXITCODE -ne 0) { Write-Error 'WSL側への鍵の配置に失敗しました' }
} finally {
    Remove-Item -LiteralPath $TmpKey -Force -ErrorAction SilentlyContinue
}

$remoteCmd = $ScriptArgs -join ' '
Write-Host "実行: docker exec $Container python3 $remoteCmd"
$sshCmd = "ssh -i $WslKey -o StrictHostKeyChecking=accept-new $VPS_HOST " +
          "'cd $VPS_APP_DIR && docker exec -i $Container python3 $remoteCmd'"
Invoke-Wsl $sshCmd
if ($LASTEXITCODE -ne 0) { Write-Error "リモート実行に失敗しました" }
