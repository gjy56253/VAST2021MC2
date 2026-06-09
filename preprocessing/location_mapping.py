import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import math
import warnings

warnings.filterwarnings('ignore')

# ====================== 最终最优参数 ======================
STAY_MIN_DURATION = 120  # 最小停留时间：2分钟
STAY_MAX_SPEED = 8  # 最大停留速度：8km/h
NUM_CLUSTERS = 34  # 明确知道有34个地点，强制生成34个簇
MATCH_TIME_WINDOW = 600  # 匹配时间窗口：10分钟


# ====================== 工具函数 ======================
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# ====================== Step 1: GPS数据预处理 ======================
def preprocess_gps(gps_path):
    print("Step 1/5: 正在预处理GPS数据...")
    gps_df = pd.read_csv(gps_path, encoding='latin1')
    gps_df.columns = ['Timestamp', 'CarID', 'lat', 'lon']
    gps_df['Timestamp'] = pd.to_datetime(gps_df['Timestamp'])
    gps_df = gps_df.sort_values(['CarID', 'Timestamp']).reset_index(drop=True)
    gps_df['time_diff'] = gps_df.groupby('CarID')['Timestamp'].diff().dt.total_seconds()
    gps_df['prev_lat'] = gps_df.groupby('CarID')['lat'].shift(1)
    gps_df['prev_lon'] = gps_df.groupby('CarID')['lon'].shift(1)
    gps_df['distance'] = gps_df.apply(
        lambda row: haversine_distance(row['prev_lat'], row['prev_lon'], row['lat'], row['lon'])
        if not pd.isna(row['prev_lat']) else 0,
        axis=1
    )
    gps_df['speed'] = gps_df.apply(
        lambda row: (row['distance'] / row['time_diff']) * 3.6
        if row['time_diff'] > 0 else 0,
        axis=1
    )
    print(f"✅ GPS数据预处理完成，共 {len(gps_df)} 条记录")
    return gps_df


# ====================== Step 2: 停留点检测 ======================
def detect_stay_points(gps_df):
    print("\nStep 2/5: 正在检测车辆停留点...")
    stay_points = []
    gps_df['is_stopped'] = gps_df['speed'] < STAY_MAX_SPEED

    for car_id, group in gps_df.groupby('CarID'):
        group = group.reset_index(drop=True)
        i = 0
        n = len(group)

        while i < n:
            if group.loc[i, 'is_stopped']:
                start_idx = i
                while i < n and group.loc[i, 'is_stopped']:
                    i += 1
                end_idx = i - 1

                duration = (group.loc[end_idx, 'Timestamp'] - group.loc[start_idx, 'Timestamp']).total_seconds()
                if duration >= STAY_MIN_DURATION:
                    center_lat = group.loc[start_idx:end_idx, 'lat'].mean()
                    center_lon = group.loc[start_idx:end_idx, 'lon'].mean()
                    stay_points.append({
                        'CarID': car_id,
                        'start_time': group.loc[start_idx, 'Timestamp'],
                        'end_time': group.loc[end_idx, 'Timestamp'],
                        'duration': duration,
                        'lat': round(center_lat, 6),
                        'lon': round(center_lon, 6)
                    })
            else:
                i += 1

    stay_points_df = pd.DataFrame(stay_points)
    print(f"✅ 停留点检测完成，共检测到 {len(stay_points_df)} 个停留点")
    return stay_points_df


# ====================== Step 3: K-Means聚类（完美替代DBSCAN） ======================
def cluster_stay_points(stay_points_df):
    print("\nStep 3/5: 正在对停留点进行K-Means聚类...")

    # K-Means聚类，强制生成正好34个簇
    kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=42, n_init=100)
    stay_points_df['cluster_id'] = kmeans.fit_predict(stay_points_df[['lat', 'lon']])

    num_clusters = len(stay_points_df['cluster_id'].unique())
    print(f"✅ K-Means聚类完成，共生成 {num_clusters} 个地点簇（目标：34个）")
    return stay_points_df


