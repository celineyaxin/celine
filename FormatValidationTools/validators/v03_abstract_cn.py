"""
中文摘要验证器
验证中文摘要标题格式、正文格式、字数要求

规范来源：规范6.3
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '三号': 16, '小四': 12,
}

WORD_COUNT_REQUIREMENTS = {
    '本科': {'body': (15000, 20000), 'abstract': (0, 300)},
    '硕士': {'body': (25000, None), 'abstract': (500, 1000)},
    '博士': {'body': (100000, None), 'abstract': (2000, 3000)},
}

TOLERANCE = {
    'font_pt': 0.5,
    'line_spacing_pt': 1,
}


class AbstractCnValidator(BaseValidator):
    """中文摘要验证器"""
    
    name = "中文摘要验证"
    description = "验证中文摘要标题格式、正文格式、字数要求"
    standard_ref = "规范6.3"
    
    def validate(self) -> bool:
        """执行中文摘要验证"""
        
        abstract_title_found = False
        abstract_text = ""
        in_abstract = False
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            clean_text = text.replace(' ', '')
            
            # 查找摘要标题
            if clean_text == '摘要':
                abstract_title_found = True
                in_abstract = True
                self._check_title_format(para, text)
                continue
            
            # 遇到关键词或英文摘要，结束中文摘要正文
            if text.startswith('关键词') or text.startswith('关键字'):
                in_abstract = False
                continue
            
            if text.upper() == 'ABSTRACT':
                in_abstract = False
                continue
            
            # 收集摘要正文
            if in_abstract and text:
                abstract_text += text
                self._check_body_format(para)
        
        # 验证是否找到摘要
        if not abstract_title_found:
            self.add_error("未找到中文摘要标题")
        
        # 验证字数
        if abstract_text:
            self._check_word_count(abstract_text)
        
        return len(self.errors) == 0
    
    def _check_title_format(self, para, text: str):
        """检查摘要标题格式"""
        
        # 检查标题内容（两字间空2字符）
        if text == '摘  要' or text == '摘 要':
            self.add_info("摘要标题格式正确：两字间有空格")
        else:
            self.add_warning("摘要标题应为'摘  要'（两字间空2字符）")
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            self.add_info("摘要标题居中对齐")
        else:
            self.add_error("摘要标题应居中对齐")
        
        # 检查字体和字号
        expected_size = FONT_SIZES['三号']  # 16pt
        
        for run in para.runs:
            # 检查字号
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) <= TOLERANCE['font_pt']:
                    self.add_info(f"摘要标题字号: 三号({actual_size}pt)")
                else:
                    self.add_error(f"摘要标题字号应为三号(16pt)，当前为{actual_size}pt")
            
            # 检查加粗
            if run.font.bold:
                self.add_info("摘要标题已加粗")
            else:
                self.add_error("摘要标题应加粗")
            
            break  # 只检查第一个run
    
    def _check_body_format(self, para):
        """检查摘要正文格式"""
        
        # 检查字号（小四号 12pt）
        expected_size = FONT_SIZES['小四']  # 12pt
        
        for run in para.runs:
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                    self.add_warning(f"摘要正文字号应为小四号(12pt)，当前为{actual_size}pt")
            break
        
        # 检查行距（固定行距22磅）
        pf = para.paragraph_format
        if pf.line_spacing:
            line_spacing = pf.line_spacing.pt if hasattr(pf.line_spacing, 'pt') else None
            if line_spacing and abs(line_spacing - 22) > TOLERANCE['line_spacing_pt']:
                self.add_warning(f"摘要正文行距应为固定22磅，当前为{line_spacing}磅")
        
        # 检查首行缩进
        if pf.first_line_indent:
            indent_cm = pf.first_line_indent.cm
            if abs(indent_cm - 0.85) > 0.2:
                self.add_warning("摘要正文首行缩进应为2汉字符")
    
    def _check_word_count(self, text: str):
        """检查摘要字数"""
        word_count = len(text)
        
        requirements = WORD_COUNT_REQUIREMENTS.get(self.thesis_type, {})
        abstract_req = requirements.get('abstract', (500, 1000))
        min_words, max_words = abstract_req
        
        if min_words and word_count < min_words:
            self.add_warning(f"中文摘要字数({word_count})少于{self.thesis_type}论文要求({min_words}字)")
        elif max_words and word_count > max_words:
            self.add_warning(f"中文摘要字数({word_count})超过{self.thesis_type}论文要求({max_words}字)")
        else:
            self.add_info(f"中文摘要字数: {word_count}字 (符合{self.thesis_type}论文要求)")


if __name__ == '__main__':
    args = parse_args()
    run_validator(AbstractCnValidator, args.doc_path, args.thesis_type)

