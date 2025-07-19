import pandas as pd
import re
# 定义文件路径
input_file = '/Users/chenyaxin/Desktop/privacy/商家筛选/处理后的商家列表.xlsx'
output_file = '/Users/chenyaxin/Desktop/privacy/商家筛选/处理后的商家列表.xlsx'

# 读取商家列表 CSV 文件
df = pd.read_excel(input_file)
df['投诉商家'] = df['投诉商家'].astype(str)

# 定义关键词列表
keywords = ['传媒', '快餐','快递','互娱','远游','美学设计','租物','头盔','剪辑','恩爱','etc',
            '轻食','肉蟹煲','酒楼','电力','电器','电气','臭鳜鱼','冰淇淋','外语','供水','ETC',
            '啤酒','俱乐部','烤鱼','跑步机','同城聊','图库','牛肉粉','智能锁','售货机','饮料',
            '免税城','票务','陪练','茅台','应用宝','软件服务','英雄','超人','硬件产品','加速器',
            '叫车','代练','用车','找房','龙湖','换电','美凯龙','应用市场','养车','槟榔','方便面',
            '葡萄酒','显示屏','机场','红枣','后援会','闺蜜','指纹锁','旅行','串串香','汽车保养',
            '自行车','旅行','投诉','电梯','身边事','出版','日托','广播','售楼处','研究院',
            '暖通','官微','官方微博','演唱会','日报','晚报','电台','能源','交通','大数据',
            '晚报','邮局','海淘','机场','顾问','婚礼','马桶','烤肉','大冒险','技术服务','奶昔',
            '广场','连锁机构','植物','环境','厨电','国际教育','联盟','定制','家庭服务','矿泉水',
            '造型设计','公益','猫舍','协作','环境','厨电','出版社','家教','外教','通行','商务',
            '招聘','省心购','情感','移动电源','黄金','省心购','驿站','设计','影院','家庭','教育',
            '听书','装修','官博','动漫','家博会','祛痘','祛斑','汽车','电话','公考','客服','约车',
            '网络科技','洗车','民宿','云购','通讯','讲堂','壁纸','修图','好物','浏览器','充值',
            '扫描','在线科技','速运','词典','时尚','数据','家装','机构','互联','机器人','在线',
            '数据','网络技术','文化']


# 剔除包含关键词的商家名称
def is_valid_company(name):
    for keyword in keywords:
        if keyword in name:
            return False
    return True

def is_english_only(name):
    return bool(re.match(r'^[a-zA-Z\s]+$', name))
original_row_count = len(df)

df = df[df['投诉商家'].apply(is_valid_company)]
english_only_companies = df[df['投诉商家'].apply(is_english_only)]['投诉商家'].tolist()
df = df[~df['投诉商家'].apply(is_english_only)]

# 打印被删除的只包含英文的商家名称
# print("被删除的只包含英文的商家名称：")
# print(english_only_companies)
new_row_count = len(df)
deleted_row_count = original_row_count - new_row_count
print(f"总共删除了 {deleted_row_count} 行内容")

df.to_excel(output_file, index=False)
print(f"处理后的数据已保存到 {output_file}")