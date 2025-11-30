"""
参考文献标题验证器
验证参考文献标题格式

规范来源：规范第5章、规范6.6
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
}

TOLERANCE = {
    'font_pt': 0.5,
}


class ReferenceTitleValidator(BaseValidator):
    """参考文献标题验证器"""
    
    name = "参考文献标题验证"
    description = "验证参考文献标题格式：黑体三号加粗居中"
    standard_ref = "规范第5章/6.6"
    
    def validate(self) -> bool:
        """执行参考文献标题验证"""
        
        ref_title_found = False
        
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text.strip()
            clean_text = text.replace(' ', '')
            
            if clean_text == '参考文献':
                ref_title_found = True
                self._check_title_format(para, text, i)
                break
        
        if not ref_title_found:
            self.add_error("未找到参考文献标题")
        
        return len(self.errors) == 0
    
    def _check_title_format(self, para, text: str, para_index: int):
        """检查参考文献标题格式"""
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            self.add_info("参考文献标题居中对齐")
        else:
            self.add_error("参考文献标题应居中对齐")
        
        # 检查字号（三号16pt）和加粗
        expected_size = FONT_SIZES['三号']  # 16pt
        
        for run in para.runs:
            # 检查字号
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) <= TOLERANCE['font_pt']:
                    self.add_info(f"参考文献标题字号: 三号({actual_size}pt)")
                else:
                    self.add_error(f"参考文献标题字号应为三号(16pt)，当前为{actual_size}pt")
            
            # 检查加粗
            if run.font.bold:
                self.add_info("参考文献标题已加粗")
            else:
                self.add_error("参考文献标题应加粗")
            
            break  # 只检查第一个run
        
        # 检查分页（参考文献应另起一页）
        self._check_page_break(para, para_index)
    
    def _check_page_break(self, para, para_index: int):
        """检查是否另起一页"""
        
        has_page_break = False
        
        # 方法1：检查段落格式中的分页属性
        pPr = para._p.find(qn('w:pPr'))
        if pPr is not None:
            pageBreakBefore = pPr.find(qn('w:pageBreakBefore'))
            if pageBreakBefore is not None:
                val = pageBreakBefore.get(qn('w:val'))
                if val is None or val != '0':
                    has_page_break = True
        
        # 方法2：检查前一段落是否有分页符
        if not has_page_break and para_index > 0:
            prev_para = self.doc.paragraphs[para_index - 1]
            if 'w:br' in prev_para._p.xml and 'w:type="page"' in prev_para._p.xml:
                has_page_break = True
        
        if has_page_break:
            self.add_info("参考文献另起一页")
        else:
            self.add_warning("参考文献应另起一页")


if __name__ == '__main__':
    args = parse_args()
    run_validator(ReferenceTitleValidator, args.doc_path, args.thesis_type)

