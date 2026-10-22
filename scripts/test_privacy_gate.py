import hashlib
import json
import unittest

from privacy_gate import scan, scan_text


class PrivacyTests(unittest.TestCase):
    def test_demo_json(self):
        value = {"公司名": "示例公司", "企业用户名": "demo_account", "企业密码": "DemoOnly#", "站点": [{"name": "美国"}], "运营负责人": [{"unionId": "demo_u01", "name": "负责人甲"}]}
        self.assertEqual(scan_text(json.dumps(value, ensure_ascii=False).encode()), set())

    def test_secret_field(self):
        value = "Real" + "Credential123!"
        findings = scan_text(json.dumps({"企业密码": value}, ensure_ascii=False).encode())
        self.assertIn("non-placeholder-sensitive-field", findings)

    def test_token(self):
        value = "ghp_" + "A" * 36
        self.assertIn("github-token", scan_text(value.encode()))

    def test_personal_contact(self):
        value = "138" + "12345678"
        self.assertIn("cn-mobile", scan_text(value.encode()))

    def test_real_business_data(self):
        self.assertIn("non-demo-business-data", scan_text(json.dumps({"公司名": "某真实业务名称"}, ensure_ascii=False).encode()))

    def test_demo_email(self):
        self.assertEqual(scan_text(b"demo@example.com"), set())

    def test_blocked_file(self):
        self.assertIn("blocked-file-type", scan(".env", b"demo", {}))

    def test_binary_unreviewed(self):
        self.assertIn("binary-requires-manual-redaction-review", scan("docs/demo.png", b"demo", {}))

    def test_binary_review(self):
        data = b"demo"
        reviews = {"docs/demo.png": {"sha256": hashlib.sha256(data).hexdigest(), "redacted": True, "reviewed_by": "reviewer-01", "reviewed_at": "2026-10-22"}}
        self.assertEqual(scan("docs/demo.png", data, reviews), set())
        self.assertIn("binary-requires-manual-redaction-review", scan("docs/demo.png", data + b"changed", reviews))

    def test_archive_blocked(self):
        self.assertIn("archive-not-allowed-store-extracted-files", scan("docs/demo.zip", b"demo", {}))


if __name__ == "__main__":
    unittest.main()
