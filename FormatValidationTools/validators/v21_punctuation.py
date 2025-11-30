"""
标点符号验证器
验证中英文标点符号使用是否正确

规范来源：规范4.1
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args


class PunctuationValidator(BaseValidator):
    """标点符号验证器"""
    
    name = "标点符号验证"
    description = "验证中英文标点符号使用是否正确"
    standard_ref = "规范4.1"
    
    def validate(self) -> bool:
        """执行标点符号验证"""
        
        issues = {
            'cn_comma_in_en': [],      # 中文逗号用于英文
            'en_comma_in_cn': [],      # 英文逗号用于中文
            'en_colon_in_cn': [],      # 英文冒号用于中文
            'en_semicolon_in_cn': [],  # 英文分号用于中文
            'en_period_in_cn': [],     # 英文句号用于中文
        }
        
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text
            if not text.strip():
                continue
            
            para_no = i + 1
            
            # 检查中文间使用英文逗号
            # 模式：中文 + 英文逗号 + 中文
            matches = re.finditer(r'([\u4e00-\u9fff]),([\u4e00-\u9fff])', text)
            for m in matches:
                # 获取上下文
                start = max(0, m.start() - 5)
                end = min(len(text), m.end() + 5)
                context = text[start:end]
                issues['en_comma_in_cn'].append((para_no, context))
            
            # 检查中文间使用英文冒号
            matches = re.finditer(r'([\u4e00-\u9fff]):([\u4e00-\u9fff])', text)
            for m in matches:
                start = max(0, m.start() - 5)
                end = min(len(text), m.end() + 5)
                context = text[start:end]
                issues['en_colon_in_cn'].append((para_no, context))
            
            # 检查中文间使用英文分号
            matches = re.finditer(r'([\u4e00-\u9fff]);([\u4e00-\u9fff])', text)
            for m in matches:
                start = max(0, m.start() - 5)
                end = min(len(text), m.end() + 5)
                context = text[start:end]
                issues['en_semicolon_in_cn'].append((para_no, context))
            
            # 检查中文间使用英文句号（不含小数点）
            matches = re.finditer(r'([\u4e00-\u9fff])\.([\u4e00-\u9fff])', text)
            for m in matches:
                # 排除：数字.数字
                if not re.search(r'\d\.\d', text):
                    start = max(0, m.start() - 5)
                    end = min(len(text), m.end() + 5)
                    context = text[start:end]
                    issues['en_period_in_cn'].append((para_no, context))
        
        # 汇总结果
        issue_messages = {
            'en_comma_in_cn': '中文间使用英文逗号(,)',
            'en_colon_in_cn': '中文间使用英文冒号(:)',
            'en_semicolon_in_cn': '中文间使用英文分号(;)',
            'en_period_in_cn': '中文间使用英文句号(.)',
        }
        
        total_issues = 0
        for key, items in issues.items():
            if items:
                total_issues += len(items)
                msg = issue_messages.get(key, key)
                self.add_warning(f"{msg}: 共{len(items)}处")
                # 显示前3个具体位置
                for para_no, context in items[:3]:
                    self.add_warning(f"  - 第{para_no}段: '...{context}...'")
                if len(items) > 3:
                    self.add_warning(f"  ... 还有{len(items) - 3}处")
        
        if total_issues == 0:
            self.add_info("标点符号使用检查通过")
        
        return len(self.errors) == 0


if __name__ == '__main__':
    args = parse_args()
    run_validator(PunctuationValidator, args.doc_path, args.thesis_type)
