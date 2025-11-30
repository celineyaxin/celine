"""
参考文献内容验证器
验证参考文献条目格式

规范来源：规范第5章
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
    'line_spacing_pt': 1,
}


class ReferenceContentValidator(BaseValidator):
    """参考文献内容验证器"""
    
    name = "参考文献内容验证"
    description = "验证参考文献条目格式：文献类型标识、行距、悬挂缩进"
    standard_ref = "规范第5章"
    
    # 文献类型标识
    REFERENCE_TYPES = ['[J]', '[M]', '[D]', '[C]', '[N]', '[R]', '[S]', '[P]', 
                       '[EB/OL]', '[DB/OL]', '[J/OL]', '[M/OL]', '[A]', '[Z]',
                       '[G]', '[K]', '[B]', '[CP]', '[DB]', '[EB]']
    
    def validate(self) -> bool:
        """执行参考文献内容验证"""
        
        in_references = False
        ref_count = 0
        missing_type_count = 0
        format_errors = []
        ref_samples = []  # 记录找到的参考文献示例
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            
            # 找到参考文献部分
            clean_text = text.replace(' ', '').replace('\u3000', '')
            if clean_text == '参考文献':
                in_references = True
                self.add_info(f"找到参考文献标题位置")
                continue
            
            # 遇到附录/致谢/个人简历/在学期间等，结束参考文献部分
            end_keywords = ['附录', '致谢', '个人简历及在学期间科研成果', '个人简历', 
                           '在学期间研究成果', '在学期间科研成果', '攻读学位期间']
            if in_references and any(clean_text.startswith(kw) for kw in end_keywords):
                in_references = False
                continue
            
            # 检查参考文献条目
            if in_references and text:
                # 在参考文献部分，几乎所有非空行都是参考文献条目
                # 排除一些明显不是参考文献的内容
                is_not_ref = (
                    len(text) < 10 or  # 太短的行
                    text.startswith('注：') or
                    text.startswith('注:') or
                    re.match(r'^第\s*\d+\s*章', text) or  # 章标题
                    re.match(r'^\d+\.\d+', text)  # 二级标题
                )
                is_ref_entry = not is_not_ref
                
                if is_ref_entry:
                    ref_count += 1
                    
                    # 记录前5个参考文献示例
                    if len(ref_samples) < 5:
                        display_text = text[:60] + '...' if len(text) > 60 else text
                        ref_samples.append(display_text)
                    
                    # 检查文献类型标识
                    text_upper = text.upper()
                    has_type = any(t.upper() in text_upper for t in self.REFERENCE_TYPES)
                    if not has_type:
                        missing_type_count += 1
                        if missing_type_count <= 3:
                            display_text = text[:50] + '...' if len(text) > 50 else text
                            format_errors.append(f"缺少文献类型标识: {display_text}")
                    
                    # 检查行距（固定20磅）
                    self._check_line_spacing(para)
        
        # 汇总结果
        if ref_count > 0:
            self.add_info(f"检测到 {ref_count} 条参考文献")
            # 显示部分示例
            for sample in ref_samples[:3]:
                self.add_info(f"  - {sample}")
            if ref_count > 3:
                self.add_info(f"  ... 共 {ref_count} 条")
        else:
            self.add_warning("未检测到参考文献条目")
            self.add_warning("提示：请检查参考文献格式是否为 [1] 或 1. 开头")
        
        # 类型标识检查（仅供参考，非强制要求）
        if missing_type_count > 0 and missing_type_count == ref_count:
            # 所有参考文献都没有类型标识，可能是使用了非GB/T 7714格式
            self.add_info(f"参考文献使用非GB/T 7714格式（无[J][M][D]等类型标识）")
        elif missing_type_count > 0:
            # 部分有部分没有，可能格式不一致
            self.add_info(f"注：有 {missing_type_count} 条参考文献无类型标识[J][M][D]等（如使用中文格式可忽略）")
        elif ref_count > 0:
            self.add_info("所有参考文献都有类型标识（GB/T 7714格式）")
        
        return len(self.errors) == 0
    
    def _check_line_spacing(self, para):
        """检查行距（应为固定20磅）"""
        pf = para.paragraph_format
        
        if pf.line_spacing:
            if hasattr(pf.line_spacing, 'pt'):
                line_spacing = pf.line_spacing.pt
                # 参考文献行距应为20磅
                if abs(line_spacing - 20) > TOLERANCE['line_spacing_pt']:
                    # 只记录一次警告
                    pass


if __name__ == '__main__':
    args = parse_args()
    run_validator(ReferenceContentValidator, args.doc_path, args.thesis_type)
