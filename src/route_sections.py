"""
章节路由脚本
根据关键词和目录结构定位议题章节
"""
import os
import re
import csv
import json
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
        self.strategy = self.rules.get("strategy", {})
        self.enable_fuzzy = self.strategy.get("enable_fuzzy_match", True)
        self.min_keyword_matches = self.strategy.get("min_keyword_matches", 1)
        
    def _load_rules(self, rules_path: str = None) -> dict:
        """加载章节规则"""
        if rules_path and os.path.exists(rules_path):
            with open(rules_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # 默认规则（扩展至20个关键词/议题）
        return {
            "topics": [
                {"name": "风险管理", "keywords": ["风险管理", "风险控制", "信用风险", "风险管控", "全面风险管理", 
                                                  "风险评估", "风险防范", "风险识别", "风险应对", "风险监测",
                                                  "风险敞口", "流动性风险", "利率风险", "汇率风险", "合规风险",
                                                  "战略风险", "声誉风险", "操作风险", "市场风险", "信用风险管理"]},
                {"name": "公司治理", "keywords": ["公司治理", "董事会", "监事会", "内部控制", "三会一层",
                                                  "股东大会", "独立董事", "审计委员会", "薪酬考核", "治理结构",
                                                  "信息披露", "关联交易", "合规管理", "风险管理委员会", "战略委员会",
                                                  "提名委员会", "监事", "高管层", "公司章程", "治理机制"]},
                {"name": "绿色金融", "keywords": ["绿色金融", "ESG", "碳中和", "可持续发展", "绿色信贷",
                                                  "碳达峰", "环保", "环境", "社会责任", "绿色债券",
                                                  "节能减排", "清洁能源", "气候风险", "绿色投资", "ESG报告",
                                                  "可持续金融", "低碳", "绿色发展", "环境责任", "绿色保险"]},
                {"name": "消费者权益保护", "keywords": ["消费者权益", "消费者保护", "客户权益", "消保", "信息安全",
                                                        "客户隐私", "投诉处理", "服务质量", "金融消费者", "客户服务",
                                                        "权益保护", "信息披露", "公平交易", "客户教育", "数据安全",
                                                        "个人信息保护", "消费者教育", "服务承诺", "投诉管理", "客户满意度"]},
                {"name": "普惠金融", "keywords": ["普惠金融", "小微企业", "小微金融", "三农", "中小企业",
                                                  "小额信贷", "农村金融", "县域金融", "乡镇企业", "民营经济",
                                                  "创业创新", "扶贫", "乡村金融", "小额贷款", "普惠服务",
                                                  "民生金融", "微型企业", "个体工商户", "农户贷款", "普惠信贷"]},
                {"name": "乡村振兴", "keywords": ["乡村振兴", "农村金融", "涉农", "县域", "支农",
                                                  "农业", "农民", "农村", "涉农贷款", "乡村发展",
                                                  "现代农业", "精准扶贫", "农村经济", "农村建设", "乡村建设",
                                                  "农业产业化", "农田水利", "农村基础设施", "农产品", "乡村旅游"]},
            ],
            "confidence": {"high": 70, "medium": 50, "low": 30},
            "strategy": {"enable_fuzzy_match": True, "enable_synonym_match": True, "min_keyword_matches": 1}
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
            section = self._find_topic_section(doc_id, topic, toc, content)
            if section:
                sections.append(section)
        
        return sections
    
    def _extract_toc(self, content: str) -> list:
        """提取目录结构（增强版）"""
        toc = []
        
        # 匹配章节标题的多种模式
        patterns = [
            r'([一二三四五六七八九十百千万\d]+)[、.．](.+?)(?=\d|$)',  # 1、标题 或 一、标题
            r'^#{1,4}\s+(.+?)(?:\s*\|\s*\d+)?$',  # Markdown 标题 (可能带页码)
            r'【(.+?)】',  # 【标题】
            r'(.+?)\s*[-—–—→→]\s*\d+',  # 标题 - 页码
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            
            # 跳过过短或过长的行
            if len(line) < 2 or len(line) > 200:
                continue
            
            # 匹配第X章
            match = re.match(r'第([一二三四五六七八九十百千万\d]+)[章节](.+)$', line)
            if match:
                chapter_num = match.group(1)
                title = match.group(2).strip()
                toc.append({
                    "type": "chapter",
                    "number": chapter_num,
                    "title": title,
                    "raw": line,
                    "score": 100
                })
                continue
            
            # 匹配 1、标题 格式
            match = re.match(r'^([一二三四五六七八九十\d]+)[、.．]\s*(.+)$', line)
            if match:
                toc.append({
                    "type": "numbered",
                    "number": match.group(1),
                    "title": match.group(2).strip(),
                    "raw": line,
                    "score": 90
                })
                continue
            
            # 匹配 Markdown 标题
            match = re.match(r'^(#+)\s+(.+?)(?:\s*\|\s*\d+)?$', line)
            if match:
                toc.append({
                    "type": "heading",
                    "level": len(match.group(1)),
                    "title": match.group(2).strip(),
                    "raw": line,
                    "score": 80 if len(match.group(1)) <= 2 else 60
                })
                continue
            
            # 匹配目录项（标题 - 页码）
            match = re.match(r'^(.+?)\s*[-—–→]\s*\d+$', line)
            if match:
                toc.append({
                    "type": "toc_item",
                    "title": match.group(1).strip(),
                    "raw": line,
                    "score": 70
                })
                continue
            
            # 匹配 【标题】格式
            match = re.match(r'【(.+?)】', line)
            if match:
                toc.append({
                    "type": "bracket",
                    "title": match.group(1).strip(),
                    "raw": line,
                    "score": 60
                })
        
        return toc
    
    def _find_topic_section(self, doc_id: str, topic: dict, toc: list, content: str) -> dict:
        """查找议题章节（增强版）"""
        topic_name = topic["name"]
        keywords = topic["keywords"]
        section_patterns = topic.get("section_patterns", [])
        
        best_match = None
        best_confidence = 0
        best_title = ""
        
        # 首先在目录中查找
        for item in toc:
            title = item.get("title", "") or item.get("raw", "")
            item_score = item.get("score", 50)
            
            # 计算匹配度
            matches = self._count_keyword_matches(title, keywords)
            
            if matches > 0:
                # 计算置信度
                confidence = self._calculate_confidence(matches, len(keywords), item_score, title, topic_name)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = item
                    best_title = title
        
        # 如果目录中没找到，直接在内容中搜索
        if not best_match and self.enable_fuzzy:
            for kw in keywords:
                if kw in content:
                    # 找到包含关键词的段落
                    confidence = 50 + len(kw) * 2  # 关键词越长置信度越高
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = {"type": "content_match", "title": kw, "raw": kw, "score": 40}
                        best_title = f"包含'{kw}'的章节"
        
        if not best_match:
            return None
        
        # 估算页码范围
        start_page = self._estimate_page(content, best_match)
        
        return {
            "doc_id": doc_id,
            "issue_name": topic_name,
            "section_title": best_title,
            "start_page": start_page,
            "end_page": start_page + 6,  # 增加估算页数
            "confidence": min(100, best_confidence),
            "quality_issue": self._assess_quality(best_confidence)
        }
    
    def _count_keyword_matches(self, text: str, keywords: list) -> int:
        """计算关键词匹配数量"""
        count = 0
        for kw in keywords:
            if kw in text:
                count += 1
        return count
    
    def _calculate_confidence(self, matches: int, total_keywords: int, item_score: int, title: str, topic_name: str) -> int:
        """计算置信度"""
        # 基础置信度：匹配比例
        base_confidence = (matches / max(total_keywords, 1)) * 60
        
        # 目录类型加成
        type_bonus = item_score / 10
        
        # 精确匹配加成
        exact_bonus = 20 if topic_name in title else 0
        
        # 标题长度加成（标题越长信息越丰富）
        title_bonus = min(len(title) // 10, 10)
        
        return int(base_confidence + type_bonus + exact_bonus + title_bonus)
    
    def _estimate_page(self, content: str, toc_item: dict) -> int:
        """估算页码"""
        raw_text = toc_item.get("raw", "")
        if not raw_text:
            return 1
            
        pos = content.find(raw_text)
        if pos < 0:
            # 如果找不到，使用内容长度估算
            pos = len(content) // 2
            
        # 假设每页约 3500 字符
        return max(1, pos // 3500 + 1)
    
    def _assess_quality(self, confidence: int) -> str:
        """评估章节质量"""
        if confidence >= self.confidence_thresholds.get("high", 70):
            return "ok"
        elif confidence >= self.confidence_thresholds.get("medium", 50):
            return "ok"
        elif confidence >= self.confidence_thresholds.get("low", 30):
            return "low_confidence"
        else:
            return "wrong_section"


def route_batch(markdown_dir: str, output_csv: str, output_jsonl: str = None, rules_path: str = None):
    """
    批量路由章节
    
    Args:
        markdown_dir: Markdown 文件目录
        output_csv: 输出 CSV 路径
        output_jsonl: 输出 JSONL 路径
        rules_path: 规则文件路径
    """
    router = SectionRouter(rules_path)
    
    md_files = list(Path(markdown_dir).rglob("*.md"))
    print(f"找到 {len(md_files)} 个 Markdown 文件")
    
    all_sections = []
    success_count = 0
    fail_count = 0
    
    for md_path in md_files:
        doc_id = md_path.stem
        sections = router.route_sections(str(md_path), doc_id)
        all_sections.extend(sections)
        
        if sections:
            success_count += 1
            print(f"✓ {doc_id}: 找到 {len(sections)} 个议题")
        else:
            fail_count += 1
            print(f"✗ {doc_id}: 未找到议题")
    
    # 保存 CSV 结果
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        if all_sections:
            writer = csv.DictWriter(f, fieldnames=all_sections[0].keys())
            writer.writeheader()
            writer.writerows(all_sections)
    
    print(f"\n保存 CSV 到: {output_csv}")
    
    # 保存 JSONL 结果
    if output_jsonl:
        os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
        with open(output_jsonl, 'w', encoding='utf-8') as f:
            for section in all_sections:
                f.write(json.dumps(section, ensure_ascii=False) + "\n")
        print(f"保存 JSONL 到: {output_jsonl}")
    
    # 统计结果
    total_docs = len(md_files)
    total_topics = total_docs * 6
    success_topics = len(all_sections)
    
    print(f"\n=== 统计结果 ===")
    print(f"文档总数: {total_docs}")
    print(f"成功定位文档: {success_count} ({(success_count/total_docs)*100:.1f}%)")
    print(f"议题总数(理论): {total_topics}")
    print(f"成功定位议题: {success_topics} ({(success_topics/total_topics)*100:.1f}%)")
    print(f"共定位 {len(all_sections)} 个章节")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="章节路由工具")
    parser.add_argument("--markdown-dir", required=True, help="Markdown 目录")
    parser.add_argument("--output-csv", required=True, help="输出 CSV 路径")
    parser.add_argument("--output-jsonl", help="输出 JSONL 路径")
    parser.add_argument("--rules", help="规则文件路径")
    
    args = parser.parse_args()
    
    route_batch(args.markdown_dir, args.output_csv, args.output_jsonl, args.rules)