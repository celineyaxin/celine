import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

# 设置中文字体显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

def count_licensed_companies(licensed_file, licensed_company_column='compn'):
    """
    统计持牌金融机构总数
    
    参数:
    licensed_file: 持牌金融机构统计文件路径
    licensed_company_column: 持牌金融机构文件中公司名列名
    
    返回:
    持牌金融机构总数
    """
    try:
        print("正在读取持牌金融机构数据...")
        licensed_df = pd.read_excel(licensed_file)
        
        if licensed_company_column not in licensed_df.columns:
            raise ValueError(f"列 '{licensed_company_column}' 不存在")
        
        # 统计唯一持牌金融机构数量
        total_licensed_companies = licensed_df[licensed_company_column].nunique()
        
        print(f"持牌金融机构统计文件中总共有 {total_licensed_companies} 个唯一持牌金融机构")
        
        # 显示前几个机构名称作为示例
        print("部分持牌金融机构示例:")
        for i, company in enumerate(licensed_df[licensed_company_column].dropna().unique()[:10]):
            print(f"  {i+1}. {company}")
        if total_licensed_companies > 10:
            print(f"  ... 还有 {total_licensed_companies - 10} 个机构")
            
        return total_licensed_companies
        
    except Exception as e:
        print(f"统计持牌金融机构时出现错误: {str(e)}")
        return None

