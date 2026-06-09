import pandas as pd
import numpy as np
import os

# 路径配置
DATA_DIR = '../data'
OUTPUT_FILE = '../data/cc_to_car_match.csv'

# 核心商铺坐标字典
LOCATION_COORDS = {
    'Abila Airport': {'lat': 36.081632, 'lon': 24.850282},
    'Abila Scrapyard': {'lat': 36.075326, 'lon': 24.846182},
    'Abila Zacharo': {'lat': 36.058322, 'lon': 24.872587},
    'Ahaggo Museum': {'lat': 36.076644, 'lon': 24.87751},
    "Albert's Fine Clothing": {'lat': 36.076436, 'lon': 24.85777},
    'Bean There Done That': {'lat': 36.081632, 'lon': 24.850482},
    "Brew've Been Served": {'lat': 36.056108, 'lon': 24.903002},
    'Brewed Awakenings': {'lat': 36.055088, 'lon': 24.87758},
    'Carlyle Chemical Inc.': {'lat': 36.059161, 'lon': 24.882402},
    'Chostus Hotel': {'lat': 36.070683, 'lon': 24.895213},
    'Coffee Cameleon': {'lat': 36.054664, 'lon': 24.889801},
    'Coffee Shack': {'lat': 36.074216, 'lon': 24.8606443},
    'Desafio Golf Course': {'lat': 36.091349, 'lon': 24.864464},
    "Frank's Fuel": {'lat': 36.073973, 'lon': 24.839702},
    "Frydos Autosupply n' More": {'lat': 36.059369, 'lon': 24.90562},
    'Gelatogalore': {'lat': 36.059646, 'lon': 24.862919},
    'General Grocer': {'lat': 36.061867, 'lon': 24.858542},
    "Guy's Gyros": {'lat': 36.059577, 'lon': 24.898624},
    'Hallowed Grounds': {'lat': 36.06366, 'lon': 24.885912},
    'Hippokampos': {'lat': 36.063403, 'lon': 24.875128},
    "Jack's Magical Beans": {'lat': 36.067489, 'lon': 24.874383},
    'Kalami Kafenion': {'lat': 36.059051, 'lon': 24.872579},
    "Katerina's Cafe": {'lat': 36.054222, 'lon': 24.900414},
    'Kronos Mart': {'lat': 36.067105, 'lon': 24.848757},
    'Kronos Pipe and Irrigation': {'lat': 36.057661, 'lon': 24.868783},
    'Maximum Iron and Steel': {'lat': 36.064306, 'lon': 24.83973},
    'Nationwide Refinery': {'lat': 36.058448, 'lon': 24.885514},
    "Octavio's Office Supplies": {'lat': 36.054012, 'lon': 24.874803},
    'Ouzeri Elian': {'lat': 36.053054, 'lon': 24.872961},
    'Roberts and Sons': {'lat': 36.065218, 'lon': 24.851994},
    "Shoppers' Delight": {'lat': 36.063546, 'lon': 24.876699},
    'Stewart and Sons Fabrication': {'lat': 36.055398, 'lon': 24.885375},
    'U-Pump': {'lat': 36.068423, 'lon': 24.868627}
}


def calculate_distance(lat1, lon1, lat2, lon2):
    return np.sqrt(((lat1 - lat2) * 111.0) ** 2 + ((lon1 - lon2) * 111.0 * np.cos(np.radians(lat1))) ** 2)


