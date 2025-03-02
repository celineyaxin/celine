import pandas as pd
import os
import re

def ensure_file_exists(excel_path):
    if not os.path.exists(excel_path):
        print(f"文件不存在：{excel_path}，将创建一个空的Excel文件。")
        df = pd.DataFrame()  # 创建一个空的DataFrame
        df.to_excel(excel_path, index=False)  # 保存为空的Excel文件
    else:
        print(f"文件存在：{excel_path}")

def remove_file(file_path):
    # 检查文件是否存在
    if os.path.exists(file_path):
        # 删除文件
        os.remove(file_path)
        print(f"文件已删除：{file_path}")
    else:
        print(f"文件不存在：{file_path}")

def append_to_excel(df, excel_path, sheet_name='Sheet1'):
    """
    将DataFrame追加到Excel文件中指定的工作表。
    
    :param df: 要追加的DataFrame
    :param excel_path: Excel文件路径
    :param sheet_name: 工作表名称，默认为'Sheet1'
    """
    with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        # 检查工作表是否存在
        if sheet_name in writer.sheets:
            sheet = writer.sheets[sheet_name]
            max_row = sheet.max_row
            # 判断工作表中是否已有列名
            if max_row > 1 or (max_row == 1 and sheet.cell(row=1, column=1).value is not None):
                header_value = False
                startrow_value = max_row
            else:
                header_value = True
                startrow_value = 0
        else:
            header_value = True
            startrow_value = 0
        
        df.to_excel(writer, sheet_name=sheet_name, index=False, header=header_value, startrow=startrow_value)
    print(f"\n数据已追加到文件: {excel_path}")

def read_items_from_excel(excel_path, code_column='Symbol'):
    """从Excel文件中读取股票代码列表"""
    try:
        # 读取Excel文件，将第一列作为字符串读取
        df = pd.read_excel(excel_path, dtype={0: str})

        # 确保这一列存在
        if code_column not in df.columns:
            raise ValueError(f"Excel文件中未找到'{code_column}'列")

        # 提取并去重
        items = df[code_column].unique().tolist()

        if code_column=='Symbol':
            # 移除可能的前导零，然后重新格式化为6位数字
            items = [str(int(code)).zfill(6) for code in items if str(code).strip()]

        print(f"从Excel中读取到 {len(items)} 个元素")
        return items

    except Exception as e:
        print(f"读取Excel文件出错: {e}")
        return []  

def contains_revision(filename):
    """判断文件名中的括号内是否包含'修订'两个字"""
    # 使用正则表达式查找括号内的内容
    patterns = [
        r'（[^）]*修订[^）]*）',
        r'（[^）]*修正稿[^）]*）?',
        r'（[^）]*修改草案[^）]*）?',
        r'.*修订稿$',
        r'.*修订版$',
        r'.*修订案$',
        r'修订稿',
        r'（[^\)]*修订[^\)]*\)',
        r'\([^）]*修正稿[^）]*）?',
        r'\([^）]*修改草案[^）]*）?',
        r'\([^\)]*修订[^\)]*\)',
        r'\([^\)]*修正稿[^\)]*\)?',
        r'\([^\)]*修改草案[^\)]*\)?'
    ]
    for pattern in patterns:
        matches = re.finditer(pattern, filename, re.IGNORECASE | re.DOTALL)
        # 将迭代器转换为列表
        matches_list = list(matches)
        # import pdb
        # pdb.set_trace()
        if matches_list:
            return False # 如果找到匹配项，返回 False；否则返回 True
    return True