---
name: json-schema-generator
description: 根据自然语言描述的数据结构，自动生成符合 JSON Schema Draft 2020-12 的 Schema、符合 Schema 的示例数据，以及面向工程落地的校验说明。当用户需要"把数据结构描述转成 JSON Schema""为接口请求/响应设计校验规则""为配置文件或表单生成 Schema""校验某段 JSON 是否满足约定结构"时使用本技能。
agent_created: true
version: "1.0.0"
---

# JSON Schema 生成器

## 概述

本技能将用户对数据结构的自然语言描述（例如"一个用户，有 id、邮箱、角色……"）转化为三件可直接使用的产物：

1. **JSON Schema**（严格遵循 [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema)）；
2. **示例数据**（一段必然通过 Schema 校验的 JSON 实例）；
3. **校验说明**（字段约束清单 + 如何在项目中落地校验的操作指引）。

适用场景：
- 设计 REST / RPC 接口的请求体（request）与响应体（response）校验规则；
- 为配置文件（如 `*.json`、由 `*.yaml` 转出的 JSON）编写 Schema，借助编辑器获得自动补全与报错；
- 生成前端表单的校验规则或后端 DTO 约束；
- 把产品文档、PRD 里的字段表翻译成机器可校验的契约；
- 校验已存在的 JSON 文本是否满足既定结构（反向用例）。

不适用场景：
- 需要 XML Schema / Protobuf / GraphQL 等其他契约格式时，本技能不覆盖；
- 涉及复杂跨文档远程 `$ref` 解析、超大规模 Schema 拆分时，需人工补充；本技能只保证**单文件** Draft 2020-12 合规。

## 工作流定义

按以下顺序执行。步骤 1 由模型完成语义解析；步骤 2–5 产出并校验产物；当请求简单（单一扁平对象）时可跳过脚本直接产出，但仍须完成步骤 6 自检。

### 步骤 1：解析自然语言为结构化字段表

从用户描述中抽取每个字段的以下属性，缺失项使用合理默认值并在产出中标注：

| 属性 | 含义 | 默认 |
|------|------|------|
| `name` | 字段名（camelCase 或业务约定，保留原样） | 必填，无默认 |
| `type` | `string` / `number` / `integer` / `boolean` / `object` / `array` / `null` | 必填，无默认 |
| `required` | 是否必填 | 默认 `false`（除非描述为"必须/一定/每个都有"） |
| `description` | 字段说明 | 默认空 |
| `format` | `date-time` / `email` / `date` / `uri` / `uuid` 等 | 可选 |
| `enum` | 枚举值集合 | 可选 |
| `default` | 默认值 | 可选 |
| `minimum` / `maximum` / `minLength` / `maxLength` / `pattern` / `minItems` / `maxItems` / `uniqueItems` | 约束 | 可选 |
| `items` | `array` 的元素 Schema | `type=array` 时必填 |
| `properties` | `object` 的嵌套字段表 | `type=object` 时必填 |

识别嵌套：`object` 字段可递归包含字段表；`array` 字段通过 `items` 描述元素结构。把"列表/数组/多个"等表述映射为 `array`。

### 步骤 2：确定根形态

依据描述选择根 Schema 形态之一：
- **单对象**：根为 `type: object`（最常见）；
- **数组包裹**：根为 `type: array`，`items` 为元素对象（如"返回用户列表"）；
- **配置 / 文档**：根为 `object`，顶层用 `additionalProperties: false` 收紧未知字段；
- **请求 / 响应对**：分别生成 `request.schema.json` 与 `response.schema.json` 两个文件。

### 步骤 3：生成 JSON Schema（Draft 2020-12）

