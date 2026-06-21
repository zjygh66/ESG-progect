# 银行ESG报告结构化解析演示脚本

> 参考：Week 13：MinerU 解析、Section 检查、Schema 与字段抽取
> 参考：Lab Week 13：MinerU、Section、Schema 与 Evidence 示范

## 演示概述

本演示展示 **Week 13 的最小抽取链路**：

```
真实银行ESG PDF
 -> MinerU API 转 Markdown
 -> parsed_docs.jsonl
 -> section routing
 -> rule baseline 或硅基流动 LLM 抽取
 -> Pydantic validation
 -> 带 evidence 的结果
```

**目标文档**: 平安银行2021年可持续发展报告  
**银行代码**: 000001（平安银行）  
**报告年份**: 2021年  

---

## 1. 用 MinerU 把 PDF 转 Markdown

### 1.1 MinerU API 配置

```bash
# 查看 .env.example（只写变量名和占位符，不写真实 Key）
cat .env.example
```

```
LLM_PROVIDER=siliconflow
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_API_KEY=your_key_here
LLM_MODEL=Qwen/Qwen3-8B

MINERU_API_KEY=your_mineru_key_here
```

**注意**: 真实 `.env` 不得提交到 Git 或作业平台。

### 1.2 运行 MinerU 解析

```bash
# 运行解析脚本
python src/parse_docs.py
```

**输出**:
```
data/parsed/markdown/*.md
data/parsed/parsed_docs.jsonl
```

### 1.3 parsed_docs.jsonl 结构

每个文档包含以下字段：

```json
{
  "doc_id": "2021-1212533363",
  "stock_code": "000001",
  "stock_name": "平安银行",
  "title": "平安银行2021年可持续发展报告",
  "pdf_path": "data/pdf/000001_2021-1212533363.pdf",
  "markdown_path": "data/parsed/markdown/000001/2021-1212533363.md",
  "parser": "mineru",
  "pages": [
    {"page_no": 1, "text": "Markdown or parsed text here"}
  ]
}
```

### 1.4 MinerU 解析检查表

```
# Parse Check

## Document
- doc_id: 2021-1212533363
- title: 平安银行2021年可持续发展报告
- pdf_path: data/pdf/000001_2021-1212533363.pdf
- markdown_path: data/parsed/markdown/000001/2021-1212533363.md

## Page Check
- 页码是否保留: ✓
- 是否有乱码: ✓ 无
- 表格是否完整: ✓ 完整
- 标题层级是否合理: ✓ 合理
- 目录是否混入正文: ✓ 未混入

## Target Content
- 目标章节是否出现: ✓ 六大议题章节均已出现
- 关键字段是否能在解析文本中找到: ✓ 可找到
- 是否需要人工修正: ✓ 不需要
```

---

## 2. Section Routing

### 2.1 Routing 与 Checking 的区别

```
Section Routing：自动找到可能相关的章节。
Section Checking：检查找到的章节是否真的对，必要时修正规则。
```

Routing 是程序行为，Checking 是质量控制。一个项目可以有简单的 Routing，但不能没有 Checking。

### 2.2 查看 Section 规则

```bash
# 查看规则配置
cat configs/section_rules.yaml
```

```yaml
topics:
  - name: "公司治理"
    keywords:
      - "公司治理"
      - "董事会"
      - "独立董事"
      - "股东大会"
      - "监事会"
      # ... 共20个关键词
    section_patterns:
      - "3"
      - "第三章"

  - name: "风险管理"
    keywords:
      - "风险管理"
      - "不良贷款率"
      - "拨备覆盖率"
      - "压力测试"
      # ... 共20个关键词
    section_patterns:
      - "3.4"
      - "风险管理"

strategy:
  search_mode: "full_text"    # 全文检索模式
  enable_fuzzy_match: true
  min_keyword_matches: 1

confidence:
  high: 70
  medium: 50
  low: 30
```

### 2.3 运行 Section Routing

```bash
# 运行章节定位
python src/route_sections.py \
    --markdown-dir data/parsed/markdown/000001 \
    --output-csv demo_output/section_locations_demo.csv \
    --output-jsonl demo_output/sections_demo.jsonl
```

**输出**:
```
data/parsed/sections.jsonl
outputs/reports/section_check_report.csv
```

### 2.4 Section 检查表

