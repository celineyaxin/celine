"""
英文摘要验证器
验证英文摘要标题格式、正文格式

规范来源：规范6.3
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '三号': 16, '小四': 12,
}

TOLERANCE = {
    'font_pt': 0.5,
    'line_spacing_pt': 1,
}


class AbstractEnValidator(BaseValidator):
    """英文摘要验证器"""
    
    name = "英文摘要验证"
    description = "验证英文摘要标题格式、正文格式"
    standard_ref = "规范6.3"
    
    def validate(self) -> bool:
        """执行英文摘要验证"""
        
        abstract_title_found = False
        in_abstract = False
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            
            # 查找Abstract标题
            if text.upper() == 'ABSTRACT':
                abstract_title_found = True
                in_abstract = True
                self._check_title_format(para, text)
                continue
            
            # 遇到Keywords，结束英文摘要正文
            if text.lower().startswith('keywords') or text.lower().startswith('key words'):
                in_abstract = False
                continue
            
            # 遇到目录等，结束
            if text.replace(' ', '') in ['目录', '目  录']:
                in_abstract = False
                continue
            
            # 检查摘要正文
            if in_abstract and text:
                self._check_body_format(para)
        
        # 验证是否找到摘要
        if not abstract_title_found:
            self.add_error("未找到英文摘要标题(Abstract)")
        
        return len(self.errors) == 0
    
    def _check_title_format(self, para, text: str):
        """检查Abstract标题格式"""
        
        # 检查大小写
        if text == 'Abstract':
            self.add_info("Abstract标题大小写正确")
        elif text == 'ABSTRACT':
            self.add_warning("Abstract标题建议首字母大写（Abstract）而非全大写")
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            self.add_info("Abstract标题居中对齐")
        else:
            self.add_error("Abstract标题应居中对齐")
        
        # 检查字体和字号
        expected_size = FONT_SIZES['三号']  # 16pt
        
        for run in para.runs:
            # 检查字号
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) <= TOLERANCE['font_pt']:
                    self.add_info(f"Abstract标题字号: 三号({actual_size}pt)")
                else:
                    self.add_error(f"Abstract标题字号应为三号(16pt)，当前为{actual_size}pt")
            
            # 检查加粗
            if run.font.bold:
                self.add_info("Abstract标题已加粗")
            else:
                self.add_error("Abstract标题应加粗")
            
            # 检查字体（规范要求Arial）
            if run.font.name:
                if run.font.name == 'Arial':
                    self.add_info("Abstract标题字体: Arial")
                else:
                    self.add_warning(f"Abstract标题字体应为Arial，当前为{run.font.name}")
            
            break  # 只检查第一个run
    
    def _check_body_format(self, para):
        """检查Abstract正文格式"""
        
        # 检查字号（小四号 12pt）
        expected_size = FONT_SIZES['小四']  # 12pt
        
        for run in para.runs:
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                    self.add_warning(f"Abstract正文字号应为小四号(12pt)，当前为{actual_size}pt")
            
            # 检查字体
            if run.font.name:
                if run.font.name != 'Times New Roman':
                    self.add_warning(f"Abstract正文英文字体应为Times New Roman，当前为{run.font.name}")
            
            break
        
        # 检查行距（固定行距22磅）
        pf = para.paragraph_format
        if pf.line_spacing:
            line_spacing = pf.line_spacing.pt if hasattr(pf.line_spacing, 'pt') else None
            if line_spacing and abs(line_spacing - 22) > TOLERANCE['line_spacing_pt']:
                self.add_warning(f"Abstract正文行距应为固定22磅，当前为{line_spacing}磅")
        
        # 检查首行缩进
        if pf.first_line_indent:
            indent_cm = pf.first_line_indent.cm
            if abs(indent_cm - 0.85) > 0.2:
                self.add_warning("Abstract正文首行缩进应为2字符")


if __name__ == '__main__':
    args = parse_args()
    run_validator(AbstractEnValidator, args.doc_path, args.thesis_type)

