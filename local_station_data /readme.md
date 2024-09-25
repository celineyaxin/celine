# 网页内容提取
## split.py
* 现在我已经通过之前的工作获得了具体的金融类投诉编码（删除2024部分数据）
<!-- 这是一个备注 -->
通过确定有贷款业务的金融类企业，提取企业内部的投诉内容
* 因为每次只能批量提取10000，要对所有编码分类成300+个文件

<!-- 这是一个备注 -->
在数据处理过程中出了一点小问题，为了提高工作效率，现在已经跑完了一部分编号。并且每个文件只有7000条文件数量比较多就会很浪费时间，所以需要代码剔除重新分
* **append.py**：需要合并一下已经提取的编码内容
* **filter_finished**.py： 把原始编码剔除已经跑好的
* **splite.py**：重新分类

## supplementary_extraction.py
* 原规则：金融类企业根据入驻商家列表确定，其中还包含投诉量较多的（投诉对象投诉100条以上）商家确定
* 补充提取内容：投诉对象100以下并且不在入驻商家列表的商家投诉
* 51913

## next_encode.py 生成下一个地区需要跑的编码 
* 修改参数：cells_count/gd_pattern/folder_path/output_excel_path/original_csv_path/output_csv_path 
 output_csv_path
### filter_province.py
* 根据网页链接规则筛选出该地方的投诉信息
* 使用文件夹中300文件合并提取
* 修改：gd_pattern/folder_path/output_excel_path
<!-- 这是一个备注 -->
gd 364823
zj 184757
sh 97656
sx 86995
gx 77547
jl 59001
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

