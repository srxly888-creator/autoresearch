# autoresearch

这个 fork 保留了原始 GPU 训练工作流（`program-train.md`），但默认模式已经切换为面向 API 用户的自动研究 / 自动解题流程。

## 初始化

启动新一轮实验时，请和用户完成以下步骤：

1. **确定 run tag**：按日期生成标签（如 `mar25`），并确保 `autoresearch/<tag>` 分支尚不存在。
2. **创建分支**：从当前 `master` 执行 `git checkout -b autoresearch/<tag>`。
3. **阅读当前任务定义**：
   - `README.md`：仓库背景与使用方式
   - `problem.md`：当前任务目标、约束、成功标准
   - `task.json`：可修改文件范围、评估命令、打分方向、超时与产物目录
   - `run_task.py`：通用评估执行器
4. **阅读任务相关文件**：
   - `mutable_paths` 中列出的文件是默认可修改范围
   - 先看清 `task.json` 中 evaluator 入口，明确评分规则
5. **确认 baseline**：改代码前先执行 `python3 run_task.py --description baseline`。
6. **确认后开始循环**：先记录 baseline，再进入实验迭代。

## 实验循环

每轮实验都按统一节奏执行：

1. 提出一个具体假设。
2. 仅修改 `mutable_paths` 里的文件（除非用户明确扩展范围）。
3. 提交改动。
4. 执行 `python3 run_task.py --description "<简短实验说明>"`。
5. 阅读终端摘要和 `artifacts/.../runs/<run_id>/` 下日志。
6. 分数按配置方向提升则保留 commit。
7. 退化或失败则回退到上一个有效版本。
8. 必要时把经验记录到 artifact 目录下的未跟踪笔记。

任务类型可以是代码生成、修 bug、性能优化、策略搜索等，但应满足：

- 成功指标清晰
- 评估可复现
- 可修改范围明确且尽量小

## 规则

**可以做的事：**
- 修改 `mutable_paths` 指定文件
- 阅读必要的只读上下文以理解任务
- 基于 evaluator 输出、日志与 git 历史推进下一轮假设

**默认不能做的事：**
- 修改 evaluator 或 `run_task.py`
- 新增依赖
- 更改 `task.json` 中评分契约

若用户明确要求扩大搜索空间，可与用户同步后再放宽限制。

## 输出格式

`python3 run_task.py` 会输出类似摘要：

```
---
task:             api_bugfix_assistant
run_id:           20260325-120000-abc123
score:            83.210000
score_direction:  maximize
status:           fail
duration_seconds: 0.218
best_score_before:82.100000
comparison:       improved
summary:          10 项测试通过 8 项；请先修复正确性
artifact_dir:     artifacts/api_bugfix_assistant/runs/20260325-120000-abc123
```

evaluator 必须把 JSON 结果写入 `AUTORESEARCH_OUTPUT_JSON` 指向路径。最小结果结构如下：

```json
{
  "score": 83.21,
  "status": "fail",
  "summary": "10 项测试通过 8 项；请先修复正确性"
}
```

## 日志记录

`run_task.py` 会自动向 `artifacts/<task>/results.tsv` 追加一行：

```
run_id	branch	commit	score	status	duration_seconds	description	summary
```

artifact 目录还会保存：

- `stdout.log`
- `stderr.log`
- `result.json`
- `metadata.json`

## 持续迭代

循环执行：

1. 先看当前分支与历史最佳分数
2. 大方向变化前重读 `problem.md`
3. 做一次聚焦改动
4. 提交
5. 跑 evaluator
6. 按评分方向决定保留或丢弃
7. 重复直到用户停止

如果当前任务是原始单 GPU `train.py` 优化流程，请改用 `program-train.md`。
