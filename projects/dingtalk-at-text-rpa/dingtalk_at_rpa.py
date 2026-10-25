"""
影刀 RPA 自定义指令：钉钉企业内部机器人群聊 @人（Text 消息）

用法：在影刀「自定义指令」里新建指令集，添加 Python 模块，把本文件内容粘进去即可。
函数 docstring 里的 `* @param` / `* @return` 会被影刀识别为指令的输入/输出参数。

只用 Python 标准库（urllib），不需要在影刀里额外 pip 安装 requests。
"""
import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse

# sessionWebhook 只允许钉钉官方域名，避免把消息发到其它地址
_ALLOWED_HOSTS = {"oapi.dingtalk.com", "api.dingtalk.com"}


def _to_list(value):
    """把 None / 字符串（逗号、空格、换行分隔）/ 列表 统一成去空白的字符串列表。"""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = re.split(r"[,，;；\s]+", str(value))
    return [str(i).strip() for i in items if str(i).strip()]


def _to_bool(value):
    """影刀界面传来的开关可能是字符串，如 "False"；直接 bool("False") 会得到 True，所以单独处理。"""
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y", "是")
    return bool(value)


def _build_text_message(content, user_ids=None, mobiles=None, at_all=False):
    """
    构造钉钉 Text 消息体。文档要求：正文里要带上 "@userid" / "@手机号"，
    并与 at 字段结合使用，才有 @ 高亮效果。
    """
    user_ids = _to_list(user_ids)
    mobiles = _to_list(mobiles)
    mention = " ".join([f"@{u}" for u in user_ids] + [f"@{m}" for m in mobiles])
    prefix = f" {mention}  \n  " if mention else ""
    return {
        "msgtype": "text",
        "text": {"content": prefix + str(content)},
        "at": {"atMobiles": mobiles, "atUserIds": user_ids, "isAtAll": _to_bool(at_all)},
    }


def send_text_at(session_webhook, content, at_user_ids=None, at_mobiles=None, at_all=False) -> dict:
    """
    钉钉群聊发送文本消息并@人
    * @param session_webhook,机器人回调消息里的 sessionWebhook 地址（钉钉域名）
    * @param content,要发送的文本内容
    * @param at_user_ids,被@人的 userid，多个用逗号分隔或传列表（回调里的 senderStaffId）
    * @param at_mobiles,被@人的手机号，多个用逗号分隔或传列表
    * @param at_all,是否@所有人，True 或 False
    * @return `result` , 钉钉接口返回的结果（字典，errcode 为 0 表示成功）
    """
    session_webhook = str(session_webhook or "").strip()
    if urlparse(session_webhook).hostname not in _ALLOWED_HOSTS:
        raise ValueError("session_webhook 不是有效的钉钉地址: %s" % session_webhook)
    if not str(content or "").strip():
        raise ValueError("content 不能为空")

    payload = _build_text_message(content, at_user_ids, at_mobiles, at_all)
    request = urllib.request.Request(
        session_webhook,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError("请求钉钉失败: %s" % e)

    if result.get("errcode", 0) != 0:
        raise RuntimeError("钉钉返回错误: %s" % result)
    return result


if __name__ == "__main__":
    # 本地自测：只打印消息体，不发请求
    print(json.dumps(_build_text_message("测试@人员效果", "user123, user456", None, "False"), ensure_ascii=False, indent=2))
