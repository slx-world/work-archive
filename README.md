# 工作代码与资料归档

记录日常工作中的代码、示例数据、使用说明和可复用资料。资料按项目归档，所有文件在推送前完成脱敏。

## 已归档项目

| 项目 | 内容 |
| --- | --- |
| [钉钉多行记录转换](projects/dingtalk-record-transform/) | 每条有效原始记录对应一条平铺记录，含 Python 代码、脱敏 JSON 示例、格式定义、Word 和 TXT 说明、验收测试 |

## 目录约定

- `projects/` 保存每个任务的代码、示例数据和项目文档。
- `docs/` 保存跨项目的说明和工作方法。
- `scripts/` 保存仓库维护脚本。
- `policy/` 保存脱敏规则及不可自动读取文件的人工复核记录。
- `templates/` 保存新任务归档模板。

## 开始使用

需要 Git 和 Python 3.8 或更新版本。每个新的克隆都要启用本地 hook：

```bash
git config core.hooksPath .githooks
python scripts/privacy_gate.py --all
```

首次归档项目的测试命令：

```bash
python -m unittest discover -s projects/dingtalk-record-transform -v
```

## 每次提交和推送

先将业务数据替换为虚构值，再查看 `git diff --cached`。本地 pre-commit 检查实际暂存内容，pre-push 检查即将上传的提交历史；GitHub Actions 作为上传后的补充检查。

```bash
git add <本次已脱敏的文件>
python scripts/privacy_gate.py --staged
git commit -m "说明本次归档内容"
python scripts/privacy_gate.py --history
git push
```

不要提交真实凭据、人员标识或原始业务附件。自动扫描覆盖常见模式，不能代替人工脱敏。详情见 [脱敏规则](policy/REDACTION.md) 和 [代理工作规则](AGENTS.md)。
