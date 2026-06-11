# tasks/task5.py
import pandas as pd
import numpy as np
import networkx as nx
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

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

# =====================================================
# 选择器选项（原5.1）
# =====================================================
persons = sorted(
    task3_mapping[~task3_mapping["FullName"].isin(["未定业务人员", "无车基层员工"])]
    ["FullName"].dropna().unique()
)
dates = sorted(gps_data["Timestamp"].dt.strftime("%Y-%m-%d").dropna().unique())

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
                            html.Li(html.A("5.3.4 卡车107工业采购链", href="#section-5-3-4",
                                           className="text-decoration-none text-muted small d-block mt-1")),
                            html.Li(html.A("5.3.5 Katerina's Cafe聚集群", href="#section-5-3-5",
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
                html.P("该系统融合人员身份、车辆轨迹、信用卡消费及社交关系网络，实现重点调查对象的联合时空行为分析。",
                       className="text-muted"),

                dbc.Row([
                    dbc.Col(html.Label("日期"), width=4),
                    dbc.Col(html.Label("调查对象"), width=4),
                    dbc.Col(html.Label("时间范围"), width=4)
                ]),
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(
                            id="t5-date-dropdown",
                            options=[{"label": "ALL", "value": "ALL"}] +
                                    [{"label": d, "value": d} for d in dates],
                            value="ALL",
                            clearable=False
                        ), width=4
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="t5-person-dropdown",
                            options=[{"label": p, "value": p} for p in persons],
                            placeholder="请选择调查对象"
                        ), width=4
                    ),
                    dbc.Col(
                        dcc.RangeSlider(
                            id="t5-time-slider",
                            min=0, max=24, step=1,
                            value=[0, 24]
                        ), width=4
                    )
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col(dcc.Graph(id="t5-map", style={"height": "700px"}), width=6),
                    dbc.Col(dcc.Graph(id="t5-network", style={"height": "700px"}), width=6)
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

                # 事件一
                html.H5("5.3.1 Kronos Mart 两次凌晨异常交易事件", id="section-5-3-1",
                        className="fw-bold text-primary mt-4"),
                html.P(
                    "本次调查首先锁定了 Kronos Mart 在2014年1月12日和1月19日凌晨出现的两组异常交易，该地点在正常营业时段主要承担日常零售功能，但两次事件均发生在凌晨3时左右，明显偏离其常规消费时间分布。",
                    className="text-muted"),
                html.Ul([
                    html.Li([html.Strong("1月12日凌晨："),
                             "员工 Orhan Strum 关联的8156号信用卡产生异常交易，并且于12日晚其所在群体的活动时间明显提前，同时发现现有GPS未能提供支持其到达该地的轨迹，交易也缺乏会员卡流水。"]),
                    html.Li([html.Strong("1月19日凌晨："),
                             "Varja, Nils 与 Ada 三人关联的卡号先后完成无会员卡交易，且三人配发车辆前一日晚间后无匹配轨迹，交易后进入较长时间记录空窗，直至白天分散恢复。"])
                ]),
                # 事件一：一行两张图，1:1等分，完全复用你logo可用的图片插入逻辑
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            html.Img(
                                src="/assets/task5_1_1.png",
                                style={"maxWidth": "100%", "maxHeight": "250px", "objectFit": "contain"}
                            ),
                            className="text-center mb-3"
                        )
                    ], md=6),
                    dbc.Col([
                        html.Div(
                            html.Img(
                                src="/assets/task5_1_2.png",
                                style={"maxWidth": "100%", "maxHeight": "250px", "objectFit": "contain"}
                            ),
                            className="text-center mb-3"
                        )
                    ], md=6)
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
                    "在案发前两周的活动轨迹中，系统识别出一组规律性的晚间人车分离模式，Orhan Strum 等六名员工经常在 Hippokampos 产生消费，但其配发车辆同期主要停靠在 Albert's Fine Clothing 附近。",
                    className="text-muted"),
                # 事件二 双图并排
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            html.Img(
                                src="/assets/task5_2_1.png",
                                style={"maxWidth": "100%", "maxHeight": "250px", "objectFit": "contain"}
                            ),
                            className="text-center mb-3"
                        )
                    ], md=6),
                    dbc.Col([
                        html.Div(
                            html.Img(
                                src="/assets/task5_2_2.png",
                                style={"maxWidth": "100%", "maxHeight": "250px", "objectFit": "contain"}
                            ),
                            className="text-center mb-3"
                        )
                    ], md=6)
                ]),
                dbc.Alert([
                    html.I(className="bi bi-info-circle-fill me-2"),
                    html.Strong("结论："),
                    "1月12日晚该群体的常规活动时间由约21时提前至约19时，随后发生8156号凌晨交易。更稳妥的判断是：这里是一个稳定的非正式聚集与车辆集中停放区域，但是否承担了凌晨事件的前置组织功能，仍需进一步证据确认。"
                ], color="secondary", className="shadow-sm"),

                # 事件三（段落已合并为单段）
                html.H5("5.3.3 Frydos—Ouzeri Elian 的9551信用卡人卡车分离链", id="section-5-3-3",
                        className="fw-bold text-primary mt-5"),
                html.P(
                    "调查以1月13日晚Nils Calixto拥有的信用卡9551的异常交易为切入点，其19:20在 Frydos 产生 10,000.00美元 极端高额交易，且无对应会员卡记录。同期，其分配车辆 1 在距离2.21公里外的 Ouzeri Elian 附近，仅十分钟后，9551在 Ouzeri Elian 产生28.75美元餐饮消费，并且重新使用会员卡，呈现出在 Frydos脱轨而在 Ouzeri 正常的模式。",
                    className="text-muted"),
                # 事件三 双图并排
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            html.Img(
                                src="/assets/task5_3_1.png",
                                style={"maxWidth": "100%", "maxHeight": "250px", "objectFit": "contain"}
                            ),
                            className="text-center mb-3"
                        )
                    ], md=6),
                    dbc.Col([
                        html.Div(
                            html.Img(
                                src="/assets/task5_3_2.png",
                                style={"maxWidth": "100%", "maxHeight": "250px", "objectFit": "contain"}
                            ),
                            className="text-center mb-3"
                        )
                    ], md=6)
                ]),
                dbc.Alert([
                    html.I(className="bi bi-bullseye me-2"),
                    html.Strong("结论："),
                    "Frydos 由于在该地发生大额资金转移被判定为高风险异常交易地点，Ouzeri 视为异常交易后重新进入正常身份模式的关键节点，而9551随后又参与19日凌晨事件，调查价值极高。"
                ], color="secondary", className="shadow-sm"),

                # 事件四（无图片，段落合并）
                html.H5("5.3.4 公共卡车107与4530号信用卡的工业采购异常链", id="section-5-3-4",
                        className="fw-bold text-primary mt-5"),
                html.P(
                    "信用卡4530被映射至公共卡车107。1月7日、8日和15日，该卡在 Kronos Pipe、Maximum Iron 等工业地点累计交易超2.6万美元，最可疑的是交易顺序与车辆路线的冲突：例如1月7日，Kronos Pipe的交易无法由卡车107解释，而随后的 Maximum Iron 交易则与轨迹吻合，且该模式在三日内重复出现。",
                    className="text-muted"),
                dbc.Alert([
                    html.I(className="bi bi-info-circle-fill me-2"),
                    html.Strong("结论："),
                    "暴露出公共卡车调度与工业采购的责任盲区。由于无法可靠识别单一使用员工，调查对象应首先确定为4530号信用卡、车辆107及其调度记录，而不应强行归责于某一名员工。"
                ], color="secondary", className="shadow-sm"),

                # 事件五
                html.H5("5.3.5 Katerina's Cafe 跨部门夜间聚集与人车分离事件群", id="section-5-3-5",
                        className="fw-bold text-primary mt-5"),
                html.P(
                    "1月6日至19日，Nils, Lucas 等十余名跨部门员工在晚间频繁于 Katerina's Cafe 产生消费，部分车辆异地停放或在交易期间保持长时间静止出现GPS空窗。",
                    className="text-muted"),
                # 事件五 双图并排
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            html.Img(
                                src="/assets/task5_5_1.png",
                                style={"maxWidth": "100%", "maxHeight": "250px", "objectFit": "contain"}
                            ),
                            className="text-center mb-3"
                        )
                    ], md=6),
                    dbc.Col([
                        html.Div(
                            html.Img(
                                src="/assets/task5_5_2.png",
                                style={"maxWidth": "100%", "maxHeight": "250px", "objectFit": "contain"}
                            ),
                            className="text-center mb-3"
                        )
                    ], md=6)
                ]),
                dbc.Alert([
                    html.I(className="bi bi-info-circle-fill me-2"),
                    html.Strong("结论："),
                    "该地点属于重复事件群，存在稳定的跨部门非正式聚集和人车分离行为，更适合被定义为高风险人员交集点和关系验证点，辅助解释凌晨交易与卡片共享。"
                ], color="secondary", className="shadow-sm"),

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


