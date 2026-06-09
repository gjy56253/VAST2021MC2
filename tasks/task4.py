# tasks/task4.py
import json
from pathlib import Path

import pandas as pd
import numpy as np
import networkx as nx
from networkx.readwrite import json_graph
import plotly.graph_objects as go
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc

# 强制接管底层 JSON 引擎，彻底消除 orjson 报错
import plotly.io as pio

pio.json.config.default_engine = 'json'

# ==========================================
# 0. 数据加载与图预处理 (直接从 data 目录读取 JSON)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def load_preprocessed_data():
    """从 data 根目录加载轻量化的 JSON/CSV 缓存"""
    required_files = [
        DATA_DIR / "task4_final_relation.csv",
        DATA_DIR / "task4_strong_relation.csv",
        DATA_DIR / "task4_social_graph.json",
        DATA_DIR / "task4_communities.json",
        DATA_DIR / "task4_degree.csv",
        DATA_DIR / "task4_betweenness.csv",
    ]
    for f in required_files:
        if not f.exists():
            print(f"警告：预处理文件缺失 {f}")
            return pd.DataFrame(), pd.DataFrame(), nx.Graph(), [], {}, pd.DataFrame()

    final_relation = pd.read_csv(DATA_DIR / "task4_final_relation.csv")
    strong_relation = pd.read_csv(DATA_DIR / "task4_strong_relation.csv")

    with open(DATA_DIR / "task4_social_graph.json", "r", encoding='utf-8') as f:
        graph_data = json.load(f)
        G = json_graph.node_link_graph(graph_data)

    with open(DATA_DIR / "task4_communities.json", "r", encoding='utf-8') as f:
        communities = [set(c) for c in json.load(f)]

    deg_df = pd.read_csv(DATA_DIR / "task4_degree.csv")
    deg = dict(zip(deg_df["employee"], deg_df["degree"]))
    between_df = pd.read_csv(DATA_DIR / "task4_betweenness.csv")

    return final_relation, strong_relation, G, communities, deg, between_df


# 全局加载
final_relation, strong_relation, G, communities, deg, between_df = load_preprocessed_data()

# 预计算节点坐标与属性
nodes = list(G.nodes())
node_community = {}
for idx, comm in enumerate(communities):
    for node in comm:
        node_community[node] = idx

deg_values = [deg.get(node, 0) for node in nodes]
between_values = [
    between_df[between_df["employee"] == node]["Betweenness"].values[0] if not between_df.empty and node in between_df[
        "employee"].values else 0 for node in nodes]

# 固定网络布局坐标
if not G.nodes:
    pos = {}
    node_x, node_y = [], []
else:
    pos = nx.spring_layout(G, k=1.3, iterations=100, seed=42)
    node_x = [pos[node][0] for node in nodes]
    node_y = [pos[node][1] for node in nodes]


