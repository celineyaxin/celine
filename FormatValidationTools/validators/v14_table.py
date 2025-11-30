"""
表题验证器
验证表题格式

规范来源：规范4.3
"""

import sys
import os
import re

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


class TableValidator(BaseValidator):
    """表题验证器"""
    
    name = "表题验证"
    description = "验证表题格式：位置在表上方、宋体小五号居中"
    standard_ref = "规范4.3"
    
    # 表题正则：更严格的匹配，避免误识别正文
    # 格式：表1-1、表1.1、表 1-1、表 1.1 等，后面可跟空格和标题文字
    TABLE_CAPTION_PATTERN = r'^表\s*(\d+)[\-\.](\d+)\s*(.*)$'
    
    def validate(self) -> bool:
        """执行表题验证"""
        
        table_captions = []
        table_count = len(self.doc.tables)
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            
            # 更严格的表题匹配
            match = re.match(self.TABLE_CAPTION_PATTERN, text)
            if match:
                # 额外检查：表题通常是短段落（<100字）且居中
                if len(text) < 100:
                    chapter = match.group(1)
                    num = match.group(2)
                    title = match.group(3).strip()
                    table_id = f"{chapter}-{num}"
                    table_captions.append((para, text, table_id))
        
        if table_count > 0:
            self.add_info(f"检测到 {table_count} 个表格对象")
        else:
            self.add_info("未检测到表格对象")
        
        if table_captions:
            self.add_info(f"检测到 {len(table_captions)} 个表题:")
            for para, text, table_id in table_captions:
                self.add_info(f"  - 表{table_id}")
                self._check_table_format(para, text, table_id)
        elif table_count > 0:
            self.add_warning("有表格但未检测到表题（格式应为：表X-X 标题）")
        
        return len(self.errors) == 0
    
    def _check_table_format(self, para, text: str, table_id: str):
        """检查表题格式"""
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            pass  # 居中正确
        else:
            self.add_error(f"表{table_id}表题应居中对齐")
        
        # 检查字号（小五号 9pt）
        expected_size = FONT_SIZES['小五']
        
        for run in para.runs:
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                    self.add_warning(f"表{table_id}表题字号应为小五号(9pt)，当前为{actual_size}pt")
            break
        
        # 检查表序与表题间空格
        if not re.match(r'^表\s*\d+[\-\.]\d+\s+\S', text):
            self.add_warning(f"表{table_id}表序与表题之间应空1格")


if __name__ == '__main__':
    args = parse_args()
    run_validator(TableValidator, args.doc_path, args.thesis_type)

