# 银行业ESG报告结构化解析与可核查性评分项目

> 数据来源：巨潮资讯网公开公告

---

## 项目概述

本项目实现银行业ESG报告的**PDF提取、结构化解析、字段抽取、可视化分析**完整流程。基于MinerU/PaddleOCR实现PDF转Markdown，使用全文检索模式定位六大核心议题（97.5%成功率），完成规则字段抽取、LLM字段抽取、派生字段计算，最终输出结构化数据并生成可视化图表，支持银行横向纵向比较。

---

## 核心功能

| 功能模块 | 说明 |
|---------|------|
| **PDF报告提取** | 从巨潮资讯网搜索并下载银行ESG相关报告PDF文件 |
| **PDF解析** | MinerU API解析PDF为Markdown，保留页码标记 |
| **章节定位** | 全文检索模式定位六大核心议题（97.5%成功率） |
| **规则字段抽取** | 基于规则匹配提取可核查性相关字段（政策引用、KPI数据、同比变化等） |
| **LLM字段抽取** | 调用本地LLM模型提取风险语调、矩阵重要性等语义字段 |
| **派生字段计算** | 计算可核查性评分（verifiability_score）等综合指标 |
| **Schema验证** | Pydantic校验确保数据结构正确 |
| **Evidence追溯** | 每条记录可追溯到原始PDF页码 |
| **跨银行对比** | 42家银行横向比较 |
| **时间序列分析** | 2021-2025年纵向追踪 |
| **数据可视化** | 生成热力图、趋势图、箱线图、散点图等4张可视化图表 |

---

## 六大核心议题

| 议题 | 关键词示例 | 扩展关键词数量 |
|------|-----------|---------------|
| 公司治理 | 董事会、独立董事、股东大会 | 20个 |
| 风险管理 | 不良贷款率、拨备覆盖率、压力测试 | 20个 |
| 绿色金融 | 绿色信贷、碳中和、ESG、可持续发展 | 20个 |
| 消费者权益保护 | 信息安全、消保、NPS、投诉处理 | 20个 |
| 普惠金融 | 小微企业贷款、普惠金融、中小企业 | 20个 |
| 乡村振兴 | 涉农贷款、乡村振兴、农村金融 | 20个 |

---

## 数据统计

| 指标 | 数值 |
|------|------|
| 银行数量 | 42家 |
| PDF文档总数 | 216份 |
| 时间跨度 | 2021-2025年 |
| PDF解析成功率 | **100%** (216/216) |
| OCR解析成功数 | 12份 (扫描版) |
| 议题定位成功率 | **97.5%** (1263/1296) |
| 高置信度 (≥70%) | 1095 (86.7%) |
| 中置信度 (50-69%) | 168 (13.3%) |
| 低置信度 (<50%) | 0 |
| 提取字段数 | 45个/文档 |
| 总提取记录 | 56,835条 |

---

## 目标字段

### 规则字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `has_policy_ref` | bool | 是否有政策引用 |
| `has_scope_statement` | bool | 是否有范围声明 |
| `has_case_study` | bool | 是否有案例研究 |
| `has_kpi_value` | bool | 是否有KPI数值 |
| `has_yoy_change` | bool | 是否有同比变化 |
| `has_method_note` | bool | 是否有方法说明 |
| `has_assurance` | bool | 是否有第三方鉴证 |

### LLM字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `risk_tone` | str | 风险语调（正面/中性/负面） |
| `matrix_importance` | str | 矩阵重要性（高/中/低） |

### 派生字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `verifiability_score` | float | 可核查性评分（0-5分） |
| `spotlight_bias_flag` | bool | 聚焦偏差标记 |

---

## 环境配置

### Python环境要求

- **Python版本**：>= 3.10
- **推荐虚拟环境**：`venv` 或 `conda`

### 依赖安装

```bash
# 进入项目目录
cd project

# 创建并激活虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 目录结构检查

确保以下目录存在：

```bash
mkdir -p data/metadata data/pdf data/parsed outputs/logs outputs/results outputs/reports outputs/analysis outputs/figures
```

### 环境变量配置

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置必要参数
```

