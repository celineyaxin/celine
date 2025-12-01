import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# ========== 1. 生成/更新过程文件（剔除+去重） ==========
def build_remaining(original: Path, output_dir: Path) -> Path:
    """返回剩余数据文件路径；首次调用会创建，后续直接读取"""
    remaining_file = output_dir / "remaining.csv"

    # 1.1 收集所有历史编号
    history_ids = set()
    for f in output_dir.glob("*.csv"):
        df = pd.read_csv(f); history_ids.update(df['投诉编号'].astype(str).str.strip())
    for f in output_dir.glob("*.xlsx"):
        df = pd.read_excel(f); history_ids.update(df['投诉编号'].astype(str).str.strip())
    logging.info(f"历史样本共 {len(history_ids)} 个编号")

    # 1.2 读原始数据并剔除已抽编号
    df_raw = pd.read_csv(original, encoding='utf-8')
    df_raw['投诉编号'] = df_raw['投诉编号'].astype(str).str.strip()
    df_left = df_raw[~df_raw['投诉编号'].isin(history_ids)].copy()

    # 1.3 按投诉内容去重
    df_left = df_left.drop_duplicates(subset=['投诉内容'])
    logging.info(f"剔除后剩余 {len(df_left)} 条，去重后 {len(df_left)} 条")

    # 1.4 写/覆盖过程文件
    df_left.to_csv(remaining_file, index=False, encoding='utf-8')
    return remaining_file

# ========== 2. 从过程文件里抽 n 条并写回剩余 ==========
def sample_from_remaining(remaining_file: Path, n: int):
    df = pd.read_csv(remaining_file)
    if len(df) < n:
        logging.warning(f"只剩 {len(df)} 条，调整样本量为 {len(df)}")
        n = len(df)

    new = df.sample(n, random_state=42)                       # 抽样
    df_unused = df.drop(new.index)                            # 删除已用行
    out_file = remaining_file.with_name(
        f"样本_{n}条_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    new.to_excel(out_file, index=False) # 保存新样本
    df_unused.to_csv(remaining_file, index=False, encoding='utf-8')  # 覆盖剩余
    logging.info(f"✅ 完成，过程文件已更新，剩余 {len(df_unused)} 条")
    remaining_file.unlink()
    logging.info("🗑 过程文件已删除")

# ========== 主流程 ==========
if __name__ == '__main__':
    original = Path("/Users/chenyaxin/Desktop/websitdata/merge_data6/delete_hostility.csv")
    out_dir  = Path("/Users/chenyaxin/Desktop/审稿修改/分类数据")
    out_dir.mkdir(exist_ok=True)

    remaining_csv = out_dir / "remaining.csv"
    if not remaining_csv.exists():
        remaining_csv = build_remaining(original, out_dir)

    n = int(input("要抽多少条？ "))
    sample_from_remaining(remaining_csv, n)