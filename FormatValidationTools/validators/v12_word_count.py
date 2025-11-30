"""
正文字数验证器
验证论文正文字数是否符合要求

规范来源：规范第1章
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args

# 字数要求
WORD_COUNT_REQUIREMENTS = {
    '本科': {'body': (15000, 20000), 'name': '1.5万至2万字'},
    '硕士': {'body': (25000, None), 'name': '2.5万字以上'},
    '博士': {'body': (100000, None), 'name': '10万字以上'},
}


class WordCountValidator(BaseValidator):
    """正文字数验证器"""
    
    name = "正文字数验证"
    description = "验证论文正文字数是否符合要求"
    standard_ref = "规范第1章"
    
    def validate(self) -> bool:
        """执行字数验证"""
        
        total_chars = 0
        in_body = False
        in_references = False
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            clean_text = text.replace(' ', '')
            
            # 正文从第一章开始
            if re.match(r'^第\s*1\s*章', text):
                in_body = True
            
            # 参考文献之后不算正文
            if clean_text == '参考文献':
                in_references = True
                in_body = False
            
            # 统计正文字数
            if in_body and not in_references:
                # 排除标题行
                if re.match(r'^第\s*\d+\s*章', text):
                    continue
                if re.match(r'^\d+\.\d+', text):
                    continue
                
                # 统计中文字符和英文单词
                chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
                english_words = len(re.findall(r'[a-zA-Z]+', text))
                
                # 英文单词按2个字符算
                total_chars += chinese_chars + english_words * 2
        
        # 获取要求
        requirements = WORD_COUNT_REQUIREMENTS.get(self.thesis_type, WORD_COUNT_REQUIREMENTS['博士'])
        min_words, max_words = requirements['body']
        req_name = requirements['name']
        
        self.add_info(f"正文字数统计: 约 {total_chars} 字")
        self.add_info(f"{self.thesis_type}论文要求: {req_name}")
        
        # 检查是否符合要求
        if min_words and total_chars < min_words:
            self.add_warning(f"正文字数({total_chars})可能少于{self.thesis_type}论文要求({min_words}字)")
        elif max_words and total_chars > max_words:
            self.add_warning(f"正文字数({total_chars})超过{self.thesis_type}论文建议上限({max_words}字)")
        else:
            self.add_info("正文字数符合要求")
        
        return len(self.errors) == 0


if __name__ == '__main__':
    args = parse_args()
    run_validator(WordCountValidator, args.doc_path, args.thesis_type)

