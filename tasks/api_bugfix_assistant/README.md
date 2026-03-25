# API 修复任务

这个任务为 API-first 用户设计。

目标：
- 自动修复一个小型 OpenAI 兼容 API 工具中的 bug
- 用本地确定性 evaluator 验证（不访问外网）

可修改文件：
- `workspace/api_client.py`

评估器：
- `evaluate.py`

执行方式：

```bash
python3 run_task.py --description baseline
```