# ==========================================
# 1. 布局模块 (Layout)
# ==========================================
def get_layout():
    return html.Div([
        dbc.Row([
            # ==========================================
            # 左侧栏：文章目录
            # ==========================================
            dbc.Col([
                html.Div([
                    html.H5("目录", className="fw-bold mb-3"),
                    html.Ul([
                        # 4.1 一级目录
                        html.Li(html.A("4.1 社交网络拓扑总览", href="#section-4-1",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        html.Ul([
                            html.Li(html.A("4.1.1 交互式关系图谱检索", href="#section-4-1-1",
                                           className="text-decoration-none text-muted")),
                            html.Li(html.A("4.1.2 非正式关联行为审计详情", href="#section-4-1-2",
                                           className="text-decoration-none text-muted")),
                        ], className="list-unstyled ms-3"),

                        # 4.2 一级目录
                        html.Li(html.A("4.2 非正式社团行为解构", href="#section-4-2",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        html.Ul([
                            html.Li(html.A("4.2.1 非正式社团核心角色画像", href="#section-4-2-1",
                                           className="text-decoration-none text-muted")),
                        ], className="list-unstyled ms-3"),
                    ], className="list-unstyled")
                ], className="sticky-top pt-4")
            ], width=3, className="border-end border-light pe-4"),

            # ==========================================
            # 右侧栏：正文内容
            # ==========================================
            dbc.Col([
                html.H2("任务四：非正式社交网络分析", className="mb-4 mt-4 text-primary"),
                html.Hr(),

                # --- 4.1 社交网络拓扑总览 ---
                html.H3("4.1 社交网络拓扑总览", id="section-4-1", className="mb-3"),
                html.P(
                    "基于私人时段的车辆共停留、共移动以及线下餐饮消费共现数据，系统过滤了居家与偶然性噪声，并引入跨部门权重参数，构建了完全独立于正式组织架构的员工私人社交图谱。",
                    className="text-justify text-muted"
                ),

                # 交互控制台
                dbc.Card(dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("社团检索：", className="small text-muted fw-bold"),
                            dcc.Dropdown(
                                id="community-dropdown",
                                # 【核心修改】手动拼接一个全量选项
                                options=[{"label": "展示全量网络拓扑", "value": None}] +
                                        [{"label": f"非正式聚类 {i + 1} (规模 {len(c)}人)", "value": i}
                                         for i, c in enumerate(communities)],
                                value=None,  # 默认值设为 None，对应“全量”
                                placeholder="展示全量网络拓扑",
                                className="mt-1"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("边缘权重剥离阈值：", className="small text-muted fw-bold"),
                            dcc.Slider(
                                id="weight-slider",
                                min=0,
                                max=float(strong_relation["score"].max()) if not strong_relation.empty else 1,
                                step=0.1,
                                value=0,
                                marks={0: "全量连边",
                                       round(float(
                                           strong_relation["score"].max()) / 2 if not strong_relation.empty else 0.5,
                                             1): "中等强度",
                                       round(float(strong_relation["score"].max()) if not strong_relation.empty else 1,
                                             1): "核心死党"}
                            )
                        ], width=6)
                    ])
                ]), className="mb-3 shadow-sm border-0 bg-light"),

                # 网络图谱
                dbc.Card(dbc.CardBody([
                    dcc.Loading(dcc.Graph(id="social-network-graph", style={"height": "650px"},
                                          config={'toImageButtonOptions': {'format': 'png', 'scale': 3}}))
                ]), className="mb-3 shadow-sm border-0 bg-white"),

                # 核心发现文本
                html.P(
                    "员工真实的非正式社交网络呈现出显著的双核主导与长尾分布并存的结构特征，聚类 1 与聚类 2 构成了规模庞大的团体，吸纳了组织内绝大多数的社交活跃节点，揭示了强烈的派系化结盟倾向，是主导内部非官方信息与资源流转的绝对核心阵地；相比之下，聚类 3 表现为具有特定共性与极高内部闭环特征的中型亚文化圈层，而其余极小规模的双人搭档或单人节点则处于非正式网络的边缘游离带。",
                    className="text-justify mb-5"
                ),

                # 4.1.2 核心非正式结盟证据簿
                html.H4("4.1.2 非正式关联行为审计详情", id="section-4-1-2", className="mt-4 mb-3"),
                html.P(
                    "系统通过综合驻留轨迹、出行轨迹与消费共现频次等多维数据对节点间的行为绑定深度进行量化评估，并针对跨职能部门间的联动行为实施了差异化增益加权，旨在通过实时联动的交互视图直观揭示非正式组织架构下的关键协作脉络。",
                    className="text-justify text-muted"
                ),
                dbc.Card(dbc.CardBody([
                    html.Div(id="relation-table-container")
                ]), className="mb-5 shadow-sm border-0 bg-white"),

                # --- 4.2 非正式社团行为解构 ---
                html.H3("4.2 非正式社团行为解构", id="section-4-2", className="mt-5 mb-3 pt-3 border-top"),
                html.P(
                    "通过多维拓扑属性解析，我们精准刻画了社团背后的意见领袖与情报中介，旨在揭示非正式权力结构的情况。",
                    className="text-justify text-muted"
                ),

                # 4.2.1 非正式社团核心角色画像
                html.H3("4.2 非正式社团核心角色画像", id="section-4-2", className="mt-5 mb-3 pt-3 border-top"),
                html.P(
                    "本分析通过中心性战略四象限图将员工的度中心性与介数中心性进行二维映射，度中心性衡量个体的直接社交动员能力，介数中心性衡量个体的跨圈层情报流转能力。通过该分布图可识别不同职能位置的员工，右上象限代表同时具备高动员能力与高信息中转能力的节点，左上象限代表具备高信息中转能力但动员范围有限的节点，右下象限代表仅具备高动员能力的节点，左下象限代表各项指标均较低的普通节点。",
                    className="text-justify text-muted mb-2"),

                dbc.Card(dbc.CardBody([
                    dcc.Loading(dcc.Graph(id="role-scatter-graph", style={"height": "500px"}))
                ]), className="mb-4 shadow-sm border-0 bg-white"),

                html.P(
                    "网络中大多数节点集中分布于左下象限，表明多数员工在非正式社交结构中处于边缘位置；而右下象限存在大量高动员能力的节点，显示组织内部存在多个活跃的局部社交群体；值得关注的是右上象限的节点，如 Ada Campo Corrente，Isak Baza 和 Felix Resumir，这些节点同时具备高社交动员力与高信息中转力，是该非正式网络中最关键的核心，应当作为合规性审查的重点关注对象。",
                    className="text-justify mb-5"),

            ], width=9, className="ps-5")
        ])
    ])