```csv
doc_id,title,target_section,found,section_title,page_start,page_end,quality_issue,notes
2021-1212533363,平安银行2021可持续发展报告,公司治理,true,公司治理,11,15,ok,
2021-1212533363,平安银行2021可持续发展报告,风险管理,true,强化风险管理,16,20,ok,
2021-1212533363,平安银行2021可持续发展报告,绿色金融,true,绿色发展,47,52,ok,
2021-1212533363,平安银行2021可持续发展报告,消费者权益保护,true,守护信息安全,29,33,ok,
2021-1212533363,平安银行2021可持续发展报告,普惠金融,true,普惠金融,37,42,ok,
2021-1212533363,平安银行2021可持续发展报告,乡村振兴,true,助力乡村振兴,42,47,ok,
```

**quality_issue 字段**:
- `ok`: 定位正确
- `not_found`: 未找到章节
- `toc_mismatch`: 目录误匹配
- `too_short`: 内容过短
- `wrong_section`: 定位错误章节

---

## 3. Schema

### 3.1 为什么先定义 Schema

Pydantic Schema 是字段契约。它能告诉模型、代码和评分标准：结果应该长什么样。

先定义 Schema 的好处：
- 明确字段
- 限制类型
- 便于验证
- 便于评分
- 避免"这次字段叫 amount，下次叫 money"的混乱

### 3.2 查看 Schema 定义

```bash
# 查看 Schema
cat src/schemas.py
```

```python
from typing import Optional, Literal
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    """证据模型"""
    text: str = Field(description="支持字段判断的原文片段")
    page_no: Optional[int] = Field(default=None, description="证据所在页码")

class SectionLocation(BaseModel):
    """章节定位结果"""
    doc_id: str
    issue_name: Literal["公司治理", "风险管理", "绿色金融", 
                         "消费者权益保护", "普惠金融", "乡村振兴"]
    section_title: str
    start_page: int
    end_page: int
    confidence: int = Field(ge=0, le=100)
    quality_issue: Literal["ok", "not_found", "too_short", "wrong_section"]

class ESGContentExtract(BaseModel):
    """ESG内容提取结果"""
    doc_id: str
    company_name: str = Field(description="银行名称")
    stock_code: Optional[str] = Field(default=None, description="证券代码")
    report_year: Literal["2021", "2022", "2023", "2024", "2025"]
    issue_name: Literal["公司治理", "风险管理", "绿色金融", 
                         "消费者权益保护", "普惠金融", "乡村振兴"]
    content: str = Field(description="提取的议题内容")
    evidence: Evidence
    has_metrics: bool = Field(description="是否包含定量指标")
    confidence: float = Field(ge=0.0, le=1.0)
```

### 3.3 Null Rule

**不确定时输出 `null`，不能编造。**

这是金融公告抽取中非常重要的规则。模型如果根据常识补全字段，结果看起来完整，但实际不可用。

---

## 4. 抽取与校验

### 4.1 两条可选路线

| 路线 | 适合场景 | 优点 | 风险 |
|------|----------|------|------|
| 规则 baseline | 关键词较明确 | 透明、便宜、可复现 | 泛化弱，容易漏掉变体 |
| 硅基流动 API | 字段表达多样、需要理解上下文 | 灵活，便于快速迭代 | 需要 API Key，必须做 JSON 校验和 evidence 检查 |

### 4.2 规则 baseline 抽取

```bash
# 运行规则抽取
python src/extract_fields.py --method rule
python src/validate_results.py
```

**输出**:
```
outputs/results/extract_results.jsonl
outputs/results/records_validated.csv
outputs/logs/validation_errors.jsonl
```

### 4.3 硅基流动 LLM 抽取

在 `.env` 中填写：
```
LLM_PROVIDER=siliconflow
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen3-8B
LLM_API_KEY=your_key_here
```

然后运行：
```bash
python src/extract_fields.py --method llm
python src/validate_results.py
```

### 4.4 LLM 提示词基本规则

```
你将收到银行ESG报告中的一个目标章节。请只根据输入文本抽取字段。
如果字段不存在，输出 null。
不得根据常识补全。
每个关键字段必须给出 evidence_text。
evidence_text 必须是输入文本中的原文片段。
输出必须是合法 JSON，并符合给定字段说明。
```

---

## 5. 规则字段抽取（C同学工作）

### 5.1 字段抽取流程

基于上游输出的 `section_locations_demo1.csv` 和解析后的 `markdown` 文件，完成可核查性相关字段的抽取：

```
section_locations.csv (上游输入)
    ↓
markdown文件 (上游输入)
    ↓
规则字段提取 (has_policy_ref, has_scope_statement, etc.)
    ↓
LLM字段提取 (risk_tone, matrix_importance)
    ↓
派生字段计算 (verifiability_score)
    ↓
base_records_demo.csv (下游输出)
```

