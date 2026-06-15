# tasks/task5.py
import pandas as pd
import numpy as np
import networkx as nx
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import math

# =====================================================
# 数据加载（原5.1所需）
# =====================================================
gps_data = pd.read_csv("data/gps.csv")
cc_data = pd.read_csv("data/cc_data.csv")

try:
    task3_mapping = pd.read_csv("data/task3_all_mapping.csv", encoding="utf-8")
except:
    try:
        task3_mapping = pd.read_csv("data/task3_all_mapping.csv", encoding="gbk")
    except:
        task3_mapping = pd.read_csv("data/task3_all_mapping.csv", encoding="latin1")

try:
    relation_df = pd.read_csv("data/task4_final_relation.csv")
except:
    relation_df = pd.DataFrame(columns=["source", "target", "score"])

gps_data["Timestamp"] = pd.to_datetime(gps_data["Timestamp"], format="%m/%d/%Y %H:%M:%S")
cc_data["timestamp"] = pd.to_datetime(cc_data["timestamp"], format="%m/%d/%Y %H:%M")

# =====================================================
# 地图边界 & 地点坐标
# =====================================================
MAP_BOUNDS = {
    "x_range": [24.82450, 24.91000],
    "y_range": [36.04500, 36.09550]
}

LOCATION_COORDS = {
    "Abila Airport": {"lat": 36.081632, "lon": 24.850282},
    "Abila Scrapyard": {"lat": 36.075326, "lon": 24.846182},
    "Abila Zacharo": {"lat": 36.058322, "lon": 24.872587},
    "Ahaggo Museum": {"lat": 36.076644, "lon": 24.87751},
    "Albert's Fine Clothing": {"lat": 36.076436, "lon": 24.85777},
    "Bean There Done That": {"lat": 36.081632, "lon": 24.850482},
    "Brew've Been Served": {"lat": 36.056108, "lon": 24.903002},
    "Brewed Awakenings": {"lat": 36.055088, "lon": 24.87758},
    "Carlyle Chemical Inc.": {"lat": 36.059161, "lon": 24.882402},
    "Chostus Hotel": {"lat": 36.070683, "lon": 24.895213},
    "Coffee Cameleon": {"lat": 36.054664, "lon": 24.889801},
    "Coffee Shack": {"lat": 36.074216, "lon": 24.8606443},
    "Desafio Golf Course": {"lat": 36.091349, "lon": 24.864464},
    "Frank's Fuel": {"lat": 36.073973, "lon": 24.839702},
    "Frydos Autosupply n' More": {"lat": 36.059369, "lon": 24.90562},
    "Gelatogalore": {"lat": 36.059646, "lon": 24.862919},
    "General Grocer": {"lat": 36.061867, "lon": 24.858542},
    "Guy's Gyros": {"lat": 36.059577, "lon": 24.898624},
    "Hallowed Grounds": {"lat": 36.06366, "lon": 24.885912},
    "Hippokampos": {"lat": 36.063403, "lon": 24.875128},
    "Jack's Magical Beans": {"lat": 36.067489, "lon": 24.874383},
    "Kalami Kafenion": {"lat": 36.059051, "lon": 24.872579},
    "Katerina's Cafe": {"lat": 36.054222, "lon": 24.900414},
    "Kronos Mart": {"lat": 36.067105, "lon": 24.848757},
    "Kronos Pipe and Irrigation": {"lat": 36.057661, "lon": 24.868783},
    "Maximum Iron and Steel": {"lat": 36.064306, "lon": 24.83973},
    "Nationwide Refinery": {"lat": 36.058448, "lon": 24.885514},
    "Octavio's Office Supplies": {"lat": 36.054012, "lon": 24.874803},
    "Ouzeri Elian": {"lat": 36.053054, "lon": 24.872961},
    "Roberts and Sons": {"lat": 36.065218, "lon": 24.851994},
    "Shoppers' Delight": {"lat": 36.063546, "lon": 24.876699},
    "Stewart and Sons Fabrication": {"lat": 36.055398, "lon": 24.885375},
    "U-Pump": {"lat": 36.068423, "lon": 24.868627}
}


# =============================================================================
# [全局常量] 视觉美学与布局配置
# =============================================================================
# 扩展版莫兰迪色卡（用于多选嫌疑人时分配专属颜色）
MORANDI_PALETTE = [
    "#7A9D8C",  # 莫兰迪绿 (默认主色)
    "#B98B82",  # 柔砖红
    "#8D99AE",  # 雾霾蓝
    "#D4A373",  # 浅驼色
    "#9E9E9E",  # 质感灰
    "#A8BFAF",  # 浅灰绿
    "#D9C5B2",  # 奶茶色
    "#C5A3FF",  # 柔紫色
]
MORANDI_SUB_NODE = "#E0E0E0"  # 单选模式下的外围普通节点（淡灰）
BG_PURE_WHITE = "#FFFFFF"  # 图表纯白背景
TEXT_GRAY = "#4A4A4A"  # 柔和深灰文字
CHART_HEIGHT = 480  # 统一图表高度，精准消除底部白边


