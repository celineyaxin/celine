"""
学位论文格式验证工具 - Web UI
基于Flask的现代化Web界面
"""

import os
import sys
import tempfile
import uuid
import webbrowser
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename

# 判断是否为打包后的exe运行
if getattr(sys, 'frozen', False):
    # 打包后的路径
    BASE_DIR = sys._MEIPASS
    VALIDATORS_DIR = os.path.join(BASE_DIR, 'validators')
else:
    # 开发环境路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    VALIDATORS_DIR = os.path.join(BASE_DIR, 'validators')

# 添加validators目录到路径
sys.path.insert(0, VALIDATORS_DIR)

from run_all import VALIDATORS

# 配置Flask模板和静态文件路径
template_folder = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=template_folder)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_validation(doc_path: str, thesis_type: str = '博士'):
    """
    运行所有验证器
    
    Args:
        doc_path: Word文档路径
        thesis_type: 论文类型
    
    Returns:
        dict: 验证结果
    """
    reports = []
    total_errors = 0
    total_warnings = 0
    passed_count = 0
    failed_count = 0
    
    for validator_class in VALIDATORS:
        try:
            validator = validator_class(doc_path, thesis_type)
            validator.validate()
            report = validator.get_report()
            reports.append(report)
            
            total_errors += report['error_count']
            total_warnings += report['warning_count']
            
            if report['passed']:
                passed_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            reports.append({
                'validator': getattr(validator_class, 'name', '未知验证器'),
                'description': getattr(validator_class, 'description', ''),
                'standard_ref': getattr(validator_class, 'standard_ref', ''),
                'passed': False,
                'errors': [f'验证器执行错误: {str(e)}'],
                'warnings': [],
                'info': [],
                'error_count': 1,
                'warning_count': 0,
                'exception': str(e)
            })
            failed_count += 1
            total_errors += 1
    
    return {
        'doc_name': os.path.basename(doc_path),
        'thesis_type': thesis_type,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_validators': len(VALIDATORS),
        'passed_count': passed_count,
        'failed_count': failed_count,
        'total_errors': total_errors,
        'total_warnings': total_warnings,
        'reports': reports,
        'passed': total_errors == 0,
    }


