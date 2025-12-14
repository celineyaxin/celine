"""
正文引用验证器
验证正文中的引用格式

规范来源：规范5.2

引用格式规范：
(1) 两种基本表述方式：
    - 括号在后：……（作者，年份）
    - 作者在前：作者（年份）认为……

(2) 作者撰写格式：
    - 中文一个作者：A（年份）
    - 英文一个作者：Bollerslev（年份）
    - 中文两个作者：A 和 B（年份）
    - 英文两个作者：Bollerslev and Anderson（年份）
    - 中文三个及以上：A 等（年份）
    - 英文三个及以上：Bollerslev et al.（年份）

(3) 括号内多个引用用分号分隔：
    - （游家兴和李斌，2007；王俊秋和张奇峰，2009）
    - （Brandt et al., 2003；江伟等，2006）
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
    description = "验证正文引用格式：作者（年份）或（作者，年份）"
    standard_ref = "规范5.2"
    
    # 正确的引用格式模式
    CORRECT_PATTERNS = {
        # 作者（年份）格式 - 作者在前
        # 单作者使用特殊处理（在_check_single_author_citations方法中）
        'cn_single': (
            None,  # 特殊处理
            '中文单作者：A（年份）'
        ),
        'cn_two': (
            r'[\u4e00-\u9fff]{2,4}和[\u4e00-\u9fff]{2,4}（\d{4}）',
            '中文双作者：A和B（年份）'
        ),
        'cn_multiple': (
            r'[\u4e00-\u9fff]{2,4}等（\d{4}）',
            '中文多作者：A等（年份）'
        ),
        'en_single': (
            None,  # 特殊处理
            '英文单作者：Author（年份）'
        ),
        'en_two': (
            r'[A-Z][a-z]+ and [A-Z][a-z]+（\d{4}）',
            '英文双作者：A and B（年份）'
        ),
        'en_multiple': (
            r'[A-Z][a-z]+ et al\.（\d{4}）',
            '英文多作者：A et al.（年份）'
        ),
        # 括号内引用格式 - （作者，年份）
        'paren_cn_single': (
            r'（[\u4e00-\u9fff]{2,4}，\d{4}）',
            '括号内中文单作者：（A，年份）'
        ),
        'paren_cn_two': (
            r'（[\u4e00-\u9fff]{2,4}和[\u4e00-\u9fff]{2,4}，\d{4}）',
            '括号内中文双作者：（A和B，年份）'
        ),
        'paren_cn_multiple': (
            r'（[\u4e00-\u9fff]{2,4}等，\d{4}）',
            '括号内中文多作者：（A等，年份）'
        ),
        'paren_en_single': (
            r'（[A-Z][a-z]+，\d{4}）',
            '括号内英文单作者：（Author，年份）'
        ),
        'paren_en_two': (
            r'（[A-Z][a-z]+ and [A-Z][a-z]+，\d{4}）',
            '括号内英文双作者：（A and B，年份）'
        ),
        'paren_en_multiple': (
            r'（[A-Z][a-z]+ et al\.，\d{4}）',
            '括号内英文多作者：（A et al.，年份）'
        ),
        # 括号内多个引用（用分号分隔）
        'paren_multi_citations': (
            r'（[^）]+[；;][^）]+）',
            '括号内多个引用'
        ),
    }
    
    # 可能的错误格式模式
    ERROR_PATTERNS = {
        # 使用英文括号而非中文括号
        'wrong_paren_en': (
            r'[A-Z][a-z]+\s*\(\d{4}\)',
            '使用了英文括号，应使用中文括号（）'
        ),
        'wrong_paren_cn': (
            r'[\u4e00-\u9fff]{2,4}\s*\(\d{4}\)',
            '使用了英文括号，应使用中文括号（）'
        ),
        # 中文作者之间使用"与"而非"和"
        'cn_wrong_connector': (
            r'[\u4e00-\u9fff]{2,4}与[\u4e00-\u9fff]{2,4}[（\(]\d{4}[）\)]',
            '中文双作者应使用"和"连接，不是"与"'
        ),
        # 英文作者使用"&"而非"and"
        'en_wrong_connector': (
            r'[A-Z][a-z]+\s*&\s*[A-Z][a-z]+[（\(]\d{4}[）\)]',
            '英文双作者应使用"and"连接，不是"&"'
        ),
        # 括号内引用使用英文逗号（应使用中文逗号）
        'cn_wrong_comma': (
            r'（[\u4e00-\u9fff]{2,4}(?:和[\u4e00-\u9fff]{2,4}|等)?,\s*\d{4}）',
            '引用应使用中文逗号"，"'
        ),
        'en_wrong_comma': (
            r'（[A-Z][a-z]+(?:\s+(?:and\s+)?[A-Z][a-z]+|\s+et\s+al\.)?,\s*\d{4}）',
            '引用应使用中文逗号"，"'
        ),
    }
    
    def validate(self) -> bool:
        """执行正文引用验证"""
        
        correct_counts = {}
        correct_samples = {}
        error_counts = {}
        error_samples = {}
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
            
            # 跳过目录等
            if re.match(r'^\s*第?\d+章', text) or re.match(r'^\s*\d+\.\d+', text):
                if len(text) < 50:  # 短标题跳过
                    continue
            
            # 检查正确的引用格式
            for pattern_name, (pattern, desc) in self.CORRECT_PATTERNS.items():
                if pattern is None:  # 特殊处理的模式，跳过
                    continue
                matches = re.findall(pattern, text)
                if matches:
                    if pattern_name not in correct_counts:
                        correct_counts[pattern_name] = 0
                        correct_samples[pattern_name] = []
                    correct_counts[pattern_name] += len(matches)
                    for m in matches[:3]:
                        if m not in correct_samples[pattern_name]:
                            correct_samples[pattern_name].append(m)
            
            # 单作者需要特殊处理：排除双作者和多作者的匹配
            self._check_single_author_citations(text, correct_counts, correct_samples)
            
            # 检查可能的错误格式
            for pattern_name, (pattern, desc) in self.ERROR_PATTERNS.items():
                matches = re.findall(pattern, text)
                if matches:
                    if pattern_name not in error_counts:
                        error_counts[pattern_name] = 0
                        error_samples[pattern_name] = []
                    error_counts[pattern_name] += len(matches)
                    for m in matches[:3]:
                        if m not in error_samples[pattern_name]:
                            error_samples[pattern_name].append(m)
        
        # 汇总正确格式
        total_correct = sum(correct_counts.values())
        if total_correct > 0:
            self.add_info(f"检测到约 {total_correct} 处正确格式的引用")
            
            # 分类显示
            author_front = []  # 作者（年份）格式
            paren_style = []   # （作者，年份）格式
            
            for pattern_name, count in correct_counts.items():
                samples = correct_samples.get(pattern_name, [])[:2]
                sample_str = f"（如：{', '.join(samples)}）" if samples else ""
                desc = self.CORRECT_PATTERNS[pattern_name][1]
                
                if pattern_name.startswith('paren_'):
                    paren_style.append(f"    - {desc}: {count}处 {sample_str}")
                else:
                    author_front.append(f"    - {desc}: {count}处 {sample_str}")
            
            if author_front:
                self.add_info("  作者（年份）格式：")
                for line in author_front:
                    self.add_info(line)
            
            if paren_style:
                self.add_info("  （作者，年份）格式：")
                for line in paren_style:
                    self.add_info(line)
        else:
            self.add_info("未检测到标准格式的正文引用")
        
        # 汇总错误格式
        total_errors = sum(error_counts.values())
        if total_errors > 0:
            for pattern_name, count in error_counts.items():
                samples = error_samples.get(pattern_name, [])[:2]
                sample_str = f"如：{', '.join(samples)}" if samples else ""
                desc = self.ERROR_PATTERNS[pattern_name][1]
                self.add_warning(f"发现 {count} 处格式问题：{desc}（{sample_str}）")
        
        # 提示规范格式
        self.add_info("引用格式规范：")
        self.add_info("  - 中文：A（年份）、A和B（年份）、A等（年份）")
        self.add_info("  - 英文：Author（年份）、A and B（年份）、A et al.（年份）")
        self.add_info("  - 括号内统一使用中文逗号：（作者，年份）或（作者，年份；作者，年份）")
        
        return len(self.errors) == 0
    
    def _check_single_author_citations(self, text, counts, samples):
        """检测单作者引用，排除双作者和多作者的情况"""
        
        # 中文单作者：A（年份），但不是"和A"、"与A"开头
        cn_single_pattern = r'[\u4e00-\u9fff]{2,4}（\d{4}）'
        cn_two_pattern = r'[\u4e00-\u9fff]{2,4}和[\u4e00-\u9fff]{2,4}（\d{4}）'
        cn_multi_pattern = r'[\u4e00-\u9fff]{2,4}等（\d{4}）'
        
        # 先找出所有双作者和多作者的匹配位置
        exclude_positions = set()
        for pattern in [cn_two_pattern, cn_multi_pattern]:
            for match in re.finditer(pattern, text):
                for pos in range(match.start(), match.end()):
                    exclude_positions.add(pos)
        
        # 检测单作者，排除在双作者/多作者匹配范围内的
        for match in re.finditer(cn_single_pattern, text):
            if match.start() in exclude_positions:
                continue
            # 检查前一个字符是否是"和"、"与"等
            if match.start() > 0:
                prev_char = text[match.start() - 1]
                if prev_char in '和与':
                    continue
            
            matched_text = match.group()
            if 'cn_single' not in counts:
                counts['cn_single'] = 0
                samples['cn_single'] = []
            counts['cn_single'] += 1
            if matched_text not in samples['cn_single'] and len(samples['cn_single']) < 3:
                samples['cn_single'].append(matched_text)
        
        # 英文单作者：Author（年份），但不是"and Author"开头
        en_single_pattern = r'[A-Z][a-z]+（\d{4}）'
        en_two_pattern = r'[A-Z][a-z]+ and [A-Z][a-z]+（\d{4}）'
        en_multi_pattern = r'[A-Z][a-z]+ et al\.（\d{4}）'
        
        # 先找出所有双作者和多作者的匹配位置
        exclude_positions = set()
        for pattern in [en_two_pattern, en_multi_pattern]:
            for match in re.finditer(pattern, text):
                for pos in range(match.start(), match.end()):
                    exclude_positions.add(pos)
        
        # 检测单作者
        for match in re.finditer(en_single_pattern, text):
            if match.start() in exclude_positions:
                continue
            # 检查前面是否是"and "
            if match.start() >= 4:
                prev_text = text[match.start()-4:match.start()]
                if prev_text.lower() == 'and ':
                    continue
            
            matched_text = match.group()
            if 'en_single' not in counts:
                counts['en_single'] = 0
                samples['en_single'] = []
            counts['en_single'] += 1
            if matched_text not in samples['en_single'] and len(samples['en_single']) < 3:
                samples['en_single'].append(matched_text)


if __name__ == '__main__':
    args = parse_args()
    run_validator(CitationValidator, args.doc_path, args.thesis_type)