# =============================================================================
# [核心引擎] 任务五：联合调查分析系统动态回调
# =============================================================================
@callback(
    [Output("t5-map", "figure"),
     Output("t5-network", "figure")],
    [Input("t5-date-checklist", "value"),  # 接收日期列表，例如 ["ALL"] 或 ["2014-01-06"]
     Input("t5-person-checklist", "value")]  # 接收人员列表
)
def update_dashboard(selected_dates, selected_persons):
    # 初始化两块无形画布
    map_fig = go.Figure()
    net_fig = go.Figure()

    # 容错处理：确保 selected_dates 始终是一个列表
    if not selected_dates:
        selected_dates = ["ALL"]

    # 1. 安全拦截：当调查名单为空时，渲染干净的旅游地图底板和空白网络图
    if not selected_persons:
        map_fig.add_layout_image(
            dict(source="/assets/MC2-tourist.jpg",
                 xref="x", yref="y",
                 x=MAP_BOUNDS["x_range"][0], y=MAP_BOUNDS["y_range"][1],
                 sizex=MAP_BOUNDS["x_range"][1] - MAP_BOUNDS["x_range"][0],
                 sizey=MAP_BOUNDS["y_range"][1] - MAP_BOUNDS["y_range"][0],
                 sizing="stretch", layer="below")
        )
        map_fig.update_layout(
            autosize=False, height=CHART_HEIGHT,
            paper_bgcolor=BG_PURE_WHITE, plot_bgcolor=BG_PURE_WHITE,
            showlegend=False, margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(range=MAP_BOUNDS["x_range"], visible=False),
            yaxis=dict(range=MAP_BOUNDS["y_range"], visible=False)
        )
        net_fig.update_layout(
            autosize=False, height=CHART_HEIGHT,
            paper_bgcolor=BG_PURE_WHITE, plot_bgcolor=BG_PURE_WHITE,
            xaxis=dict(visible=False), yaxis=dict(visible=False), margin=dict(l=0, r=0, t=0, b=0)
        )
        return map_fig, net_fig

    # 2. 色彩矩阵分配：为每一位被选中的员工绑定一个永不混淆的专属莫兰迪色
    person_colors = {
        person: MORANDI_PALETTE[i % len(MORANDI_PALETTE)]
        for i, person in enumerate(selected_persons)
    }

    # ==================== 左侧：时空轨迹与消费重叠分析 ====================
    for i, person in enumerate(selected_persons):
        # 获取该员工的人事档案映射
        person_rows = task3_mapping[task3_mapping["FullName"] == person]
        if person_rows.empty:
            continue

        car_id = person_rows["Matched_CarID"].iloc[0]
        cc_list = person_rows["last4ccnum"].astype(str).unique()
        current_color = person_colors[person]

        # 【核心新增】：为每位员工计算一个专属的极小经纬度偏移量（Jitter）
        # 让多人的星标围绕中心点呈环形散开。0.00015 是偏移半径，可根据底图比例尺微调。
        angle = i * (2 * math.pi / len(selected_persons)) if len(selected_persons) > 0 else 0
        offset_lat = 0.00015 * math.sin(angle)
        offset_lon = 0.00015 * math.cos(angle)

        # --- 数据切片：动态支持多日期过滤 ---
        gps_filtered = gps_data[gps_data["id"] == car_id].copy()
        if "ALL" not in selected_dates:
            gps_filtered = gps_filtered[gps_filtered["Timestamp"].dt.strftime("%Y-%m-%d").isin(selected_dates)]
        gps_filtered = gps_filtered.sort_values("Timestamp")

        cc_filtered = cc_data[cc_data["last4ccnum"].astype(str).isin(cc_list)].copy()
        if "ALL" not in selected_dates:
            cc_filtered = cc_filtered[cc_filtered["timestamp"].dt.strftime("%Y-%m-%d").isin(selected_dates)]

        # --- 图层绘制：专属颜色双重覆盖 ---
        # 绘制 GPS 轨迹折线（GPS 本身自带物理位置的离散性，无需人工偏移）
        if not gps_filtered.empty:
            map_fig.add_trace(go.Scatter(
                x=gps_filtered["long"], y=gps_filtered["lat"],
                mode="lines+markers",
                line=dict(color=current_color, width=2.5),
                marker=dict(size=4, color=current_color),
                name=f"{person} 轨迹"
            ))

        # 绘制信用卡消费星标（附加偏移量，解决完全重叠问题）
        lats, lons, texts = [], [], []
        for _, row in cc_filtered.iterrows():
            loc = row["location"]
            if loc in LOCATION_COORDS:
                # 在绝对坐标的基础上，加上该员工专属的微量偏移
                lats.append(LOCATION_COORDS[loc]["lat"] + offset_lat)
                lons.append(LOCATION_COORDS[loc]["lon"] + offset_lon)
                texts.append(f"<b>调查对象: {person}</b><br>消费地点: {loc}<br>交易时间: {row['timestamp']}")

        if lats:
            map_fig.add_trace(go.Scatter(
                x=lons, y=lats, mode="markers",
                marker=dict(size=18, color=current_color, symbol="star", opacity=0.9,
                            line=dict(width=1, color=BG_PURE_WHITE)),
                text=texts, hoverinfo="text",
                name=f"{person} 消费"
            ))

    # 封装地图全局配置
    map_fig.add_layout_image(
        dict(source="/assets/MC2-tourist.jpg", xref="x", yref="y",
             x=MAP_BOUNDS["x_range"][0], y=MAP_BOUNDS["y_range"][1],
             sizex=MAP_BOUNDS["x_range"][1] - MAP_BOUNDS["x_range"][0],
             sizey=MAP_BOUNDS["y_range"][1] - MAP_BOUNDS["y_range"][0],
             sizing="stretch", layer="below")
    )
    map_fig.update_layout(
        autosize=False, height=CHART_HEIGHT,
        paper_bgcolor=BG_PURE_WHITE, plot_bgcolor=BG_PURE_WHITE, showlegend=False, margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(range=MAP_BOUNDS["x_range"], visible=False),
        yaxis=dict(range=MAP_BOUNDS["y_range"], visible=False)
    )

    # ==================== 右侧：自适应情报网络图 ====================
    G = nx.Graph()

    if len(selected_persons) == 1:
        # 模式一：深挖单人关系网（自身 + 潜藏密切关系 Top 10）
        main_person = selected_persons[0]
        rel = relation_df[(relation_df["source"] == main_person) | (relation_df["target"] == main_person)]
        rel = rel.sort_values("score", ascending=False).head(10)

        G.add_node(main_person, color=person_colors[main_person], size=26)
        for _, row in rel.iterrows():
            other = row["target"] if row["source"] == main_person else row["source"]
            G.add_node(other, color=MORANDI_SUB_NODE, size=16)
            G.add_edge(main_person, other, weight=row["score"])

    else:
        # 模式二：群体合谋排查（仅展示选中嫌疑人内部的互相勾连）
        for person in selected_persons:
            G.add_node(person, color=person_colors[person], size=24)

        rel = relation_df[relation_df["source"].isin(selected_persons) & relation_df["target"].isin(selected_persons)]
        for _, row in rel.iterrows():
            G.add_edge(row["source"], row["target"], weight=row["score"])

    # 网络图拓扑解算与视觉渲染
    if len(G.nodes()) == 0:
        pass  # 无节点时直接跳过渲染
    elif len(G.nodes()) == 1:
        pos = {list(G.nodes())[0]: (0, 0)}
    else:
        pos = nx.spring_layout(G, seed=42, k=1.5)

    weights = [G[u][v].get('weight', 1) for u, v in G.edges()]
    max_w = max(weights) if weights else 1
    min_w = min(weights) if weights else 0

    # 渲染关系连线：越密切的线越实、越粗
    for u, v in G.edges():
        w = G[u][v].get('weight', 1)
        intensity = 0.3 + 0.7 * ((w - min_w) / (max_w - min_w + 1e-5)) if max_w > min_w else 0.7
        edge_color = f"rgba(122, 157, 140, {intensity})"

        x0, y0 = pos[u]
        x1, y1 = pos[v]
        net_fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None], mode="lines",
            line=dict(color=edge_color, width=1 + intensity * 3),
            hoverinfo="none"
        ))

    # 渲染人员节点：色彩直接同步左侧地图
    node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
    for node in G.nodes():
        if node in pos:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            node_color.append(G.nodes[node]["color"])
            node_size.append(G.nodes[node]["size"])

    if node_x:
        net_fig.add_trace(go.Scatter(
            x=node_x, y=node_y, mode="markers+text",
            text=node_text, textposition="top center",
            marker=dict(size=node_size, color=node_color, line=dict(color=BG_PURE_WHITE, width=1.5)),
            textfont=dict(size=10, color=TEXT_GRAY)
        ))

    net_fig.update_layout(
        autosize=False, height=CHART_HEIGHT,
        paper_bgcolor=BG_PURE_WHITE, plot_bgcolor=BG_PURE_WHITE,
        showlegend=False, margin=dict(l=15, r=15, t=15, b=15),
        xaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        yaxis=dict(visible=False)
    )

    return map_fig, net_fig



