"""
页面设置验证器
验证A4纸张尺寸（PDF规范中只说明了A4尺寸，未说明边距要求）

规范来源：规范6.1
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
PAGE_SETUP = {
    'width_mm': 210,
    'height_mm': 297,
}

TOLERANCE = {
    'page_mm': 1,
}


class PageSetupValidator(BaseValidator):
    """页面设置验证器"""
    
    name = "页面设置验证"
    description = "验证A4纸张尺寸"
    standard_ref = "规范6.1"
    
    def validate(self) -> bool:
        """执行页面设置验证"""
        
        for i, section in enumerate(self.doc.sections):
            section_name = f"节{i+1}" if len(self.doc.sections) > 1 else ""
            
            # 验证纸张尺寸
            self._check_page_size(section, section_name)
        
        return len(self.errors) == 0
    
    def _check_page_size(self, section, section_name: str):
        """检查纸张尺寸"""
        if section.page_width is None or section.page_height is None:
            self.add_warning(f"{section_name}无法获取纸张尺寸信息")
            return
        
        width_mm = section.page_width.mm
        height_mm = section.page_height.mm
        
        width_ok = abs(width_mm - PAGE_SETUP['width_mm']) <= TOLERANCE['page_mm']
        height_ok = abs(height_mm - PAGE_SETUP['height_mm']) <= TOLERANCE['page_mm']
        
        if width_ok and height_ok:
            self.add_info(f"纸张尺寸: A4 ({width_mm:.1f}mm × {height_mm:.1f}mm)")
        else:
            if not width_ok:
                self.add_error(f"{section_name}页面宽度应为210mm，当前为{width_mm:.1f}mm")
            if not height_ok:
                self.add_error(f"{section_name}页面高度应为297mm，当前为{height_mm:.1f}mm")


if __name__ == '__main__':
    args = parse_args()
    run_validator(PageSetupValidator, args.doc_path, args.thesis_type)
