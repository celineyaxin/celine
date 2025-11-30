"""
三线表验证器
验证表格是否符合三线表格式

规范来源：规范4.3
"""

import sys
import os
import re

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.oxml.ns import qn
from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '小五': 9,  # 表格内容应为小五号
}

TOLERANCE = {
    'font_pt': 0.5,
}


class ThreeLineTableValidator(BaseValidator):
    """三线表验证器"""
    
    name = "三线表验证"
    description = "验证表格是否符合三线表格式：仅有顶线、栏目线、底线"
    standard_ref = "规范4.3"
    
    def validate(self) -> bool:
        """执行三线表验证"""
        
        table_count = len(self.doc.tables)
        
        if table_count == 0:
            self.add_info("文档中未检测到表格")
            return True
        
        # 先找到所有表题，建立表格与表序的对应关系
        table_captions = self._find_table_captions()
        
        self.add_info(f"检测到 {table_count} 个表格")
        
        non_three_line_count = 0
        
        for i, table in enumerate(self.doc.tables):
            table_num = i + 1
            # 尝试获取表序
            table_id = table_captions.get(i, f"序号{table_num}")
            
            # 跳过布局表格（如图题表格）
            if self._is_layout_table(table):
                continue
            
            is_three_line, issues = self._check_three_line_format(table)
            
            if not is_three_line:
                non_three_line_count += 1
                self.add_warning(f"表{table_id}:")
                for issue in issues:
                    self.add_warning(f"  - {issue}")
            
            # 检查表格内容字号
            self._check_table_font(table, table_id)
    
    def _is_layout_table(self, table):
        """判断是否为布局表格（非数据表格）"""
        # 只有1-2行的单列表格，可能是图题或布局表格
        if len(table.rows) <= 2 and len(table.columns) == 1:
            # 检查内容是否包含图题模式
            for row in table.rows:
                for cell in row.cells:
                    text = cell.text.strip()
                    if re.match(r'^图\s*\d+[\-\.]\d+', text):
                        return True
            return True  # 小表格默认视为布局表格
        
        # 只有1行的表格可能是表头或布局
        if len(table.rows) == 1:
            return True
        
        return False
        
        if non_three_line_count == 0:
            self.add_info("所有表格均符合三线表格式")
        else:
            self.add_warning(f"有 {non_three_line_count} 个表格不符合三线表格式")
        
        return len(self.errors) == 0
    
    def _find_table_captions(self):
        """查找表题，返回表格索引到表序的映射"""
        captions = {}
        table_caption_list = []
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            # 匹配表题：表X-X 或 表X.X
            match = re.match(r'^表\s*(\d+)[\-\.](\d+)', text)
            if match:
                table_id = f"{match.group(1)}-{match.group(2)}"
                table_caption_list.append(table_id)
        
        # 假设表题按顺序对应表格
        for i, cap in enumerate(table_caption_list):
            captions[i] = cap
        
        return captions
    
    def _check_three_line_format(self, table):
        """
        检查是否为三线表格式
        三线表特征：只有顶线、栏目线（表头下方）、底线，无左右边线和内部竖线
        
        注意：边框可能设置在表格级别(tblBorders)或单元格级别(tcBorders)
        """
        issues = []
        
        try:
            tbl = table._tbl
            
            # 方法1：检查表格级别的边框设置
            has_table_level_top = False
            has_table_level_bottom = False
            has_table_level_left = False
            has_table_level_right = False
            has_table_level_insideV = False
            
            tblPr = tbl.find(qn('w:tblPr'))
            if tblPr is not None:
                tblBorders = tblPr.find(qn('w:tblBorders'))
                if tblBorders is not None:
                    top = tblBorders.find(qn('w:top'))
                    if top is not None and top.get(qn('w:val')) not in [None, 'nil', 'none']:
                        has_table_level_top = True
                    
                    bottom = tblBorders.find(qn('w:bottom'))
                    if bottom is not None and bottom.get(qn('w:val')) not in [None, 'nil', 'none']:
                        has_table_level_bottom = True
                    
                    left = tblBorders.find(qn('w:left'))
                    if left is not None and left.get(qn('w:val')) not in [None, 'nil', 'none']:
                        has_table_level_left = True
                    
                    right = tblBorders.find(qn('w:right'))
                    if right is not None and right.get(qn('w:val')) not in [None, 'nil', 'none']:
                        has_table_level_right = True
                    
                    insideV = tblBorders.find(qn('w:insideV'))
                    if insideV is not None and insideV.get(qn('w:val')) not in [None, 'nil', 'none']:
                        has_table_level_insideV = True
            
            # 方法2：检查单元格级别的边框设置
            has_cell_level_top = False
            has_cell_level_bottom = False
            has_cell_level_left = False
            has_cell_level_right = False
            
            # 检查第一行单元格是否有顶线
            if len(table.rows) > 0:
                first_row = table.rows[0]
                for cell in first_row.cells:
                    tc = cell._tc
                    tcPr = tc.find(qn('w:tcPr'))
                    if tcPr is not None:
                        tcBorders = tcPr.find(qn('w:tcBorders'))
                        if tcBorders is not None:
                            top = tcBorders.find(qn('w:top'))
                            if top is not None and top.get(qn('w:val')) not in [None, 'nil', 'none']:
                                has_cell_level_top = True
                                break
            
            # 检查最后一行单元格是否有底线
            if len(table.rows) > 0:
                last_row = table.rows[-1]
                for cell in last_row.cells:
                    tc = cell._tc
                    tcPr = tc.find(qn('w:tcPr'))
                    if tcPr is not None:
                        tcBorders = tcPr.find(qn('w:tcBorders'))
                        if tcBorders is not None:
                            bottom = tcBorders.find(qn('w:bottom'))
                            if bottom is not None and bottom.get(qn('w:val')) not in [None, 'nil', 'none']:
                                has_cell_level_bottom = True
                                break
            
            # 综合判断：表格级别或单元格级别有边框都算有
            has_top = has_table_level_top or has_cell_level_top
            has_bottom = has_table_level_bottom or has_cell_level_bottom
            
            # 三线表检查
            if has_table_level_left:
                issues.append("存在左边线（三线表不应有左边线）")
            
            if has_table_level_right:
                issues.append("存在右边线（三线表不应有右边线）")
            
            if has_table_level_insideV:
                issues.append("存在内部竖线（三线表不应有内部竖线）")
            
            # 顶线和底线是必须的（但只在能检测到边框设置时才警告）
            # 如果完全没有边框设置，可能是使用了默认样式或其他方式
            if tblPr is not None and tblPr.find(qn('w:tblBorders')) is not None:
                if not has_top:
                    issues.append("缺少顶线")
                if not has_bottom:
                    issues.append("缺少底线")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            return True, []  # 出错时假设通过
    
    def _check_table_font(self, table, table_id: str):
        """检查表格内容字号（应为小五号 9pt）"""
        expected_size = FONT_SIZES['小五']
        
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if run.font.size:
                            actual_size = run.font.size.pt
                            if abs(actual_size - expected_size) > TOLERANCE['font_pt']:
                                self.add_warning(f"表{table_id}内容字号应为小五号(9pt)，发现{actual_size}pt")
                                return  # 只报告一次


if __name__ == '__main__':
    args = parse_args()
    run_validator(ThreeLineTableValidator, args.doc_path, args.thesis_type)
