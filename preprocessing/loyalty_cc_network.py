import pandas as pd
import os

# ==========================================
# 路径配置：脚本放在 preprocessing 下，数据在同级的 data 下
# ==========================================
DATA_DIR = '../data'
INPUT_FILE = os.path.join(DATA_DIR, 'cc_loyalty_matched.csv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'cc_loyalty_network.csv')


def main():
    print(f"正在从 {DATA_DIR} 目录加载全外连接大表...")
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 错误：找不到文件 {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, encoding='latin1')

    print("\n正在提取 [信用卡] 与 [会员卡] 的对应关系...")

    # 1. 提取两列并全局去重
    mapping_df = df[['last4ccnum', 'loyaltynum']].drop_duplicates().copy()

    # 2. 将 NaN 统一替换为字符串 'NA'
    mapping_df['last4ccnum'] = mapping_df['last4ccnum'].fillna('NA')
    mapping_df['loyaltynum'] = mapping_df['loyaltynum'].fillna('NA')

    # ==========================================
    # 核心步骤 1：智能清洗 NA（处理“唯一绑定伴随的冗余 NA”）
    # ==========================================
    valid_cc_to_loy = mapping_df[(mapping_df['last4ccnum'] != 'NA') & (mapping_df['loyaltynum'] != 'NA')]
    cc_with_real_matches = valid_cc_to_loy['last4ccnum'].unique()
    loy_with_real_matches = valid_cc_to_loy['loyaltynum'].unique()

    cond_a = (mapping_df['last4ccnum'] != 'NA') & (mapping_df['loyaltynum'] != 'NA')
    cond_b = (mapping_df['last4ccnum'] != 'NA') & (mapping_df['loyaltynum'] == 'NA') & (
        ~mapping_df['last4ccnum'].isin(cc_with_real_matches))
    cond_c = (mapping_df['last4ccnum'] == 'NA') & (mapping_df['loyaltynum'] != 'NA') & (
        ~mapping_df['loyaltynum'].isin(loy_with_real_matches))

    final_mapping_df = mapping_df[cond_a | cond_b | cond_c].copy()
    final_mapping_df.columns = ['Credit_Card', 'Loyalty_Card']

    # ==========================================
    # 核心步骤 2：新增“精准匹配度”属性评估 (Is_Precise)
    # ==========================================
    print("正在评估卡片映射的歧义性 (计算 1对1 属性)...")

    # 统计真实卡号在最终映射表中出现的次数 (排除 NA 占位符的干扰)
    cc_counts = final_mapping_df[final_mapping_df['Credit_Card'] != 'NA']['Credit_Card'].value_counts()
    loy_counts = final_mapping_df[final_mapping_df['Loyalty_Card'] != 'NA']['Loyalty_Card'].value_counts()

    def get_match_type(row):
        cc = row['Credit_Card']
        loy = row['Loyalty_Card']

        # 只要真实的卡号在表中出现了大于 1 次，就说明它卷入了“互借/代刷”的歧义网络
        cc_is_unique = True if cc == 'NA' else (cc_counts.get(cc, 0) == 1)
        loy_is_unique = True if loy == 'NA' else (loy_counts.get(loy, 0) == 1)

        # 如果信用卡和会员卡都是唯一的专属映射 (或彻底的孤立卡)，则标记为 1
        if cc_is_unique and loy_is_unique:
            return 1
        else:
            return 0  # 存在 1对多、多对1 或 多对多

    # 生成新列
    final_mapping_df['Is_Precise'] = final_mapping_df.apply(get_match_type, axis=1)

    # 3. 排序：按信用卡号排序，让歧义的卡片挨在一起方便查看
    final_mapping_df.sort_values(by=['Credit_Card', 'Loyalty_Card'], inplace=True)

    # 4. 保存文件
    final_mapping_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    print("-" * 50)
    print(f"✅ 网络关系表提取成功！共 {len(final_mapping_df)} 条记录。")
    precise_count = (final_mapping_df['Is_Precise'] == 1).sum()
    ambiguous_count = (final_mapping_df['Is_Precise'] == 0).sum()
    print(f"🎯 绝对 1对1 的精准匹配记录数: {precise_count}")
    print(f"⚠️ 卷入 1对多/多对多 的歧义记录数: {ambiguous_count}")
    print(f"📂 文件已保存至: {OUTPUT_FILE}")
    print("-" * 50)

    print("\n👇 映射关系表前 10 条数据预览:")
    print(final_mapping_df.head(10).to_string(index=False))


if __name__ == '__main__':
    main()