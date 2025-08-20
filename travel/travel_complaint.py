import os
import pandas as pd
from glob import glob

# 配置路径
excel_path = "/Users/chenyaxin/Desktop/InternetTourismConvention/旅游商家.xlsx"  # 替换为你的Excel文件路径
csv_folder = "/Volumes/yaxindedisk 1/黑猫数据库/黑猫原始网页数据备份/merge_data2"           # 替换为CSV文件夹路径
output_file = "./travel_complaint_results.csv"        # 输出结果文件名

# 1. 读取Excel文件中的投诉对象列
excel_data = pd.read_excel(excel_path)
target_complaints = excel_data["投诉对象"].unique().tolist()  # 获取唯一值列表
print(f"从Excel中获取到 {len(target_complaints)} 个需要匹配的投诉对象")

# 2. 初始化结果列表
results = []
processed_files = 0
matched_records = 0

# 3. 遍历文件夹中的所有CSV文件
for csv_file in glob(os.path.join(csv_folder, "*.csv")):
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_file)
        
        # 检查必要列是否存在
        required_columns = ["投诉对象", "发布时间", "投诉编号", "发起投诉内容"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            print(f"警告: 文件 {os.path.basename(csv_file)} 缺少列: {', '.join(missing_cols)}")
            continue
        
        # 过滤出目标投诉对象
        filtered = df[df["投诉对象"].isin(target_complaints)]
        
        if not filtered.empty:
            # 提取所需列
            result_subset = filtered[["投诉对象", "发布时间", "投诉编号", "发起投诉内容"]].copy()
            
            # 添加到结果列表
            results.append(result_subset)
            matched_records += len(result_subset)
            print(f"文件 {os.path.basename(csv_file)} 中找到 {len(result_subset)} 条匹配记录")
        
        processed_files += 1
        
    except Exception as e:
        print(f"处理文件 {os.path.basename(csv_file)} 时出错: {str(e)}")
        continue

# 4. 合并结果并保存
if results:
    # 合并所有结果
    final_df = pd.concat(results, ignore_index=True)
    
    # 按投诉对象和发布时间排序
    final_df.sort_values(by=["投诉对象", "发布时间"], inplace=True)
    
    # 保存到CSV
    final_df.to_csv(output_file, index=False, encoding="utf_8_sig")  # 使用中文兼容编码
    
    print(f"\n处理完成: 共扫描 {processed_files} 个CSV文件")
    print(f"找到 {matched_records} 条匹配记录")
    print(f"结果已保存到: {output_file}")
    
    # 显示结果预览
    print("\n结果预览:")
    print(final_df.head(3))
else:
    print("未找到匹配的投诉记录")