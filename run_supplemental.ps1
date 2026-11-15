<#
run_supplemental.ps1 - the supplemental control matrix against Proteus
(the adaptive opponent). Mirrors EXPERIMENT_DESIGN.md sections B/C/D.

Cells (per model):
  informed_ablated            temp 0.0  n=4
  informed_no_prescription    temp 0.0  n=4
  informed_no_opponent        temp 0.0  n=4
  informed @ 0.3              temp 0.3  n=4
  informed @ 0.7              temp 0.7  n=4
  informed @ 1.0              temp 1.0  n=4
  informed_diamondsquare      temp 0.0  n=4
  informed_trianglesquare     temp 0.0  n=4
  informed_revorder           temp 0.0  n=1
  minimalist_diamondsquare    temp 0.0  n=1
  ------------------------------------------------
  = 34 sessions/model x 7 = 238 sessions = 47,600 trials

Prereqs (run first, in this shell):
  $env:OPENROUTER_API_KEY = "sk-or-..."
  python .\verify_conditions.py     # must print ALL CHECKS PASSED
  python .\verify_models.py
  python .\token_probe.py           # ESPECIALLY before the temp-1.0 cells
Uses a SEPARATE master seed from the main run so derived session seeds don't collide.
#>

param(
  [int]    $MasterSeed    = 20260801,
  [int]    $NTrials       = 200,
  [int]    $MaxTokens     = 20000,
  [int]    $MaxTokensCeiling = 80000,
  [int]    $DescWindow    = 5,
  [int]    $CompactWindow = 25,
  [string] $Opponent      = "proteus",
  [string] $OutputDir     = "data_supplemental",
  [string] $RunId         = "",
  [string[]] $Models = @(
      "anthropic/claude-opus-4.8","anthropic/claude-sonnet-4.6","anthropic/claude-haiku-4.5",
      "openai/gpt-5.4","openai/gpt-5.4-mini","google/gemini-3.1-flash-lite","google/gemini-3-flash-preview"),
  [string[]] $Groups = @("opus","sonnet","haiku","gpt54","gpt54mini","gemini31fl","gemini3fp"),
  [string[]] $Displays = @("Claude Opus 4.8","Claude Sonnet 4.6","Claude Haiku 4.5",
      "GPT-5.4","GPT-5.4-mini","Gemini 3.1 Flash Lite","Gemini 3 Flash Preview")
)

if (-not $env:OPENROUTER_API_KEY) { Write-Error "OPENROUTER_API_KEY not set."; exit 1 }
if ($RunId -eq "") { $RunId = [guid]::NewGuid().ToString() }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# (prompt_mode, temperature, sessions) per cell
$cells = @(
  @("informed_ablated",         0.0, 4),
  @("informed_no_prescription", 0.0, 4),
  @("informed_no_opponent",     0.0, 4),
  @("informed",                 0.3, 4),
  @("informed",                 0.7, 4),
  @("informed",                 1.0, 4),
  @("informed_diamondsquare",   0.0, 4),
  @("informed_trianglesquare",  0.0, 4),
  @("informed_revorder",        0.0, 1),
  @("minimalist_diamondsquare", 0.0, 1)
)

$sessionIndex = 0
$skipped = 0
Write-Host "SUPPLEMENTAL RUN $RunId  master seed $MasterSeed  opponent $Opponent" -ForegroundColor Cyan
for ($m = 0; $m -lt $Models.Count; $m++) {
  foreach ($c in $cells) {
    $mode = $c[0]; $temp = $c[1]; $n = $c[2]
    for ($s = 0; $s -lt $n; $s++) {
      # resume guard: skip this session if a COMPLETE one already exists on disk.
      $sdir = Join-Path $OutputDir $Groups[$m]
      $ttok = "t" + (("{0:0.0}" -f $temp) -replace '\.','p')   # matches run_session's temp token
      $pat  = "$($Groups[$m])_$($Opponent)_$($mode)_$($ttok)_s$($sessionIndex)_*.csv"
      $done = $false
      foreach ($cf in @(Get-ChildItem -Path $sdir -Filter $pat -ErrorAction SilentlyContinue)) {
        try { if (@(Import-Csv $cf.FullName).Count -eq $NTrials) { $done = $true; break } } catch {}
      }
      if ($done) { Write-Host ("   skip [{0}] {1} t{2} ({3}/{4}) (already complete)" -f $Groups[$m], $mode, $temp, ($s+1), $n) -ForegroundColor DarkGray; $skipped++; $sessionIndex++; continue }
      Write-Host ("-> [{0}] {1} t{2} ({3}/{4})" -f $Groups[$m], $mode, $temp, ($s+1), $n)
      python .\run_session.py `
        --model $Models[$m] --model-group $Groups[$m] --model-display $Displays[$m] `
        --prompt-mode $mode --opponent $Opponent `
        --n-trials $NTrials --temperature $temp `
        --max-tokens $MaxTokens --max-tokens-ceiling $MaxTokensCeiling `
        --desc-window $DescWindow --compact-window $CompactWindow `
        --master-seed $MasterSeed --session-index $sessionIndex `
        --run-id $RunId --output-dir $OutputDir
      if ($LASTEXITCODE -ne 0) { Write-Warning "session $sessionIndex ($mode t$temp) exited $LASTEXITCODE - rerun if truncation-abort" }
      $sessionIndex++
    }
  }
}
Write-Host "DONE. supplemental sessions=$sessionIndex  (skipped $skipped already-complete)  run_id=$RunId  -> $OutputDir" -ForegroundColor Green
Write-Host "Now: python .\reconcile.py --data $OutputDir --expected-per-session $NTrials" -ForegroundColor Yellow
