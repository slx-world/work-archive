#Requires -Version 5.0
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m pip install -q -r requirements.txt

$Src = Join-Path $Root "data\examples\发货单-示例-含合并单元格.xlsx"
$Out = Join-Path $Root "data\processed\发货单-示例-已处理.xlsx"
$Cols = "发货单号,物流中心编码,创建时间,发货单状态,物流商"
$Sheet = "发货单详情"

$Result = python process_shipment_excel.py $Src $Cols $Out --sheet $Sheet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/export_preview.py --all
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "已生成: $Result"
Write-Host "在线预览已更新（CSV / Markdown，GitHub 可直接打开）"