import pandas as pd
import re

def remove_all_brackets_content(text):
    """
    移除所有括号及其内容
    """
    if not isinstance(text, str):
        return text
    
    # 移除中文括号及其内容
    text = re.sub(r'（[^）]*）', '', text)
    # 移除英文括号及其内容
    text = re.sub(r'\([^)]*\)', '', text)
    
    # 移除多余空格并去除首尾空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def match_after_removing_brackets(licensed_file, frequency_file, licensed_col='compn', frequency_col='模型生成全称'):
    """
    移除括号内容后进行匹配，并将未匹配的机构写入文件
    """
    try:
        # 读取两个文件
        licensed_df = pd.read_excel(licensed_file)
        frequency_df = pd.read_excel(frequency_file)
        
        # 提取唯一名称（不去除括号）
        licensed_unique = licensed_df[licensed_col].dropna().unique()
        frequency_unique = frequency_df[frequency_col].dropna().unique()
        
        # 创建处理后的唯一名称（去除括号）
        licensed_clean = [remove_all_brackets_content(name) for name in licensed_unique]
        frequency_clean = [remove_all_brackets_content(name) for name in frequency_unique]
        
        # 找出完全未匹配的名称
        completely_unmatched = []
        for i, company in enumerate(licensed_unique):
            # 检查原始匹配
            if company in frequency_unique:
                continue
            
            # 检查移除括号后的匹配
            if licensed_clean[i] in frequency_clean:
                continue
            else:
                # 记录未匹配的名称
                completely_unmatched.append(company)
        
        # 计算匹配率（基于唯一名称）
        total_companies = len(licensed_unique)
        matched_count = total_companies - len(completely_unmatched)
        match_rate = matched_count / total_companies * 100
        
        # 输出结果
        print("="*60)
        print("移除括号内容后的匹配效果")
        print("="*60)
        print(f"持牌金融机构唯一名称数: {total_companies}")
        print(f"成功匹配数: {matched_count}")
        print(f"未匹配数: {len(completely_unmatched)}")
        print(f"匹配率: {match_rate:.2f}%")
        
        # 将未匹配的机构写入文件
        if completely_unmatched:     
            # 写入Excel文件
            excel_filename = "/Users/chenyaxin/Desktop/未匹配的持牌金融机构.xlsx"
            unmatched_df = pd.DataFrame({
                '序号': range(1, len(completely_unmatched)+1),
                '机构名称': completely_unmatched
            })
            unmatched_df.to_excel(excel_filename, index=False)
            
            print(f"\n未匹配机构列表已保存到:")
            print(f"  - {excel_filename}")
        else:
            print("\n所有机构都已成功匹配!")
        
        return {
            'match_rate': match_rate,
            'unmatched_count': len(completely_unmatched),
            'unmatched_companies': completely_unmatched
        }
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        return None

def main():
    """
    主函数
    """
    # 文件路径配置
    licensed_file = "/Users/chenyaxin/Desktop/信息规范/持牌金融机构统计.xlsx"
    frequency_file = "/Users/chenyaxin/Desktop/信息规范/行政处罚需要完整的全称/文件中简称对应企业名称整理.xlsx"
    
    print("移除括号内容后进行匹配...")
    
    # 执行匹配
    result = match_after_removing_brackets(
        licensed_file=licensed_file,
        frequency_file=frequency_file,
        licensed_col='compn',
        frequency_col='模型生成全称'
    )
    
    if result:
        print(f"\n匹配完成!")

if __name__ == "__main__":
    main()