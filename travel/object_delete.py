import pandas as pd
import shutil
from openpyxl import load_workbook
csv_path = '/Users/chenyaxin/Desktop/互联网旅游公约/商家列表.csv'

filtered_df = pd.read_excel(csv_path)
keywords = ['银行', '基金', '教育','贷','健身','整形','医院','医美','金融','手游','驾校','火锅','房地产','家居','潮玩','玩具','拼多多','手表','中介','生物','轻奢','厨具',
            '分期','信用卡','电脑','宽带','借款','美术','游戏','课堂','音乐','阅读','汽配','果园','物业','环保','母婴','信托','京东','通信','教育科技','网络服务','经销',
            '借','财经','财会','相机','钱包','保险','会计','学校','医生','床垫','冰箱','支付','运动','影音','保健','男装','图书','门窗','出租车','专营店','照片','鞋',
            '学校','学堂','瑜伽','网教','人寿','面包','同仁堂','体育','方特','坚果','维修','复印','体脂','资产','贸易','网络科技','散热','租赁','法律','电玩','商城',
            '短视频','快递','乐园','小说','人保寿险','婚纱','公主','知识','手机','学历','餐饮','安防','药房','家具','4s','家具','纹绣','科技发展','店','租房','咨询',
            '祛痘','钢琴','英语','数码','汽车','皮肤','家纺','服饰','资产管理','地产','设计师','珠宝','护肤','雅思','电竞','摩托车','摄像头','生鲜','理财','生活','蛋糕',
            '斗地主','pos','婚恋','医疗','充电宝','顺风车','家电','家居','快跑','水果','奶茶','健康','燕窝','首饰','电器','营销','卫浴','电子商务','数字科技','闲置',
            '早教','充电','文学','植发','信息科技','成语','直播','万科','照明','摄影','食品','工具','美妆','分期','车饰','万达','旗舰店','批发','优选','疫苗','传播',
            '文具','社区','设备','户外','装饰','视频','户外','专柜','艺术','美甲','电动车','商学院','信息技术','财富管理','超市','文玩','商贸','销售','托管','物流','娱乐',
            '医药','工艺','灯饰','购物','宠物','养殖','家政','百货','游泳','微信','工厂','舞蹈','美容','衣橱','酒吧','水产','供应链','隐形眼镜','律师','文化科技','比萨',
            '文化传媒','传媒文化','数字技术','能源科技','馆','营业厅','培训','麻将','代购','相声','公园','电子科技','饰品','学习机','饮水机','新闻','地铁','售后','乳业',
            '电商','凉茶','餐厅','网银','网校','权益保障','披萨','suv','洗衣','奶粉','半永久','耳机','显示器','韩语','共享单车','麻辣烫','笔记本','快充','融资担保','企业管理',
            '彩妆','证券','财商','期货','用车','啤酒','编程','留学','征信','眼镜','啤酒','零食','茶饮','顺丰','58','宅急送','养生壶','月嫂','牧业','美食','童装','牙刷','学院',
            '网约车','零钱通','合作社','工程','皮件','置业','财富','鲜果','婚庆','教学','菜场','酒业','投资','运输','燃气','日用品','信用社','企业服务','中医','女装','学习',
            '派送','人力资源','房产','印刷','单车','女装','考研','婚姻','空调','窗帘','房产','财险','物联网','农业','区块链','广告','口腔','饮食','建材']
# mask = filtered_df['投诉对象'].str.contains('|'.join(keywords), na=False)
regex_pattern = '|'.join([keyword for keyword in keywords])  # 将关键词列表转换为正则表达式
mask_keywords = filtered_df['投诉对象'].str.contains(regex_pattern, na=False, case=False)

business_names_path = '/Users/chenyaxin/Desktop/互联网旅游公约/可删除商家.xlsx'
business_names_df = pd.read_excel(business_names_path)
business_names = set(business_names_df['商家名称'])
mask_comma = filtered_df['投诉对象'].str.contains('[,，]', na=False)

df_filtered = filtered_df[~mask_keywords & ~filtered_df['投诉对象'].isin(business_names) & ~mask_comma]
df_rejected = filtered_df[mask_keywords | filtered_df['投诉对象'].isin(business_names) | mask_comma]
excel_path = '/Users/chenyaxin/Desktop/互联网旅游公约/object_results.xlsx'
excel_path = '/Users/chenyaxin/Desktop/互联网旅游公约/merchant_results.xlsx'

# 使用ExcelWriter保存数据到两个工作表
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    df_filtered.to_excel(writer, sheet_name='Filtered Data', index=False)
    df_rejected.to_excel(writer, sheet_name='Rejected Data', index=False)
    print(f"处理后的数据已保存至 '{excel_path}'，其中包含两个新的工作表：'Filtered Data' 和 'Rejected Data'")
