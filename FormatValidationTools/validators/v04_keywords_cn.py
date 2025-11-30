"""
中文关键词验证器
验证中文关键词格式

规范来源：规范6.3
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '小四': 12,
}


class KeywordsCnValidator(BaseValidator):
    """中文关键词验证器"""
    
    name = "中文关键词验证"
    description = "验证中文关键词格式：标签、分隔符、数量"
    standard_ref = "规范6.3"
    
    def validate(self) -> bool:
        """执行中文关键词验证"""
        
        keywords_found = False
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            
            # 查找关键词行
            if text.startswith('关键词') or text.startswith('关键字'):
                keywords_found = True
                self._check_keywords_format(para, text)
                break
        
        if not keywords_found:
            self.add_error("未找到中文关键词")
        
        return len(self.errors) == 0
    
    def _check_keywords_format(self, para, text: str):
        """检查关键词格式"""
        
        # 检查冒号
        if '：' in text:
            self.add_info("关键词使用中文冒号（：）")
        elif ':' in text:
            self.add_warning("关键词应使用中文冒号（：）而非英文冒号(:)")
        else:
            self.add_warning("关键词后应有冒号")
        
        # 提取关键词内容
        content = text
        if '：' in text:
            content = text.split('：', 1)[1]
        elif ':' in text:
            content = text.split(':', 1)[1]
        
        # 检查分隔符
        if '；' in content:
            keywords = content.split('；')
            self.add_info(f"关键词使用中文分号（；）分隔")
        elif ';' in content:
            keywords = content.split(';')
            self.add_warning("关键词应使用中文分号（；）分隔")
        elif ',' in content or '，' in content:
            keywords = content.replace('，', ',').split(',')
            self.add_warning("关键词应使用中文分号（；）分隔，而非逗号")
        else:
            keywords = [content]
        
        # 检查数量
        keywords = [k.strip() for k in keywords if k.strip()]
        keyword_count = len(keywords)
        
        if 3 <= keyword_count <= 5:
            self.add_info(f"关键词数量: {keyword_count}个 (符合3-5个要求)")
        elif keyword_count < 3:
            self.add_warning(f"关键词数量({keyword_count})少于要求(3-5个)")
        else:
            self.add_warning(f"关键词数量({keyword_count})多于要求(3-5个)")
        
        # 注：规范只要求"黑体小四号"，未明确要求加粗
        # 黑体本身是粗体字体，与bold属性不同


if __name__ == '__main__':
    args = parse_args()
    run_validator(KeywordsCnValidator, args.doc_path, args.thesis_type)

