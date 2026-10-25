#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install -q -r requirements.txt

SRC="$ROOT/data/examples/发货单-示例-含合并单元格.xlsx"
OUT="$ROOT/data/processed/发货单-示例-已处理.xlsx"

RESULT="$(python3 process_shipment_excel.py \
  "$SRC" \
  "发货单号,物流中心编码,创建时间,发货单状态,物流商" \
  "$OUT")"

echo "已生成: $RESULT"