严格使用 Draft 2020-12 关键字（见 `references/draft2020-12-keywords.md`）。核心规则：
- 根对象必须声明 `"$schema": "https://json-schema.org/draft/2020-12/schema"`；
- 顶层 `object` 用 `properties` 定义字段，用 `required` 数组列出必填项；
- 枚举用 `enum`；字符串格式用 `format`；数值范围用 `minimum` / `maximum`；字符串长度用 `minLength` / `maxLength`；正则用 `pattern`；
- 不允许使用已废弃关键字（`definitions` 改用 `$defs`，`id` 改用 `$id`，`exclusiveMinimum` 等保持数值语义）；
- 复用结构用 `$defs` + `$ref: "#/$defs/xxx"`，不要跨文件 `$ref`。

### 步骤 4：生成示例数据

构造一段 JSON，使每个字段都取到符合类型与约束的代表值：
- `enum` → 取第一个枚举值；
- `format` → 取合规字面量（`email` 取 `"user@example.com"`，`date-time` 取 `"2026-08-05T17:00:00Z"` 等）；
- `minimum` / `maximum` → 取区间内中值；`minLength` / `maxLength` → 取满足最小长度；
- `array` → 含 1–2 个合规元素；`object` → 递归填充；
- 布尔取 `true`，数值取 `0` 或区间内值，字符串取有意义占位。

示例数据**必须**能通过步骤 3 的 Schema（步骤 6 验证）。

### 步骤 5：生成校验说明

输出一份面向工程落地的清单：
- **必填字段清单**：列出所有 `required` 字段；
- **约束摘要**：逐字段写清类型、范围、格式、枚举；
- **校验方式**：给出一段可复制的校验命令（见下方"校验方式"模板）；
- **常见错误**：枚举越界、类型不符、缺少必填、`additionalProperties` 多余字段等。

### 步骤 6：自检（必做）

逐项核对，任一项不通过则回到对应步骤修正：
1. `$schema` 指向 Draft 2020-12；
2. 每个 `required` 项都存在于 `properties`；
3. `array` 有 `items`，`object` 嵌套已展开；
4. 示例数据用 `jsonschema` 库或在线校验器验证通过；
5. 无废弃关键字、无跨文件 `$ref`。

## 输入输出约束

**输入**
- 自然语言描述，或字段表 / PRD 片段 / 现有 JSON 样本（反向推断结构时）；
- 可选约束：目标形态（单对象 / 数组 / 请求响应对）、是否收紧 `additionalProperties`、是否输出多语言注释。

**输出**
- 至少三件产物，按以下命名：
  - `schema.json`：Draft 2020-12 Schema 主体；
  - `example.json`：合规示例实例；
  - `validation-notes.md`：校验说明（必填清单 + 校验命令 + 常见错误）。
- 代码块内 JSON Schema 关键字与 camelCase 字段名**保留英文**；说明文字使用简体中文。
- Schema 必须可被标准 Draft 2020-12 校验器解析，示例必须可通过校验。

**校验方式模板**（写入 `validation-notes.md`）：

```bash
# 依赖：pip install jsonschema
python -c "
import json, jsonschema
from jsonschema import Draft202012Validator
schema = json.load(open('schema.json', encoding='utf-8'))
data = json.load(open('example.json', encoding='utf-8'))
Draft202012Validator.check_schema(schema)   # 校验 Schema 自身合法性
Draft202012Validator(schema).validate(data) # 校验示例数据
print('OK: example.json 通过 schema.json 校验')
"
```

也可调用本技能附带的脚本，先由模型产出 `spec.json`（步骤 1 的结构化结果），再一键生成并校验全部产物：

```bash
python scripts/generate_schema.py --spec spec.json --out ./out
```

## 示例模板

### 示例 1：用户对象（单对象 + 枚举 + 嵌套）

用户自然语言输入：
> "定义一个用户，必须有 id（整数）、email（邮箱格式，必须）、name（字符串）；role 只能是 admin 或 user，默认 user；tags 是字符串数组；profile 里含 age（整数，0–120）和 city（字符串）。"

