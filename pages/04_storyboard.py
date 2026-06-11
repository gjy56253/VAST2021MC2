# pages/case_reconstruction.py
import json
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from networkx.readwrite import json_graph

# ---------- 页面注册 ----------
dash.register_page(__name__, name="案件还原", order=4)

# ==========================================
# 0. 常量与数据加载
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MAP_BOUNDS = {"x_range": [24.82450, 24.91000], "y_range": [36.04500, 36.09550]}

LOCATION_COORDS = {
    "Albert's Fine Clothing": {"lat": 36.076436, "lon": 24.85777},
    "Brew've Been Served": {"lat": 36.056108, "lon": 24.903002},
    "Carlyle Chemical Inc.": {"lat": 36.059161, "lon": 24.882402},
    "Desafio Golf Course": {"lat": 36.091349, "lon": 24.864464},
    "Frydos Autosupply n' More": {"lat": 36.059369, "lon": 24.90562},
    "General Grocer": {"lat": 36.061867, "lon": 24.858542},
    "Guy's Gyros": {"lat": 36.059577, "lon": 24.898624},
    "Hippokampos": {"lat": 36.063403, "lon": 24.875128},
    "Katerina's Cafe": {"lat": 36.054222, "lon": 24.900414},
    "Kronos Mart": {"lat": 36.067105, "lon": 24.848757},
    "Kronos Pipe and Irrigation": {"lat": 36.057661, "lon": 24.868783},
    "Maximum Iron and Steel": {"lat": 36.064306, "lon": 24.83973},
    "Ouzeri Elian": {"lat": 36.053054, "lon": 24.872961},
}

# 核心嫌疑人
SUSPECTS = {
    "Nils Calixto": {
        "cc": [9551, 6691, 2681], "loyalty": "L5777", "car": 1,
        "dept": "IT", "title": "Helpdesk", "color": "#E74C3C",
        "evidence": "$10,000 Frydos + Kronos Mart凌晨交易 + 16h电子静默",
        "danger": "极高",
    },
    "Ada Campo-Corrente": {
        "cc": [8332], "loyalty": "L8566", "car": 10,
        "dept": "Executive", "title": "SVP/CIO", "color": "#9B59B6",
        "evidence": "凌晨集群交易 + 卡片共享网络核心 + 社团桥接",
        "danger": "极高",
    },
    "Orhan Strum": {
        "cc": [8156], "loyalty": "L5224", "car": 32,
        "dept": "Executive", "title": "SVP/COO", "color": "#E67E22",
        "evidence": "Hippokampos聚集核心 + 首次凌晨异常交易",
        "danger": "高",
    },
    "Varja Lagos": {
        "cc": [3484], "loyalty": "L7761", "car": 23,
        "dept": "Security", "title": "Badging Office", "color": "#3498DB",
        "evidence": "门禁权限 + 凌晨集群交易首笔发起 + 10h电子静默",
        "danger": "高",
    },
}

SUSPECT_NAMES = set(SUSPECTS.keys())
SUSPECT_CC_SET = set()
for _info in SUSPECTS.values():
    SUSPECT_CC_SET.update(_info["cc"])

# 社团颜色
COMM_COLORS = ["#5DADE2", "#EC7063", "#58D68D", "#F4D03F", "#AF7AC5"]
# 阶段颜色
PHASE_COLORS = {
    "gather": "#3498DB", "escalate": "#E67E22", "fund": "#9B59B6",
    "act": "#E74C3C", "silence": "#2C3E50",
}


