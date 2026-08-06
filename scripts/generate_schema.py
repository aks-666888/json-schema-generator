#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON Schema 生成器 —— 确定性产物生成脚本（CodeBuddy Skill: json-schema-generator）

读取模型在"步骤 1"产出的结构化 spec.json，自动生成：
  - schema.json        Draft 2020-12 Schema 主体
  - example.json       必然通过 Schema 的示例实例
  - validation-notes.md 校验说明（必填清单 + 校验命令 + 常见错误）

纯标准库实现，无强依赖。若环境中已安装 jsonschema，则自动启用
Draft 202012Validator 强校验（check_schema + validate）。

用法：
  python generate_schema.py --spec spec.json --out ./out
  python generate_schema.py --spec spec.json            # 输出到当前目录
  cat spec.json | python generate_schema.py -           # 从 stdin 读取
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"

# 各 format 对应的合规占位示例
FORMAT_SAMPLES = {
    "date-time": "2026-08-05T17:00:00Z",
    "date": "2026-08-05",
    "time": "17:00:00",
    "email": "user@example.com",
    "uri": "https://example.com",
    "uuid": "00000000-0000-0000-0000-000000000000",
    "hostname": "example.com",
    "ipv4": "192.168.1.1",
    "ipv6": "2001:db8::1",
}


def build_schema(root):
    """由 spec 递归构造 Draft 2020-12 Schema。"""
    root_type = root.get("rootType", "object")
    schema = {
        "$schema": SCHEMA_URI,
        "title": root.get("title", "GeneratedSchema"),
    }
    if root.get("description"):
        schema["description"] = root["description"]

    if root_type == "array":
        schema["type"] = "array"
        item_root = dict(root)
        item_root["rootType"] = "object"
        item_root.pop("additionalProperties", None)
        schema["items"] = _build_object(item_root)
        for k in ("minItems", "maxItems", "uniqueItems"):
            if k in root:
                schema[k] = root[k]
        return schema

    schema.update(_build_object(root))
    return schema


def _build_object(node):
    """构造一个 object 类型的 Schema 片段。"""
    schema = {"type": "object"}
    props = {}
    required = []
    for f in node.get("fields", []):
        props[f["name"]] = _build_field(f)
        if f.get("required"):
            required.append(f["name"])
    schema["properties"] = props
    if required:
        schema["required"] = required
    if node.get("additionalProperties") is not None:
        schema["additionalProperties"] = node["additionalProperties"]
    if node.get("description"):
        schema["description"] = node["description"]
    return schema


def _build_field(f):
    """构造单个字段的 Schema 片段。"""
    t = f["type"]
    s = {"type": t}
    for k in ("description", "format", "enum", "default", "minimum", "maximum",
              "exclusiveMinimum", "exclusiveMaximum", "minLength", "maxLength",
              "pattern", "minItems", "maxItems", "uniqueItems", "multipleOf",
              "examples"):
        if k in f:
            s[k] = f[k]
    if t == "object":
        s.update(_build_object(f))
    elif t == "array":
        if "items" in f:
            s["items"] = _build_field(f["items"])
        else:
            s["items"] = {"type": "string"}
    return s


def build_example(root):
    """由 spec 递归构造必然合规的示例实例。"""
    if root.get("rootType") == "array":
        item_root = dict(root)
        item_root["rootType"] = "object"
        item_root.pop("additionalProperties", None)
        return [_build_object_example(item_root)]
    return _build_object_example(root)


def _build_object_example(node):
    obj = {}
    for f in node.get("fields", []):
        obj[f["name"]] = _build_field_example(f)
    return obj


def _build_field_example(f):
    t = f["type"]
    if "default" in f:
        return f["default"]
    if t == "string":
        if "enum" in f:
            return f["enum"][0]
        if "format" in f:
            return FORMAT_SAMPLES.get(f["format"], "string")
        if "minLength" in f:
            return "a" * max(1, int(f["minLength"]))
        if "pattern" in f:
            return "abc"
        return "string"
    if t == "integer":
        if "enum" in f:
            return f["enum"][0]
        if "minimum" in f and "maximum" in f:
            return int((f["minimum"] + f["maximum"]) / 2)
        if "minimum" in f:
            return int(f["minimum"])
        if "maximum" in f:
            return int(f["maximum"])
        return 0
    if t == "number":
        if "enum" in f:
            return float(f["enum"][0])
        if "minimum" in f and "maximum" in f:
            return float((f["minimum"] + f["maximum"]) / 2)
        if "minimum" in f:
            return float(f["minimum"])
        if "maximum" in f:
            return float(f["maximum"])
        return 0.0
    if t == "boolean":
        return True
    if t == "null":
        return None
    if t == "array":
        n = max(1, int(f.get("minItems", 1)))
        item = _build_field_example(f["items"]) if "items" in f else "string"
        return [item] * min(n, 2)
    if t == "object":
        return _build_object_example(f)
    return None


