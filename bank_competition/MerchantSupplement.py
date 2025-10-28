import pandas as pd
import os
import glob

def find_new_financial_institutions(csv_folder, licensed_file, output_file, company_column='投诉对象'):
    """
    通过关键词搜索新的金融机构投诉对象
    
    参数:
    csv_folder: CSV文件所在文件夹路径
    licensed_file: 持牌金融机构文件路径
    output_file: 输出文件路径
    company_column: 投诉对象列名
    """
    
    try:
        # 定义金融机构关键词
        # 专注于金融监管总局监管的金融机构关键词
        keywords = [
            # 银行业
            '银行', '信托', '金融资产管理',
            
            # 保险业
            '保险', '人寿', '财险', '再保险', '养老险', '健康险',
            
            # 其他金融机构
            '金融租赁', '消费金融', '汽车金融', '货币经纪', '财务公司'
            ]
        
        # 读取持牌金融机构列表
        print("正在读取持牌金融机构列表...")
        licensed_df = pd.read_excel(licensed_file)
        licensed_companies = set(licensed_df['投诉对象'].dropna().astype(str).str.strip())
        print(f"已加载 {len(licensed_companies)} 个持牌金融机构")
        
        # 获取所有CSV文件
        csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))
        print(f"扫描 {len(csv_files)} 个CSV文件...")
        
        # 收集所有包含关键词但不在持牌列表中的投诉对象
        new_financial_companies = {}
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                if company_column not in df.columns:
                    continue
                
                # 清理数据
                df[company_column] = df[company_column].fillna('').astype(str).str.strip()
                
                # 对每个关键词进行搜索
                for keyword in keywords:
                    # 查找包含关键词的投诉对象
                    mask = df[company_column].str.contains(keyword, case=False, na=False)
                    keyword_companies = df.loc[mask, company_column]
                    
                    # 统计频率并排除已持牌机构
                    for company in keyword_companies:
                        if company not in licensed_companies:
                            if company not in new_financial_companies:
                                new_financial_companies[company] = 0
                            new_financial_companies[company] += 1
                
                print(f"  处理文件: {os.path.basename(csv_file)}")
                
            except Exception as e:
                print(f"  处理文件 {csv_file} 时出错: {str(e)}")
                continue
        
        # 将结果转换为DataFrame
        if new_financial_companies:
            result_data = []
            for company, count in new_financial_companies.items():
                # 确定所属类别
                category = "其他"
                for keyword in keywords:
                    if keyword in company:
                        category = keyword
                        break
                
                result_data.append({
                    '投诉对象': company,
                    '出现次数': count,
                    '类别': category
                })
            
            # 创建结果DataFrame
            result_df = pd.DataFrame(result_data)
            
            # 按出现次数降序排列
            result_df = result_df.sort_values('出现次数', ascending=False)
            
            # 保存到Excel
            result_df.to_excel(output_file, index=False)
            
            # 统计信息
            total_new_companies = len(result_df)
            total_complaints = result_df['出现次数'].sum()
            
            # 按类别统计
            category_counts = result_df['类别'].value_counts()
            
            print(f"\n发现完成!")
            print(f"总共发现 {total_new_companies} 个新的金融机构投诉对象")
            print(f"总投诉记录数: {total_complaints}")
            
            print(f"\n按类别分布:")
            for category, count in category_counts.items():
                category_complaints = result_df[result_df['类别'] == category]['出现次数'].sum()
                print(f"  {category}: {count} 个机构, {category_complaints} 条投诉")
            
            print(f"\n前10个最频繁的新金融机构投诉对象:")
            for idx, row in result_df.head(10).iterrows():
                print(f"  {row['投诉对象']} (出现次数: {row['出现次数']})")
            
            print(f"\n结果已保存到: {output_file}")
            
            return result_df
        else:
            print("没有发现新的金融机构投诉对象")
            return None
            
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        return None

def main():
    """
    主函数
    """
    # 文件路径配置
    csv_folder = "/Users/chenyaxin/Desktop/InternetTourismConvention/原始数据处理"
    licensed_file = "/Users/chenyaxin/Desktop/信息规范/持牌金融机构统计.xlsx"
    output_file = "/Users/chenyaxin/Desktop/新发现金融机构投诉对象.xlsx"
    
    print("开始搜索新的金融机构投诉对象...")
    print(f"CSV文件夹: {csv_folder}")
    print(f"持牌机构文件: {licensed_file}")
    print(f"输出文件: {output_file}")
    print("-" * 50)
    
    # 执行搜索
    result_df = find_new_financial_institutions(
        csv_folder=csv_folder,
        licensed_file=licensed_file,
        output_file=output_file,
        company_column='投诉对象'
    )

if __name__ == "__main__":
    main()