def analyze_complaint_trends(complaint_file, licensed_file, date_column='发布时间', company_column='投诉对象', licensed_company_column='compn'):
    """
    分析投诉数据的时间趋势和商家覆盖情况
    
    参数:
    complaint_file: 投诉数据文件路径
    licensed_file: 持牌金融机构统计文件路径
    date_column: 发布时间列名
    company_column: 投诉对象列名
    licensed_company_column: 持牌金融机构文件中公司名列名
    """
    
    try:
        # 先统计持牌金融机构总数
        total_licensed_companies = count_licensed_companies(licensed_file, licensed_company_column)
        if total_licensed_companies is None:
            return None
            
        print("-" * 50)
        
        # 读取投诉数据
        print("正在读取投诉数据...")
        df = pd.read_csv(complaint_file)
        
        # 检查必要的列是否存在
        if date_column not in df.columns:
            raise ValueError(f"列 '{date_column}' 不存在")
        if company_column not in df.columns:
            raise ValueError(f"列 '{company_column}' 不存在")
        
        print(f"投诉数据总行数: {len(df)}")
        
        # 转换发布时间为datetime格式
        print("正在转换时间格式...")
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # 删除时间转换失败的行
        original_count = len(df)
        df = df.dropna(subset=[date_column])
        print(f"有效时间记录: {len(df)} / {original_count}")
        
        # 读取持牌金融机构数据
        licensed_df = pd.read_excel(licensed_file)
        licensed_companies = licensed_df[licensed_company_column].dropna().unique()
        
        # 提取时间维度
        df['年份'] = df[date_column].dt.year
        df['月份'] = df[date_column].dt.month
        df['季度'] = df[date_column].dt.quarter
        df['年月'] = df[date_column].dt.to_period('M')
        
        # 1. 按年份统计投诉数量
        yearly_counts = df['年份'].value_counts().sort_index()
        
        # 2. 按年份统计唯一持牌金融机构数量
        yearly_companies = {}
        for year in yearly_counts.index:
            year_companies = df[df['年份'] == year][company_column].unique()
            # 只统计持牌金融机构
            licensed_year_companies = [company for company in year_companies if company in licensed_companies]
            yearly_companies[year] = len(licensed_year_companies)
        
        yearly_companies = pd.Series(yearly_companies)
        
        # 3. 按季度统计
        quarterly_counts = df.groupby(['年份', '季度']).size().reset_index(name='投诉数量')
        quarterly_counts['年份季度'] = quarterly_counts['年份'].astype(str) + 'Q' + quarterly_counts['季度'].astype(str)
        
        # 4. 按月统计
        monthly_counts = df['年月'].value_counts().sort_index()
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('持牌金融机构投诉数据时间趋势分析', fontsize=16, fontweight='bold')
        
        # 1. 年度投诉趋势和商家覆盖
        x = np.arange(len(yearly_counts.index))
        width = 0.35
        
        bars1 = axes[0, 0].bar(x - width/2, yearly_counts.values, width, label='投诉数量', color='skyblue', alpha=0.7)
        bars2 = axes[0, 0].bar(x + width/2, yearly_companies.values, width, label='唯一商家数量', color='lightcoral', alpha=0.7)
        
        axes[0, 0].set_title('年度投诉趋势与商家覆盖')
        axes[0, 0].set_xlabel('年份')
        axes[0, 0].set_ylabel('数量')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(yearly_counts.index)
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 在柱状图上添加数值标签
        for bar in bars1:
            height = bar.get_height()
            axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + max(yearly_counts.values)*0.01,
                           f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        for bar in bars2:
            height = bar.get_height()
            axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + max(yearly_companies.values)*0.01,
                           f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        # 2. 季度投诉趋势
        quarter_labels = quarterly_counts['年份季度'].tolist()
        axes[0, 1].plot(quarter_labels, quarterly_counts['投诉数量'], marker='o', linewidth=2, markersize=6)
        axes[0, 1].set_title('季度投诉趋势')
        axes[0, 1].set_xlabel('季度')
        axes[0, 1].set_ylabel('投诉数量')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. 月度趋势图（显示最近24个月）
        recent_monthly = monthly_counts.tail(24)
        axes[1, 0].plot(recent_monthly.index.astype(str), recent_monthly.values, 
                       marker='s', linewidth=2, markersize=4, color='green')
        axes[1, 0].set_title('近24个月投诉趋势')
        axes[1, 0].set_xlabel('年月')
        axes[1, 0].set_ylabel('投诉数量')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 4. 季节性分析（按月份聚合所有年份）
        monthly_avg = df.groupby('月份').size()
        months = ['1月', '2月', '3月', '4月', '5月', '6月', 
                 '7月', '8月', '9月', '10月', '11月', '12月']
        axes[1, 1].bar(months, monthly_avg.values, color='orange', alpha=0.7)
        axes[1, 1].set_title('月度季节性分析（所有年份）')
        axes[1, 1].set_xlabel('月份')
        axes[1, 1].set_ylabel('平均投诉数量')
        axes[1, 1].grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 只显示图表，不保存
        plt.show()
        
        # 计算投诉数据中涉及的持牌金融机构数量
        all_complaint_companies = df[company_column].unique()
        covered_licensed_companies = len([company for company in all_complaint_companies if company in licensed_companies])
        
        # 输出统计摘要
        print("\n=== 投诉数据分析摘要 ===")
        print(f"数据时间范围: {df[date_column].min()} 到 {df[date_column].max()}")
        print(f"总投诉记录: {len(df)}")
        print(f"总持牌金融机构数量: {total_licensed_companies}")
        print(f"投诉数据中涉及的持牌金融机构数量: {covered_licensed_companies}")
        print(f"覆盖率: {covered_licensed_companies/total_licensed_companies*100:.2f}%")
        print(f"覆盖年份: {len(yearly_counts)} 年")
        print(f"覆盖月份: {len(monthly_counts)} 个月")
        
        print("\n年度统计:")
        for year in yearly_counts.index:
            year_complaints = yearly_counts[year]
            year_companies = yearly_companies[year]
            print(f"  {year}年: {year_complaints} 条投诉, {year_companies} 个唯一持牌金融机构")
        
        # 计算平均每个商家的投诉数量
        print(f"\n平均每个持牌金融机构的投诉数量: {len(df) / covered_licensed_companies:.2f}")
        
        return {
            'yearly': yearly_counts,
            'yearly_companies': yearly_companies,
            'quarterly': quarterly_counts,
            'monthly': monthly_counts,
            'total_licensed_companies': total_licensed_companies,
            'covered_licensed_companies': covered_licensed_companies
        }
        
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        return None

def main():
    """
    主函数
    """
    # 文件路径配置
    complaint_file = "/Users/chenyaxin/Desktop/投诉内容汇总.csv"  # 替换为您的投诉数据文件路径
    licensed_file = "/Users/chenyaxin/Desktop/信息规范/持牌金融机构统计.xlsx"  # 替换为您的持牌金融机构统计文件路径
    
    print("开始分析持牌金融机构投诉数据时间趋势...")
    print(f"投诉数据文件: {complaint_file}")
    print(f"持牌金融机构文件: {licensed_file}")
    print("=" * 50)
    
    # 执行分析
    results = analyze_complaint_trends(
        complaint_file=complaint_file,
        licensed_file=licensed_file,
        date_column='发布时间',
        company_column='投诉对象',
        licensed_company_column='compn'
    )
    
    if results is not None:
        print("\n分析完成!")

if __name__ == "__main__":
    main()