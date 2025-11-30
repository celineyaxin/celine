"""
验证报告生成器
生成HTML格式的验证报告

用法：python report_generator.py thesis.docx --output report.html
"""

import sys
import os
import argparse
from datetime import datetime

# 配置控制台输出编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_all import VALIDATORS


def generate_html_report(doc_path: str, thesis_type: str = '博士', output_path: str = None):
    """
    生成HTML格式的验证报告
    
    Args:
        doc_path: Word文档路径
        thesis_type: 论文类型
        output_path: 输出HTML文件路径
    """
    
    if not os.path.exists(doc_path):
        print(f"错误: 文件不存在 - {doc_path}")
        return None
    
    # 运行所有验证器
    reports = []
    total_errors = 0
    total_warnings = 0
    
    for validator_class in VALIDATORS:
        try:
            validator = validator_class(doc_path, thesis_type)
            validator.validate()
            report = validator.get_report()
            reports.append(report)
            total_errors += report['error_count']
            total_warnings += report['warning_count']
        except Exception as e:
            reports.append({
                'validator': validator_class.name,
                'error': str(e),
                'passed': False,
            })
    
    # 生成HTML
    html = _generate_html(doc_path, thesis_type, reports, total_errors, total_warnings)
    
    # 确定输出路径
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        output_path = f"{base_name}_验证报告.html"
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"验证报告已生成: {output_path}")
    return output_path


def _generate_html(doc_path: str, thesis_type: str, reports: list, 
                   total_errors: int, total_warnings: int) -> str:
    """生成HTML内容"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    doc_name = os.path.basename(doc_path)
    
    # 计算统计数据
    passed_count = sum(1 for r in reports if r.get('passed', False))
    failed_count = len(reports) - passed_count
    
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
        
        if 'error' in report:
            # 验证器执行出错
            validators_html += f'''
            <div class="validator failed">
                <h3>❌ {validator_name}</h3>
                <p class="error">执行错误: {report['error']}</p>
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
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .doc-name {{
            font-size: 16px;
            opacity: 0.8;
        }}
        .header .timestamp {{
            font-size: 14px;
            opacity: 0.6;
            margin-top: 5px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat {{
            text-align: center;
            padding: 20px;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .stat .number {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat .label {{
            font-size: 14px;
            color: #666;
        }}
        .stat.passed .number {{ color: #10b981; }}
        .stat.failed .number {{ color: #ef4444; }}
        .stat.warning .number {{ color: #f59e0b; }}
        .stat.total .number {{ color: #6366f1; }}
        .overall {{
            padding: 20px 30px;
            font-size: 20px;
            font-weight: bold;
            text-align: center;
        }}
        .overall.passed {{ background: #d1fae5; color: #065f46; }}
        .overall.warning {{ background: #fef3c7; color: #92400e; }}
        .overall.failed {{ background: #fee2e2; color: #991b1b; }}
        .validators {{
            padding: 20px 30px 30px;
        }}
        .validators h2 {{
            font-size: 20px;
            margin-bottom: 20px;
            color: #1a1a2e;
        }}
        .validator {{
            margin-bottom: 15px;
            padding: 15px 20px;
            border-radius: 10px;
            border-left: 4px solid;
        }}
        .validator.passed {{
            background: #f0fdf4;
            border-color: #10b981;
        }}
        .validator.warning {{
            background: #fffbeb;
            border-color: #f59e0b;
        }}
        .validator.failed {{
            background: #fef2f2;
            border-color: #ef4444;
        }}
        .validator h3 {{
            font-size: 16px;
            margin-bottom: 10px;
        }}
        .validator .ref {{
            font-weight: normal;
            font-size: 14px;
            color: #666;
        }}
        .validator .items {{
            font-size: 14px;
        }}
        .validator .info {{
            color: #0369a1;
            margin: 5px 0;
        }}
        .validator .warning-item {{
            color: #b45309;
            margin: 5px 0;
        }}
        .validator .error-item {{
            color: #dc2626;
            margin: 5px 0;
        }}
        .validator .more {{
            color: #666;
            font-style: italic;
            margin-top: 5px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            font-size: 14px;
            color: #666;
        }}
        @media (max-width: 600px) {{
            .summary {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
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
            <div class="stat total">
                <div class="number">{len(reports)}</div>
                <div class="label">验证项目</div>
            </div>
            <div class="stat passed">
                <div class="number">{passed_count}</div>
                <div class="label">通过</div>
            </div>
            <div class="stat warning">
                <div class="number">{total_warnings}</div>
                <div class="label">警告</div>
            </div>
            <div class="stat failed">
                <div class="number">{total_errors}</div>
                <div class="label">错误</div>
            </div>
        </div>
        
        <div class="overall {status_class}">
            {overall_status}
        </div>
        
        <div class="validators">
            <h2>详细验证结果</h2>
            {validators_html}
        </div>
        
        <div class="footer">
            基于《中国金融学院金融类专业学位论文写作规范》（2025年5月版）
        </div>
    </div>
</body>
</html>'''
    
    return html


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='论文格式验证报告生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument('doc_path', help='Word文档路径')
    parser.add_argument('--type', dest='thesis_type', default='博士',
                        choices=['本科', '硕士', '博士', 'bachelor', 'master', 'phd'],
                        help='论文类型（默认：博士）')
    parser.add_argument('--output', '-o', dest='output_path',
                        help='输出HTML文件路径')
    
    args = parser.parse_args()
    
    # 转换英文类型名
    type_mapping = {
        'bachelor': '本科',
        'master': '硕士',
        'phd': '博士',
    }
    thesis_type = type_mapping.get(args.thesis_type, args.thesis_type)
    
    generate_html_report(args.doc_path, thesis_type, args.output_path)


if __name__ == '__main__':
    main()

