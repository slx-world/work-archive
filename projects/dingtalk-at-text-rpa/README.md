# 钉钉群聊发送文本并 @人（影刀 RPA 指令）

在钉钉企业内部机器人的群聊回调里，用 `sessionWebhook` 发送 Text 消息并 @ 指定的人。封装成影刀可复用的自定义指令 `send_text_at`。

## 目录

```text
dingtalk-at-text-rpa/
├── dingtalk_at_rpa.py            # 影刀指令（推荐）：仅用标准库 urllib
├── dingtalk_at_rpa_requests.py   # 同功能，改用 requests（需在影刀里安装 requests）
├── server/dingtalk_at_server.py  # Flask 回调服务示例，用于理解 @人 流程，非影刀必需
├── test_dingtalk_at.py           # 离线测试（不发真实请求）
├── examples/text_message.json    # 消息体示例（虚构 userid）
├── data/影刀调用模块_参数与步骤.xlsx  # 调用模块的参数对照与操作步骤清单
└── docs/使用说明.md
```

## 输入输出

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `session_webhook` | 是 | 机器人回调里的 sessionWebhook，仅允许 `oapi.dingtalk.com`、`api.dingtalk.com` |
| `content` | 是 | 文本内容，不能为空 |
| `at_user_ids` | 否 | 被 @ 人的 userid，逗号/空格分隔或列表（回调里的 `senderStaffId`） |
| `at_mobiles` | 否 | 被 @ 人的手机号，格式同上 |
| `at_all` | 否 | 是否 @ 所有人；支持 `"False"`、`"是"` 等字符串 |
| 返回值 `result` | | 钉钉返回的字典，`errcode` 为 0 表示成功；失败抛出异常 |

## 使用方式

把 `dingtalk_at_rpa.py` 粘进影刀自定义指令集的 Python 模块，再按 `docs/使用说明.md` 配置指令输入输出。

```python
from dingtalk_at_rpa import send_text_at
result = send_text_at(session_webhook, "测试@人员效果", at_user_ids="demo_u01,demo_u02")
```

## 验证结果

```bash
python -m unittest discover -s projects/dingtalk-at-text-rpa -v
```

12 个离线测试通过（requests 未安装时 requests 版测试自动跳过）。测试使用 mock，**没有**对真实钉钉接口发过请求；影刀内的配置流程由使用者在界面上完成并反馈可用，但未在本仓库中自动化验证。

## 已知限制

- 只有 Text 消息有 @ 高亮效果。
- `senderStaffId` 仅在企业内部群中可获取，开发者后台“调试”群拿不到。
- sessionWebhook 有时效，不能长期保存复用。
- 域名白名单是按常见钉钉域名设定的，若钉钉返回其他域名需调整 `_ALLOWED_HOSTS`。

## 脱敏记录

示例中的 userid、webhook、session 均为虚构占位值（demo 前缀）；未包含真实 sessionWebhook、userid、手机号或群信息。Excel 与说明文档只含通用参数说明。详见 `policy/本次资料更新脱敏记录.txt` 的钉钉 @人 部分。
