import pandas as pd
import os

# ==========================================
# 路径配置：脚本在 preprocessing 下，数据在同级的 data 下
# ==========================================
DATA_DIR = '../data'
CC_FILE = os.path.join(DATA_DIR, 'cc_data.csv')
LOYALTY_FILE = os.path.join(DATA_DIR, 'loyalty_data.csv')

# 分流输出的两个文件
MATCHED_OUTPUT = os.path.join(DATA_DIR, 'cc_loyalty_matched.csv')
UNMATCHED_OUTPUT = os.path.join(DATA_DIR, 'unmatched_data.csv')


def main():
    print(f"正在从 {DATA_DIR} 目录加载数据...")
    cc_df = pd.read_csv(CC_FILE, encoding='latin1')
    loyalty_df = pd.read_csv(LOYALTY_FILE, encoding='latin1')

    print(f"原始信用卡记录数: {len(cc_df)} 条")
    print(f"原始会员卡记录数: {len(loyalty_df)} 条")

    print("\n正在处理时间戳并对齐日期...")
    cc_time_col = 'timestamp' if 'timestamp' in cc_df.columns else 'tiemstamp'

    # 保留原有的精确时间戳，并将单独的日期提取出来作为 Date 列
    cc_df['timestamp_exact'] = cc_df[cc_time_col]
    cc_df['Date'] = cc_df[cc_time_col].apply(lambda x: str(x).split(' ')[0])
    cc_df.drop(columns=[cc_time_col], inplace=True)
    cc_df.rename(columns={'timestamp_exact': 'timestamp'}, inplace=True)

    loyalty_df.rename(columns={'timestamp': 'Date'}, inplace=True)

    # ==========================================
    # 核心步骤 1：隔离那 3 组会导致笛卡尔积的双胞胎数据
    # ==========================================
    print("\n正在隔离 3 组重复的异常交易（防止合并笛卡尔积）...")

    # 已经清洗好乱码，直接进行精确字符串匹配
    cc_cond_1 = (cc_df['Date'] == '2014-01-09') & (cc_df['location'] == "Guy's Gyros") & (cc_df['price'] == 8.23)
    cc_cond_2 = (cc_df['Date'] == '2014-01-09') & (cc_df['location'] == "Katerina's Cafe") & (cc_df['price'] == 26.60)
    cc_cond_3 = (cc_df['Date'] == '2014-01-11') & (cc_df['location'] == 'Hippokampos') & (cc_df['price'] == 63.21)

    cc_mask = cc_cond_1 | cc_cond_2 | cc_cond_3
    cc_clean = cc_df[~cc_mask].copy()

    lo_cond_1 = (loyalty_df['Date'] == '2014-01-09') & (loyalty_df['location'] == "Guy's Gyros") & (
                loyalty_df['price'] == 8.23)
    lo_cond_2 = (loyalty_df['Date'] == '2014-01-09') & (loyalty_df['location'] == "Katerina's Cafe") & (
                loyalty_df['price'] == 26.60)
    lo_cond_3 = (loyalty_df['Date'] == '2014-01-11') & (loyalty_df['location'] == 'Hippokampos') & (
                loyalty_df['price'] == 63.21)

    loyalty_mask = lo_cond_1 | lo_cond_2 | lo_cond_3
    loyalty_clean = loyalty_df[~loyalty_mask].copy()

    print(f"已暂时隔离信用卡记录: {cc_mask.sum()} 条 (留待后续手动分析)")
    print(f"已暂时隔离会员卡记录: {loyalty_mask.sum()} 条 (留待后续手动分析)")

    # ==========================================
    # 核心步骤 2：执行全外连接并完成数据分流
    # ==========================================
    print("\n正在根据 [Date, location, price] 进行全外连接合并...")

    merged_df = pd.merge(
        cc_clean,
        loyalty_clean,
        on=['Date', 'location', 'price'],
        how='outer',
        indicator=True
    )

    # 1. 提取纯未匹配的残留数据（left_only 或 right_only）存入独立文件，供案情分析
    unmatched_df = merged_df[merged_df['_merge'] != 'both'].drop(columns=['_merge']).copy()

    # 2. 生成最终的大表（Outer Join 完整包含匹配和未匹配记录，供 Task 1 图表使用）
    matched_outer_df = merged_df.drop(columns=['_merge']).copy()
    matched_outer_df.drop_duplicates(inplace=True)

    # ==========================================
    # 保存结果
    # ==========================================
    matched_outer_df.to_csv(MATCHED_OUTPUT, index=False)
    unmatched_df.to_csv(UNMATCHED_OUTPUT, index=False)

    print(f"\n✅ 数据处理完成！")
    print("-" * 50)
    print(f"🎯 [大表] 全外连接总表 (cc_loyalty_matched.csv): {len(matched_outer_df)} 条 -> 已保存")
    print(f"     (包含大部队的所有匹配与未匹配数据，保证 Task 1 网页图表正常渲染)")

    cc_only = unmatched_df['loyaltynum'].isna().sum()
    loyalty_only = unmatched_df['last4ccnum'].isna().sum()
    print(f"🕵️  [独立表] 纯未匹配残留表 (unmatched_data.csv): {len(unmatched_df)} 条 -> 已保存")
    print(f"     💳 仅有信用卡记录 (未出示会员卡): {cc_only} 条")
    print(f"     🏅 仅有会员卡记录 (纯现金支付等): {loyalty_only} 条")
    print("-" * 50)


if __name__ == '__main__':
    main()