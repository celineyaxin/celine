import pandas as pd

def extract_2019_penalty_records():
    """
    提取2019年的完整行政处罚记录和企业统计
    """
    try:
        # 文件路径
        penalty_file = "/Users/chenyaxin/Desktop/信息规范/行政处罚/行政处罚记录_最终结果.xlsx"
        
        print("开始提取2019年行政处罚记录...")
        
        # 1. 读取行政处罚记录文件
        df = pd.read_excel(penalty_file)
        print(f"总记录数量: {len(df)}")
        
        # 2. 检查数据列
        print(f"文件包含的列: {list(df.columns)}")
        
        # 3. 提取2019年记录
        if '处罚年' in df.columns:
            # 提取2019年记录
            df_2019 = df[df['处罚年'] == 2019].copy()
            
            print(f"\n2019年行政处罚记录提取结果:")
            print(f"2019年记录数量: {len(df_2019)}")
            print(f"占总记录比例: {len(df_2019)/len(df)*100:.2f}%")
            
            # 4. 保存完整的2019年处罚记录
            penalty_output_file = "/Users/chenyaxin/Desktop/2019年完整行政处罚记录.xlsx"
            df_2019.to_excel(penalty_output_file, index=False)
            print(f"\n完整2019年行政处罚记录已保存到: {penalty_output_file}")
            
            # 5. 创建企业统计列表（企业名称 + 处罚次数）
            if '模型生成全称' in df_2019.columns:
                # 按企业统计处罚次数
                company_stats = df_2019['模型生成全称'].value_counts().reset_index()
                company_stats.columns = ['企业全称', '处罚次数']
                
                # 按处罚次数降序排列
                company_stats = company_stats.sort_values('处罚次数', ascending=False)
                
                # 保存企业统计列表
                company_output_file = "/Users/chenyaxin/Desktop/2019年处罚企业统计.xlsx"
                company_stats.to_excel(company_output_file, index=False)
                
                print(f"企业统计列表已保存到: {company_output_file}")
                print(f"涉及企业总数: {len(company_stats)}")
                
                # 显示处罚次数最多的前20家企业
                print(f"\n处罚次数最多的前20家企业:")
                for i, row in company_stats.head(20).iterrows():
                    print(f"  {i+1}. {row['企业全称']}: {row['处罚次数']}次")
                
                # 统计处罚次数的分布
                print(f"\n处罚次数分布:")
                penalty_count_dist = company_stats['处罚次数'].value_counts().sort_index()
                for count, freq in penalty_count_dist.items():
                    print(f"  处罚{count}次的企业: {freq}家")
                
                return {
                    'total_records': len(df),
                    '2019_records': len(df_2019),
                    'company_count': len(company_stats),
                    'penalty_records_file': penalty_output_file,
                    'company_stats_file': company_output_file,
                    'company_stats': company_stats
                }
            else:
                print("错误: 文件中没有'模型生成全称'列")
                return None
        else:
            print("错误: 文件中没有'处罚年'列")
            return None
            
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    主函数
    """
    # 提取2019年记录
    result = extract_2019_penalty_records()
    
    if result:
        print(f"\n" + "="*60)
        print("提取完成!")
        print("="*60)
        print(f"总记录数量: {result['total_records']}")
        print(f"2019年记录数量: {result['2019_records']}")
        print(f"涉及企业数量: {result['company_count']}")
        print(f"\n生成的文件:")
        print(f"  完整处罚记录: {result['penalty_records_file']}")
        print(f"  企业统计列表: {result['company_stats_file']}")

if __name__ == "__main__":
    main()