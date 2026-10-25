# -*- coding: utf-8 -*-
"""
影刀 RPA 可复用指令：发货单 Excel 取消合并单元格并规整为逐行完整数据。

入参：
  file_path      - 源 Excel 文件路径
  column_names   - 需要向下填充的列字段名（逗号/中文逗号/分号分隔），
                   一般为合并单元格所在列，如：发货单号,物流中心编码,创建时间,发货单状态,物流商
  output_name    - 处理后的文件名称（可带或不带 .xlsx）

出参：
  处理后文件的完整路径（与源文件同目录）
"""

from __future__ import annotations

import os
import re
from copy import copy
from typing import Iterable, List, Optional, Sequence, Union

from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet


def _parse_column_names(column_names: Union[str, Sequence[str]]) -> List[str]:
    """将影刀传入的列名参数解析为列表。"""
    if isinstance(column_names, (list, tuple)):
        names = [str(x).strip() for x in column_names]
    else:
        text = str(column_names).strip()
        # 兼容逗号、中文逗号、分号、竖线、换行
        names = re.split(r"[,，;；|\n\r\t]+", text)
        names = [n.strip() for n in names]
    return [n for n in names if n]


def _normalize_output_name(output_name: str) -> str:
    name = str(output_name).strip().strip('"').strip("'")
    if not name:
        raise ValueError("处理后的文件名称不能为空")
    if not name.lower().endswith((".xlsx", ".xlsm")):
        name = f"{name}.xlsx"
    return name


def _resolve_output_path(file_path: str, output_name: str) -> str:
    """
    解析输出路径：
    - 若 output_name 为绝对路径，或包含目录分隔符，则按其路径写入；
    - 否则写到源文件同目录下。
    """
    output_name = _normalize_output_name(output_name)
    if os.path.isabs(output_name) or os.path.dirname(output_name):
        output_path = os.path.abspath(output_name)
    else:
        output_path = os.path.join(os.path.dirname(file_path), output_name)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    return output_path


def _header_map(ws: Worksheet, header_row: int = 1) -> dict:
    mapping = {}
    for col in range(1, ws.max_column + 1):
        value = ws.cell(header_row, col).value
        if value is None:
            continue
        key = str(value).strip()
        if key:
            mapping[key] = col
    return mapping


def _unmerge_and_fill(ws: Worksheet) -> None:
    """取消全部合并单元格，并把原值写回合并区域内每一个单元格。"""
    merged_ranges = list(ws.merged_cells.ranges)
    for merged in merged_ranges:
        min_row, min_col = merged.min_row, merged.min_col
        max_row, max_col = merged.max_row, merged.max_col
        value = ws.cell(min_row, min_col).value
        ws.unmerge_cells(str(merged))
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                ws.cell(row, col).value = value


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _forward_fill_columns(ws: Worksheet, cols: Iterable[int], header_row: int = 1) -> None:
    """对指定列做向下填充（空单元格沿用上一行有效值）。"""
    last_values = {col: None for col in cols}
    for row in range(header_row + 1, ws.max_row + 1):
        for col in cols:
            cell = ws.cell(row, col)
            if _is_blank(cell.value):
                if last_values[col] is not None:
                    cell.value = last_values[col]
            else:
                last_values[col] = cell.value


def _row_values(ws: Worksheet, row: int, max_col: int) -> List:
    return [ws.cell(row, col).value for col in range(1, max_col + 1)]


def _row_all_blank(values: Sequence) -> bool:
    return all(_is_blank(v) for v in values)


def _dedupe_preserve_order(rows: List[List]) -> List[List]:
    """按整行内容去重，保留首次出现顺序。"""
    seen = set()
    result = []
    for row in rows:
        key = tuple("" if _is_blank(v) else str(v).strip() for v in row)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _copy_column_widths(source: Worksheet, target: Worksheet) -> None:
    for col_idx in range(1, source.max_column + 1):
        letter = get_column_letter(col_idx)
        width = source.column_dimensions[letter].width
        if width:
            target.column_dimensions[letter].width = width


