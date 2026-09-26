param(
  [Parameter(Mandatory = $true)][string]$Project,
  [string]$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
)

$ErrorActionPreference = 'Stop'
if ($RunId -notmatch '^\d{8}T\d{6}Z$') { throw 'RunId must be a UTC timestamp such as 20260927T010203Z.' }
$projectRoot = (Resolve-Path -LiteralPath $Project).Path
$runDirectory = Join-Path $projectRoot (Join-Path 'raw/qatar-census-2020' $RunId)
if (Test-Path -LiteralPath $runDirectory) { throw "Acquisition directory already exists: $runDirectory" }
New-Item -ItemType Directory -Path $runDirectory | Out-Null

$sources = @(
  @{ name = 'results-page.html'; url = 'https://www.npc.qa/en/statistics/census2020/Pages/results/default.aspx'; type = 'text/html' },
  @{ name = 'Census_Final_Results.xlsx'; url = 'https://www.npc.qa/en/statistics/census2020/results/Documents/Census_Final_Results.xlsx'; type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' },
  @{ name = 'Census_Final_Results.pdf'; url = 'https://www.npc.qa/en/statistics/census2020/results/Documents/Census_Final_Results.pdf'; type = 'application/pdf' },
  @{ name = 'Census_2020_Res_Summary_En.pdf'; url = 'https://www.npc.qa/en/statistics/census2020/results/Documents/Census_2020_Res_Summary_En.pdf'; type = 'application/pdf' }
)

$receipts = foreach ($source in $sources) {
  $target = Join-Path $runDirectory $source.name
  try {
    $response = Invoke-WebRequest -Uri $source.url -OutFile $target -PassThru -TimeoutSec 120
    $bytes = [System.IO.File]::ReadAllBytes($target)
    $signature = if ($source.name -like '*.pdf') { '%PDF-' } elseif ($source.name -like '*.xlsx') { 'PK' } else { '<' }
    $head = [System.Text.Encoding]::UTF8.GetString($bytes, 0, [Math]::Min($bytes.Length, 128)).TrimStart().TrimStart([char]0xFEFF)
    if (-not $head.StartsWith($signature)) {
      throw "Unexpected file signature for $($source.name)"
    }
    $receipt = [ordered]@{
      status = 'acquired'
      source_id = 'qat-npc-census-2020'
      url = $source.url
      http_status = [int]$response.StatusCode
      content_type = [string]$response.Headers['Content-Type']
      retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
      file = $source.name
      bytes = [long]$bytes.Length
      sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    }
  } catch {
    $receipt = [ordered]@{
      status = 'failed'
      source_id = 'qat-npc-census-2020'
      url = $source.url
      retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
      file = $source.name
      error = $_.Exception.Message
    }
  }
  $receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$target.receipt.json" -Encoding utf8
  if ($receipt.status -ne 'acquired') { throw "Acquisition failed for $($source.name); see its receipt." }
  $receipt
}

[ordered]@{ run_id = $RunId; source = 'Qatar National Planning Council, Census 2020'; receipts = @($receipts) } |
  ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDirectory 'manifest.json') -Encoding utf8
$receipts | ForEach-Object { "$($_['file'])`t$($_['bytes'])`t$($_['sha256'])" }
