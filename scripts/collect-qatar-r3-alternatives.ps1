param(
  [Parameter(Mandatory = $true)][string]$Project,
  [string]$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $Project).Path
$directory = Join-Path $root (Join-Path 'raw/qatar-r3-alternatives' $RunId)
if (Test-Path -LiteralPath $directory) { throw "Already exists: $directory" }
New-Item -ItemType Directory -Path $directory | Out-Null
$sources = @(
  @{name='msdp-ar-khor.html'; url='https://www.mm.gov.qa/QatarMasterPlan/Arabic/MSDP-Municipalities.aspx?panel=Khor'; kind='html'},
  @{name='msdp-ar-wakra.html'; url='https://www.mm.gov.qa/QatarMasterPlan/Arabic/MSDP-Municipalities.aspx?panel=Wakra'; kind='html'},
  @{name='msdp-ar-sheehaniya.html'; url='https://www.mm.gov.qa/QatarMasterPlan/Arabic/MSDP-Municipalities.aspx?panel=shahaniya'; kind='html'},
  @{name='mof-state-budget-2025.pdf'; url='https://www.mof.gov.qa/en/Shared%20Documents/StateBudget2025.pdf'; kind='pdf'},
  @{name='mof-state-budget-2026.html'; url='https://www.mof.gov.qa/statebudget2026'; kind='html'}
)
$receipts = foreach ($source in $sources) {
  $target = Join-Path $directory $source.name
  $receipt = [ordered]@{url=$source.url; file=$source.name; retrieved_at=(Get-Date).ToUniversalTime().ToString('o')}
  try {
    Invoke-WebRequest -Uri $source.url -OutFile $target -TimeoutSec 120
    $bytes = [IO.File]::ReadAllBytes($target)
    $signature = [Text.Encoding]::ASCII.GetString($bytes,0,[Math]::Min(5,$bytes.Length))
    if ($source.kind -eq 'pdf' -and $signature -ne '%PDF-') { throw "Expected PDF; got $signature" }
    if ($source.kind -eq 'html' -and [Text.Encoding]::UTF8.GetString($bytes) -notmatch '<html|<!DOCTYPE') { throw 'Expected HTML' }
    $receipt.status='acquired'; $receipt.http_status=200; $receipt.bytes=$bytes.Length
    $receipt.sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
  } catch {
    $receipt.status='failed'; $receipt.error=$_.Exception.Message
  }
  $receipt | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath "$target.receipt.json" -Encoding utf8
  $receipt
}
[ordered]@{run_id=$RunId;receipts=@($receipts)} | ConvertTo-Json -Depth 5 |
  Set-Content -LiteralPath (Join-Path $directory 'manifest.json') -Encoding utf8
$receipts | ForEach-Object { "$($_.status)`t$($_.file)`t$($_.bytes)`t$($_.error)" }
if (@($receipts | Where-Object status -ne 'acquired').Count) { exit 1 }
