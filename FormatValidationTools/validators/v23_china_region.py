"""
中国香港/台湾表述验证器
验证文中是否正确使用"中国香港"、"中国台湾"、"中国澳门"

规范来源：规范4.1、第2章
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args


class ChinaRegionValidator(BaseValidator):
    """中国香港/台湾表述验证器"""
    
    name = "中国香港/台湾表述验证"
    description = "验证是否正确使用'中国香港'、'中国台湾'、'中国澳门'"
    standard_ref = "规范4.1/第2章"
    
    def validate(self) -> bool:
        """执行中国香港/台湾表述验证"""
        
        issues = {
            '香港': [],
            '台湾': [],
            '澳门': [],
        }
        
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text
            if not text.strip():
                continue
            
            # 检查"香港"是否有"中国"前缀
            if '香港' in text:
                matches = re.finditer(r'(?<!中国)香港', text)
                for match in matches:
                    # 获取上下文
                    start = max(0, match.start() - 10)
                    end = min(len(text), match.end() + 10)
                    context = text[start:end]
                    issues['香港'].append((i + 1, context))
            
            # 检查"台湾"是否有"中国"前缀
            if '台湾' in text:
                matches = re.finditer(r'(?<!中国)台湾', text)
                for match in matches:
                    start = max(0, match.start() - 10)
                    end = min(len(text), match.end() + 10)
                    context = text[start:end]
                    issues['台湾'].append((i + 1, context))
            
            # 检查"澳门"是否有"中国"前缀
            if '澳门' in text:
                matches = re.finditer(r'(?<!中国)澳门', text)
                for match in matches:
                    start = max(0, match.start() - 10)
                    end = min(len(text), match.end() + 10)
                    context = text[start:end]
                    issues['澳门'].append((i + 1, context))
        
        # 汇总结果
        total_issues = sum(len(v) for v in issues.values())
        
        if total_issues == 0:
            self.add_info("未发现需要加'中国'前缀的香港/台湾/澳门表述")
        else:
            for region, region_issues in issues.items():
                if region_issues:
                    self.add_warning(f"发现 {len(region_issues)} 处'{region}'应改为'中国{region}'")
                    for line_no, context in region_issues[:3]:
                        self.add_warning(f"  第{line_no}段: ...{context}...")
                    if len(region_issues) > 3:
                        self.add_warning(f"  ... 还有 {len(region_issues) - 3} 处")
        
        return len(self.errors) == 0


if __name__ == '__main__':
    args = parse_args()
    run_validator(ChinaRegionValidator, args.doc_path, args.thesis_type)

