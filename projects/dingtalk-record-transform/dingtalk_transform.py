"""钉钉记录转换。无第三方依赖，无打印，无网络请求，不修改输入。

transform_records(records) -> 每条有效原始记录对应一条平铺记录
transform(records) -> transform_records 的兼容入口
main(iPaas_result) -> {"result": 平铺记录列表}
"""


def _text(value, location):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError(location + " 必须是字符串或 null")
    return value


def _items(value, location):
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(location + " 必须是列表或 null")
    return value


def extract_records(payload, records_path=None):
    """提取记录列表。对象包装必须显式传入字段路径，不猜测接口结构。

    示例：extract_records(payload, ["data", "records"])
    未指定路径时，payload 本身必须是列表。
    """
    if records_path is not None:
        if not isinstance(records_path, (list, tuple)):
            raise TypeError("records_path 必须是字段路径列表或元组")
        for position, part in enumerate(records_path):
            if not isinstance(part, str):
                raise TypeError("records_path 中的字段名必须是字符串")
            if not isinstance(payload, dict) or part not in payload:
                raise ValueError("记录列表路径不存在，位置 " + str(position))
            payload = payload[part]
    if not isinstance(payload, list):
        raise TypeError("记录数据必须是列表，请绑定记录列表或显式指定 records_path")
    return payload


def transform_records(records):
    """逐条展开记录，不按公司或店铺合并，不去重，不修改输入。

    缺失或 null 的用户名、密码输出为空字符串。非空字符串原样保留。
    非法结构立即报错；错误仅包含字段位置，不包含账号密码值。
    """
    records = extract_records(records)
    result = []

    for index, record in enumerate(records):
        location = "records[" + str(index) + "]"
        if not isinstance(record, dict):
            raise TypeError(location + " 必须是对象")
        fields = record.get("fields")
        if fields is None:
            continue
        if not isinstance(fields, dict):
            raise TypeError(location + ".fields 必须是对象或 null")
        if not fields:
            continue

        prefix = location + ".fields."
        company = _text(fields.get("公司名"), prefix + "公司名")
        if not company.strip():
            raise ValueError(prefix + "公司名不能为空")
        username = _text(fields.get("企业用户名"), prefix + "企业用户名")
        password = _text(fields.get("企业密码"), prefix + "企业密码")
        shop = _text(fields.get("店铺"), prefix + "店铺") or company
        if not shop.strip():
            raise ValueError(prefix + "店铺不能只包含空白字符")
        output_record = {
            "公司名": company,
            "企业用户名": username,
            "企业密码": password,
            "店铺": shop,
            "站点": [], "unionId": [], "name": [],
        }

        sites = _items(fields.get("站点"), prefix + "站点")
        for site_index, site in enumerate(sites):
            site_location = prefix + "站点[" + str(site_index) + "]"
            if not isinstance(site, dict):
                raise TypeError(site_location + " 必须是对象")
            name = _text(site.get("name"), site_location + ".name")
            output_record["站点"].append(name)

        people = _items(fields.get("运营负责人"), prefix + "运营负责人")
        for person_index, person in enumerate(people):
            person_location = prefix + "运营负责人[" + str(person_index) + "]"
            if not isinstance(person, dict):
                raise TypeError(person_location + " 必须是对象")
            union_id = _text(person.get("unionId"), person_location + ".unionId")
            name = _text(person.get("name"), person_location + ".name")
            output_record["unionId"].append(union_id)
            output_record["name"].append(name)

        result.append(output_record)

    return result


def transform(records):
    """兼容现有调用名称，返回同样的逐条平铺结果。"""
    return transform_records(records)


def main(iPaas_result):
    """函数入口示例。平台若规定其他函数名或参数签名，请仅适配入口。"""
    return {"result": transform(iPaas_result)}
