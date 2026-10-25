# -*- coding: utf-8 -*-
"""
影刀 RPA「自定义 Python 指令」粘贴模板。

使用方式（影刀流程设计器）：
1. 安装依赖：pip install openpyxl
2. 将本仓库 process_shipment_excel.py 放到影刀可访问路径，
   或把 process_shipment_excel.py 内容与本文件合并后整段粘贴。
3. 新建自定义指令，声明 3 个输入、1 个输出：
     输入 file_path     - 源文件路径
     输入 column_names  - 需要处理（向下填充）的列字段名称
     输入 output_name   - 处理后的文件名称
     输出 result        - 处理后文件路径
4. 在指令代码中调用下方 execute(...)，把返回值赋给输出。

推荐 column_names 取值：
  发货单号,物流中心编码,创建时间,发货单状态,物流商
"""

from process_shipment_excel import process_excel


def execute(file_path: str, column_names: str, output_name: str) -> str:
    """影刀指令执行函数，返回处理后文件路径。"""
    return process_excel(file_path, column_names, output_name)


# ---- 影刀可视化参数绑定示例（按实际变量名调整）----
# file_path = xx_文件路径
# column_names = "发货单号,物流中心编码,创建时间,发货单状态,物流商"
# output_name = "发货单_已处理.xlsx"
# result = execute(file_path, column_names, output_name)
