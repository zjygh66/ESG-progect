#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试搜索公告脚本
"""

import os
import sys
import csv

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_search_script():
    """测试搜索脚本"""
    print("=" * 60)
    print("测试搜索公告脚本")
    print("=" * 60)
    
    # 1. 检查配置文件是否存在
    config_path = 'configs/crawl.yaml'
    if os.path.exists(config_path):
        print(f"✓ 配置文件存在: {config_path}")
    else:
        print(f"✗ 配置文件不存在: {config_path}")
        return False
    
    # 2. 检查脚本文件是否存在
    script_path = 'src/search_announcements.py'
    if os.path.exists(script_path):
        print(f"✓ 脚本文件存在: {script_path}")
    else:
        print(f"✗ 脚本文件不存在: {script_path}")
        return False
    
    # 3. 检查输出目录是否存在
    output_dir = 'data/metadata'
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ 输出目录已准备: {output_dir}")
    
    # 4. 检查csv写入功能
    test_csv_path = os.path.join(output_dir, 'test_metadata.csv')
    try:
        with open(test_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = ['stock_code', 'stock_name', 'announcement_title', 'publish_date', 'pdf_url', 'source', 'error_message']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                'stock_code': '000001',
                'stock_name': '平安银行',
                'announcement_title': '2022年度ESG报告',
                'publish_date': '2022-04-20',
                'pdf_url': 'http://www.cninfo.com.cn/...',
                'source': 'cninfo',
                'error_message': ''
            })
        print(f"✓ CSV写入测试通过")
        os.remove(test_csv_path)
    except Exception as e:
        print(f"✗ CSV写入测试失败: {e}")
        return False
    
    print("=" * 60)
    print("所有测试通过！")
    print("=" * 60)
    return True


def show_usage():
    """显示使用说明"""
    print("\n运行命令:")
    print("=" * 60)
    print("python src/search_announcements.py --config configs/crawl.yaml")
    print("=" * 60)
    print("\n说明:")
    print("1. 脚本会读取 configs/crawl.yaml 中的配置")
    print("2. 搜索巨潮资讯网的公告")
    print("3. 结果保存到 data/metadata/metadata.csv")
    print("4. 每次请求间隔 sleep_seconds 秒（默认1.5秒）")
    print("5. 如果请求失败，会在 error_message 字段记录错误信息")


if __name__ == '__main__':
    test_search_script()
    show_usage()