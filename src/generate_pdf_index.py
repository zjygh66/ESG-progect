#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成PDF索引脚本
读取metadata.csv，计算PDF文件的SHA256哈希值，输出JSON Lines格式的索引文件
并从各类银行中随机抽取样本PDF
"""

import csv
import hashlib
import json
import os
import random
import re
import shutil
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def calculate_sha256(file_path):
    """计算文件的SHA256哈希值"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (FileNotFoundError, IOError):
        return None


def get_file_size(file_path):
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except (FileNotFoundError, IOError):
        return None


def extract_announcement_id(pdf_url):
    """从PDF URL中提取announcementId"""
    match = re.search(r'announcementId=(\d+)', pdf_url)
    if match:
        return match.group(1)
    return None


def get_pdf_local_path(stock_code, pdf_url, title=None, base_dir=None):
    """根据stock_code和pdf_url生成PDF的本地路径"""
    if base_dir is None:
        base_dir = PROJECT_ROOT / "data" / "pdf"
    else:
        base_dir = Path(base_dir)
    
    announcement_id = extract_announcement_id(pdf_url)
    if not announcement_id:
        return None
    
    # 优先从标题中提取年份（如"工商银行2021年社会责任报告"或"工商银行2021<em>社会</em>..."）
    year = None
    if title:
        # 移除HTML标签后再提取年份
        clean_title = re.sub(r'<[^>]+>', '', title)
        year_match = re.search(r'(\d{4})年', clean_title)
        if year_match:
            year = year_match.group(1)
        # 如果还是没有找到，尝试直接匹配4位数字（取第一个）
        if not year:
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
    
    # 如果标题中没有年份，则从URL的announcementTime中提取
    if not year:
        year_match = re.search(r'announcementTime=(\d{4})-', pdf_url)
        year = year_match.group(1) if year_match else "unknown"
    
    # 构建文件路径: {stock_code}/{year}_{announcement_id}.pdf
    pdf_dir = base_dir / stock_code
    pdf_file = pdf_dir / f"{year}_{announcement_id}.pdf"
    
    if pdf_file.exists():
        return str(pdf_file.relative_to(PROJECT_ROOT))
    return None


def categorize_bank(stock_code):
    """根据股票代码判断银行类型"""
    # 国有大行
    state_owned = ['601398', '601939', '601288', '601988', '601328', '601658']
    # 股份行
    joint_stock = ['000001', '600036', '601166', '601998', '600000', 
                   '601818', '600016', '600015', '601916']
    
    stock_code_str = str(stock_code)
    
    if stock_code_str in state_owned:
        return '国有大行'
    elif stock_code_str in joint_stock:
        return '股份行'
    else:
        return '城商行'


def generate_pdf_index(csv_path, output_path):
    """生成PDF索引JSON Lines文件"""
    index_records = []
    
    # 处理BOM问题
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stock_code = row['stock_code']
            stock_name = row['stock_name']
            title = row['announcement_title']
            publish_date = row['publish_date']
            pdf_url = row['pdf_url']
            
            # 获取本地PDF路径
            local_path = get_pdf_local_path(stock_code, pdf_url, title)
            
            # 计算SHA256和文件大小
            if local_path:
                full_path = PROJECT_ROOT / local_path
                sha256 = calculate_sha256(full_path)
                file_size = get_file_size(full_path)
            else:
                sha256 = None
                file_size = None
            
            record = {
                'doc_id': extract_announcement_id(pdf_url),
                'stock_code': stock_code,
                'title': title,
                'publish_date': publish_date,
                'pdf_url': pdf_url,
                'local_path': local_path,
                'sha256': sha256,
                'file_size_bytes': file_size
            }
            index_records.append(record)
    
    # 写入JSON Lines文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in index_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    return index_records


