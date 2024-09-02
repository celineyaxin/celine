import os
import pandas as pd
import multiprocessing

def merge_files(file_range, num):
    start, end = file_range
    folder_path = '/Users/chenyaxin/Desktop/websitdata/source_data'  
    output_folder = '/Users/chenyaxin/Desktop/websitdata/merge_data2' 

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    files_to_merge = [str(i) + ".xlsx" for i in range(start, end)]
    df_batch = pd.DataFrame()
    for file_name in files_to_merge:
        file_path = os.path.join(folder_path, file_name)
        if not os.path.exists(file_path):
            print(f"文件 {file_path} 不存在，跳过。")
            continue 
        df = pd.read_excel(file_path, engine='openpyxl', parse_dates=False) 
        # 修改参数保证时间不变
        df_batch = pd.concat([df_batch, df], ignore_index=True)
    
    output_file = os.path.join(output_folder, f'merged_{num}.csv')
    df_batch.to_csv(output_file, index=False)
    print(str(num) + "批次的文件合并完成。")

def execute_in_stages(task_ranges, func, processes_per_stage):
    pools = []
    for num, tasks in enumerate(task_ranges, start=1):
        process = multiprocessing.Process(target=func, args=(tasks, num))
        process.start()
        pools.append(process)
        if num % processes_per_stage == 0:
            for p in pools:
                p.join()
                p.close()
            pools.clear()


if __name__ == "__main__":
    num_files = 2500
    total_processes = 64

    file_ranges = [(i * num_files // total_processes, (i + 1) * num_files // total_processes) for i in range(total_processes)]
    execute_in_stages(file_ranges, merge_files, processes_per_stage=total_processes // 8)

    print("所有批次的文件合并完成。")

