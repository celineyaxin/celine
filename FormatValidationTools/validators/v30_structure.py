"""
论文结构顺序验证器
验证论文各部分是否按规范顺序排列

规范来源：规范3.1
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args


class StructureValidator(BaseValidator):
    """论文结构顺序验证器"""
    
    name = "论文结构顺序验证"
    description = "验证论文各部分是否按规范顺序排列"
    standard_ref = "规范3.1"
    
    # 论文标准结构顺序
    STANDARD_ORDER = [
        ('封面', ['对外经济贸易大学', '学位论文']),
        ('摘要', ['摘要', '摘 要', '摘  要']),
        ('Abstract', ['Abstract', 'ABSTRACT']),
        ('目录', ['目录', '目 录', '目  录']),
        ('正文', ['第1章', '第一章', '第 1 章']),
        ('参考文献', ['参考文献']),
        ('附录', ['附录', '附 录']),  # 可选
        ('致谢', ['致谢', '致 谢', '致  谢']),
        ('个人简历', ['个人简历', '科研成果']),
    ]
    
    def validate(self) -> bool:
        """执行结构验证"""
        
        # 记录各部分出现的位置
        found_sections = {}
        
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text.strip()
            clean_text = text.replace(' ', '')
            
            for section_name, keywords in self.STANDARD_ORDER:
                if section_name in found_sections:
                    continue  # 已找到该部分
                
                for kw in keywords:
                    if kw in text or kw.replace(' ', '') in clean_text:
                        found_sections[section_name] = i
                        break
        
        # 检查是否存在必要部分
        required_sections = ['摘要', 'Abstract', '目录', '正文', '参考文献', '致谢']
        optional_sections = ['附录', '个人简历']
        
        missing_required = []
        for section in required_sections:
            if section not in found_sections:
                missing_required.append(section)
        
        if missing_required:
            for section in missing_required:
                self.add_warning(f"未找到必要部分: {section}")
        else:
            self.add_info("所有必要部分都存在")
        
        # 检查顺序
        self._check_order(found_sections)
        
        # 报告可选部分
        for section in optional_sections:
            if section in found_sections:
                self.add_info(f"包含可选部分: {section}")
            else:
                self.add_info(f"未包含可选部分: {section}（可选）")
        
        return len(self.errors) == 0
    
    def _check_order(self, found_sections: dict):
        """检查各部分顺序是否正确"""
        
        # 获取已找到部分的顺序
        order = [(name, pos) for name, pos in found_sections.items()]
        order.sort(key=lambda x: x[1])
        
        self.add_info(f"检测到的结构顺序: {' → '.join([name for name, _ in order])}")
        
        # 检查顺序是否符合规范
        expected_order = [name for name, _ in self.STANDARD_ORDER]
        actual_order = [name for name, _ in order]
        
        # 过滤出实际存在的部分
        expected_filtered = [s for s in expected_order if s in actual_order]
        
        # 比较顺序
        order_correct = True
        for i, section in enumerate(actual_order):
            expected_pos = expected_filtered.index(section) if section in expected_filtered else -1
            if expected_pos != i and expected_pos != -1:
                # 找到实际位置和期望位置不符的情况
                if i < len(expected_filtered) and expected_filtered[i] != section:
                    order_correct = False
        
        if order_correct:
            self.add_info("论文结构顺序正确")
        else:
            self.add_warning("论文结构顺序可能不符合规范")
            self.add_info(f"规范顺序应为: 封面 → 摘要 → Abstract → 目录 → 正文 → 参考文献 → (附录) → 致谢 → 个人简历")


if __name__ == '__main__':
    args = parse_args()
    run_validator(StructureValidator, args.doc_path, args.thesis_type)

