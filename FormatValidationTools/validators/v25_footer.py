"""
页脚页码验证器
验证页脚页码格式

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
    '小五': 9,
}

TOLERANCE = {
    'font_pt': 0.5,
}


class FooterValidator(BaseValidator):
    """页脚页码验证器"""
    
    name = "页脚页码验证"
    description = "验证页脚页码格式：Times New Roman小五号、居中"
    standard_ref = "页眉页脚规范"
    
    def validate(self) -> bool:
        """执行页脚验证"""
        
        section_count = len(self.doc.sections)
        footers_with_content = 0
        footer_infos = []
        
        for i, section in enumerate(self.doc.sections):
            section_name = f"节{i+1}" if section_count > 1 else ""
            
            # 检查不同类型的页脚
            footers_to_check = [
                (section.footer, "默认页脚"),
                (section.first_page_footer, "首页页脚"),
                (section.even_page_footer, "偶数页页脚"),
            ]
            
            for footer, footer_type in footers_to_check:
                if footer and footer.paragraphs:
                    for para in footer.paragraphs:
                        text = para.text.strip()
                        xml = para._p.xml
                        
                        # 检查是否有页码（数字或域代码）
                        has_page_field = (
                            'PAGE' in xml or
                            'w:fldChar' in xml or
                            'NUMPAGES' in xml or
                            'w:instrText' in xml
                        )
                        has_page_num = bool(re.search(r'\d+', text))
                        
                        if text:
                            footers_with_content += 1
                            footer_infos.append(f"{section_name}{footer_type}: {text}")
                            self._check_footer_format(para, text, f"{section_name}{footer_type}")
                            break
                        elif has_page_field:
                            footers_with_content += 1
                            footer_infos.append(f"{section_name}{footer_type}: (页码域)")
                            self.add_info(f"{section_name}{footer_type}: 检测到页码域代码")
                            break
        
        # 如果通过python-docx没找到，尝试直接读取XML
        if footers_with_content == 0:
            xml_footers = self._check_footer_xml()
            if xml_footers:
                footers_with_content = len(xml_footers)
                for info in xml_footers:
                    footer_infos.append(info)
        
        if footers_with_content > 0:
            self.add_info(f"检测到 {footers_with_content} 个页脚/页码")
            for info in footer_infos[:5]:
                self.add_info(f"  {info}")
        else:
            self.add_warning("未检测到页脚页码")
            self.add_info("提示: 页码可能在首页/偶数页设置中，或使用了域代码")
            self.add_info("提示: 也可能页码使用了文本框或特殊格式")
        
        return len(self.errors) == 0
    
    def _check_footer_xml(self):
        """直接读取docx中的footer XML文件检测页码"""
        footer_infos = []
        
        try:
            with zipfile.ZipFile(self.doc_path, 'r') as z:
                footer_files = [f for f in z.namelist() if 'footer' in f.lower() and f.endswith('.xml')]
                
                for ff in footer_files:
                    content = z.read(ff).decode('utf-8')
                    # 提取文本内容
                    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', content)
                    text_content = ''.join(texts).strip()
                    
                    has_page_field = 'PAGE' in content or 'NUMPAGES' in content
                    
                    if text_content or has_page_field:
                        file_name = os.path.basename(ff)
                        if text_content:
                            footer_infos.append(f"{file_name}: '{text_content}'")
                        else:
                            footer_infos.append(f"{file_name}: (页码域)")
        except Exception as e:
            pass
        
        return footer_infos
    
    def _check_footer_format(self, para, text: str, section_name: str):
        """检查页脚格式"""
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            pass  # 居中正确
        else:
            self.add_warning(f"{section_name}页码应居中对齐")
        
        # 检查字号（小五号 9pt）
        expected_size = FONT_SIZES['小五']
        
        for run in para.runs:
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                    self.add_warning(f"{section_name}页码字号应为小五号(9pt)，当前为{actual_size}pt")
            
            # 检查字体
            if run.font.name:
                if run.font.name != 'Times New Roman':
                    self.add_warning(f"{section_name}页码字体应为Times New Roman，当前为{run.font.name}")
            
            break


if __name__ == '__main__':
    args = parse_args()
    run_validator(FooterValidator, args.doc_path, args.thesis_type)
