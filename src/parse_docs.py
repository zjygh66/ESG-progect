"""
PDF 解析脚本
使用 MinerU API 或 pdfminer.six 解析 PDF 为 Markdown
"""
import os
import sys
import json
import yaml
from pathlib import Path

# 设置控制台编码
sys.stdout.reconfigure(encoding='utf-8')

# 尝试导入 MinerU
try:
    from magic_pdf import magic_pdf
    MINERU_AVAILABLE = True
except ImportError:
    MINERU_AVAILABLE = False

# 尝试导入 pdfminer
try:
    from pdfminer.high_level import extract_text
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False


class PDFParser:
    """PDF 解析器"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.api_key = os.getenv("MINERU_API_KEY")
        
    def _load_config(self, config_path: str = None) -> dict:
        """加载配置"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {
            "parser": {
                "primary": "pdfminer",
                "fallback": "pdfminer"
            }
        }
    
    def parse(self, pdf_path: str, output_path: str = None) -> dict:
        """
        解析 PDF 文件
        
        Args:
            pdf_path: PDF 文件路径
            output_path: 输出 Markdown 路径
            
        Returns:
            dict: 解析结果，包含 doc_id, pages 等
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        # 生成 doc_id (从文件名提取)
        doc_id = Path(pdf_path).stem
        
        # 解析策略
        parser_type = self.config.get("parser", {}).get("primary", "pdfminer")
        
        if parser_type == "mineru_api" and MINERU_AVAILABLE and self.api_key:
            return self._parse_with_mineru(pdf_path, doc_id, output_path)
        else:
            return self._parse_with_pdfminer(pdf_path, doc_id, output_path)
    
    def _parse_with_mineru(self, pdf_path: str, doc_id: str, output_path: str) -> dict:
        """使用 MinerU API 解析"""
        print(f"使用 MinerU API 解析: {doc_id}")
        
        # MinerU 解析逻辑
        # result = magic_pdf.parse(pdf_path, api_key=self.api_key)
        
        # 简化实现
        return self._parse_with_pdfminer(pdf_path, doc_id, output_path)
    
    def _parse_with_pdfminer(self, pdf_path: str, doc_id: str, output_path: str) -> dict:
        """使用 pdfminer 解析"""
        print(f"使用 pdfminer 解析: {doc_id}")
        
        try:
            # 提取文本
            text = extract_text(pdf_path)
            
            # 按页分割 (简单实现)
            pages = []
            lines = text.split('\n')
            current_page = []
            current_page_no = 1
            
            for line in lines:
                # 检测分页标记 (需要更精确的实现)
                if line.strip() == '' and len(current_page) > 50:
                    pages.append({
                        "page_no": current_page_no,
                        "text": '\n'.join(current_page)
                    })
                    current_page = []
                    current_page_no += 1
                else:
                    current_page.append(line)
            
            # 最后一页
            if current_page:
                pages.append({
                    "page_no": current_page_no,
                    "text": '\n'.join(current_page)
                })
            
            # 生成 Markdown
            markdown_content = self._generate_markdown(pages)
            
            # 保存文件
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
            
            return {
                "doc_id": doc_id,
                "pages": pages,
                "page_count": len(pages),
                "markdown_path": output_path
            }
            
        except Exception as e:
            print(f"解析失败: {e}")
            raise
    
    def _generate_markdown(self, pages: list) -> str:
        """生成 Markdown 格式"""
        md_lines = []
        
        for page in pages:
            md_lines.append(f"## 第 {page['page_no']} 页\n")
            md_lines.append(page['text'])
            md_lines.append("\n---\n\n")
        
        return '\n'.join(md_lines)


def parse_batch(pdf_dir: str, output_dir: str, bank_code: str = None):
    """
    批量解析 PDF
    
    Args:
        pdf_dir: PDF 目录
        output_dir: 输出目录
        bank_code: 银行代码 (可选)
    """
    parser = PDFParser()
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_files = list(Path(pdf_dir).glob("**/*.pdf"))
    print(f"找到 {len(pdf_files)} 个 PDF 文件")
    
    results = []
    
    for pdf_path in pdf_files:
        try:
            # 生成输出路径
            doc_id = pdf_path.stem
            output_path = os.path.join(output_dir, f"{doc_id}.md")
            
            # 解析
            result = parser.parse(str(pdf_path), output_path)
            result["pdf_path"] = str(pdf_path)
            results.append(result)
            
            print(f"✓ 解析成功: {doc_id}")
            
        except Exception as e:
            print(f"✗ 解析失败: {pdf_path.name} - {e}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF 解析工具")
    parser.add_argument("--pdf-dir", required=True, help="PDF 目录")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--bank-code", help="银行代码")
    
    args = parser.parse_args()
    
    results = parse_batch(args.pdf_dir, args.output_dir, args.bank_code)
    print(f"\n完成: 成功 {len(results)}/{len(list(Path(args.pdf_dir).glob('**/*.pdf')))} 个文件")
