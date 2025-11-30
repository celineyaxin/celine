"""
数字格式验证器
验证数字使用是否规范

规范来源：规范4.1
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args


class NumberValidator(BaseValidator):
    """数字格式验证器"""
    
    name = "数字格式验证"
    description = "验证数字使用是否规范：大数字千分位分隔、统计数据格式"
    standard_ref = "规范4.1"
    
    def validate(self) -> bool:
        """执行数字格式验证"""
        
        issues = {
            'missing_thousand_sep': [],  # 缺少千分位分隔符
            'wrong_percent': [],         # 百分比格式错误
        }
        
        in_skip_section = False
        
        # 需要跳过的章节关键词
        skip_section_starts = ['参考文献', '在学期间研究成果', '在学期间科研成果', 
                               '攻读学位期间', '个人简历及在学期间科研成果']
        skip_section_ends = ['附录', '致谢']
        
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text
            if not text.strip():
                continue
            
            clean_text = text.strip().replace(' ', '').replace('\u3000', '')
            
            # 检测需要跳过的章节开始
            if any(clean_text.startswith(kw) or clean_text == kw for kw in skip_section_starts):
                in_skip_section = True
                continue
            
            # 检测跳过章节结束（遇到其他主要章节）
            if in_skip_section and any(clean_text.startswith(kw) for kw in skip_section_ends):
                in_skip_section = False
            
            # 跳过这些章节
            if in_skip_section:
                continue
            
            line_no = i + 1
            
            # 检查千分位分隔符
            self._check_thousand_separator(text, line_no, issues)
            
            # 检查百分比格式
            self._check_percent_format(text, line_no, issues)
        
        # 汇总结果
        total_issues = sum(len(v) for v in issues.values())
        
        if total_issues == 0:
            self.add_info("数字格式检查通过")
        else:
            for issue_type, data in issues.items():
                if data:
                    if issue_type == 'missing_thousand_sep':
                        self.add_warning(f"大数字可能缺少千分位分隔符: 共{len(data)}处")
                        for item in data[:5]:
                            line_no, number, text_sample = item
                            self.add_warning(f"  - 第{line_no}段: '{number}' 建议写成 '{self._format_with_comma(number)}'")
                        if len(data) > 5:
                            self.add_warning(f"  ... 还有{len(data) - 5}处")
                    elif issue_type == 'wrong_percent':
                        self.add_warning(f"百分比格式问题: 共{len(data)}处")
                        for item in data[:3]:
                            line_no, text_sample = item
                            self.add_warning(f"  - 第{line_no}段: '{text_sample}'")
        
        return len(self.errors) == 0
    
    def _check_thousand_separator(self, text: str, line_no: int, issues: dict):
        """检查大数字是否有千分位分隔符"""
        
        # 查找4位及以上的整数（不含年份、编号等）
        # 排除：年份(1990-2099)、小数、已有逗号的数字、百分比后的数字
        
        # 找出所有4位及以上的数字
        numbers = re.findall(r'\b(\d{4,})\b', text)
        
        for num in numbers:
            # 排除年份 (1900-2099)
            if re.match(r'^(19|20)\d{2}$', num):
                continue
            
            # 排除已经有逗号分隔的（检查原文中该数字附近是否有逗号）
            if f',{num}' in text or f'{num},' in text:
                continue
            
            # 排除小数的整数部分（检查数字后是否紧跟小数点）
            pattern = rf'{num}\.\d'
            if re.search(pattern, text):
                continue
            
            # 排除表格编号、章节编号等 (如 表3-1 中的数字)
            if re.search(rf'[表图第]\s*{num}', text):
                continue
            
            # 排除百分比 (如 12345%)
            if re.search(rf'{num}%', text):
                continue
            
            # 4位以上的数字且>=1000，建议使用千分位
            if int(num) >= 10000:  # 只对>=10000的数字提醒
                text_sample = text[:40] + '...' if len(text) > 40 else text
                issues['missing_thousand_sep'].append((line_no, num, text_sample))
    
    def _format_with_comma(self, num_str: str) -> str:
        """将数字格式化为千分位分隔格式"""
        return '{:,}'.format(int(num_str))
    
    def _check_percent_format(self, text: str, line_no: int, issues: dict):
        """检查百分比格式"""
        
        # 错误格式：百分之+数字（应该用%）
        wrong_percent = re.findall(r'百分之\d+', text)
        
        if wrong_percent:
            text_sample = text[:50] + '...' if len(text) > 50 else text
            issues['wrong_percent'].append((line_no, text_sample))


if __name__ == '__main__':
    args = parse_args()
    run_validator(NumberValidator, args.doc_path, args.thesis_type)