def _load_data():
    data = {}

    # 社交网络图
    graph_path = DATA_DIR / "task4_social_graph.json"
    if graph_path.exists():
        with open(graph_path, "r", encoding="utf-8") as f:
            gd = json.load(f)
            if "links" in gd and "edges" not in gd:
                gd["edges"] = gd["links"]
            data["G"] = json_graph.node_link_graph(gd)
    else:
        data["G"] = nx.Graph()

    # 社团
    comm_path = DATA_DIR / "task4_communities.json"
    if comm_path.exists():
        with open(comm_path, "r", encoding="utf-8") as f:
            data["communities"] = json.load(f)
    else:
        data["communities"] = []

    # 社交关系
    rel_path = DATA_DIR / "task4_final_relation.csv"
    data["relations"] = pd.read_csv(rel_path) if rel_path.exists() else pd.DataFrame()

    # 中心性
    for key, fname in [("degree", "task4_degree.csv"), ("betweenness", "task4_betweenness.csv")]:
        p = DATA_DIR / fname
        data[key] = pd.read_csv(p) if p.exists() else pd.DataFrame()

    # 信用卡+会员卡交易
    cc_path = DATA_DIR / "cc_loyalty_matched.csv"
    if cc_path.exists():
        df = pd.read_csv(cc_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", dayfirst=False, errors="coerce")
        df["Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=False, errors="coerce")
        data["cc_loyalty"] = df
    else:
        data["cc_loyalty"] = pd.DataFrame()

    # 车辆停留
    stays_path = DATA_DIR / "vehicle_stays.csv"
    if stays_path.exists():
        df = pd.read_csv(stays_path)
        df["start_time"] = pd.to_datetime(df["start_time"])
        df["end_time"] = pd.to_datetime(df["end_time"])
        data["stays"] = df
    else:
        data["stays"] = pd.DataFrame()

    # GPS
    gps_path = DATA_DIR / "gps.csv"
    if gps_path.exists():
        df = pd.read_csv(gps_path, usecols=["Timestamp", "id", "lat", "long"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        data["gps"] = df
    else:
        data["gps"] = pd.DataFrame()

    return data


DATA = _load_data()

# 预计算网络布局
G = DATA["G"]
if G.nodes:
    _pos = nx.spring_layout(G, k=1.8, iterations=120, seed=42)
else:
    _pos = {}

# 社团成员映射
_node_community = {}
for _idx, _comm in enumerate(DATA["communities"]):
    for _n in _comm:
        _node_community[_n] = _idx


# ==========================================
# 1. 图表构建函数
# ==========================================

def _build_narrative_flow():
    """五步流程图：聚集 → 升级 → 资金 → 行动 → 静默"""
    fig = go.Figure()

    # 莫兰迪低饱和绿色系配色（已替换好，柔和不艳丽）
    PHASE_COLORS = {
        "gather": "#83A598",
        "escalate": "#C9A888",
        "fund": "#A898A8",
        "act": "#BC8C80",
        "silence": "#4A5A54"
    }

    # ========== 修正后的流程图绘制代码 ==========
    # 已精简subtitle，只保留你指定的短句，无需换行，自动居中
    stages = [
        {"label": "规律聚集", "sub": "人车分离模式确立",
         "x": 0.6, "color": PHASE_COLORS["gather"]},
        {"label": "行动升级", "sub": "首次凌晨异常交易",
         "x": 2.8, "color": PHASE_COLORS["escalate"]},
        {"label": "资金准备", "sub": "$10,000 大额交易",
         "x": 5.0, "color": PHASE_COLORS["fund"]},
        {"label": "秘密行动", "sub": "Kronos Mart 集群交易",
         "x": 7.2, "color": PHASE_COLORS["act"]},
        {"label": "电子静默", "sub": "后错峰重现",
         "x": 9.4, "color": PHASE_COLORS["silence"]},
    ]

    # 连接箭头（适配放大后的大圆，箭头向内缩进）
    for i in range(len(stages) - 1):
        fig.add_annotation(
            x=stages[i]["x"] + 0.75, y=0.5,
            ax=stages[i + 1]["x"] - 0.75, ay=0.5,
            xref="x", yref="y", axref="x", ayref="y",
            arrowhead=2, arrowsize=1.8, arrowwidth=2.5,
            arrowcolor="#BDC3C7",
        )

    for s in stages:
        # 圆圈放大，完整包裹内部文字
        fig.add_trace(go.Scatter(
            x=[s["x"]], y=[0.5],
            mode="markers+text",
            marker=dict(size=66, color=s["color"], opacity=0.92,
                        line=dict(width=2.5, color="white")),
            text=[s["label"]],
            textposition="middle center",
            textfont=dict(size=14, color="white", family="Arial"),
            hoverinfo="text",
            hovertext=f"<b>{s['label']}</b>",
            showlegend=False,
        ))
        # 下方精简说明文字，天然水平居中，无换行干扰
        fig.add_trace(go.Scatter(
            x=[s["x"]], y=[-0.18],
            mode="text",
            text=[s["sub"]],
            textposition="top center",
            textfont=dict(size=10, color="#7F8C8D"),
            hoverinfo="skip", showlegend=False,
        ))

    # 画布布局适配
    fig.update_layout(
        xaxis=dict(visible=False, range=[-0.7, 10.4]),
        yaxis=dict(visible=False, range=[-0.38, 1.1]),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20, r=20, t=20, b=65),
        height=320,
    )
    return fig


def _build_key_timeline():
    """精简版宏观时间线（全参数合规 · 彻底修复所有报错）"""
    fig = go.Figure()

    # 你最终确定的事件文案
    events = [
        {"date": "1/6 - 1/15", "text": "Hippokampos出现人车分离规律聚集",
         "color": PHASE_COLORS["gather"]},
        {"date": "1/12  19:00", "text": "聚集时间由21时前移至19时",
         "color": PHASE_COLORS["escalate"]},
        {"date": "1/12  03:39", "text": "Orhan Strum于Kronos Mart交易$277",
         "color": PHASE_COLORS["escalate"]},
        {"date": "1/13  19:20", "text": "Nils Calixto于Frydos进行$10,000大额交易",
         "color": PHASE_COLORS["fund"]},
        {"date": "1/13  19:30", "text": "同卡于Ouzeri Elian交易$28.75恢复身份",
         "color": PHASE_COLORS["fund"]},
        {"date": "1/18  19:00", "text": "三名嫌疑人遗弃公司车辆",
         "color": PHASE_COLORS["act"]},
        {"date": "1/19  03:13", "text": "Varja Lagos于Kronos Mart交易$87.66",
         "color": PHASE_COLORS["act"]},
        {"date": "1/19  03:45", "text": "Nils Calixto于Kronos Mart交易$194.51",
         "color": PHASE_COLORS["act"]},
        {"date": "1/19  03:48", "text": "Ada Campo-Corrente于Kronos Mart交易$150.36",
         "color": PHASE_COLORS["act"]},
        {"date": "1/19  13:00+", "text": "错峰重现",
         "color": PHASE_COLORS["silence"]},
    ]

    y_labels = [e["date"] for e in events]
    colors = [e["color"] for e in events]

    # 1. 绘制拉长的横向条形图（宽度=3，空间充足）
    fig.add_trace(go.Bar(
        x=[3] * len(events),
        y=y_labels,
        orientation="h",
        marker=dict(color=colors, opacity=0.9, line=dict(width=1, color="white")),
        hoverinfo="skip",
        showlegend=False,
    ))

    # 2. 逐行渲染文本 + 自动适配文字颜色（解决列表/textcolor报错）
    for item in events:
        color_hex = item["color"]
        # 十六进制颜色转亮度，判断文字颜色
        r = int(color_hex[1:3], 16)
        g = int(color_hex[3:5], 16)
        b = int(color_hex[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000

        # 深色背景白字，浅色背景深灰字
        txt_color = "#FFFFFF" if brightness < 130 else "#2C3E50"

        # 单条独立文本轨迹，textfont 仅用合法参数 size / color
        fig.add_trace(go.Scatter(
            x=[1.5],          # 条形水平中点，实现居中
            y=[item["date"]],
            mode="text",
            text=[item["text"]],
            textposition="middle center",
            textfont=dict(size=10.5, color=txt_color),
            hoverinfo="skip",
            showlegend=False
        ))

    # 3. 右侧阶段标签（已删除非法 weight 属性，纯合规写法）
    phase_labels = [
        {"y": "1/6 - 1/15", "label": "阶段一", "color": PHASE_COLORS["gather"]},
        {"y": "1/12  19:00", "label": "阶段二", "color": PHASE_COLORS["escalate"]},
        {"y": "1/13  19:20", "label": "阶段三", "color": PHASE_COLORS["fund"]},
        {"y": "1/18  19:00", "label": "阶段四", "color": PHASE_COLORS["act"]},
        {"y": "1/19  13:00+", "label": "阶段五", "color": PHASE_COLORS["silence"]},
    ]
    for pl in phase_labels:
        fig.add_trace(go.Scatter(
            x=[3.25],
            y=[pl["y"]],
            mode="text",
            text=[pl["label"]],
            textposition="middle left",
            # 仅保留合法参数：size + color，移除 weight
            textfont=dict(size=10, color=pl["color"]),
            hoverinfo="skip",
            showlegend=False
        ))

    # 4. 布局配置（坐标轴、边距、高度全部适配）
    fig.update_layout(
        xaxis=dict(visible=False, range=[-0.2, 4.0]),
        yaxis=dict(type="category", autorange="reversed", tickfont=dict(size=10)),
        bargap=0.3,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=110, r=65, t=15, b=15),
        height=430,
    )

    return fig


def _build_social_network():
    """社交网络：高亮4名嫌疑人及其关联"""
    if not _pos:
        return go.Figure()

    fig = go.Figure()

    normal_ex, normal_ey = [], []
    suspect_ex, suspect_ey = [], []
    for u, v, d in G.edges(data=True):
        ux, uy = _pos[u]
        vx, vy = _pos[v]
        is_s = u in SUSPECT_NAMES and v in SUSPECT_NAMES
        if is_s:
            suspect_ex += [ux, vx, None]
            suspect_ey += [uy, vy, None]
        else:
            normal_ex += [ux, vx, None]
            normal_ey += [uy, vy, None]

    fig.add_trace(go.Scatter(
        x=normal_ex, y=normal_ey, mode="lines",
        line=dict(width=0.8, color="#D5DBDB"),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=suspect_ex, y=suspect_ey, mode="lines",
        line=dict(width=3, color="#E74C3C"),
        hoverinfo="skip", showlegend=False,
    ))

    for comm_idx in range(len(DATA["communities"])):
        comm_set = set(DATA["communities"][comm_idx])
        normal_nodes = [n for n in comm_set if n not in SUSPECT_NAMES and n in _pos]
        if normal_nodes:
            fig.add_trace(go.Scatter(
                x=[_pos[n][0] for n in normal_nodes],
                y=[_pos[n][1] for n in normal_nodes],
                mode="markers",
                marker=dict(size=10, color=COMM_COLORS[comm_idx % len(COMM_COLORS)],
                            opacity=0.55, line=dict(width=0.5, color="white")),
                hoverinfo="text",
                hovertext=normal_nodes,
                showlegend=False,
            ))
        s_nodes = [n for n in comm_set if n in SUSPECT_NAMES and n in _pos]
        for n in s_nodes:
            fig.add_trace(go.Scatter(
                x=[_pos[n][0]], y=[_pos[n][1]],
                mode="markers+text",
                marker=dict(size=24, color=SUSPECTS[n]["color"], opacity=0.95,
                            line=dict(width=3, color="white")),
                text=[n.split()[0]],
                textposition="top center",
                textfont=dict(size=12, color="#2C3E50", family="Arial Bold"),
                hoverinfo="text",
                hovertext=f"<b>{n}</b><br>{SUSPECTS[n]['title']} ({SUSPECTS[n]['dept']})",
                showlegend=False,
            ))

    for i, comm in enumerate(DATA["communities"]):
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=8, color=COMM_COLORS[i % len(COMM_COLORS)]),
            name=f"社团 {i + 1}（{len(comm)}人）",
        ))

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=10)),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=30, b=10),
        height=420,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


