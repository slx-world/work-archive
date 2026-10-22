# 钉钉多行记录转换

版本 2.0.0 将每条有效原始记录输出为一条平铺记录。公司名、企业用户名、企业密码、店铺、站点、unionId、name 位于同一层；相同公司、相同店铺或完全重复的输入记录都分别保留。

## 使用方式

直接执行式代码节点使用 [dingtalk_node.py](dingtalk_node.py)，输入参数 iPaas_result 绑定原始记录列表，输出变量为 result。函数式节点使用 [dingtalk_transform.py](dingtalk_transform.py)，main 返回含 result 的对象。入口签名按实际平台适配，转换代码不需要导入模块或打印。

## 数据格式

```json
[
  {
    "公司名": "示例医疗公司",
    "企业用户名": "demo_medical",
    "企业密码": "DemoOnly}|#2026",
    "店铺": "示例医疗店",
    "站点": ["美国", "加拿大", "墨西哥"],
    "unionId": ["demo_u01"],
    "name": ["负责人甲"]
  }
]
```

逐条读取 fields 并展开，不分组、不合并、不去重。站点列表和负责人列表保留原始顺序及重复项，unionId 与 name 按下标对应。密码字符原样保留；只有归档示例使用虚构凭据，运行代码不会把业务密码改成占位符。

输入示例见 [input.json](examples/input.json)，输出示例见 [output.json](examples/output.json)，函数入口的外层封装见 [main_output.json](examples/main_output.json)。示例均使用虚构业务资料。结构定义见 [输出 JSON Schema](schemas/output.schema.json)。

## 从旧版迁移

旧版读取站点的形式为 `result[i][店铺名]["站点"]`，新版改为 `result[i]["站点"]`；店铺名称读取 `result[i]["店铺"]`。原始输入不变，转换不再合并原始记录。`transform_records(records)` 是主函数，`transform(records)` 保留为兼容入口，但也返回新版平铺格式。

仓库示例含 10 条输入，其中 2 条为空、1 条为重复记录，因此输出 8 条。用户提供的数据有 7 条有效记录，转换后为 7 条。旧版格式和去重行为可从 Git 历史查看，当前目录中的代码、示例及文档统一采用逐条平铺规则。

每条输出固定包含七个字段，店铺名即使等于“公司名”等字段名也不会覆盖数据。fields 缺失、null 或空对象时跳过。非空 fields 的公司名必须非空白；店铺缺失或为空字符串时取公司名。缺失值规则和输入类型校验详见 [使用说明](使用说明.txt) 或 [Word 说明书](使用说明.docx)。

## 验证

```bash
python -m unittest discover -s projects/dingtalk-record-transform -v
```

在仓库根目录执行。测试覆盖平铺结构、跨店铺隔离、重复记录、密码原样保留、节点入口及缺失值。钉钉平台中的输入输出绑定仍需接入后确认。
