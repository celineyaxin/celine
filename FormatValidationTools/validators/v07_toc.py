"""
目录验证器
验证目录标题格式和目录条目格式

规范来源：规范6.4
"""

import sys
import os
import re
import zipfile

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from base_validator import BaseValidator, run_validator, parse_args

# 常量定义
FONT_SIZES = {
    '三号': 16,
    '小四': 12,
    '五号': 10.5,
}

TOLERANCE = {
    'font_pt': 0.5,
}

# 目录规范要求
TOC_SPEC = {
    '目录标题': {
        'font': '黑体',
        'size': 16,  # 三号
        'bold': True,
        'align': 'center',
        'line_spacing': '多倍行距4',
    },
    '一级标题': {
        'font': '黑体',
        'size': 12,  # 小四
        'line_spacing': 22,  # 固定22磅
        'space_before': 0.5,  # 段前0.5行
        'space_after': 0,
    },
    '二级标题': {
        'font': '黑体',
        'size': 10.5,  # 五号
        'line_spacing': 22,  # 固定22磅
        'space_before': 0,
        'space_after': 0,
        'indent': 1,  # 缩进1个汉字符
    },
}


class TocValidator(BaseValidator):
    """目录验证器"""
    
    name = "目录验证"
    description = "验证目录标题格式（黑体三号加粗居中）和自动生成"
    standard_ref = "规范6.4"
    
    def validate(self) -> bool:
        """执行目录验证"""
        
        toc_title_found = False
        has_auto_toc = False
        
        for para in self.doc.paragraphs:
            text = para.text.strip()
            clean_text = text.replace(' ', '').replace('\u3000', '')  # 去除全角和半角空格
            
            # 查找目录标题（支持多种写法）
            # 1. 独立的"目录"段落
            # 2. 段落开头就是"目录"且长度较短
            if clean_text == '目录':
                toc_title_found = True
                self._check_title_format(para, text)
                continue
            
            # 可能目录标题在段落开头
            if clean_text.startswith('目录') and len(clean_text) <= 10:
                toc_title_found = True
                self._check_title_format(para, text)
                continue
            
            # 检查是否使用自动目录
            xml = para._p.xml
            if 'TOC' in xml or 'w:instrText' in xml:
                has_auto_toc = True
        
        # 如果检测到自动目录但没找到标题，也算找到了目录
        if not toc_title_found and has_auto_toc:
            toc_title_found = True
            self.add_info("检测到Word自动目录（目录标题可能嵌入在目录域中）")
        
        # 验证结果
        if not toc_title_found:
            self.add_warning("未找到独立的目录标题段落（请检查是否有'目录'或'目  录'）")
            self.add_info("提示：如果目录是自动生成的，标题可能嵌入在目录域中")
        
        if has_auto_toc:
            self.add_info("使用了Word自动目录功能")
            # 检查目录条目格式
            self._check_toc_entries()
        else:
            self.add_warning("建议使用Word自动目录功能（插入 → 索引和目录）")
        
        return len(self.errors) == 0
    
    def _check_toc_entries(self):
        """检查目录条目格式 - 从XML中提取目录内容"""
        
        # 从docx的XML中提取带TOC样式的段落内容
        toc_entries = self._extract_toc_from_xml()
        
        if not toc_entries:
            self.add_info("未检测到目录条目内容")
            self.add_info("请手动检查目录格式")
            return
        
        # 统计目录层级
        level_counts = {'TOC1': 0, 'TOC2': 0, 'TOC3': 0}
        
        for entry in toc_entries:
            style = entry['style']
            if 'TOC1' in style or 'toc1' in style.lower():
                level_counts['TOC1'] += 1
            elif 'TOC2' in style or 'toc2' in style.lower():
                level_counts['TOC2'] += 1
            elif 'TOC3' in style or 'toc3' in style.lower():
                level_counts['TOC3'] += 1
        
        self.add_info(f"检测到 {len(toc_entries)} 个目录条目")
        self.add_info(f"目录层级: 一级{level_counts['TOC1']}个, 二级{level_counts['TOC2']}个, 三级{level_counts['TOC3']}个")
        
        # 显示部分目录条目示例
        self.add_info("目录条目示例:")
        for i, entry in enumerate(toc_entries[:5]):
            style = entry['style']
            text = entry['text']
            level = "一级" if "TOC1" in style else ("二级" if "TOC2" in style else "三级")
            display_text = text[:40] + '...' if len(text) > 40 else text
            self.add_info(f"  [{level}] {display_text}")
        
        if len(toc_entries) > 5:
            self.add_info(f"  ... 共 {len(toc_entries)} 个条目")
        
        # 检查目录格式问题
        issues = []
        
        # 1. 检查是否有页码
        entries_without_page = 0
        for entry in toc_entries:
            clean_text = entry['text'].strip()
            if clean_text and not re.search(r'\d+$', clean_text):
                entries_without_page += 1
        
        if entries_without_page > len(toc_entries) * 0.5:
            issues.append("部分目录条目可能缺少页码")
        
        # 2. 检查一级标题是否存在
        if level_counts['TOC1'] == 0:
            issues.append("未检测到一级目录条目（章标题）")
        
        # 3. 检查目录层级是否超过2级
        if level_counts['TOC3'] > 0:
            issues.append(f"规范要求目录层次只需到2级标题，但检测到{level_counts['TOC3']}个三级标题")
        
        # 4. 检查TOC样式定义（这是最准确的方式）
        self._check_toc_style_definitions(issues)
        
        # 报告问题
        if issues:
            for issue in issues:
                self.add_warning(issue)
        else:
            self.add_info("目录结构检查通过")
        
        # 输出规范提示
        self.add_info("目录格式规范提示:")
        self.add_info("  - 一级标题: 黑体小四(12pt), 固定行距22磅, 段前0.5行")
        self.add_info("  - 二级标题: 黑体五号(10.5pt), 固定行距22磅, 缩进1个汉字符")
    
    def _check_toc_style_definitions(self, issues):
        """检查TOC样式定义是否符合规范（最准确的方式）"""
        try:
            with zipfile.ZipFile(self.doc_path, 'r') as z:
                styles_content = z.read('word/styles.xml').decode('utf-8')
                
                # 提取所有样式信息
                style_info = {}
                style_pattern = r'<w:style[^>]*w:styleId="([^"]+)"[^>]*>(.*?)</w:style>'
                for match in re.finditer(style_pattern, styles_content, re.DOTALL):
                    style_id = match.group(1)
                    style_xml = match.group(2)
                    
                    # 提取字号
                    sz_match = re.search(r'<w:sz w:val="(\d+)"', style_xml)
                    font_size = int(sz_match.group(1)) / 2 if sz_match else None
                    
                    # 提取基础样式
                    based_match = re.search(r'<w:basedOn w:val="([^"]+)"', style_xml)
                    based_on = based_match.group(1) if based_match else None
                    
                    # 提取字体
                    font_match = re.search(r'<w:rFonts[^>]*w:eastAsia="([^"]+)"', style_xml)
                    font = font_match.group(1) if font_match else None
                    
                    style_info[style_id] = {
                        'size': font_size, 
                        'based_on': based_on,
                        'font': font
                    }
                
                # 检查TOC1样式（应为小四12pt）
                toc1_size = self._resolve_style_size('TOC1', style_info)
                if toc1_size:
                    if abs(toc1_size - 12) > 0.5:
                        self.add_info(f"TOC1样式字号: {toc1_size}pt (规范要求小四12pt)")
                    else:
                        self.add_info(f"TOC1样式字号: {toc1_size}pt ✓")
                else:
                    self.add_info("TOC1样式字号: 继承默认值")
                
                # 检查TOC2样式（应为五号10.5pt）
                toc2_size = self._resolve_style_size('TOC2', style_info)
                if toc2_size:
                    if abs(toc2_size - 10.5) > 0.5:
                        self.add_info(f"TOC2样式字号: {toc2_size}pt (规范要求五号10.5pt)")
                    else:
                        self.add_info(f"TOC2样式字号: {toc2_size}pt ✓")
                else:
                    self.add_info("TOC2样式字号: 继承默认值")
                    
        except Exception as e:
            pass
    
    
    def _extract_toc_from_xml(self):
        """从docx的XML中提取目录条目（包含格式信息）"""
        toc_entries = []
        
        try:
            with zipfile.ZipFile(self.doc_path, 'r') as z:
                content = z.read('word/document.xml').decode('utf-8')
                
                # 先读取样式定义，获取TOC样式的字号（作为备用）
                style_sizes = self._get_toc_style_sizes(z)
                
                # 提取带TOC样式的段落
                para_pattern = r'<w:p [^>]*>.*?</w:p>'
                paragraphs = re.findall(para_pattern, content, re.DOTALL)
                
                for para in paragraphs:
                    # 检查是否有TOC样式
                    style_match = re.search(r'<w:pStyle w:val="(TOC\d|toc\d)"', para, re.IGNORECASE)
                    if style_match:
                        style = style_match.group(1).upper()
                        
                        # 提取文本
                        texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', para)
                        full_text = ''.join(texts).strip()
                        
                        # 获取字号：优先使用段落run中直接定义的字号
                        font_size = None
                        sz_match = re.search(r'<w:sz w:val="(\d+)"', para)
                        if sz_match:
                            font_size = int(sz_match.group(1)) / 2  # 段落run的直接字号
                        else:
                            font_size = style_sizes.get(style)  # 备用：样式定义的字号
                        
                        # 提取缩进 (w:ind w:left单位是twip, 1twip=1/1440英寸)
                        indent = None
                        ind_match = re.search(r'<w:ind[^>]*w:left="(\d+)"', para)
                        if ind_match:
                            indent = int(ind_match.group(1)) / 1440 * 2.54  # 转换为厘米
                        
                        if full_text:
                            toc_entries.append({
                                'style': style,
                                'text': full_text,
                                'font_size': font_size,
                                'indent': indent,
                            })
        except Exception as e:
            pass
        
        return toc_entries
    
    def _get_toc_style_sizes(self, zip_file):
        """从styles.xml获取TOC样式的字号定义"""
        style_sizes = {}
        
        try:
            styles_content = zip_file.read('word/styles.xml').decode('utf-8')
            
            # 先提取所有样式及其字号和基础样式
            style_info = {}
            style_pattern = r'<w:style[^>]*w:styleId="([^"]+)"[^>]*>.*?</w:style>'
            for match in re.finditer(style_pattern, styles_content, re.DOTALL):
                style_id = match.group(1)
                style_xml = match.group(0)
                
                # 提取字号
                sz_match = re.search(r'<w:sz w:val="(\d+)"', style_xml)
                font_size = int(sz_match.group(1)) / 2 if sz_match else None
                
                # 提取基础样式
                based_match = re.search(r'<w:basedOn w:val="([^"]+)"', style_xml)
                based_on = based_match.group(1) if based_match else None
                
                style_info[style_id] = {'size': font_size, 'based_on': based_on}
            
            # 解析TOC样式的字号（考虑继承）
            for toc_style in ['TOC1', 'TOC2', 'TOC3']:
                size = self._resolve_style_size(toc_style, style_info)
                if size:
                    style_sizes[toc_style] = size
                    
        except Exception as e:
            pass
        
        return style_sizes
    
    def _resolve_style_size(self, style_id, style_info, depth=0):
        """递归解析样式字号（考虑继承链）"""
        if depth > 10 or style_id not in style_info:
            return None
        
        info = style_info[style_id]
        
        # 如果有直接定义的字号，返回
        if info['size']:
            return info['size']
        
        # 否则，查找基础样式的字号
        if info['based_on']:
            return self._resolve_style_size(info['based_on'], style_info, depth + 1)
        
        return None
    
    def _check_title_format(self, para, text: str):
        """检查目录标题格式"""
        
        self.add_info(f"找到目录标题: '{text}'")
        
        # 检查标题内容（两字间空2字符）
        if text == '目  录' or text == '目 录' or text == '目\u3000录':
            self.add_info("目录标题格式正确：两字间有空格")
        elif text == '目录':
            self.add_warning("目录标题应为'目  录'（两字间空2字符）")
        
        # 检查居中对齐
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            self.add_info("目录标题居中对齐")
        else:
            self.add_error("目录标题应居中对齐")
        
        # 检查字号（三号16pt）和加粗
        expected_size = FONT_SIZES['三号']  # 16pt
        
        for run in para.runs:
            # 检查字号
            if run.font.size:
                actual_size = run.font.size.pt
                if abs(actual_size - expected_size) <= TOLERANCE['font_pt']:
                    self.add_info(f"目录标题字号: 三号({actual_size}pt)")
                else:
                    self.add_error(f"目录标题字号应为三号(16pt)，当前为{actual_size}pt")
            
            # 检查加粗
            if run.font.bold:
                self.add_info("目录标题已加粗")
            else:
                self.add_error("目录标题应加粗")
            
            break  # 只检查第一个run


if __name__ == '__main__':
    args = parse_args()
    run_validator(TocValidator, args.doc_path, args.thesis_type)