# =====================================================
# 选择器选项（原5.1）
# =====================================================
persons = sorted(
    task3_mapping[~task3_mapping["FullName"].isin(["未定业务人员", "无车基层员工"])]
    ["FullName"].dropna().unique()
)
dates = sorted(gps_data["Timestamp"].dt.strftime("%Y-%m-%d").dropna().unique())


# 1. 在调用函数生成图表后，立即强制覆盖排版属性
event1_map_fig, event1_net_fig = update_dashboard(
    selected_dates=["2014-01-12", "2014-01-19"],
    selected_persons=["Orhan Strum", "Varja Lagos", "Nils Calixto", "Ada Campo-Corrente"]
)

# 核心修复：重置预生成图表的自适应开关，并缩小内部固定高度以适配展示区块
event1_map_fig.update_layout(autosize=True, height=340, margin=dict(l=0, r=0, t=0, b=0))
event1_net_fig.update_layout(autosize=True, height=340, margin=dict(l=0, r=0, t=0, b=0))

event2_map_fig, event2_net_fig = update_dashboard(
    selected_dates=["2014-01-12"],
    selected_persons=["Orhan Strum", "Lars Azada", "Vira Frente", "Ada Campo-Corrente", "Axel Calzas", "Gustav Cazar"]
)

# 强制覆盖为自适应宽高与紧凑间距
event2_map_fig.update_layout(autosize=True, height=340, margin=dict(l=0, r=0, t=0, b=0))
event2_net_fig.update_layout(autosize=True, height=340, margin=dict(l=0, r=0, t=0, b=0))

