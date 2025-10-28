import pandas as pd

def extract_penalty_records_by_quarter(file_path, start_year=2020, end_year=2024, end_quarter=1):
    """
    从Excel文件中提取指定时间范围内的行政处罚记录（到2024年Q1为止）
    
    参数:
    file_path: Excel文件路径
    start_year: 起始年份
    end_year: 结束年份
    end_quarter: 结束季度（默认1，即Q1）
    
    返回:
    DataFrame: 包含指定时间范围行政处罚记录的DataFrame
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 检查是否存在必要的列
        required_columns = ['处罚年']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"错误：文件中没有找到以下列: {missing_columns}")
            print("可用的列有：", df.columns.tolist())
            return None
        
        # 将'处罚年'列转换为数值类型，处理可能的异常
        df['处罚年'] = pd.to_numeric(df['处罚年'], errors='coerce')
        
        # 如果有处罚月列，处理处罚月
        if '处罚月' in df.columns:
            df['处罚月'] = pd.to_numeric(df['处罚月'], errors='coerce')
            # 根据处罚月计算季度
            df['处罚季度'] = ((df['处罚月'] - 1) // 3 + 1).astype('Int64')
        
        # 构建筛选条件
        # 2020-2023年的所有数据
        condition_2020_2023 = (df['处罚年'] >= start_year) & (df['处罚年'] <= end_year - 1)
        
        # 2024年只保留Q1数据
        if '处罚季度' in df.columns:
            condition_2024_q1 = (df['处罚年'] == end_year) & (df['处罚季度'] <= end_quarter)
            # 组合条件
            filtered_df = df[condition_2020_2023 | condition_2024_q1]
        else:
            # 如果没有季度信息，保守处理：只取2024年且处罚月<=3的数据
            if '处罚月' in df.columns:
                condition_2024_q1 = (df['处罚年'] == end_year) & (df['处罚月'] <= 3)
                filtered_df = df[condition_2020_2023 | condition_2024_q1]
            else:
                # 如果连月份信息都没有，只能取到2023年
                print("警告：没有找到'处罚月'列，只能提取到2023年数据")
                filtered_df = df[df['处罚年'] <= end_year - 1]
        
        # 按年份和月份排序
        sort_columns = ['处罚年']
        if '处罚月' in df.columns:
            sort_columns.append('处罚月')
        filtered_df = filtered_df.sort_values(sort_columns)
        
        # 输出统计信息
        print(f"成功提取 {len(filtered_df)} 条 {start_year}年-{end_year}年Q{end_quarter} 的行政处罚记录")
        print(f"各年份记录数量：")
        year_counts = filtered_df['处罚年'].value_counts().sort_index()
        for year, count in year_counts.items():
            if '处罚季度' in filtered_df.columns and year == end_year:
                quarter_counts = filtered_df[filtered_df['处罚年'] == year]['处罚季度'].value_counts()
                quarter_info = "，".join([f"Q{q}: {c}条" for q, c in quarter_counts.items()])
                print(f"  {int(year)}年: {count}条 ({quarter_info})")
            else:
                print(f"  {int(year)}年: {count}条")
        
        return filtered_df
        
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return None
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 文件路径
    file_path = "/Users/chenyaxin/Desktop/信息规范/行政处罚/行政处罚记录_最终结果.xlsx"
    
    # 提取2020-2024Q1的记录
    result_df = extract_penalty_records_by_quarter(file_path, 2020, 2024, 1)
    
    # 如果成功提取数据，可以进一步处理或保存
    if result_df is not None and len(result_df) > 0:
        # 显示前几行数据
        print("\n前5条记录：")
        print(result_df[['处罚年', '处罚月', '处罚季度'] if '处罚季度' in result_df.columns else ['处罚年']].head())
        
        # 可以选择保存到新的Excel文件
        output_file = "/Users/chenyaxin/Desktop/2020-2024Q1行政处罚记录.xlsx"
        result_df.to_excel(output_file, index=False)
        print(f"\n结果已保存到: {output_file}")
        
        # 显示统计信息
        print(f"\n数据统计：")
        print(f"总记录数: {len(result_df)}")
        print(f"时间范围: {int(result_df['处罚年'].min())}年-{int(result_df['处罚年'].max())}年")
        
        # 如果有季度信息，显示季度分布
        if '处罚季度' in result_df.columns:
            print("季度分布:")
            quarter_stats = result_df.groupby(['处罚年', '处罚季度']).size().reset_index(name='数量')
            print(quarter_stats)