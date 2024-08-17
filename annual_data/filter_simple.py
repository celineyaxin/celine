import os
import pandas as pd
import sys

title=['董事会报告','董事局报告','经营情况讨论与分析','经营层讨论与分析','管理层讨论与分析','管理层分析与讨论','董事会工作报告','董事局工作报告']
nexttitle=['监事会工作报告\n','监事会工作报告 \n','监事会报告 \n','重要事项 \n','公司治理 \n','监事会报告\n','重要事项\n','公司治理\n']


with open('/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/test/000014_2008_沙河股份_2008年年度报告_2009-04-24的副本.txt','r',encoding='utf-8') as f:
    text=f.read()
    minindex1=sys.maxsize
    for i in range(len(title)):
        if text.find(title[i])!= -1 and text[text.find(title[i])+len(title[i])] not in ['“','。','分','一','中','关','之','》','"','—','”','第'] and text.find(title[i]) < minindex1:
                minindex1=text.find(title[i])
                topic=title[i]
                continue
        elif text.find(title[i],text.find(title[i])+1)!= -1 and text.find(title[i]) < minindex1:
                minindex1=text.find(title[i])
                topic=title[i]
        splittext=text.split(topic)
        import pdb
        pdb.set_trace()
        print(topic)

        for ind,j in enumerate(splittext[1:]):
            if j[0:2]==' \n' or j[0]=='\n' or j[0]==' ' or j[0]=='	':
                result=''
                for k in range(ind+1,len(splittext[1:])+1):
                    result=result+splittext[k]
                break
            else:
                continue
        minindex2=sys.maxsize

        for k in range(len(nexttitle)):
            if result.find(nexttitle[k])!= -1 and result.find(nexttitle[k])<minindex2:
                minindex2=result.find(nexttitle[k])
                nexttopic=nexttitle[k]
            else:
                continue
        result=result.split(nexttopic)[0]
        
        with open('/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/提取文本txt/000001_2001.txt','w',encoding='utf-8') as w:
            #result=result.replace('\n','')#删除换行符
            w.write(result)
            w.close()
        print(str(ind)+'完成')