event3_map_fig, event3_net_fig = update_dashboard(
    selected_dates=["2014-01-13"],
    selected_persons=["Nils Calixto"]
)

# 强制覆盖为自适应宽高与紧凑间距
event3_map_fig.update_layout(autosize=True, height=340, margin=dict(l=0, r=0, t=0, b=0))
event3_net_fig.update_layout(autosize=True, height=340, margin=dict(l=0, r=0, t=0, b=0))

event5_map_fig, event5_net_fig = update_dashboard(
    selected_dates=["2014-01-18"],
    selected_persons=["Nils Calixto", "Sven Flecha", "Isande Borrasca", "Lucas Alcazar", "Hennie Osvaldo", "Bertrand Ovan"]
)

# 强制覆盖为自适应宽高与紧凑间距
event5_map_fig.update_layout(autosize=True, height=340, margin=dict(l=0, r=0, t=0, b=0))
event5_net_fig.update_layout(autosize=True, height=340, margin=dict(l=0, r=0, t=0, b=0))

# =====================================================
# 总布局（融合5.1 + 5.2~5.4）
# =====================================================
def get_layout():
    return html.Div([
        dbc.Row([
            # ========== 左侧目录 ==========
            dbc.Col([
                html.Div([
                    html.H5("目录", className="fw-bold mb-3"),
                    html.Ul([
                        # 5.1 联合调查分析系统
                        html.Li(html.A("5.1 联合调查分析系统", href="#section-5-1",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        # 5.2 可疑地点风险排名
                        html.Li(html.A("5.2 可疑地点风险排名", href="#section-5-2",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        # 5.3 核心事件复盘
                        html.Li(html.A("5.3 核心事件复盘", href="#section-5-3",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        html.Ul([
                            html.Li(html.A("5.3.1 Kronos Mart凌晨异常交易", href="#section-5-3-1",
                                           className="text-decoration-none text-muted small d-block mt-1")),
                            html.Li(html.A("5.3.2 Hippokampos异常聚集", href="#section-5-3-2",
                                           className="text-decoration-none text-muted small d-block mt-1")),
                            html.Li(html.A("5.3.3 Frydos—Ouzeri人车分离", href="#section-5-3-3",
                                           className="text-decoration-none text-muted small d-block mt-1")),
                            html.Li(html.A("5.3.4 Katerina's Cafe聚集群", href="#section-5-3-4",
                                           className="text-decoration-none text-muted small d-block mt-1")),
                            html.Li(html.A("5.3.5 Abila Airport 高危异常消费与公共卡车隐秘物流链", href="#section-5-3-5",
                                           className="text-decoration-none text-muted small d-block mt-1")),
                        ], className="list-unstyled ms-3"),
                        # 5.4 调查结论与不确定性
                        html.Li(html.A("5.4 调查结论与不确定性", href="#section-5-4",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                    ], className="list-unstyled")
                ], className="sticky-top pt-4")
            ], width=3, className="border-end border-light pe-4"),

            # ========== 右侧正文 ==========
            dbc.Col([
                html.H2("任务五：异常事件联合调查分析", className="mb-4 mt-4 text-primary"),
                html.Hr(),

                # ---- 5.1 联合调查分析系统 ----
                html.H3("5.1 联合调查分析系统", id="section-5-1"),
                html.P(
                    "该系统深度融合人员身份与物理轨迹以及财务消费和社交网络，旨在实现重点调查对象的多维度时空行为轨迹重叠分析。系统具备灵活的交叉筛选与多目标动态比对能力，左侧空间视图在真实地理底板上精准叠加选定人员的车辆行驶路线与线下商铺消费星标，并为不同嫌疑人分配专属色彩以便于直观剥离复杂线索。右侧拓扑视图则同步渲染自适应的情报关联结构，当仅锁定单一调查对象时，系统会自动深挖并呈现与其隐藏联系最为紧密的前十名核心人员，若同时圈定多名目标，网络将智能聚焦并揭示该特定群体内部的隐秘交往闭环。",
                    className="text-muted"),

                # 控制面板表头
                dbc.Row([
                    dbc.Col(html.Label("调查日期", className="fw-bold"), width=3),
                    dbc.Col(html.Label("嫌疑人名单", className="fw-bold"), width=9)
                ], className="mb-2"),

                # 控制面板输入区
                dbc.Row([
                    # 日期选择改为 Checklist，并与右侧高度强制锁定对齐
                    dbc.Col(
                        html.Div([
                            dcc.Checklist(
                                id="t5-date-checklist",  # 注意 ID 已更改
                                options=[{"label": "ALL", "value": "ALL"}] +
                                        [{"label": d, "value": d} for d in dates],
                                value=["ALL"],  # 默认传出列表格式
                                # 设置为 block 让日期竖向排列更清晰
                                labelStyle={"display": "block", "cursor": "pointer", "marginBottom": "5px",
                                            "color": "#4A4A4A"},
                                inputStyle={"marginRight": "8px"}
                            )
                        ], style={
                            "height": "150px",  # 关键：将 maxHeight 改为固定的 height
                            "overflowY": "auto",
                            "border": "1px solid #ced4da",
                            "padding": "10px",
                            "borderRadius": "0.25rem",
                            "backgroundColor": "#f8f9fa"
                        }), width=3
                    ),
                    # 人员选择框也固定高度
                    dbc.Col(
                        html.Div([
                            dcc.Checklist(
                                id="t5-person-checklist",
                                options=[{"label": p, "value": p} for p in persons],
                                value=[],
                                labelStyle={"display": "inline-block", "cursor": "pointer", "marginRight": "20px",
                                            "marginBottom": "5px", "color": "#4A4A4A"},
                                inputStyle={"marginRight": "5px"}
                            )
                        ], style={
                            "height": "150px",  # 关键：与左侧日期框保持绝对一致
                            "overflowY": "auto",
                            "border": "1px solid #ced4da",
                            "padding": "10px",
                            "borderRadius": "0.25rem",
                            "backgroundColor": "#f8f9fa"
                        }), width=9
                    )
                ], className="mb-4"),

                # 图表展示区：将 700px 修正为 450px（或 480px 留点呼吸空间），消灭底部白边
                dbc.Row([
                    dbc.Col(dcc.Graph(id="t5-map", style={"height": "480px"}), width=6),
                    dbc.Col(dcc.Graph(id="t5-network", style={"height": "480px"}), width=6)
                ]),

                # ---- 5.2 可疑地点风险排名 ----
                html.H3("5.2 可疑地点风险排名", id="section-5-2", className="mt-5 pt-3 border-top"),
                html.P("基于任务1-4的综合证据，以下为风险排名前十的地点。", className="text-muted"),

                dbc.Table(
                    [
                        html.Thead(
                            html.Tr([
                                html.Th("排名", className="text-center py-3",
                                        style={"backgroundColor": "#7a8b8c", "color": "white", "border": "none"}),
                                html.Th("地点名称", className="text-center py-3",
                                        style={"backgroundColor": "#7a8b8c", "color": "white", "border": "none"}),
                                html.Th("关联核心事件", className="text-center py-3",
                                        style={"backgroundColor": "#7a8b8c", "color": "white", "border": "none"}),
                                html.Th("主要风险特征", className="text-center py-3",
                                        style={"backgroundColor": "#7a8b8c", "color": "white", "border": "none"})
                            ])
                        ),
                        html.Tbody([
                            html.Tr([
                                html.Td(html.Span("1", className="badge bg-danger rounded-pill"),
                                        className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("Kronos Mart", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#f0f7f4", "color": "#2c3e50"}),
                                html.Td("事件一", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("凌晨集群、无会员卡、无车辆解释", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"})
                            ]),
                            html.Tr([
                                html.Td(html.Span("2", className="badge bg-danger rounded-pill"),
                                        className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("Frydos Autosupply n' More", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#ffffff", "color": "#2c3e50"}),
                                html.Td("事件三", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("极端高额(10k)、人卡车彻底分离", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"})
                            ]),
                            html.Tr([
                                html.Td(html.Span("3", className="badge bg-danger rounded-pill"),
                                        className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("Kronos Pipe and Irrigation", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#f0f7f4", "color": "#2c3e50"}),
                                html.Td("事件四", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("工业采购与车辆位置反复冲突", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"})
                            ]),
                            html.Tr([
                                html.Td(html.Span("4", className="badge bg-warning text-dark rounded-pill"),
                                        className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("Katerina's Cafe", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#ffffff", "color": "#2c3e50"}),
                                html.Td("事件五", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("跨部门夜间长期聚集", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"})
                            ]),
                            html.Tr([
                                html.Td(html.Span("5", className="badge bg-warning text-dark rounded-pill"),
                                        className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("Hippokampos", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#f0f7f4", "color": "#2c3e50"}),
                                html.Td("事件二", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("长期聚集与人车规律性分离", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"})
                            ]),
                            html.Tr([
                                html.Td("6", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("Albert's Fine Clothing", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#ffffff", "color": "#2c3e50"}),
                                html.Td("事件二", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("高频隐蔽车辆集中停放地", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"})
                            ]),
                            html.Tr([
                                html.Td("7", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("Ouzeri Elian", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#f0f7f4", "color": "#2c3e50"}),
                                html.Td("事件三", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("异常交易后的身份与轨迹恢复节点", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"})
                            ]),
                            html.Tr([
                                html.Td("8", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("Maximum Iron and Steel", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#ffffff", "color": "#2c3e50"}),
                                html.Td("事件四", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("公共卡车与高额采购链集散地", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"})
                            ]),
                            html.Tr([
                                html.Td("9", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("Carlyle Chemical Inc.", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#f0f7f4", "color": "#2c3e50"}),
                                html.Td("事件四", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"}),
                                html.Td("高额工业采购盲区", className="text-center align-middle",
                                        style={"backgroundColor": "#f0f7f4"})
                            ]),
                            html.Tr([
                                html.Td("10", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("Abila Airport", className="text-center align-middle fw-bold",
                                        style={"backgroundColor": "#ffffff", "color": "#2c3e50"}),
                                html.Td("其他线索", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"}),
                                html.Td("多卡共享会员卡，待进一步核验", className="text-center align-middle",
                                        style={"backgroundColor": "#ffffff"})
                            ]),
                        ])
                    ],
                    bordered=False,
                    hover=True,
                    responsive=True,
                    className="mb-5 shadow-sm",
                    style={"fontSize": "0.95rem", "border": "1px solid #dce8e2", "borderRadius": "8px",
                           "overflow": "hidden"}
                ),

                # ---- 5.3 核心事件复盘 ----
                html.H3("5.3 核心事件复盘", id="section-5-3", className="mt-5 pt-3 border-top"),

                html.H5("5.3.1 Kronos Mart 两次凌晨异常交易事件", id="section-5-3-1",
                        className="fw-bold text-primary mt-4"),
                html.P(
                    "本次调查首先锁定了 Kronos Mart 在2014年1月12日和1月19日凌晨出现的两组异常交易，该地点在正常营业时段主要承担日常零售功能，但两次事件均发生在凌晨3时左右，明显偏离其常规消费时间分布。",
                    className="text-muted"),
                html.Ul([
                    html.Li([html.Strong("1月12日凌晨："),
                             "员工 Orhan Strum 关联的8156号信用卡产生异常交易，并且于12日晚其所在群体的活动时间明显提前，同时发现现有GPS未能提供支持其到达该地的轨迹，交易也缺乏会员卡流水。"]),
                    html.Li([html.Strong("1月19日凌晨："),
                             "Varja Lagos、Nils Calixto 与 Ada Campo Corrente 在 Kronos Mart 先后完成无会员卡交易，且三人配发车辆前一日晚间后无匹配轨迹，交易后进入较长时间记录空窗，直至白天分散恢复。"])
                ]),

                # 2. 规范外层容器与底部间距 (将 mb-4 加在 dbc.Col 上以推开下方的元素)
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            dcc.Graph(
                                id="t5-event1-map",
                                figure=event1_map_fig,
                                style={"width": "100%", "height": "100%"},  # 让图表乖乖填满父容器
                                config={
                                    "displayModeBar": True,
                                    "responsive": True,
                                    "toImageButtonOptions": {"format": "png", "scale": 2}
                                }  # 强制开启前端响应式
                            ),
                            style={"height": "350px"},  # 将高度限制放在外部 Div 上，确保边框能完美包裹
                            className="shadow-sm bg-white p-1 rounded border"
                        )
                    ], md=6, className="mb-4"),  # 这里的 mb-4 才是真正能推开底部结论框的关键

                    dbc.Col([
                        html.Div(
                            dcc.Graph(
                                id="t5-event1-network",
                                figure=event1_net_fig,
                                style={"width": "100%", "height": "100%"},
                                config={
                                    "displayModeBar": True,
                                    "responsive": True,
                                    "toImageButtonOptions": {"format": "png", "scale": 2}
                                }
                            ),
                            style={"height": "350px"},
                            className="shadow-sm bg-white p-1 rounded border"
                        )
                    ], md=6, className="mb-4")
                ]),

                dbc.Alert([
                    html.I(className="bi bi-bullseye me-2"),
                    html.Strong("结论："),
                    "Kronos Mart 是本次调查中风险等级最高的可疑地点，现有证据确认相关信用卡集中出现，但不足以证明持卡人使用了何种交通方式，可能被用于夜间非正常交易、卡片集中使用或隐蔽人员接触。"
                ], color="secondary", className="shadow-sm"),

                # 事件二
                html.H5("5.3.2 Hippokampos—Albert's Fine Clothing 规律性人车分离", id="section-5-3-2",
                        className="fw-bold text-primary mt-5"),
                html.P(
                    "对 1 月 12 日进行凌晨交易的 Orhan Strum 进行活动轨迹探究，识别出一组规律性的晚间人车分离模式，其经常于 21：30 在 Hippokampos 产生消费，但其配发车辆同期主要停靠在 Albert's Fine Clothing 附近。进一步提取该时间在 Hippokampos 消费的其他员工，发现 Lars Azada、Vira Frente、Ada Campo Corrente、Axel Calzas 以及 Gustav Cazar 均有相似的人车分离行为，且在历次聚集记录中，未在 HippoKampos 产生消费的人员均会在同一时间段于 Albert's Fine Clothing 留下消费记录，具备协同互补特征。同时，发现 1 月 12 日，即前述凌晨异常交易发生当晚，该群体的整体聚集时间自惯常的晚 21 时提前至晚 19 时左右。",
                    className="text-muted"),

                # 事件二：双图并排，套用事件一的自适应完美排版
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            dcc.Graph(
                                id="t5-event2-map",
                                figure=event2_map_fig,
                                style={"width": "100%", "height": "100%"},  # 图表自适应撑满
                                config={
                                    "displayModeBar": True,
                                    "responsive": True,
                                    "toImageButtonOptions": {"format": "png",  "scale": 2}
                                }
                            ),
                            style={"height": "350px"},  # 外部容器锁定高度以包裹阴影边框
                            className="shadow-sm bg-white p-1 rounded border"
                        )
                    ], md=6, className="mb-4"),  # mb-4 用于推开下方的结论框

                    dbc.Col([
                        html.Div(
                            dcc.Graph(
                                id="t5-event2-network",
                                figure=event2_net_fig,
                                style={"width": "100%", "height": "100%"},
                                config={
                                    "displayModeBar": True,
                                    "responsive": True,
                                    "toImageButtonOptions": {"format": "png", "scale": 2}
                                }
                            ),
                            style={"height": "350px"},
                            className="shadow-sm bg-white p-1 rounded border"
                        )
                    ], md=6, className="mb-4")
                ]),

                dbc.Alert([
                    html.I(className="bi bi-info-circle-fill me-2"),
                    html.Strong("结论："),
                    "1月12日晚该群体的常规活动时间由约21时提前至约19时，随后发生13号凌晨交易，基于此推断 Hippokampos 和 Albert's Fine Clothing 分别是稳定的非正式聚集与车辆集中停放区域，但是否真实承担了凌晨事件的前置组织功能，仍需进一步证据确认。"
                ], color="secondary", className="shadow-sm"),

                # 事件三（段落已合并为单段）
                html.H5("5.3.3 Frydos—Ouzeri Elian 的9551信用卡人卡车分离链", id="section-5-3-3",
                        className="fw-bold text-primary mt-5"),
                html.P(
                    "对 1 月 19 日 进行凌晨交易的信用卡 9551 卡主 Nils Calixto 进行进一步调查，发现其 1 月 13 日 19:20 在 Frydos 产生 10,000.00 美元极端高额交易，且无对应会员卡记录。同期，其分配车辆 1 在距离2.21公里外的 Ouzeri Elian 附近，仅十分钟后，9551在 Ouzeri Elian 产生28.75美元餐饮消费，并且重新使用会员卡，呈现出在 Frydos脱轨而在 Ouzeri 正常的模式。",
                    className="text-muted"),

                # 事件三：双图并排，套用自适应完美排版
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            dcc.Graph(
                                id="t5-event3-map",
                                figure=event3_map_fig,
                                style={"width": "100%", "height": "100%"},  # 图表自适应撑满
                                config={
                                    "displayModeBar": True,
                                    "responsive": True,
                                    "toImageButtonOptions": {"format": "png", "scale": 2}
                                }
                            ),
                            style={"height": "350px"},  # 外部容器锁定高度以包裹阴影边框
                            className="shadow-sm bg-white p-1 rounded border"
                        )
                    ], md=6, className="mb-4"),  # mb-4 用于推开下方的结论框

                    dbc.Col([
                        html.Div(
                            dcc.Graph(
                                id="t5-event3-network",
                                figure=event3_net_fig,
                                style={"width": "100%", "height": "100%"},
                                config={
                                    "displayModeBar": True,
                                    "responsive": True,
                                    "toImageButtonOptions": {"format": "png",  "scale": 2}
                                }
                            ),
                            style={"height": "350px"},
                            className="shadow-sm bg-white p-1 rounded border"
                        )
                    ], md=6, className="mb-4")
                ]),

                dbc.Alert([
                    html.I(className="bi bi-bullseye me-2"),
                    html.Strong("结论："),
                    "Frydos 由于在该地发生大额资金转移被判定为高风险异常交易地点，Ouzeri 视为异常交易后重新进入正常身份模式的关键节点，而 Nils Calixto 随后又参与 19 日凌晨事件，调查价值极高。"
                ], color="secondary", className="shadow-sm"),

                # 事件四：双图并排，套用自适应完美排版
                html.H5("5.3.4 Katerina's Cafe 跨部门夜间聚集与人车分离事件群", id="section-5-3-5",
                        className="fw-bold text-primary mt-5"),
                html.P(
                    "进一步对 Nils Calixto 进行调查，发现 1 月 6 日至 19 日，以 Nils Calixto、Sven Flecha、Isande Borrasca、Lucas Alcazar、Hennie Osvaldo、Bertrand Ovan 等为核心的十余名跨部门员工在晚间频繁于 Katerina's Cafe 产生消费，部分车辆异地停放或在交易期间保持长时间静止出现 GPS 空窗。",
                    className="text-muted"),
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            dcc.Graph(
                                id="t5-event5-map",
                                figure=event5_map_fig,
                                style={"width": "100%", "height": "100%"},  # 图表自适应撑满父容器
                                config={
                                    "displayModeBar": True,
                                    "responsive": True,
                                    "toImageButtonOptions": {"format": "png",  "scale": 2}
                                }
                            ),
                            style={"height": "350px"},  # 外部容器锁定高度以包裹阴影边框
                            className="shadow-sm bg-white p-1 rounded border"
                        )
                    ], md=6, className="mb-4"),  # mb-4 用于将结论框向下完美推开

                    dbc.Col([
                        html.Div(
                            dcc.Graph(
                                id="t5-event5-network",
                                figure=event5_net_fig,
                                style={"width": "100%", "height": "100%"},
                                config={
                                    "displayModeBar": True,
                                    "responsive": True,
                                    "toImageButtonOptions": {"format": "png",  "scale": 2}
                                }
                            ),
                            style={"height": "350px"},
                            className="shadow-sm bg-white p-1 rounded border"
                        )
                    ], md=6, className="mb-4")
                ]),

                dbc.Alert([
                    html.I(className="bi bi-info-circle-fill me-2"),
                    html.Strong("结论："),
                    "该地点属于重复事件群，存在稳定的跨部门非正式聚集和人车分离行为，更适合被定义为高风险人员交集点和关系验证点，辅助解释凌晨交易与卡片共享。"
                ], color="secondary", className="shadow-sm"),



                # 事件五（无图片，段落合并）
                html.H5("5.3.5 Abila Airport 高危异常消费与公共卡车隐秘物流链", id="section-5-3-4",
                        className="fw-bold text-primary mt-5"),

                html.P(
                    "在对城市边缘高危地点 Abila Airport 进行异常消费轨迹复核时，我们首先锁定了频繁爆发接近五千美元单笔上限交易的卡号3506、9220与2276。由于这几张信用卡在常规员工轿车映射表中处于完全独立、无配车登记的状态，导致其持卡人的具体身份信息在初始阶段无法得知。为破解其物理出行谜题，我们将审计视线穿透至公司重型物流资产，最终成功抓取到了关键的车辆匹配记录。",
                    className="text-muted mb-2", style={"textAlign": "justify", "lineHeight": "1.8"}),

                html.P(
                    "数据显示上述人员实际上公然违反了公司禁令，频繁驾驶本该用于纯粹公务的101号与106号公务卡车前往机场。此外，4530号信用卡也暴露出与107号卡车绑定的类似异动。卡车在机场货运区域的频繁滞留，与幽灵卡号8642等大额反常资金动向在时空上高度咬合，证实该群体已彻底将严禁私用的重型公务车辆演变为私人地下走私网络的物流承载工具，涉嫌严重的职务犯罪。",
                    className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),

                dbc.Alert([
                    html.I(className="bi bi-info-circle-fill me-2"),
                    html.Strong("结论："),
                    "未知持卡人信用卡8642、3506、9220、2276频繁在 Abila Airport 爆发超三千美元异常消费，且全量匹配证实其违规调用公司101及106号卡车。推测其利用公务车辆构建走私物流通路进行职务犯罪，彻底暴露出公共卡车调度的责任盲区。后续调查应直接锁定涉事卡车的调度审批记录。"
                ], color="secondary", className="shadow-sm mt-4"),



                # ---- 5.4 调查结论与不确定性 ----
                html.H3("5.4 调查结论与不确定性", id="section-5-4", className="mt-5 pt-3 border-top"),
                html.P(
                    "综合上述分析，Kronos Mart、Frydos Autosupply、Kronos Pipe 三处地点风险最高，建议进行深入调查。同时，由于公共卡车与无车人员的数据盲区，部分结论仍存在不确定性。",
                    className="text-muted"),

                # 事件研判工作台（小部件，可选保留，但为避免冲突，此处不放置原来5.1部分的交互）
                # 若需保留原新内容中的研判工作台，可加在此处，但ID已独立，不会干扰。
            ], width=9, className="ps-5")
        ])
    ])

layout = get_layout
