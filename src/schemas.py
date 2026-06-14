"""
Pydantic 数据模型定义
用于验证和结构化解析结果
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class PageContent(BaseModel):
    """单页内容"""
    page_no: int = Field(..., description="页码")
    text: str = Field(..., description="页面文本内容")


class ParsedDocument(BaseModel):
    """解析后的文档模型"""
    doc_id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    pdf_path: str = Field(..., description="原始PDF路径")
    markdown_path: str = Field(..., description="解析后Markdown路径")
    pages: List[PageContent] = Field(default_factory=list, description="页面内容列表")
    
    # 元数据
    bank_code: Optional[str] = Field(None, description="银行代码")
    year: Optional[int] = Field(None, description="报告年份")
    page_count: int = Field(0, description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "2021-1212533363",
                "title": "平安银行2021年社会责任报告",
                "pdf_path": "/path/to/pdf/2021-1212533363.pdf",
                "markdown_path": "/path/to/markdown/2021-1212533363.md",
                "pages": [
                    {"page_no": 1, "text": "..."},
                    {"page_no": 2, "text": "..."}
                ],
                "bank_code": "000001",
                "year": 2021,
                "page_count": 100
            }
        }


class SectionLocation(BaseModel):
    """章节位置信息"""
    doc_id: str = Field(..., description="文档ID")
    issue_name: str = Field(..., description="议题名称")
    section_title: str = Field(..., description="章节标题")
    start_page: Optional[int] = Field(None, description="起始页码")
    end_page: Optional[int] = Field(None, description="结束页码")
    confidence: float = Field(..., ge=0, le=100, description="置信度(0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "2021-1212533363",
                "issue_name": "风险管理",
                "section_title": "第六章 风险管理",
                "start_page": 15,
                "end_page": 28,
                "confidence": 85.0
            }
        }


class ExtractedContent(BaseModel):
    """抽取的内容模型"""
    doc_id: str = Field(..., description="文档ID")
    topic: str = Field(..., description="议题名称")
    content: str = Field(..., description="抽取的内容")
    difficulty: str = Field(..., description="难度等级: easy/medium/hard")
    source_pages: str = Field(..., description="来源页码")
    
    # 质量指标
    char_count: int = Field(0, description="字符数")
    has_metrics: bool = Field(False, description="是否包含定量指标")
    confidence: float = Field(0, description="抽取置信度")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "2021-1212533363",
                "topic": "风险管理",
                "content": "本行建立了完善的风险管理体系...",
                "difficulty": "medium",
                "source_pages": "15-28",
                "char_count": 5000,
                "has_metrics": True,
                "confidence": 85.0
            }
        }


class ValidationError(BaseModel):
    """验证错误模型"""
    doc_id: str = Field(..., description="文档ID")
    field: str = Field(..., description="错误字段")
    expected: str = Field(..., description="期望值")
    actual: str = Field(..., description="实际值")
    severity: str = Field("warning", description="严重程度: error/warning/info")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
