"""本地验收测试；仅使用 Python 标准库。运行 python -m unittest -v。"""
import copy
import json
from pathlib import Path
import unittest

from dingtalk_transform import extract_records, main, transform


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
        self.assertEqual(data["示例店铺"], {"站点": ["美国"], "unionId": ["demo_u1"], "name": ["负责人甲"]})

    def test_empty(self):
        self.assertEqual(transform([]), [])

    def test_empty_fields(self):
        self.assertEqual(transform([{}, {"fields": None}, {"fields": {}}]), [])

    def test_multiple_shops(self):
        data = transform([row(), row(店铺="店铺乙")])
        self.assertEqual(len(data), 1)
        self.assertIn("店铺乙", data[0])

    def test_company_separation(self):
        self.assertEqual(len(transform([row(), row(公司名="另一公司")])), 2)

    def test_account_separation(self):
        self.assertEqual(len(transform([row(), row(企业用户名="demo2")])), 2)

    def test_password_separation(self):
        self.assertEqual(len(transform([row(), row(企业密码="DemoDifferent")])), 2)

    def test_password_whitespace(self):
        password = "  Demo\n}|#\t  "
        self.assertEqual(transform([row(企业密码=password)])[0]["企业密码"], password)

    def test_merge_and_order(self):
        data = transform([row(), row(站点=[{"name": "日本"}, {"name": "美国"}])])
        self.assertEqual(data[0]["示例店铺"]["站点"], ["美国", "日本"])

    def test_duplicate_people(self):
        data = transform([row(), row()])[0]["示例店铺"]
        self.assertEqual(data["unionId"], ["demo_u1"])

    def test_changed_person_name(self):
        people = [{"unionId": "demo_u1", "name": "负责人甲"}, {"unionId": "demo_u1", "name": "新名称"}]
        data = transform([row(运营负责人=people)])[0]["示例店铺"]
        self.assertEqual(data["unionId"], ["demo_u1", "demo_u1"])
        self.assertEqual(data["name"], ["负责人甲", "新名称"])

    def test_partial_people(self):
        people = [{}, {"unionId": "demo_u2"}, {"name": "负责人乙"}]
        data = transform([row(运营负责人=people)])[0]["示例店铺"]
        self.assertEqual(data["unionId"], ["demo_u2", ""])
        self.assertEqual(data["name"], ["", "负责人乙"])

    def test_missing_optional(self):
        data = transform([{"fields": {"公司名": "示例公司"}}])[0]
        self.assertEqual(data["企业用户名"], "")
        self.assertEqual(data["企业密码"], "")
        self.assertEqual(data["示例公司"], {"站点": [], "unionId": [], "name": []})

    def test_null_optional(self):
        data = transform([row(企业用户名=None, 企业密码=None, 站点=None, 运营负责人=None)])[0]
        self.assertEqual(data["企业密码"], "")
        self.assertEqual(data["示例店铺"]["站点"], [])

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

    def test_reserved_shop(self):
        for name in ("公司名", "企业用户名", "企业密码"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                transform([row(店铺=name)])

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
        self.assertEqual(len(expected), 5)
        self.assertEqual(sum(len(x) - 3 for x in expected), 7)


if __name__ == "__main__":
    unittest.main()