def _write_clean_workbook(
    headers: Sequence,
    rows: Sequence[Sequence],
    source_ws: Optional[Worksheet] = None,
) -> Workbook:
    wb = Workbook()
    ws = wb.active
    ws.title = "发货单详情"

    for col, header in enumerate(headers, start=1):
        ws.cell(1, col).value = header

    for r_idx, row in enumerate(rows, start=2):
        for c_idx, value in enumerate(row, start=1):
            ws.cell(r_idx, c_idx).value = value

    if source_ws is not None:
        _copy_column_widths(source_ws, ws)

    # 明确保证没有任何合并单元格
    assert len(list(ws.merged_cells.ranges)) == 0
    return wb


def process_excel(
    file_path: str,
    column_names: Union[str, Sequence[str]],
    output_name: str,
    sheet_name: Optional[str] = None,
    dedupe: bool = True,
) -> str:
    """
    处理发货单 Excel：取消合并、按指定列向下填充、整行去重后导出。

    :param file_path: 源文件路径
    :param column_names: 需要向下填充的列字段名称
    :param output_name: 处理后的文件名称
    :param sheet_name: 工作表名，默认取第一个
    :param dedupe: 是否按整行去重（默认 True，适合发货单重复明细行）
    :return: 处理后文件的完整路径
    """
    file_path = os.path.abspath(str(file_path).strip().strip('"').strip("'"))
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"找不到文件: {file_path}")

    fill_names = _parse_column_names(column_names)
    if not fill_names:
        raise ValueError("需要处理的列的字段名称不能为空")

    output_path = _resolve_output_path(file_path, output_name)

    wb = load_workbook(file_path)
    if sheet_name:
        if sheet_name not in wb.sheetnames:
            raise ValueError(f"工作表不存在: {sheet_name}，可用: {wb.sheetnames}")
        ws = wb[sheet_name]
    else:
        ws = wb[wb.sheetnames[0]]

    headers_map = _header_map(ws, header_row=1)
    if not headers_map:
        raise ValueError("未读取到表头，请确认第一行为字段名称")

    missing = [name for name in fill_names if name not in headers_map]
    if missing:
        raise ValueError(
            f"以下列名在表头中不存在: {missing}；实际表头: {list(headers_map.keys())}"
        )

    fill_cols = [headers_map[name] for name in fill_names]
    max_col = ws.max_column
    headers = [ws.cell(1, c).value for c in range(1, max_col + 1)]

    _unmerge_and_fill(ws)
    _forward_fill_columns(ws, fill_cols, header_row=1)

    data_rows: List[List] = []
    for row_idx in range(2, ws.max_row + 1):
        values = _row_values(ws, row_idx, max_col)
        if _row_all_blank(values):
            continue
        data_rows.append(values)

    if dedupe:
        data_rows = _dedupe_preserve_order(data_rows)

    out_wb = _write_clean_workbook(headers, data_rows, source_ws=ws)
    out_wb.save(output_path)
    wb.close()
    out_wb.close()
    return output_path


# ========== 影刀自定义指令入口 ==========
# 在影刀中创建「Python」指令/模块时，将三个输入参数绑定到下方同名变量，
# 并把本函数的返回值设为输出「处理后文件路径」。
def main(file_path: str, column_names: str, output_name: str) -> str:
    """
    影刀指令主入口。

    影刀参数建议配置：
      - file_path: 文本 / 文件路径
      - column_names: 文本，例如 发货单号,物流中心编码,创建时间,发货单状态,物流商
      - output_name: 文本，例如 发货单_已处理.xlsx
    输出：
      - 处理后文件完整路径
    """
    return process_excel(file_path, column_names, output_name)


if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="发货单 Excel 取消合并并规整（影刀可复用）")
    parser.add_argument("file_path", help="源 Excel 文件路径")
    parser.add_argument(
        "column_names",
        help="需要向下填充的列名，逗号分隔，如：发货单号,物流中心编码,创建时间,发货单状态,物流商",
    )
    parser.add_argument("output_name", help="处理后的文件名称")
    parser.add_argument("--sheet", default=None, help="工作表名称，默认第一个")
    parser.add_argument("--no-dedupe", action="store_true", help="不去重，仅取消合并并填充")
    args = parser.parse_args()

    try:
        result = process_excel(
            args.file_path,
            args.column_names,
            args.output_name,
            sheet_name=args.sheet,
            dedupe=not args.no_dedupe,
        )
    except Exception as exc:  # noqa: BLE001 - CLI 需要把错误完整返回给调用方
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    # 便于影刀/命令行直接拿到路径
    print(result)
