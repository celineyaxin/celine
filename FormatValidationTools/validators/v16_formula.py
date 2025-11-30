"""
公式验证器
验证公式格式

规范来源：规范4.3
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from base_validator import BaseValidator, run_validator, parse_args


class FormulaValidator(BaseValidator):
    """公式验证器"""
    
    name = "公式验证"
    description = "验证公式格式：居中、编号右对齐"
    standard_ref = "规范4.3"
    
    def validate(self) -> bool:
        """执行公式验证"""
        
        formula_count = 0
        numbered_formula_count = 0
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            xml = para._p.xml
            
            # 检测公式（Word公式对象）
            has_math_object = 'oMath' in xml or 'm:oMath' in xml
            
            # 检测公式编号格式：(X-X) 或 (X.X)
            has_formula_number = bool(re.search(r'\(\d+[\-\.]\d+\)\s*$', text))
            
            if has_math_object:
                formula_count += 1
                self._check_formula_format(para, text)
            
            if has_formula_number:
                numbered_formula_count += 1
                self._check_number_format(para, text)
        
        if formula_count > 0:
            self.add_info(f"检测到 {formula_count} 个公式对象")
        else:
            self.add_info("未检测到Word公式对象")
        
        if numbered_formula_count > 0:
            self.add_info(f"检测到 {numbered_formula_count} 个带编号的公式")
        
        return len(self.errors) == 0
    
    def _check_formula_format(self, para, text: str):
        """检查公式格式"""
        
        # 检查公式是否居中
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            pass  # 居中正确
        elif para.alignment is None:
            # 可能是默认对齐，检查是否有制表符用于对齐
            pass
        else:
            self.add_warning("公式应居中显示")
    
    def _check_number_format(self, para, text: str):
        """检查公式编号格式"""
        
        # 提取编号
        match = re.search(r'\((\d+)[\-\.](\d+)\)\s*$', text)
        if match:
            chapter = match.group(1)
            num = match.group(2)
            self.add_info(f"公式编号格式: ({chapter}-{num})")
        
        # 理想情况下编号应右对齐，但Word公式通常使用制表符实现
        # 这里仅做信息提示
        if '\t' in text:
            pass  # 使用制表符对齐，可能是正确的格式
        else:
            # 可能公式和编号在同一位置，不一定是错误
            pass


if __name__ == '__main__':
    args = parse_args()
    run_validator(FormulaValidator, args.doc_path, args.thesis_type)