def _build_gathering_pattern():
    """Hippokampos聚集时间线 + 人车分离示意"""
    fig = go.Figure()

    cc = DATA.get("cc_loyalty", pd.DataFrame())
    if cc.empty:
        return fig

    hippo = cc[cc["location"] == "Hippokampos"].copy()
    hippo = hippo[hippo["timestamp"].notna()]
    hippo["hour"] = hippo["timestamp"].dt.hour + hippo["timestamp"].dt.minute / 60
    hippo = hippo[(hippo["hour"] >= 18) & (hippo["hour"] <= 24)]
    hippo["date_str"] = hippo["timestamp"].dt.strftime("%m/%d")
    hippo["is_suspect"] = hippo["last4ccnum"].apply(
        lambda x: int(x) in SUSPECT_CC_SET if pd.notna(x) else False
    )

    hippo = hippo[hippo["timestamp"].dt.day.between(6, 15)]

    normal = hippo[~hippo["is_suspect"]]
    fig.add_trace(go.Scatter(
        x=normal["date_str"], y=normal["hour"],
        mode="markers",
        marker=dict(size=8, color="#BDC3C7", opacity=0.6),
        hoverinfo="text",
        hovertext=[f"{r['date_str']} {r['timestamp'].strftime('%H:%M')}<br>信用卡 {int(r['last4ccnum'])}"
                   for _, r in normal.iterrows()],
        name="其他员工",
    ))

    for name, info in SUSPECTS.items():
        s = hippo[hippo["last4ccnum"].apply(lambda x: int(x) in info["cc"] if pd.notna(x) else False)]
        if s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s["date_str"], y=s["hour"],
            mode="markers+text",
            marker=dict(size=14, color=info["color"], opacity=0.9,
                        line=dict(width=2, color="white")),
            text=[name.split()[0]] * len(s),
            textposition="top center",
            textfont=dict(size=10, color=info["color"]),
            hoverinfo="text",
            hovertext=[f"<b>{name}</b><br>{r['timestamp'].strftime('%m/%d %H:%M')}"
                       for _, r in s.iterrows()],
            name=name,
        ))

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.62, y=0.95,
        text="1/12 聚集时间前移 21:00 → 19:00",
        showarrow=False,
        font=dict(size=11, color="#E67E22"),
        bordercolor="#E67E22", borderwidth=1,
        bgcolor="rgba(255,255,255,0.92)",
    )

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.15, y=0.95,
        text="车辆停放于Albert's Fine Clothing — 人车分离",
        showarrow=False,
        font=dict(size=10, color="#7F8C8D"),
        bordercolor="#D5DBDB", borderwidth=1,
        bgcolor="rgba(255,255,255,0.9)",
    )

    fig.update_layout(
        yaxis=dict(
            title="时刻",
            tickvals=[18, 19, 20, 21, 22, 23],
            ticktext=["18:00", "19:00", "20:00", "21:00", "22:00", "23:00"],
            range=[17.5, 24],
            gridcolor="#F0F0F0",
        ),
        xaxis=dict(title="日期"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=9)),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=20, t=30, b=40),
        height=380,
    )
    return fig


