<#
  run_counterbalanced.ps1 — counterbalanced replication of the framing effect (56 sessions).

  Reads counterbalanced_replication\run_config.json and runs each model's 8 sessions in the
  prescribed order (four adjacent minimalist/informed pairs; two MI and two IM), with the
  Proteus seed PAIRED within each pair. Everything else is identical to the main study.

  Usage (PowerShell, from the project folder):
      $env:OPENROUTER_API_KEY = "sk-or-..."
      .\run_counterbalanced.ps1 -DryRun        # print the schedule, call nothing
      .\run_counterbalanced.ps1                # the real run (56 sessions, ~6-7 h)

  Safe to re-run: complete sessions already on disk are skipped (resume guard).
  Data lands in data_counterbalanced\<group>\ , one CSV per session.
#>
param(
  [string] $ConfigPath = ".\counterbalanced_replication\run_config.json",
  [string] $OutputDir  = "data_counterbalanced",
  [int]    $NTrials    = 200,
  [double] $Temperature = 0.0,
  [int]    $MaxTokens  = 20000,
  [int]    $DescWindow = 5,
  [int]    $CompactWindow = 25,
  [string] $Opponent   = "proteus",
  [string] $RunId      = "",
  [switch] $DryRun
)

if (-not (Test-Path $ConfigPath)) { Write-Error "config not found: $ConfigPath"; exit 1 }
if (-not $DryRun -and -not $env:OPENROUTER_API_KEY) {
  Write-Error "OPENROUTER_API_KEY not set in this shell."; exit 1
}

$cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
if ($RunId -eq "") { $RunId = [guid]::NewGuid().ToString() }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$total = ($cfg.models | ForEach-Object { $_.sessions.Count } | Measure-Object -Sum).Sum
Write-Host "COUNTERBALANCED RUN  $RunId" -ForegroundColor Cyan
Write-Host "  master seed $($cfg.master_seed) | $total sessions | $NTrials trials | temp $Temperature | -> $OutputDir`n" -ForegroundColor Cyan

$ttok = "t" + (("{0:0.0}" -f $Temperature) -replace '\.','p')
$ran = 0; $skipped = 0

foreach ($m in $cfg.models) {
  Write-Host ("=== {0}  [{1}]  sequence {2}: {3}" -f $m.model, $m.family, $m.sequence, $m.sequence_string) -ForegroundColor Yellow
  foreach ($s in $m.sessions) {
    $tag = "{0} pair{1}/{2} {3}" -f $m.group, $s.pair, $s.position_in_pair, $s.condition

    # resume guard: skip if a complete session for this global index already exists
    $sdir = Join-Path $OutputDir $m.group
    $pat  = "$($m.group)_$($Opponent)_$($s.condition)_$($ttok)_s$($s.session_index)_*.csv"
    $done = $false
    foreach ($cf in @(Get-ChildItem -Path $sdir -Filter $pat -ErrorAction SilentlyContinue)) {
      try { if (@(Import-Csv $cf.FullName).Count -eq $NTrials) { $done = $true; break } } catch {}
    }
    if ($done) { Write-Host ("   skip  {0}  (already complete)" -f $tag) -ForegroundColor DarkGray; $skipped++; continue }

    Write-Host ("   ->    {0}   session_index {1}  seed {2}" -f $tag, $s.session_index, $s.session_seed)
    if ($DryRun) { $ran++; continue }

    python .\run_session.py `
      --model          $m.slug `
      --model-group    $m.group `
      --model-display  $m.model `
      --prompt-mode    $s.condition `
      --opponent       $Opponent `
      --n-trials       $NTrials `
      --temperature    $Temperature `
      --max-tokens     $MaxTokens `
      --desc-window    $DescWindow `
      --compact-window $CompactWindow `
      --master-seed    $cfg.master_seed `
      --session-index  $s.session_index `
      --session-seed   $s.session_seed `
      --run-id         $RunId `
      --output-dir     $OutputDir

    if ($LASTEXITCODE -ne 0) { Write-Warning "session $($s.session_index) exited $LASTEXITCODE (re-run this script to resume)" }
    $ran++
  }
}

Write-Host ("`nDONE. run_id={0}  ran={1}  skipped={2}  -> {3}" -f $RunId, $ran, $skipped, $OutputDir) -ForegroundColor Green
Write-Host "Next: python .\reconcile.py --data $OutputDir   then the analysis in counterbalanced_replication\" -ForegroundColor Green
