# LLM 抽取脚本使用说明

## 概述

使用 LLM (如 Claude/GPT-4) 抽取议题具体内容，提高抽取质量。

---

## 使用方法

### 1. 准备输入数据

```bash
# 生成抽取任务列表
python prepare_extract_tasks.py \
    --input section_locations.csv \
    --output extract_tasks.jsonl
```

### 2. 调用 LLM API

```bash
# 使用 Claude API
python extract_with_claude.py \
    --input extract_tasks.jsonl \
    --output extract_results_v1.jsonl \
    --api-key $ANTHROPIC_API_KEY

# 或使用 GPT-4 API
python extract_with_gpt4.py \
    --input extract_tasks.jsonl \
    --output extract_results_v1.jsonl \
    --api-key $OPENAI_API_KEY
```

### 3. 后处理

```bash
# 验证抽取结果
python validate_extract.py \
    --input extract_results_v1.jsonl \
    --errors validation_errors.jsonl
```

---

## API 配置

### Claude API

```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
```

### OpenAI API

```bash
export OPENAI_API_KEY="sk-xxxxx"
```

---

## 抽取 Prompt 示例

```markdown
你是一个专业的金融文本分析助手。请从银行社会责任报告中抽取特定议题的内容。

## 任务
从以下文本中抽取「{topic}」议题的完整内容。

## 要求
1. 保持原文结构，不要改写
2. 保留所有定量指标（如百分比、金额等）
3. 识别并标注关键数据
4. 评估内容难度：easy/medium/hard

## 评判标准
- easy: 内容结构清晰，定量数据完整
- medium: 内容基本完整，但部分数据缺失
- hard: 内容分散，缺少关键数据

## 输入文本
{content}

## 输出格式
```json
{
    "content": "抽取的完整内容",
    "metrics": ["识别到的定量指标列表"],
    "difficulty": "easy/medium/hard",
    "summary": "100字以内的摘要"
}
```
```

---

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --input | str | 必需 | 输入 CSV/JSONL 文件 |
| --output | str | 必需 | 输出 JSONL 文件 |
| --batch-size | int | 10 | 批处理大小 |
| --max-tokens | int | 4096 | 最大输出 token |
| --temperature | float | 0.3 | 采样温度 |

---

## 成本估算

| 模型 | 单次抽取成本 | 1000次抽取成本 |
|------|-------------|----------------|
| Claude-3.5-Sonnet | ~$0.003 | ~$3 |
| GPT-4o | ~$0.01 | ~$10 |

---

**更新时间**: 2026-06-13
