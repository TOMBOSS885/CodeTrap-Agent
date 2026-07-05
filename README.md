# CodeTrap-Agent

CodeTrap-Agent 是一个本地化的 AI 出题工作台。它参考 CodeSetArena 的课程平台形态，但目标互补：不再让学生手工设计题目去测试 AI，而是让 AI 主动生成“难住 AI 的编程题包”，并要求每道题同时包含题面、函数签名、参考答案、测试用例和坑点说明。

## 核心思路

系统会把模型放在“出题者”位置，要求它构造高混淆度题目：

- 题面必须明确输入输出与边界。
- 参考答案必须是可执行 Python 函数。
- 测试用例必须覆盖公开样例、隐藏边界和对抗样例。
- 坑点必须写出来，包括常见错误、诱导误读、边界条件和可能击穿 AI 解题器的原因。
- 本地会对生成结果做结构校验与陷阱覆盖评分，尽量避免“看起来难，实际很空”的题。

## 快速开始

```powershell
pip install -e .[dev]
codetrap-agent init
codetrap-agent settings set --base-url https://api.example.com/v1 --api-key sk-xxx --models gpt-4.1
codetrap-agent generate --topic "字符串解析" --count 2
codetrap-agent list
codetrap-agent serve --port 3141
```

没有可用模型时，可以用 mock 模式跑通流程：

```powershell
codetrap-agent generate --topic "区间与排序" --count 1 --mock
pytest
```

默认数据目录为 `.codetrap-agent`，所有题包和原始模型响应都会保存在本地。
