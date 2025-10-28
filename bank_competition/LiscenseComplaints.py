import pandas as pd
import os
import glob
import re 

def extract_complaints_by_company(csv_folder, company_list_file, output_file, company_column='投诉对象', content_column='发起投诉内容'):
    """
    从多个CSV文件中根据投诉对象提取对应的完整投诉记录
    
    参数:
    csv_folder: CSV文件所在文件夹路径
    company_list_file: 机构列表文件路径
    output_file: 输出文件路径
    company_column: 投诉对象列名
    content_column: 投诉内容列名
    """
    
    try:
        # 读取机构列表，包含投诉对象、商家编码和compn
        print("正在读取机构列表...")
        company_df = pd.read_excel(company_list_file, sheet_name='Sheet1')
        
        print(f"Excel总行数: {len(company_df)}")
        print(f"投诉对象列非空行数: {company_df['投诉对象'].notna().sum()}")
        print(f"投诉对象列唯一值数量: {company_df['投诉对象'].nunique()}")
        
        # 检查必要的列是否存在
        if '投诉对象' not in company_df.columns:
            print("错误: 机构列表文件中缺少'投诉对象'列")
            return None, 0, 0
        
        if 'compn' not in company_df.columns:
            print("错误: 机构列表文件中缺少'compn'列")
            return None, 0, 0
            
        # 创建投诉对象到商家编码和compn的映射字典
        company_code_mapping = {}
        company_compn_mapping = {}
        
        for _, row in company_df.iterrows():
            company = row['投诉对象']
            if pd.notna(company):
                # 商家编码
                company_code = row['商家编码'] if pd.notna(row.get('商家编码')) else ''
                company_code_mapping[company] = company_code
                
                # compn
                compn = row['compn'] if pd.notna(row.get('compn')) else ''
                company_compn_mapping[company] = compn
        
        company_names = list(company_code_mapping.keys())
        print(f"已加载 {len(company_names)} 个投诉对象")
        
        # 检查重复的投诉对象
        duplicate_mask = company_df['投诉对象'].duplicated(keep=False) & company_df['投诉对象'].notna()
        duplicates = company_df[duplicate_mask]
        if not duplicates.empty:
            print(f"\n发现 {len(duplicates)} 个重复的投诉对象:")
            for company in duplicates['投诉对象'].unique():
                dup_rows = duplicates[duplicates['投诉对象'] == company]
                print(f"  '{company}' 出现了 {len(dup_rows)} 次:")
                for _, row in dup_rows.iterrows():
                    code = row.get('商家编码', '无')
                    compn = row.get('compn', '无')
                    print(f"     商家编码: {code}, compn: {compn}")

        # 获取所有CSV文件
        csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))
        print(f"找到 {len(csv_files)} 个CSV文件")
        
        # 初始化结果列表和未匹配的投诉对象集合
        all_matched_rows = []
        matched_companies = set()
        
        # 处理每个CSV文件
        for i, csv_file in enumerate(csv_files, 1):
            print(f"正在处理文件 {i}/{len(csv_files)}: {os.path.basename(csv_file)}")
            
            try:
                # 读取CSV文件
                df = pd.read_csv(csv_file)
                
                # 检查必要的列是否存在
                missing_columns = []
                if company_column not in df.columns:
                    missing_columns.append(company_column)
                if content_column not in df.columns:
                    missing_columns.append(content_column)
                    
                if missing_columns:
                    print(f"  跳过文件 {csv_file}，缺少列: {', '.join(missing_columns)}")
                    print(f"  文件中的列: {', '.join(df.columns.tolist())}")
                    continue
                
                # 清理数据
                df[company_column] = df[company_column].fillna('').astype(str).str.strip()
                
                # 对每个机构名称，查找匹配的投诉记录
                for company in company_names:
                    company_clean = company.strip().lower()
                    mask = df[company_column].fillna('').str.strip().str.lower() == company_clean      
                    matched_rows = df.loc[mask].copy()

                   
                    # 如果有匹配的记录，添加到结果中
                    if not matched_rows.empty:
                        # 添加匹配的机构名称、商家编码和compn
                        matched_rows['匹配的投诉对象'] = company
                        matched_rows['商家编码'] = company_code_mapping[company]
                        matched_rows['compn'] = company_compn_mapping[company]  # 添加compn列
                        all_matched_rows.append(matched_rows)
                        # 记录匹配到的投诉对象
                        matched_companies.add(company)
                        
            except Exception as e:
                print(f"  处理文件 {csv_file} 时出错: {str(e)}")
                continue
        
        # 合并所有匹配的记录
        if all_matched_rows:
            print("正在合并所有匹配的记录...")
            result_df = pd.concat(all_matched_rows, ignore_index=True)
            
            # 重新排列列的顺序，将重要列放在前面
            important_columns = ['商家编码', 'compn', '匹配的投诉对象', company_column, content_column]
            other_columns = [col for col in result_df.columns if col not in important_columns]
            new_column_order = important_columns + other_columns
            result_df = result_df[new_column_order]
            
            # 按投诉对象排序
            result_df = result_df.sort_values(company_column)
            
            # 保存结果到CSV
            result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            # 计算统计信息
            covered_companies = len(matched_companies)  # 覆盖的商家数量
            total_complaints = len(result_df)  # 总投诉数量
            coverage_rate = (covered_companies / len(company_names)) * 100  # 覆盖率
            
            # 计算商家编码覆盖率
            valid_codes = result_df['商家编码'].notna() & (result_df['商家编码'].astype(str).str.strip() != '')
            valid_code_count = valid_codes.sum()
            code_coverage_rate = (valid_code_count / total_complaints) * 100
            
            # 计算compn覆盖率
            valid_compn = result_df['compn'].notna() & (result_df['compn'].astype(str).str.strip() != '')
            valid_compn_count = valid_compn.sum()
            compn_coverage_rate = (valid_compn_count / total_complaints) * 100
            
            # 找出未匹配的投诉对象
            all_companies_set = set(company_names)
            unmatched_companies = all_companies_set - matched_companies
            
            print(f"\n处理完成!")
            print(f"共为 {covered_companies} 个投诉对象找到投诉记录")
            print(f"总投诉记录数: {total_complaints}")
            print(f"投诉对象覆盖率: {coverage_rate:.2f}% ({covered_companies}/{len(company_names)})")
            print(f"商家编码覆盖率: {code_coverage_rate:.2f}% ({valid_code_count}/{total_complaints})")
            print(f"compn覆盖率: {compn_coverage_rate:.2f}% ({valid_compn_count}/{total_complaints})")
            print(f"结果已保存到: {output_file}")
            
            # 打印未匹配的投诉对象
            if unmatched_companies:
                print(f"\n未找到匹配记录的投诉对象 ({len(unmatched_companies)}个):")
                for i, company in enumerate(sorted(unmatched_companies), 1):
                    code = company_code_mapping.get(company, '无')
                    compn = company_compn_mapping.get(company, '无')
                    print(f"  {i}. {company} (商家编码: {code}, compn: {compn})")
            else:
                print(f"\n所有投诉对象都找到了匹配记录!")
            
            return result_df, covered_companies, total_complaints
        else:
            print("没有找到任何匹配的投诉记录")
            print(f"\n所有投诉对象都没有找到匹配记录:")
            for i, company in enumerate(sorted(company_names), 1):
                code = company_code_mapping.get(company, '无')
                compn = company_compn_mapping.get(company, '无')
                print(f"  {i}. {company} (商家编码: {code}, compn: {compn})")
            return None, 0, 0
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        return None, 0, 0