**`.env` 文件关键配置项：**

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MINERU_API_KEY` | MinerU API密钥 | - |
| `LLM_API_KEY` | LLM API密钥（搜索阶段可选） | - |
| `LLM_API_BASE_URL` | LLM API基础URL | `https://api.openai.com/v1` |
| `LLM_MODEL_NAME` | LLM模型名称 | `gpt-3.5-turbo` |
| `CNINFO_BASE_URL` | 巨潮资讯网基础URL | `https://www.cninfo.com.cn` |
| `DOWNLOAD_INTERVAL` | 下载间隔（秒） | `2` |
| `MAX_WORKERS` | 最大并发数 | `4` |

### 本地LLM部署（Ollama）

本项目使用本地部署的 `deepseek-r1-abliterated:1.5b` 模型：

```bash
# 安装 Ollama
# https://ollama.com/download

# 拉取模型
ollama pull huihui_ai/deepseek-r1-abliterated:1.5b

# 启动 Ollama 服务（默认端口 11434）
ollama serve

# 验证服务
curl http://localhost:11434/api/tags
```

---

## 项目文件结构

```
project/
├── README.md                             # 项目说明
├── requirements.txt                      # Python依赖
├── .env.example                          # 环境变量模板
│
├── configs/
│   ├── model_config.yaml                # 模型配置
│   ├── section_rules.yaml               # 章节定位规则（20关键词/议题）
│   ├── workflow.yaml                    # 工作流配置
│   ├── crawl.yaml                       # 爬取配置
│   └── LLM抽取说明.md                    # LLM抽取说明
│
├── src/
│   ├── schemas.py                       # Pydantic数据模型
│   ├── parse_docs.py                    # PDF解析脚本
│   ├── route_sections.py                # 章节路由脚本（全文检索模式）
│   ├── extract_fields.py                # 字段抽取脚本
│   ├── validate_results.py              # 数据验证脚本
│   ├── pipeline_run.py                  # 工作流入口
│   ├── search_announcements.py          # 公告搜索脚本
│   ├── download_pdfs.py                 # PDF下载脚本
│   ├── llm_extractor.py                 # LLM抽取脚本
│   ├── batch_extract_all.py             # 批量抽取脚本
│   └ visualize_esg.py                   # 可视化脚本
│
├── templates/
│   └ parse_check.md                     # 解析检查模板
│
├── data/
│   ├── metadata/metadata.csv            # 元数据（216条）
│   ├── pdf/                             # 原始PDF文件（216份）
│   │   ├── 000001/                      # 按股票代码分类
│   │   ├── 001227/
│   │   └ ... (42家银行)
│   └ parsed/
│       ├── parsed_docs.jsonl            # 文档元数据
│       ├── sections.jsonl               # 章节定位结果（1263条）
│       ├── scanned_pdfs.md              # OCR处理记录
│       └ markdown/                      # 解析后的Markdown（42个银行文件夹）
│           ├── 000001/
│           ├── 001227/
│           └ ... (42家银行)
│
├── outputs/
│   ├── reports/
│   │   ├── section_check_report.csv    # Section检查报告
│   │   ├── section_check_report.md     # Section检查报告(Markdown)
│   │   ├── parse_check.md              # PDF解析检查
│   │   └ summary_report.md             # 项目汇总报告
│   │
│   ├── results/
│   │   ├── extract_results.jsonl       # 抽取结果
│   │   ├── records_validated.csv       # 验证后的记录
│   │   ├── base_records.csv            # 全量字段提取结果
│   │   ├── bank_trend.csv              # 各银行年度趋势数据
│   │   ├── year_comparison.csv         # 跨年份对比数据
│   │   └ validation_errors.jsonl       # 验证错误日志
│   │
│   ├── analysis/
│   │   ├── comparison_summary.md       # 跨银行对比总览
│   │   ├── 风险管理_comparison.md      # 6个议题对比报告
│   │   ├── 公司治理_comparison.md
│   │   ├── 绿色金融_comparison.md
│   │   ├── 消费者权益保护_comparison.md
│   │   ├── 普惠金融_comparison.md
│   │   └── 乡村振兴_comparison.md
│   │
│   ├── time_series/
│   │   ├── timeseries_summary.md       # 时间序列总览
│   │   ├── 000001_timeseries.md        # 42家银行时间序列
│   │   ├── 001227_timeseries.md
│   │   └ ... (42家银行)
│   │
│   ├── topics_content/
│   │   ├── topics_content_summary.md   # 议题内容总览
│   │   ├── 风险管理/                   # 按议题分类的内容
│   │   ├── 公司治理/
│   │   ├── 绿色金融/
│   │   ├── 消费者权益保护/
│   │   ├── 普惠金融/
│   │   └── 乡村振兴/
│   │
│   ├── figures/
│   │   ├── 图1_热力图_银行议题可核查性评分.png/pdf
│   │   ├── 图2_趋势图_可核查性评分变化.png/pdf
│   │   ├── 图3_箱线图_银行类型评分分布.png/pdf
│   │   ├── 图4_散点图_言行偏离分析.png/pdf
│   │   └ interpretations.md            # 图表解读
│   │
│   ├── logs/
│   │   ├── run_log.jsonl               # 工作流运行日志
│   │   ├── search.log                  # 搜索日志
│   │   ├── download.log                # PDF下载日志
│   │   ├── extract_log.txt             # 提取过程日志
│   │   ├── processed_ids_v2.json       # 断点续传记录
│   │   ├── failed_downloads.csv        # 下载失败记录
│   │   └ validation_errors.jsonl       # 验证错误日志
│   │
│   └ sample_outputs/                   # 示例输出
│
├── demo_output/
│   ├── demo_script.md                  # 演示脚本
│   ├── demo_report.md                  # 演示报告
│
├── ai_worklog_week13.md                # AI工作日志
├── workflow_design.md                  # 工作流设计
├── workflow_graph.md                   # 工作流图示
│
└── final_report.md                      # 最终报告
```