def select_sample_pdfs(index_records, output_dir, sample_list_path, sample_size=1):
    """从各类银行中随机抽取样本PDF"""
    # 按银行类型分组
    banks_by_category = {
        '国有大行': [],
        '股份行': [],
        '城商行': []
    }
    
    for record in index_records:
        if record['local_path']:  # 只选择存在的PDF
            category = categorize_bank(record['stock_code'])
            if category in banks_by_category:
                banks_by_category[category].append(record)
    
    # 从每个类别中随机选择样本
    selected_samples = []
    for category, records in banks_by_category.items():
        if records:
            samples = random.sample(records, min(sample_size, len(records)))
            selected_samples.extend(samples)
    
    # 确保输出目录存在
    sample_dir = Path(output_dir)
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制选中的PDF到sample目录
    copied_files = []
    for sample in selected_samples:
        src_path = PROJECT_ROOT / sample['local_path']
        dst_path = sample_dir / src_path.name
        
        try:
            shutil.copy2(src_path, dst_path)
            copied_files.append({
                'bank_name': sample['stock_code'] + ' ' + sample.get('title', ''),
                'category': categorize_bank(sample['stock_code']),
                'source_path': sample['local_path'],
                'copied_path': str(dst_path.relative_to(PROJECT_ROOT)),
                'sha256': sample['sha256'],
                'file_size': sample['file_size_bytes']
            })
        except Exception as e:
            print(f"Warning: Failed to copy {src_path}: {e}")
    
    # 生成sample_list.md
    with open(sample_list_path, 'w', encoding='utf-8') as f:
        f.write("# 样本PDF列表\n\n")
        f.write("本列表包含从各类银行中随机抽取的ESG报告样本。\n\n")
        
        # 按类别分组输出
        current_category = None
        for item in copied_files:
            if item['category'] != current_category:
                current_category = item['category']
                f.write(f"\n## {current_category}\n\n")
                f.write("| 股票代码 | 报告标题 | 文件大小 | SHA256 | 路径 |\n")
                f.write("|---------|---------|---------|--------|------|\n")
            
            # 简化标题
            title = item['bank_name']
            if '<' in title:  # 移除HTML标签
                title = re.sub(r'<[^>]+>', '', title)
            
            size_str = f"{item['file_size'] / 1024:.2f} KB" if item['file_size'] else "N/A"
            sha256_short = item['sha256'][:16] + '...' if item['sha256'] else "N/A"
            
            f.write(f"| {item['source_path'].split('/')[1]} | {title} | {size_str} | `{sha256_short}` | `{item['copied_path']}` |\n")
        
        f.write("\n## 统计信息\n\n")
        f.write(f"- 国有大行样本数: {len([x for x in copied_files if x['category'] == '国有大行'])}\n")
        f.write(f"- 股份行样本数: {len([x for x in copied_files if x['category'] == '股份行'])}\n")
        f.write(f"- 城商行样本数: {len([x for x in copied_files if x['category'] == '城商行'])}\n")
        f.write(f"- 总计: {len(copied_files)} 份\n")
    
    return copied_files


def main():
    """主函数"""
    # 设置随机种子以确保可复现
    random.seed(42)
    
    # 定义路径
    metadata_csv = PROJECT_ROOT / "data" / "metadata" / "metadata.csv"
    index_output = PROJECT_ROOT / "data" / "pdf_index.jsonl"
    sample_dir = PROJECT_ROOT / "data" / "sample_pdf"
    sample_list = PROJECT_ROOT / "outputs" / "reports" / "sample_list.md"
    
    # 确保输出目录存在
    (PROJECT_ROOT / "outputs" / "reports").mkdir(parents=True, exist_ok=True)
    
    # 检查输入文件是否存在
    if not metadata_csv.exists():
        print(f"Error: Metadata file not found: {metadata_csv}")
        return
    
    print(f"Reading metadata from: {metadata_csv}")
    print(f"Output index file: {index_output}")
    
    # 生成索引
    index_records = generate_pdf_index(metadata_csv, index_output)
    print(f"Generated index with {len(index_records)} records")
    
    # 统计信息
    existing_files = sum(1 for r in index_records if r['local_path'] is not None)
    print(f"Found {existing_files} existing PDF files out of {len(index_records)} records")
    
    # 抽取样本
    print(f"\nSelecting sample PDFs...")
    samples = select_sample_pdfs(index_records, sample_dir, sample_list, sample_size=1)
    print(f"Selected {len(samples)} sample PDFs")
    print(f"Sample list saved to: {sample_list}")
    
    # 按类别统计
    category_stats = {}
    for record in index_records:
        if record['local_path']:
            cat = categorize_bank(record['stock_code'])
            category_stats[cat] = category_stats.get(cat, 0) + 1
    
    print("\nPDF files by category:")
    for cat, count in sorted(category_stats.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