### 5.2 查看字段提取脚本

```bash
# 查看字段提取脚本
cat demoC/extract_demo.py
```

**核心字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `has_policy_ref` | bool | 是否引用政策文件 |
| `has_scope_statement` | bool | 是否有范围声明 |
| `has_case_study` | bool | 是否有案例研究 |
| `has_kpi_value` | bool | 是否包含KPI数值 |
| `has_yoy_change` | bool | 是否有同比变化 |
| `has_method_note` | bool | 是否有方法说明 |
| `has_assurance` | bool | 是否有第三方鉴证 |
| `in_material_matrix` | bool | 是否在实质性矩阵中出现 |
| `risk_tone` | str | 风险语调（展示性/平衡/风险透明） |
| `matrix_importance` | str | 矩阵重要性（高/中/低/未出现） |
| `verifiability_score` | int | 可核查性评分（0-5分） |
| `spotlight_bias_flag` | bool | 聚焦偏差标记 |

### 5.3 运行字段提取

```bash
# 进入demoC目录
cd demo_output_B/demoC

# 运行字段提取脚本
python extract_demo.py
```

**输出**：
```
demoC/outputs/base_records_demo.csv
demoC/outputs/base_records_demo.jsonl
```

### 5.4 字段提取结果示例

```csv
doc_id,stock_code,company_name,report_year,issue_name,section_title,source_page,evidence_snippet,has_policy_ref,has_scope_statement,has_case_study,has_kpi_value,has_yoy_change,has_method_note,has_assurance,in_material_matrix,risk_tone,matrix_importance,verifiability_score,spotlight_bias_flag
2021-1212533363,000001,平安银行,2021,公司治理,公司治理,11,"2021年末，本行制造业中长期贷款较上年末增长29.2%；...",False,False,False,True,True,True,False,False,风险透明（含负面）,未出现,2,False
2021-1212533363,000001,平安银行,2021,风险管理,强化风险管理,16,...（以此类推）
```

### 5.5 可核查性评分计算

**计算公式**：
```
verifiability_score = min(
    has_policy_ref + has_scope_statement + has_case_study + 
    has_kpi_value + has_yoy_change,
    5
)
```

| 议题 | 可核查性评分 | 主要贡献字段 |
|------|-------------|-------------|
| 公司治理 | 2分 | has_kpi_value, has_yoy_change |
| 风险管理 | 2分 | has_kpi_value, has_yoy_change |
| 绿色金融 | 2分 | has_kpi_value, has_yoy_change |
| 消费者权益保护 | 2分 | has_kpi_value, has_yoy_change |
| 普惠金融 | 2分 | has_kpi_value, has_yoy_change |
| 乡村振兴 | 2分 | has_kpi_value, has_yoy_change |

### 5.6 LLM字段提取（可选）

如需启用LLM字段提取（需要Ollama服务），修改 `extract_demo.py` 中的 `use_llm=True`：

```python
result = extract_rule_fields(
    text=clean_content[:10000],
    issue_name=issue_name,
    source_page=page_num,
    doc_id=doc_id,
    stock_code=stock_code,
    report_year=2021,
    use_llm=True  # 启用LLM字段提取
)
```

**LLM配置**：
- 模型：`deepseek-r1-abliterated:1.5b`
- API：`http://localhost:11434/api/generate`
- 超时：120秒

---

## 6. 结构化数据输出

### 6.1 输出文件结构

```
demo_output_B/demoC/
├── markdown/
│   └── 000001/
│       └── 2021-1212533363.md    # 解析后的markdown文件
├── outputs/
│   ├── base_records_demo.csv     # 结构化CSV数据
│   └── base_records_demo.jsonl   # 结构化JSONL数据
└── extract_demo.py               # 字段提取脚本
```

### 6.2 CSV字段说明

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| doc_id | str | 文档ID |
| stock_code | str | 银行代码 |
| company_name | str | 银行名称 |
| report_year | int | 报告年份 |
| issue_name | str | 议题名称 |
| section_title | str | 章节标题 |
| source_page | int | 证据来源页码 |
| evidence_snippet | str | 证据片段（原文） |
| has_policy_ref | bool | 政策引用标记 |
| has_scope_statement | bool | 范围声明标记 |
| has_case_study | bool | 案例研究标记 |
| has_kpi_value | bool | KPI数值标记 |
| has_yoy_change | bool | 同比变化标记 |
| has_method_note | bool | 方法说明标记 |
| has_assurance | bool | 第三方鉴证标记 |
| in_material_matrix | bool | 实质性矩阵标记 |
| risk_tone | str | 风险语调 |
| matrix_importance | str | 矩阵重要性 |
| verifiability_score | int | 可核查性评分 |
| spotlight_bias_flag | bool | 聚焦偏差标记 |

