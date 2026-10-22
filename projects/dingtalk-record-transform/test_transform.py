"""本地验收测试；仅使用 Python 标准库。运行 python -m unittest -v。"""
import copy
import json
from pathlib import Path
import unittest

from dingtalk_transform import extract_records, main, transform, transform_records


def row(**updates):
    fields = {
        "公司名": "示例公司", "企业用户名": "demo", "企业密码": " Demo}|# ",
        "店铺": "示例店铺", "站点": [{"name": "美国"}],
        "运营负责人": [{"unionId": "demo_u1", "name": "负责人甲"}],
    }
    fields.update(updates)
    return {"fields": fields}


class TransformTests(unittest.TestCase):
    def test_single(self):
        data = transform([row()])[0]
        self.assertEqual(data["企业密码"], " Demo}|# ")
        self.assertEqual(data, {
            "公司名": "示例公司", "企业用户名": "demo", "企业密码": " Demo}|# ",
            "店铺": "示例店铺", "站点": ["美国"], "unionId": ["demo_u1"], "name": ["负责人甲"],
        })

    def test_empty(self):
        self.assertEqual(transform([]), [])

    def test_empty_fields(self):
        self.assertEqual(transform([{}, {"fields": None}, {"fields": {}}]), [])

    def test_multiple_shops(self):
        data = transform([row(), row(店铺="店铺乙")])
        self.assertEqual(len(data), 2)
        self.assertEqual([item["店铺"] for item in data], ["示例店铺", "店铺乙"])

    def test_company_separation(self):
        self.assertEqual(len(transform([row(), row(公司名="另一公司")])), 2)

    def test_account_separation(self):
        self.assertEqual(len(transform([row(), row(企业用户名="demo2")])), 2)

    def test_password_separation(self):
        self.assertEqual(len(transform([row(), row(企业密码="DemoDifferent")])), 2)

    def test_password_whitespace(self):
        password = "  Demo\n}|#\t  "
        self.assertEqual(transform([row(企业密码=password)])[0]["企业密码"], password)

    def test_preserve_record_and_site_order(self):
        data = transform([row(), row(站点=[{"name": "日本"}, {"name": "美国"}])])
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["站点"], ["美国"])
        self.assertEqual(data[1]["站点"], ["日本", "美国"])

    def test_duplicate_people(self):
        person = {"unionId": "demo_u1", "name": "负责人甲"}
        data = transform([row(运营负责人=[person, person])])[0]
        self.assertEqual(data["unionId"], ["demo_u1", "demo_u1"])
        self.assertEqual(data["name"], ["负责人甲", "负责人甲"])

    def test_duplicate_records_preserved(self):
        data = transform([row(), row()])
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], data[1])
        self.assertIsNot(data[0], data[1])
        data[0]["站点"].append("日本")
        self.assertEqual(data[1]["站点"], ["美国"])

    def test_duplicate_sites_and_missing_names_preserved(self):
        data = transform([row(站点=[{"name": "美国"}, {"name": "美国"}, {}, {"name": None}])])[0]
        self.assertEqual(data["站点"], ["美国", "美国", "", ""])

    def test_transform_records_entry(self):
        self.assertEqual(transform_records([row()]), transform([row()]))

    def test_changed_person_name(self):
        people = [{"unionId": "demo_u1", "name": "负责人甲"}, {"unionId": "demo_u1", "name": "新名称"}]
        data = transform([row(运营负责人=people)])[0]
        self.assertEqual(data["unionId"], ["demo_u1", "demo_u1"])
        self.assertEqual(data["name"], ["负责人甲", "新名称"])

    def test_partial_people(self):
        people = [{}, {"unionId": "demo_u2"}, {"name": "负责人乙"}]
        data = transform([row(运营负责人=people)])[0]
        self.assertEqual(data["unionId"], ["", "demo_u2", ""])
        self.assertEqual(data["name"], ["", "", "负责人乙"])

    def test_missing_optional(self):
        data = transform([{"fields": {"公司名": "示例公司"}}])[0]
        self.assertEqual(data["企业用户名"], "")
        self.assertEqual(data["企业密码"], "")
        self.assertEqual(data["店铺"], "示例公司")
        self.assertEqual(data["站点"], [])
        self.assertEqual(data["unionId"], [])
        self.assertEqual(data["name"], [])

    def test_null_optional(self):
        data = transform([row(企业用户名=None, 企业密码=None, 站点=None, 运营负责人=None)])[0]
        self.assertEqual(data["企业密码"], "")
        self.assertEqual(data["站点"], [])

    def test_input_unchanged(self):
        data = [row()]
        original = copy.deepcopy(data)
        transform(data)
        self.assertEqual(data, original)

    def test_wrapper_path(self):
        payload = {"data": {"records": [row()]}}
        self.assertEqual(transform(extract_records(payload, ["data", "records"])), transform([row()]))

    def test_missing_path(self):
        with self.assertRaises(ValueError):
            extract_records({}, ["data", "records"])

    def test_invalid_path_type(self):
        for path in ("data.records", [0]):
            with self.subTest(path=path), self.assertRaises(TypeError):
                extract_records({}, path)

    def test_requires_list(self):
        for value in (None, {}, "[]", 1):
            with self.subTest(value=value), self.assertRaises(TypeError):
                transform(value)

    def test_invalid_records(self):
        for value in ([None], [{"fields": []}], [{"fields": {"站点": []}}]):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                transform(value)

    def test_invalid_fields(self):
        for updates in ({"企业密码": 123}, {"站点": "美国"}, {"站点": ["美国"]},
                        {"站点": [{"name": 123}]}, {"运营负责人": {}},
                        {"运营负责人": [1]}, {"运营负责人": [{"unionId": 1}]}):
            with self.subTest(updates=updates), self.assertRaises(TypeError):
                transform([row(**updates)])

    def test_shop_matching_field_name(self):
        for name in ("公司名", "企业用户名", "企业密码", "店铺", "站点", "name", "unionId"):
            with self.subTest(name=name):
                data = transform([row(店铺=name)])[0]
                self.assertEqual(data["店铺"], name)
                self.assertEqual(data["公司名"], "示例公司")
                self.assertEqual(data["站点"], ["美国"])

    def test_shop_data_isolation(self):
        data = transform([row(), row(店铺="示例乙店", 站点=[{"name": "日本"}],
                                    运营负责人=[{"unionId": "demo_u2", "name": "负责人乙"}])])
        self.assertEqual(data[0]["站点"], ["美国"])
        self.assertEqual(data[1]["站点"], ["日本"])
        self.assertEqual(data[0]["unionId"], ["demo_u1"])
        self.assertEqual(data[1]["unionId"], ["demo_u2"])
        data[0]["站点"].append("加拿大")
        self.assertEqual(data[1]["站点"], ["日本"])

    def test_flat_output_contract(self):
        data = transform([row()])[0]
        self.assertEqual(set(data), {"公司名", "企业用户名", "企业密码", "店铺", "站点", "unionId", "name"})
        self.assertFalse(any(isinstance(value, dict) for value in data.values()))

    def test_shop_fallback_variants(self):
        data = transform([row(店铺=None), row(店铺="")])
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["店铺"], "示例公司")
        self.assertEqual(data[1]["店铺"], "示例公司")

    def test_output_schema_fields(self):
        base = Path(__file__).parent
        schema = json.loads((base / "schemas" / "output.schema.json").read_text(encoding="utf-8"))
        keys = {"公司名", "企业用户名", "企业密码", "店铺", "站点", "unionId", "name"}
        self.assertEqual(set(schema["items"]["required"]), keys)
        self.assertEqual(set(schema["items"]["properties"]), keys)
        self.assertIs(schema["items"]["additionalProperties"], False)

    def test_blank_names(self):
        for updates in ({"公司名": " "}, {"店铺": " "}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                transform([row(**updates)])

    def test_no_secret_in_error(self):
        secret = "SECRET_DO_NOT_LOG"
        with self.assertRaises(TypeError) as caught:
            transform([row(企业密码=secret, 站点="bad")])
        self.assertNotIn(secret, str(caught.exception))

    def test_main(self):
        self.assertEqual(main([row()]), {"result": transform([row()])})

    def test_direct_node(self):
        path = Path(__file__).parent / "dingtalk_node.py"
        context = {"iPaas_result": [row()]}
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), context)
        self.assertEqual(context["result"], transform([row()]))

    def test_examples(self):
        base = Path(__file__).parent / "examples"
        source = json.loads((base / "input.json").read_text(encoding="utf-8"))
        expected = json.loads((base / "output.json").read_text(encoding="utf-8"))
        self.assertEqual(transform(source), expected)
        self.assertEqual(len(expected), 8)
        self.assertEqual(expected[0], expected[-1])
        for item in expected:
            self.assertEqual(len(item["unionId"]), len(item["name"]))
        wrapped = json.loads((base / "main_output.json").read_text(encoding="utf-8"))
        self.assertEqual(main(source), wrapped)


if __name__ == "__main__":
    unittest.main()
