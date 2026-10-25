# 发货单 Excel 规整（影刀 RPA）

将带合并单元格的发货单 Excel，处理成无合并、每行字段完整的扁平表，供影刀 RPA 循环读取。

## 处理效果

| 发货单号 | 物流中心编码 | 创建时间 | 发货单状态 | 物流商 | 货件单号 | 货件状态 |
| --- | --- | --- | --- | --- | --- | --- |
| SP260001001 | TEB9 | 2026-10-09 16:31:45 | 已发货 | 示例物流 | FBADEMO00001 | IN_TRANSIT |

## 目录

```text
fahuodan-excel-rpa/
├── process_shipment_excel.py   # 核心处理 + 影刀入口 main()
├── yingdao_command.py          # 影刀自定义指令模板
├── requirements.txt
├── data/
│   ├── raw/发货单-示例-含合并单元格.xlsx
│   └── processed/发货单-示例-已处理.xlsx
├── docs/
│   ├── 影刀使用说明.md
│   └── 数据处理说明.md
└── scripts/run_example.sh
```

示例数据已脱敏（虚构发货单号 / 货件单号 / 物流商），仅保留字段结构与合并形态。

## 快速开始

```bash
cd projects/fahuodan-excel-rpa
pip install -r requirements.txt
bash scripts/run_example.sh
```

或：

```bash
python process_shipment_excel.py \
  "data/examples/发货单-示例-含合并单元格.xlsx" \
  "发货单号,物流中心编码,创建时间,发货单状态,物流商" \
  "data/processed/发货单-示例-已处理.xlsx"
```

## 影刀参数

| 参数 | 说明 |
| --- | --- |
| `file_path` | 源 Excel 路径 |
| `column_names` | 需向下填充的列名，逗号分隔 |
| `output_name` | 输出文件名或路径 |
| 返回值 | 处理后文件完整路径 |

```python
from process_shipment_excel import main
result = main(file_path, "发货单号,物流中心编码,创建时间,发货单状态,物流商", "发货单_已处理.xlsx")
```

详见 `docs/影刀使用说明.md`、`docs/数据处理说明.md`。
