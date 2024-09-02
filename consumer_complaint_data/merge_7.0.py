import os
import pandas as pd
import multiprocessing
from multiprocessing import Manager
import csv
from itertools import zip_longest

class DataMerger:
    def __init__(self, folder_path, output_folder, excel_file_path, corner_case_path):
        self.folder_path = folder_path
        self.output_folder = output_folder
        self.excel_file_path = excel_file_path
        self.corner_case_path = corner_case_path
        self.cornerCase = self._filterCornerCase()
        self.keyWordSeller = self._load_keywords()
        self.filterSeller = self._filterSeller()
        self.status = 0
        self.result = Manager().dict()

    def _filterCornerCase(self):
        replacement_dict = {}
        with open(self.corner_case_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # 从CSV文件中读取替换规则
                original_value = row['关键词']
                replacement_value = row['替换值']
                replacement_dict[original_value] = replacement_value
        return replacement_dict

    def _filterSeller(self):
        keyWords = ['贷','钱','金','交','银','期','花','付','借','款','易','宝','支','保','险','科','教','鑫','融','还']
        result = []
        for i in self.keyWordSeller.keys():
            for key in keyWords:
                if key in i:
                    result.append(i)
        return result

    def _load_keywords(self):
        df = pd.read_excel(self.excel_file_path, sheet_name='Sheet1')
        columns_of_interest = ['商家名', '编码']
        strip_series = df[columns_of_interest].applymap(lambda x: x.strip() if isinstance(x, str) else x)
        result = {}
        for key, value in zip_longest(strip_series[columns_of_interest[0]], strip_series[columns_of_interest[1]]):
            result[key] = value
        return result
        
    def merge_files(self, file_range, num):
        start, end = file_range
        files_to_merge = ["merged_" + str(i) + ".csv" for i in range(start, end)]
        df_batch = pd.DataFrame()

        for file_name in files_to_merge:
            file_path = os.path.join(self.folder_path, file_name)
            if not os.path.exists(file_path):
                print(f"文件 {file_path} 不存在，跳过。")
                continue
            df = pd.read_csv(file_path, low_memory=False)
            df['filter_result'] = df.apply(lambda row: self._filter(row['发起投诉内容'], row['投诉进度'], row['投诉对象'], row['投诉编号']), axis=1)
            df['投诉商家'] = df['filter_result'].apply(lambda result: result.get('投诉商家', ''))
            df['匹配状态'] = df['filter_result'].apply(lambda result: result.get('匹配状态', ''))
            df['投诉编号'] = df['filter_result'].apply(lambda result: result.get('投诉编号', ''))
            filtered_df = df[['投诉编号', '投诉商家', '匹配状态']]
            df_batch = pd.concat([df_batch, filtered_df], ignore_index=True)
            print(file_name)
        
        self.result[num] = df_batch
        print(f"{num}批次的文件合并完成。")

    def _filter(self, column_context, process_status, complain_object, complain_id):
        column_context = str(column_context)
        complain_object = str(complain_object)
        process_status = str(process_status)
        if "商家只有匹配成功" in complain_object or "待分配" in process_status:
            return {'投诉商家': complain_object, '匹配状态': '0', '投诉编号': complain_id}
        elif str(complain_id) == 'nan':
            return {}
        else:
            filterName = self.cornercase_replace(complain_object, column_context)
            return {'投诉商家': filterName, '匹配状态': self.status, '投诉编号': complain_id}

    def cornercase_replace(self, source_name, column_context):
        wordInplaceDict = {'建设银行':'中国建设银行','建行':'中国建设银行'}
        keyFilterWord = ['借钱', '贷款', '还款', '催收', '借款', '利息', '利率', '砍头息']
        keySourceName = {'美团' : '美团借钱', '哈啰': '哈啰金融', '唯品会': '唯品花', '去哪儿网' : '去哪儿网金融'}
        if source_name in self.cornerCase.keys():
                self.status = 2
                return self.cornerCase[source_name]
        for key in wordInplaceDict.keys():
            if key in source_name:
                self.status = 2
                return wordInplaceDict[key]
        for key in keySourceName.keys():
            if key in source_name:
                if any(word in column_context for word in keyFilterWord) :
                    self.status = 2
                    return keySourceName[key]
        for key , num in self.keyWordSeller.items():
            if source_name in key:
                self.status = 2
                return source_name
        for keyword, num in self.keyWordSeller.items():
            if keyword in source_name:
                    self.status = 2
                    return keyword
        if "客服" in source_name:
            source_name = source_name.split("客服")[0]
            if source_name in self.cornerCase.keys():
                self.status = 2
                return self.cornerCase[source_name]
        self.status = 1
        return source_name

    def execute_in_stages(self, task_ranges, processes_per_stage, total_processes):
        pools = []
        for num, tasks in enumerate(task_ranges, start=1):
            process = multiprocessing.Process(target=self.merge_files, args=(tasks, num))
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
        self.merge_2(total_processes)

    def merge_2(self, total_process):
        df_batch = pd.DataFrame()
        output_file = os.path.join(self.output_folder, f'mergedSeller.csv')
        for i in range(1, total_process + 1):
            df_batch = pd.concat([df_batch, self.result[i]], axis=0, ignore_index=True)   #0纵向合并；1横向合并
        df_batch.to_csv(output_file, index=False)
        

if __name__ == "__main__":
    merger = DataMerger(
        folder_path='/Users/chenyaxin/Desktop/websitdata/merge_data2',
        output_folder='/Users/chenyaxin/Desktop/websitdata/merge_data3',
        excel_file_path='/Users/chenyaxin/Desktop/websitdata/商家列表.xlsx',
        corner_case_path='/Users/chenyaxin/Desktop/websitdata/corner_cases.csv'
    )
    num_files = 65
    total_processes = 5

    file_ranges = [(i * num_files // total_processes, (i + 1) * num_files // total_processes) for i in range(total_processes)]
    merger.execute_in_stages(file_ranges, total_processes // 5, total_processes)

    print("所有批次的文件合并完成。")
    
