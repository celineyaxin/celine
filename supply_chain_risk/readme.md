# 大纲

## annual_data
### filter_simple.py
提取单个年报文件中的指定内容

### filter.py
提取所有年报文件中的制定内容

### merge.py
提取出的文件内容进行合并

### frequence.py
* 查看根据文本内容的分词结果
* 对一些高频词进行stop_words以及user_dic的补充
* 确定min_freq的数值
* 接下来根据调整的结果可以直接构造jason文件了

### jasonsave.py
根据分词的结果保存进jason文件

### word2vec_train
* 根据分词结果对文本进行训练
* 能够更好的查看epoch的迭代信息

### word2vec_test
看训练的结果

### output
结果输出

## earnings_call
### append.py
合并两个文件内容，并且提出包含文本内容的列

### frequence.py
* 查看根据文本内容的分词结果
* 对一些高频词进行stop_words以及user_dic的补充
* 确定min_freq的数值

### jasonsave.py
根据分词的结果保存进jason文件

### word2vec_train
* 根据分词结果对文本进行训练
* 能够更好的查看epoch的迭代信息

### word2vec_test
看训练的结果

### output

## matric_measurement
* 这一个文件夹主要针对已经获得的词汇和结果进行对应词语的指标构造

### stopwords.txt
需要删除的对象都有：
* 标点符号
* 连词
* 人称代词
* 敬语
* 拟声词
* 删除称呼

### risk_words.py
* 对提取出来的词语进行筛选

### supplychain_words.py
* 对提取出来的供应链相关词语进行筛选

### random_sample.py
* 对/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/merged_output.xlsx文件随机抽取2000条信息找一找可以剔除掉的词都有哪些，确认stopwords以及selfdictionary

### duplicates_drop.py
* 对整理出来的stopwords以及selfdictionary删除重复值（不然会增加运算负荷）

### mergeQA.py
* merge_excel_files：将业绩说明会的两个文件合并处理
* remove_salutations/remove_specific_greetings：删除文本中名字、称呼
* group_and_merge_texts：对业绩说明会中投资者和管理层的问答内容根据年份股票代码进行合并，得到年份的业绩说明会记录
（在实际运行过程中因为文件太大，一个.py文件难以运行，我们分成两部分处理）

### measurement.py
* apply_cut_text：筛选出合并的内容并进行分词处理
* cut_text_with_custom_dict： 删除停用词，补充自用词进行分词
* calculate_supply_chain_risk： 根据分词后的文本构造指标
<!-- 这是一个备注 -->
在运行的过程中由于文本数据很大，直接运算压力很大，所以我们使用分年份的方式对数据进行处理

### writer.py
* 将文件写入到一个excel文件


