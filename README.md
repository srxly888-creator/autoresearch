**[English](./README-EN.md)** | **简体中文** | **[繁體中文](./README-ZH-TW.md)** | **[📚 Learning Notes](./.learning/README.md)**

# autoresearch (API-first fork)

这个 fork 的默认目标不是训练模型，而是帮 API 用户自动解决工程问题：

- 自动修 bug
- 自动补接口实现
- 自动跑测试并比较结果
- 自动保留改进、丢弃退化方案

你只需要有一个可执行评估器（tests/benchmark），agent 就能在约束范围内持续迭代。

## 适用人群

- 主要使用 OpenAI/GLM/Claude/DeepSeek 等 API 的团队
- 没有本地 GPU，或不想维护训练基础设施
- 想把“提出方案 -> 改代码 -> 跑验证 -> 记录结果”做成自动循环

## 核心思路

本仓库把自动研究拆成 4 个固定部件：

1. `problem.md`：问题定义（目标、约束、验收标准）
2. `task.json`：任务配置（可改文件、评估命令、打分方向、超时）
3. `run_task.py`：统一运行入口（执行评估、记录 artifacts、打印摘要）
4. `tasks/<task_name>/evaluate.py`：你的评估器（输出 score/status/summary）

这 4 个部件组合后，就能在任何“可评估”的工程问题上复用。

## 快速开始前提（本地接通 GLM-5 API）

先把本机 API 调用打通，再进自动研究流程。

### 1) 准备环境

```bash
python3 --version
python3 -m pip install -U openai
```

### 2) 配置密钥

```bash
export ZAI_API_KEY="你的智谱 API Key"
```

### 3) 最小联通验证（GLM-5）

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("ZAI_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

resp = client.chat.completions.create(
    model="glm-5",
    messages=[{"role": "user", "content": "只回复 OK"}],
    temperature=0
)
print(resp.choices[0].message.content)
```

如果你在某些编程工具中使用 GLM Coding Plan，可改用 coding 端点：

- `https://open.bigmodel.cn/api/coding/paas/v4/`

官方教材/文档入口：

- OpenAI 兼容接入：[docs.bigmodel.cn/cn/guide/develop/openai/introduction](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction)
- API 使用概述：[docs.bigmodel.cn/cn/api/introduction](https://docs.bigmodel.cn/cn/api/introduction)
- 模型迁移指南：[docs.bigmodel.cn/cn/guide/platform/model-migration](https://docs.bigmodel.cn/cn/guide/platform/model-migration)

## 30 秒快速开始（通过前提后）

```bash
git clone git@github.com:srxly888-creator/autoresearch.git
cd autoresearch
python3 run_task.py --description baseline
```

如果你已经在仓库目录里，直接执行：

```bash
python3 run_task.py --description baseline
```

你会得到：

- `artifacts/api_bugfix_assistant/results.tsv`（历史结果）
- `artifacts/api_bugfix_assistant/runs/<run_id>/`（每次运行日志和结构化结果）

当前默认任务是：

- `tasks/api_bugfix_assistant/workspace/api_client.py`

这个任务模拟真实 API 工程需求：修复 OpenAI-compatible 请求构造、响应解析和重试策略。

## 如何让 agent 自动迭代

在仓库里启动你的 Codex/Claude 后，直接给它：

```text
Read program.md, run baseline with python3 run_task.py, then start the experiment loop and keep only score-improving changes.
```

默认策略：

- 只允许修改 `mutable_paths` 指定文件
- 每次改动后都跑评估器
- 分数提升才保留，否则回退

## 如何替换成你的真实任务

只改下面三处即可：

1. `problem.md`
2. `task.json`
3. `tasks/<your_task>/evaluate.py`

建议流程：

1. 在 `problem.md` 写清楚业务目标和硬约束
2. 在 `task.json` 指定可修改代码范围和评估命令
3. 在 `evaluate.py` 做确定性验证并写出结果 JSON：

```json
{
  "score": 87.5,
  "status": "pass",
  "summary": "all tests passed; p95 latency improved"
}
```

注意：评估器需要把这个 JSON 写到环境变量 `AUTORESEARCH_OUTPUT_JSON` 指向的路径。

## 目录结构

```text
problem.md
program.md
task.json
run_task.py
tasks/
  api_bugfix_assistant/
    evaluate.py
    workspace/
      api_client.py
artifacts/
```

## 与原始训练模式的关系

这个 fork 保留了原始训练模式，但不作为默认入口：

- `program-train.md`
- `train.py`
- `prepare.py`

如果你要做单卡训练优化，使用训练模式；如果你要做 API 工程问题优化，使用默认通用模式。

## 常见问题

### 没有 GPU 能用吗？

可以。默认任务和通用框架不依赖本地 GPU。

### 必须联网吗？

不一定。默认 evaluator 是本地确定性评估，不访问网络。

### API Key 放哪？

如果你的真实任务需要调用外部 API，建议通过环境变量注入，不要写进代码库。

## 许可证

MIT
