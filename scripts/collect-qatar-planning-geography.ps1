param(
  [Parameter(Mandatory = $true)][string]$Project,
  [string]$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
)

$ErrorActionPreference = 'Stop'
if ($RunId -notmatch '^\d{8}T\d{6}Z$') { throw 'RunId must be a UTC timestamp.' }
$projectRoot = (Resolve-Path -LiteralPath $Project).Path
$runDirectory = Join-Path $projectRoot (Join-Path 'raw/qatar-planning-geography' $RunId)
if (Test-Path -LiteralPath $runDirectory) { throw "Acquisition directory already exists: $runDirectory" }
New-Item -ItemType Directory -Path $runDirectory | Out-Null

$sources = @(
  @{ name = 'qnmp-products.html'; url = 'https://www.mm.gov.qa/QatarMasterPlan/English/Product.html'; signature = '<' },
  @{ name = 'qnmp-msdp-zoning.html'; url = 'https://www.mm.gov.qa/QatarMasterPlan/English/msdp-zoning.aspx'; signature = '<' },
  @{ name = 'doha-municipality-strategy-2017.pdf'; url = 'https://www.mm.gov.qa/QatarMasterPlan/Downloads-qnmp/MunicipalityStrategy/English/Doha%20Dec%202017.pdf'; signature = '%PDF-' },
  @{ name = 'municipality-gis-current.json'; url = 'https://services.gisqatar.org.qa/server/rest/services/Vector/MunicipalityAT/MapServer/0/query?where=1%3D1&outFields=OBJECTID%2CCODE%2CGFCODE%2CMNCP_KEY%2CMNCP_NO%2CENAME%2CSTARTDATE%2CENDDATE%2CSOURCE%2CRELIABLE&returnGeometry=false&f=json'; signature = '{' }
)
$receipts = foreach ($source in $sources) {
  $target = Join-Path $runDirectory $source.name
  try {
    $response = Invoke-WebRequest -Uri $source.url -OutFile $target -PassThru -TimeoutSec 120
    $bytes = [System.IO.File]::ReadAllBytes($target)
    $head = [System.Text.Encoding]::UTF8.GetString($bytes, 0, [Math]::Min($bytes.Length, 128)).TrimStart().TrimStart([char]0xFEFF)
    if (-not $head.StartsWith($source.signature)) { throw "Unexpected file signature for $($source.name)" }
    $receipt = [ordered]@{
      status = 'acquired'
      source_id = 'qat-ministry-planning-or-gis-lead'
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
      source_id = 'qat-ministry-planning-or-gis-lead'
      url = $source.url
      retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
      file = $source.name
      error = $_.Exception.Message
    }
  }
  $receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$target.receipt.json" -Encoding utf8
  $receipt
}
[ordered]@{ run_id = $RunId; source = 'Qatar Ministry of Municipality planning and GIS location pass'; receipts = @($receipts) } |
  ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDirectory 'manifest.json') -Encoding utf8
$receipts | ForEach-Object { "$($_['status'])`t$($_['file'])`t$($_['bytes'])`t$($_['sha256'])" }
if ($receipts.Where({ $_['status'] -ne 'acquired' }).Count -gt 0) { throw 'One or more official leads failed; inspect each receipt.' }
