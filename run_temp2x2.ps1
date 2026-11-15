<#
  run_temp2x2.ps1 - prompt x temperature replication (196 sessions).

  Reads temp2x2_replication\run_config.json and runs each model's 28 sessions in the
  prescribed order: 14 adjacent minimalist/informed pairs, 7 at temperature 0 and 7 at
  temperature 1, with the Proteus seed PAIRED within each pair. Prompts, opponent, trial
  count and logging are identical to the main study.

  Usage (PowerShell, from the project folder):
      $env:OPENROUTER_API_KEY = "sk-or-..."
      .\run_temp2x2.ps1 -DryRun                 # print the schedule, call nothing
      .\run_temp2x2.ps1 -Pilot                  # 20-trial check of both prompts at temp 1, all models
      .\run_temp2x2.ps1                         # the real run (196 sessions)
      .\run_temp2x2.ps1 -Only opus,sonnet       # only these model groups (for parallel terminals)

  Safe to re-run: complete sessions already on disk are skipped (resume guard).
  Data lands in data_temp2x2\<group>\ , one CSV per session. Pilot data goes to
  data_temp2x2_pilot\ with different seeds and is never analyzed with the real run.
#>
param(
  [string]   $ConfigPath = ".\temp2x2_replication\run_config.json",
  [string]   $OutputDir  = "data_temp2x2",
  [int]      $NTrials    = 200,
  [int]      $MaxTokens  = 20000,
  [int]      $DescWindow = 5,
  [int]      $CompactWindow = 25,
  [string]   $Opponent   = "proteus",
  [string]   $RunId      = "",
  [string[]] $Only       = @(),
  [switch]   $Pilot,
  [switch]   $DryRun
)

if (-not (Test-Path $ConfigPath)) { Write-Error "config not found: $ConfigPath"; exit 1 }
if (-not $DryRun -and -not $env:OPENROUTER_API_KEY) {
  Write-Error "OPENROUTER_API_KEY not set in this shell."; exit 1
}

$cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
if ($RunId -eq "") { $RunId = [guid]::NewGuid().ToString() }
if ($Pilot) { $OutputDir = "data_temp2x2_pilot"; $NTrials = 20 }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$inv = [System.Globalization.CultureInfo]::InvariantCulture

$models = @($cfg.models)
if ($Only.Count -gt 0) { $models = @($models | Where-Object { $Only -contains $_.group }) }
if ($models.Count -eq 0) { Write-Error "no models selected (check -Only against the group names)"; exit 1 }

$label = "TEMP 2x2 RUN"; if ($Pilot) { $label = "TEMP 2x2 PILOT" }
Write-Host "$label  $RunId" -ForegroundColor Cyan
Write-Host "  master seed $($cfg.master_seed) | $($models.Count) models | $NTrials trials | -> $OutputDir`n" -ForegroundColor Cyan

$ran = 0; $skipped = 0; $failed = 0

foreach ($m in $models) {
  Write-Host ("=== {0}  [{1}]  order {2}, first temperature {3}" -f $m.model, $m.family, $m.order_sequence, $m.temp_start) -ForegroundColor Yellow
  $sessions = @($m.sessions)
  if ($Pilot) {
    # first temperature-1 pair of this model only
    $firstPair = ($sessions | Where-Object { [double]$_.temperature -eq 1.0 } | Select-Object -First 1).stream_pair
    $sessions = @($sessions | Where-Object { $_.stream_pair -eq $firstPair })
  }
  foreach ($s in $sessions) {
    $temp  = ([double]$s.temperature).ToString("0.0", $inv)
    $ttok  = "t" + ($temp -replace '\.','p')
    $sidx  = [int]$s.session_index
    $seed  = [long]$s.session_seed
    if ($Pilot) { $sidx = $sidx + 9000; $seed = $seed + 500000 }
    $tag = "{0} T={1} pair{2}/{3} {4}" -f $m.group, $temp, $s.pair_within_temp, $s.position_in_pair, $s.condition

    # resume guard: skip if a complete session for this global index already exists
    $sdir = Join-Path $OutputDir $m.group
    $pat  = "$($m.group)_$($Opponent)_$($s.condition)_$($ttok)_s$($sidx)_*.csv"
    $done = $false
    foreach ($cf in @(Get-ChildItem -Path $sdir -Filter $pat -ErrorAction SilentlyContinue)) {
      try { if (@(Import-Csv $cf.FullName).Count -eq $NTrials) { $done = $true; break } } catch {}
    }
    if ($done) { Write-Host ("   skip  {0}  (already complete)" -f $tag) -ForegroundColor DarkGray; $skipped++; continue }

    Write-Host ("   ->    {0}   session_index {1}  seed {2}" -f $tag, $sidx, $seed)
    if ($DryRun) { $ran++; continue }

    python .\run_session.py `
      --model          $m.slug `
      --model-group    $m.group `
      --model-display  $m.model `
      --prompt-mode    $s.condition `
      --opponent       $Opponent `
      --n-trials       $NTrials `
      --temperature    $temp `
      --max-tokens     $MaxTokens `
      --desc-window    $DescWindow `
      --compact-window $CompactWindow `
      --master-seed    $cfg.master_seed `
      --session-index  $sidx `
      --session-seed   $seed `
      --run-id         $RunId `
      --output-dir     $OutputDir

    if ($LASTEXITCODE -ne 0) { $failed++; Write-Warning "session $sidx exited $LASTEXITCODE (re-run this script to resume)" }
    $ran++
  }
}

$color = "Green"; if ($failed -gt 0) { $color = "Red" }
Write-Host ("`nDONE. run_id={0}  ran={1}  skipped={2}  failed={3}  -> {4}" -f $RunId, $ran, $skipped, $failed, $OutputDir) -ForegroundColor $color
if ($failed -gt 0) { Write-Host "Some sessions failed. Re-run the same command; complete sessions are skipped." -ForegroundColor Red }
elseif (-not $Pilot -and -not $DryRun) { Write-Host "Next: python .\temp2x2_replication\analyze_temp2x2.py" -ForegroundColor Green }
