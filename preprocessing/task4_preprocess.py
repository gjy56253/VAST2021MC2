# preprocessing/task4_preprocess.py
import os
import json
from pathlib import Path
import pandas as pd
import numpy as np
import networkx as nx
from networkx.readwrite import json_graph
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import MinMaxScaler
from itertools import combinations
from collections import defaultdict


# ==========================================
# 1. 路径配置 (直接输出至 data 目录)
# ==========================================
def find_project_root(start_path, target_dir="data"):
    current = Path(start_path).resolve()
    for parent in [current] + list(current.parents):
        if (parent / target_dir).is_dir():
            return parent
    raise FileNotFoundError(f"找不到包含 '{target_dir}' 的目录")


CURRENT_FILE = Path(__file__).resolve()
BASE_DIR = find_project_root(CURRENT_FILE, "data")
DATA_DIR = BASE_DIR / "data"

# 输出路径定义
FINAL_RELATION_CSV = DATA_DIR / "task4_final_relation.csv"
STRONG_RELATION_CSV = DATA_DIR / "task4_strong_relation.csv"
GRAPH_JSON = DATA_DIR / "task4_social_graph.json"
COMMUNITIES_JSON = DATA_DIR / "task4_communities.json"
DEGREE_CSV = DATA_DIR / "task4_degree.csv"
BETWEEN_CSV = DATA_DIR / "task4_betweenness.csv"


def safe_read_csv(file_path):
    try:
        return pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception:
        try:
            return pd.read_csv(file_path, encoding='gbk')
        except Exception:
            return pd.read_csv(file_path, encoding='latin1')


