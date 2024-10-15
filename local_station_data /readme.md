# 网页内容提取
## split.py
* 现在我已经通过之前的工作获得了具体的金融类投诉编码（删除2024部分数据）
<!-- 这是一个备注 -->
通过确定有贷款业务的金融类企业，提取企业内部的投诉内容
* 因为每次只能批量提取10000，要对所有编码分类成300+个文件

<!-- 这是一个备注 -->
在数据处理过程中出了一点小问题，为了提高工作效率，现在已经跑完了一部分编号。并且每个文件只有7000条文件数量比较多就会很浪费时间，所以需要代码剔除重新分
* **append.py**：需要合并一下已经提取的编码内容
* **filter_finished.py**： 把原始编码剔除已经跑好的
* **splite.py**：重新分类
<!-- 这是一个备注 -->

## supplementary_extraction.py
* 原规则：金融类企业根据入驻商家列表确定，其中还包含投诉量较多的（投诉对象投诉100条以上）商家确定
* 补充提取内容：投诉对象100以下并且不在入驻商家列表的商家投诉
* 51913

## supplementary_encode.py
* 爬取过程中会有一些遗漏，筛选出来重新爬取
* 从进行分类的文件中complaint_ids_classfy_xx剔除已经爬取的地方
* 修改参数：pattern/folder_path（都是同一个地方站）
* 在筛选之后还是需要分子文件重新爬取筛选，使用split.py文件修改i

## next_encode.py 生成下一个地区需要跑的编码 
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
* **filter_province_simple.py**：使用少量文件合并提取

### filter_finished.py
* 把原始编码剔除已经跑好的
* 修改:original_csv_path/merged_excel_path

## splite.py
* 重新根据数量分类
* 修改：file_path

<!-- 这是一个备注 -->
### 对于每一个地区的数据筛选完之后都可以做一波剔除然后再跑下一个省份的数据
* **filter_province.py**：提取出省份的信息
* **filter_finished**.py：删除这些已经确定省份的信息
* **split.py**：再进行分组

