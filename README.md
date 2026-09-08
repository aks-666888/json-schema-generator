# json-schema-generator

根据自然语言描述的数据结构，自动生成符合 **JSON Schema Draft 2020-12** 的 Schema、示例数据与校验说明。纯标准库，零外部依赖，本地离线可用。

> 说人话，出 Schema。

## 特性

- 自然语言直出：不写 JSON，用中文/英文描述数据结构即可
- 标准合规：严格 JSON Schema Draft 2020-12，无废弃关键字（definitions→$defs 等）
- 三件套交付：schema.json + example.json（必然通过校验）+ validation-notes.md（字段约束 + 校验命令）
- 零依赖：纯 Python 标准库实现，无 jsonschema 也能跑（检测到则自动强校验）
- 8 类边界情况：类型不明、枚举 vs 自由串、递归结构、跨文件 $ref、Draft 版本冲突、超大结构、反向推断等

## 快速开始

### 方式一：直接告诉 AI（推荐）

把这段话发给支持本技能的 AI：

```
定义一个用户，必须有 id（整数）、email（邮箱格式，必须）、name（字符串）；
role 只能是 admin 或 user，默认 user；tags 是字符串数组；
profile 里含 age（整数，0–120）和 city（字符串）。
```

自动产出三件套。

### 方式二：脚本生成

```bash
# 1. 先产出结构化 spec.json（见 examples/）
python scripts/generate_schema.py --spec spec.json --out ./out
# 2. 产物：out/schema.json, out/example.json, out/validation-notes.md
```

### 方式三：反向校验已有 JSON

把现成 JSON 交给它，自动归纳结构并生成 Schema。

## 适用场景

- REST / RPC 接口请求响应校验规则
- 配置文件 / 表单的 Schema（编辑器自动补全 + 报错）
- PRD 字段表 → 机器可校验契约
- 校验某段 JSON 是否满足既定结构

## 目录结构

```
json-schema-generator/
├── SKILL.md                    # 技能定义与完整工作流
├── scripts/
│   └── generate_schema.py      # spec.json → schema/example/notes（零依赖）
└── references/
    └── draft2020-12-keywords.md  # 2020-12 关键字速查 + 废弃关键字对照
```

## 安装

- AI 助手（CodeBuddy/WorkBuddy）：把整个目录放入 ~/.workbuddy/skills/（用户级）即可被自动识别
- 手动使用：直接用 scripts/generate_schema.py

## License

Internal

## 常见问题（FAQ）

**装完第一步先干什么？**
直接跑一次自带的示例，看到输出长什么样再换成自己的数据，别一上来就改配置。

**我的数据会不会被上传？**
不会。全程在你自己的电脑上跑，不联网、不上传，关掉就没了。

**跑不起来最常见的原因？**
九成是运行环境版本不对。先确认版本，再看报错第一行——第一行基本就写明了缺什么。

**生成的 Schema 直接能用吗？**
能，输出就是标准格式，拿去校验器里直接跑。

**嵌套结构支持吗？**
支持，多层嵌套和复用结构都能出。

**和在线工具比优势在哪？**
不用把你的数据结构贴到别人网站上。


## 💛 支持作者

工具永久免费开源。如果它帮到了你，欢迎到爱发电请我喝杯奶茶：
https://afdian.com/a/xiaoqiangdev
你的支持让我能持续更新更多效率工具。