def _build_micro_jan12_13():
    """1月12-13日转折日微观时间线（优化拥挤+悬浮详情）"""
    fig = go.Figure()

    events = [
        {"time": "1/12 19:22", "label": "Axel Calzas", "loc": "Hippokampos", "type": "gather"},
        {"time": "1/12 19:29", "label": "Lars Azada", "loc": "Hippokampos", "type": "gather"},
        {"time": "1/12 19:35", "label": "Vira Frente", "loc": "Hippokampos", "type": "gather"},
        {"time": "1/12 19:44", "label": "Ada Campo-Corrente", "loc": "Hippokampos", "type": "suspect"},
        {"time": "1/12 19:51", "label": "Orhan Strum", "loc": "Hippokampos", "type": "suspect"},
        {"time": "1/12 20:05", "label": "Gustav Cazar", "loc": "Hippokampos", "type": "gather"},
        {"time": "1/12 03:39", "label": "Orhan Strum", "loc": "Kronos Mart", "amt": "$277", "type": "abnormal"},
        {"time": "1/13 19:20", "label": "Nils Calixto", "loc": "Frydos", "amt": "$10,000", "type": "abnormal"},
        {"time": "1/13 19:30", "label": "同卡", "loc": "Ouzeri Elian", "amt": "$28", "type": "recover"},
    ]

    # 统一莫兰迪低饱和配色，不再艳丽
    type_colors = {
        "gather": "#B8C2C4",
        "suspect": "#C9A888",
        "abnormal": "#BC8C80",
        "recover": "#A898A8",
    }
    type_sizes = {"gather": 10, "suspect": 16, "abnormal": 20, "recover": 14}

    # 枚举索引做X轴均匀排布，交替文字上下摆放防重叠
    for idx, ev in enumerate(events):
        # 悬浮完整详情弹窗
        hover_text = f"<b>{ev['time']}</b><br>地点：{ev['loc']}"
        if "amt" in ev:
            hover_text += f"<br>交易金额：{ev['amt']}"

        # 偶数点文字在上，奇数点文字在下，错开不重叠
        pos = "top center" if idx % 2 == 0 else "bottom center"

        fig.add_trace(go.Scatter(
            x=[idx], y=[1],
            mode="markers+text",
            marker=dict(
                size=type_sizes[ev["type"]],
                color=type_colors[ev["type"]],
                opacity=0.9,
                line=dict(width=1.5, color="white")
            ),
            text=[ev["label"]],  # 页面只显示人名，极短不拥挤
            textposition=pos,
            textfont=dict(size=8.5, color=type_colors[ev["type"]]),
            hoverinfo="text",
            hovertext=hover_text,
            showlegend=False,
        ))

    # 水平基准时间线（X轴0~8完整覆盖9个节点，修复原坐标错位）
    fig.add_shape(
        type="line", x0=0, x1=len(events)-1, y0=1, y1=1,
        line=dict(color="#EAECEE", width=2)
    )

    # 两段标注坐标适配新索引布局
    fig.add_annotation(x=4.5, y=0.6, text="7小时空白 → 首次凌晨异常交易",
                       showarrow=False, font=dict(size=10, color="#BC8C80"))
    fig.add_annotation(x=7.5, y=0.6, text="次日：$10,000大额交易 + 身份恢复",
                       showarrow=False, font=dict(size=10, color="#A898A8"))

    fig.update_layout(
        xaxis=dict(visible=False, range=[-0.6, len(events)-0.4]),
        yaxis=dict(visible=False, range=[0.2, 1.9]),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20, r=20, t=25, b=25),
        height=300,
    )
    return fig