def build_notes(root, schema, example):
    """生成校验说明 Markdown。"""
    lines = []
    lines.append(f"# {schema.get('title', 'Schema')} 校验说明\n")
    lines.append(f"> 生成时间：{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}  ")
    lines.append(f"> Schema 版本：{SCHEMA_URI}\n")

    lines.append("## 必填字段清单\n")
    reqs = _collect_required(schema)
    if reqs:
        for r in reqs:
            lines.append(f"- `{r}`")
    else:
        lines.append("- （无必填字段）")
    lines.append("")

    lines.append("## 约束摘要\n")
    lines.append("| 字段 | 类型 | 约束 |")
    lines.append("|------|------|------|")
    for row in _collect_constraints(schema):
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## 校验方式\n")
    lines.append("```bash")
    lines.append("# 依赖：pip install jsonschema")
    lines.append("python -c \"")
    lines.append("import json")
    lines.append("from jsonschema import Draft202012Validator")
    lines.append("schema = json.load(open('schema.json', encoding='utf-8'))")
    lines.append("data = json.load(open('example.json', encoding='utf-8'))")
    lines.append("Draft202012Validator.check_schema(schema)")
    lines.append("Draft202012Validator(schema).validate(data)")
    lines.append("print('OK: example.json 通过 schema.json 校验')")
    lines.append("\"")
    lines.append("```\n")

    lines.append("## 常见错误\n")
    lines.append("- 枚举字段取值越界（不在 `enum` 列表内）；")
    lines.append("- 类型不符（如字符串传给整数 / 数值字段）；")
    lines.append("- 缺少 `required` 中声明的字段；")
    if schema.get("additionalProperties") is False:
        lines.append("- 出现 `properties` 未定义的额外字段（`additionalProperties: false` 会拒绝）；")
    lines.append("- 数值 / 字符串长度超出 `minimum`/`maximum`/`minLength`/`maxLength` 约束；")
    lines.append("- `format` 字段未满足格式要求（如 `email` 缺少 `@`）。")
    return "\n".join(lines)


def _collect_required(schema, prefix=""):
    out = []
    if schema.get("type") == "object" and "properties" in schema:
        for name in schema.get("required", []):
            out.append(prefix + name)
        for name, sub in schema["properties"].items():
            out.extend(_collect_required(sub, prefix + name + "."))
    if schema.get("type") == "array" and "items" in schema:
        out.extend(_collect_required(schema["items"], prefix + "[]"))
    return out


def _collect_constraints(schema, path=""):
    rows = []
    if schema.get("type") == "object" and "properties" in schema:
        for name, sub in schema["properties"].items():
            child = (path + "." + name) if path else name
            rows.extend(_collect_constraints(sub, child))
    elif schema.get("type") == "array" and "items" in schema:
        rows.extend(_collect_constraints(schema["items"], path + "[]"))
    else:
        constraints = []
        for k in ("format", "enum", "minimum", "maximum", "minLength",
                 "maxLength", "pattern", "minItems", "maxItems"):
            if k in schema:
                constraints.append(f"{k}={schema[k]}")
        t = schema.get("type", "—")
        rows.append([path or "(root)", t, "；".join(constraints) if constraints else "—"])
    return rows


def main():
    ap = argparse.ArgumentParser(description="JSON Schema 生成器：spec -> schema/example/notes")
    ap.add_argument("--spec", required=True, help="spec.json 路径，或 '-' 表示从 stdin 读取")
    ap.add_argument("--out", default=".", help="输出目录，默认当前目录")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.spec == "-" else open(args.spec, encoding="utf-8").read()
    root = json.loads(raw)

    schema = build_schema(root)
    example = build_example(root)
    notes = build_notes(root, schema, example)

    os.makedirs(args.out, exist_ok=True)
    schema_path = os.path.join(args.out, "schema.json")
    example_path = os.path.join(args.out, "example.json")
    notes_path = os.path.join(args.out, "validation-notes.md")

    with open(schema_path, "w", encoding="utf-8") as fh:
        json.dump(schema, fh, ensure_ascii=False, indent=2)
    with open(example_path, "w", encoding="utf-8") as fh:
        json.dump(example, fh, ensure_ascii=False, indent=2)
    with open(notes_path, "w", encoding="utf-8") as fh:
        fh.write(notes)

    # 可选强校验
    try:
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(example)
        print(f"[OK] 强校验通过：{schema_path} / {example_path}")
    except ImportError:
        print("[INFO] 未安装 jsonschema，跳过强校验（仅完成产物生成）。")
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] 强校验未通过：{e}")
        return 1

    print(f"[DONE] 已生成：\n  - {schema_path}\n  - {example_path}\n  - {notes_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
