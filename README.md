# 银行ESG报告结构化解析项目

## 项目概述

基于 MinerU/PaddleOCR 实现银行 ESG 报告的结构化解析，包含 PDF 转 Markdown、议题定位（97.5%成功率）、跨银行对比和时间序列分析。

---

## 必需文件清单

### 1. 环境配置
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `.env.example` | `./` | ✓ | MinerU API Key 配置模板 |

### 2. 配置文件
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `configs/model_config.yaml` | `configs/` | ✓ | 模型配置模板 |
| `configs/section_rules.yaml` | `configs/` | ✓ | 章节定位规则（20关键词/议题） |
| `configs/LLM抽取说明.md` | `configs/` | ✓ | LLM 抽取脚本说明 |
| `configs/workflow.yaml` | `configs/` | ✓ | 工作流配置 |

### 3. 核心代码
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `src/schemas.py` | `src/` | ✓ | Pydantic 数据模型 |
| `src/parse_docs.py` | `src/` | ✓ | PDF 解析脚本 |
| `src/route_sections.py` | `src/` | ✓ | 章节路由脚本（优化后） |
| `src/pipeline_run.py` | `src/` | ✓ | 工作流入口脚本 |

### 4. 数据文件
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `data/parsed/parsed_docs.jsonl` | `data/parsed/` | ✓ | 文档元数据 (216条) |
| `data/parsed/sections.jsonl` | `data/parsed/` | ✓ | 议题定位结果 (1263条) |
| `data/parsed/scanned_pdfs.md` | `data/parsed/` | ✓ | OCR处理记录 |
| `data/parsed/markdown/*.md` | `data/parsed/markdown/` | ✓ | 解析后的Markdown文件 (按银行分42个文件夹) |

### 5. 模板文件
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `templates/parse_check.md` | `templates/` | ✓ | 解析检查模板 |

### 6. 检查报告
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `outputs/reports/section_check_report.csv` | `outputs/reports/` | ✓ | 章节定位检查报告 (CSV) |
| `outputs/reports/section_check_report.md` | `outputs/reports/` | ✓ | 章节定位检查报告 (Markdown) |
| `outputs/reports/parse_check.md` | `outputs/reports/` | ✓ | PDF解析检查报告 |
| `outputs/reports/summary_report.md` | `outputs/reports/` | ✓ | 项目汇总报告 |

### 7. 抽取结果
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `outputs/results/extract_results.jsonl` | `outputs/results/` | ✓ | LLM 抽取结果 |
| `outputs/results/records_validated.csv` | `outputs/results/` | ✓ | 校验通过记录 |
| `outputs/logs/validation_errors.jsonl` | `outputs/logs/` | ✓ | 验证错误日志 |

### 8. 分析报告
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `outputs/analysis/comparison_summary.md` | `outputs/analysis/` | ✓ | 跨银行对比总览 |
| `outputs/analysis/*_comparison.md` | `outputs/analysis/` | ✓ | 6个议题对比报告 |
| `outputs/time_series/timeseries_summary.md` | `outputs/time_series/` | ✓ | 时间序列总览 |
| `outputs/time_series/*_timeseries.md` | `outputs/time_series/` | ✓ | 42家银行时间序列 |
| `outputs/topics_content/topics_content_summary.md` | `outputs/topics_content/` | ✓ | 议题内容总览 |
| `outputs/topics_content/*/*.md` | `outputs/topics_content/` | ✓ | 议题内容提取结果 |

### 9. 日志文件
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `outputs/logs/run_log.jsonl` | `outputs/logs/` | ✓ | 工作流运行日志 |
| `outputs/logs/complete_search.log` | `outputs/logs/` | ✓ | 完整搜索日志 |
| `outputs/logs/search.log` | `outputs/logs/` | ✓ | 搜索日志 |
| `outputs/logs/search_robust.log` | `outputs/logs/` | ✓ | 健壮搜索日志 |
| `outputs/logs/download.log` | `outputs/logs/` | ✓ | PDF下载日志 |

