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
    移除括号内容后进行匹配，并提取匹配成功和未匹配的商家
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
        
        # 找出匹配成功的名称和未匹配的名称
        matched_companies = []
        unmatched_companies = []
        
        for i, company in enumerate(licensed_unique):
            # 检查原始匹配
            if company in frequency_unique:
                matched_companies.append(company)
                continue
            
            # 检查移除括号后的匹配
            if licensed_clean[i] in frequency_clean:
                matched_companies.append(company)
            else:
                # 记录未匹配的名称
                unmatched_companies.append(company)
        
        # 计算匹配率（基于唯一名称）
        total_companies = len(licensed_unique)
        matched_count = len(matched_companies)
        unmatched_count = len(unmatched_companies)
        match_rate = matched_count / total_companies * 100
        
        # 输出结果
        print("="*60)
        print("移除括号内容后的匹配效果")
        print("="*60)
        print(f"持牌金融机构唯一名称数: {total_companies}")
        print(f"成功匹配数: {matched_count}")
        print(f"未匹配数: {unmatched_count}")
        print(f"匹配率: {match_rate:.2f}%")
        
        # 提取匹配成功的商家在频率统计文件中的所有记录
        matched_records = frequency_df[frequency_df[frequency_col].isin(matched_companies)]
        
        # 对于通过去除括号匹配的商家，需要额外处理
        for i, company in enumerate(licensed_unique):
            if company not in matched_companies and licensed_clean[i] in frequency_clean:
                # 找到对应的匹配记录
                clean_match_records = frequency_df[frequency_df[frequency_col].apply(remove_all_brackets_content) == licensed_clean[i]]
                matched_records = pd.concat([matched_records, clean_match_records])
        
        # 去重
        matched_records = matched_records.drop_duplicates()
        
        print(f"\n从机构名称频率统计文件中提取到的匹配记录数量: {len(matched_records)}")
        
        # 只提取需要的两列
        matched_records_simplified = matched_records[['模型生成全称', '机构名称']]
        
        # 将匹配成功的机构写入文件
        if len(matched_records_simplified) > 0:
            # 写入Excel文件
            excel_filename = "/Users/chenyaxin/Desktop/匹配成功的持牌金融机构.xlsx"
            matched_records_simplified.to_excel(excel_filename, index=False)
            print(f"匹配成功的机构列表已保存到:")
            print(f"  - {excel_filename}")
        else:
            print("\n没有匹配到任何机构!")
        
        # 将未匹配的机构写入文件
        if unmatched_companies:
            # 写入Excel文件
            unmatched_filename = "/Users/chenyaxin/Desktop/未匹配的持牌金融机构.xlsx"
            unmatched_df = pd.DataFrame({
                '序号': range(1, len(unmatched_companies)+1),
                '机构名称': unmatched_companies
            })
            unmatched_df.to_excel(unmatched_filename, index=False)
            print(f"未匹配的机构列表已保存到:")
            print(f"  - {unmatched_filename}")
            
            # 打印前20个未匹配的机构作为示例
            print(f"\n前20个未匹配的机构:")
            for i, company in enumerate(unmatched_companies[:20]):
                print(f"  {i+1}. {company}")
            if len(unmatched_companies) > 20:
                print(f"  ... 还有 {len(unmatched_companies) - 20} 个未匹配机构")
        else:
            print("\n所有机构都已成功匹配!")
        
        return {
            'match_rate': match_rate,
            'matched_count': matched_count,
            'unmatched_count': unmatched_count,
            'matched_companies': matched_companies,
            'unmatched_companies': unmatched_companies,
            'matched_records': matched_records_simplified
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
        print(f"匹配成功的商家数量: {result['matched_count']}")
        print(f"未匹配的商家数量: {result['unmatched_count']}")
        print(f"提取到的记录数量: {len(result['matched_records'])}")

if __name__ == "__main__":
    main()