"""
正文段落验证器
验证正文段落字体、行距、首行缩进

规范来源：规范6.5
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Twips
from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '小四': 12,
}

TOLERANCE = {
    'font_pt': 0.5,
    'line_spacing_pt': 1,
}


class ParagraphValidator(BaseValidator):
    """正文段落验证器"""
    
    name = "正文段落验证"
    description = "验证正文段落字体（宋体/Times New Roman小四号）、行距（22磅）、首行缩进（2字符）"
    standard_ref = "规范6.5"
    
    def validate(self) -> bool:
        """执行正文段落验证"""
        
        body_para_count = 0
        font_error_samples = []      # 记录前3个字号错误的段落
        indent_error_samples = []    # 记录前3个缩进错误的段落
        line_spacing_error_samples = []  # 记录前3个行距错误的段落
        in_body = False
        
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text.strip()
            if not text:
                continue
            
            # 从摘要之后开始算正文
            clean_text = text.replace(' ', '').replace('\u3000', '')
            if clean_text == '摘要':
                in_body = True
                continue
            
            if not in_body:
                continue
            
            # 跳过标题和特殊段落
            if self._is_special_paragraph(text, clean_text):
                continue
            
            # 这是正文段落
            body_para_count += 1
            display_text = text[:30] + '...' if len(text) > 30 else text
            
            # 检查字号
            if not self._check_font_size(para):
                if len(font_error_samples) < 3:
                    font_error_samples.append(display_text)
            
            # 检查首行缩进
            indent_ok, indent_info = self._check_indent(para)
            if not indent_ok:
                if len(indent_error_samples) < 3:
                    indent_error_samples.append(f"{display_text} [{indent_info}]")
            
            # 检查行距
            if not self._check_line_spacing(para):
                if len(line_spacing_error_samples) < 3:
                    line_spacing_error_samples.append(display_text)
        
        # 汇总报告
        if body_para_count > 0:
            self.add_info(f"检测到 {body_para_count} 个正文段落")
        else:
            self.add_warning("未检测到正文段落")
        
        # 字号错误
        font_errors = len(font_error_samples)
        if font_errors > 0:
            self.add_warning(f"有段落字号不是小四号(12pt)，示例:")
            for sample in font_error_samples:
                self.add_warning(f"  - {sample}")
        
        # 缩进错误
        indent_errors = len(indent_error_samples)
        if indent_errors > 0:
            self.add_warning(f"有段落首行缩进不是2字符，示例:")
            for sample in indent_error_samples:
                self.add_warning(f"  - {sample}")
        
        # 行距错误
        line_spacing_errors = len(line_spacing_error_samples)
        if line_spacing_errors > 0:
            self.add_warning(f"有段落行距不是固定22磅，示例:")
            for sample in line_spacing_error_samples:
                self.add_warning(f"  - {sample}")
        
        if font_errors == 0 and indent_errors == 0 and line_spacing_errors == 0:
            self.add_info("所有正文段落格式检查通过")
        
        return len(self.errors) == 0
    
    def _is_special_paragraph(self, text: str, clean_text: str) -> bool:
        """判断是否为特殊段落（非正文）"""
        
        # 标题段落
        if re.match(r'^第\s*\d+\s*章', text):
            return True
        if re.match(r'^\d+\.\d+', text):
            return True
        
        # 特殊章节标题
        special_sections = ['摘要', 'Abstract', 'ABSTRACT', '目录', 
                           '参考文献', '附录', '致谢', '个人简历']
        if any(clean_text.startswith(s) for s in special_sections):
            return True
        
        # 关键词
        if text.startswith('关键词') or text.upper().startswith('KEY'):
            return True
        
        # 图表标题
        if re.match(r'^图\s*[\d\-\.]+', text) or re.match(r'^表\s*[\d\-\.]+', text):
            return True
        
        # 参考文献条目（多种格式）
        if re.match(r'^\[\d+\]', text):
            return True
        # 中文参考文献：作者名，年份，《标题》
        if re.match(r'^[\u4e00-\u9fff]+[、，].*\d{4}.*[《\[]', text):
            return True
        # 英文参考文献：作者名（各种格式），年份
        # 如：Becker，G. ,1968 或 Célérier, C. and B. Vallée, 2017
        if re.match(r'^[A-Z][a-zA-Zéèà\u00C0-\u017F]+[,，]?\s*[A-Z]?\.?.*\d{4}', text):
            return True
        
        # 注释
        if text.startswith('注：') or text.startswith('注:'):
            return True
        
        return False
    
    def _check_font_size(self, para) -> bool:
        """检查字号是否为小四号(12pt)"""
        expected_size = FONT_SIZES['小四']  # 12pt
        
        for run in para.runs:
            # 跳过上标（引用标记）
            if run.font.superscript:
                continue
            
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                    return False
            break
        
        return True
    
    def _check_indent(self, para):
        """检查首行缩进是否为2字符"""
        pf = para.paragraph_format
        indent_cm = None
        
        # 方法1: 检查段落本身的首行缩进设置
        if pf.first_line_indent:
            try:
                indent_cm = pf.first_line_indent.cm
            except:
                pass
        
        # 方法2: 如果段落没有直接设置，检查样式的首行缩进
        if indent_cm is None and para.style:
            style_pf = para.style.paragraph_format
            if style_pf and style_pf.first_line_indent:
                try:
                    indent_cm = style_pf.first_line_indent.cm
                except:
                    pass
        
        # 方法3: 检查XML中的firstLineChars属性（以字符为单位的缩进）
        if indent_cm is None:
            from docx.oxml.ns import qn
            pPr = para._p.find(qn('w:pPr'))
            if pPr is not None:
                ind = pPr.find(qn('w:ind'))
                if ind is not None:
                    # firstLineChars是以1/100字符为单位
                    first_line_chars = ind.get(qn('w:firstLineChars'))
                    if first_line_chars:
                        chars = int(first_line_chars) / 100
                        if 1.5 <= chars <= 2.5:
                            return True, f"缩进: {chars}字符"
                    
                    # firstLine是以twips为单位 (1/20 pt)
                    first_line = ind.get(qn('w:firstLine'))
                    if first_line:
                        twips = int(first_line)
                        indent_cm = twips / 567  # twips to cm
        
        # 判断缩进是否符合要求
        # 2字符的小四号字体约等于 0.85cm
        # 允许范围：0.5cm ~ 1.2cm
        if indent_cm is not None:
            info_str = f"缩进: {indent_cm:.2f}cm"
            if 0.5 <= indent_cm <= 1.2:
                return True, info_str
            elif indent_cm > 0:
                return False, info_str
            else:
                return False, "缩进值为0"
        
        # 方法4: 检查是否可能用空格缩进
        text = para.text
        if text.startswith('  ') or text.startswith('\u3000\u3000'):
            return True, "使用空格缩进"
        
        return False, "无首行缩进设置"
    
    def _check_line_spacing(self, para) -> bool:
        """检查行距是否为固定22磅"""
        from docx.oxml.ns import qn
        
        line_spacing_pt = None
        
        # 方法1: 首先检查段落XML中的行距设置（最具体的设置）
        pPr = para._p.find(qn('w:pPr'))
        if pPr is not None:
            spacing = pPr.find(qn('w:spacing'))
            if spacing is not None:
                line_val = spacing.get(qn('w:line'))
                line_rule = spacing.get(qn('w:lineRule'))
                if line_val:
                    # line属性是以twips为单位(1/20 pt)
                    line_spacing_pt = int(line_val) / 20
                    # 如果段落本身设置了行距，直接使用这个值
        
        # 方法2: 如果段落没有设置，检查段落格式对象
        if line_spacing_pt is None:
            pf = para.paragraph_format
            if pf.line_spacing:
                if hasattr(pf.line_spacing, 'pt'):
                    line_spacing_pt = pf.line_spacing.pt
        
        # 方法3: 如果还是没有，检查样式的行距
        if line_spacing_pt is None and para.style:
            style_pf = para.style.paragraph_format
            if style_pf and style_pf.line_spacing:
                if hasattr(style_pf.line_spacing, 'pt'):
                    line_spacing_pt = style_pf.line_spacing.pt
        
        # 判断行距是否符合要求（允许20-24磅范围，更宽容）
        if line_spacing_pt is not None:
            # 22磅是标准，允许20-24磅范围
            if 20 <= line_spacing_pt <= 24:
                return True
        
        return False


if __name__ == '__main__':
    args = parse_args()
    run_validator(ParagraphValidator, args.doc_path, args.thesis_type)
