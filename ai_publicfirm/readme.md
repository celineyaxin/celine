# 获取投诉数据
## filter_public.py
根据上市公司投诉对象列表 **投诉对象匹配列表.xlsx** 提取上市公司投诉数据**listed-complaints.csv**

## feature_extraction.py 
* 提取上市公司收到的投诉相关的特征：对应的投诉回应时长,回复状态,投诉金额等信息
* 与**listed-complaints.csv**文件中的关键信息合并生成**complaints_character.csv**（检验是否能够作为工具变量）


# 根据投诉文本内容分类
## get_sample.py
* 对投诉文本的内容进行分类

## text_sample_classify.py 
* 对投诉文本的内容进行分类

