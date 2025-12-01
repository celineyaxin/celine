import pandas as pd
from datetime import datetime
import os

def generate_simple_monthly_report(csv_file, output_excel=None, date_column='发布时间'):
    """
    按月份统计投诉数量并生成简化的Excel报告
    
    参数:
    csv_file: CSV文件路径
    output_excel: 输出的Excel文件路径（可选）
    date_column: 时间列的列名，默认为'时间'
    """
    try:
        # 读取CSV文件
        print(f"正在读取文件: {csv_file}")
        df = pd.read_csv(csv_file)
        print(f"成功读取 {len(df)} 行数据")
        
        # 转换时间列
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # 过滤无效日期
        df = df.dropna(subset=[date_column])
        
        # 按月统计投诉数量
        monthly_stats = df.groupby(df[date_column].dt.to_period('M')).size().reset_index()
        monthly_stats.columns = ['年月', '投诉数量']
        
        # 按时间排序
        monthly_stats = monthly_stats.sort_values('年月')

        os.makedirs(output_folder, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(csv_file))[0]
        output_excel = os.path.join(output_folder, f"{base_name}_月度投诉统计.xlsx")
     
        
        # 生成Excel文件
        monthly_stats.to_excel(output_excel, index=False)
        
        # 输出结果
        print(f"\n统计完成! 共统计 {len(monthly_stats)} 个月份的数据")
        print(f"Excel文件已生成: {output_excel}")
        
        # 显示前几行数据预览
        print("\n数据预览:")
        print(monthly_stats.head())
        
        return monthly_stats
        
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 替换为您的CSV文件路径
    csv_file = "/Users/chenyaxin/Desktop/websitdata/bert/results/是否明示/merged_data.csv"  # 您的CSV文件
    output_folder = "/Users/chenyaxin/Desktop/审稿修改/画图"
    generate_simple_monthly_report(csv_file)