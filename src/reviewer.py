import json
import os
from src.llm_client import LLMClient


SYSTEM_PROMPT = """你是一位资深的软件需求分析师和技术评审专家，拥有10年以上大型项目的需求评审经验。你的任务是对需求文档进行专业、全面、深入的评审，识别出文档中存在的问题和风险。

请严格按照以下评审维度进行分析：

1. 【完整性 Incompleteness】
   - 是否缺少关键业务流程、功能模块或接口定义？
   - 是否缺少异常场景、边界条件的处理描述？
   - 是否缺少非功能性需求（性能、安全、可用性、可扩展性等）？
   - 是否缺少数据定义、数据格式或数据字典？
   - 是否缺少与其他系统的集成说明？

2. 【不明确性 Ambiguity】
   - 是否存在模糊不清的描述（如"快速"、"友好"、"高效"等主观词汇）？
   - 是否有一句话可以被多种方式理解的地方？
   - 是否缺少关键参数、阈值或量化指标？
   - 是否有术语未定义或前后使用不一致？

3. 【矛盾性 Contradiction】
   - 文档不同章节之间是否存在互相矛盾的描述？
   - 功能描述与约束条件是否冲突？
   - 数据流或业务流程是否存在逻辑矛盾？

4. 【不可实现性 Feasibility】
   - 是否存在技术上难以实现或不切实际的需求？
   - 是否有超出预算或时间限制的不合理要求？
   - 是否有与现有系统架构严重冲突的设计？
   - 是否存在明显的性能瓶颈或安全隐患？

5. 【可测试性 Testability】
   - 需求是否可以被量化和验证？
   - 是否有明确的验收标准？
   - 测试场景是否完整覆盖了正常和异常路径？

对于每一个发现的问题，请提供：
- 问题类型（从上述5类中选择）
- 问题严重级别（P0/P1/P2/P3，P0最严重）
- 原文引用（如果能定位到具体段落）
- 具体问题描述
- 改进建议

请以结构化的JSON格式输出，不要包含任何额外的解释性文本，只输出JSON。"""


USER_PROMPT_TEMPLATE = """请对以下需求文档进行评审：

--- 文档开始 ---
{document_text}
--- 文档结束 ---

请以JSON数组格式输出所有发现的问题，格式如下：
[
  {{
    "issue_type": "完整性",
    "severity": "P0",
    "location": "原文引用或章节位置",
    "description": "问题的具体描述...",
    "suggestion": "改进建议..."
  }},
  ...
]

如果文档没有明显问题，也请输出空数组 []。"""


class RequirementsReviewer:
    def __init__(self, config=None):
        self.llm = LLMClient(config)
        self.system_prompt = SYSTEM_PROMPT

    def review(self, document_text):
        prompt = USER_PROMPT_TEMPLATE.format(document_text=document_text)

        print("正在调用 LLM 进行需求评审...")
        response_text = self.llm.chat(self.system_prompt, prompt)

        issues = self._parse_response(response_text)
        return issues

    def review_chunks(self, chunks):
        all_issues = []
        seen = set()

        for i, chunk in enumerate(chunks):
            print(f"正在评审第 {i+1}/{len(chunks)} 个文档分块...")
            issues = self.review(chunk)
            for issue in issues:
                key = (issue.get('issue_type', ''), issue.get('description', '')[:100])
                if key not in seen:
                    seen.add(key)
                    all_issues.append(issue)

        return all_issues

    def _parse_response(self, response_text):
        text = response_text.strip()

        if not text:
            return []

        start = text.find('[')
        end = text.rfind(']')

        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            try:
                data = json.loads(json_str)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass

        cleaned = self._clean_and_retry(text)
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        return self._fallback_parse(text)

    def _clean_and_retry(self, text):
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('```'):
                continue
            if line.startswith('json'):
                continue
            lines.append(line)
        return '\n'.join(lines).strip()

    def _fallback_parse(self, text):
        issues = []
        blocks = text.split('\n\n')
        for block in blocks:
            if len(block.strip()) < 20:
                continue
            if any(k in block for k in ['问题', '风险', '建议', 'P0', 'P1', 'P2', 'P3']):
                issues.append({
                    'issue_type': '未分类',
                    'severity': 'P2',
                    'location': '见描述',
                    'description': block,
                    'suggestion': '请参考原文上下文进行改进'
                })
        return issues
