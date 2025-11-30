"""
图题验证器
验证图题格式

规范来源：规范4.3
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
    '小五': 9,
}

TOLERANCE = {
    'font_pt': 0.5,
}


class FigureValidator(BaseValidator):
    """图题验证器"""
    
    name = "图题验证"
    description = "验证图题格式：位置在图下方、宋体小五号居中"
    standard_ref = "规范4.3"
    
    def validate(self) -> bool:
        """执行图题验证"""
        
        figure_count = 0
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            
            # 匹配图题模式：图X-X 或 图X.X
            if re.match(r'^图\s*[\d\-\.]+', text):
                figure_count += 1
                self._check_figure_format(para, text)
        
        if figure_count > 0:
            self.add_info(f"检测到 {figure_count} 个图题")
        else:
            self.add_info("未检测到图题")
        
        return len(self.errors) == 0
    
    def _check_figure_format(self, para, text: str):
        """检查图题格式"""
        
        display_text = text[:30] + '...' if len(text) > 30 else text
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            pass  # 居中正确
        else:
            self.add_error(f"图题'{display_text}'应居中对齐")
        
        # 检查字号（小五号 9pt）
        expected_size = FONT_SIZES['小五']
        
        for run in para.runs:
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                    self.add_warning(f"图题'{display_text}'字号应为小五号(9pt)，当前为{actual_size}pt")
            break
        
        # 检查图序与图题间空格
        if not re.match(r'^图\s*[\d\-\.]+\s+\S', text):
            self.add_warning(f"图序与图题之间应空1格: '{display_text}'")


if __name__ == '__main__':
    args = parse_args()
    run_validator(FigureValidator, args.doc_path, args.thesis_type)

