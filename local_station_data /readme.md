# 网页内容提取

## split.py
* 现在我已经通过之前的工作获得了具体的金融类投诉编码（有贷款业务）**financial_complains.csv**
* 删除2024部分数据获取**编号.csv**用于分组爬取地方站信息
<!-- 这是一个备注 -->
每次只能批量提取10000，要对所有编码分类成300+个文件

<!-- 这是一个备注 -->
在刚开始test的过程中出现了分类的失误：
* 现在运行了一部分编号
* 每个文件只有7000条文件数量比较多就会很浪费时间
需要代码剔除重新分类
* **append.py**：需要合并一下已经提取的编码内容
* **filter_finished.py**： 把原始编码剔除已经跑好的
* **splite.py**：重新分类

## supplementary_extraction.py
* 原规则：金融类企业根据入驻商家列表确定，其中还包含投诉量较多的（投诉对象投诉100条以上）商家确定
* 补充提取内容：投诉对象100以下并且不在入驻商家列表的商家投诉**51913条未处理数据**
* 根据待提取商家列表获取对应的投诉内容
* 商家列表中的商家信息并不完全来自于金融类企业，根据关键词对投诉的内容进行进一步的筛选
# 地方站数据处理
对于每一个地区的数据筛选完之后都可以做一波剔除然后再跑下一个省份的数据

## 1. supplementary_encode.py
* 爬取过程中会有一些遗漏，筛选出来重新爬取
* 从进行分类的文件中complaint_ids_classfy_xx剔除已经爬取的地方
* 修改参数：pattern/folder_path（都是同一个地方站）
* 在筛选之后还是需要分子文件重新爬取筛选，使用split.py文件修改i

## 2. next_encode.py 生成下一个地区需要跑的编码 
* 修改参数：cells_count/gd_pattern/folder_path/output_excel_path/original_csv_path/output_csv_path 
 output_csv_path
### filter_province.py
* 根据网页链接规则筛选出该地方的投诉信息
* 使用文件夹中300文件合并提取
* 修改：gd_pattern/folder_path/output_excel_path
<!-- 这是一个备注 -->
gd 370813
zj 186552
sh 97860
sx 87142
gx 77602
jl 59057
jiangsu 234083
hunan 122908
henan 145238
hb    127448
sc    143220
fj    91145
ah    101823
hainan 31586
jx    168200
hebei 103653
hlj   45047
ln    81142
cq    55826
tj    34649
* **filter_province_simple.py**：使用少量文件合并提取

### filter_finished.py
* 把原始编码剔除已经跑好的
* 修改:original_csv_path/merged_excel_path

## 3. splite.py
* 重新根据数量分类
* 修改：file_path

## 4. summary.py
* 在原始文件中新加入一列：地区列统计每个地方站的投诉地区
financial_complains.csv ➡️ updated_complaint_summary.csv
updated_complaint_summary.csv ➡️ 
## 5. statistics.py
* 统计地方年份信息
* mean:合并之后根据分好的组别调整指标

# 爬取过程中的遗漏进行查漏补缺
## all_add.py
* 原始文件中2018-2024年数据，删除2019之前及2024之后的数据
* 筛选出没有地区信息的数据no_region_info.csv
* 添加到add_classfy_gd.csv重新进行循环

<!-- 这是一个备注 -->
1. check 之后有一些连续的跑错的重新生成merge.xlsx文件
2. 重新生成add_classfy_zhejiang.csv，剔除add_classfy_zj.csv中的投诉编号，找出没跑过的add_classfy_zj_part12.csv
3. merged.xlsx重新跑一遍得到zj.csv
4. 同样的处理一下江苏站：先得到add_classfy_jiangsu_part12.csv，再得到 merged.xlsx/jiangsu.csv
5. double_check.py:merged.xlsx与zj.csv做一个double check筛选出真的属于地方站的信息
(浙江站只有一条，江苏站一条都没有所以不用做进一步的剔除)
filter_province ➡️ double_check.py ➡️ filter_finished.py ➡️ split.py
* filter_province.py:gd_pattern/folder_path/output_excel_path
gd 24406
zj 1
jiangsu 0
jx 6226
henan 0
hunan 0
hb  7105
sc  9364
ah  6381
hebei  7291
sh 0
fj 6228
sx 0
ln 5837
gx 0
jl 1
cq 3929
hlj 3048
hainan 1562
tj 2606
* 添加投诉对象对应的投诉数量小于100的金融类投诉


