"""
论文格式验证模块包
基于《中国金融学院金融类专业学位论文写作规范》（2025年5月版）

每个验证器文件只验证一个功能，遵循单一职责原则。
"""

__version__ = "1.0.0"
__author__ = "Thesis Format Tool"

# 字号对照表（磅值）
FONT_SIZES = {
    '初号': 42, '小初': 36, '一号': 26, '小一': 24,
    '二号': 22, '小二': 18, '三号': 16, '小三': 15,
    '四号': 14, '小四': 12, '五号': 10.5, '小五': 9,
    '六号': 7.5, '小六': 6.5,
}

# 论文类型字数要求
WORD_COUNT_REQUIREMENTS = {
    '本科': {'body': (15000, 20000), 'abstract': (0, 300)},
    '硕士': {'body': (25000, None), 'abstract': (500, 1000)},
    '博士': {'body': (100000, None), 'abstract': (2000, 3000)},
}

# 页面设置常量
PAGE_SETUP = {
    'width_mm': 210,
    'height_mm': 297,
    'margin_top_cm': 2.5,
    'margin_bottom_cm': 2.0,
    'margin_left_cm': 2.5,
    'margin_right_cm': 2.0,
    'header_distance_cm': 1.5,
    'footer_distance_cm': 1.75,
}

# 容差设置
TOLERANCE = {
    'margin_cm': 0.1,
    'font_pt': 0.5,
    'line_spacing_pt': 1,
    'page_mm': 1,
}

