import pandas as pd
import os
from tqdm import tqdm
import time

# 获取文件夹中的文件列表
folder_path = '/Volumes/yaxindedisk 1/黑猫数据库/黑猫原始网页数据备份/merge_data2'
print(f"开始处理文件夹: {folder_path}")

# 只获取CSV文件，并过滤掉隐藏文件（以点开头的文件）
files = [f for f in os.listdir(folder_path) 
         if f.endswith('.csv') and not f.startswith('.')]
print(f"在文件夹中找到 {len(files)} 个CSV文件（已过滤隐藏文件）")

# 记录开始时间
start_time = time.time()

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

# 计算耗时
end_time = time.time()
elapsed_time = end_time - start_time
minutes = int(elapsed_time // 60)
seconds = int(elapsed_time % 60)

print(f"构建完成！耗时: {minutes}分{seconds}秒")
print(f"共收集 {len(all_complaint_objects)} 个唯一投诉对象名称")

# 关键词搜索功能
def search_complaint_objects(keyword, max_results=100):
    """搜索包含关键词的投诉对象"""
    # 将集合转换为列表并排序，使结果更有序
    sorted_objects = sorted(all_complaint_objects, key=lambda x: str(x))
    
    # 搜索包含关键词的对象
    results = [obj for obj in sorted_objects if keyword in str(obj)]
    return results

# 交互式搜索界面
print("\n" + "="*50)
print("关键词搜索功能已启用")
print("输入关键词搜索投诉对象（输入'exit'退出）")
print("="*50)

while True:
    keyword = input("\n请输入关键词: ").strip()
    
    if keyword.lower() in ['exit', 'quit', '退出']:
        print("退出搜索功能")
        break
    
    if not keyword:
        print("请输入有效的关键词")
        continue
    
    print(f"正在搜索包含 '{keyword}' 的投诉对象...")
    start_search = time.time()
    
    # 执行搜索
    results = search_complaint_objects(keyword)
    
    end_search = time.time()
    search_time = end_search - start_search
    
    # 显示搜索结果
    if not results:
        print(f"未找到包含 '{keyword}' 的投诉对象")
    else:
        print(f"\n找到 {len(results)} 个包含 '{keyword}' 的投诉对象 (搜索耗时: {search_time:.4f}秒)")
        print("-"*60)
        
        # 显示前max_results个结果
        max_display = 100
        for i, obj in enumerate(results[:max_display], 1):
            print(f"{i}. {obj}")
        
        if len(results) > max_display:
            print(f"\n...显示前 {max_display} 个结果，共 {len(results)} 个")
        
        # 提供导出选项
        export = input("\n是否导出完整结果到CSV文件? (y/n): ").strip().lower()
        if export == 'y':
            export_file = f"投诉对象搜索_{keyword}.csv"
            export_df = pd.DataFrame(results, columns=['投诉对象'])
            export_df.to_csv(export_file, index=False, encoding='utf-8-sig')
            print(f"已导出完整结果到: {export_file}")
    
    print("-"*60)
    print(f"搜索完成！")

print("程序结束")