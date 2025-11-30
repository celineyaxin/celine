"""
批量运行所有验证器
汇总生成验证报告

用法：python run_all.py thesis.docx --type 博士
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

from docx import Document

# 导入所有验证器
from v01_page_setup import PageSetupValidator
from v02_cover import CoverValidator
from v03_abstract_cn import AbstractCnValidator
from v04_keywords_cn import KeywordsCnValidator
from v05_abstract_en import AbstractEnValidator
from v06_keywords_en import KeywordsEnValidator
from v07_toc import TocValidator
from v08_heading1 import Heading1Validator
from v09_heading2 import Heading2Validator
from v10_heading3 import Heading3Validator
from v11_paragraph import ParagraphValidator
from v12_word_count import WordCountValidator
from v13_figure import FigureValidator
from v14_table import TableValidator
from v14b_table_continuation import TableContinuationValidator
from v15_three_line_table import ThreeLineTableValidator
from v16_formula import FormulaValidator
from v17_footnote import FootnoteValidator
from v18_reference_title import ReferenceTitleValidator
from v19_reference_content import ReferenceContentValidator
from v20_citation import CitationValidator
from v21_punctuation import PunctuationValidator
from v22_number import NumberValidator
from v23_china_region import ChinaRegionValidator
from v24_header import HeaderValidator
from v25_footer import FooterValidator
from v26_appendix import AppendixValidator
from v27_acknowledgement import AcknowledgementValidator
from v28_resume import ResumeValidator
from v29_spine import SpineValidator
from v30_structure import StructureValidator

# 完整的验证器列表（按验证顺序排列）
VALIDATORS = [
    PageSetupValidator,          # 1. 页面设置
    CoverValidator,              # 2. 封面
    AbstractCnValidator,         # 3. 中文摘要
    KeywordsCnValidator,         # 4. 中文关键词
    AbstractEnValidator,         # 5. 英文摘要
    KeywordsEnValidator,         # 6. 英文关键词
    TocValidator,                # 7. 目录
    Heading1Validator,           # 8. 一级标题
    Heading2Validator,           # 9. 二级标题
    Heading3Validator,           # 10. 三级标题
    ParagraphValidator,          # 11. 正文段落
    WordCountValidator,          # 12. 字数
    FigureValidator,             # 13. 图题
    TableValidator,              # 14. 表题
    TableContinuationValidator,  # 14b. 续表
    ThreeLineTableValidator,     # 15. 三线表
    FormulaValidator,            # 16. 公式
    FootnoteValidator,           # 17. 脚注
    ReferenceTitleValidator,     # 18. 参考文献标题
    ReferenceContentValidator,   # 19. 参考文献内容
    CitationValidator,           # 20. 正文引用
    PunctuationValidator,        # 21. 标点符号
    NumberValidator,             # 22. 数字格式
    ChinaRegionValidator,        # 23. 中国香港/台湾
    HeaderValidator,             # 24. 页眉
    FooterValidator,             # 25. 页脚
    AppendixValidator,           # 26. 附录
    AcknowledgementValidator,    # 27. 致谢
    ResumeValidator,             # 28. 个人简历
    SpineValidator,              # 29. 书脊
    StructureValidator,          # 30. 论文结构
]


def run_all_validators(doc_path: str, thesis_type: str = '博士', verbose: bool = True):
    """
    运行所有验证器
    
    Args:
        doc_path: Word文档路径
        thesis_type: 论文类型
        verbose: 是否打印详细信息
    
    Returns:
        dict: 汇总报告
    """
    
    if not os.path.exists(doc_path):
        print(f"错误: 文件不存在 - {doc_path}")
        return None
    
    print()
    print("=" * 70)
    print("论文格式验证工具 - 批量验证")
    print(f"文档: {os.path.basename(doc_path)}")
    print(f"论文类型: {thesis_type}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # 汇总结果
    total_errors = 0
    total_warnings = 0
    passed_count = 0
    failed_count = 0
    reports = []
    
    # 逐个运行验证器
    for validator_class in VALIDATORS:
        try:
            validator = validator_class(doc_path, thesis_type)
            validator.validate()
            report = validator.get_report()
            reports.append(report)
            
            if verbose:
                validator.print_report()
            
            total_errors += report['error_count']
            total_warnings += report['warning_count']
            
            if report['passed']:
                passed_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            print(f"运行 {validator_class.name} 时出错: {e}")
            failed_count += 1
    
    # 打印汇总报告
    print()
    print("=" * 70)
    print("汇总报告")
    print("=" * 70)
    print()
    
    print(f"验证器总数: {len(VALIDATORS)}")
    print(f"通过: {passed_count}")
    print(f"未通过: {failed_count}")
    print()
    print(f"总错误数: {total_errors}")
    print(f"总警告数: {total_warnings}")
    print()
    
    # 各验证器状态
    print("各验证器状态:")
    print("-" * 50)
    for report in reports:
        status = "✓" if report['passed'] else "✗"
        errors = report['error_count']
        warnings = report['warning_count']
        print(f"  {status} {report['validator']}: {errors}错误, {warnings}警告")
    
    print()
    print("-" * 70)
    
    # 最终结论
    if total_errors == 0 and total_warnings == 0:
        print("✓ 最终结果: 全部通过")
    elif total_errors == 0:
        print(f"○ 最终结果: 基本通过（有 {total_warnings} 条警告）")
    else:
        print(f"✗ 最终结果: 未通过（有 {total_errors} 条错误需修复）")
    
    print("=" * 70)
    
    return {
        'doc_path': doc_path,
        'thesis_type': thesis_type,
        'timestamp': datetime.now().isoformat(),
        'total_validators': len(VALIDATORS),
        'passed_count': passed_count,
        'failed_count': failed_count,
        'total_errors': total_errors,
        'total_warnings': total_warnings,
        'reports': reports,
        'passed': total_errors == 0,
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='论文格式验证工具 - 批量验证',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python run_all.py thesis.docx
  python run_all.py thesis.docx --type 硕士
  python run_all.py thesis.docx --type phd --quiet
        '''
    )
    
    parser.add_argument('doc_path', help='Word文档路径')
    parser.add_argument('--type', dest='thesis_type', default='博士',
                        choices=['本科', '硕士', '博士', 'bachelor', 'master', 'phd'],
                        help='论文类型（默认：博士）')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='静默模式，只显示汇总报告')
    
    args = parser.parse_args()
    
    # 转换英文类型名
    type_mapping = {
        'bachelor': '本科',
        'master': '硕士',
        'phd': '博士',
    }
    thesis_type = type_mapping.get(args.thesis_type, args.thesis_type)
    
    # 运行验证
    result = run_all_validators(
        args.doc_path,
        thesis_type,
        verbose=not args.quiet
    )
    
    # 返回退出码
    if result and result['passed']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

