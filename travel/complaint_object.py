import pandas as pd
import os
from tqdm import tqdm
import time

# 记录开始时间
start_time = time.time()

# 读取对照组.xlsx文件
对照组_file = '/Users/chenyaxin/Desktop/InternetTourismConvention/对照组企业处理.xlsx'
对照组_df = pd.read_excel(对照组_file)
print(f"读取对照组文件完成，共 {len(对照组_df)} 条记录")

# 筛选旅游类商家（"是否为旅游类"列等于1）
旅游类_df = 对照组_df[对照组_df['是否为旅游类'] == 1]
print(f"找到 {len(旅游类_df)} 个旅游类商家需要处理")

# 获取文件夹中的文件列表
folder_path = '/Volumes/yaxindedisk 1/黑猫数据库/黑猫原始网页数据备份/merge_data2'
# 只获取CSV文件，并过滤掉隐藏文件（以点开头的文件）
files = [f for f in os.listdir(folder_path) 
         if f.endswith('.csv') and not f.startswith('.')]
print(f"在文件夹中找到 {len(files)} 个CSV文件（已过滤隐藏文件）")

# 步骤1: 构建所有CSV文件中投诉对象的集合
print("开始构建投诉对象集合...")
all_complaint_objects = set()  # 使用集合自动去重

# 创建进度条
pbar_files = tqdm(total=len(files), desc="读取CSV文件")
for file in files:
    file_path = os.path.join(folder_path, file)
    try:
        # 读取CSV文件，只读取投诉对象列
        file_df = pd.read_csv(file_path, usecols=['投诉对象'])
        
        # 检查是否有"投诉对象"列
        if '投诉对象' in file_df.columns:
            # 去重并添加到集合
            unique_objects = file_df['投诉对象'].dropna().unique()
            all_complaint_objects.update(unique_objects)
            
    except KeyError:
        # 如果文件没有"投诉对象"列，跳过
        pass
    except Exception as e:
        print(f"\n读取文件 {file} 时出错：{str(e)}")
    
    pbar_files.update(1)

pbar_files.close()
print(f"构建完成！共收集 {len(all_complaint_objects)} 个唯一投诉对象名称")

# 步骤2: 处理旅游类商家
print("开始匹配商家名称...")
pbar_companies = tqdm(total=len(旅游类_df), desc="匹配商家名称")

for index, row in 旅游类_df.iterrows():
    商家名称 = row['投诉商家']
    原始投诉对象 = row.get('投诉对象', '')  # 获取原始投诉对象值
    
    # 如果原始投诉对象已经有值且不是"未找到"，则跳过
    if pd.notna(原始投诉对象) and 原始投诉对象 != '未找到' and 原始投诉对象 != '':
        pbar_companies.update(1)
        continue
    
    # 检查商家名称是否在集合中
    if 商家名称 in all_complaint_objects:
        对照组_df.loc[index, '投诉对象'] = 商家名称
    else:
        对照组_df.loc[index, '投诉对象'] = '未找到'
    
    pbar_companies.update(1)

pbar_companies.close()

# 保存更新后的对照组.xlsx文件
output_file = '/Users/chenyaxin/Desktop/InternetTourismConvention/更新后的对照组.xlsx'
对照组_df.to_excel(output_file, index=False)

# 计算耗时
end_time = time.time()
elapsed_time = end_time - start_time
minutes = int(elapsed_time // 60)
seconds = int(elapsed_time % 60)

print(f"\n处理完成！耗时: {minutes}分{seconds}秒")
print(f"结果已保存到: {output_file}")
print(f"总商家数: {len(对照组_df)}, 旅游类商家数: {len(旅游类_df)}")
print(f"匹配成功的商家数: {len(旅游类_df[对照组_df['投诉对象'] != '未找到'])}")