def main():
    print("正在加载基础数据并启动时空碰撞引擎...")
    cc_df = pd.read_csv(os.path.join(DATA_DIR, 'cc_data.csv'), encoding='latin1')
    gps_df = pd.read_csv(os.path.join(DATA_DIR, 'gps.csv'), encoding='latin1')
    personnel_df = pd.read_csv(os.path.join(DATA_DIR, 'car-assignments.csv'), encoding='latin1')

    # 时间与坐标格式化
    cc_time_col = 'timestamp' if 'timestamp' in cc_df.columns else 'tiemstamp'
    cc_df['timestamp'] = pd.to_datetime(cc_df[cc_time_col])
    cc_df = cc_df.sort_values('timestamp').copy()

    gps_df['Timestamp'] = pd.to_datetime(gps_df['Timestamp'])
    gps_df = gps_df.sort_values('Timestamp').copy()

    cc_df = cc_df[cc_df['location'].isin(LOCATION_COORDS.keys())].copy()
    cc_df['cc_lat'] = cc_df['location'].apply(lambda x: LOCATION_COORDS[x]['lat'])
    cc_df['cc_lon'] = cc_df['location'].apply(lambda x: LOCATION_COORDS[x]['lon'])

    gps_df = gps_df.rename(columns={'lat': 'gps_lat', 'long': 'gps_lon'})

    unique_ccs = cc_df['last4ccnum'].unique()
    truck_ids = [101, 104, 105, 106, 107]
    company_cars = sorted([int(x) for x in personnel_df['CarID'].dropna().unique() if int(x) not in truck_ids])
    all_cars = company_cars + truck_ids

    hit_matrix = []

    # 构建所有55张卡与所有40辆车的全排列碰撞矩阵
    for cc_id in unique_ccs:
        target_txns = cc_df[cc_df['last4ccnum'] == cc_id].copy()
        total_txns = len(target_txns)

        for car_id in all_cars:
            car_gps = gps_df[gps_df['id'] == car_id].copy()
            if car_gps.empty:
                continue

            merged = pd.merge_asof(
                target_txns, car_gps,
                left_on='timestamp', right_on='Timestamp',
                direction='nearest', tolerance=pd.Timedelta('15min')
            )
            valid_matches = merged.dropna(subset=['Timestamp']).copy()

            hits = 0
            if not valid_matches.empty:
                valid_matches['distance_km'] = calculate_distance(
                    valid_matches['cc_lat'], valid_matches['cc_lon'],
                    valid_matches['gps_lat'], valid_matches['gps_lon']
                )
                hits = (valid_matches['distance_km'] <= 0.25).sum()

            hit_matrix.append({
                'CC_ID': cc_id, 'Car_ID': car_id, 'Total_Txns': total_txns,
                'Hits': hits, 'Hit_Rate': hits / total_txns
            })

    df_hits = pd.DataFrame(hit_matrix)

    assignments = []
    assigned_ccs = set()
    assigned_cars = set()

    # 阶段一：35辆专属配车严格最优绑定
    df_company = df_hits[df_hits['Car_ID'].isin(company_cars)].sort_values(
        by=['Hit_Rate', 'Hits'], ascending=[False, False]
    )

    for _, row in df_company.iterrows():
        cc = row['CC_ID']
        car = row['Car_ID']
        if car not in assigned_cars and cc not in assigned_ccs and row['Hits'] > 0:
            assignments.append({
                'last4ccnum': cc, 'Matched_CarID': car, 'Total_Txns': row['Total_Txns'],
                'Hits': row['Hits'], 'Hit_Rate': round(row['Hit_Rate'] * 100, 2),
                'Match_Logic': '专属配车基准绑定'
            })
            assigned_cars.add(car)
            assigned_ccs.add(cc)

    # 阶段二：处理剩余20张卡 还原物理真相
    unassigned_ccs = set(unique_ccs) - assigned_ccs

    for cc in unassigned_ccs:
        cc_hits = df_hits[df_hits['CC_ID'] == cc].sort_values(
            by=['Hit_Rate', 'Hits'], ascending=[False, False]
        )
        best_match = cc_hits.iloc[0]

        # 只要产生过1次以上空间重合就进行业务归类
        if best_match['Hits'] > 0:
            car = best_match['Car_ID']
            logic = '公共卡车调用' if car in truck_ids else '次级卡从属绑定'
            assignments.append({
                'last4ccnum': cc, 'Matched_CarID': car, 'Total_Txns': best_match['Total_Txns'],
                'Hits': best_match['Hits'], 'Hit_Rate': round(best_match['Hit_Rate'] * 100, 2),
                'Match_Logic': logic
            })
        else:
            # 彻底没有轨迹的幽灵卡 这就是那2个拼车或步行的人
            assignments.append({
                'last4ccnum': cc, 'Matched_CarID': np.nan, 'Total_Txns': best_match['Total_Txns'],
                'Hits': 0, 'Hit_Rate': 0.0, 'Match_Logic': '无物理轨迹匹配'
            })

    result_df = pd.DataFrame(assignments)

    # 注入人事元数据
    personnel_df['FullName'] = personnel_df.apply(lambda r: f"{r['FirstName']} {r['LastName']}", axis=1)
    valid_personnel = personnel_df.dropna(subset=['CarID']).drop_duplicates(subset=['CarID'])
    info_cols = ['FullName', 'CurrentEmploymentType', 'CurrentEmploymentTitle']
    car_info_map = valid_personnel.set_index('CarID')[info_cols].to_dict('index')

    final_rows = []
    for _, row in result_df.iterrows():
        car_id = row['Matched_CarID']
        row_dict = row.to_dict()

        if pd.isna(car_id):
            row_dict['FullName'] = '无车基层员工'
            row_dict['CurrentEmploymentType'] = '未知'
            row_dict['CurrentEmploymentTitle'] = '未知'
            row_dict['Vehicle_Type'] = '无关联车辆'
        elif car_id in truck_ids:
            row_dict['FullName'] = '未定业务人员'
            row_dict['CurrentEmploymentType'] = '跨部门调用'
            row_dict['CurrentEmploymentTitle'] = '现场作业'
            row_dict['Vehicle_Type'] = '公共卡车'
        else:
            p_info = car_info_map.get(car_id, {})
            row_dict['FullName'] = p_info.get('FullName', '系统外人员')
            row_dict['CurrentEmploymentType'] = p_info.get('CurrentEmploymentType', '未知部门')
            row_dict['CurrentEmploymentTitle'] = p_info.get('CurrentEmploymentTitle', '未知职务')
            row_dict['Vehicle_Type'] = '公司专属配车'

        final_rows.append(row_dict)

    final_df = pd.DataFrame(final_rows)
    final_df = final_df.sort_values(by=['Vehicle_Type', 'Hit_Rate'], ascending=[True, False])

    final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"数据重构完毕 55张信用卡全量映射已输出至 {OUTPUT_FILE}")


if __name__ == '__main__':
    main()