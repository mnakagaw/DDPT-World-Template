param(
  [Parameter(Mandatory = $true)][string]$Project,
  [string]$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'Use PowerShell 7 or later for reliable Al Meezan downloads.' }
if ($RunId -notmatch '^\d{8}T\d{6}Z$') { throw 'RunId must be a UTC timestamp.' }
$root = (Resolve-Path -LiteralPath $Project).Path
$directory = Join-Path $root (Join-Path 'raw/qatar-r3-legal' $RunId)
if (Test-Path -LiteralPath $directory) { throw "Already exists: $directory" }
New-Item -ItemType Directory -Path $directory | Out-Null
$sources = @(
  @{ name='resolution-109-2024.html'; url='https://almeezan.qa/LawPage.aspx?id=9617&language=ar'; kind='html' },
  @{ name='resolution-109-2024-articles.html'; url='https://almeezan.qa/LawArticles.aspx?LawTreeSectionID=21430&language=ar&lawId=9617'; kind='html' },
  @{ name='resolution-109-2024-attachments.html'; url='https://almeezan.qa/LawOtherAttachments.aspx?id=9617&language=ar'; kind='html' },
  @{ name='resolution-68-2011.html'; url='https://almeezan.qa/LawPage.aspx?id=3837&language=ar'; kind='html' },
  @{ name='resolution-68-2011-attachments.html'; url='https://almeezan.qa/LawOtherAttachments.aspx?id=3837&language=ar'; kind='html' },
  @{ name='gazette-2024-issue-9.pdf'; url='https://www.almeezan.qa/PDF/2024/9.pdf'; kind='pdf' }
)
$receipts = foreach ($source in $sources) {
  $target = Join-Path $directory $source.name
  $receipt = [ordered]@{ url=$source.url; file=$source.name; retrieved_at=(Get-Date).ToUniversalTime().ToString('o') }
  try {
    Invoke-WebRequest -Uri $source.url -OutFile $target -TimeoutSec 180
    $head = [System.IO.File]::ReadAllBytes($target)
    if ($source.kind -eq 'pdf' -and [System.Text.Encoding]::ASCII.GetString($head,0,5) -ne '%PDF-') { throw 'Expected PDF signature' }
    if ($source.kind -eq 'html' -and -not ([System.Text.Encoding]::UTF8.GetString($head) -match 'الميزان|almeezan')) { throw 'Legal portal identity not found' }
    $receipt.status = 'acquired'
    $receipt.http_status = 200
    $receipt.content_type = if ($source.kind -eq 'pdf') { 'application/pdf' } else { 'text/html' }
    $receipt.bytes = [long]$head.Length
    $receipt.sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
  } catch {
    $receipt.status = 'failed'
    $receipt.error = $_.Exception.Message
  }
  $receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$target.receipt.json" -Encoding utf8
  $receipt
}
[ordered]@{ run_id=$RunId; receipts=@($receipts) } | ConvertTo-Json -Depth 6 |
  Set-Content -LiteralPath (Join-Path $directory 'manifest.json') -Encoding utf8
$receipts | ForEach-Object { "$($_.status)`t$($_.file)`t$($_.bytes)`t$($_.error)" }
if (@($receipts | Where-Object { $_.status -ne 'acquired' }).Count) { exit 1 }
