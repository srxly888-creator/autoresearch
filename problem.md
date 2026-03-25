# 当前任务

默认任务面向 API 场景，适用于基于托管大模型 API 做产品开发的团队。

## 目标

修复并增强下面这个 OpenAI 兼容 API 工具模块：

- `tasks/api_bugfix_assistant/workspace/api_client.py`

目标能力：

1. 正确构造 chat 请求 payload
2. 对常见响应结构稳健提取助手文本
3. 仅在可重试错误时重试

## 成功指标

- 主指标：最大化 `score`
- 正确性门槛：evaluator 全部测试通过后才能达到 `status=pass`
- 速度加分：正确性 100% 后，文本提取越快得分越高

evaluator 为本地确定性检查，不访问外网。

## 可修改范围

默认只允许修改：

- `tasks/api_bugfix_assistant/workspace/api_client.py`

以下文件默认只读：

- `task.json`
- `run_task.py`
- `tasks/api_bugfix_assistant/evaluate.py`
- `problem.md`

## 约束

- 保持现有函数名不变：
  - `build_chat_request(...)`
  - `extract_text_from_response(...)`
  - `should_retry(...)`
- 仅使用 Python 标准库
- 保持行为可预测、易理解
- 不允许硬编码 evaluator 答案

## 任务背景

这个默认任务模拟了常见真实场景：

- API 团队需要稳定的请求/响应处理层
- 常见 bug 集中在 payload 格式、解析边界条件、重试策略
- 这类问题非常适合“本地可复现测试 + 自动修复循环”

要切换到你的真实项目，可按以下步骤：

1. 重写 `problem.md`
2. 更新 `task.json`
3. 把 `mutable_paths` 指向你的可修改文件
4. 把 evaluator 命令替换成你的测试/基准脚本
