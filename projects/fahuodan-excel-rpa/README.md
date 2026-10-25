# 发货单 Excel 规整（影刀 RPA）

将带合并单元格的发货单 Excel，处理成无合并、每行字段完整的扁平表，供影刀 RPA 循环读取。

## 处理效果

| 发货单号 | 物流中心编码 | 创建时间 | 发货单状态 | 物流商 | 货件单号 | 货件状态 |
| --- | --- | --- | --- | --- | --- | --- |
| SP260001001 | TEB9 | 2026-10-09 16:31:45 | 已发货 | 示例物流 | FBADEMO00001 | IN_TRANSIT |

源表示例含 **15** 处合并、**8** 行明细；处理后 **3** 条去重记录、**0** 处合并。

## 目录

```text
fahuodan-excel-rpa/
├── process_shipment_excel.py   # 核心处理 + 影刀入口 main()
├── yingdao_command.py          # 影刀自定义指令模板
├── requirements.txt
├── data/
│   ├── examples/发货单-示例-含合并单元格.xlsx
│   └── processed/
│       ├── 发货单-示例-已处理.xlsx
│       └── 发货单-示例-已处理_预览.csv
├── docs/
│   ├── 影刀使用说明.md
│   └── 数据处理说明.md
└── scripts/
    ├── run_example.sh
    ├── run_example.ps1
    └── export_preview.py      # 生成 CSV 预览
```

示例数据已脱敏（虚构发货单号 / 货件单号 / 物流商），仅保留字段结构与合并形态。  
工作表名：`发货单详情`。表头七列与上表一致。

## 快速开始

```bash
cd projects/fahuodan-excel-rpa
pip install -r requirements.txt
```

Windows：

```powershell
.\scripts\run_example.ps1
```

macOS / Linux：

```bash
bash scripts/run_example.sh
```

或直接：

```bash
python process_shipment_excel.py \
  "data/examples/发货单-示例-含合并单元格.xlsx" \
  "发货单号,物流中心编码,创建时间,发货单状态,物流商" \
  "data/processed/发货单-示例-已处理.xlsx" \
  --sheet "发货单详情"
```

## 影刀参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `file_path` | 是 | 源 Excel 路径 |
| `column_names` | 是* | 需向下填充的列名，逗号分隔；默认五列主字段 |
| `output_name` | 是* | 输出文件名或路径；仅文件名时写到源文件同目录 |
| `sheet_name` | 否 | 工作表名；空则取第一个（样例为「发货单详情」） |
| `dedupe` | 否 | 是否整行去重，默认 `True`；可传 `"True"` / `"False"` |
| 返回值 `result` | — | 处理后文件完整路径 |

\* 命令行 / `main()` 对 `column_names`、`output_name` 有默认值；影刀自定义指令建议显式传入。

```python
from process_shipment_excel import main

result = main(
    file_path,
    "发货单号,物流中心编码,创建时间,发货单状态,物流商",
    "发货单_已处理.xlsx",
    sheet_name="发货单详情",
    dedupe=True,
)
```

详见 [`docs/影刀使用说明.md`](docs/影刀使用说明.md)、[`docs/数据处理说明.md`](docs/数据处理说明.md)。
