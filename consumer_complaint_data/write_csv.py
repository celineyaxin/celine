import csv
cornerCase = {'wbjq客服': '微博借钱','星途金融客服' : '苏宁金融', '广发信用卡': '广发银行', '小易服务': '分期乐', '捷信消费金融有限公司': '捷信金融','贴芯贷':'贴心贷','邮储银行电子银行':'中国邮政储蓄银行',
            '启丰售后':'优逸花','商盟商务服务有限公司':'商盟统统付','极融服务':'极融借款','阳光消费_TS':'阳光消费金融','华夏信用卡中心微博':'华夏银行','AntView':'小微金融','阳光保险集团':'中国阳光保险',
            '中国移动和包':'中国移动和包支付','阿里客服':'淘宝客服','京东客服':'京东商城','顺丰官方客服':'顺丰速运','拍拍':'京东拍拍','书汇天涯':'柠檬分期','51Talk青少英语':'51Talk在线青少儿英语',
            '51Talk在线青少儿英语':'51Talk在线青少儿英语','58速运官博':'快狗打车','晟晟炘炘物联':'即刻分期','139邮箱-客服精灵':'139邮箱-客服精灵','3D木门官方':'3D无漆木门','95511平安':'中国平安',
            '滴滴出行客服':'滴滴用车','苏宁客服中心':'苏宁易购'}
filename = '/Users/chenyaxin/Desktop/websitdata/corner_cases.csv'
with open(filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['关键词', '替换值'])
    for key, value in cornerCase.items():
        writer.writerow([key, value])

        