---

## 7. 给学生的观察任务

请学生打开一条 `base_records_demo.csv`，追溯：

```
base_records_demo.csv
 -> section_locations_demo1.csv
 -> markdown/000001/2021-1212533363.md
 -> data/pdf/*.pdf
 -> metadata.csv
```

回答以下问题：

1. **哪个字段对可核查性评分贡献最大？**
   - 答：has_kpi_value（KPI数值）和has_yoy_change（同经变化）贡献最大

2. **evidence_snippet是否真的出现在markdown原文里？**
   - 答：需要人工核对，确保evidence_snippet是原文片段，不能是模型编造

3. **如果所有布尔字段都为False，可核查性评分是多少？**
   - 答：0分（最低分）

4. **spotlight_bias_flag什么情况下会触发？**
   - 答：当matrix_importance为"高"但verifiability_score≤2时触发

---

## 8. 完整流程演示

### 8.1 端到端运行

```bash
# A同学工作（MinerU解析 + Section Routing）
python src/parse_docs.py                # MinerU解析
python src/route_sections.py           # Section Routing

# C同学工作（规则字段抽取）
cd demo_output_B/demoC
python extract_demo.py                  # 字段提取

# 查看输出结果
cat outputs/base_records_demo.csv
```

### 8.2 输出文件清单

| 文件 | 说明 | 格式 |
|------|------|------|
| `section_locations_demo1.csv` | 章节定位结果（上游） | CSV |
| `base_records_demo.csv` | 结构化字段记录（下游） | CSV |
| `base_records_demo.jsonl` | 结构化字段记录（下游） | JSONL |

---

## 9. 工作上下游衔接

### 9.1 上下游接口

**上游输出**（A同学）：
- `section_locations_demo1.csv`：章节定位结果
- `sections_demo.jsonl`：章节定位详情
- `markdown/`：解析后的markdown文件目录

**下游输入**（C同学）：
- `section_locations_demo1.csv`：作为字段提取的输入
- `markdown/`：作为文本内容的来源

**下游输出**（C同学）：
- `base_records_demo.csv`：包含所有规则字段、LLM字段和派生字段的结构化数据

### 9.2 数据流向图

```
┌─────────────────┐
│   PDF文档       │
└────────┬────────┘
         │ MinerU解析
         ▼
┌─────────────────┐
│   Markdown      │
└────────┬────────┘
         │ Section Routing
         ▼
┌─────────────────┐     ┌─────────────────┐
│ section_locations│────▶│  规则字段提取   │
│   .csv           │     │  LLM字段提取    │
└─────────────────┘     │  派生字段计算   │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ base_records    │
                        │   .csv/.jsonl   │
                        └─────────────────┘
```

---

## 附录：常见错误

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| 找不到markdown文件 | doc_id与实际文件名不匹配 | 检查markdown目录结构和doc_id |
| 可核查性评分全0 | 关键词未匹配 | 检查关键词库配置 |
| evidence_snippet为空 | 文本分割问题 | 检查HTML过滤和文本处理逻辑 |
| LLM连接失败 | Ollama服务未启动 | 启动Ollama服务：ollama serve |

---

## 附录：环境配置

### C同学工作环境配置

```bash
# 1. 安装Python依赖
pip install pandas numpy matplotlib seaborn

# 2. 配置Ollama（可选，用于LLM字段提取）
ollama pull huihui_ai/deepseek-r1-abliterated:1.5b
ollama serve

# 3. 验证Ollama服务
curl http://localhost:11434/api/tags
```

### 运行命令汇总

```bash
# 进入demoC目录
cd demo_output_B/demoC

# 运行字段提取
python extract_demo.py

# 查看输出
cat outputs/base_records_demo.csv

# 输出字段统计
python -c "import pandas as pd; df=pd.read_csv('outputs/base_records_demo.csv'); print(df['verifiability_score'].describe())"
```

---

*上游工作：A同学（MinerU解析 + Section Routing）*  
*下游工作：C同学（规则字段抽取 + LLM字段抽取 + 派生字段计算）*  
*参考课程: Week 13 & Lab Week 13 - https://ml-nlp.netlify.app/*