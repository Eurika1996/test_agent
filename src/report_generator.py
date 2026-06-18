import os
from datetime import datetime


SEVERITY_ORDER = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, '未分类': 4}

SEVERITY_EMOJI = {
    'P0': '🔴',
    'P1': '🟠',
    'P2': '🟡',
    'P3': '🟢',
    '未分类': '⚪'
}


def _severity_key(issue):
    sev = issue.get('severity', 'P3')
    return SEVERITY_ORDER.get(sev, 99)


def _sanitize(text):
    if text is None:
        return ''
    return str(text).strip()


class ReportGenerator:
    def __init__(self):
        pass

    def generate(self, issues, document_path, output_path=None):
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join('outputs', 'review_report_' + timestamp + '.md')

        parent_dir = os.path.dirname(os.path.abspath(output_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        sorted_issues = sorted(issues, key=_severity_key)

        by_type = {}
        by_severity = {'P0': [], 'P1': [], 'P2': [], 'P3': [], '未分类': []}
        for issue in sorted_issues:
            issue_type = _sanitize(issue.get('issue_type', '未分类'))
            severity = _sanitize(issue.get('severity', 'P3'))
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
            if severity in by_severity:
                by_severity[severity].append(issue)
            else:
                by_severity['未分类'].append(issue)

        lines = []

        lines.append('# 需求文档评审报告')
        lines.append('')
        lines.append('**评审时间**: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        lines.append('**文档来源**: `' + os.path.basename(document_path) + '`')
        lines.append('**问题总数**: **' + str(len(sorted_issues)) + ' 个**')
        lines.append('**严重分布**: P0=' + str(len(by_severity['P0'])) + ', P1=' + str(len(by_severity['P1'])) + ', P2=' + str(len(by_severity['P2'])) + ', P3=' + str(len(by_severity['P3'])))
        lines.append('')

        lines.append('## 严重级别说明')
        lines.append('')
        lines.append('| 级别 | 描述 |')
        lines.append('|------|------|')
        lines.append('| 🔴 P0 | 致命问题 - 会导致项目无法进行或产生严重后果，必须立即处理 |')
        lines.append('| 🟠 P1 | 严重问题 - 严重影响功能实现或系统稳定性，需优先处理 |')
        lines.append('| 🟡 P2 | 一般问题 - 影响部分功能或用户体验，需正常安排处理 |')
        lines.append('| 🟢 P3 | 轻微问题 - 不影响核心功能，可作为改进项 |')
        lines.append('')

        lines.append('## 问题概览（按严重级别）')
        lines.append('')
        lines.append('### 🔴 P0 级问题')
        lines.append('')
        if by_severity['P0']:
            for i, issue in enumerate(by_severity['P0'], 1):
                lines.extend(self._format_issue(i, issue))
        else:
            lines.append('暂无 P0 级问题')
        lines.append('')

        lines.append('### 🟠 P1 级问题')
        lines.append('')
        if by_severity['P1']:
            for i, issue in enumerate(by_severity['P1'], 1):
                lines.extend(self._format_issue(i, issue))
        else:
            lines.append('暂无 P1 级问题')
        lines.append('')

        lines.append('### 🟡 P2 级问题')
        lines.append('')
        if by_severity['P2']:
            for i, issue in enumerate(by_severity['P2'], 1):
                lines.extend(self._format_issue(i, issue))
        else:
            lines.append('暂无 P2 级问题')
        lines.append('')

        lines.append('### 🟢 P3 级问题')
        lines.append('')
        if by_severity['P3']:
            for i, issue in enumerate(by_severity['P3'], 1):
                lines.extend(self._format_issue(i, issue))
        else:
            lines.append('暂无 P3 级问题')
        lines.append('')

        lines.append('## 问题分类（按类型）')
        lines.append('')
        for issue_type, issues_of_type in by_type.items():
            lines.append('### ' + issue_type + '（' + str(len(issues_of_type)) + ' 个）')
            lines.append('')
            lines.append('| # | 严重级别 | 问题描述 | 改进建议 |')
            lines.append('|---|---------|---------|---------|')
            for i, issue in enumerate(issues_of_type, 1):
                emoji = SEVERITY_EMOJI.get(issue.get('severity', 'P3'), '')
                desc = _sanitize(issue.get('description', '')).replace('\n', ' ')
                if len(desc) > 100:
                    desc = desc[:97] + '...'
                sugg = _sanitize(issue.get('suggestion', '')).replace('\n', ' ')
                if len(sugg) > 100:
                    sugg = sugg[:97] + '...'
                lines.append('| ' + str(i) + ' | ' + emoji + ' ' + issue.get('severity', 'P3') + ' | ' + desc + ' | ' + sugg + ' |')
            lines.append('')

        lines.append('## 详细问题清单')
        lines.append('')
        lines.append('共 **' + str(len(sorted_issues)) + '** 个问题的完整清单（按严重级别排序）')
        lines.append('')
        for idx, issue in enumerate(sorted_issues, 1):
            severity = issue.get('severity', 'P3')
            emoji = SEVERITY_EMOJI.get(severity, '')
            lines.append('### ' + str(idx) + '. ' + emoji + ' [' + severity + '] ' + _sanitize(issue.get('issue_type', '未分类')))
            lines.append('')
            if issue.get('location'):
                lines.append('**原文引用**:')
                lines.append('')
                lines.append('> ' + _sanitize(issue.get('location', '')))
                lines.append('')
            lines.append('**问题描述**:')
            lines.append('')
            lines.append(_sanitize(issue.get('description', '')))
            lines.append('')
            lines.append('**改进建议**:')
            lines.append('')
            lines.append(_sanitize(issue.get('suggestion', '')))
            lines.append('')

        lines.append('---')
        lines.append('')
        lines.append('*本报告由 需求文档评审 Agent 自动生成*')
        lines.append('')

        content = '\n'.join(lines)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def _format_issue(self, index, issue):
        lines = []
        severity = issue.get('severity', 'P3')
        emoji = SEVERITY_EMOJI.get(severity, '')
        lines.append('**问题 ' + str(index) + '**: ' + emoji + ' [' + severity + '] ' + _sanitize(issue.get('issue_type', '未分类')) + '**')
        lines.append('')
        if issue.get('location'):
            lines.append('- **原文引用**: ' + _sanitize(issue.get('location', '')))
        lines.append('- **问题描述**: ' + _sanitize(issue.get('description', '')))
        lines.append('- **改进建议**: ' + _sanitize(issue.get('suggestion', '')))
        lines.append('')
        return lines
