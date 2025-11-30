"""
正文引用验证器
验证正文中的引用格式

规范来源：规范5.2
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args


class CitationValidator(BaseValidator):
    """正文引用验证器"""
    
    name = "正文引用验证"
    description = "验证正文引用格式：[X]上标、字号"
    standard_ref = "规范5.2"
    
    # 引用格式模式
    CITATION_PATTERNS = [
        (r'\[\d+(?:[-,]\d+)*\]', '[数字]格式'),           # [1] [1-3] [1,2,3]
        (r'[A-Z][a-z]+\s+(?:and|&)\s+[A-Z][a-z]+[（\(]\d{4}[）\)]', '作者(年份)格式'),  # Author and Author（2023）
        (r'[A-Z][a-z]+\s+et\s+al\.[（\(]\d{4}[）\)]', 'et al.(年份)格式'),  # Author et al.（2023）
        (r'[\u4e00-\u9fff]+等[（\(]\d{4}[）\)]', '中文等(年份)格式'),  # 王某等（2023）
        (r'[\u4e00-\u9fff]+和[\u4e00-\u9fff]+[（\(]\d{4}[）\)]', '中文和(年份)格式'),  # 王某和李某（2023）
    ]
    
    def validate(self) -> bool:
        """执行正文引用验证"""
        
        citation_counts = {}
        citation_samples = {}
        in_references = False
        
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text.strip()
            
            # 检测参考文献部分，跳过
            clean_text = text.replace(' ', '').replace('\u3000', '')
            if clean_text == '参考文献':
                in_references = True
                continue
            if in_references:
                continue
            
            # 跳过参考文献列表中的编号
            if re.match(r'^\s*\[\d+\]', text):
                continue
            
            # 检查各种引用格式
            for pattern, pattern_name in self.CITATION_PATTERNS:
                matches = re.findall(pattern, text)
                if matches:
                    if pattern_name not in citation_counts:
                        citation_counts[pattern_name] = 0
                        citation_samples[pattern_name] = []
                    citation_counts[pattern_name] += len(matches)
                    if len(citation_samples[pattern_name]) < 3:
                        for m in matches[:2]:
                            citation_samples[pattern_name].append(m)
        
        # 汇总结果
        total_citations = sum(citation_counts.values())
        
        if total_citations > 0:
            self.add_info(f"检测到约 {total_citations} 处正文引用")
            for pattern_name, count in citation_counts.items():
                samples = citation_samples.get(pattern_name, [])[:2]
                sample_str = f"（如：{', '.join(samples)}）" if samples else ""
                self.add_info(f"  - {pattern_name}: {count}处 {sample_str}")
        else:
            self.add_info("未检测到明显的正文引用格式")
            self.add_info("提示：常见引用格式包括[1]、作者（年份）等")
        
        return len(self.errors) == 0


if __name__ == '__main__':
    args = parse_args()
    run_validator(CitationValidator, args.doc_path, args.thesis_type)

