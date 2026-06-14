"""
ESG 报告字段数据模型

定义银行 ESG 报告结构化解析的数据结构，包含规则字段、派生字段和 LLM 字段。
"""

from typing import Optional
from pydantic import BaseModel, Field


class IssueRecord(BaseModel):
    """
    ESG 议题记录数据模型
    
    包含从银行 ESG 报告中抽取的所有字段，用于存储和处理结构化数据。
    """
    
    # ========== 基础字段 ==========
    doc_id: str = Field(description="文档唯一标识")
    company_code: str = Field(description="股票代码")
    report_year: int = Field(description="报告年份（2021-2025）")
    issue_name: str = Field(description="议题名称（6个标准议题之一）")
    anchor_type: str = Field(description="锚点类型（matrix/narrative/kpi）")
    source_page: int = Field(description="证据页码")
    evidence_snippet: str = Field(description="原文片段（1-3句）")
    
    # ========== 矩阵字段（A组） ==========
    in_material_matrix: bool = Field(description="是否在实质性矩阵中")
    matrix_importance: str = Field(description="矩阵重要性（高/中/低/未出现）")
    
    # ========== 正文字段（B组） ==========
    has_policy_ref: bool = Field(description="是否提及政策/办法/制度")
    has_scope_statement: bool = Field(description="是否包含范围说明")
    has_case_study: bool = Field(description="是否包含案例研究")
    risk_tone: str = Field(description="风险语调（展示性/平衡/风险透明）")
    
    # ========== 绩效表字段（C组） ==========
    has_kpi_value: bool = Field(description="是否包含量化指标")
    kpi_value: Optional[str] = Field(description="提取的KPI数值")
    has_yoy_change: bool = Field(description="是否包含同比变化")
    has_method_note: bool = Field(description="是否包含编制方法说明")
    has_assurance: bool = Field(description="是否经过第三方鉴证")
    
    # ========== 派生字段 ==========
    verifiability_score: int = Field(description="可核查性评分（0-5）")
    spotlight_bias_flag: bool = Field(description="言行偏离标志")
    
    def calculate_verifiability_score(self) -> int:
        """
        计算可核查性评分（0-5分）
        
        评分规则：
        - has_policy_ref: 1分
        - has_scope_statement: 1分
        - has_case_study: 1分
        - has_kpi_value: 1分
        - has_yoy_change: 1分
        - has_method_note: 1分
        
        总分最高为5分。
        
        返回:
            int: 0-5分
        """
        score = (
            int(self.has_policy_ref)
            + int(self.has_scope_statement)
            + int(self.has_case_study)
            + int(self.has_kpi_value)
            + int(self.has_yoy_change)
            + int(self.has_method_note)
        )
        return min(score, 5)
    
    def check_spotlight_bias(self) -> bool:
        """
        检查"言行偏离"（Spotlight Bias）
        
        判断条件：
        - matrix_importance == "高"
        - verifiability_score <= 2
        
        返回:
            bool: True表示存在言行偏离
        """
        return self.matrix_importance == "高" and self.verifiability_score <= 2
