"""提交前敏感信息检查。仅输出文件路径和规则名，不输出匹配到的内容。"""
import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".xml", ".csv",
    ".tsv", ".js", ".ts", ".html", ".css", ".sh", ".ps1", ".bat", ".ini",
    ".cfg", ".sql", ".rst", ".example", ".gitignore", ".gitattributes",
}
RULES = [
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b")),
    ("aws-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("bearer-token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b", re.I)),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("cn-mobile", re.compile(r"(?<![\w])(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")),
    ("cn-id-card", re.compile(r"(?<!\w)[1-9]\d{5}(?:19|20)\d{2}[01]\d[0-3]\d\d{3}[0-9Xx](?!\w)")),
    ("credential-in-url", re.compile(r"https?://[^\s/:@]+:[^\s/@]+@", re.I)),
    ("dingtalk-real-union-id", re.compile(r"[A-Za-z0-9]{12,}iEiE\b")),
    ("email", re.compile(r"[\w.+-]+@([\w.-]+\.[A-Za-z]{2,})")),
]
ASSIGNMENT = re.compile(
    r'''(?:["']?)(企业密码|企业用户名|unionId|password|passwd|pwd|token|secret|api_key|access_key)(?:["']?)\s*[:=]\s*(["'])([^\r\n]*?)\2''',
    re.I,
)
BLOCKED_NAMES = {".env", "credentials.json", "hosts.yml", "id_rsa", "id_ed25519"}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".log"}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def placeholder(value):
    value = value.strip().lower()
    return not value or value.startswith(("demo", "test", "example", "sample", "fake", "redacted", "changeme", "placeholder", "<", "${", "{{", "示例", "测试", "已脱敏")) or value in {"***", "...", "secret_do_not_log"}


def scan_text(data):
    text = data.decode("utf-8-sig")
    findings = set()
    for rule, regex in RULES:
        for match in regex.finditer(text):
            if rule == "email" and match.group(1).lower() in {"example.com", "example.org", "example.net"}:
                continue
            findings.add(rule)
    for match in ASSIGNMENT.finditer(text):
        if not placeholder(match.group(3)):
            findings.add("non-placeholder-sensitive-field")
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return findings

    def walk(value, parent=""):
        if isinstance(value, dict):
            for key, child in value.items():
                sensitive = key in {"公司名", "企业用户名", "企业密码", "unionId"}
                sensitive = sensitive or (key == "name" and ("unionId" in value or parent == "运营负责人" or isinstance(child, list)))
                if sensitive:
                    if isinstance(child, str) and not placeholder(child) and not child.startswith("负责人"):
                        findings.add("non-demo-business-data")
                    if isinstance(child, list):
                        for item in child:
                            if isinstance(item, str) and not placeholder(item) and not item.startswith("负责人"):
                                findings.add("non-demo-business-data")
                walk(child, key)
        elif isinstance(value, list):
            for child in value:
                walk(child, parent)
    walk(parsed)
    return findings


def scan(path, data, reviews):
    normalized = path.replace("\\", "/")
    name = Path(normalized).name.lower()
    suffix = Path(normalized).suffix.lower()
    digest = hashlib.sha256(data).hexdigest()
    if name in BLOCKED_NAMES or (name.startswith(".env.") and not name.endswith(".example")) or suffix in BLOCKED_SUFFIXES:
        return {"blocked-file-type"}
    # 人工复核只能用于图像等无法自动读取的二进制，不豁免文本和可读文档。
    if suffix == ".docx":
        findings = set()
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for info in archive.infolist():
                    if info.file_size > 20_000_000:
                        findings.add("oversized-document-member")
                        continue
                    if info.filename.startswith(("word/media/", "word/embeddings/")):
                        findings.add("document-requires-manual-redaction-review")
                    if info.filename.endswith((".xml", ".rels")):
                        findings.update(scan_text(archive.read(info)))
        except (zipfile.BadZipFile, UnicodeDecodeError):
            findings.add("unreadable-document")
        return findings
    if suffix == ".zip":
        return {"archive-not-allowed-store-extracted-files"}
    if suffix in TEXT_SUFFIXES or name in {"pre-commit", "pre-push", ".gitignore", ".gitattributes"}:
        try:
            return scan_text(data)
        except UnicodeDecodeError:
            return {"non-utf8-text"}
    entry = reviews.get(normalized, {})
    if isinstance(entry, dict) and entry.get("sha256") == digest and entry.get("redacted") is True and entry.get("reviewed_by") and entry.get("reviewed_at"):
        return set()
    return {"binary-requires-manual-redaction-review"}


def check(blobs, reviews):
    count = 0
    failures = []
    seen = set()
    for path, data in blobs:
        signature = (path, hashlib.sha256(data).digest())
        if signature in seen:
            continue
        seen.add(signature)
        count += 1
        rules = scan(path, data, reviews)
        if rules:
            failures.append((path, ", ".join(sorted(rules))))
    for path, rules in failures:
        print("BLOCK " + path + " [" + rules + "]", file=sys.stderr)
    print("Privacy check: " + str(count) + " file versions; " + str(len(failures)) + " blocked.")
    return 1 if failures else 0


def tree_blobs(ref):
    for entry in git("ls-tree", "-r", "-z", ref).split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        mode, kind, sha = meta.split()
        name = path.decode("utf-8")
        if kind != b"blob" or mode == b"120000":
            yield name, b"UNSUPPORTED_BINARY"
            continue
        yield name, git("cat-file", "blob", sha.decode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="扫描 Git 已跟踪文件的工作区内容")
    mode.add_argument("--staged", action="store_true", help="扫描暂存区实际内容")
    mode.add_argument("--history", action="store_true", help="扫描所有本地可达提交的文件版本")
    mode.add_argument("--pre-push", action="store_true", help="从 Git hook 标准输入读取待推送范围")
    args = parser.parse_args()
    review_file = ROOT / "policy" / "manual-reviews.json"
    reviews = json.loads(review_file.read_text(encoding="utf-8")) if review_file.exists() else {}
    if args.all:
        paths = git("ls-files", "-z").split(b"\0")
        return check(((p.decode("utf-8"), (ROOT / p.decode("utf-8")).read_bytes()) for p in paths if p and (ROOT / p.decode("utf-8")).is_file()), reviews)
    if args.staged:
        paths = git("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z").split(b"\0")
        return check(((p.decode("utf-8"), git("show", ":" + p.decode("utf-8"))) for p in paths if p), reviews)
    commits = set()
    if args.history:
        commits.update(git("rev-list", "--all").decode().splitlines())
    else:
        for line in sys.stdin:
            local_ref, local_sha, remote_ref, remote_sha = line.split()
            if local_sha == "0" * 40:
                continue
            # 新建远端分支检查完整本地历史；已有分支检查新增范围。
            revs = [local_sha] if remote_sha == "0" * 40 else [local_sha, "^" + remote_sha]
            commits.update(git("rev-list", *revs).decode().splitlines())
    return check((blob for commit in sorted(commits) for blob in tree_blobs(commit)), reviews)


if __name__ == "__main__":
    sys.exit(main())
