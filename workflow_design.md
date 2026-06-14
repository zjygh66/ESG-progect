# Workflow Design

## 项目目标

本项目旨在从银行 ESG 报告 PDF 中自动抽取六个核心议题（风险管理、公司治理、绿色金融、消费者权益保护、普惠金融、乡村振兴）的相关内容，生成结构化的数据报告和分析结果。

## 总流程图

```
Collect -> Audit -> Parse -> Inspect/Route -> Extract -> Validate -> Aggregate -> Report
```

## 节点表

| 节点 | 输入 | 输出 | 成功标准 | 失败处理 | 日志 |
|------|------|------|----------|----------|------|
| **Audit** | metadata.csv, PDF目录 | audit_report.csv, valid_pdfs.txt | 验证文件存在性和完整性 | 标记无效文件，记录错误原因 | 检查文件数、有效数、错误数 |
| **Parse** | PDF文件, MinerU API Key | Markdown文件, parsed_docs.jsonl | 成功转换为Markdown，包含完整内容 | 记录失败原因，跳过该文件 | 处理数、成功数、失败数、耗时 |
| **Route** | Markdown文件, section_rules.yaml | sections.jsonl, section_check_report.csv | 成功定位议题章节，置信度≥70% | 标记未找到的议题，记录低置信度结果 | 定位章节数、置信度分布 |
| **Extract** | sections.jsonl, prompts | extract_results.jsonl | LLM成功抽取字段 | 记录抽取失败，保留原始内容 | 抽取记录数、成功率 |
| **Validate** | extract_results.jsonl, schemas | records_validated.csv, validation_errors.jsonl | Pydantic校验通过 | 记录校验失败原因 | 校验记录数、错误类型统计 |
| **Aggregate** | records_validated.csv | 汇总分析表 | 成功聚合数据 | 记录聚合错误 | 聚合统计信息 |
| **Report** | 所有中间结果 | summary_report.md | 成功生成报告 | 记录报告生成错误 | 报告生成状态 |

## 人工检查点

1. **Route之后**：人工抽查章节定位准确性，调整关键词规则
2. **Extract之后**：人工检查抽取字段质量，优化Prompt
3. **Validate之后**：审核校验失败记录，决定是否人工修正

## 配置文件

- configs/workflow.yaml - 工作流配置
- configs/section_rules.yaml - 章节定位规则（20个关键词/议题）
- configs/model_config.yaml - 模型配置

## 最小运行命令

```bash
# 运行单个步骤
python pipeline_run.py --config configs/workflow.yaml --step audit
python pipeline_run.py --config configs/workflow.yaml --step parse --limit 10
python pipeline_run.py --config configs/workflow.yaml --step route
python pipeline_run.py --config configs/workflow.yaml --step extract --limit 10
python pipeline_run.py --config configs/workflow.yaml --step validate
python pipeline_run.py --config configs/workflow.yaml --step report

# 运行完整流程（小样本）
python pipeline_run.py --config configs/workflow.yaml --step all --limit 5

# 运行完整流程（全量）
python pipeline_run.py --config configs/workflow.yaml --step all
```

## 项目统计（截至2026-06-14）

| 指标 | 数值 |
|------|------|
| 银行数量 | 42 家 |
| PDF文档总数 | 216 份 |
| 时间范围 | 2021-2025 年 |
| PDF解析成功率 | **100%** (216/216) |
| OCR处理文档数 | 12 份 (扫描版) |
| 议题定位成功率 | **97.5%** (1263/1296) |
| 高置信度 (≥70%) | 1095 (86.7%) |
| 中置信度 (50-69%) | 168 (13.3%) |
| 低置信度 (<50%) | 0 |
| 提取字段数 | 45 个/文档 |
| 总提取记录 | 56,835 条 |

## 改进历程

| 改进项 | 改进前 | 改进后 | 提升幅度 |
|--------|--------|--------|----------|
| 章节定位成功率 | 3.9% | **97.5%** | **+24倍** |
| 关键词数量 | 5-7个 | 20个 | +200% |
| 目录格式支持 | 3种 | 6种 | +100% |
| OCR处理成功率 | 0% | 100% | 新增 |
| 时间序列分析 | 无 | 42家银行 | 新增 |
| 跨银行对比 | 无 | 6个议题 | 新增 |

## 日志系统

项目已实现完整的日志记录功能，运行日志路径：`outputs/logs/run_log.jsonl`

日志格式示例：
```json
{"time": "2026-06-14T10:00:00", "step": "parse", "doc_id": "000001_2024", "status": "success", "elapsed": 2.31, "error": null}
```

日志记录内容：
- 每一步的执行状态（成功/失败）
- 处理记录数
- 耗时统计
- 错误原因（失败时）