def _build_micro_jan18_19():
    """1月18-19日秘密行动微观时间线｜精简绘图文字+hover悬浮完整详情+错开防重叠"""
    fig = go.Figure()

    events = [
        {
            "time": "1/18 19:08",
            "short_label": "Varja",
            "full_text": "Varja: Guy's Gyros $39.68",
            "type": "normal"
        },
        {
            "time": "1/18 19:23",
            "short_label": "车辆23",
            "full_text": "车辆23停于General Grocer",
            "type": "abandon"
        },
        {
            "time": "1/18 19:37",
            "short_label": "车辆1",
            "full_text": "车辆1停于Kronos Mart（22.8h）",
            "type": "abandon"
        },
        {
            "time": "1/18 19:41",
            "short_label": "车辆10",
            "full_text": "车辆10停于Kronos Mart（23h）",
            "type": "abandon"
        },
        {
            "time": "1/19 03:13",
            "short_label": "Varja",
            "full_text": "Varja → Kronos Mart $87.66",
            "type": "cluster"
        },
        {
            "time": "1/19 03:45",
            "short_label": "Nils",
            "full_text": "Nils → Kronos Mart $194.51",
            "type": "cluster"
        },
        {
            "time": "1/19 03:48",
            "short_label": "Ada",
            "full_text": "Ada → Kronos Mart $150.36",
            "type": "cluster"
        },
        {
            "time": "1/19 13:27",
            "short_label": "Varja重现",
            "full_text": "Varja 重现（Ouzeri Elian）",
            "type": "reappear"
        },
        {
            "time": "1/19 13:51",
            "short_label": "Ada重现",
            "full_text": "Ada 重现（高尔夫球场）",
            "type": "reappear"
        },
        {
            "time": "1/19 19:49",
            "short_label": "Nils重现",
            "full_text": "Nils 重现（Ouzeri Elian, 16h）",
            "type": "reappear"
        },
    ]

    # 统一整套报表莫兰迪低饱和配色，不再艳丽刺眼
    type_colors = {
        "normal": "#B8C2C4",
        "abandon": "#C9A888",
        "cluster": "#BC8C80",
        "reappear": "#4A5A54",
    }
    type_sizes = {"normal": 8, "abandon": 14, "cluster": 18, "reappear": 12}

    for idx, ev in enumerate(events):
        # 偶数文字在上，奇数文字在下，上下错开杜绝文字重叠拥挤
        text_pos = "top center" if idx % 2 == 0 else "bottom center"
        # 鼠标悬浮弹窗：完整时间+完整事件详情
        hover_content = f"<b>{ev['time']}</b><br>{ev['full_text']}"

        fig.add_trace(go.Scatter(
            x=[idx], y=[1],
            mode="markers+text",
            marker=dict(
                size=type_sizes[ev["type"]],
                color=type_colors[ev["type"]],
                opacity=0.9,
                line=dict(width=1.5, color="white")
            ),
            text=[ev["short_label"]],        # 图上只展示极短文字，不挤占空间
            textposition=text_pos,
            textfont=dict(size=8.5, color=type_colors[ev["type"]]),
            hoverinfo="text",
            hovertext=hover_content,
            showlegend=False,
        ))

    # 水平基准时间轴线
    fig.add_shape(
        type="line",
        x0=-0.3,
        x1=len(events) - 0.7,
        y0=1, y1=1,
        line=dict(color="#EAECEE", width=2)
    )

    # 下方分段标注，坐标适配新均匀索引布局
    fig.add_annotation(x=1.5, y=0.55, text="车辆遗弃",
                       showarrow=False, font=dict(size=10, color="#C9A888"))
    fig.add_annotation(x=5, y=0.55, text="凌晨集群交易（无会员卡）",
                       showarrow=False, font=dict(size=10, color="#BC8C80"))
    fig.add_annotation(x=8, y=0.55, text="电子静默结束",
                       showarrow=False, font=dict(size=10, color="#4A5A54"))

    fig.update_layout(
        xaxis=dict(visible=False, range=[-0.5, len(events) - 0.5]),
        yaxis=dict(visible=False, range=[0.15, 1.85]),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20, r=20, t=25, b=30),
        height=300,
    )
    return fig


