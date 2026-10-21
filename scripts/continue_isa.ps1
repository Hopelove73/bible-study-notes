<#
  以赛亚书全书续写 · 自动监督器

  循环：查状态 → 用 opencode-cli 开一个新会话继续写 → 遇到限流就退避重试
        → 直到 scripts\status.py 报告 66 章全部通过。

  用法：
    powershell -ExecutionPolicy Bypass -File scripts\continue_isa.ps1
    powershell -ExecutionPolicy Bypass -File scripts\continue_isa.ps1 -MaxRounds 500
#>
param(
  [int]$MaxRounds  = 500,
  [int]$BaseDelay  = 60,
  [int]$MaxDelay   = 900,
  [int]$RoundsPerSession = 1
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$cli = "$env:LOCALAPPDATA\Programs\@opencodedesktop\resources\opencode-cli.exe"
$logDir = Join-Path $root "logs"
$log    = Join-Path $logDir "continue_isa.log"
$pidF   = Join-Path $logDir "supervisor.pid"

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

function Log([string]$m) {
  $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
  Add-Content -Path $log -Value $line -Encoding UTF8
  Write-Output $line
}

# 防止重复启动
if (Test-Path $pidF) {
  $old = (Get-Content $pidF -Raw).Trim()
  if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue)) {
    Log "已有监督器在跑 (pid=$old)，本实例退出。"
    exit 0
  }
}
Set-Content -Path $pidF -Value $PID -Encoding ASCII

Log "监督器启动 pid=$PID 最大轮次=$MaxRounds cli=$cli"

$delay = $BaseDelay
for ($i = 1; $i -le $MaxRounds; $i++) {
  $out = & py (Join-Path $root "scripts\status.py") --next 2>&1
  $todo = ($out | Select-Object -Last 1).ToString().Trim()
  $code = $LASTEXITCODE

  if ($code -eq 0 -and $todo -eq "") {
    Log "以赛亚书 66 章全部通过 P0，监督器结束。"
    break
  }
  if ($todo -eq "") { $todo = "（状态未知）" }

  Log "第 $i 轮，待办章节：$todo"

  $prompt = @"
继续以赛亚书全书精读笔记项目。项目目录：D:\圣经笔记\skill

第一步：完整阅读 D:\圣经笔记\skill\.agents\skills\isa-finish\SKILL.md（监督技能文件），严格按其中的流程与铁律执行。

当前待完成章节：$todo

本轮要求：
1. 用子代理写这些章，同时最多 2–3 个（超过 4 个会触发 API 限流）。每个子代理只写自己的 isa-XX.html。
2. 逐章跑 check_note.py 独立复核，P0 必须全过（只允许 A17 残留）。
3. 合并 assets/people.js：每章恰好 3 位 ★★★，yahweh 与 isaiah 为常驻，另加本章专属 1 位。
4. 生成 reviews/isa-XX.txt 审查报告。
5. 运行 py scripts\reg_index.py --write 更新首页目录与 books/ 下的 66 个书卷页。
6. git add -A；git commit；git push origin main（git 可执行文件在 C:\Program Files\Git\cmd\git.exe，推送失败要重试）。

做完这批不要停，继续下一批，直到 scripts\status.py 显示 66 章全部通过。
"@

  $title = "以赛亚书续写 第${i}轮"
  $res = & $cli run --auto --title $title $prompt 2>&1
  $text = ($res | Out-String)
  Add-Content -Path $log -Value $text -Encoding UTF8

  if ($text -match "Rate limit|rate limit|429") {
    Log "触发限流，退避 $delay 秒后重试。"
    Start-Sleep -Seconds $delay
    $delay = [Math]::Min($delay * 2, $MaxDelay)
  } else {
    Log "本轮会话结束。"
    $delay = $BaseDelay
    Start-Sleep -Seconds 15
  }
}

Log "监督器退出。"
Remove-Item $pidF -ErrorAction SilentlyContinue
