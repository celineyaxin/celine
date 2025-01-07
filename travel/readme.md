## filter_treat.py
* 提取（同程艺龙、携程、美团、马蜂窝、去哪儿网）处理组企业（处理组列表.xlsx）的投诉内容travel_complaints.csv
* mt_qn.py:其中美团、去哪儿网他们不同的业务投诉对象相同，需要进一步剔除得到meituan_quna.csv
* split.py:切分代码爬取使用服务条目
* 使用服务.otd：到网站批量进一步提取“使用服务”项目筛选出出行服务的部分
* omitted.py:有一些没爬取到的编号，做一个筛选，补充爬取
* which_service.py:根据获得的网页信息筛选出美团商家和去哪商家中去哪出行服务/美团出行服务的投诉编号extracted_complaints.csv
* delete_bike.py:需要删除的单车/充电宝相关的投诉内容 meituan_delete.csv
* final_treat.py:最后筛选出处理组treat.csv
* :补充提取时间列treat_with_time.csv

## sample_similarity.py
* ori_docu_process.py:为了提升运算的效率，需要处理原始文件，提取需要的列生成新的文件夹（删除2024年）
* random_filter.py:随机抽取处理组投诉内容作为相似度匹配的样本部treatment_sample.csv
* sample_similarity.py:根据上面获得的样本通过文本相似度（余弦相似度）sample_similarity_count.xlsx
## 一个可能的解决方式是先把原始文件按照投诉对象分类整合再算相似度 ##
#### 根据名称筛选投诉对象
* words_delete.py:出来的结果非常混杂，根据名称特征做一个剔除
* object_delete.py:针对投诉对象列表
* doublecheck.py:针对筛选出来的结果再筛选一遍
# 要做的
* 政策前后投诉量有没有明显的变化
* 需要识别的文本类型
有旅游，酒店，机票，航空
有多少上市企业