# ===================== 莫兰迪配色常量（纯白背景）=====================
# 莫兰迪绿色系为主，低饱和度、柔和视觉
MORANDI_MAIN_NODE = "#7A9D8C"    # 选中人员-主节点（深莫兰迪绿）
MORANDI_SUB_NODE = "#A8BFAF"     # 关联人员-普通节点（浅莫兰迪绿）
MORANDI_EDGE_LINE = "#C8D2CC"    # 关系连线（灰调莫兰迪绿）
MORANDI_GPS_TRACE = "#94A89E"    # GPS轨迹线（柔调绿棕）
MORANDI_CC_STAR = "#B98B82"      # 消费星标（低饱和柔砖红，不刺眼）
BG_PURE_WHITE = "#FFFFFF"        # 图表全局纯白背景
TEXT_GRAY = "#4A4A4A"            # 文字深灰（替代纯黑，更柔和）
CHART_HEIGHT = 450               # 统一图表高度（可按需微调：400~500）

# =====================================================
# 回调：5.1 联合调查分析系统（原回调，已去除调试打印）
# =====================================================
# =====================================================
# 回调：5.1 联合调查分析系统（样式优化+莫兰迪配色+防拉伸）
# =====================================================
# =====================================================
# 回调：5.1 联合调查分析系统（仅修改颜色，布局/逻辑完全保留原版）
# =====================================================
# =====================================================
# 回调：5.1 联合调查分析系统 | 美化版 + 1:1宽度 + 缩小高度
# =====================================================
@callback(
    [Output("t5-map", "figure"),
     Output("t5-network", "figure")],
    [Input("t5-date-dropdown", "value"),
     Input("t5-person-dropdown", "value"),
     Input("t5-time-slider", "value")]
)
def update_dashboard(selected_date, selected_person, time_range):
    map_fig = go.Figure()
    net_fig = go.Figure()

    if not selected_person:
        return map_fig, net_fig

    person_rows = task3_mapping[task3_mapping["FullName"] == selected_person]
    if person_rows.empty:
        return map_fig, net_fig

    car_id = person_rows["Matched_CarID"].iloc[0]
    cc_list = person_rows["last4ccnum"].astype(str).unique()

    # GPS过滤
    gps_filtered = gps_data[gps_data["id"] == car_id].copy()
    if selected_date != "ALL":
        gps_filtered = gps_filtered[gps_filtered["Timestamp"].dt.strftime("%Y-%m-%d") == selected_date]
    gps_filtered["hour"] = gps_filtered["Timestamp"].dt.hour + gps_filtered["Timestamp"].dt.minute / 60
    gps_filtered = gps_filtered[(gps_filtered["hour"] >= time_range[0]) & (gps_filtered["hour"] <= time_range[1])]
    gps_filtered = gps_filtered.sort_values("Timestamp")

    # 信用卡过滤
    cc_filtered = cc_data[cc_data["last4ccnum"].astype(str).isin(cc_list)].copy()
    if selected_date != "ALL":
        cc_filtered = cc_filtered[cc_filtered["timestamp"].dt.strftime("%Y-%m-%d") == selected_date]

    # 地图轨迹
    if not gps_filtered.empty:
        map_fig.add_trace(go.Scatter(
            x=gps_filtered["long"], y=gps_filtered["lat"],
            mode="lines+markers",
            line=dict(color=MORANDI_GPS_TRACE, width=3),
            marker=dict(size=5, color=MORANDI_GPS_TRACE),
            name="GPS轨迹"
        ))

    lats, lons, texts = [], [], []
    for _, row in cc_filtered.iterrows():
        loc = row["location"]
        if loc in LOCATION_COORDS:
            lats.append(LOCATION_COORDS[loc]["lat"])
            lons.append(LOCATION_COORDS[loc]["lon"])
            texts.append(f"{loc}<br>{row['timestamp']}")

    if lats:
        map_fig.add_trace(go.Scatter(
            x=lons, y=lats, mode="markers",
            marker=dict(size=18, color=MORANDI_CC_STAR, symbol="star", opacity=0.85),
            text=texts, hoverinfo="text",
            name="消费记录"
        ))

    # 背景底图
    map_fig.add_layout_image(
        dict(source="/assets/MC2-tourist.jpg",
             xref="x", yref="y",
             x=MAP_BOUNDS["x_range"][0],
             y=MAP_BOUNDS["y_range"][1],
             sizex=MAP_BOUNDS["x_range"][1] - MAP_BOUNDS["x_range"][0],
             sizey=MAP_BOUNDS["y_range"][1] - MAP_BOUNDS["y_range"][0],
             sizing="stretch",
             layer="below")
    )

    map_fig.update_layout(
        autosize=False,
        height=CHART_HEIGHT,
        paper_bgcolor=BG_PURE_WHITE,
        plot_bgcolor=BG_PURE_WHITE,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(range=MAP_BOUNDS["x_range"], showgrid=False, showticklabels=False, zeroline=False, ticks=""),
        yaxis=dict(range=MAP_BOUNDS["y_range"], showgrid=False, showticklabels=False, zeroline=False, ticks="")
    )

    # 网络图
    rel = relation_df[(relation_df["source"] == selected_person) | (relation_df["target"] == selected_person)]
    rel = rel.sort_values("score", ascending=False).head(10)

    G = nx.Graph()
    G.add_node(selected_person)
    for _, row in rel.iterrows():
        other = row["target"] if row["source"] == selected_person else row["source"]
        G.add_edge(selected_person, other, weight=row["score"])

    if len(G.nodes()) == 1:
        pos = {selected_person: (0, 0)}
    else:
        pos = nx.spring_layout(G, seed=42, k=1.2)  # 小幅收紧节点间距，适配小尺寸

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    net_fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color=MORANDI_EDGE_LINE, width=2.2),
        hoverinfo="none"
    ))

    node_x, node_y, node_text, node_color = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_color.append(MORANDI_MAIN_NODE if node == selected_person else MORANDI_SUB_NODE)

    net_fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=node_text, textposition="top center",
        marker=dict(size=24, color=node_color, line=dict(color=BG_PURE_WHITE, width=1.2)),
        textfont=dict(size=9, color=TEXT_GRAY)  # 缩小字体适配小尺寸
    ))

    net_fig.update_layout(
        autosize=False,
        height=CHART_HEIGHT,
        paper_bgcolor=BG_PURE_WHITE,
        plot_bgcolor=BG_PURE_WHITE,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        yaxis=dict(visible=False)
    )

    return map_fig, net_fig