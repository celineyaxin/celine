"""
英文关键词验证器
验证英文关键词(KEY WORDS)格式

规范来源：规范6.3
- "KEY WORDS": Arial 小四号
- 词组: Times New Roman 小四号
- 用英文";"隔开
- 单词首字母大写
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '小四': 12,
}

TOLERANCE = {
    'font_pt': 0.5,
}


class KeywordsEnValidator(BaseValidator):
    """英文关键词验证器"""
    
    name = "英文关键词验证"
    description = "验证英文关键词(KEY WORDS)格式：Arial小四号"
    standard_ref = "规范6.3"
    
    def validate(self) -> bool:
        """执行英文关键词验证"""
        
        keywords_found = False
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            
            # 查找Keywords行（支持多种写法）
            text_upper = text.upper()
            if text_upper.startswith('KEYWORDS') or text_upper.startswith('KEY WORDS'):
                keywords_found = True
                self._check_keywords_format(para, text)
                break
        
        if not keywords_found:
            self.add_error("未找到英文关键词(KEY WORDS)")
        
        return len(self.errors) == 0
    
    def _check_keywords_format(self, para, text: str):
        """检查Keywords格式"""
        
        # 检查标签写法
        text_upper = text.upper()
        if text_upper.startswith('KEY WORDS'):
            self.add_info("KEY WORDS标签格式正确")
        elif text_upper.startswith('KEYWORDS'):
            self.add_warning("建议使用'KEY WORDS'（空格分开）而非'Keywords'")
        
        # 检查冒号
        if ':' in text:
            self.add_info("KEY WORDS使用英文冒号(:)")
        elif '：' in text:
            self.add_warning("KEY WORDS应使用英文冒号(:)而非中文冒号（：）")
        else:
            self.add_warning("KEY WORDS后应有冒号")
        
        # 提取关键词内容
        content = ""
        if ':' in text:
            content = text.split(':', 1)[1].strip()
        elif '：' in text:
            content = text.split('：', 1)[1].strip()
        
        # 检查分隔符（应为英文分号）
        if '; ' in content:
            self.add_info("使用英文分号+空格(; )分隔")
        elif ';' in content:
            self.add_info("使用英文分号(;)分隔")
        elif ',' in content:
            self.add_warning("关键词应使用英文分号(;)分隔，而非逗号")
        
        # 检查"KEY WORDS"标签的字体（应为Arial小四号）
        expected_size = FONT_SIZES['小四']  # 12pt
        label_checked = False
        
        for run in para.runs:
            run_text_upper = run.text.upper()
            if 'KEY' in run_text_upper or 'WORDS' in run_text_upper:
                label_checked = True
                # 检查字体
                if run.font.name:
                    if run.font.name == 'Arial':
                        self.add_info("KEY WORDS标签使用Arial字体 ✓")
                    else:
                        self.add_warning(f"KEY WORDS标签应使用Arial字体，当前为{run.font.name}")
                
                # 检查字号
                if run.font.size:
                    actual_size = run.font.size.pt
                    if abs(actual_size - expected_size) <= TOLERANCE['font_pt']:
                        self.add_info(f"KEY WORDS标签字号: 小四号({actual_size}pt) ✓")
                    else:
                        self.add_warning(f"KEY WORDS标签字号应为小四号(12pt)，当前为{actual_size}pt")
                break
        
        # 检查关键词内容
        if content:
            self._check_keywords_content(para, content)
    
    def _check_keywords_content(self, para, content: str):
        """检查关键词内容格式"""
        
        # 分割关键词
        if ';' in content:
            keywords = [kw.strip() for kw in content.split(';') if kw.strip()]
        elif ',' in content:
            keywords = [kw.strip() for kw in content.split(',') if kw.strip()]
        else:
            keywords = [content.strip()] if content.strip() else []
        
        if not keywords:
            self.add_warning("未检测到关键词内容")
            return
        
        self.add_info(f"检测到 {len(keywords)} 个英文关键词")
        
        # 检查首字母大写
        capitalization_issues = []
        for kw in keywords:
            words = kw.split()
            for word in words:
                # 跳过介词、冠词等小词（通常不需要大写）
                skip_words = ['a', 'an', 'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by']
                if word.lower() in skip_words and word != words[0]:
                    continue
                # 检查是否首字母大写
                if word and word[0].isalpha() and not word[0].isupper():
                    if len(capitalization_issues) < 3:
                        capitalization_issues.append(f"'{word}'")
        
        if capitalization_issues:
            self.add_warning(f"关键词单词首字母应大写: {', '.join(capitalization_issues)}")
        else:
            self.add_info("关键词首字母大写格式正确 ✓")
        
        # 检查关键词内容的字体（应为Times New Roman）
        content_font_checked = False
        for run in para.runs:
            # 跳过KEY WORDS标签
            run_text_upper = run.text.upper()
            if 'KEY' in run_text_upper or 'WORDS' in run_text_upper or ':' in run.text:
                continue
            
            # 检查关键词内容的字体
            if run.text.strip() and any(kw in run.text for kw in keywords[:1]):
                content_font_checked = True
                if run.font.name:
                    if 'Times' in run.font.name:
                        self.add_info(f"关键词内容使用Times New Roman字体 ✓")
                    else:
                        self.add_warning(f"关键词内容应使用Times New Roman字体，当前为{run.font.name}")
                break
        
        # 显示关键词示例
        if keywords:
            examples = keywords[:3]
            if len(keywords) > 3:
                self.add_info(f"关键词示例: {'; '.join(examples)}; ...")
            else:
                self.add_info(f"关键词: {'; '.join(examples)}")


if __name__ == '__main__':
    args = parse_args()
    run_validator(KeywordsEnValidator, args.doc_path, args.thesis_type)
