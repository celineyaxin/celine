"""
二级标题验证器
验证二级标题格式

规范来源：规范6.5
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
    '四号': 14,
}

TOLERANCE = {
    'font_pt': 0.5,
}


class Heading2Validator(BaseValidator):
    """二级标题验证器"""
    
    name = "二级标题验证"
    description = "验证二级标题格式：X.X、黑体四号、左对齐"
    standard_ref = "规范6.5"
    
    def validate(self) -> bool:
        """执行二级标题验证"""
        
        heading2_count = 0
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # 匹配二级标题模式：X.X（不含X.X.X）
            # 如 1.1、2.3、10.5 等
            if re.match(r'^\d+\.\d+\s+\S', text) and not re.match(r'^\d+\.\d+\.\d+', text):
                heading2_count += 1
                self._check_heading2_format(para, text)
        
        if heading2_count > 0:
            self.add_info(f"检测到 {heading2_count} 个二级标题")
        else:
            self.add_warning("未检测到二级标题（X.X格式）")
        
        return len(self.errors) == 0
    
    def _check_heading2_format(self, para, text: str):
        """检查二级标题格式"""
        
        display_text = text[:20] + '...' if len(text) > 20 else text
        
        # 检查左对齐
        if para.alignment in [WD_ALIGN_PARAGRAPH.LEFT, None]:
            pass  # 左对齐正确，不重复报告
        else:
            self.add_warning(f"二级标题'{display_text}'应左对齐")
        
        # 检查字号（四号 14pt）
        expected_size = FONT_SIZES['四号']
        
        for run in para.runs:
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                    self.add_warning(f"二级标题'{display_text}'字号应为四号(14pt)，当前为{actual_size}pt")
            break
        
        # 检查段前段后间距（0.5行）
        pf = para.paragraph_format
        if pf.space_before:
            space_before_pt = pf.space_before.pt
            # 0.5行约等于6pt（12pt字号的一半）
            if space_before_pt < 4 or space_before_pt > 10:
                self.add_warning(f"二级标题'{display_text}'段前间距应为0.5行")
        
        if pf.space_after:
            space_after_pt = pf.space_after.pt
            if space_after_pt < 4 or space_after_pt > 10:
                self.add_warning(f"二级标题'{display_text}'段后间距应为0.5行")


if __name__ == '__main__':
    args = parse_args()
    run_validator(Heading2Validator, args.doc_path, args.thesis_type)

