#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF下载脚本
从 metadata.csv 读取 pdf_url（详情页链接），提取真正的 PDF 下载链接并下载到 data/pdf/
支持限速、重试和失败记录
"""

import argparse
import csv
import json
import logging
import os
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 获取项目根目录（脚本所在目录的父目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setup_logging():
    """设置日志配置"""
    log_dir = os.path.join(PROJECT_ROOT, 'outputs', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(log_dir, 'download.log'), encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)


def create_session(retries=3, backoff_factor=1, cookies=None):
    """创建带重试机制的 requests session"""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # 设置请求头，模拟浏览器
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/pdf,application/x-pdf,application/octet-stream,text/html,application/json',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Referer': 'https://www.cninfo.com.cn/'
    })
    
    # 添加登录 Cookie
    if cookies:
        session.cookies.update(cookies)
    
    return session


def extract_pdf_url(session, detail_url, timeout=30):
    """
    从公告详情页面提取真正的 PDF 下载链接
    :param session: requests session 对象
    :param detail_url: 公告详情页 URL
    :param timeout: 请求超时时间
    :return: (pdf_url, error_message)
    """
    try:
        # 从详情页 URL 中提取参数
        # URL 格式: http://www.cninfo.com.cn/new/disclosure/detail?stockCode=xxx&announcementId=xxx&orgId=xxx&announcementTime=xxx
        params = {}
        if '?' in detail_url:
            query_string = detail_url.split('?')[1]
            for pair in query_string.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    params[key] = value
        
        if not params.get('announcementId'):
            return None, "无法从 URL 中提取 announcementId"
        
        # 调用巨潮资讯网的 API 获取公告详情（使用 HTTPS 和 POST 方法）
        api_url = 'https://www.cninfo.com.cn/new/announcement/bulletin_detail'
        api_params = {
            'announceId': params.get('announcementId', ''),
            'flag': 'false',  # plate == 'szse' ? true : false
            'announceTime': params.get('announcementTime', '')
        }
        
        response = session.post(api_url, data=api_params, timeout=timeout)
        response.raise_for_status()
        
        # 解析 JSON 响应
        data = response.json()
        
        if data and data.get('announcement'):
            adjunct_url = data['announcement'].get('adjunctUrl', '')
            if adjunct_url:
                # 构建完整的 PDF URL
                pdf_url = f"http://static.cninfo.com.cn/{adjunct_url}"
                return pdf_url, ""
            else:
                return None, "API 返回中没有找到 adjunctUrl"
        else:
            return None, "API 返回数据格式不正确"
        
    except requests.exceptions.RequestException as e:
        return None, f"请求 API 失败: {str(e)}"
    except json.JSONDecodeError as e:
        return None, f"解析 JSON 失败: {str(e)}"
    except Exception as e:
        return None, f"提取 PDF 链接失败: {str(e)}"


def download_pdf(session, pdf_url, save_path, timeout=30):
    """
    下载单个 PDF 文件
    :param session: requests session 对象
    :param pdf_url: PDF 文件的 URL
    :param save_path: 保存路径
    :param timeout: 请求超时时间
    :return: (success, error_message)
    """
    try:
        response = session.get(pdf_url, timeout=timeout, stream=True)
        response.raise_for_status()  # 检查 HTTP 错误
        
        # 检查内容类型
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' not in content_type.lower() and 'application/octet-stream' not in content_type.lower():
            return False, f"内容类型不是 PDF: {content_type}"
        
        # 写入文件
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 验证文件大小
        file_size = os.path.getsize(save_path)
        if file_size < 100:
            os.remove(save_path)
            return False, f"下载的文件太小({file_size}字节)，可能是错误页面"
        
        return True, ""
    
    except requests.exceptions.RequestException as e:
        return False, str(e)


def load_metadata(metadata_path):
    """加载 metadata.csv"""
    if not os.path.isabs(metadata_path):
        metadata_path = os.path.join(PROJECT_ROOT, metadata_path)
    
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"metadata 文件不存在: {metadata_path}")
    
    with open(metadata_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_failed_downloads(failed_records, output_path):
    """保存下载失败记录"""
    if not os.path.isabs(output_path):
        output_path = os.path.join(PROJECT_ROOT, output_path)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = ['stock_code', 'stock_name', 'announcement_title', 'publish_date', 'pdf_url', 'error_message']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(failed_records)


def parse_cookies(cookie_string):
    """解析 Cookie 字符串为字典"""
    cookies = {}
    if cookie_string:
        for part in cookie_string.split(';'):
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                cookies[key.strip()] = value.strip()
    return cookies


def main():
    parser = argparse.ArgumentParser(description='从 metadata.csv 下载 PDF 文件到 data/pdf/')
    parser.add_argument('--metadata', type=str, default='data/metadata/metadata.csv', help='metadata.csv 文件路径')
    parser.add_argument('--output-dir', type=str, default='data/pdf', help='PDF 保存目录')
    parser.add_argument('--failed-log', type=str, default='outputs/logs/failed_downloads.csv', help='失败记录文件')
    parser.add_argument('--sleep-seconds', type=float, default=2.0, help='请求间隔秒数')
    parser.add_argument('--retries', type=int, default=3, help='重试次数')
    parser.add_argument('--timeout', type=int, default=30, help='请求超时时间（秒）')
    parser.add_argument('--cookie', type=str, default='', help='巨潮资讯网登录 Cookie')
    args = parser.parse_args()
    
    # 解析 Cookie
    cookies = parse_cookies(args.cookie)
    if cookies:
        print(f"已加载 {len(cookies)} 个 Cookie")
    else:
        print("警告: 未提供 Cookie，可能无法下载 PDF")
    
    # 设置日志
    logger = setup_logging()
    
    # 创建保存目录
    pdf_dir = args.output_dir if os.path.isabs(args.output_dir) else os.path.join(PROJECT_ROOT, args.output_dir)
    os.makedirs(pdf_dir, exist_ok=True)
    
    # 加载 metadata
    logger.info(f"加载 metadata 文件: {args.metadata}")
    try:
        records = load_metadata(args.metadata)
        logger.info(f"共找到 {len(records)} 条记录")
    except Exception as e:
        logger.error(f"加载 metadata 失败: {e}")
        return
    
    # 创建带重试的 session（传入 Cookie）
    session = create_session(retries=args.retries, cookies=cookies)
    
    # 统计变量
    total = len(records)
    downloaded = 0
    skipped = 0
    failed = 0
    failed_records = []
    
    # 下载 PDF
    logger.info("开始下载 PDF 文件...")
    for i, record in enumerate(records, 1):
        detail_url = record.get('pdf_url', '').strip()
        stock_code = record.get('stock_code', '').strip()
        stock_name = record.get('stock_name', '').strip()
        announcement_title = record.get('announcement_title', '').strip()
        publish_date = record.get('publish_date', '').strip()
        
        # 跳过空 URL
        if not detail_url:
            logger.warning(f"[{i}/{total}] 跳过空 URL - {stock_code} {stock_name}")
            failed_records.append({
                'stock_code': stock_code,
                'stock_name': stock_name,
                'announcement_title': announcement_title,
                'publish_date': publish_date,
                'pdf_url': detail_url,
                'error_message': '详情页 URL 为空'
            })
            failed += 1
            continue
        
        # 生成文件名（使用股票代码+日期+标题的哈希值）
        title_hash = str(abs(hash(announcement_title)))[:8]
        filename = f"{stock_code}_{publish_date}_{title_hash}.pdf"
        save_path = os.path.join(pdf_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(save_path):
            logger.info(f"[{i}/{total}] 跳过已存在 - {filename}")
            skipped += 1
            continue
        
        # 从详情页提取真正的 PDF 下载链接
        logger.info(f"[{i}/{total}] 提取 PDF 链接 - {stock_code} {stock_name}")
        pdf_url, error_msg = extract_pdf_url(session, detail_url, timeout=args.timeout)
        
        if not pdf_url:
            logger.error(f"[{i}/{total}] 提取 PDF 链接失败 - {stock_code} {stock_name}: {error_msg}")
            failed_records.append({
                'stock_code': stock_code,
                'stock_name': stock_name,
                'announcement_title': announcement_title,
                'publish_date': publish_date,
                'pdf_url': detail_url,
                'error_message': f'提取链接失败: {error_msg}'
            })
            failed += 1
            
            # 请求间隔
            if i < total:
                time.sleep(args.sleep_seconds)
            continue
        
        # 下载文件
        logger.info(f"[{i}/{total}] 下载中 - {pdf_url[:50]}...")
        success, error_msg = download_pdf(session, pdf_url, save_path, timeout=args.timeout)
        
        if success:
            file_size = os.path.getsize(save_path)
            logger.info(f"[{i}/{total}] 下载成功 - {filename} ({file_size} bytes)")
            downloaded += 1
        else:
            logger.error(f"[{i}/{total}] 下载失败 - {stock_code} {stock_name}: {error_msg}")
            failed += 1
            failed_records.append({
                'stock_code': stock_code,
                'stock_name': stock_name,
                'announcement_title': announcement_title,
                'publish_date': publish_date,
                'pdf_url': pdf_url,
                'error_message': f'下载失败: {error_msg}'
            })
        
        # 限速间隔
        if i < total:
            time.sleep(args.sleep_seconds)
    
    # 保存失败记录
    if failed_records:
        save_failed_downloads(failed_records, args.failed_log)
        logger.info(f"已保存 {len(failed_records)} 条失败记录到 {args.failed_log}")
    
    # 输出统计
    logger.info("=" * 50)
    logger.info(f"下载完成")
    logger.info(f"总数: {total}")
    logger.info(f"成功: {downloaded}")
    logger.info(f"跳过(已存在): {skipped}")
    logger.info(f"失败: {failed}")
    logger.info("=" * 50)


if __name__ == '__main__':
    main()