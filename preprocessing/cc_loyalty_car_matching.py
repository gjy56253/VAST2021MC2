import pandas as pd
import numpy as np
import os

# 路径配置
DATA_DIR = '../data'
OUTPUT_CERTAIN = os.path.join(DATA_DIR, 'task3_certain_mapping.csv')
OUTPUT_UNCERTAIN = os.path.join(DATA_DIR, 'task3_uncertain_mapping.csv')
OUTPUT_ALL = os.path.join(DATA_DIR, 'task3_all_mapping.csv')


def main():
    print("正在启动 人-车-卡 身份映射融合引擎 (加入真实交易频次概率测算)...")

    # ==================== 1. 读取三份核心数据表 ====================
    # 采用多重编码兼容模式彻底解决 UnicodeDecodeError
    def safe_read_csv(file_name):
        file_path = os.path.join(DATA_DIR, file_name)
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return pd.read_csv(file_path, encoding='gbk')
            except UnicodeDecodeError:
                return pd.read_csv(file_path, encoding='latin1')

    df_network = safe_read_csv('cc_loyalty_network.csv')
    df_car = safe_read_csv('cc_to_car_match.csv')
    df_matched = safe_read_csv('cc_loyalty_matched.csv')  # 读取全量交易流水表

    # ==================== 2. 字段映射与标准化 ====================
    if 'Credit_Card' in df_network.columns:
        df_network.rename(columns={'Credit_Card': 'last4ccnum'}, inplace=True)
    if 'Loyalty_Card' in df_network.columns:
        df_network.rename(columns={'Loyalty_Card': 'loyaltynum'}, inplace=True)

    # 统计每辆车被多少张信用卡绑定
    car_cc_counts = df_car.groupby('Matched_CarID')['last4ccnum'].transform('count')
    df_car['Car_CC_Count'] = car_cc_counts

    # ==================== 3. 概率测算模块 ====================
    truck_ids = [101, 104, 105, 106, 107]

    # --- 3.1 计算车辆侧的归属概率 (Car_Share_Prob) ---
    hit_rate_sums = df_car.groupby('Matched_CarID')['Hit_Rate'].transform('sum')
    car_probs = []
    for idx, row in df_car.iterrows():
        car_id = row['Matched_CarID']
        # 集群逻辑：卡车或没有匹配到车的，视为 9 人集群，概率均分为 1/9
        if pd.isna(car_id) or car_id in truck_ids:
            car_probs.append(1.0 / 9.0)
        else:
            # 专属配车逻辑：基于 Hit_Rate 比例分配
            if hit_rate_sums[idx] > 0:
                car_probs.append(row['Hit_Rate'] / hit_rate_sums[idx])
            else:
                car_probs.append(1.0)
    df_car['Car_Share_Prob'] = car_probs

    # --- 3.2 计算会员卡侧的归属概率 (Loyalty_Share_Prob) ---
    # 利用 cc_loyalty_matched.csv 中的所有交易数据，计算卡卡共现次数
    df_matched_valid = df_matched.dropna(subset=['last4ccnum', 'loyaltynum']).copy()
    match_counts = df_matched_valid.groupby(['last4ccnum', 'loyaltynum']).size().reset_index(name='Match_Count')

    # 将真实的匹配次数左连接回网络结构表
    df_network = pd.merge(df_network, match_counts, on=['last4ccnum', 'loyaltynum'], how='left')
    # 对于极少数在流水中未体现但存在于网络关系的异常记录，保底置为 1 次
    df_network['Match_Count'] = df_network['Match_Count'].fillna(1)

    # 以信用卡为单位，计算每张会员卡的交易占比
    loyalty_sums = df_network.groupby('last4ccnum')['Match_Count'].transform('sum')
    df_network['Loyalty_Share_Prob'] = np.where(loyalty_sums > 0, df_network['Match_Count'] / loyalty_sums, 1.0)

    # ==================== 4. 核心合并与总概率 ====================
    # 以信用卡为中心桥梁执行外连接
    df_merged = pd.merge(df_car, df_network, on='last4ccnum', how='outer')

    # 计算综合推断概率 (Inference_Probability)
    df_merged['Car_Share_Prob'] = df_merged['Car_Share_Prob'].fillna(1.0)
    df_merged['Loyalty_Share_Prob'] = df_merged['Loyalty_Share_Prob'].fillna(1.0)
    df_merged['Inference_Probability'] = df_merged['Car_Share_Prob'] * df_merged['Loyalty_Share_Prob']

    # 格式化概率显示为百分比
    df_merged['Inference_Probability_Str'] = df_merged['Inference_Probability'].apply(lambda x: f"{x:.2%}")

    # ==================== 5. 建立自动化诊断规则 ====================
    def diagnose_uncertainty(row):
        reasons = []

        # --- A. 物理轨迹层面的不确定性 ---
        if pd.isna(row['Matched_CarID']):
            reasons.append("无物理轨迹(幽灵集群)")
        elif row['Matched_CarID'] in truck_ids:
            reasons.append("公共卡车(幽灵集群)")
        elif row.get('Car_CC_Count', 1) > 1:
            reasons.append(f"一车绑多卡(车主概率:{row['Car_Share_Prob']:.0%})")

        # --- B. 消费逻辑层面的不确定性 ---
        if row.get('Is_Precise', 1) == 0:
            reasons.append(f"积分卡交叉互用(交易共现概率:{row['Loyalty_Share_Prob']:.0%})")
        elif pd.isna(row['loyaltynum']):
            reasons.append("无会员卡记录(刻意隐匿信息)")

        # --- C. 结果判定 ---
        if len(reasons) == 0:
            return pd.Series(['High (铁证)', '无异常，完美1对1'])
        else:
            return pd.Series(['Low (高危)', ' | '.join(reasons)])

    # 应用诊断逻辑
    df_merged[['Certainty_Level', 'Uncertainty_Reason']] = df_merged.apply(diagnose_uncertainty, axis=1)

    # ==================== 6. 数据导出 ====================
    final_cols = [
        'last4ccnum', 'loyaltynum', 'Matched_CarID',
        'FullName', 'CurrentEmploymentType', 'CurrentEmploymentTitle',
        'Inference_Probability_Str', 'Car_Share_Prob', 'Loyalty_Share_Prob', 'Match_Count',
        'Certainty_Level', 'Uncertainty_Reason'
    ]
    existing_cols = [col for col in final_cols if col in df_merged.columns]
    df_final = df_merged[existing_cols].copy()

    # 物理隔离：生成 确定性铁证区 与 盲区异常数据集
    df_certain = df_final[df_final['Certainty_Level'].str.contains('High')]
    df_uncertain = df_final[df_final['Certainty_Level'].str.contains('Low')]

    # 规范排序，以概率和异常原因排序，方便后续作图使用
    df_certain = df_certain.sort_values(by=['Matched_CarID', 'last4ccnum'])
    df_uncertain = df_uncertain.sort_values(by=['Car_Share_Prob', 'Uncertainty_Reason'], ascending=[False, True])

    # 输出文件
    df_all = df_final.sort_values(by=['Certainty_Level'])
    df_all.to_csv(OUTPUT_ALL, index=False, encoding='utf-8-sig')
    df_certain.to_csv(OUTPUT_CERTAIN, index=False, encoding='utf-8-sig')
    df_uncertain.to_csv(OUTPUT_UNCERTAIN, index=False, encoding='utf-8-sig')

    print("融合完成！(已集成真实交易流水频次计算)")
    print(f"👉 完美对应 (铁证): {len(df_certain)} 条")
    print(f"👉 存在异常 (不确定): {len(df_uncertain)} 条")


if __name__ == '__main__':
    main()