def run_comprehensive_preprocessing():
    print("==================================================")
    print(" 开始执行: 真实员工全量非正式社交网络数据清洗 ")
    print("==================================================")

    # ==========================================
    # 2. 加载全量基准总表并过滤虚拟标签
    # ==========================================
    mapping_all = safe_read_csv(DATA_DIR / "task3_all_mapping.csv")

    # 1. 彻底清除 Pandas 带来的空值幽灵
    mapping_all['FullName'] = mapping_all['FullName'].replace(
        ['nan', 'NaN', 'None', '', ' ', float('nan')], np.nan
    )
    valid_mapping = mapping_all.dropna(subset=['FullName']).copy()
    valid_mapping['FullName'] = valid_mapping['FullName'].astype(str).str.strip()

    # 2. 核心隔离墙：剔除代表群体的“虚拟标签”
    exclude_names = ["未定业务人员", "无车基层员工"]
    valid_mapping = valid_mapping[~valid_mapping['FullName'].isin(exclude_names)]

    all_employees = valid_mapping['FullName'].unique().tolist()

    print(f"成功剔除空值与虚拟群体标签，锁定真实独立员工数: {len(all_employees)} 人")

    # 构建字典
    car_to_name = {}
    name_to_dept = {}
    carless_employees = set()

    for _, row in valid_mapping.iterrows():
        name = row['FullName']
        dept = str(row.get('CurrentEmploymentType', '未知部门')).strip()
        if dept in ['nan', 'NaN', 'None', '']:
            dept = '未知部门'
        name_to_dept[name] = dept

        car_id = row.get('Matched_CarID')
        if pd.notna(car_id) and str(car_id).strip() not in ['nan', 'NaN', 'None', '']:
            try:
                car_to_name[int(float(car_id))] = name
            except ValueError:
                pass
        else:
            carless_employees.add(name)

    # 确认真正的无车员工 (防止一人双行导致误判)
    employees_with_cars = set(car_to_name.values())
    carless_employees = carless_employees - employees_with_cars

    print(f"其中专属车辆有效绑定数: {len(car_to_name)} 辆 (对应 {len(employees_with_cars)} 名员工)")
    print(f"确认未分配车辆(无车)真实员工: {len(carless_employees)} 人")

    # ==========================================
    # 3. GPS 驻留与同行网络计算 (严查驻留时长)
    # ==========================================
    print("\n[步骤 1] 处理物理轨迹：严格过滤偶发相遇...")
    gps = safe_read_csv(DATA_DIR / "gps.csv")
    gps["Timestamp"] = pd.to_datetime(gps["Timestamp"])
    gps["hour"] = gps["Timestamp"].dt.hour
    gps["weekday"] = gps["Timestamp"].dt.weekday
    gps["date"] = gps["Timestamp"].dt.date

    social_gps = gps[(gps["hour"] >= 18) | (gps["hour"] <= 6) | (gps["weekday"] >= 5)].copy()

    coords = social_gps[["lat", "long"]].values
    db = DBSCAN(eps=0.0002, min_samples=10)
    social_gps["cluster"] = db.fit_predict(coords)

    social_gps = social_gps[social_gps["cluster"] != -1].copy()
    social_gps["time_bin"] = social_gps["Timestamp"].dt.floor("15min")

    pair_stay_durations = defaultdict(int)

    for (date_day, cluster), group in social_gps.groupby(["date", "cluster"]):
        car_time_map = defaultdict(set)
        for _, row in group.iterrows():
            try:
                car_id = int(row["id"])
                if car_id in car_to_name:
                    car_time_map[car_to_name[car_id]].add(row["time_bin"])
            except:
                pass

        employees_today = list(car_time_map.keys())
        if len(employees_today) < 2:
            continue

        for empA, empB in combinations(sorted(employees_today), 2):
            overlap_bins = car_time_map[empA].intersection(car_time_map[empB])
            # 必须持续驻留超过 2 个时间片（即 > 15分钟），否则视为路过
            if len(overlap_bins) >= 2:
                pair_stay_durations[(empA, empB)] += len(overlap_bins)

    print(f"提取到有效连续驻留的伴随关系对数: {len(pair_stay_durations)}")

    gps_relation_list = []
    for (empA, empB), weight in pair_stay_durations.items():
        gps_relation_list.append({
            "source": empA, "target": empB,
            "location_weight": weight * 1.0,
            "travel_weight": weight * 1.2
        })
    gps_rel_df = pd.DataFrame(gps_relation_list) if gps_relation_list else pd.DataFrame(
        columns=["source", "target", "location_weight", "travel_weight"])

    # ==========================================
    # 4. 线下消费网络计算 (高危场所加权 + 解决 1对多映射)
    # ==========================================
    print("\n[步骤 2] 处理财务消费网络并规避一人多卡冲突...")
    cc_loyalty_matched = safe_read_csv(DATA_DIR / "cc_loyalty_matched.csv")
    cc_loyalty_matched["timestamp"] = pd.to_datetime(cc_loyalty_matched["timestamp"])
    cc_loyalty_matched["date"] = cc_loyalty_matched["timestamp"].dt.date
    consume = cc_loyalty_matched.dropna(subset=["loyaltynum"]).copy()

    # 精准打补丁：将会员卡映射到人，并彻底剔除无效空卡号
    valid_mapping['loyaltynum'] = valid_mapping['loyaltynum'].astype(str).str.replace('.0', '', regex=False).str.strip()
    loyalty_to_name = dict(zip(valid_mapping["loyaltynum"], valid_mapping["FullName"]))
    loyalty_to_name.pop('nan', None)
    loyalty_to_name.pop('', None)
    loyalty_to_name.pop('NaN', None)

    consume_pairs = defaultdict(float)
    social_place_factors = {
        "Katerina's Cafe": 2.0,
        "Brew've Been Served": 1.8,
        "Gelatiamo": 1.5,
        "Kronos Pipe and Cigars": 1.8
    }

    for (date_day, location), group in consume.groupby(["date", "location"]):
        sorted_group = group.sort_values("timestamp").to_dict("records")
        factor = social_place_factors.get(location, 1.0)

        for i in range(len(sorted_group)):
            for j in range(i + 1, len(sorted_group)):
                time_delta_min = (sorted_group[j]["timestamp"] - sorted_group[i]["timestamp"]).total_seconds() / 60.0
                if time_delta_min > 30.0:
                    break

                cardA = str(sorted_group[i]["loyaltynum"]).strip()
                cardB = str(sorted_group[j]["loyaltynum"]).strip()

                if cardA in loyalty_to_name and cardB in loyalty_to_name:
                    nameA = loyalty_to_name[cardA]
                    nameB = loyalty_to_name[cardB]

                    # 核心拦截：如果是同一个人名下的两张卡互刷，直接无视
                    if nameA == nameB:
                        continue

                    pair = tuple(sorted([nameA, nameB]))
                    consume_pairs[pair] += factor

    print(f"提取到高置信线下财务共现关系对数: {len(consume_pairs)}")
    consume_relation_list = [{"source": p[0], "target": p[1], "consume_weight": w} for p, w in consume_pairs.items()]
    consume_rel_df = pd.DataFrame(consume_relation_list) if consume_relation_list else pd.DataFrame(
        columns=["source", "target", "consume_weight"])

    # ==========================================
    # 5. 异构网络重组：动态控权与跨部门结盟奖励
    # ==========================================
    print("\n[步骤 3] 整合多模态数据，注入无车人群逻辑与正式组织防线...")
    if gps_rel_df.empty and consume_rel_df.empty:
        print("危险：无有效关系产生！")
        return

    if gps_rel_df.empty:
        final_relation = consume_rel_df.copy()
        final_relation["location_weight"] = 0.0
        final_relation["travel_weight"] = 0.0
    elif consume_rel_df.empty:
        final_relation = gps_rel_df.copy()
        final_relation["consume_weight"] = 0.0
    else:
        final_relation = pd.merge(gps_rel_df, consume_rel_df, on=["source", "target"], how="outer").fillna(0)

    scaler = MinMaxScaler()
    weight_cols = ["location_weight", "travel_weight", "consume_weight"]
    for col in weight_cols:
        if final_relation[col].max() != final_relation[col].min():
            final_relation[col + "_norm"] = scaler.fit_transform(final_relation[[col]])
        else:
            final_relation[col + "_norm"] = 0.0

    final_scores = []
    for _, row in final_relation.iterrows():
        src, tgt = row["source"], row["target"]

        # 1. 动态权重：含无车人员的社交分数，由线下消费全权接管
        if src in carless_employees or tgt in carless_employees:
            base_score = row["consume_weight_norm"]
        else:
            base_score = 0.4 * row["location_weight_norm"] + 0.4 * row["travel_weight_norm"] + 0.2 * row[
                "consume_weight_norm"]

        # 2. 揭秘“非正式关系”：同部门予以工作削弱，跨部门暗中交往予以大幅奖励
        deptA = name_to_dept.get(src, "未知部门A")
        deptB = name_to_dept.get(tgt, "未知部门B")

        if deptA == deptB and deptA != "未知部门A":
            structure_factor = 0.8
        else:
            structure_factor = 1.2

        final_scores.append(base_score * structure_factor)

    final_relation["score"] = final_scores
    final_relation = final_relation.sort_values("score", ascending=False).reset_index(drop=True)
    final_relation.to_csv(FINAL_RELATION_CSV, index=False)

    score_threshold = final_relation["score"].quantile(0.75) if not final_relation.empty else 0.0
    strong_relation = final_relation[final_relation["score"] >= score_threshold].copy()
    strong_relation.to_csv(STRONG_RELATION_CSV, index=False)

    # ==========================================
    # 6. 图拓扑建模与标准化 JSON 导出 (终结 Pickle 时代)
    # ==========================================
    print("\n[步骤 4] 执行全量图拓扑解析与 JSON 序列化...")
    G = nx.Graph()

    # 锁定图的基石：填入所有真实独立员工，确保孤立节点不丢失
    for emp in all_employees:
        G.add_node(emp, department=name_to_dept.get(emp, "未知部门"))

    for _, row in strong_relation.iterrows():
        G.add_edge(row["source"], row["target"], weight=float(row["score"]))

    deg_dict = dict(G.degree(weight="weight"))
    between_dict = nx.betweenness_centrality(G, weight="weight")

    from networkx.algorithms.community import greedy_modularity_communities
    communities_sets = list(greedy_modularity_communities(G))
    communities_list = [list(c) for c in communities_sets]

    pd.DataFrame(list(deg_dict.items()), columns=['employee', 'degree']).to_csv(DEGREE_CSV, index=False)
    pd.DataFrame(list(between_dict.items()), columns=['employee', 'Betweenness']).to_csv(BETWEEN_CSV, index=False)

    with open(COMMUNITIES_JSON, 'w', encoding='utf-8') as f:
        json.dump(communities_list, f, ensure_ascii=False)

    graph_data = json_graph.node_link_data(G)
    with open(GRAPH_JSON, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, ensure_ascii=False)

    print("==================================================")
    print(f" 预处理引擎完美收官！数据已输出至: {DATA_DIR} ")
    print("==================================================")


if __name__ == "__main__":
    run_comprehensive_preprocessing()