param(
  [Parameter(Mandatory = $true)][string]$Project,
  [string]$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
)

$ErrorActionPreference = 'Stop'
if ($RunId -notmatch '^\d{8}T\d{6}Z$') { throw 'RunId must be a UTC timestamp.' }
$projectRoot = (Resolve-Path -LiteralPath $Project).Path
$runDirectory = Join-Path $projectRoot (Join-Path 'raw/qatar-r3-official-pages' $RunId)
if (Test-Path -LiteralPath $runDirectory) { throw "Acquisition directory already exists: $runDirectory" }
New-Item -ItemType Directory -Path $runDirectory | Out-Null

$qnmp = 'https://www.mm.gov.qa/QatarMasterPlan/English/MSDP-Municipalities.aspx?panel='
$gis = 'https://services.gisqatar.org.qa/server/rest/services/Vector/MunicipalityAT/MapServer/0'
$sources = @(
  @{ name = 'msdp-shamal.html'; url = "${qnmp}Shamal"; kind = 'panel' },
  @{ name = 'msdp-khor.html'; url = "${qnmp}Khor"; kind = 'panel' },
  @{ name = 'msdp-daayen.html'; url = "${qnmp}Daayen"; kind = 'panel' },
  @{ name = 'msdp-umm-slal.html'; url = "${qnmp}UmmSlal"; kind = 'panel' },
  @{ name = 'msdp-doha.html'; url = "${qnmp}doha"; kind = 'panel' },
  @{ name = 'msdp-sheehaniya.html'; url = "${qnmp}shahaniya"; kind = 'panel' },
  @{ name = 'msdp-rayyan.html'; url = "${qnmp}Rayyan"; kind = 'panel' },
  @{ name = 'msdp-wakra.html'; url = "${qnmp}Wakra"; kind = 'panel' },
  @{ name = 'municipality-current-layer.json'; url = "$gis`?f=pjson"; kind = 'layer' },
  @{ name = 'municipality-current-polygons.geojson'; url = "$gis/query?where=1%3D1&outFields=OBJECTID%2CCODE%2CGFCODE%2CMNCP_KEY%2CMNCP_NO%2CENAME%2CSTARTDATE%2CENDDATE%2CSOURCE%2CRELIABLE&returnGeometry=true&outSR=4326&f=geojson"; kind = 'geometry' },
  @{ name = 'npc-terms.html'; url = 'https://www.npc.qa/en/aboutus/pages/TermsOfUse.aspx'; kind = 'terms' }
)

$receipts = foreach ($source in $sources) {
  $target = Join-Path $runDirectory $source.name
  try {
    $response = Invoke-WebRequest -Uri $source.url -OutFile $target -PassThru -TimeoutSec 120
    $body = [System.IO.File]::ReadAllText($target)
    if ($source.kind -eq 'panel' -and $body -notmatch 'Municipality') { throw 'MSDP panel identity text was not found' }
    if ($source.kind -eq 'terms' -and $body -notmatch 'Terms of use') { throw 'NPC terms heading was not found' }
    if ($source.kind -in @('layer', 'geometry')) {
      $parsed = $body | ConvertFrom-Json -Depth 100
      if ($parsed.error) { throw "GIS returned an error for $($source.name)" }
      if ($source.kind -eq 'layer' -and ($parsed.name -ne 'Municipalities' -or $parsed.id -ne 0 -or $parsed.geometryType -ne 'esriGeometryPolygon')) { throw 'Current municipality layer identity changed' }
      if ($source.kind -eq 'geometry' -and ($parsed.type -ne 'FeatureCollection' -or @($parsed.features).Count -ne 8)) { throw 'Expected eight current municipality polygons' }
    }
    $receipt = [ordered]@{
      status = 'acquired'; source_id = if ($source.kind -in @('layer','geometry')) { 'qat-gis-municipality-current' } elseif ($source.kind -eq 'terms') { 'qat-npc-terms' } else { 'qat-mm-qnmp-msdp-panel' }
      url = $source.url; http_status = [int]$response.StatusCode; content_type = [string]$response.Headers['Content-Type']
      retrieved_at = (Get-Date).ToUniversalTime().ToString('o'); file = $source.name
      bytes = [long](Get-Item -LiteralPath $target).Length; sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    }
  } catch {
    $receipt = [ordered]@{
      status = 'failed'; url = $source.url; retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
      file = $source.name; error = $_.Exception.Message
    }
  }
  $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$target.receipt.json" -Encoding utf8
  $receipt
}
[ordered]@{ run_id = $RunId; source = 'Qatar R3 official MSDP panels, current municipality GIS and NPC terms'; receipts = @($receipts) } |
  ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDirectory 'manifest.json') -Encoding utf8
$receipts | ForEach-Object { "$($_['status'])`t$($_['file'])`t$($_['bytes'])`t$($_['sha256'])`t$($_['error'])" }
if (@($receipts | Where-Object status -ne 'acquired').Count) { exit 1 }
