"""dingtalk_at_rpa / dingtalk_at_rpa_requests 的离线测试：不发真实网络请求。"""
import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dingtalk_at_rpa as rpa

try:
    import requests
    import dingtalk_at_rpa_requests as rpa_req
except ImportError:  # 未安装 requests 时跳过 requests 版测试
    requests = None
    rpa_req = None

HOOK = "https://oapi.dingtalk.com/robot/sendBySession?session=demo_session"


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class BuildMessageTests(unittest.TestCase):
    def test_at_users_and_string_switch(self):
        msg = rpa._build_text_message("你好", "demo_u01, demo_u02", None, "False")
        self.assertEqual(msg["at"]["atUserIds"], ["demo_u01", "demo_u02"])
        self.assertIs(msg["at"]["isAtAll"], False)  # 字符串 "False" 不能被当成 True
        self.assertTrue(msg["text"]["content"].startswith(" @demo_u01 @demo_u02"))

    def test_at_all_true_string(self):
        self.assertIs(rpa._build_text_message("x", None, None, "是")["at"]["isAtAll"], True)

    def test_no_mention_prefix(self):
        self.assertEqual(rpa._build_text_message("x")["text"]["content"], "x")

    def test_matches_example_file(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "examples", "text_message.json"), encoding="utf-8") as f:
            example = json.load(f)
        msg = rpa._build_text_message("测试@人员效果", ["demo_u01", "demo_u02"])
        self.assertEqual(msg["text"], example["text"])
        self.assertEqual(msg["at"], example["at"])


class SendTests(unittest.TestCase):
    def test_rejects_non_dingtalk_host(self):
        with self.assertRaises(ValueError):
            rpa.send_text_at("https://example.com/x", "hi")

    def test_rejects_empty_content(self):
        with self.assertRaises(ValueError):
            rpa.send_text_at(HOOK, "  ")

    def test_success(self):
        with mock.patch("urllib.request.urlopen", return_value=FakeResp(b'{"errcode":0,"errmsg":"ok"}')):
            self.assertEqual(rpa.send_text_at(HOOK, "hi", "demo_u01")["errcode"], 0)

    def test_errcode(self):
        with mock.patch("urllib.request.urlopen", return_value=FakeResp(b'{"errcode":310000,"errmsg":"bad"}')):
            with self.assertRaises(RuntimeError):
                rpa.send_text_at(HOOK, "hi")

    def test_network_error(self):
        import urllib.error
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
            with self.assertRaises(RuntimeError):
                rpa.send_text_at(HOOK, "hi")


@unittest.skipIf(requests is None, "requests 未安装")
class RequestsVersionTests(unittest.TestCase):
    def test_success(self):
        resp = mock.Mock()
        resp.json.return_value = {"errcode": 0}
        with mock.patch("requests.post", return_value=resp) as post:
            self.assertEqual(rpa_req.send_text_at(HOOK, "hi", "demo_u01"), {"errcode": 0})
            self.assertEqual(post.call_args.kwargs["json"]["at"]["atUserIds"], ["demo_u01"])

    def test_http_error(self):
        resp = mock.Mock()
        resp.raise_for_status.side_effect = requests.HTTPError("500")
        with mock.patch("requests.post", return_value=resp):
            with self.assertRaises(RuntimeError):
                rpa_req.send_text_at(HOOK, "hi")

    def test_rejects_non_dingtalk_host(self):
        with self.assertRaises(ValueError):
            rpa_req.send_text_at("https://example.com/x", "hi")


if __name__ == "__main__":
    unittest.main()