产出 `schema.json`：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "User",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "email", "name"],
  "properties": {
    "id": { "type": "integer", "description": "用户唯一标识" },
    "email": { "type": "string", "format": "email", "description": "登录邮箱" },
    "name": { "type": "string", "minLength": 1 },
    "role": { "type": "string", "enum": ["admin", "user"], "default": "user" },
    "tags": { "type": "array", "items": { "type": "string" } },
    "profile": {
      "type": "object",
      "required": ["age"],
      "properties": {
        "age": { "type": "integer", "minimum": 0, "maximum": 120 },
        "city": { "type": "string" }
      }
    }
  }
}
```

产出 `example.json`：

```json
{
  "id": 1001,
  "email": "user@example.com",
  "name": "张三",
  "role": "user",
  "tags": ["vip", "active"],
  "profile": { "age": 28, "city": "杭州" }
}
```

### 示例 2：订单列表接口（数组根 + 请求 / 响应）

用户自然语言输入：
> "订单列表接口：请求体含 page（整数，默认 1）、pageSize（整数 1–100，默认 20）；响应是订单数组，每个订单有 orderId（字符串）、amount（数字 ≥ 0）、status（枚举 pending/paid/shipped）、createdAt（date-time），以及 items 数组，元素含 sku（字符串）和 qty（整数 ≥ 1）。"

请求 `request.schema.json`（节选）：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OrderListRequest",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "page": { "type": "integer", "minimum": 1, "default": 1 },
    "pageSize": { "type": "integer", "minimum": 1, "maximum": 100, "default": 20 }
  }
}
```

响应 `response.schema.json`（节选，根为数组）：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OrderListResponse",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["orderId", "amount", "status", "createdAt", "items"],
    "properties": {
      "orderId": { "type": "string" },
      "amount": { "type": "number", "minimum": 0 },
      "status": { "type": "string", "enum": ["pending", "paid", "shipped"] },
      "createdAt": { "type": "string", "format": "date-time" },
      "items": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["sku", "qty"],
          "properties": {
            "sku": { "type": "string" },
            "qty": { "type": "integer", "minimum": 1 }
          }
        }
      }
    }
  }
}
```

## 边界情况处理

- **字段类型不明确**：如"时间""编号"未给类型，按 `string` + `format`（`date-time` / `uuid`）保守处理，并在 `validation-notes.md` 标注假设。
- **缺少必填指示**：无"必须"等表述时默认非必填，但把推断依据写入说明，请用户确认。
- **枚举 vs 自由字符串**：用户列了"例如 A、B、C"但说"等"时，视为开放字符串（不加 `enum`），仅把示例列入 `examples`（Draft 2020-12 注解关键字）。
- **递归 / 自引用结构**（如评论树）：用 `$defs` 定义节点，`$ref` 指向自身，避免无限展开；示例数据只递归 1–2 层。
- **跨文件引用需求**：本技能默认单文件；若用户要求拆分多文件，使用相对路径 `$ref`（如 `"$ref": "common.json#/$defs/address"`）并提示需校验器支持跨文件解析。
- **Draft 版本冲突**：用户若提到 `draft-07` / `2019-09`，明确本技能固定输出 **2020-12**；如需其他版本，转换关键字（`definitions↔$defs`、`$id↔id`）并标注。
- **超大 / 超深结构**：字段超过 50 或嵌套超过 5 层时，建议拆分为 `$defs` 并分段生成，逐段自检，避免一次性产出难以校验的巨型 Schema。
- **反向校验（已有 JSON 推断 Schema）**：先用人工归纳或推断工具梳理结构，再回填约束；推断出的 `type` 以样本中出现的类型并集为准，并在说明中标注"推断"字样。

## 资源

### scripts/
- `generate_schema.py`：读取结构化 `spec.json`（模型在步骤 1 产出），自动生成 `schema.json`、`example.json` 与校验片段，并可选调用 `jsonschema` 做 Draft 2020-12 自检。纯标准库实现，无强依赖；检测到 `jsonschema` 时自动启用强校验。

### references/
- `draft2020-12-keywords.md`：Draft 2020-12 关键字速查表（类型、约束、组合关键字、`$defs` / `$ref`、废弃关键字对照），生成 Schema 时按需查阅以保持合规。
