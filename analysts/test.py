import pandas as pd
import numpy as np
from datetime import datetime

def process_analyst_data():
    """
    处理分析师数据的完整流程
    """
    # 1. 读取分析师数据
    analyst_df = pd.read_excel('/Users/chenyaxin/Desktop/analysts/数据/筛选分析师名单/分析师.xlsx', header=1)
    print(f"原始数据共{len(analyst_df)}条记录")
    
    # 2. 读取证券业协会统计情况，剔除不在名单上的券商
    sac_df = pd.read_excel('/Users/chenyaxin/Desktop/analysts/数据/筛选分析师名单/证券业协会统计情况.xlsx')
    
    # 获取协会会员的机构名称列表
    sac_institutions = sac_df['机构名称'].unique().tolist()
    print(f"证券业协会共有{len(sac_institutions)}家机构")
    
    # 筛选出在协会名单上的券商
    before_broker_filter = len(analyst_df)
    analyst_df = analyst_df[analyst_df['券商名称'].isin(sac_institutions)]
    after_broker_filter = len(analyst_df)
    
    print(f"删除不在证券业协会名单上的券商后，删除了 {before_broker_filter - after_broker_filter} 条记录")
    print(f"剩余 {after_broker_filter} 条记录")
    
    # 3. 删除2020年之后没有发布过报告的分析师
    analyst_df['报告日期'] = pd.to_datetime(analyst_df['报告日期'])
    
    # 找出每个分析师最新的报告日期
    latest_reports = analyst_df.groupby('分析师代码')['报告日期'].max().reset_index()
    
    # 筛选出2020年后没有发布过报告的分析师
    cutoff_date = pd.Timestamp('2020-01-01')
    analysts_no_report_after_2020 = latest_reports[
        latest_reports['报告日期'] < cutoff_date
    ]['分析师代码']
    
    # 获取筛选后的数据
    filtered_df = analyst_df[~analyst_df['分析师代码'].isin(analysts_no_report_after_2020)]
    print(f"删除了 {len(analysts_no_report_after_2020)} 个在2020年后没有发布过报告的分析师")
    print(f"剩余 {len(filtered_df)} 条记录")
    
    # 4. 计算每个分析师的首次报告日期
    first_report_dates = filtered_df.groupby('分析师代码')['报告日期'].min().reset_index()
    first_report_dates.rename(columns={'报告日期': '首次报告日期'}, inplace=True)
    
    # 5. 根据分析师ID和券商代码删除重复值
    # 保留每个分析师在每个券商的唯一记录
    before_dedup = len(filtered_df)
    dedup_df = filtered_df.drop_duplicates(subset=['分析师代码', '券商代码'], keep='first')
    after_dedup = len(dedup_df)
    
    print(f"删除重复值后，删除了 {before_dedup - after_dedup} 条记录")
    print(f"剩余 {after_dedup} 条记录")
    
    # 6. 将首次报告日期合并到主数据框
    dedup_df = pd.merge(dedup_df, first_report_dates, on='分析师代码', how='left')
    
    # 7. 按时间顺序整理每个分析师的券商经历
    # 按分析师ID分组，并按报告日期排序
    dedup_df = dedup_df.sort_values(['分析师代码', '报告日期'])
    
    # 保存排序后的数据
    sorted_output_path = '/Users/chenyaxin/Desktop/analysts/数据/排序后的分析师数据.xlsx'
    dedup_df.to_excel(sorted_output_path, index=False)
    print(f"排序后的数据已保存到: {sorted_output_path}")
    
    # 统计分析师数量
    analyst_count = dedup_df['分析师代码'].nunique()
    print(f"共有 {analyst_count} 名分析师")
    
    # 8. 读取已有分析师信息，添加标记列而不是删除
    existing_analysts_df = pd.read_excel('/Users/chenyaxin/Desktop/analysts/数据/analy_experi/基本信息.xlsx', header=1)
    
    # 获取已有分析师的代码列表
    existing_analyst_codes = existing_analysts_df['分析师代码'].unique()
    
    # 添加标记列：如果分析师已有数据，则标记为1，否则为0
    dedup_df['已有数据'] = dedup_df['分析师代码'].isin(existing_analyst_codes).astype(int)
    
    # 统计已有数据和需要处理的数据
    existing_count = dedup_df['已有数据'].sum()
    need_process_count = len(dedup_df) - existing_count
    
    print(f"已有数据记录: {existing_count} 条")
    print(f"需要处理记录: {need_process_count} 条")
    
    # 输出最终统计信息
    final_analyst_count = dedup_df['分析师代码'].nunique()
    print(f"最终分析师数量: {final_analyst_count}")
    
    # 保存完整结果到文件（包含标记列和首次报告日期）
    output_path = '/Users/chenyaxin/Desktop/analysts/数据/完整分析师名单_含标记.xlsx'
    dedup_df.to_excel(output_path, index=False)
    print(f"完整结果已保存到: {output_path}")
    
    # 同时保存一份只需要处理的数据
    need_process_df = dedup_df[dedup_df['已有数据'] == 0]
    need_process_path = '/Users/chenyaxin/Desktop/analysts/数据/需要处理的分析师名单.xlsx'
    need_process_df.to_excel(need_process_path, index=False)
    print(f"需要处理的数据已保存到: {need_process_path}")
    
    return dedup_df, need_process_df

# 执行处理函数
if __name__ == "__main__":
    full_data, need_process_data = process_analyst_data()
    
    # 显示处理后的数据前几行
    print("\n完整数据预览（包含标记列和首次报告日期）:")
    print(full_data.head())
    
    print("\n需要处理的数据预览:")
    print(need_process_data.head())