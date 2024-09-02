import os
import pandas as pd
import multiprocessing
from multiprocessing import Manager
import csv
import hashlib
import shutil

class DataSplit:
    def __init__(self, folder_path, output_folder):
        self.folder_path = folder_path
        self.output_folder = output_folder
        self.status = 0
        self.file_num_list = [0, 9, 41, 71, 92, 97]
        self.result = Manager().dict()
        if os.path.isdir(self.output_folder):
            shutil.rmtree(self.output_folder)
        os.makedirs(self.output_folder)
        
    def split_files(self, file_range, num):
        start, end = file_range
        files_to_merge = ["merged_" + str(i) + ".csv" for i in range(start, end)]
        # files_to_merge = ["../code/test.csv"]

        for file_name in files_to_merge:
            file_path = os.path.join(self.folder_path, file_name)
            if not os.path.exists(file_path):
                print(f"文件 {file_path} 不存在，跳过。")
                continue
            df = pd.read_csv(file_path, low_memory=False)
            # df = pd.read_excel(file_path, engine='openpyxl', parse_dates=False) 
            df["发布时间"] = pd.to_datetime(df["发布时间"], format='%Y年%m月%d日 %H:%M')
            start_year = 2018
            end_year = 2024

            for year in range(start_year, end_year + 1):
                for month in range(1, 13):
                    for i in range(len(self.file_num_list) - 1):
                        df_batch = pd.DataFrame()
                        outputFilename = f"{year}_{month:02d}_{self.file_num_list[i+1]:02d}_{num}"
                        mask = (df['发布时间'].dt.year == year) & (df['发布时间'].dt.month == month)
                        month_data_all = df.loc[mask]
                        month_data = month_data_all.iloc[:,self.file_num_list[i]:self.file_num_list[i+1]]
                        output_folder = os.path.join(self.output_folder, f"output_{year}_{month:02d}")
                        if not os.path.exists(output_folder):
                            os.makedirs(output_folder)
                        output_file = os.path.join(output_folder, f"{year}_{month:02d}_{self.file_num_list[i+1]:02d}"+".csv")
                        if i != 0:
                            month_data = pd.concat([month_data_all['投诉编号'], month_data], axis = 1)
                        if os.path.exists(output_file):
                            month_data.to_csv(output_file, mode='a', header=False, index=False)
                        else:
                            month_data.to_csv(output_file, index=False)
                            

            print(file_name)
            # mask = (df['发布时间'].dt.year == 2018) & (df['发布时间'].dt.month == 3)
            # month_data = df.loc[mask]
            # df_batch = pd.DataFrame()
            # df_batch = month_data.iloc[:,9:15]
            # df_batch = pd.concat([df['投诉编号'], df_batch], axis = 1)
            # print(df_batch['发起投诉时间'])
        print(f"{num}批次的文件合并完成。")
    
    def execute_in_stages(self, task_ranges, processes_per_stage, total_processes):
        pools = []
        for num, tasks in enumerate(task_ranges, start=1):
            process = multiprocessing.Process(target=self.split_files, args=(tasks, num))
            process.start()
            pools.append(process)
            if num % processes_per_stage == 0:
                for p in pools:
                    p.join()
                    p.close()
                pools.clear()
        for p in pools:
            p.join()
            p.close()
            pools.clear()

        

if __name__ == "__main__":
    merger = DataSplit(
        folder_path='/Users/chenyaxin/Desktop/websitdata/merge_data2',
        output_folder='/Users/chenyaxin/Desktop/websitdata/merge_data4',
    )
    num_files = 65
    total_processes = 1

    file_ranges = [(i * num_files // total_processes, (i + 1) * num_files // total_processes) for i in range(total_processes)]
    merger.execute_in_stages(file_ranges, total_processes // 1, total_processes)

    print("所有批次的文件合并完成。")