import pandas as pd

def extract_penalty_records():
    """
    使用匹配成功的商家简称提取行政处罚记录，并包含模型生成全称
    """
    try:
        # 文件路径配置
        matched_file = "/Users/chenyaxin/Desktop/匹配成功的持牌金融机构.xlsx"
        penalty_file = "/Users/chenyaxin/Desktop/信息规范/行政处罚需要完整的全称/提取所属公司.xlsx"
        
        print("开始提取行政处罚记录...")
        
        # 1. 读取匹配成功的商家文件
        matched_df = pd.read_excel(matched_file)
        print(f"匹配成功的商家文件记录数量: {len(matched_df)}")
        
        # 2. 提取机构名称列并去重，同时保留对应的模型生成全称
        # 创建一个简称到全称的映射字典（一个简称可能对应多个全称）
        short_to_full_mapping = {}
        for _, row in matched_df.iterrows():
            short_name = row['机构名称']
            full_name = row['模型生成全称']
            if pd.notna(short_name):
                if short_name not in short_to_full_mapping:
                    short_to_full_mapping[short_name] = []
                if full_name not in short_to_full_mapping[short_name]:
                    short_to_full_mapping[short_name].append(full_name)
        
        short_names = list(short_to_full_mapping.keys())
        print(f"去重后的简称数量: {len(short_names)}")
        
        # 显示前10个简称作为示例
        print(f"前10个简称示例: {list(short_names[:10])}")
        
        # 3. 读取行政处罚文件
        penalty_df = pd.read_excel(penalty_file)
        print(f"行政处罚文件记录数量: {len(penalty_df)}")
        
        # 数据清洗
        penalty_df['所属公司'] = penalty_df['所属公司'].str.strip()
        
        # 4. 用简称匹配行政处罚记录
        penalty_matched = penalty_df[penalty_df['所属公司'].isin(short_names)]
        
        # 5. 为匹配到的行政处罚记录添加对应的模型生成全称
        print("\n为行政处罚记录添加模型生成全称...")
        
        # 创建一个列表来存储最终结果
        final_records = []
        
        for _, penalty_row in penalty_matched.iterrows():
            short_name = penalty_row['所属公司']
            if short_name in short_to_full_mapping:
                # 为每个简称对应的所有全称创建一条记录
                for full_name in short_to_full_mapping[short_name]:
                    new_row = penalty_row.copy()
                    new_row['模型生成全称'] = full_name
                    final_records.append(new_row)
        
        # 转换为DataFrame
        final_df = pd.DataFrame(final_records)
        
        # 6. 统计结果
        total_penalty_records = len(final_df)
        covered_companies = final_df['所属公司'].nunique()
        
        print("\n" + "="*60)
        print("行政处罚记录提取结果")
        print("="*60)
        print(f"使用的简称数量: {len(short_names)}")
        print(f"匹配到的行政处罚记录数量: {total_penalty_records}")
        print(f"覆盖的商家数量: {covered_companies}/{len(short_names)}")
        
        # 7. 行政处罚条目的年度分布
        print("\n行政处罚条目年度分布:")
        if '处罚年' in final_df.columns:
            # 统计年度分布
            year_distribution = final_df['处罚年'].value_counts().sort_index()
            
            for year, count in year_distribution.items():
                if pd.notna(year):
                    print(f"  {int(year)}年: {count}条")
            
            # 统计空值或无效年份
            null_years = final_df['处罚年'].isna().sum()
            if null_years > 0:
                print(f"  无有效年份: {null_years}条")
        else:
            print("未找到'处罚年'列")
        
        # 8. 找出未匹配的简称
        matched_short_names = final_df['所属公司'].unique()
        unmatched_short_names = set(short_names) - set(matched_short_names)
        
        if len(unmatched_short_names) > 0:
            print(f"\n未匹配到行政处罚记录的简称数量: {len(unmatched_short_names)}")
            print(f"前10个未匹配的简称:")
            for i, name in enumerate(list(unmatched_short_names)[:10]):
                print(f"  {i+1}. {name}")
                # 显示对应的全称
                if name in short_to_full_mapping:
                    print(f"     对应全称: {', '.join(short_to_full_mapping[name])}")
        
        # 9. 保存匹配到的行政处罚记录（包含模型生成全称）
        print("\n" + "="*60)
        print("保存结果")
        print("="*60)
        
        output_file = "/Users/chenyaxin/Desktop/行政处罚记录_最终结果.xlsx"
        final_df.to_excel(output_file, index=False)
        print(f"行政处罚记录已保存到: {output_file}")
        print(f"最终文件包含列: {list(final_df.columns)}")
        
        # 10. 按商家统计处罚记录数量
        print(f"\n按商家统计处罚记录数量 (前20个):")
        penalty_by_company = final_df['所属公司'].value_counts().head(20)
        for company, count in penalty_by_company.items():
            print(f"  {company}: {count}条")
            # 显示对应的全称
            if company in short_to_full_mapping:
                print(f"     全称: {', '.join(short_to_full_mapping[company])}")
        
        return {
            'short_names_count': len(short_names),
            'penalty_records_count': total_penalty_records,
            'covered_companies_count': covered_companies,
            'penalty_data': final_df,
            'unmatched_short_names': unmatched_short_names
        }
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    主函数
    """
    result = extract_penalty_records()
    
    if result:
        print(f"\n" + "="*60)
        print("最终统计结果")
        print("="*60)
        print(f"使用的简称数量: {result['short_names_count']}")
        print(f"匹配到的行政处罚记录数量: {result['penalty_records_count']}")
        print(f"覆盖的商家数量: {result['covered_companies_count']}")
        print(f"覆盖率: {result['covered_companies_count']/result['short_names_count']*100:.2f}%")

if __name__ == "__main__":
    main()