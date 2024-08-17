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

### risk_words.py
* 对提取出来的词语进行筛选

### supplychain_words.py
* 对提取出来的供应链相关词语进行筛选

### measurement.py
* 