---

## 运行命令

### 1. 搜索公告（获取PDF下载链接）

```bash
python src/search_announcements.py \
    --config configs/crawl.yaml \
    --output data/metadata/metadata.csv \
    --verbose
```

**参数说明：**
- `--config`：爬取配置文件路径，默认 `configs/crawl.yaml`
- `--output`：输出元数据文件路径
- `--verbose`：显示详细日志

**搜索配置（`configs/crawl.yaml`）：**

```yaml
project_name: "bank_esg_verifiability"
source: "cninfo"
keywords:
  - "社会责任报告"
  - "ESG报告"
  - "可持续发展报告"
  - "环境、社会及治理报告"
markets:
  - "sz"    # 深交所
  - "sh"    # 上交所
date_range:
  start: "2021-01-01"
  end: "2026-04-30"
max_records: 2000
sleep_seconds: 1.5
output:
  metadata: "data/metadata/metadata.csv"
  pdf_dir: "data/pdf"
  failed_downloads: "outputs/logs/failed_downloads.csv"
```

### 2. 下载PDF文件

```bash
python src/download_pdfs.py \
    --metadata data/metadata/metadata.csv \
    --output-dir data/pdf \
    --config configs/crawl.yaml \
    --workers 4 \
    --verbose
```

**参数说明：**
- `--metadata`：元数据CSV文件路径
- `--output-dir`：PDF存储目录
- `--config`：配置文件路径
- `--workers`：并发下载线程数
- `--verbose`：显示下载进度

**输出位置：**

| 输出文件 | 路径 | 说明 |
|------|------|------|
| 元数据CSV | `data/metadata/metadata.csv` | 包含PDF下载链接的完整清单 |
| PDF文件 | `data/pdf/{stock_code}/{year}_{report_id}.pdf` | 按股票代码和年份分类存储 |
| 下载日志 | `outputs/logs/download.log` | PDF下载过程日志 |
| 失败记录 | `outputs/logs/failed_downloads.csv` | 下载失败的记录 |
| 搜索日志 | `outputs/logs/search.log` | 公告搜索过程日志 |

