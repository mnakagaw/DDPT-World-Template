param(
  [Parameter(Mandatory = $true)][string]$Project,
  [string]$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
)

$ErrorActionPreference = 'Stop'
if ($RunId -notmatch '^\d{8}T\d{6}Z$') { throw 'RunId must be a UTC timestamp.' }
$projectRoot = (Resolve-Path -LiteralPath $Project).Path
$runDirectory = Join-Path $projectRoot (Join-Path 'raw/qatar-census-2020-geography' $RunId)
if (Test-Path -LiteralPath $runDirectory) { throw "Acquisition directory already exists: $runDirectory" }
New-Item -ItemType Directory -Path $runDirectory | Out-Null

$gis = 'https://services.gisqatar.org.qa/server/rest/services/Vector/Census_Zone/MapServer'
$sources = @(
  @{ name = 'census-zone-2020-layer.json'; url = "$gis/0?f=pjson"; kind = 'layer' },
  @{ name = 'census-zone-2020-polygons.geojson'; url = "$gis/0/query?where=1%3D1&outFields=OBJECTID%2CZONE_NO%2CMUNICIPAL_CODE%2CMUNICIPALITY_NAME_EN&returnGeometry=true&outSR=4326&f=geojson"; kind = 'geometry' },
  @{ name = 'census-zone-population-2020.json'; url = "$gis/1/query?where=1%3D1&outFields=OBJECTID%2CZONE_NO%2CTOTAL_MALE_2020%2CTOTAL_FEMALE_2020&returnGeometry=false&f=json"; kind = 'population' },
  @{ name = 'qnmp-msdp-eight-municipalities.html'; url = 'https://www.mm.gov.qa/QatarMasterPlan/English/MSDP-Municipalities.aspx?panel=about'; kind = 'planning' }
)

$receipts = foreach ($source in $sources) {
  $target = Join-Path $runDirectory $source.name
  try {
    $response = Invoke-WebRequest -Uri $source.url -OutFile $target -PassThru -TimeoutSec 150
    $body = [System.IO.File]::ReadAllText($target)
    if ($source.kind -eq 'planning') {
      if (-not ($body -match 'completed an MSDP for each of the 8 municipalities')) {
        throw 'QNMP eight-municipality statement was not in the acquired page'
      }
    } else {
      $parsed = $body | ConvertFrom-Json -Depth 100
      if ($parsed.error) { throw "GIS service returned an error for $($source.name)" }
      if ($source.kind -eq 'layer') {
        if ($parsed.name -ne 'Census_Zone_2020' -or $parsed.geometryType -ne 'esriGeometryPolygon') {
          throw 'Census_Zone_2020 layer identity changed'
        }
      } elseif ($source.kind -eq 'geometry') {
        if ($parsed.type -ne 'FeatureCollection' -or @($parsed.features).Count -ne 91) {
          throw 'Expected 91 Census_Zone_2020 polygon features'
        }
      } elseif (@($parsed.features).Count -ne 91) {
        throw 'Expected 91 census zone population rows'
      }
    }
    $receipt = [ordered]@{
      status = 'acquired'
      source_id = if ($source.kind -eq 'planning') { 'qat-mm-qnmp-msdp-eight' } else { 'qat-gis-census-zone-2020' }
      url = $source.url
      http_status = [int]$response.StatusCode
      content_type = [string]$response.Headers['Content-Type']
      retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
      file = $source.name
      bytes = [long](Get-Item -LiteralPath $target).Length
      sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    }
  } catch {
    $receipt = [ordered]@{
      status = 'failed'
      source_id = if ($source.kind -eq 'planning') { 'qat-mm-qnmp-msdp-eight' } else { 'qat-gis-census-zone-2020' }
      url = $source.url
      retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
      file = $source.name
      error = $_.Exception.Message
    }
  }
  $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$target.receipt.json" -Encoding utf8
  $receipt
}
[ordered]@{ run_id = $RunId; source = 'Qatar official 2020 census-zone GIS and QNMP municipality-plan discovery'; receipts = @($receipts) } |
  ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDirectory 'manifest.json') -Encoding utf8
$receipts | ForEach-Object { "$($_['status'])`t$($_['file'])`t$($_['bytes'])`t$($_['sha256'])" }
if ($receipts.Where({ $_['status'] -ne 'acquired' }).Count -gt 0) { throw 'One or more official sources failed; inspect each receipt.' }