def generate_html_report(result: dict) -> str:
    """生成HTML报告"""
    doc_name = result['doc_name']
    thesis_type = result['thesis_type']
    timestamp = result['timestamp']
    reports = result['reports']
    total_errors = result['total_errors']
    total_warnings = result['total_warnings']
    passed_count = result['passed_count']
    
    # 确定总体状态
    if total_errors == 0 and total_warnings == 0:
        overall_status = '✅ 全部通过'
        status_class = 'passed'
    elif total_errors == 0:
        overall_status = f'⚠️ 基本通过（{total_warnings}条警告）'
        status_class = 'warning'
    else:
        overall_status = f'❌ 未通过（{total_errors}条错误）'
        status_class = 'failed'
    
    # 生成验证器结果HTML
    validators_html = ''
    for report in reports:
        validator_name = report.get('validator', '未知')
        standard_ref = report.get('standard_ref', '')
        
        if 'exception' in report:
            validators_html += f'''
            <div class="validator failed">
                <h3>❌ {validator_name}</h3>
                <p class="error">执行错误: {report['exception']}</p>
            </div>
            '''
        else:
            errors = report.get('errors', [])
            warnings = report.get('warnings', [])
            info = report.get('info', [])
            passed = report.get('passed', False)
            
            status_icon = '✅' if passed and not warnings else ('⚠️' if passed else '❌')
            status = 'passed' if passed and not warnings else ('warning' if passed else 'failed')
            
            items_html = ''
            
            if info:
                for item in info:
                    items_html += f'<div class="info">ℹ️ {item}</div>'
            
            if warnings:
                for item in warnings[:10]:
                    items_html += f'<div class="warning-item">⚠️ {item}</div>'
                if len(warnings) > 10:
                    items_html += f'<div class="more">...还有 {len(warnings)-10} 条警告</div>'
            
            if errors:
                for item in errors[:10]:
                    items_html += f'<div class="error-item">❌ {item}</div>'
                if len(errors) > 10:
                    items_html += f'<div class="more">...还有 {len(errors)-10} 条错误</div>'
            
            validators_html += f'''
            <div class="validator {status}">
                <h3>{status_icon} {validator_name} <span class="ref">({standard_ref})</span></h3>
                <div class="items">{items_html}</div>
            </div>
            '''
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>论文格式验证报告 - {doc_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #1a1a2e;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
            color: #fff;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .doc-name {{ font-size: 16px; opacity: 0.9; }}
        .header .timestamp {{ font-size: 14px; opacity: 0.7; margin-top: 5px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            padding: 25px;
            background: #16213e;
        }}
        .stat {{
            text-align: center;
            padding: 20px;
            background: #1a1a2e;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat .number {{ font-size: 36px; font-weight: bold; margin-bottom: 5px; }}
        .stat .label {{ font-size: 14px; color: #888; }}
        .stat.passed .number {{ color: #00d9a5; }}
        .stat.failed .number {{ color: #e94560; }}
        .stat.warning .number {{ color: #ffc857; }}
        .stat.total .number {{ color: #6c63ff; }}
        .overall {{
            padding: 20px 30px;
            font-size: 20px;
            font-weight: bold;
            text-align: center;
        }}
        .overall.passed {{ background: rgba(0,217,165,0.2); color: #00d9a5; }}
        .overall.warning {{ background: rgba(255,200,87,0.2); color: #ffc857; }}
        .overall.failed {{ background: rgba(233,69,96,0.2); color: #e94560; }}
        .validators {{ padding: 20px 30px 30px; }}
        .validators h2 {{ font-size: 20px; margin-bottom: 20px; color: #fff; }}
        .validator {{
            margin-bottom: 15px;
            padding: 15px 20px;
            border-radius: 10px;
            border-left: 4px solid;
            background: rgba(255,255,255,0.05);
        }}
        .validator.passed {{ border-color: #00d9a5; }}
        .validator.warning {{ border-color: #ffc857; }}
        .validator.failed {{ border-color: #e94560; }}
        .validator h3 {{ font-size: 16px; margin-bottom: 10px; color: #fff; }}
        .validator .ref {{ font-weight: normal; font-size: 14px; color: #888; }}
        .validator .items {{ font-size: 14px; }}
        .validator .info {{ color: #6c63ff; margin: 5px 0; }}
        .validator .warning-item {{ color: #ffc857; margin: 5px 0; }}
        .validator .error-item {{ color: #e94560; margin: 5px 0; }}
        .validator .more {{ color: #666; font-style: italic; margin-top: 5px; }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #16213e;
            font-size: 14px;
            color: #666;
        }}
        @media (max-width: 600px) {{ .summary {{ grid-template-columns: repeat(2, 1fr); }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 论文格式验证报告</h1>
            <div class="doc-name">{doc_name}</div>
            <div class="timestamp">论文类型: {thesis_type} | 生成时间: {timestamp}</div>
        </div>
        <div class="summary">
            <div class="stat total"><div class="number">{len(reports)}</div><div class="label">验证项目</div></div>
            <div class="stat passed"><div class="number">{passed_count}</div><div class="label">通过</div></div>
            <div class="stat warning"><div class="number">{total_warnings}</div><div class="label">警告</div></div>
            <div class="stat failed"><div class="number">{total_errors}</div><div class="label">错误</div></div>
        </div>
        <div class="overall {status_class}">{overall_status}</div>
        <div class="validators">
            <h2>详细验证结果</h2>
            {validators_html}
        </div>
        <div class="footer">基于《中国金融学院金融类专业学位论文写作规范》</div>
    </div>
</body>
</html>'''
    
    return html


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/validate', methods=['POST'])
def validate():
    """验证上传的文档"""
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '只支持 .docx 格式的文件'}), 400
    
    thesis_type = request.form.get('thesis_type', '博士')
    
    # 保存上传的文件
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        file.save(filepath)
        
        # 运行验证
        result = run_validation(filepath, thesis_type)
        
        # 存储结果用于下载报告
        session['last_result'] = result
        session['last_filepath'] = filepath
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'验证过程出错: {str(e)}'}), 500
    
    finally:
        # 清理临时文件
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass


@app.route('/download-report', methods=['POST'])
def download_report():
    """下载HTML报告"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无验证结果数据'}), 400
    
    try:
        html_content = generate_html_report(data)
        
        # 创建临时文件
        report_filename = f"{data.get('doc_name', 'report').rsplit('.', 1)[0]}_验证报告.html"
        report_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{report_filename}")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return send_file(
            report_path,
            as_attachment=True,
            download_name=report_filename,
            mimetype='text/html'
        )
        
    except Exception as e:
        return jsonify({'error': f'生成报告失败: {str(e)}'}), 500


def open_browser():
    """延迟打开浏览器"""
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    # 确保templates目录存在（开发环境）
    if not getattr(sys, 'frozen', False):
        templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
    
    print("=" * 60)
    print("学位论文格式验证工具 - Web UI")
    print("=" * 60)
    print("正在启动，浏览器将自动打开...")
    print("如果浏览器未自动打开，请访问: http://127.0.0.1:5000")
    print("关闭此窗口可停止程序")
    print("=" * 60)
    
    # 启动后自动打开浏览器
    threading.Timer(1.5, open_browser).start()
    
    # 生产模式运行（关闭debug避免重复打开浏览器）
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)