layout = get_layout()


# ==========================================
# 交互回调模块 (Callbacks)
# ==========================================
@callback(
    Output("social-network-graph", "figure"),
    Output("relation-table-container", "children"),
    Output("role-scatter-graph", "figure"),
    Input("community-dropdown", "value"),
    Input("weight-slider", "value")
)
def update_all_visuals(comm_idx, min_weight):
    if not G.nodes:
        return go.Figure(), html.Div("暂无数据"), go.Figure()

    # 1. 网络图更新逻辑
    if comm_idx is not None:
        selected_nodes = list(communities[comm_idx])
        edges_to_keep = [(u, v) for u, v, d in G.edges(data=True)
                         if u in selected_nodes and v in selected_nodes and d.get("weight", 0) >= min_weight]
        node_color = ["#E74C3C" if node in selected_nodes else "#F2F4F4" for node in nodes]
        node_size = [deg.get(node, 0) * 35 + 15 for node in nodes]
        sub_edge_x, sub_edge_y = [], []
        for u, v in edges_to_keep:
            x0, y0 = pos[u]; x1, y1 = pos[v]
            sub_edge_x.extend([x0, x1, None]); sub_edge_y.extend([y0, y1, None])
        edge_trace = go.Scatter(x=sub_edge_x, y=sub_edge_y, line=dict(width=1.5, color='#BDC3C7'), mode='lines')
        node_trace = go.Scatter(
            x=node_x, y=node_y, mode='markers+text', text=nodes, textposition="top center",
            textfont=dict(size=10, color="#2C3E50"),
            marker=dict(size=node_size, color=node_color, line=dict(width=1.5, color='white')),
            hoverinfo='text',
            hovertext=[f"<b>{node}</b><br>度中心性: {deg.get(node, 0):.2f}<br>介数中心性: {between_values[i]:.3f}" for i, node in enumerate(nodes)]
        )
    else:
        edges_to_keep = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("weight", 0) >= min_weight]
        sub_edge_x, sub_edge_y = [], []
        for u, v, _ in edges_to_keep:
            x0, y0 = pos[u]; x1, y1 = pos[v]
            sub_edge_x.extend([x0, x1, None]); sub_edge_y.extend([y0, y1, None])
        edge_trace = go.Scatter(x=sub_edge_x, y=sub_edge_y, line=dict(width=0.8, color='#D5DBDB'), mode='lines')
        discrete_colors = ['#5DADE2', '#F4D03F', '#48C9B0', '#AF7AC5', '#E59866', '#EC7063']
        node_color = [discrete_colors[node_community.get(node, 0) % len(discrete_colors)] for node in nodes]
        node_size = [deg.get(node, 0) * 35 + 15 for node in nodes]
        node_trace = go.Scatter(
            x=node_x, y=node_y, mode='markers+text', text=nodes, textposition="top center",
            textfont=dict(size=10, color="#34495E"),
            marker=dict(size=node_size, color=node_color, line=dict(width=1, color='white')),
            hoverinfo='text',
            hovertext=[f"<b>{node}</b><br>社团: {node_community.get(node, -1) + 1}<br>度中心性: {deg.get(node, 0):.2f}<br>介数中心性: {between_values[i]:.3f}" for i, node in enumerate(nodes)]
        )

    fig_net = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(showlegend=False, hovermode='closest', margin=dict(b=0, l=0, r=0, t=0), plot_bgcolor='white', paper_bgcolor='white', xaxis=dict(visible=False), yaxis=dict(visible=False)))

    # 2. 表格逻辑 (配色优化版)
    filtered_rel = strong_relation[strong_relation["score"] >= min_weight].copy()
    if comm_idx is not None:
        community_nodes = communities[comm_idx]
        filtered_rel = filtered_rel[
            filtered_rel["source"].isin(community_nodes) & filtered_rel["target"].isin(community_nodes)]

    # 构造表格行
    rows = []
    for i, (_, row) in enumerate(filtered_rel.head(12).iterrows()):
        bg_color = "#f0f7f4" if i % 2 == 0 else "#ffffff"
        rows.append(html.Tr([
            html.Td(row["source"], className="text-center align-middle", style={"backgroundColor": bg_color}),
            html.Td(row["target"], className="text-center align-middle", style={"backgroundColor": bg_color}),
            html.Td(f"{row['score']:.3f}", className="text-center align-middle", style={"backgroundColor": bg_color})
        ]))

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("起点", className="text-center"),
            html.Th("终点", className="text-center"),
            html.Th("分数", className="text-center")
        ]), className="table-light"),
        html.Tbody(rows)
    ], bordered=False, hover=True, size="sm", className="mb-0")

    # 3. 散点图逻辑
    fig_scatter = go.Figure()
    colors = ["#E74C3C" if (comm_idx is not None and node in communities[comm_idx]) else "#BDC3C7" for node in nodes]
    sizes = [15 if (comm_idx is not None and node in communities[comm_idx]) else 10 for node in nodes]
    fig_scatter.add_trace(go.Scatter(x=deg_values, y=between_values, mode='markers+text', text=nodes, marker=dict(size=sizes, color=colors, opacity=0.8), textposition="top center", textfont=dict(size=9), hoverinfo='text', hovertext=[f"<b>{n}</b><br>度中心性: {d:.2f}<br>介数中心性: {b:.3f}" for n, d, b in zip(nodes, deg_values, between_values)]))
    fig_scatter.add_vline(x=np.mean(deg_values) if deg_values else 0, line_dash="dash", line_color="#7F8C8D")
    fig_scatter.add_hline(y=np.mean(between_values) if between_values else 0, line_dash="dash", line_color="#7F8C8D")
    fig_scatter.update_layout(title="中心性战略定性四象限图", xaxis_title="度中心性", yaxis_title="介数中心性", plot_bgcolor='white', paper_bgcolor='white')

    return fig_net, table, fig_scatter