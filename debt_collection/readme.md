## get_sample.py
* replace_xiaoyi.py合并了分期易数据/并且剔除了恶意投诉的部分获得**financial_final.csv**
* 按照年份平均的随机抽取5000条投诉文本，用于bert分类之前的文本标记**classify_sample.csv**

## bank_filter.py
* 从金融类投诉中筛选出银行相关的投诉内容**bank_complaints.csv**

## text_sample_classify.py 
* 对投诉文本的内容进行分类
1. 私自扣款不属于催收？/标注清楚两个结果（包含扣款和不扣款）
* 根据模型输出的文本特征对结果进行切分和筛选，分别写入结果与理由两列，添加到**classify_result.csv**
* 方式转变：电话催收、上门催收和法律诉讼催收
* 恶性类型的催收减少：暴力催收
* 银行不良贷款降低（降低催收需求）/还款提醒

## classify_double.py （用v3切分规则）
**下一次用这部分代码可以考虑优化一下写入的部分**
* 对投诉文本的内容进行分类
* 根据模型输出的文本特征对结果进行切分和筛选，分别写入结果与理由两列，添加到**classify_result_double.csv**

## classify_double_r1.py （要求简洁表达就需要更换识别的正则）
**下一次用这部分代码可以考虑优化一下写入的部分**
* 对投诉文本的内容进行分类
* 根据模型输出的文本特征对结果进行切分和筛选，分别写入结果与理由两列，添加到**classify_result_double.csv**


## result_split.py（合并进text_sample_classify.py）
* 根据模型输出的文本特征对结果进行切分和筛选，分别写入结果与理由两列，添加到**classify_result.csv**
* 是否催收相关：切分出模型输出开头的是/否
* 判断理由：删除前面的标点符号；删除第一个冒号及之前的内容

## bert_train.py
* 需要提供train、dev、test三个文件，文件要求两列一列是文本内容，一列是做好的标记，在提供的文件中不需要写列名,将**classify_result.csv**按照4000，500，500切分成三个文件
* 三个文件保存的格式如果出问题去notepad++调整编码

## second_sample.py
* 获取**sampled_fraud.xlsx**
## treat.py
* 筛选出处理组企业看看他们都有哪些投诉内容

## summary.py
* 统计预测数量

## summary.py
* 对prediction结果的文件也要剔除恶意重复投诉的内容

drop if 投诉对象==“找靓机”    1000181
drop if 投诉对象==“小黑鱼科技” 1002636

逾期；还款；银行