**metadata.csv 格式：**

| 字段名 | 类型 | 说明 |
|------|------|------|
| `stock_code` | string | 股票代码 |
| `stock_name` | string | 股票名称 |
| `report_title` | string | 报告标题 |
| `report_date` | string | 报告日期 (YYYY-MM-DD) |
| `announcement_date` | string | 公告日期 (YYYY-MM-DD) |
| `pdf_url` | string | PDF下载链接 |
| `file_name` | string | 保存的文件名 |
| `status` | string | 下载状态 (pending/downloaded/failed) |

### 3. PDF解析（MinerU API）

```bash
python src/parse_docs.py
```

### 4. 章节定位（全文检索模式）

```bash
python src/route_sections.py \
    --markdown-dir data/parsed/markdown \
    --output-csv outputs/reports/section_locations.csv \
    --output-jsonl data/parsed/sections.jsonl \
    --rules configs/section_rules.yaml
```

### 5. 全量字段提取（规则字段 + 派生计算）

```bash
python src/batch_extract_all.py
```

**功能说明**：
- 读取 `outputs/reports/section_locations.csv`
- 扫描 `data/parsed/markdown/` 目录读取解析后的Markdown文件
- 执行规则字段抽取和派生字段计算
- 支持断点续传（已处理记录保存在 `outputs/logs/processed_ids_v2.json`）
- 每50条记录打印一次进度

### 6. LLM字段提取

```bash
python src/llm_extractor.py
```

**功能说明**：
- 调用本地 Ollama API 提取 `risk_tone`（风险语调）和 `matrix_importance`（矩阵重要性）字段
- 支持 JSON 和纯文本两种输出格式解析
- 失败时返回规则保底值

### 7. 数据可视化

```bash
python src/visualize_esg.py
```

**功能说明**：
- 基于提取结果生成4张可视化图表
- 输出 PNG 和 PDF 两种格式

### 8. 完整工作流

```bash
# 运行完整流程（小样本）
python src/pipeline_run.py --step all --limit 5

# 运行完整流程（全量）
python src/pipeline_run.py --step all
```

---

## 完整执行流程

```bash
# 1. 搜索公告（获取PDF下载链接）
python src/search_announcements.py --config configs/crawl.yaml

# 2. 下载PDF文件到本地
python src/download_pdfs.py --metadata data/metadata/metadata.csv --output-dir data/pdf

# 3. PDF解析（MinerU API）
python src/parse_docs.py

# 4. 章节定位（全文检索模式）
python src/route_sections.py --markdown-dir data/parsed/markdown

# 5. 启动 Ollama 服务（后台运行）
ollama serve

# 6. 执行全量字段提取
python src/batch_extract_all.py

# 7. 执行 LLM 字段提取
python src/llm_extractor.py

# 8. 生成可视化图表
python src/visualize_esg.py

# 9. 查看输出
ls outputs/results/
ls outputs/figures/
```

---

## 技术架构

### 完整工作流

```
巨潮公告数据
  ↓ 搜索公告
metadata.csv (PDF下载链接)
  ↓ 下载PDF
PDF文件 (216份)
  ↓ MinerU解析
Markdown文件 (含页码标记)
  ↓ Section Routing (全文检索模式)
sections.jsonl (章节定位结果)
  ↓ 规则字段抽取
base_records.csv
  ↓ LLM字段抽取
LLM字段 (risk_tone, matrix_importance)
  ↓ 派生字段计算
verifiability_score
  ↓ Pydantic Validation
records_validated.csv
  ↓ 跨银行对比
comparison_*.md
  ↓ 时间序列分析
timeseries_*.md
  ↓ 可视化
可视化图表 (4张)
```

### PDF解析方案

