"""
章节路由脚本
根据关键词和目录结构定位议题章节
"""
import os
import re
import csv
import yaml
import sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


class SectionRouter:
    """章节路由定位器"""
    
    def __init__(self, rules_path: str = None):
        self.rules = self._load_rules(rules_path)
        self.topics = self.rules.get("topics", [])
        self.confidence_thresholds = self.rules.get("confidence", {})
        
    def _load_rules(self, rules_path: str = None) -> dict:
        """加载章节规则"""
        if rules_path and os.path.exists(rules_path):
            with open(rules_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # 默认规则
        return {
            "topics": [
                {"name": "风险管理", "keywords": ["风险管理", "风险控制", "信用风险"]},
                {"name": "公司治理", "keywords": ["公司治理", "董事会", "监事会", "内部控制"]},
                {"name": "绿色金融", "keywords": ["绿色金融", "ESG", "碳中和", "可持续发展"]},
                {"name": "消费者权益保护", "keywords": ["消费者权益", "消费者保护", "客户权益"]},
                {"name": "普惠金融", "keywords": ["普惠金融", "小微企业", "三农"]},
                {"name": "乡村振兴", "keywords": ["乡村振兴", "农村金融", "涉农"]},
            ],
            "confidence": {"high": 80, "medium": 60, "low": 40}
        }
    
    def route_sections(self, markdown_path: str, doc_id: str) -> list:
        """
        定位文档中的议题章节
        
        Args:
            markdown_path: Markdown 文件路径
            doc_id: 文档ID
            
        Returns:
            list: 章节位置列表
        """
        if not os.path.exists(markdown_path):
            return []
        
        # 读取 Markdown 内容
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取目录结构
        toc = self._extract_toc(content)
        
        # 定位章节
        sections = []
        for topic in self.topics:
            section = self._find_topic_section(
                doc_id, topic, toc, content
            )
            if section:
                sections.append(section)
        
        return sections
    
    def _extract_toc(self, content: str) -> list:
        """提取目录结构"""
        toc = []
        
        # 匹配章节标题
        # 第X章 或 ## 标题
        patterns = [
            r'第([一二三四五六七八九十百千万\d]+)[章节]',  # 第X章
            r'^#{1,3}\s+(.+)$',  # Markdown 标题
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            
            # 匹配第X章
            match = re.match(r'第([一二三四五六七八九十百千万\d]+)[章节]', line)
            if match:
                chapter_num = match.group(1)
                title = re.sub(r'第[一二三四五六七八九十百千万\d]+[章节]', '', line).strip()
                toc.append({
                    "type": "chapter",
                    "number": chapter_num,
                    "title": title,
                    "raw": line
                })
                continue
            
            # 匹配 Markdown 标题
            match = re.match(r'^#{1,3}\s+(.+)$', line)
            if match:
                toc.append({
                    "type": "heading",
                    "level": len(re.match(r'^(#+)\s+', line).group(1)),
                    "title": match.group(1),
                    "raw": line
                })
        
        return toc
    
    def _find_topic_section(self, doc_id: str, topic: dict, toc: list, content: str) -> dict:
        """查找议题章节"""
        topic_name = topic["name"]
        keywords = topic["keywords"]
        
        best_match = None
        best_confidence = 0
        
        for item in toc:
            title = item.get("title", "") or item.get("raw", "")
            
            # 关键词匹配
            for kw in keywords:
                if kw in title:
                    # 精确匹配权重更高
                    confidence = 85 if kw == topic_name else 70
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = item
        
        if not best_match:
            return None
        
        # 估算页码范围 (基于内容位置)
        start_page = self._estimate_page(content, best_match)
        
        return {
            "doc_id": doc_id,
            "issue_name": topic_name,
            "section_title": best_match.get("title") or best_match.get("raw", ""),
            "start_page": start_page,
            "end_page": start_page + 5,  # 估算5页
            "confidence": best_confidence
        }
    
    def _estimate_page(self, content: str, toc_item: str) -> int:
        """估算页码"""
        # 简单实现：按字符数估算
        # 假设每页约 3000 字符
        pos = content.find(toc_item if isinstance(toc_item, str) else toc_item.get("raw", ""))
        if pos < 0:
            return 1
        return max(1, pos // 3000 + 1)


def route_batch(markdown_dir: str, output_csv: str, rules_path: str = None):
    """
    批量路由章节
    
    Args:
        markdown_dir: Markdown 文件目录
        output_csv: 输出 CSV 路径
        rules_path: 规则文件路径
    """
    router = SectionRouter(rules_path)
    
    md_files = list(Path(markdown_dir).rglob("*.md"))
    print(f"找到 {len(md_files)} 个 Markdown 文件")
    
    all_sections = []
    
    for md_path in md_files:
        doc_id = md_path.stem
        sections = router.route_sections(str(md_path), doc_id)
        all_sections.extend(sections)
        
        if sections:
            print(f"✓ {doc_id}: 找到 {len(sections)} 个议题")
        else:
            print(f"⚠ {doc_id}: 未找到议题")
    
    # 保存结果
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        if all_sections:
            writer = csv.DictWriter(f, fieldnames=all_sections[0].keys())
            writer.writeheader()
            writer.writerows(all_sections)
    
    print(f"\n保存结果到: {output_csv}")
    print(f"共定位 {len(all_sections)} 个章节")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="章节路由工具")
    parser.add_argument("--markdown-dir", required=True, help="Markdown 目录")
    parser.add_argument("--output-csv", required=True, help="输出 CSV 路径")
    parser.add_argument("--rules", help="规则文件路径")
    
    args = parser.parse_args()
    
    route_batch(args.markdown_dir, args.output_csv, args.rules)
