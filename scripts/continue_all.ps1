# 全圣经章节笔记 · 自动监督器（以赛亚书 -> 旧约全部 -> 新约全部）
#
# 循环：查状态 -> 打开一个新的 opencode 会话继续写 -> 遇限流退避重试
#       -> 直到 status.py 报告全部章节完成。
#
# 本文件刻意只用 ASCII，以免 Windows PowerShell 5.1 读取无 BOM 的 UTF-8 时乱码。
# 中文提示词放在 scripts/prompt_template.txt（UTF-8），由本脚本按 UTF-8 读入。
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts\continue_all.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\continue_all.ps1 -MaxRounds 2000
#   powershell -ExecutionPolicy Bypass -File scripts\continue_all.ps1 -DryRun

param(
  [int]$MaxRounds  = 2000,
  [int]$Batch      = 4,
  [int]$BaseDelay  = 60,
  [int]$MaxDelay   = 900,
  [string]$Scope   = "all",
  [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$cli = "$env:LOCALAPPDATA\Programs\@opencodedesktop\resources\opencode-cli.exe"
$logDir = Join-Path $root "logs"
$log    = Join-Path $logDir "continue_all.log"
$pidF   = Join-Path $logDir "supervisor.pid"
$tplF   = Join-Path $PSScriptRoot "prompt_template.txt"

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

function Log([string]$m) {
  $line = "[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] " + $m
  Add-Content -Path $log -Value $line -Encoding UTF8
  Write-Output $line
}

if (-not (Test-Path $cli)) { Log "opencode-cli.exe not found: $cli"; exit 1 }
if (-not (Test-Path $tplF)) { Log "prompt template not found: $tplF"; exit 1 }

$template = [System.IO.File]::ReadAllText($tplF, [System.Text.Encoding]::UTF8)

if (Test-Path $pidF) {
  $old = (Get-Content $pidF -Raw).Trim()
  if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue)) {
    Log "supervisor already running (pid=$old), exiting."
    exit 0
  }
}
Set-Content -Path $pidF -Value $PID -Encoding ASCII

Log "supervisor started pid=$PID maxRounds=$MaxRounds batch=$Batch scope=$Scope"

$delay = $BaseDelay
$prevTodo = ""

# model rotation: on rate limit, try the next model
$models = @(
  "",
  "opencode/minimax-m3.1-flash-free",
  "opencode/glm-5.3-flash-free",
  "opencode/deepseek-v4.1-flash-free",
  "opencode/mimo-v2.6-flash-free",
  "opencode/beam-free",
  "opencode/longcat-2.5-preview-free"
)
$modelIdx = 0

for ($i = 1; $i -le $MaxRounds; $i++) {
  $out = & py (Join-Path $root "scripts\status.py") --next $Batch --books $Scope 2>&1
  $raw = ($out | Select-Object -Last 1).ToString().Trim()
  $code = $LASTEXITCODE

  if ($code -eq 0 -and $raw -eq "") {
    Log "all chapters complete. supervisor exiting."
    break
  }

  # raw is "id:status id:status ..."; keep raw for progress detection, ids for the prompt
  $todo = ""
  if ($raw -ne "") {
    $ids = @()
    foreach ($tok in ($raw -split '\s+')) { $ids += (($tok -split ':')[0]) }
    $todo = $ids -join ' '
  } else {
    $todo = "(unknown)"
  }

  if ($raw -eq $prevTodo) {
    Log "round $i : no progress on [$raw], backing off $delay s."
    Start-Sleep -Seconds $delay
    $delay = [Math]::Min($delay * 2, $MaxDelay)
  } else {
    Log "round $i : todo = $raw"
    $prevTodo = $raw
    $delay = $BaseDelay
  }

  $prompt = $template.Replace("{{CHAPTERS}}", $todo).Replace("{{STATES}}", $raw)
  $title = "bible-notes-round-" + $i

  if ($DryRun) {
    Log "DRY RUN - prompt follows:"
    Log $prompt
    break
  }

  $cliArgs = @("run", "--auto", "--title", $title)
  if ($models[$modelIdx] -ne "") { $cliArgs += @("--model", $models[$modelIdx]) }
  $cliArgs += $prompt
  $res = & $cli @cliArgs 2>&1
  $text = ($res | Out-String)
  Add-Content -Path $log -Value $text -Encoding UTF8

  if ($text -match "Rate limit|rate limit|429|Too Many Requests") {
    $modelIdx = ($modelIdx + 1) % $models.Count
    $nextModel = $models[$modelIdx]
    if ($nextModel -eq "") { $nextModel = "(default)" }
    Log "rate limited. switching model to $nextModel, backing off $delay s."
    Start-Sleep -Seconds $delay
    $delay = [Math]::Min($delay * 2, $MaxDelay)
  } else {
    Log "round $i session finished (model=$($models[$modelIdx]))."
    $modelIdx = 0
    $delay = $BaseDelay
    Start-Sleep -Seconds 10
  }
}

Log "supervisor exiting."
Remove-Item $pidF -ErrorAction SilentlyContinue
