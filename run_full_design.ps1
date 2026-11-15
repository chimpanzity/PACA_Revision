<#
run_full_design.ps1 - orchestrate the full Proteus replication.

Design (matches Paper 1): 7 models x 2 prompt conditions x N sessions x 200 trials.
Default N = 7 sessions per cell => 7 x 2 x 7 = 98 sessions, 19,600 trials.

Every session gets a derived, recorded seed from ONE master seed, and all
sessions in this run share ONE run_id (a GUID), written into every CSV row, so
the whole run is reconstructable. CSVs + per-session manifests land in .\data.

USAGE (PowerShell):
  $env:OPENROUTER_API_KEY = "sk-or-..."          # set your key for this shell
  python .\verify_models.py                       # confirm all 7 slugs first
  .\run_full_design.ps1                            # run everything
  .\run_full_design.ps1 -SessionsPerCell 3        # smaller pilot
  .\run_full_design.ps1 -Models @("anthropic/claude-sonnet-4.6") -Groups @("sonnet")

Notes:
  - MASTER SEED is fixed below for reproducibility; change it for a fresh run.
  - RUN ID is a fresh GUID each invocation (or pass -RunId to resume/label).
  - Uses the committed (no-peek) opponent. To also collect a random-opponent
    control, re-run with -Opponent random.
#>

param(
  [int]    $SessionsPerCell = 7,
  [int]    $NTrials         = 200,
  [int]    $MasterSeed      = 20260701,
  [double] $Temperature     = 0.0,
  [int]    $MaxTokens       = 20000,
  [int]    $DescWindow      = 5,
  [int]    $CompactWindow   = 25,
  [string] $Opponent        = "proteus",
  [string] $OutputDir       = "data",
  [string] $RunId           = "",
  [string[]] $Models = @(
      "anthropic/claude-opus-4.8",
      "anthropic/claude-sonnet-4.6",
      "anthropic/claude-haiku-4.5",
      "openai/gpt-5.4",
      "openai/gpt-5.4-mini",
      "google/gemini-3.1-flash-lite",
      "google/gemini-3-flash-preview"
  ),
  [string[]] $Groups = @("opus","sonnet","haiku","gpt54","gpt54mini","gemini31fl","gemini3fp"),
  [string[]] $Displays = @("Claude Opus 4.8","Claude Sonnet 4.6","Claude Haiku 4.5",
                           "GPT-5.4","GPT-5.4-mini","Gemini 3.1 Flash Lite","Gemini 3 Flash Preview"),
  [string[]] $Conditions = @("minimalist","informed")
)

if (-not $env:OPENROUTER_API_KEY) { Write-Error "OPENROUTER_API_KEY not set in this shell."; exit 1 }
if ($Models.Count -ne $Groups.Count) { Write-Error "Models and Groups must be the same length."; exit 1 }
if ($RunId -eq "") { $RunId = [guid]::NewGuid().ToString() }

$startedUtc = (Get-Date).ToUniversalTime().ToString("o")
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# run_id, seeds, and full config are stamped into every CSV row (no separate manifest file).
$totalSessions = $Models.Count * $Conditions.Count * $SessionsPerCell
Write-Host "RUN $RunId  |  master seed $MasterSeed  |  $totalSessions sessions" -ForegroundColor Cyan

# session-index is GLOBAL across the whole run so every derived seed is unique.
$sessionIndex = 0
$skipped = 0
for ($m = 0; $m -lt $Models.Count; $m++) {
  foreach ($cond in $Conditions) {
    for ($s = 0; $s -lt $SessionsPerCell; $s++) {
      # resume guard: skip this session if a COMPLETE one already exists on disk.
      # (session-index uniquely identifies the cell for a given design + master seed.)
      $sdir = Join-Path $OutputDir $Groups[$m]
      $ttok = "t" + (("{0:0.0}" -f $Temperature) -replace '\.','p')   # matches run_session's temp token
      $pat  = "$($Groups[$m])_$($Opponent)_$($cond)_$($ttok)_s$($sessionIndex)_*.csv"
      $done = $false
      foreach ($cf in @(Get-ChildItem -Path $sdir -Filter $pat -ErrorAction SilentlyContinue)) {
        try { if (@(Import-Csv $cf.FullName).Count -eq $NTrials) { $done = $true; break } } catch {}
      }
      if ($done) { Write-Host ("   skip [{0}/{1}] session {2} (already complete)" -f $Groups[$m], $cond, $s) -ForegroundColor DarkGray; $skipped++; $sessionIndex++; continue }
      Write-Host ("-> [{0}/{1}] {2}  session {3}" -f $Groups[$m], $cond, $Models[$m], $s)
      python .\run_session.py `
        --model        $Models[$m] `
        --model-group  $Groups[$m] `
        --model-display $Displays[$m] `
        --prompt-mode  $cond `
        --opponent     $Opponent `
        --n-trials     $NTrials `
        --temperature  $Temperature `
        --max-tokens   $MaxTokens `
        --desc-window  $DescWindow `
        --compact-window $CompactWindow `
        --master-seed  $MasterSeed `
        --session-index $sessionIndex `
        --run-id       $RunId `
        --output-dir   $OutputDir
      if ($LASTEXITCODE -ne 0) { Write-Warning "session $sessionIndex exited $LASTEXITCODE" }
      $sessionIndex++
    }
  }
}
Write-Host "DONE. run_id=$RunId  sessions=$sessionIndex  (skipped $skipped already-complete)  -> $OutputDir" -ForegroundColor Green
