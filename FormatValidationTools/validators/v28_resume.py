"""
个人简历及科研成果验证器
验证个人简历及在学期间科研成果部分格式

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


class ResumeValidator(BaseValidator):
    """个人简历及科研成果验证器"""
    
    name = "个人简历及科研成果验证"
    description = "验证个人简历/在学期间研究成果标题格式"
    standard_ref = "规范6.6"
    
    def validate(self) -> bool:
        """执行验证"""
        
        resume_found = False
        
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text.strip()
            clean_text = text.replace(' ', '').replace('\u3000', '')
            
            # 匹配多种可能的标题写法
            # 1. "个人简历及在学期间科研成果"
            if '个人简历' in clean_text and '科研成果' in clean_text:
                resume_found = True
                self._check_title_format(para, text, i)
                break
            
            # 2. "个人简历"
            if clean_text == '个人简历':
                resume_found = True
                self._check_title_format(para, text, i)
                break
            
            # 3. "在学期间研究成果" 或 "在学期间科研成果"
            if clean_text in ['在学期间研究成果', '在学期间科研成果']:
                resume_found = True
                self._check_title_format(para, text, i)
                break
            
            # 4. 包含"在学期间"和"成果"的组合
            if '在学期间' in clean_text and '成果' in clean_text:
                resume_found = True
                self._check_title_format(para, text, i)
                break
        
        if not resume_found:
            self.add_warning("未找到个人简历及在学期间科研成果部分（或'在学期间研究成果'）")
        
        return len(self.errors) == 0
    
    def _check_title_format(self, para, text: str, para_index: int):
        """检查标题格式"""
        
        display_text = text[:30] + '...' if len(text) > 30 else text
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            self.add_info(f"'{display_text}'居中对齐")
        else:
            self.add_error(f"'{display_text}'应居中对齐")
        
        # 检查字号（三号16pt）和加粗
        expected_size = FONT_SIZES['三号']
        
        for run in para.runs:
            # 检查字号
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) <= TOLERANCE['font_pt']:
                    self.add_info(f"标题字号: 三号({actual_size}pt)")
                else:
                    self.add_error(f"标题字号应为三号(16pt)，当前为{actual_size}pt")
            
            # 检查加粗
            if run.font.bold:
                self.add_info("标题已加粗")
            else:
                self.add_error("标题应加粗")
            
            break
        
        # 检查分页
        self._check_page_break(para, para_index)
    
    def _check_page_break(self, para, para_index: int):
        """检查是否另起一页"""
        
        has_page_break = False
        
        # 方法1：检查段落本身的pageBreakBefore属性
        pPr = para._p.find(qn('w:pPr'))
        if pPr is not None:
            pageBreakBefore = pPr.find(qn('w:pageBreakBefore'))
            if pageBreakBefore is not None:
                val = pageBreakBefore.get(qn('w:val'))
                if val is None or val != '0':
                    has_page_break = True
            
            # 检查分节符
            sectPr = pPr.find(qn('w:sectPr'))
            if sectPr is not None:
                has_page_break = True
        
        # 方法2：检查前面几个段落是否有分页符（考虑空段落）
        if not has_page_break:
            # 检查前5个段落
            for i in range(1, min(6, para_index + 1)):
                prev_idx = para_index - i
                if prev_idx < 0:
                    break
                prev_para = self.doc.paragraphs[prev_idx]
                prev_xml = prev_para._p.xml
                
                # 检查分页符
                if 'w:br' in prev_xml and 'w:type="page"' in prev_xml:
                    has_page_break = True
                    break
                
                # 检查分节符
                if '<w:sectPr' in prev_xml:
                    has_page_break = True
                    break
                
                # 如果遇到非空段落还没找到，停止搜索
                if prev_para.text.strip():
                    break
        
        if has_page_break:
            self.add_info("在学期间研究成果部分另起一页 ✓")
        else:
            self.add_warning("在学期间研究成果部分应另起一页")


if __name__ == '__main__':
    args = parse_args()
    run_validator(ResumeValidator, args.doc_path, args.thesis_type)

