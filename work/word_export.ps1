# Export DOCX -> PDF through an already-running Word instance.
# COM *launch* fails in this agent context (CO_E_SERVER_EXEC_FAILURE), but
# attaching to a Word process we start ourselves works in Windows PowerShell 5.1.
param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [Parameter(Mandatory = $true)][string]$Pdf
)

$ErrorActionPreference = 'Continue'

if (Test-Path $Pdf) { Remove-Item -LiteralPath $Pdf -Force }

function Get-Word {
    try {
        return [Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application')
    } catch {
        return $null
    }
}

$word = Get-Word
$started = $false

if (-not $word) {
    Write-Output "no running Word; starting one"
    $exe = 'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE'
    Start-Process -FilePath $exe -ArgumentList '/q' | Out-Null
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        $word = Get-Word
        if ($word) { $started = $true; break }
    }
}

if (-not $word) {
    Write-Output "FAILED: could not attach to Word"
    exit 1
}

Write-Output "attached to Word (started_by_us=$started)"

try {
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($Docx, $false, $true)
    $pages = $doc.ComputeStatistics(2)
    $doc.ExportAsFixedFormat($Pdf, 17)
    $doc.Close(0)
    Write-Output "pages=$pages"
} catch {
    Write-Output "EXPORT ERROR: $($_.Exception.Message)"
    exit 1
}

Start-Sleep -Milliseconds 500

if (Test-Path $Pdf) {
    Write-Output "OK size=$((Get-Item $Pdf).Length)"
} else {
    Write-Output "FAILED: no PDF produced"
    exit 1
}
