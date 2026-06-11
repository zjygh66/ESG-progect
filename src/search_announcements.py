#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
巨潮资讯网公告搜索脚本
使用 AKShare 获取公告列表并生成 metadata.csv，不下载 PDF
支持行业筛选（如银行业）
"""

import argparse
import csv
import logging
import os
import sys
import time

import akshare as ak
import yaml

# 获取项目根目录（脚本所在目录的父目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 银行业股票代码列表（A股主要银行）
BANK_STOCK_CODES = {
    # 大型国有银行
    '601398': '工商银行',
    '601939': '建设银行',
    '601988': '中国银行',
    '601288': '农业银行',
    '601328': '交通银行',
    
    # 股份制商业银行
    '600036': '招商银行',
    '600000': '浦发银行',
    '601998': '中信银行',
    '601818': '光大银行',
    '600016': '民生银行',
    '601166': '兴业银行',
    '000001': '平安银行',
    '600015': '华夏银行',
    
    # 城市商业银行
    '601169': '北京银行',
    '601009': '南京银行',
    '002142': '宁波银行',
    '600926': '杭州银行',
    '600919': '江苏银行',
    '601229': '上海银行',
    '601577': '长沙银行',
    '601997': '贵阳银行',
    '601838': '成都银行',
    '002936': '郑州银行',
    '002948': '青岛银行',
    '600928': '西安银行',
    '601860': '紫金银行',
    
    # 农村商业银行
    '002958': '青农商行',
    '603323': '苏农银行',
    '002839': '张家港行',
    '002807': '江阴银行',
}


def setup_logging():
    """设置日志配置"""
    log_dir = os.path.join(PROJECT_ROOT, 'outputs', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(log_dir, 'search.log'), encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)


def load_config(config_path):
    """加载配置文件"""
    if not os.path.isabs(config_path):
        config_path = os.path.join(PROJECT_ROOT, config_path)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_bank_stock_codes(logger):
    """获取银行业股票代码列表"""
    logger.info("使用预定义的银行业股票列表")
    return set(BANK_STOCK_CODES.keys())


def search_announcements_akshare(keywords, markets, date_range, max_records, sleep_seconds, logger, filter_bank=False):
    """
    使用 AKShare 获取公告列表
    :param keywords: 搜索关键词列表
    :param markets: 市场列表 (sz=深交所, sh=上交所)
    :param date_range: 日期范围 {"start": "2022-01-01", "end": "2023-12-31"}
    :param max_records: 最大记录数
    :param sleep_seconds: 请求间隔秒数
    :param logger: 日志对象
    :param filter_bank: 是否只筛选银行业股票
    :return: 公告列表
    """
    results = []
    
    # 获取银行股票代码列表
    bank_stocks = get_bank_stock_codes(logger) if filter_bank else None
    
    # 转换日期格式 (YYYY-MM-DD -> YYYYMMDD)
    start_date = date_range['start'].replace('-', '')
    end_date = date_range['end'].replace('-', '')
    
    # 市场转换
    market_map = {
        'sz': '沪深京',
        'sh': '沪深京',
        'bj': '沪深京'
    }
    
    total_records = 0
    
    for keyword in keywords:
        logger.info(f"搜索关键词: {keyword}")
        
        for market in markets:
            market_name = market_map.get(market, '沪深京')
            
            try:
                # 调用 AKShare 巨潮资讯公告接口
                logger.debug(f"调用 AKShare 接口: market={market_name}, keyword={keyword}, start_date={start_date}, end_date={end_date}")
                
                df = ak.stock_zh_a_disclosure_report_cninfo(
                    symbol='',  # 空字符串表示所有股票
                    market=market_name,
                    keyword=keyword,
                    category='',  # 空字符串表示所有类别
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df.empty:
                    logger.info(f"关键词 '{keyword}' 在 {market_name} 市场无数据")
                    continue
                
                logger.info(f"找到 {len(df)} 条记录")
                
                # 如果只筛选银行股，过滤数据
                if filter_bank:
                    df = df[df['代码'].isin(bank_stocks)]
                    logger.info(f"筛选银行股后剩余 {len(df)} 条记录")
                
                if df.empty:
                    logger.info(f"筛选银行股后无数据")
                    continue
                
                # 限制每次返回的数量
                if len(df) > (max_records - total_records):
                    df = df.head(max_records - total_records)
                
                # 转换为结果列表
                for _, row in df.iterrows():
                    result = {
                        'stock_code': str(row.get('代码', '')).strip(),
                        'stock_name': str(row.get('简称', '')).strip(),
                        'announcement_title': str(row.get('公告标题', '')).strip(),
                        'publish_date': str(row.get('公告时间', '')).strip()[:10],  # 只保留日期部分
                        'pdf_url': str(row.get('公告链接', '')).strip(),
                        'source': 'akshare_cninfo',
                        'error_message': ''
                    }
                    results.append(result)
                    total_records += 1
                    logger.debug(f"找到公告: {result['stock_code']} - {result['announcement_title'][:50]}...")
                
                if total_records >= max_records:
                    logger.info(f"已达到最大记录数 {max_records}")
                    return results
                
                # 请求间隔
                time.sleep(sleep_seconds)
                
            except Exception as e:
                logger.error(f"获取 {market_name} 市场数据失败: {str(e)}")
                results.append({
                    'stock_code': '',
                    'stock_name': '',
                    'announcement_title': '',
                    'publish_date': '',
                    'pdf_url': '',
                    'source': 'akshare_cninfo',
                    'error_message': f"获取数据失败: {str(e)}"
                })
                continue
    
    return results


def save_metadata(announcements, output_path, logger):
    """保存 metadata.csv"""
    if not os.path.isabs(output_path):
        output_path = os.path.join(PROJECT_ROOT, output_path)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = ['stock_code', 'stock_name', 'announcement_title', 'publish_date', 'pdf_url', 'source', 'error_message']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(announcements)
    
    logger.info(f"共保存 {len(announcements)} 条记录到 {output_path}")


def main():
    parser = argparse.ArgumentParser(description='使用 AKShare 获取巨潮资讯公告列表并生成 metadata.csv')
    parser.add_argument('--config', type=str, default='configs/crawl.yaml', help='配置文件路径')
    parser.add_argument('--bank-only', action='store_true', help='只抓取银行业股票的公告')
    args = parser.parse_args()
    
    # 设置日志
    os.makedirs('outputs/logs', exist_ok=True)
    logger = setup_logging()
    
    # 加载配置
    logger.info(f"加载配置文件: {args.config}")
    config = load_config(args.config)
    
    # 搜索公告
    logger.info(f"开始搜索公告，关键词: {config['keywords']}")
    if args.bank_only:
        logger.info("仅筛选银行业股票")
    
    announcements = search_announcements_akshare(
        keywords=config['keywords'],
        markets=config['markets'],
        date_range=config['date_range'],
        max_records=config['max_records'],
        sleep_seconds=config['sleep_seconds'],
        logger=logger,
        filter_bank=args.bank_only
    )
    
    # 保存结果
    output_path = config['output']['metadata']
    save_metadata(announcements, output_path, logger)
    
    logger.info("搜索完成")


if __name__ == '__main__':
    main()