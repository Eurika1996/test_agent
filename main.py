import os
import sys
import json
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.document_reader import DocumentReader, chunk_text
from src.reviewer import RequirementsReviewer
from src.report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description='需求文档评审 Agent - 自动分析需求文档并生成评审报告')
    parser.add_argument('document', help='需求文档路径（支持 .md/.txt/.docx/.pdf）')
    parser.add_argument('-o', '--output', help='输出报告路径（默认为 outputs 目录自动命名）')
    parser.add_argument('--chunk-size', type=int, default=4000, help='文档分块大小（字符数）')
    parser.add_argument('--dry-run', action='store_true', help='仅读取和分块文档，不调用 LLM')
    parser.add_argument('--save-issues', help='将原始问题保存为 JSON 文件的路径')

    args = parser.parse_args()

    doc_path = args.document
    if not os.path.exists(doc_path):
        print(f'错误: 文件不存在: {doc_path}')
        sys.exit(1)

    print('='*60)
    print('  需求文档评审 Agent')
    print('='*60)

    reader = DocumentReader()
    print(f'[1/4] 读取文档: {os.path.basename(doc_path)}')
    text = reader.read(doc_path)
    print(f'      文档总字数: {len(text)} 字符')

    print(f'[2/4] 文档分块 (chunk-size={args.chunk_size})')
    chunks = chunk_text(text, max_chunk_size=args.chunk_size)
    print(f'      共 {len(chunks)} 个分块')

    if args.dry_run:
        print(f'      调试模式（dry-run），不调用 LLM 分析')
        print(f'      第一个分块预览:')
        if chunks:
            print(chunks[0][:300] + '...')
        print('完成。')
        sys.exit(0)

    print(f'[3/4] 调用 LLM 进行需求评审...')
    try:
        reviewer = RequirementsReviewer()
        issues = reviewer.review_chunks(chunks)
    except Exception as e:
        print(f'      评审失败: {e}')
        print(f'      请检查 API Key 是否正确配置（.env 文件或环境变量）')
        sys.exit(1)

    print(f'      共发现 {len(issues)} 个问题')

    print(f'[4/4] 生成 Markdown 报告...')
    report = ReportGenerator()
    output_path = report.generate(issues, doc_path, args.output)
    print(f'      报告已保存到: {os.path.abspath(output_path)}')

    if args.save_issues:
        with open(args.save_issues, 'w', encoding='utf-8') as f:
            json.dump(issues, f, ensure_ascii=False, indent=2)
        print(f'      原始问题 JSON 已保存到: {args.save_issues}')

    print('='*60)
    print('  评审完成！')
    print(f'  请查看报告: {os.path.abspath(output_path)}')
    print('='*60)


if __name__ == '__main__':
    main()