| 方案 | 说明 | 适用场景 |
|------|------|----------|
| **MinerU API** | 主方案，需配置API Key | 正常PDF |
| **pdfminer.six** | 备用方案，无API Key时自动降级 | 正常PDF |
| **PaddleOCR** | OCR方案，处理扫描版PDF | 扫描版PDF |

### 章节路由优化

| 改进项 | 改进前 | 改进后 | 提升幅度 |
|--------|--------|--------|----------|
| 章节定位成功率 | 3.9% | **97.5%** | **+24倍** |
| 关键词数量 | 5-7个 | 20个 | +200% |
| 目录格式支持 | 3种 | 6种 | +100% |
| OCR处理成功率 | 0% | 100% | 新增 |

---

## Pydantic Schema设计

### 核心模型

```python
class ParsedDocument(BaseModel):
    """解析后的文档模型"""
    doc_id: str
    title: str
    pdf_path: str
    markdown_path: str
    pages: List[PageContent]
    bank_code: Optional[str]
    year: Optional[int]
    page_count: int

class SectionLocation(BaseModel):
    """章节位置信息"""
    doc_id: str
    issue_name: Literal["公司治理", "风险管理", "绿色金融", 
                         "消费者权益保护", "普惠金融", "乡村振兴"]
    section_title: str
    start_page: Optional[int]
    end_page: Optional[int]
    confidence: float = Field(..., ge=0, le=100)
    quality_issue: Literal["ok", "not_found", "too_short", "wrong_section"]

class Evidence(BaseModel):
    """证据模型"""
    text: str
    page_no: Optional[int]

class ExtractedContent(BaseModel):
    """抽取的内容模型"""
    doc_id: str
    topic: str
    content: str
    source_pages: str
    confidence: float
    evidence: Optional[Evidence]
```

---

## Evidence追溯链

每条记录可追溯到原始PDF：

```
records_validated.csv
 -> extract_results.jsonl (evidence字段)
 -> sections.jsonl (章节定位)
 -> parsed_docs.jsonl (pages字段)
 -> data/pdf/*.pdf (原始PDF)
```

每条记录包含：
- `doc_id`：文档ID
- `evidence.text`：原文片段
- `evidence.page_no`：证据所在页码

---

## 输出文件清单

### 字段提取结果

| 文件 | 路径 | 说明 |
|------|------|------|
| 基础记录 | `outputs/results/base_records.csv` | 全量字段提取结果（含时间戳版本） |
| 银行趋势 | `outputs/results/bank_trend.csv` | 各银行年度趋势数据 |
| 年份对比 | `outputs/results/year_comparison.csv` | 跨年份对比数据 |
| 提取日志 | `outputs/logs/extract_log.txt` | 提取过程日志 |
| 已处理记录 | `outputs/logs/processed_ids_v2.json` | 断点续传记录 |

### 可视化图表

| 文件 | 路径 | 说明 |
|------|------|------|
| 热力图 | `outputs/figures/图1_热力图_银行议题可核查性评分.png/pdf` | 银行×议题可核查性评分 |
| 趋势图 | `outputs/figures/图2_趋势图_可核查性评分变化.png/pdf` | 2021-2025年评分变化 |
| 箱线图 | `outputs/figures/图3_箱线图_银行类型评分分布.png/pdf` | 不同类型银行分布对比 |
| 散点图 | `outputs/figures/图4_散点图_言行偏离分析.png/pdf` | 重要性-可核查性偏离分析 |
| 图表解读 | `outputs/figures/interpretations.md` | 每张图的解读文字 |

### 分析报告

| 文件 | 说明 |
|------|------|
| `outputs/analysis/comparison_summary.md` | 跨银行对比总览 |
| `outputs/analysis/*_comparison.md` | 6个议题对比报告 |
| `outputs/time_series/timeseries_summary.md` | 时间序列总览 |
| `outputs/time_series/*_timeseries.md` | 42家银行时间序列 |
| `outputs/topics_content/topics_content_summary.md` | 议题内容总览 |
| `outputs/topics_content/*/*.md` | 议题内容提取结果 |
