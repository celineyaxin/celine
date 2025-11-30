"""
附录验证器
验证附录部分格式

规范来源：规范6.6
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '三号': 16,
    '小四': 12,
}

TOLERANCE = {
    'font_pt': 0.5,
}


class AppendixValidator(BaseValidator):
    """附录验证器"""
    
    name = "附录验证"
    description = "验证附录标题格式：'附 录'两字间空2字符、黑体三号加粗居中"
    standard_ref = "规范6.6"
    
    def validate(self) -> bool:
        """执行附录验证"""
        
        appendix_found = False
        
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text.strip()
            clean_text = text.replace(' ', '')
            
            if clean_text == '附录':
                appendix_found = True
                self._check_title_format(para, text, i)
                break
        
        if not appendix_found:
            self.add_info("未找到附录部分（附录为可选内容）")
        
        return len(self.errors) == 0
    
    def _check_title_format(self, para, text: str, para_index: int):
        """检查附录标题格式"""
        
        # 检查标题内容（两字间空2字符）
        if text == '附  录' or text == '附 录':
            self.add_info("附录标题格式正确：两字间有空格")
        else:
            self.add_warning("附录标题应为'附  录'（两字间空2字符）")
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            self.add_info("附录标题居中对齐")
        else:
            self.add_error("附录标题应居中对齐")
        
        # 检查字号（三号16pt）和加粗
        expected_size = FONT_SIZES['三号']
        
        for run in para.runs:
            # 检查字号
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) <= TOLERANCE['font_pt']:
                    self.add_info(f"附录标题字号: 三号({actual_size}pt)")
                else:
                    self.add_error(f"附录标题字号应为三号(16pt)，当前为{actual_size}pt")
            
            # 检查加粗
            if run.font.bold:
                self.add_info("附录标题已加粗")
            else:
                self.add_error("附录标题应加粗")
            
            break
        
        # 检查分页
        self._check_page_break(para, para_index)
    
    def _check_page_break(self, para, para_index: int):
        """检查是否另起一页"""
        
        has_page_break = False
        
        pPr = para._p.find(qn('w:pPr'))
        if pPr is not None:
            pageBreakBefore = pPr.find(qn('w:pageBreakBefore'))
            if pageBreakBefore is not None:
                val = pageBreakBefore.get(qn('w:val'))
                if val is None or val != '0':
                    has_page_break = True
        
        if not has_page_break and para_index > 0:
            prev_para = self.doc.paragraphs[para_index - 1]
            if 'w:br' in prev_para._p.xml and 'w:type="page"' in prev_para._p.xml:
                has_page_break = True
        
        if has_page_break:
            self.add_info("附录另起一页")
        else:
            self.add_warning("附录应另起一页")


if __name__ == '__main__':
    args = parse_args()
    run_validator(AppendixValidator, args.doc_path, args.thesis_type)

