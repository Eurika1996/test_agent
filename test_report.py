import sys
from src.report_generator import ReportGenerator

test_issues = [
    {
        'issue_type': '完整性',
        'severity': 'P0',
        'location': '"项目要在两个月内完成开发和上线"',
        'description': '文档未提供技术选型和架构设计，也没有指定团队规模和技术背景，无法评估两个月是否合理。',
        'suggestion': '补充技术栈选型、系统架构设计、以及详细的项目计划。'
    },
    {
        'issue_type': '不明确性',
        'severity': 'P1',
        'location': '"系统应该是友好的、高效的"',
        'description': '"友好"和"高效"是主观描述，没有量化指标，无法评估是否满足需求。',
        'suggestion': '明确量化指标，如：首屏加载时间 < 2s，系统平均响应时间 < 200ms。'
    },
    {
        'issue_type': '完整性',
        'severity': 'P2',
        'location': '"用户可以提交订单进行支付"',
        'description': '文档未说明支持哪些支付方式（支付宝、微信支付、银联等）。',
        'suggestion': '列出所有支持的支付渠道和每种支付的流程。'
    },
    {
        'issue_type': '可测试性',
        'severity': 'P3',
        'location': '整个文档',
        'description': '文档缺少验收标准和测试场景描述，测试团队无法制定测试计划。',
        'suggestion': '为每个功能模块补充明确的验收标准和核心测试用例。'
    }
]

print('测试 ReportGenerator...')
report = ReportGenerator()
output = report.generate(test_issues, 'examples/sample_requirements.md', 'outputs/test_report.md')
print('测试报告已生成: ' + output)

with open(output, 'r', encoding='utf-8') as f:
    content = f.read()
    print('报告字数: ' + str(len(content)))
    print('--- 预览 ---')
    print(content[:800] + '...')
print('测试通过！')
