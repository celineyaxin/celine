# import requests
# import pandas as pd
# import pdfplumber
# pdf_path = "downloads/000001_平安银行/20140715_平安银行：公司章程及其附件修订对照表.pdf"
# all_tables = []
# with pdfplumber.open(pdf_path) as pdf:
#     for page in pdf.pages:
#         tables = page.extract_tables()
#         tables = [item for sublist in tables for item in sublist]
#         if tables:
#             all_tables.extend(tables)
# url = "https://api.siliconflow.cn/v1/chat/completions"

# payload = {
#     "model": "Qwen/QVQ-72B-Preview",
#     "messages" :[
#     {'role': 'user', 'content': f"{all_tables}, \n这个一个pdf解析到的表格，你现在需要把他分为修订前和修订后，我不要中间过程，也不要代码，只要最后的data_frame形式的结果，其中列名格式如下：\修订前,修订后\n"}
# ],
# }
# headers = {
#     "Authorization": "Bearer sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol",
#     "Content-Type": "application/json"
# }

# response = requests.request("POST", url, json=payload, headers=headers)

# print(response.text)

from openai import OpenAI
import pandas as pd
import pdfplumber
pdf_path = "downloads/000001_平安银行/20140715_平安银行：公司章程及其附件修订对照表.pdf"
client = OpenAI(api_key="sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol", base_url="https://api.siliconflow.cn/v1")
all_tables = []
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        tables = [item for sublist in tables for item in sublist]
        if tables:
            all_tables.extend(tables)
    
response = client.chat.completions.create(
    model='deepseek-ai/DeepSeek-V2.5',
    messages=[
        {'role': 'user', 'content': f"{all_tables}, \n这个一个pdf解析到的表格，你现在需要把他分为修订前和修订后，我不要中间过程，也不要代码，只要最后的的结果，最后的结果必须是一个csv的形式，尤其要注意，一定要用双引号分割内容，不然在read的csv的时候会出错，其中只有两列，列名格式如下：\修订前,修订后\n,切记，一定要以csv形式的形式返回结果就好，千万不要返回代码，不要返回中间过程"}
    ],
    stream=True
)

full_response = ""
for chunk in response:
    full_response += chunk.choices[0].delta.content
    # print(chunk.choices[0].delta.content, end='')
# full_response = full_response.replace('\n', ' ').replace('\r', ' ')
# 打印完整响应
print(full_response)

# 将响应解析为DataFrame
from io import StringIO

csv_data = StringIO(full_response)
df = pd.read_csv(csv_data, header=0)
print(df)