def _build_location_map():
    """Top 4 嫌疑地点地图 + 1/18-19 GPS轨迹"""
    fig = go.Figure()

    fig.add_layout_image(dict(
        source="/assets/MC2-tourist.jpg",
        xref="x", yref="y",
        x=MAP_BOUNDS["x_range"][0], y=MAP_BOUNDS["y_range"][1],
        sizex=MAP_BOUNDS["x_range"][1] - MAP_BOUNDS["x_range"][0],
        sizey=MAP_BOUNDS["y_range"][1] - MAP_BOUNDS["y_range"][0],
        sizing="stretch", layer="below",
    ))

    gps = DATA.get("gps", pd.DataFrame())
    if not gps.empty:
        for name, info in SUSPECTS.items():
            car_id = info["car"]
            mask = (
                (gps["id"] == car_id) &
                (gps["Timestamp"] >= "2014-01-18 18:00") &
                (gps["Timestamp"] <= "2014-01-19 20:00")
            )
            traj = gps[mask].sort_values("Timestamp")
            if len(traj) > 1:
                fig.add_trace(go.Scatter(
                    x=traj["long"], y=traj["lat"],
                    mode="lines",
                    line=dict(width=2, color=info["color"], dash="dot"),
                    opacity=0.5,
                    hoverinfo="skip", showlegend=False,
                ))

    top4 = [
        {"rank": 1, "name": "Kronos Mart", "lat": 36.067105, "lon": 24.848757,
         "color": "#C0392B", "size": 28,
         "info": "1/12 & 1/19 凌晨3点异常交易集群<br>车辆1过夜停留11-23h<br>均无会员卡记录"},
        {"rank": 2, "name": "Frydos Autosupply", "lat": 36.059369, "lon": 24.90562,
         "color": "#E74C3C", "size": 24,
         "info": "1/13 $10,000异常大额交易<br>人车分离，无会员卡"},
        {"rank": 3, "name": "Hippokampos", "lat": 36.063403, "lon": 24.875128,
         "color": "#E67E22", "size": 20,
         "info": "1/6-15 规律性人车分离聚集<br>1/12 聚集时间异常前移"},
        {"rank": 4, "name": "Ouzeri Elian", "lat": 36.053054, "lon": 24.872961,
         "color": "#F39C12", "size": 16,
         "info": "多次作为异常交易后身份恢复点<br>多卡活动链重复节点"},
    ]

    for loc in top4:
        fig.add_trace(go.Scatter(
            x=[loc["lon"]], y=[loc["lat"]],
            mode="markers+text",
            marker=dict(size=loc["size"], color=loc["color"],
                        opacity=0.85, line=dict(width=2.5, color="white")),
            text=[f"#{loc['rank']} {loc['name']}"],
            textposition="top center",
            textfont=dict(size=11, color="#2C3E50"),
            hoverinfo="text",
            hovertext=f"<b>#{loc['rank']} {loc['name']}</b><br>{loc['info']}",
            showlegend=False,
        ))

    fig.add_trace(go.Scatter(
        x=[24.848757, 24.875128, 24.872961, 24.90562],
        y=[36.067105, 36.063403, 36.053054, 36.059369],
        mode="lines",
        line=dict(color="#BDC3C7", width=1.5, dash="dot"),
        hoverinfo="skip", showlegend=False,
    ))

    fig.update_layout(
        xaxis=dict(range=MAP_BOUNDS["x_range"], visible=False),
        yaxis=dict(range=MAP_BOUNDS["y_range"], visible=False),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=0, t=20, b=0),
        height=480,
    )
    return fig


# ==========================================
# 2. 布局辅助
# ==========================================
_GRAPH_CFG = {"config": {"toImageButtonOptions": {"format": "png", "scale": 3}}}


def _suspect_card(name, info):
    """生成单个嫌疑人的 dbc.Card"""
    return dbc.Card([
        html.Div(style={"height": "6px", "backgroundColor": info["color"], "borderRadius": "4px 4px 0 0"}),
        dbc.CardBody([
            html.H6(name, className="mb-1", style={"color": "#2C3E50"}),
            html.Small(f"{info['title']} · {info['dept']}", className="text-muted d-block mb-2"),
            html.Hr(className="my-2"),
            html.P(info["evidence"], className="mb-2", style={"fontSize": "0.82rem", "color": "#566573"}),
            html.Small(f"信用卡: {', '.join(str(c) for c in info['cc'])}  |  车辆: {info['car']}",
                       className="text-muted d-block mb-2"),
            html.Span(f"可疑度：{info['danger']}",
                      className="badge",
                      style={"backgroundColor": info["color"], "color": "white", "fontSize": "0.78rem"}),
        ]),
    ], className="h-100 shadow-sm border-0")


