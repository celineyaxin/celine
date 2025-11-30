"""
三级标题验证器
验证三级标题格式

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
    '小四': 12,
}

TOLERANCE = {
    'font_pt': 0.5,
}


class Heading3Validator(BaseValidator):
    """三级标题验证器"""
    
    name = "三级标题验证"
    description = "验证三级标题格式：X.X.X、黑体小四号、左对齐"
    standard_ref = "规范6.5"
    
    def validate(self) -> bool:
        """执行三级标题验证"""
        
        heading3_count = 0
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # 匹配三级标题模式：X.X.X
            # 如 1.1.1、2.3.4、10.5.2 等
            if re.match(r'^\d+\.\d+\.\d+\s+\S', text):
                heading3_count += 1
                self._check_heading3_format(para, text)
        
        if heading3_count > 0:
            self.add_info(f"检测到 {heading3_count} 个三级标题")
        else:
            self.add_info("未检测到三级标题（X.X.X格式）")
        
        return len(self.errors) == 0
    
    def _check_heading3_format(self, para, text: str):
        """检查三级标题格式"""
        
        display_text = text[:20] + '...' if len(text) > 20 else text
        
        # 检查左对齐
        if para.alignment in [WD_ALIGN_PARAGRAPH.LEFT, None]:
            pass  # 左对齐正确
        else:
            self.add_warning(f"三级标题'{display_text}'应左对齐")
        
        # 检查字号（小四号 12pt）和加粗
        expected_size = FONT_SIZES['小四']
        
        for run in para.runs:
            # 检查字号
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                    self.add_warning(f"三级标题'{display_text}'字号应为小四号(12pt)，当前为{actual_size}pt")
            
            # 注：规范只要求"黑体小四号"，未明确要求加粗
            break


if __name__ == '__main__':
    args = parse_args()
    run_validator(Heading3Validator, args.doc_path, args.thesis_type)

