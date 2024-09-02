import os
import pandas as pd
import multiprocessing
from multiprocessing import Manager
import csv
from itertools import zip_longest
import re
import numpy as np

class DataMerger:
    def __init__(self, folder_path, output_folder, excel_file_path, corner_case_path, financial_firm):
        self.folder_path = folder_path
        self.output_folder = output_folder
        self.corner_case_path = corner_case_path
        self.cornerCase = self._filterCornerCase()
        self.financial_firm = self._load_keywords(financial_firm)
        self.keyWordSeller = self._load_keywords(excel_file_path)
        self.filterSeller = self._filterSeller()
        self.status = 0
        self.number = -1
        self.result = Manager().dict()

    def _filterCornerCase(self):
        replacement_dict = {}
        with open(self.corner_case_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
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

    def _load_keywords(self, excel_file_path):
        df = pd.read_csv(excel_file_path, low_memory=False)
        columns_of_interest = ['投诉商家', '商家编码']
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
            # df['filter_result'] = df.apply(lambda row: self._filter(row['发起投诉内容'], row['投诉进度'], row['投诉对象'], row['投诉编号'], row['发起投诉时间'], row['参与集体投诉时间'], row['参与集体投诉内容']), axis=1)
            df['filter_result'] = df.apply(lambda row: self._filter(row['发起投诉内容'], row['投诉进度'], row['投诉对象'], row['投诉编号'], row['发布时间'], row['参与集体投诉内容']), axis=1)
            df['投诉商家'] = df['filter_result'].apply(lambda result: result.get('投诉商家', ''))
            df['匹配状态'] = df['filter_result'].apply(lambda result: result.get('匹配状态', ''))
            df['投诉编号'] = df['filter_result'].apply(lambda result: result.get('投诉编号', ''))
            df['编码'] = df['filter_result'].apply(lambda result: result.get('编码', ''))
            # df['投诉发起时间'] = df['filter_result'].apply(lambda result: result.get('投诉发起时间', ''))
            df['发布时间'] = df['filter_result'].apply(lambda result: result.get('发布时间', ''))
            df['投诉内容'] = df['filter_result'].apply(lambda result: result.get('投诉内容', ''))
            # filtered_df = df[['投诉商家', '编码','投诉编号', '投诉发起时间','投诉内容']]
            filtered_df = df[['投诉商家', '编码','投诉编号', '发布时间','投诉内容']]
            df_batch = pd.concat([df_batch, filtered_df], ignore_index=True).dropna(how='all')
            print(file_name)
        
        self.result[num] = df_batch
        print(f"{num}批次的文件合并完成。")
        
    # def _filter(self, column_context, process_status, complain_object, complain_id, time1, time2, collective):
    def _filter(self, column_context, process_status, complain_object, complain_id, time, collective): 
        column_context = str(column_context)
        complain_object = str(complain_object)
        process_status = str(process_status)
        collective =str(collective)
        if ("商家只有匹配成功" in complain_object or "待分配" in process_status):
            filterName = self.process_0(complain_object, column_context)
        elif str(complain_id) == 'nan':
            # return {'投诉商家': np.nan, '匹配状态': np.nan, '投诉编号': np.nan, '编码': np.nan, '投诉发起时间': np.nan, '投诉内容': np.nan}
            return {'投诉商家': np.nan, '匹配状态': np.nan, '投诉编号': np.nan, '编码': np.nan, '发布时间': np.nan, '投诉内容': np.nan}
        else:
            filterName = self.cornercase_replace(complain_object, column_context)
        if filterName in self.financial_firm.keys():
            if column_context == 'nan':
                column_context = collective
            # if str(time1) == 'nan':
            #     time = time2
            # else:
            #     time = time1
            # return {'投诉商家': filterName, '匹配状态': self.status, '投诉编号': complain_id, '编码': self.number, '投诉发起时间': time, '投诉内容': column_context}
            return {'投诉商家': filterName, '匹配状态': self.status, '投诉编号': complain_id, '编码': self.number, '发布时间': time, '投诉内容': column_context}
        else:
            # return {'投诉商家': np.nan, '匹配状态': np.nan, '投诉编号': np.nan, '编码': np.nan, '投诉发起时间': np.nan, '投诉内容': np.nan}
            return {'投诉商家': np.nan, '匹配状态': np.nan, '投诉编号': np.nan, '编码': np.nan, '发布时间': np.nan, '投诉内容': np.nan}
 
    def process_0(self, complain_object, column_context):
        if "商家只有匹配成功" in complain_object:
            pattern = r"(\S+)\s+商家只有匹配成功"
            matches = re.findall(pattern, complain_object)[0]
            # print(matches)
        else:
            matches = complain_object
        filterName = self.cornercase_replace(matches, column_context)
        if self.status == 2:
            self.status = 3
        else:
            self.status = 0
            self.number = -2
        return filterName
    
    def cornercase_replace(self, source_name, column_context):
        wordInplaceDict = {'建设银行':'中国建设银行','建行':'中国建设银行'}
        keyFilterWord = ['借钱', '贷款', '还款', '催收', '借款', '利息', '利率', '砍头息']
        keySourceName = {'美团' : '美团借钱', '哈啰': '哈啰金融', '唯品会': '唯品花', '去哪儿网' : '去哪儿网金融'}
        if source_name in self.cornerCase.keys():
            self.status = 2
            self.number = self.keyWordSeller[self.cornerCase[source_name]]
            return self.cornerCase[source_name]
        for key in wordInplaceDict.keys():
            if key in source_name:
                self.status = 2
                self.number = self.keyWordSeller[wordInplaceDict[key]]
                return wordInplaceDict[key]
        for key in keySourceName.keys():
            if key in source_name:
                if any(word in column_context for word in keyFilterWord) :
                    self.status = 2
                    self.number = self.keyWordSeller[keySourceName[key]]
                    return keySourceName[key]
        for key , num in self.keyWordSeller.items():
            if source_name in key:
                self.status = 2
                self.number = num
                return source_name
        for keyword, num in self.keyWordSeller.items():
            if keyword in source_name:
                    self.status = 2
                    self.number = num
                    return keyword
        if "客服" in source_name:
            source_name = source_name.split("客服")[0]
            if source_name in self.cornerCase.keys():
                self.status = 2
                self.number = self.keyWordSeller[self.cornerCase[source_name]]
                return self.cornerCase[source_name]
        self.status = 1
        self.number = -1
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
        output_file = os.path.join(self.output_folder, f'financial_complains.csv')
        for i in range(1, total_process + 1):
            df_batch = pd.concat([df_batch, self.result[i]], axis=0, ignore_index=True)   #0纵向合并；1横向合并
        df_batch.to_csv(output_file, index=False)
        

if __name__ == "__main__":
    merger = DataMerger(
        folder_path='/Users/chenyaxin/Desktop/websitdata/merge_data2',
        output_folder='/Users/chenyaxin/Desktop/websitdata/merge_data3',
        excel_file_path='/Users/chenyaxin/Desktop/websitdata/code/商家列表.csv',
        corner_case_path='/Users/chenyaxin/Desktop/websitdata/code/corner_cases_all.csv',
        financial_firm='/Users/chenyaxin/Desktop/websitdata/code/financial_firm.csv'
    )
    num_files = 65
    total_processes = 25

    file_ranges = [(i * num_files // total_processes, (i + 1) * num_files // total_processes) for i in range(total_processes)]
    merger.execute_in_stages(file_ranges, total_processes // 5, total_processes)

    print("所有批次的文件合并完成。")

  