def main():
    """
    主函数
    """
    # 文件路径配置
    csv_folder = "/Users/chenyaxin/Desktop/InternetTourismConvention/原始数据处理"
    company_list_file = "/Users/chenyaxin/Desktop/信息规范/持牌金融机构统计.xlsx"
    output_file = "/Users/chenyaxin/Desktop/投诉内容汇总.csv"
    
    print("开始提取投诉内容...")
    print(f"CSV文件夹: {csv_folder}")
    print(f"投诉对象列表文件: {company_list_file}")
    print(f"输出文件: {output_file}")
    print("-" * 50)
    
    # 执行提取
    result_df, covered_companies, total_complaints = extract_complaints_by_company(
        csv_folder=csv_folder,
        company_list_file=company_list_file,
        output_file=output_file,
        company_column='投诉对象',
        content_column='发起投诉内容'
    )
    
    if result_df is not None:
        # 显示前10个投诉对象及其记录数量
        complaint_counts = result_df['匹配的投诉对象'].value_counts()
        print(f"\n投诉最多的前10个投诉对象:")
        for company, count in complaint_counts.head(10).items():
            code = result_df[result_df['匹配的投诉对象'] == company]['商家编码'].iloc[0]
            compn = result_df[result_df['匹配的投诉对象'] == company]['compn'].iloc[0]
            print(f"  {company} (商家编码: {code}, compn: {compn}): {count} 条投诉")
        
        # 显示统计摘要
        print(f"\n=== 统计摘要 ===")
        print(f"覆盖投诉对象数量: {covered_companies}")
        print(f"总投诉记录数: {total_complaints}")
        
        # 商家编码统计
        valid_codes = result_df['商家编码'].notna() & (result_df['商家编码'].astype(str).str.strip() != '')
        valid_code_count = valid_codes.sum()
        print(f"包含商家编码的记录数: {valid_code_count} ({valid_code_count/total_complaints*100:.2f}%)")
        
        # compn统计
        valid_compn = result_df['compn'].notna() & (result_df['compn'].astype(str).str.strip() != '')
        valid_compn_count = valid_compn.sum()
        print(f"包含compn的记录数: {valid_compn_count} ({valid_compn_count/total_complaints*100:.2f}%)")

if __name__ == "__main__":
    main()