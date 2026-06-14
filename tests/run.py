#!/usr/bin/env python3
"""
金融文本智能分析项目 - 主入口
"""

import argparse
import sys


COMMANDS = {
    "download": "从巨潮资讯网下载 PDF 文档",
    "extract": "从 PDF 中提取文本",
    "analyze": "使用 LLM 分析文本（待实现）",
    "report": "生成分析报告",
}


def cmd_download(args):
    """下载 PDF 文档"""
    print("下载功能待实现")
    pass


def cmd_extract(args):
    """提取 PDF 文本"""
    print("提取功能待实现")
    pass


def cmd_analyze(args):
    """LLM 分析"""
    print("分析功能待实现")
    pass


def cmd_report(args):
    """生成报告"""
    print("报告功能待实现")
    pass


def main():
    parser = argparse.ArgumentParser(
        description="金融文本智能分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
可用命令:
  download    从巨潮资讯网下载 PDF 文档
  extract     从 PDF 中提取文本
  analyze     使用 LLM 分析文本
  report      生成分析报告

示例:
  python run.py download --stock 000001
  python run.py extract --input data/pdfs/
  python run.py analyze --texts outputs/texts/
        """
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # download 命令
    sp_download = subparsers.add_parser("download", help="下载 PDF 文档")
    sp_download.add_argument("--stock", type=str, help="股票代码")
    sp_download.add_argument("--date", type=str, help="日期范围 YYYY-MM-DD")

    # extract 命令
    sp_extract = subparsers.add_parser("extract", help="提取 PDF 文本")
    sp_extract.add_argument("--input", type=str, default="data/pdfs/", help="PDF 目录")
    sp_extract.add_argument("--output", type=str, default="outputs/texts/", help="输出目录")

    # analyze 命令
    sp_analyze = subparsers.add_parser("analyze", help="LLM 分析")
    sp_analyze.add_argument("--texts", type=str, default="outputs/texts/", help="文本目录")

    # report 命令
    sp_report = subparsers.add_parser("report", help="生成报告")
    sp_report.add_argument("--input", type=str, default="outputs/results/", help="分析结果目录")
    sp_report.add_argument("--output", type=str, default="outputs/reports/", help="报告输出目录")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # 命令分发
    dispatch = {
        "download": cmd_download,
        "extract": cmd_extract,
        "analyze": cmd_analyze,
        "report": cmd_report,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
