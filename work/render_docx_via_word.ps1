# Use Microsoft Word to export a DOCX to PDF (stand-in for the missing LibreOffice).
param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [Parameter(Mandatory = $true)][string]$Pdf
)

$ErrorActionPreference = 'Stop'

if (Test-Path $Pdf) { Remove-Item -LiteralPath $Pdf -Force }

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.Options.UpdateLinksAtOpen = $false

$doc = $word.Documents.Open($Docx, $false, $true)

# 17 = wdExportFormatPDF
$doc.ExportAsFixedFormat(
    $Pdf,
    17,
    $false,
    0,
    0,
    0,
    0,
    0,
    $true,
    $true,
    0,
    $true,
    $true,
    $false
)

$pages = $doc.ComputeStatistics(2)   # 2 = wdStatisticPages
$doc.Close(0)
$word.Quit(0)

Start-Sleep -Milliseconds 400

if (Test-Path $Pdf) {
    Write-Output "OK pages=$pages size=$((Get-Item $Pdf).Length)"
} else {
    Write-Output "FAILED pages=$pages"
    exit 1
}