# ====================== Step 4: 一对一强制匹配算法 ======================
def build_cluster_location_map(stay_points_df, cc_path):
    print("\nStep 4/5: 正在建立簇与地点名称的一对一强制映射...")

    cc_df = pd.read_csv(cc_path, encoding='latin1')
    cc_df['timestamp'] = pd.to_datetime(cc_df['timestamp'])

    # 从信用卡数据中提取所有34个地点的完整列表
    all_locations = sorted(cc_df['location'].unique())
    all_clusters = sorted(stay_points_df['cluster_id'].unique())

    print(f"📊 待匹配：{len(all_clusters)} 个簇 ↔ {len(all_locations)} 个地点")

    # 构建匹配次数矩阵
    print("\n🔧 正在构建匹配次数矩阵...")
    match_matrix = np.zeros((len(all_clusters), len(all_locations)), dtype=int)

    for i, cluster_id in enumerate(all_clusters):
        cluster_stays = stay_points_df[stay_points_df['cluster_id'] == cluster_id]

        for _, stay in cluster_stays.iterrows():
            time_start = stay['start_time'] - pd.Timedelta(seconds=MATCH_TIME_WINDOW)
            time_end = stay['end_time'] + pd.Timedelta(seconds=MATCH_TIME_WINDOW)

            mask = (cc_df['timestamp'] >= time_start) & (cc_df['timestamp'] <= time_end)
            transactions = cc_df[mask]

            for _, txn in transactions.iterrows():
                j = all_locations.index(txn['location'])
                match_matrix[i][j] += 1

    # 一对一贪心匹配
    print("\n🎯 正在执行一对一强制匹配...")
    cluster_to_location = {}
    location_to_cluster = {}
    used_clusters = set()
    used_locations = set()

    while True:
        max_count = -1
        best_i = -1
        best_j = -1

        for i in range(len(all_clusters)):
            if i in used_clusters:
                continue
            for j in range(len(all_locations)):
                if j in used_locations:
                    continue
                if match_matrix[i][j] > max_count:
                    max_count = match_matrix[i][j]
                    best_i = i
                    best_j = j

        if max_count <= 0:
            break

        cluster_id = all_clusters[best_i]
        location = all_locations[best_j]
        cluster_to_location[cluster_id] = location
        location_to_cluster[location] = (cluster_id, max_count)
        print(f"✅ 匹配成功：{location} → 簇 {cluster_id} ({max_count} 次匹配)")

        used_clusters.add(best_i)
        used_locations.add(best_j)

    # 标记未匹配的簇和地点
    for cluster_id in all_clusters:
        if cluster_id not in cluster_to_location:
            cluster_to_location[cluster_id] = 'Unknown'

    for location in all_locations:
        if location not in location_to_cluster:
            location_to_cluster[location] = (None, 0)

    # 打印匹配统计
    print("\n📍 最终匹配结果统计：")
    print("=" * 60)
    matched_count = len([loc for loc in cluster_to_location.values() if loc != 'Unknown'])
    print(f"✅ 成功匹配 {matched_count}/{len(all_clusters)} 个簇")
    print(f"✅ 成功匹配 {matched_count}/{len(all_locations)} 个地点")
    print("=" * 60)

    return cluster_to_location, location_to_cluster, all_locations, cc_df


# ====================== Step 5: 生成最终结果 ======================
def generate_final_result(stay_points_df, cluster_map, output_path):
    print("\nStep 5/5: 正在生成最终结果文件...")
    stay_points_df['location'] = stay_points_df['cluster_id'].map(cluster_map)
    stay_points_df.to_csv(output_path, index=False)

    print("\n📊 最终结果统计：")
    print("=" * 50)
    print(f"总停留点数：{len(stay_points_df)}")
    print(f"成功匹配地点的停留点数：{len(stay_points_df[stay_points_df['location'] != 'Unknown'])}")
    print(f"匹配成功率：{len(stay_points_df[stay_points_df['location'] != 'Unknown']) / len(stay_points_df) * 100:.1f}%")
    print(f"结果已保存到：{output_path}")
    print("=" * 50)

    return stay_points_df


# ====================== 主程序 ======================
if __name__ == "__main__":
    GPS_PATH = "../data/gps.csv"
    CC_LOYALTY_PATH = "../data/cc_loyalty_matched.csv"
    OUTPUT_PATH = "../data/vehicle_stays.csv"

    print("=" * 70)
    print("VAST 2021 MC2 地点自动映射工具（K-Means完美版）")
    print("=" * 70)

    gps_df = preprocess_gps(GPS_PATH)
    stay_points_df = detect_stay_points(gps_df)
    stay_points_df = cluster_stay_points(stay_points_df)

    # 计算每个簇的质心经纬度
    cluster_centroids = stay_points_df.groupby('cluster_id')[['lat', 'lon']].mean().reset_index()
    centroid_dict = dict(zip(
        cluster_centroids['cluster_id'],
        zip(cluster_centroids['lat'].round(6), cluster_centroids['lon'].round(6))
    ))

    cluster_to_location, location_to_cluster, all_locations, cc_df = build_cluster_location_map(stay_points_df,
                                                                                                CC_LOYALTY_PATH)

    # 输出所有34个地点的完整信息
    print("\n" + "=" * 100)
    print("📋 所有34个地点的完整匹配信息表（按地点名称排序）")
    print("=" * 100)
    print(f"{'序号':<4} {'地点名称':<35} {'簇ID':<6} {'匹配次数':<8} {'质心纬度':<14} {'质心经度':<14}")
    print("-" * 100)

    for idx, location in enumerate(all_locations, 1):
        cluster_id, match_count = location_to_cluster[location]

        if cluster_id is not None and cluster_id in centroid_dict:
            lat, lon = centroid_dict[cluster_id]
            print(f"{idx:<4} {location:<35} {cluster_id:<6} {match_count:<8} {lat:<14.6f} {lon:<14.6f}")
        else:
            print(f"\033[31m{idx:<4} {location:<35} {'-':<6} {'0':<8} {'-':<14} {'-':<14}\033[0m")

    print("=" * 100)

    # 在这里添加手动匹配修正
    # location_to_cluster['Abila Airport'] = (25, 1)

    # 根据手动修正更新cluster_to_location
    for location, (cluster_id, _) in location_to_cluster.items():
        if cluster_id is not None:
            cluster_to_location[cluster_id] = location

    final_df = generate_final_result(stay_points_df, cluster_to_location, OUTPUT_PATH)

    print("\n🎉 所有步骤完成！")
    print("现在你可以使用 ../data/vehicle_stays.csv 进行Task2异常验证分析")