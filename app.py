import os
import json
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS

from src.document_reader import DocumentReader, chunk_text
from src.reviewer import RequirementsReviewer
from src.report_generator import ReportGenerator

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = 'uploads'
OUTPUT_DIR = 'outputs'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

tasks = {}

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>需求文档评审 Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            padding: 40px 20px;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 12px;
            padding: 60px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #fafafa;
        }
        .upload-area:hover, .upload-area.dragover {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .upload-area .icon { font-size: 48px; margin-bottom: 15px; }
        .upload-area .hint { color: #888; font-size: 14px; margin-top: 10px; }
        .file-info {
            margin-top: 20px;
            padding: 15px;
            background: #f5f7fa;
            border-radius: 8px;
            display: none;
        }
        .file-info.show { display: block; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 40px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 20px;
            font-weight: bold;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .status {
            padding: 20px;
            border-radius: 12px;
            display: none;
        }
        .status.show { display: block; }
        .status.running { background: #fff8e1; }
        .status.success { background: #e8f5e9; }
        .status.error { background: #ffebee; }
        .status-title { font-weight: bold; margin-bottom: 10px; font-size: 18px; }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.5s;
        }
        .log {
            background: #263238;
            color: #aed581;
            padding: 15px;
            border-radius: 8px;
            font-family: "Courier New", monospace;
            font-size: 13px;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 15px;
        }
        .log-line { margin: 3px 0; }
        .report {
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .report h1 { color: #333; border-bottom: 3px solid #667eea; padding-bottom: 15px; margin-bottom: 25px; }
        .report h2 { color: #555; margin-top: 30px; margin-bottom: 15px; padding-left: 10px; border-left: 4px solid #667eea; }
        .report h3 { color: #666; margin-top: 25px; margin-bottom: 12px; }
        .report p { line-height: 1.8; margin: 10px 0; color: #444; }
        .report table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px; }
        .report th { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 12px; text-align: left; }
        .report td { padding: 12px; border-bottom: 1px solid #eee; }
        .report tr:hover { background: #f5f7fa; }
        .report blockquote { border-left: 4px solid #667eea; padding: 10px 20px; margin: 15px 0; background: #f5f7fa; color: #555; border-radius: 4px; }
        .report code { background: #f5f7fa; padding: 2px 8px; border-radius: 4px; font-family: "Courier New", monospace; font-size: 14px; }
        .stats-box { display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap; }
        .stat-item { flex: 1; min-width: 150px; padding: 20px; border-radius: 12px; text-align: center; }
        .stat-item .num { font-size: 2em; font-weight: bold; }
        .stat-item .label { font-size: 0.9em; color: #666; margin-top: 5px; }
        .p0 { background: #ffebee; color: #c62828; }
        .p1 { background: #fff3e0; color: #ef6c00; }
        .p2 { background: #fffde7; color: #f9a825; }
        .p3 { background: #e8f5e9; color: #2e7d32; }
        .download-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: #4caf50;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        }
        .download-btn:hover { background: #43a047; }
        input[type=file] { display: none; }
        .examples {
            margin-top: 15px;
            padding: 15px;
            background: #e8f5e9;
            border-radius: 8px;
        }
        .examples a { color: #2e7d32; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 需求文档评审 Agent</h1>
            <p>智能分析需求文档，自动识别完整性、不明确性、矛盾性、不可实现性等问题</p>
        </div>

        <div class="card" id="uploadCard">
            <div class="upload-area" id="uploadArea">
                <div class="icon">📄</div>
                <h2>点击上传或拖拽需求文档到这里</h2>
                <p class="hint">支持 .md / .txt / .docx / .pdf 格式</p>
                <input type="file" id="fileInput" accept=".md,.txt,.docx,.pdf">
            </div>
            <div class="file-info" id="fileInfo">
                <strong>已选择：</strong><span id="fileName"></span>
                <span style="color:#888; margin-left:10px;" id="fileSize"></span>
            </div>
            <div style="text-align:center;">
                <button class="btn" id="reviewBtn" disabled>🚀 开始评审</button>
            </div>
            <div class="examples">
                <strong>💡 没有文档？</strong> <a href="/examples/sample_requirements.md">使用示例需求文档</a> 试试，或者 <a href="/examples/sample_requirements.md" download>下载示例</a>
            </div>
        </div>

        <div class="status" id="status">
            <div class="status-title" id="statusTitle">评审中...</div>
            <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
            <div id="statusMsg">正在准备...</div>
            <div class="log" id="log"></div>
        </div>

        <div class="report" id="report" style="display:none;"></div>
    </div>

<script>
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const reviewBtn = document.getElementById('reviewBtn');
    const status = document.getElementById('status');
    const statusTitle = document.getElementById('statusTitle');
    const statusMsg = document.getElementById('statusMsg');
    const log = document.getElementById('log');
    const progressFill = document.getElementById('progressFill');
    const report = document.getElementById('report');

    let currentFile = null;

    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.classList.add('dragover'); });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', e => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', e => { if (e.target.files.length) handleFile(e.target.files[0]); });

    function handleFile(file) {
        currentFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = '(' + (file.size / 1024).toFixed(1) + ' KB)';
        fileInfo.classList.add('show');
        reviewBtn.disabled = false;
    }

    reviewBtn.addEventListener('click', () => {
        if (!currentFile) return;
        startReview();
    });

    function addLog(msg) {
        const line = document.createElement('div');
        line.className = 'log-line';
        line.textContent = '> ' + msg;
        log.appendChild(line);
        log.scrollTop = log.scrollHeight;
    }

    function setProgress(p) { progressFill.style.width = p + '%'; }

    async function startReview() {
        const formData = new FormData();
        formData.append('file', currentFile);

        status.className = 'status show running';
        statusTitle.textContent = '🔄 正在评审...';
        statusMsg.textContent = '文档上传中...';
        log.innerHTML = '';
        report.style.display = 'none';
        reviewBtn.disabled = true;
        setProgress(10);

        try {
            const res = await fetch('/api/review', { method: 'POST', body: formData });
            const data = await res.json();

            if (!data.success) {
                throw new Error(data.message || '评审失败');
            }

            const taskId = data.task_id;
            addLog('任务已创建：' + taskId);
            setProgress(20);

            await pollTask(taskId);
        } catch (err) {
            status.className = 'status show error';
            statusTitle.textContent = '❌ 出错了';
            statusMsg.textContent = err.message;
            reviewBtn.disabled = false;
        }
    }

    async function pollTask(taskId) {
        const poll = async () => {
            const res = await fetch('/api/task/' + taskId);
            const data = await res.json();

            if (data.status === 'running') {
                setProgress(data.progress || 30);
                statusMsg.textContent = data.message || '评审中...';
                if (data.logs) data.logs.forEach(l => addLog(l));
                setTimeout(poll, 2000);
            } else if (data.status === 'done') {
                setProgress(100);
                status.className = 'status show success';
                statusTitle.textContent = '✅ 评审完成！';
                statusMsg.textContent = '共发现 ' + data.issue_count + ' 个问题';
                report.style.display = 'block';
                report.innerHTML = data.report_html;
                reviewBtn.disabled = false;
                window.scrollTo({ top: report.offsetTop - 20, behavior: 'smooth' });
            } else if (data.status === 'error') {
                setProgress(100);
                status.className = 'status show error';
                statusTitle.textContent = '❌ 评审失败';
                statusMsg.textContent = data.message;
                reviewBtn.disabled = false;
            }
        };
        setTimeout(poll, 1000);
    }
</script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/examples/<path:filename>')
def serve_example(filename):
    return send_from_directory('examples', filename)


import markdown as md_lib
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension


def markdown_to_html(md_content):
    html = md_lib.markdown(md_content, extensions=['tables', 'fenced_code'])
    return html


@app.route('/api/review', methods=['POST'])
def api_review():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '未上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '文件名为空'}), 400

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = os.path.splitext(file.filename)[1].lower()
    safe_name = 'doc_' + timestamp + ext
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    file.save(save_path)

    task_id = 'task_' + timestamp
    tasks[task_id] = {
        'status': 'running',
        'progress': 5,
        'message': '任务创建成功',
        'logs': [],
        'file_path': save_path,
        'file_name': file.filename
    }

    thread = threading.Thread(target=run_review, args=(task_id,))
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'task_id': task_id})


def run_review(task_id):
    task = tasks[task_id]
    file_path = task['file_path']

    try:
        task['logs'].append('读取文档：' + task['file_name'])
        task['progress'] = 15
        task['message'] = '读取文档...'

        reader = DocumentReader()
        text = reader.read(file_path)
        char_count = len(text)
        task['logs'].append('文档字数：' + str(char_count) + ' 字符')
        task['progress'] = 25

        task['message'] = '分块处理...'
        chunks = chunk_text(text, max_chunk_size=4000)
        task['logs'].append('共 ' + str(len(chunks)) + ' 个分块')
        task['progress'] = 35

        task['message'] = '调用 LLM 评审中（可能需要10-30秒）...'
        reviewer = RequirementsReviewer()
        issues = reviewer.review_chunks(chunks)
        task['logs'].append('发现 ' + str(len(issues)) + ' 个问题')
        task['progress'] = 75

        task['message'] = '生成报告...'
        report_gen = ReportGenerator()
        report_path = report_gen.generate(issues, task['file_name'])
        task['progress'] = 90

        with open(report_path, 'r', encoding='utf-8') as f:
            report_md = f.read()

        report_html = markdown_to_html(report_md)

        task['status'] = 'done'
        task['progress'] = 100
        task['message'] = '完成'
        task['issue_count'] = len(issues)
        task['report_html'] = report_html
        task['report_path'] = report_path
        task['logs'].append('报告已保存：' + report_path)

    except Exception as e:
        task['status'] = 'error'
        task['message'] = str(e)
        task['logs'].append('错误：' + str(e))


@app.route('/api/task/<task_id>')
def api_task(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    return jsonify(task)


if __name__ == '__main__':
    print('=' * 60)
    print('  需求文档评审 Agent - Web 界面')
    print('=' * 60)
    print('  请在浏览器中打开: http://127.0.0.1:5000')
    print('=' * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
