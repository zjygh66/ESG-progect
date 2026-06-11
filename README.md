# 金融文本智能课程项目

## 项目目标

本项目旨在构建一个基于巨潮资讯网 PDF 文档的金融文本智能分析系统。主要功能包括：

1. **PDF 文档解析**：从巨潮资讯网获取的 PDF 文档中提取文本内容
2. **文本智能分析**：利用 LLM 技术对金融文本进行深度分析
3. **信息抽取**：从非结构化文本中抽取关键金融信息
4. **结果评估**：对分析结果进行评估和报告生成

## 目录结构

```
project_B/
├── README.md              # 项目说明文档
├── ai_worklog.md          # AI 辅助开发工作日志
├── .env.example           # 环境变量配置示例
├── requirements.txt       # Python 依赖包
├── run.py                 # 主运行脚本
├── configs/               # 配置文件目录
│   └── task.yaml          # 任务配置文件
├── data/                  # 数据目录
│   ├── metadata/          # 元数据存储
│   ├── pdf/               # 原始 PDF 文件
│   └── parsed/            # 解析后的文本数据
├── src/                   # 源代码目录
│   ├── __init__.py        # 包初始化文件
│   ├── cninfo/            # 巨潮资讯网数据获取模块
│   ├── llm/               # LLM 调用模块
│   ├── mineru/            # PDF 解析模块
│   ├── workflow/          # 工作流管理模块
│   └── evaluation/        # 评估模块
├── outputs/               # 输出目录
│   ├── logs/              # 运行日志
│   ├── results/           # 分析结果
│   └── reports/           # 生成的报告
└── tests/                 # 测试代码目录
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目（如果适用）
cd project_B

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，填入必要的配置信息
# 注意：不要将 .env 文件提交到版本控制系统
```

### 3. 运行项目

```bash
# 查看帮助信息
python run.py --help

# 查看版本信息
python run.py --version

# 执行特定任务（示例）
python run.py --task parse --config configs/task.yaml
python run.py --task analyze --verbose
python run.py --task all
```

## 开发指南

### 模块说明

- **cninfo**: 负责从巨潮资讯网获取 PDF 文档及相关元数据
- **mineru**: 使用 MinerU 等工具解析 PDF 文档
- **llm**: 封装 LLM API 调用，提供文本分析能力
- **workflow**: 编排各模块工作流程
- **evaluation**: 评估分析结果的质量和准确性

### 开发流程

1. 在 `ai_worklog.md` 中记录开发过程
2. 遵循模块化设计原则
3. 编写单元测试（tests 目录）
4. 定期提交代码并更新文档

## 注意事项

- 本项目为课程项目骨架，业务逻辑待实现
- 请勿在代码中硬编码 API Key 等敏感信息
- 所有敏感配置应通过 `.env` 文件管理
- 遵守巨潮资讯网的数据使用规范

## 许可证

本项目仅用于课程学习目的。