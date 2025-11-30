"""
书脊验证器
验证书脊格式（仅提供格式建议，实际书脊通常单独制作）

规范来源：规范6.6
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '四号': 14,
}


class SpineValidator(BaseValidator):
    """书脊验证器"""
    
    name = "书脊验证"
    description = "检查书脊格式要求：仿宋四号，纵向排列"
    standard_ref = "规范6.6"
    
    def validate(self) -> bool:
        """执行书脊验证"""
        
        # 书脊通常不在Word正文中，而是单独制作
        # 这里提供格式规范说明
        
        self.add_info("书脊格式要求（供参考）:")
        self.add_info("  字体: 仿宋四号(14pt)")
        self.add_info("  方向: 纵向排列")
        self.add_info("  上边界: 约5cm")
        self.add_info("  下边界: 约5cm")
        self.add_info("  内容: 论文题目 + 作者姓名 + 学校名称")
        
        # 尝试在文档中查找书脊相关内容
        spine_found = False
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            if '书脊' in text or '书  脊' in text:
                spine_found = True
                self.add_info("检测到书脊相关内容")
                break
        
        if not spine_found:
            self.add_info("书脊通常单独制作，不在正文Word文档中")
        
        return len(self.errors) == 0


if __name__ == '__main__':
    args = parse_args()
    run_validator(SpineValidator, args.doc_path, args.thesis_type)

