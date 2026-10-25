"""
钉钉企业内部机器人：群聊 @人（Text 消息，Webhook / sessionWebhook 方式）
对照文档《企业内部机器人群聊实现@人接入指南》实现。

流程：用户在企业内部群 @机器人 -> 钉钉 POST 到「消息接收地址」-> 取 senderStaffId 和 sessionWebhook
      -> 构造 Text 消息 -> POST 到 sessionWebhook，被 @ 的人即为发消息的人

依赖：pip install flask requests
运行：python dingtalk_at.py   （默认监听 8090，路径 /robots）

测试触发词（与文档示例一致，空格会被去掉后再比较）：Text@人员效果

注意：必须在「企业内部群」里测试。开发者后台点“调试”进入的测试群拿不到 senderStaffId。
"""
from urllib.parse import urlparse

import requests
from flask import Flask, request

app = Flask(__name__)

# sessionWebhook 来自请求体，转发前限制域名，避免被伪造请求利用去访问任意地址
ALLOWED_WEBHOOK_HOSTS = {"oapi.dingtalk.com", "api.dingtalk.com"}


def build_text(content, user_ids=None, mobiles=None, at_all=False):
    """
    构造 Text 消息，被 @ 人员高亮显示。
    文档要求：content 里要带上 "@userid"（或 "@手机号"），并与 at 字段结合使用，才有 @ 效果。
    """
    user_ids = list(user_ids or [])
    mobiles = list(mobiles or [])
    mention = " ".join([f"@{u}" for u in user_ids] + [f"@{m}" for m in mobiles])
    prefix = f" {mention}  \n  " if mention else ""
    return {
        "msgtype": "text",
        "text": {"content": prefix + content},
        "at": {"atMobiles": mobiles, "atUserIds": user_ids, "isAtAll": bool(at_all)},
    }


def send_by_session_webhook(session_webhook, payload):
    host = urlparse(session_webhook).hostname
    if host not in ALLOWED_WEBHOOK_HOSTS:
        raise ValueError(f"不允许的 sessionWebhook 域名: {host}")
    resp = requests.post(session_webhook, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"钉钉返回错误: {data}")
    return data


@app.post("/robots")
def robots():
    body = request.get_json(silent=True) or {}
    content = body.get("text", {}).get("content", "").replace(" ", "")
    user_id = body.get("senderStaffId")  # 发消息人的 userId
    session_webhook = body.get("sessionWebhook")

    if content == "Text@人员效果" and user_id and session_webhook:
        try:
            payload = build_text("测试@人员效果", user_ids=[user_id])
            print(send_by_session_webhook(session_webhook, payload))
        except Exception as e:  # 示例里只打印，生产环境请接入日志/告警
            print("发送失败:", e)
    return ""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
