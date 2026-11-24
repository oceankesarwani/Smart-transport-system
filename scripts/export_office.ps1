param(
    [string]$Presentation = "docs/presentation.pptx",
    [string]$PresentationPdf = "docs/PPT.pdf",
    [switch]$RenderSrs
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pptxPath = [System.IO.Path]::GetFullPath((Join-Path $root $Presentation))
$pdfPath = [System.IO.Path]::GetFullPath((Join-Path $root $PresentationPdf))
$powerpoint = New-Object -ComObject PowerPoint.Application
try {
    $deck = $powerpoint.Presentations.Open($pptxPath, $true, $false, $false)
    if ($deck.Slides.Count -ne 5) { throw 'Presentation must contain exactly five slides' }
    $deck.SaveAs($pdfPath,32)
    $deck.Close()
} finally { $powerpoint.Quit() }
if ($RenderSrs) {
    $target = Join-Path $root 'tmp\docx-render'
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    try {
        $doc = $word.Documents.Open((Join-Path $root 'docs\SRS.docx'),$false,$true,$false)
        $doc.ExportAsFixedFormat((Join-Path $target 'SRS.pdf'),17)
        $doc.Close(0)
    } finally { $word.Quit() }
}
Write-Output 'Five-slide PDF exported'
