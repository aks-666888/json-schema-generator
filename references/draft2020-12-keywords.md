# JSON Schema Draft 2020-12 关键字速查表

生成 Schema 时对照使用，确保严格符合 Draft 2020-12。完整规范见
<https://json-schema.org/draft/2020-12/schema>。

## 通用 / 元数据

| 关键字 | 作用 |
|--------|------|
| `$schema` | 声明所用草案，固定为 `https://json-schema.org/draft/2020-12/schema` |
| `$id` | 基URI，用于解析相对 `$ref`（取代旧版 `id`） |
| `$ref` | 引用其他 Schema 片段，如 `#/$defs/Address` |
| `$defs` | 存放可复用子 Schema（取代旧版 `definitions`） |
| `$anchor` / `$dynamicRef` / `$dynamicAnchor` | 动态引用（高级用法） |
| `title` / `description` | 人类可读标题 / 说明 |
| `default` | 默认值 |
| `examples` | 示例值集合（注解，不参与校验） |
| `deprecated` / `readOnly` / `writeOnly` | 注解类标记 |
| `comment` | 注释（不校验） |

## 类型

| 关键字 | 作用 |
|--------|------|
| `type` | `string` / `number` / `integer` / `object` / `array` / `boolean` / `null`；可为数组表示多类型 |
| `enum` | 取值必须是指定集合之一 |
| `const` | 取值必须等于指定常量 |

## 字符串约束

| 关键字 | 作用 |
|--------|------|
| `minLength` / `maxLength` | 长度上下限 |
| `pattern` | 正则（ECMA 262） |
| `format` | `date-time` / `date` / `time` / `email` / `uri` / `uuid` / `hostname` / `ipv4` / `ipv6` 等（默认不强制，仅注解，除非校验器开启） |
| `contentEncoding` / `contentMediaType` | 内容编码 / 媒体类型 |

## 数值约束

| 关键字 | 作用 |
|--------|------|
| `minimum` / `maximum` | 含边界范围 |
| `exclusiveMinimum` / `exclusiveMaximum` | 不含边界范围（**数值语义**，非 draft-07 的布尔语义） |
| `multipleOf` | 必须为该数的整数倍 |

## 对象约束

| 关键字 | 作用 |
|--------|------|
| `properties` | 字段名 → 子 Schema 映射 |
| `required` | 必填字段名数组 |
| `additionalProperties` | `true` / `false` 或子 Schema，控制未声明字段 |
| `propertyNames` | 字段名的 Schema 约束 |
| `patternProperties` | 按正则匹配字段名 |
| `minProperties` / `maxProperties` | 字段数量上下限 |
| `dependentRequired` | 某字段存在时其它字段必填 |
| `dependentSchemas` | 条件性子 Schema |
| `unevaluatedProperties` | 未被其它关键字评估的属性的约束（高级） |

## 数组约束

| 关键字 | 作用 |
|--------|------|
| `items` | 元素 Schema（2020-12 中统一为单 Schema，对全体元素生效） |
| `prefixItems` | 元组式：按位置定义前 N 个元素（取代 draft-07 的元组 `items`） |
| `minItems` / `maxItems` | 元素数量上下限 |
| `uniqueItems` | 元素是否唯一 |
| `contains` / `minContains` / `maxContains` | 至少含一个 / 指定数量满足条件的元素 |
| `unevaluatedItems` | 未被评估的元素的约束（高级） |

## 组合关键字

| 关键字 | 作用 |
|--------|------|
| `allOf` | 必须满足全部子 Schema |
| `anyOf` | 满足至少一个 |
| `oneOf` | 恰好满足一个 |
| `not` | 必须不满足 |
| `if` / `then` / `else` | 条件约束 |

## 废弃 / 变更对照（切勿在 2020-12 中使用旧写法）

| 旧版（draft-07 / 2019-09） | 2020-12 写法 |
|----------------------------|--------------|
| `definitions` | `$defs` |
| `id` | `$id` |
| `exclusiveMinimum` / `exclusiveMaximum` 为布尔 | 改为数值：`"exclusiveMinimum": 10` |
| 元组 `items` 为数组 | 改用 `prefixItems` |
| `$recursiveRef` / `$recursiveAnchor` | 改用 `$dynamicRef` / `$dynamicAnchor` |
| 依赖 `dependencies` | 改用 `dependentRequired` / `dependentSchemas` |