### 10. 工作日志
| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `ai_worklog_week13.md` | `./` | ✓ | AI 工作日志 |
| `workflow_design.md` | `./` | ✓ | 工作流设计文档 |
| `workflow_graph.md` | `./` | ✓ | 工作流图示文档 |

---

## 文件结构

```
project/
├── .env.example                          # 环境变量模板
├── ai_worklog_week13.md                  # AI 工作日志
├── workflow_design.md                    # 工作流设计
├── workflow_graph.md                     # 工作流图示
├── README.md                             # 项目说明
│
├── configs/
│   ├── model_config.yaml                # 模型配置
│   ├── section_rules.yaml               # 章节规则
│   ├── LLM抽取说明.md                   # LLM 抽取说明
│   └── workflow.yaml                    # 工作流配置
│
├── src/
│   ├── schemas.py                       # Pydantic 数据模型
│   ├── parse_docs.py                    # PDF 解析脚本
│   ├── route_sections.py                # 章节路由脚本
│   └── pipeline_run.py                  # 工作流入口
│
├── templates/
│   └── parse_check.md                   # 解析检查模板
│
├── data/
│   └── parsed/
│       ├── parsed_docs.jsonl            # 文档元数据 (216条)
│       ├── sections.jsonl               # 议题定位结果 (1263条)
│       ├── scanned_pdfs.md              # OCR处理记录
│       └── markdown/                    # Markdown文件 (按银行分)
│           ├── 000001/
│           ├── 001227/
│           └── ... (42家银行)
│
└── outputs/
    ├── reports/
    │   ├── section_check_report.csv
    │   ├── section_check_report.md
    │   ├── parse_check.md
    │   └── summary_report.md
    ├── results/
    │   ├── extract_results.jsonl
    │   ├── records_validated.csv
    │   └── validation_errors.jsonl
    ├── logs/
    │   ├── run_log.jsonl
    │   ├── complete_search.log
    │   ├── search.log
    │   ├── search_robust.log
    │   └── download.log
    ├── analysis/                        # 跨银行对比报告
    │   ├── comparison_summary.md
    │   ├── 风险管理_comparison.md
    │   ├── 公司治理_comparison.md
    │   ├── 绿色金融_comparison.md
    │   ├── 消费者权益保护_comparison.md
    │   ├── 普惠金融_comparison.md
    │   └── 乡村振兴_comparison.md
    ├── time_series/                     # 时间序列报告
    │   ├── timeseries_summary.md
    │   ├── 000001_timeseries.md
    │   ├── 001227_timeseries.md
    │   └── ... (42家银行)
    └── topics_content/                  # 议题内容提取
        ├── topics_content_summary.md
        ├── 风险管理/
        ├── 公司治理/
        ├── 绿色金融/
        ├── 消费者权益保护/
        ├── 普惠金融/
        └── 乡村振兴/
```

---

## 数据统计

| 指标 | 数值 |
|------|------|
| 银行数量 | 42 家 |
| PDF 文档总数 | 216 份 |
| 时间跨度 | 2021-2025 |
| PDF 解析成功率 | **100%** (216/216) |
| OCR 解析成功数 | 12 份 (扫描版) |
| 议题定位成功率 | **97.5%** (1263/1296) |
| 高置信度 (≥70%) | 1095 (86.7%) |
| 中置信度 (50-69%) | 168 (13.3%) |
| 低置信度 (<50%) | 0 |
| 提取字段数 | 45 个/文档 |
| 总提取记录 | 56835 条 |

---

## 核心议题

1. **风险管理** - 风险控制、信用风险、市场风险、全面风险管理
2. **公司治理** - 董事会、监事会、内部控制、三会一层
3. **绿色金融** - ESG、双碳、碳中和、绿色信贷
4. **消费者权益保护** - 客户保护、信息安全、投诉处理
5. **普惠金融** - 小微企业、三农、农村金融
6. **乡村振兴** - 农村金融、涉农贷款、乡村发展

