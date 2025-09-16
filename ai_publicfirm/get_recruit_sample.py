import pandas as pd

# 读取CSV文件
def load_data(file_path):
    return pd.read_csv(file_path)

# 统计职位描述列的缺失值数量、每年的缺失值数量及其占比
def count_missing_values(df, date_column, column_name):
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df['year'] = df[date_column].dt.year
    total_count = len(df)
    missing_count = df[column_name].isnull().sum()
    yearly_missing_counts = df.groupby('year')[column_name].apply(lambda x: x.isnull().sum())
    yearly_missing_percentages = yearly_missing_counts / df.groupby('year').size() * 100
    return total_count, missing_count, yearly_missing_counts, yearly_missing_percentages


# 确定数据覆盖的年份范围和年份分布
def get_year_range(df, date_column):
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df['year'] = df[date_column].dt.year
    year_counts = df['year'].value_counts().sort_index()
    min_year = year_counts.index.min()
    max_year = year_counts.index.max()
    return min_year, max_year, year_counts

# 打印统计信息
def print_statistics(total_count, missing_count, yearly_missing_counts, yearly_missing_percentages, year_range, year_counts):
    print(f"总数据量: {total_count}")
    print(f"职位描述列的缺失值数量: {missing_count}")
    print(f"职位描述列的缺失值占比: {missing_count / total_count * 100:.2f}%")
    print(f"数据覆盖的年份范围: {year_range[0]} - {year_range[1]}")
    print("每年的记录数量分布：")
    print(year_counts)
    print("每年的职位描述缺失值数量及占比：")
    for year in yearly_missing_counts.index:
        print(f"{year}: {yearly_missing_counts[year]} ({yearly_missing_percentages[year]:.2f}%)")

# 提供一个接口，询问用户是否继续进行下一个任务
def ask_user():
    response = input("是否要进行下一个任务？(yes/no): ")
    return response.lower() == 'yes'

def sample_data(df, date_column, source_column, sample_size=5000):
    # 确保日期列是datetime类型
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df['year'] = df[date_column].dt.year
    
    # 按年份和来源分层抽样
    stratified_sample = df.groupby(['year', source_column], group_keys=False).apply(
        lambda x: x.sample(min(len(x), sample_size // len(df.groupby(['year', source_column]))), random_state=42)
    )
    
    # 如果分层抽样后的样本数不足5000，再进行随机抽样补充
    if len(stratified_sample) < sample_size:
        additional_samples = df.drop(stratified_sample.index).sample(sample_size - len(stratified_sample), random_state=42)
        stratified_sample = pd.concat([stratified_sample, additional_samples])
    
    return stratified_sample

# 主函数
def main(file_path):
    # 加载数据
    df = load_data(file_path)
    
    # 统计职位描述列的缺失值数量、每年的缺失值数量及其占比
    total_count, missing_count, yearly_missing_counts, yearly_missing_percentages = count_missing_values(df, '招聘发布日期', '职位描述')
    
    # 确定数据覆盖的年份范围和年份分布
    min_year, max_year, year_counts = get_year_range(df, '招聘发布日期')
    
    # 打印统计信息
    print_statistics(total_count, missing_count, yearly_missing_counts, yearly_missing_percentages, (min_year, max_year), year_counts)
    
    # 提供一个接口，询问用户是否继续进行下一个任务
    if ask_user():
        # 随机抽取5000条样本
        sample_df = sample_data(df, '招聘发布日期', '来源', sample_size=5000)
        print(f"随机抽取的样本数量: {len(sample_df)}")
        sample_df.to_csv('/Users/chenyaxin/Desktop/sampled_data.csv', index=False)
        print("样本数据已保存到 '/Users/chenyaxin/Desktop/sampled_data.csv' 文件中。")

if __name__ == "__main__":
    file_path = '/Users/chenyaxin/Desktop/上市公司投诉数据探究/人工智能/上市公司招聘大数据/上市公司招聘大数据2014-2023年.csv'  # 替换为你的CSV文件路径
    main(file_path)