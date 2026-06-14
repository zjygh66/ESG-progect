"""
正式项目 PDF 解析脚本
使用 MinerU API 将巨潮 PDF 转换为 Markdown

要求：
1. 必须配置有效的 MINERU_API_KEY
2. MinerU 返回失败时脚本直接退出
3. 解析结果为空时脚本直接退出
4. 输出统一结构：doc_id、title、pdf_path、markdown_path、pages
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 设置控制台编码
sys.stdout.reconfigure(encoding='utf-8')

# 尝试导入 MinerU
try:
    from magic_pdf import magic_pdf
    MINERU_AVAILABLE = True
except ImportError:
    MINERU_AVAILABLE = False


def check_mineru_key() -> str:
    """检查 MinerU API Key 是否配置"""
    api_key = os.getenv("MINERU_API_KEY")
    
    if not api_key:
        print("❌ 错误：未配置 MINERU_API_KEY 环境变量")
        print("请设置环境变量：export MINERU_API_KEY=your_api_key")
        print("或创建 .env 文件并添加：MINERU_API_KEY=your_api_key")
        sys.exit(1)
    
    if not MINERU_AVAILABLE:
        print("❌ 错误：未安装 magic_pdf 库")
        print("请运行：pip install magic_pdf")
        sys.exit(1)
    
    return api_key


def parse_with_mineru(pdf_path: str, api_key: str) -> dict:
    """
    使用 MinerU API 解析 PDF
    
    Args:
        pdf_path: PDF 文件路径
        api_key: MinerU API Key
    
    Returns:
        dict: 解析结果，包含 pages 等字段
    
    Raises:
        SystemExit: 解析失败时退出
    """
    print(f"📄 正在解析: {pdf_path}")
    
    try:
        # 使用 MinerU API 解析
        result = magic_pdf.parse(
            pdf_path,
            api_key=api_key,
            options={
                "return_type": "markdown",
                "include_pages": True
            }
        )
        
        # 检查解析结果
        if not result:
            print(f"❌ MinerU 返回空结果")
            sys.exit(1)
        
        # 检查是否有内容
        if "content" not in result or not result["content"]:
            print(f"❌ MinerU 解析内容为空")
            sys.exit(1)
        
        # 检查 pages 字段
        if "pages" not in result or not result["pages"]:
            print(f"❌ MinerU 未返回页面信息")
            sys.exit(1)
        
        print(f"✅ 解析成功: {len(result['pages'])} 页")
        return result
        
    except Exception as e:
        print(f"❌ MinerU 解析失败: {str(e)}")
        sys.exit(1)


def parse_pdf(pdf_path: str, output_dir: str, api_key: str) -> dict:
    """
    解析单个 PDF 文件并保存 Markdown
    
    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        api_key: MinerU API Key
    
    Returns:
        dict: 文档元数据
    """
    # 生成 doc_id
    doc_id = Path(pdf_path).stem
    
    # 解析 PDF
    result = parse_with_mineru(pdf_path, api_key)
    
    # 提取标题（从内容或文件名）
    title = result.get("title", "")
    if not title:
        title = Path(pdf_path).name.replace(".pdf", "")
    
    # 生成输出路径
    markdown_path = os.path.join(output_dir, f"{doc_id}.md")
    
    # 保存 Markdown
    os.makedirs(output_dir, exist_ok=True)
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(result["content"])
    
    # 返回统一结构
    return {
        "doc_id": doc_id,
        "title": title,
        "pdf_path": os.path.abspath(pdf_path),
        "markdown_path": os.path.abspath(markdown_path),
        "pages": result["pages"],
        "page_count": len(result["pages"])
    }


def parse_batch(pdf_dir: str, output_dir: str, metadata_path: str):
    """
    批量解析 PDF 文件
    
    Args:
        pdf_dir: PDF 文件目录
        output_dir: Markdown 输出目录
        metadata_path: 元数据输出路径
    """
    # 检查 MinerU Key
    api_key = check_mineru_key()
    
    # 查找 PDF 文件
    pdf_files = list(Path(pdf_dir).rglob("*.pdf"))
    
    if not pdf_files:
        print("❌ 未找到 PDF 文件")
        sys.exit(1)
    
    print(f"📁 找到 {len(pdf_files)} 个 PDF 文件")
    
    # 解析所有 PDF
    docs_metadata = []
    
    for pdf_path in pdf_files:
        try:
            doc_meta = parse_pdf(str(pdf_path), output_dir, api_key)
            docs_metadata.append(doc_meta)
            print(f"📝 已处理: {doc_meta['title']}")
        except SystemExit:
            # 解析失败时退出整个脚本
            raise
        except Exception as e:
            print(f"⚠️ 跳过 {pdf_path.name}: {e}")
            continue
    
    # 保存元数据
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        for doc in docs_metadata:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    
    print(f"\n✅ 完成！成功解析 {len(docs_metadata)} 个文档")
    print(f"📄 元数据已保存到: {metadata_path}")
    print(f"📁 Markdown 文件已保存到: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="正式项目 PDF 解析脚本")
    parser.add_argument("--pdf-dir", required=True, help="PDF 文件目录")
    parser.add_argument("--output-dir", required=True, help="Markdown 输出目录")
    parser.add_argument("--metadata-path", required=True, help="元数据输出路径")
    
    args = parser.parse_args()
    
    # 检查参数
    if not os.path.exists(args.pdf_dir):
        print(f"❌ PDF 目录不存在: {args.pdf_dir}")
        sys.exit(1)
    
    # 执行批量解析
    parse_batch(args.pdf_dir, args.output_dir, args.metadata_path)


if __name__ == "__main__":
    main()
