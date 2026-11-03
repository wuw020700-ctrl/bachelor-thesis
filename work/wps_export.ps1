# Export DOCX -> PDF through WPS Office.
#
# Microsoft Word's COM server cannot be launched from this agent context
# (CO_E_SERVER_EXEC_FAILURE), but WPS Office's KWps.Application works.
param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [Parameter(Mandatory = $true)][string]$Pdf
)

$ErrorActionPreference = 'Stop'

if (Test-Path $Pdf) { Remove-Item -LiteralPath $Pdf -Force }

$app = New-Object -ComObject KWps.Application
$app.Visible = $false
$app.DisplayAlerts = 0

$doc = $app.Documents.Open($Docx)

# 17 = wdExportFormatPDF, ExportAsFixedFormat is Word-compatible in WPS
$doc.ExportAsFixedFormat($Pdf, 17)
$doc.Close()
$app.Quit()

Start-Sleep -Milliseconds 600

if (Test-Path $Pdf) {
    Write-Output "OK bytes=$((Get-Item $Pdf).Length)"
} else {
    Write-Output "FAILED: no PDF produced"
    exit 1
}