---

## 课程要求对照

| 要求 | 实现 | 文件 |
|------|------|------|
| metadata 可控可查 | ✓ | `parsed_docs.jsonl` |
| PDF 可复现下载 | ✓ | `pdf_path` 字段记录原始路径 |
| MinerU 解析证据链 | ✓ | `pages` 字段记录页码内容 |
| Pydantic Schema | ✓ | `schemas.py` |
| difficulty 档位依据 | ✓ | `confidence` 字段记录置信度 |
| workflow 设计文档 | ✓ | `workflow_design.md` |
| workflow 图示 | ✓ | `workflow_graph.md` |
| pipeline 入口 | ✓ | `pipeline_run.py` |

---

## 运行命令

```bash
# 运行单个步骤
python src/pipeline_run.py --config configs/workflow.yaml --step audit
python src/pipeline_run.py --config configs/workflow.yaml --step parse --limit 10
python src/pipeline_run.py --config configs/workflow.yaml --step route
python src/pipeline_run.py --config configs/workflow.yaml --step extract --limit 10
python src/pipeline_run.py --config configs/workflow.yaml --step validate
python src/pipeline_run.py --config configs/workflow.yaml --step report

# 运行完整流程（小样本）
python src/pipeline_run.py --config configs/workflow.yaml --step all --limit 5

# 运行完整流程（全量）
python src/pipeline_run.py --config configs/workflow.yaml --step all

# 章节路由（单独运行）
python src/route_sections.py --markdown-dir data/parsed/markdown --output-csv outputs/reports/section_locations.csv --output-jsonl data/parsed/sections.jsonl --rules configs/section_rules.yaml
```

---

## 改进历程

| 改进项 | 改进前 | 改进后 | 提升幅度 |
|--------|--------|--------|----------|
| 章节定位成功率 | 3.9% | **97.5%** | **+24倍** |
| 关键词数量 | 5-7个 | 20个 | +200% |
| 目录格式支持 | 3种 | 6种 | +100% |
| OCR处理成功率 | 0% | 100% | 新增 |

---

## 关键技术实现

### PDF解析方案
- **主方案**: MinerU API（需配置 API Key）
- **备用方案**: `pdfminer.six`（无 API Key 时自动降级）
- **OCR方案**: PaddleOCR 2.7.3（处理扫描版PDF）

### 章节路由优化
- 支持6种目录格式匹配（第X章、数字编号、Markdown标题等）
- 每个议题扩展至20个关键词
- 启用模糊匹配和同义词识别
- 置信度计算综合匹配比例、标题长度等因素

### 数据验证
- Pydantic Schema 校验抽取结果
- 记录校验错误类型和原因
- 支持错误记录人工复核

---

## 输出文件清单

运行完整流程后生成的关键输出：

| 类型 | 文件 | 说明 |
|------|------|------|
| 日志 | `outputs/logs/run_log.jsonl` | 工作流运行日志 |
| 定位结果 | `data/parsed/sections.jsonl` | 1263条章节定位记录 |
| 抽取结果 | `outputs/results/extract_results.jsonl` | LLM抽取字段 |
| 校验结果 | `outputs/results/records_validated.csv` | 216条有效记录 |
| 汇总报告 | `outputs/reports/summary_report.md` | 项目汇总报告 |
| 章节报告 | `outputs/reports/section_check_report.md` | 定位检查报告 |
| 跨银行对比 | `outputs/analysis/comparison_summary.md` | 6个议题对比 |
| 时间序列 | `outputs/time_series/timeseries_summary.md` | 42家银行趋势 |

---

**生成时间**: 2026-06-14  
**记录人**: 陶羿莼  
**项目状态**: ✅ 完成