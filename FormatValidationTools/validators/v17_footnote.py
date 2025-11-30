"""
脚注验证器
验证脚注格式

规范来源：规范4.3
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '小五': 9,
}

# 圈号字符
CIRCLED_NUMBERS = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'


class FootnoteValidator(BaseValidator):
    """脚注验证器"""
    
    name = "脚注验证"
    description = "验证脚注格式：上标、圈号或Word脚注"
    standard_ref = "规范4.3"
    
    def validate(self) -> bool:
        """执行脚注验证"""
        
        word_footnote_count = 0
        circled_number_count = 0
        
        for para in self.doc.paragraphs:
            text = para.text
            xml = para._p.xml
            
            # 检测Word脚注引用
            if 'w:footnoteReference' in xml:
                word_footnote_count += 1
            
            # 检测圈号脚注
            for char in CIRCLED_NUMBERS:
                if char in text:
                    circled_number_count += text.count(char)
            
            # 检查上标格式
            self._check_superscript(para)
        
        # 汇总结果
        total_footnotes = word_footnote_count + circled_number_count
        
        if total_footnotes > 0:
            self.add_info(f"检测到脚注引用: 约 {total_footnotes} 处")
            if word_footnote_count > 0:
                self.add_info(f"  Word脚注: {word_footnote_count} 处")
            if circled_number_count > 0:
                self.add_info(f"  圈号脚注: {circled_number_count} 处")
        else:
            self.add_info("未检测到脚注引用")
        
        # 检查脚注内容（如果使用Word脚注功能）
        self._check_footnote_content()
        
        return len(self.errors) == 0
    
    def _check_superscript(self, para):
        """检查脚注引用是否使用上标格式"""
        
        for run in para.runs:
            text = run.text
            
            # 检查圈号是否为上标
            has_circled = any(char in text for char in CIRCLED_NUMBERS)
            if has_circled and not run.font.superscript:
                self.add_warning("圈号脚注应使用上标格式")
                return  # 只报告一次
    
    def _check_footnote_content(self):
        """检查脚注内容格式"""
        
        # Word脚注内容存储在文档的footnotes部分
        # python-docx对脚注支持有限，这里做基础检查
        try:
            # 尝试访问脚注部分
            footnotes_part = self.doc.part.footnotes_part
            if footnotes_part:
                self.add_info("文档包含Word脚注")
        except:
            pass  # 无法访问脚注部分


if __name__ == '__main__':
    args = parse_args()
    run_validator(FootnoteValidator, args.doc_path, args.thesis_type)

