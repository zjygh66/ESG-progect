#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融文本智能课程项目 - 主运行脚本
"""

import argparse
import sys


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='金融文本智能课程项目 - 基于巨潮资讯网PDF数据的文本分析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run.py --help              显示帮助信息
  python run.py --version           显示版本信息

项目功能:
  1. PDF文档解析与文本提取
  2. 金融文本智能分析
  3. 信息抽取与结构化
  4. 结果评估与报告生成
        """
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='%(prog)s 1.0.0'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='configs/task.yaml',
        help='配置文件路径 (默认: configs/task.yaml)'
    )
    
    parser.add_argument(
        '--task',
        type=str,
        choices=['parse', 'analyze', 'evaluate', 'all'],
        default='all',
        help='执行的任务类型: parse(解析), analyze(分析), evaluate(评估), all(全部)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs',
        help='输出目录 (默认: outputs)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细输出信息'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("金融文本智能课程项目")
    print("=" * 60)
    print(f"配置文件: {args.config}")
    print(f"任务类型: {args.task}")
    print(f"输出目录: {args.output_dir}")
    print(f"详细模式: {'开启' if args.verbose else '关闭'}")
    print("=" * 60)
    print("\n提示: 这是一个项目骨架，业务逻辑待实现。")
    print("请参考 README.md 了解项目结构和开发指南。")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())