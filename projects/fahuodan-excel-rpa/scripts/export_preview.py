# -*- coding: utf-8 -*-
"""把处理后的 xlsx 导出为 UTF-8 CSV 预览，便于 GitHub 在线查看。"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from openpyxl import load_workbook


def export_preview(xlsx_path: str, csv_path: str | None = None) -> str:
    src = Path(xlsx_path)
    if not src.is_file():
        raise FileNotFoundError("找不到文件: %s" % src)
    dest = Path(csv_path) if csv_path else src.with_name(src.stem + "_预览.csv")

    wb = load_workbook(src, read_only=True, data_only=True)
    try:
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
    finally:
        wb.close()

    with dest.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(["" if v is None else v for v in row])
    return str(dest.resolve())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python export_preview.py <xlsx> [csv]")
        sys.exit(1)
    out = export_preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(out)
