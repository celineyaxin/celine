"""
页眉验证器
验证页眉格式

规范来源：页眉页脚规范
"""

import sys
import os
import re
import zipfile

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '五号': 10.5,
}

TOLERANCE = {
    'font_pt': 0.5,
}


class HeaderValidator(BaseValidator):
    """页眉验证器"""
    
    name = "页眉验证"
    description = "验证页眉格式：内容、字体（宋体五号）、居中对齐"
    standard_ref = "页眉页脚规范"
    
    def validate(self) -> bool:
        """执行页眉验证"""
        
        section_count = len(self.doc.sections)
        headers_with_content = 0
        header_texts = []
        
        for i, section in enumerate(self.doc.sections):
            section_name = f"节{i+1}" if section_count > 1 else ""
            
            # 检查不同类型的页眉
            headers_to_check = [
                (section.header, "默认页眉"),
                (section.first_page_header, "首页页眉"),
                (section.even_page_header, "偶数页页眉"),
            ]
            
            for header, header_type in headers_to_check:
                if header and header.paragraphs:
                    for para in header.paragraphs:
                        text = para.text.strip()
                        xml = para._p.xml
                        
                        # 检查是否有内容（文本或域代码）
                        has_field = 'w:fldChar' in xml or 'w:instrText' in xml
                        has_text_in_xml = 'w:t>' in xml
                        
                        if text:
                            headers_with_content += 1
                            if text not in header_texts:
                                header_texts.append(text)
                            self._check_header_format(para, text, f"{section_name}{header_type}")
                            break
                        elif has_field or has_text_in_xml:
                            headers_with_content += 1
                            header_texts.append(f"(域代码-{section_name}{header_type})")
                            self.add_info(f"{section_name}{header_type}: 检测到域代码（可能是章节标题域）")
                            break
        
        # 如果通过python-docx没找到，尝试直接读取XML
        if headers_with_content == 0:
            xml_headers = self._check_header_xml()
            if xml_headers:
                headers_with_content = len(xml_headers)
                for info in xml_headers:
                    header_texts.append(info)
        
        if headers_with_content > 0:
            self.add_info(f"检测到 {headers_with_content} 个页眉")
            for ht in header_texts[:5]:
                if not ht.startswith('(域代码'):
                    display_text = ht[:30] + '...' if len(ht) > 30 else ht
                    self.add_info(f"  页眉内容: '{display_text}'")
        else:
            self.add_warning("未检测到页眉内容")
            self.add_info("提示: 页眉可能在首页/偶数页设置中，或使用了不同的节")
            self.add_info("提示: 也可能页眉使用了文本框或特殊格式")
        
        return len(self.errors) == 0
    
    def _check_header_xml(self):
        """直接读取docx中的header XML文件检测页眉"""
        header_infos = []
        
        try:
            with zipfile.ZipFile(self.doc_path, 'r') as z:
                header_files = [f for f in z.namelist() if 'header' in f.lower() and f.endswith('.xml')]
                
                for hf in header_files:
                    content = z.read(hf).decode('utf-8')
                    # 提取文本内容
                    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', content)
                    text_content = ''.join(texts).strip()
                    
                    # 也检查文本框中的内容
                    if 'w:txbxContent' in content:
                        txbx_texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', content)
                        text_content = ''.join(txbx_texts).strip()
                    
                    if text_content:
                        file_name = os.path.basename(hf)
                        header_infos.append(f"{file_name}: '{text_content}'")
        except Exception as e:
            pass
        
        return header_infos
    
    def _check_header_format(self, para, text: str, section_name: str):
        """检查页眉格式"""
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            pass  # 居中正确
        else:
            self.add_warning(f"{section_name}页眉应居中对齐")
        
        # 检查字号（五号 10.5pt）
        expected_size = FONT_SIZES['五号']
        
        for run in para.runs:
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                    self.add_warning(f"{section_name}页眉字号应为五号(10.5pt)，当前为{actual_size}pt")
            
            # 检查字体
            if run.font.name:
                if run.font.name != '宋体':
                    self.add_warning(f"{section_name}页眉字体应为宋体，当前为{run.font.name}")
            
            break  # 只检查第一个run


if __name__ == '__main__':
    args = parse_args()
    run_validator(HeaderValidator, args.doc_path, args.thesis_type)