# ==========================================
# 3. 左侧目录
# ==========================================
sidebar = html.Div([
    html.H5("目录", className="fw-bold mb-3", style={"color": "black"}),
    html.Ul([
        html.Li(html.A("1. 案件阶段与时间线", href="#section-1",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Ul([
            html.Li(html.A("1.1 阶段概览", href="#section-1-1",
                           className="text-decoration-none text-muted")),
            html.Li(html.A("1.2 关键时间线", href="#section-1-2",
                           className="text-decoration-none text-muted")),
        ], className="list-unstyled ms-3"),
        html.Li(html.A("2. 社交网络与嫌疑人定位", href="#section-2",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Li(html.A("3. Hippokampos聚集模式", href="#section-3",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Li(html.A("4. 转折与高潮", href="#section-4",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Ul([
            html.Li(html.A("4.1 1月12-13日", href="#section-4-1",
                           className="text-decoration-none text-muted")),
            html.Li(html.A("4.2 1月18-19日", href="#section-4-2",
                           className="text-decoration-none text-muted")),
        ], className="list-unstyled ms-3"),
        html.Li(html.A("5. 嫌疑人与地点", href="#section-5",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Ul([
            html.Li(html.A("5.1 核心嫌疑人", href="#section-5-1",
                           className="text-decoration-none text-muted")),
            html.Li(html.A("5.2 嫌疑地点", href="#section-5-2",
                           className="text-decoration-none text-muted")),
        ], className="list-unstyled ms-3"),
        html.Li(html.A("6. 最终推理与结论", href="#section-6",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
    ], className="list-unstyled")
], className="sticky-top pt-4")

# ==========================================
# 4. 右侧正文
# ==========================================
main_content = html.Div([

    html.H2("案件还原", className="fw-bold text-center mb-5", style={"color": "black"}),

    # ========== 1. 案件阶段与时间线 ==========
    html.H4("1. 案件阶段与时间线", id="section-1", className="fw-bold mb-3 border-bottom pb-2",
            style={"color": "black"}),
    html.P(
        "案件呈现五阶段递进模式：从Hippokampos的规律性人车分离聚集，"
        "到聚集时间异常前移与首次凌晨交易，再到$10,000大额资金异动，"
        "最终演化为三人凌晨协同交易与系统性电子静默。",
        className="text-muted mb-4",
        style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.05rem"}
    ),

    # 1.1 阶段概览
    html.H5("1.1 阶段概览", id="section-1-1", className="fw-bold mb-3", style={"color": "#2C3E50"}),
    dbc.Card(dbc.CardBody([
        dcc.Graph(figure=_build_narrative_flow(), style={"height": "300px"}, **_GRAPH_CFG),
    ]), className="mb-4 shadow-sm border-0 bg-white"),

    # 1.2 关键时间线
    html.H5("1.2 关键时间线", id="section-1-2", className="fw-bold mb-3 mt-4 pt-3 border-top",
            style={"color": "#2C3E50"}),
    dbc.Card(dbc.CardBody([
        dcc.Graph(figure=_build_key_timeline(), style={"height": "400px"}, **_GRAPH_CFG),
    ]), className="mb-4 shadow-sm border-0 bg-white"),
    html.P(
        "1月12日聚集时间前移是首个转折信号；1月13日$10,000大额交易标志着资金准备阶段；"
        "1月19日凌晨三名分属不同社团的嫌疑人在Kronos Mart精准汇合，"
        "展示了高度组织化的协同能力。",
        className="text-muted mb-5",
        style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.05rem"}
    ),

    # ========== 2. 社交网络与嫌疑人定位 ==========
    html.H4("2. 社交网络与嫌疑人定位", id="section-2", className="fw-bold mb-3 border-bottom pb-2",
            style={"color": "black"}),
    dbc.Card(dbc.CardBody([
        dcc.Graph(figure=_build_social_network(), style={"height": "420px"}, **_GRAPH_CFG),
    ]), className="mb-4 shadow-sm border-0 bg-white"),
    html.P(
        "两个主要社团通过Ada Campo-Corrente桥接，她是全网络的信息中转枢纽。"
        "四名嫌疑人分属三个社团、三个部门，却在凌晨交易中精准汇合——"
        "这一模式与偶然重叠不符。",
        className="text-muted mb-5",
        style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.05rem"}
    ),

    # ========== 3. Hippokampos聚集模式 ==========
    html.H4("3. Hippokampos聚集模式", id="section-3", className="fw-bold mb-3 border-bottom pb-2",
            style={"color": "black"}),
    dbc.Card(dbc.CardBody([
        dcc.Graph(figure=_build_gathering_pattern(), style={"height": "380px"}, **_GRAPH_CFG),
    ]), className="mb-4 shadow-sm border-0 bg-white"),
    html.P(
        "1月6日至15日，嫌疑人每晚约21时在Hippokampos聚集，而公司车辆统一停放于"
        "Albert's Fine Clothing——形成系统性人车分离。1月12日聚集时间异常前移至19时，"
        "随后即发生首次凌晨异常交易（03:39）。",
        className="text-muted mb-5",
        style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.05rem"}
    ),

    # ========== 4. 转折与高潮 ==========
    html.H4("4. 转折与高潮", id="section-4", className="fw-bold mb-3 border-bottom pb-2",
            style={"color": "black"}),

    # 4.1
    html.H5("4.1 1月12-13日：升级与资金", id="section-4-1", className="fw-bold mb-3", style={"color": "#2C3E50"}),
    dbc.Card(dbc.CardBody([
        dcc.Graph(figure=_build_micro_jan12_13(), style={"height": "280px"}, **_GRAPH_CFG),
    ]), className="mb-3 shadow-sm border-0 bg-white"),
    html.P(
        "1月12日聚集前移至19时，7小时后Orhan Strum于03:39完成首次Kronos Mart凌晨交易；"
        "1月13日Nils Calixto关联信用卡在Frydos消费$10,000，10分钟内即在同一张卡上"
        "恢复会员卡记录——呈现\"异常交易→身份恢复\"模式。",
        className="text-muted mb-4",
        style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.05rem"}
    ),

    # 4.2
    html.H5("4.2 1月18-19日：秘密行动", id="section-4-2", className="fw-bold mb-3 mt-4 pt-3 border-top",
            style={"color": "#2C3E50"}),
    dbc.Card(dbc.CardBody([
        dcc.Graph(figure=_build_micro_jan18_19(), style={"height": "280px"}, **_GRAPH_CFG),
    ]), className="mb-3 shadow-sm border-0 bg-white"),
    html.P(
        "三名嫌疑人于1月18日晚19时分别遗弃公司车辆，利用非监控交通工具完成隐秘集结。"
        "1月19日凌晨03:13-03:48在Kronos Mart完成集群交易（均无会员卡记录），"
        "随后维持10-16小时电子静默，错峰重现。",
        className="text-muted mb-5",
        style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.05rem"}
    ),

    # ========== 5. 嫌疑人与地点 ==========
    html.H4("5. 嫌疑人与地点", id="section-5", className="fw-bold mb-3 border-bottom pb-2",
            style={"color": "black"}),

    # 5.1 核心嫌疑人
    html.H5("5.1 核心嫌疑人", id="section-5-1", className="fw-bold mb-3", style={"color": "#2C3E50"}),
    dbc.Row([
        dbc.Col(_suspect_card(name, info), width=3)
        for name, info in SUSPECTS.items()
    ], className="mb-3"),
    html.P(
        "Nils Calixto（IT）与Ada Campo-Corrente（SVP/CIO）可疑度极高——"
        "同时参与$10,000大额交易与Kronos Mart凌晨集群交易。"
        "Orhan Strum（SVP/COO）发起首次凌晨异常交易；"
        "Varja Lagos（安保/门禁办公室）持有门禁权限并触发集群交易首笔。",
        className="text-muted mb-4",
        style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.05rem"}
    ),

    # 5.2 嫌疑地点
    html.H5("5.2 嫌疑地点", id="section-5-2", className="fw-bold mb-3 mt-4 pt-3 border-top",
            style={"color": "#2C3E50"}),
    dbc.Card(dbc.CardBody([
        dcc.Graph(figure=_build_location_map(), style={"height": "480px"}, **_GRAPH_CFG),
    ]), className="mb-4 shadow-sm border-0 bg-white"),
    html.P(
        "Kronos Mart排名第一：两次凌晨异常交易集群，车辆过夜停留11-23小时。"
        "Frydos Autosupply：$10,000异常大额交易。"
        "Hippokampos：系统性人车分离聚集。"
        "Ouzeri Elian：多次充当异常交易后身份恢复节点。"
        "虚线为1月18-19日嫌疑车辆GPS轨迹。",
        className="text-muted mb-5",
        style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.05rem"}
    ),

    # ========== 6. 最终推理与结论 ==========
    html.H4("6. 最终推理与结论", id="section-6", className="fw-bold mb-3 border-bottom pb-2",
            style={"color": "black"}),

    html.Div([
        html.P([
            "基于前述分析，我们推断：",
        ], className="mb-3", style={"fontSize": "1rem", "lineHeight": "1.8"}),

        html.P([
            html.Span("Hippokampos的规律聚集", className="fw-bold",
                      style={"color": PHASE_COLORS["gather"]}),
            " 为组织建立了非正式通信渠道",
            html.Span("（证据：5晚人车分离）", className="text-muted"),
            " → ",
            html.Span("1月12日的时间前移", className="fw-bold",
                      style={"color": PHASE_COLORS["escalate"]}),
            " 标志着从\"社交\"到\"行动\"的转换信号",
            html.Span("（证据：19时聚集→03:39凌晨交易）", className="text-muted"),
            " → ",
            html.Span("1月13日的$10,000交易", className="fw-bold",
                      style={"color": PHASE_COLORS["fund"]}),
            " 构成资金准备环节",
            html.Span("（证据：人车分离+无会员卡+10分钟身份恢复）", className="text-muted"),
            " → ",
            html.Span("1月19日凌晨的集群交易", className="fw-bold",
                      style={"color": PHASE_COLORS["act"]}),
            " 是行动高潮",
            html.Span("（证据：三人遗弃车辆+无会员卡+35分钟内三笔交易）", className="text-muted"),
            " → ",
            html.Span("案发后的电子静默", className="fw-bold",
                      style={"color": PHASE_COLORS["silence"]}),
            " 展示了预谋的反侦察方案。",
        ], style={"fontSize": "0.95rem", "lineHeight": "2.0"}),

        html.P(
            "四名嫌疑人分属三个社团、三个部门，其协同能力超出了偶然巧合的解释范围。",
            className="mt-3 fw-bold", style={"fontSize": "1rem"},
        ),
    ], className="mb-4"),

    dbc.Alert([
        html.H6("最终结论", className="alert-heading fw-bold mb-2"),
        html.Hr(className="my-2"),
        html.P([
            html.Strong("主要嫌疑人："),
            "Nils Calixto, Ada Campo-Corrente, Orhan Strum, Varja Lagos",
        ], className="mb-1"),
        html.P([
            html.Strong("核心可疑地点："),
            "Kronos Mart (#1), Frydos Autosupply (#2), "
            "Hippokampos (#3), Ouzeri Elian (#4)",
        ], className="mb-1"),
        html.P([
            html.Strong("案件性质："),
            "有组织的协同可疑活动，伴随系统性身份混淆与反侦察行为",
        ], className="mb-0"),
    ], color="dark", className="mb-4"),

    html.Div([
        html.Small([
            html.Strong("不确定性说明："),
            "①员工失踪当天数据完全缺失，无法确认最终事件；"
            "②Nils Calixto身份映射置信度仅52%，存在多卡干扰；"
            "③GPS为定期记录而非连续追踪，存在时间窗口盲区；"
            "④凌晨交易金额本身不具有明确非法含义，可疑性来源于交易时段、"
            "缺失会员卡记录和人车分离的综合判定。",
        ], className="text-muted"),
    ], className="mb-4"),

], className="px-md-4")

# ==========================================
# 5. 整体页面布局组合
# ==========================================
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(sidebar, width=3, className="border-end border-light pe-4 d-none d-md-block"),
            dbc.Col(main_content, width=9)
        ], className="my-5")
    ], fluid=False, style={"maxWidth": "1200px"})
])