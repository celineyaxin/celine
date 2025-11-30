"""
封面验证器
验证封面必要信息和格式

规范来源：规范6.2
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '二号': 22,
}

TOLERANCE = {
    'font_pt': 0.5,
}


class CoverValidator(BaseValidator):
    """封面验证器"""
    
    name = "封面验证"
    description = "验证封面必要信息（学校、题目、作者、导师等）和格式"
    standard_ref = "规范6.2"
    
    # 封面必须包含的关键词
    REQUIRED_ITEMS = {
        '学校名称': ['对外经济贸易大学', '大学'],
        '论文类型': ['学位论文', '硕士', '博士', '本科'],
        '作者信息': ['姓名', '学号', '作者'],
        '导师信息': ['导师', '指导教师'],
        '专业信息': ['专业', '学科'],
        '学院信息': ['学院', '院系', '金融'],
        '日期': ['年', '月'],
    }
    
    def validate(self) -> bool:
        """执行封面验证"""
        
        found_items = {k: False for k in self.REQUIRED_ITEMS}
        cover_paras = []
        
        # 收集封面段落（直到遇到摘要）
        for para in self.doc.paragraphs:
            text = para.text.strip()
            clean_text = text.replace(' ', '')
            
            # 遇到摘要，封面结束
            if clean_text == '摘要':
                break
            
            if text:
                cover_paras.append((para, text))
                
                # 检查必要信息
                for item, keywords in self.REQUIRED_ITEMS.items():
                    for kw in keywords:
                        if kw in text:
                            found_items[item] = True
                            break
        
        # 检查封面格式
        self._check_cover_format(cover_paras)
        
        # 汇总缺失项
        missing = [k for k, v in found_items.items() if not v]
        if missing:
            self.add_warning(f"封面可能缺少: {', '.join(missing)}")
        else:
            self.add_info("封面包含所有必要信息")
        
        return len(self.errors) == 0
    
    def _check_cover_format(self, cover_paras):
        """检查封面格式"""
        
        for para, text in cover_paras:
            # 检查居中对齐
            if para.alignment != WD_ALIGN_PARAGRAPH.CENTER:
                display_text = text[:15] + '...' if len(text) > 15 else text
                self.add_warning(f"封面内容'{display_text}'应居中对齐")
            
            # 检查论文标题格式（较长的文本，通常是题目）
            is_title = (len(text) > 15 and 
                       not any(kw in text for kw in 
                               ['姓名', '学号', '导师', '专业', '学院', '年', '月', '大学', '学位论文']))
            
            if is_title:
                for run in para.runs:
                    # 检查字号（二号 22pt）
                    if run.font.size:
                        actual_size = run.font.size.pt
                        expected_size = FONT_SIZES['二号']
                        if abs(actual_size - expected_size) <= TOLERANCE['font_pt']:
                            self.add_info("论文标题字号: 二号(22pt)")
                        else:
                            self.add_warning(f"封面论文标题字号应为二号(22pt)，当前为{actual_size}pt")
                    
                    # 检查加粗
                    if run.font.bold:
                        self.add_info("论文标题已加粗")
                    else:
                        self.add_warning("封面论文标题应加粗")
                    
                    break  # 只检查第一个run


if __name__ == '__main__':
    args = parse_args()
    run_validator(CoverValidator, args.doc_path, args.thesis_type)

