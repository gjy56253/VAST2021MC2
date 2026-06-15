# tasks/task2.py
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ==========================================
# 0. Global Data Loading & Coordinates
# ==========================================
MAP_BOUNDS = {"x_range": [24.82450, 24.91000], "y_range": [36.04500, 36.09550]}

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

try:
    gps_data = pd.read_csv('data/gps.csv', usecols=['Timestamp', 'id', 'lat', 'long'])
    gps_data['Timestamp'] = pd.to_datetime(gps_data['Timestamp'])
    available_dates = sorted(list(gps_data['Timestamp'].dt.strftime('%Y-%m-%d').unique()))
    available_cars = sorted(list(gps_data['id'].unique()))
except:
    gps_data = pd.DataFrame(columns=['Timestamp', 'id', 'lat', 'long'])
    available_dates, available_cars = [], []

try:
    cc_data = pd.read_csv('data/cc_loyalty_matched.csv', encoding='latin1')
    cc_data['timestamp'] = pd.to_datetime(cc_data['timestamp'])
    available_ccs = sorted([str(c).replace('.0', '') for c in cc_data['last4ccnum'].dropna().unique()])
except:
    cc_data = pd.DataFrame(columns=['timestamp', 'location', 'last4ccnum', 'price'])
    available_ccs = []

# ==========================================
# 极简版底层映射加载：只映射 信用卡ID -> 车辆ID (彻底解决编码报错)
# ==========================================
cc_match_dict = {}
try:
    # 优先尝试 GBK (Windows 常用)，如果失败则回退到 latin1 (VAST 数据集万能编码)
    # 并且使用 usecols 强制只读这两列，彻底忽略文件里可能存在的中文乱码列
    try:
        cc_to_car = pd.read_csv('data/cc_to_car_match.csv', encoding='gbk', usecols=['last4ccnum', 'Matched_CarID'])
    except Exception:
        cc_to_car = pd.read_csv('data/cc_to_car_match.csv', encoding='latin1', usecols=['last4ccnum', 'Matched_CarID'])

    for _, row in cc_to_car.iterrows():
        try:
            # 暴力转换：先把值转float再转int再转str，彻底免疫 "7819.0" 这种格式
            cc_num = str(int(float(row['last4ccnum'])))
            car_val = row['Matched_CarID']

            # 判断车辆是否为空
            if pd.notna(car_val) and str(car_val).strip().lower() not in ['', 'nan']:
                car_id = int(float(car_val))
            else:
                car_id = None

            cc_match_dict[cc_num] = car_id
        except Exception:
            continue  # 遇到脏数据整行跳过
except Exception as e:
    print(f"映射表读取失败: {e}")

car_options = [{'label': '🌟 所有车辆', 'value': 'ALL'}] + [{'label': f'车辆 {c}', 'value': c} for c in available_cars]


# ==========================================
# Layout
# ==========================================
def get_layout():
    return html.Div([
        dbc.Row([
            # 左侧栏：文章目录
            dbc.Col([
                html.Div([
                    html.H5("目录", className="fw-bold mb-3"),
                    html.Ul([

                        html.Li(
                            html.A(
                                "2.1 时空交互分析台",
                                href="#section-2-1",
                                className="text-decoration-none text-muted fw-bold d-block mt-3"
                            )
                        ),

                        html.Li(
                            html.A(
                                "2.2 核心异常事件复盘",
                                href="#section-2-2",
                                className="text-decoration-none text-muted fw-bold d-block mt-3"
                            )
                        ),

                        html.Ul([

                            html.Li(
                                html.A(
                                    "2.2.1 凌晨3点异常交易验证",
                                    href="#section-2-2-1",
                                    className="text-decoration-none text-muted small d-block mt-1"
                                )
                            ),

                            html.Ul([

                                html.Li(
                                    html.A(
                                        "2.2.1.1 1月12日凌晨3点单笔交易",
                                        href="#section-2-2-1-1",
                                        className="text-decoration-none text-muted small d-block mt-1"
                                    )
                                ),

                                html.Li(
                                    html.A(
                                        "2.2.1.2 1月19日凌晨3点集群交易",
                                        href="#section-2-2-1-2",
                                        className="text-decoration-none text-muted small d-block mt-1"
                                    )
                                ),

                            ], className="list-unstyled ms-4"),

                            html.Li(
                                html.A(
                                    "2.2.2 瞬移异常事件再验证",
                                    href="#section-2-2-2",
                                    className="text-decoration-none text-muted small d-block mt-2"
                                )
                            ),

                            html.Ul([

                                html.Li(
                                    html.A(
                                        "2.2.2.1 信用卡6816轨迹",
                                        href="#section-2-2-2-1",
                                        className="text-decoration-none text-muted small d-block mt-1"
                                    )
                                ),

                                html.Li(
                                    html.A(
                                        "2.2.2.2 信用卡9551轨迹",
                                        href="#section-2-2-2-2",
                                        className="text-decoration-none text-muted small d-block mt-1"
                                    )
                                ),

                                html.Li(
                                    html.A(
                                        "2.2.2.3 信用卡7108轨迹",
                                        href="#section-2-2-2-3",
                                        className="text-decoration-none text-muted small d-block mt-1"
                                    )
                                ),

                            ], className="list-unstyled ms-4"),

                        ], className="list-unstyled ms-3"),

                        html.Li(
                            html.A(
                                "2.3 跨源数据偏差量化",
                                href="#section-2-3",
                                className="text-decoration-none text-muted fw-bold d-block mt-3"
                            )
                        )

                    ], className="list-unstyled")
                ], className="sticky-top pt-4")
            ], width=3, className="border-end border-light pe-4"),

            # 右侧栏：正文内容
            dbc.Col([
                html.H2("任务二：时空对齐与跨源数据偏差分析",
                        className="mb-4 mt-4 text-primary"),
                html.Hr(),

                # --- 2.1 Workbench ---
                html.H3("2.1 时空交互分析台", id="section-2-1", className="mb-3"),
                html.P(
                    "通过整合GPS轨迹与交易数据，我们构建了多维时空比对系统，即允许动态比对车辆实际行驶路线与消费地点，进而精准锚定更多异常活动。",
                    className="text-muted"),

                dbc.Card(dbc.CardBody([
                    dbc.Row([
                        dbc.Col([html.Label("筛选日期：", className="fw-bold"), dcc.Dropdown(id='t2-date-dropdown',
                                                                                               options=[
                                                                                                   {'label': d,
                                                                                                    'value': d}
                                                                                                   for d in
                                                                                                   available_dates],
                                                                                               value='2014-01-19',
                                                                                               clearable=False)],
                                width=3),
                        dbc.Col([html.Label("目标信用卡：", className="fw-bold text-dark"),
                                 dcc.Dropdown(id='t2-cc-dropdown',
                                              options=[{'label': f'信用卡 {c}', 'value': c} for c in available_ccs],
                                              value='9551', clearable=True)], width=4),
                        dbc.Col([html.Label("关联追踪车辆：", className="fw-bold text-primary"),
                                 dcc.Dropdown(id='t2-car-dropdown', options=car_options, value='ALL', clearable=False)],
                                width=5),
                    ]),
                    html.Div([
                        html.Label("全局时间切片：", className="fw-bold text-dark mt-3"),
                        dcc.RangeSlider(id='t2-time-slider', min=0, max=24, step=0.5,
                                        marks={i: f'{i}:00' for i in range(0, 25, 2)}, value=[0, 24],
                                        tooltip={"placement": "bottom", "always_visible": True})
                    ], className="mt-2 bg-white p-3 border rounded"),
                    html.Div(id='t2-info-board', className="mt-3")
                ]), className="mb-4 shadow-sm border-0 bg-light"),

                dbc.Row([
                    dbc.Col([dbc.Card([dbc.CardHeader(html.H6("地理空间映射图", className="mb-0 fw-bold")),
                                       dbc.CardBody(dcc.Loading(dcc.Graph(id='t2-map', style={"height": "400px"})))],
                                      className="shadow-sm border-0 bg-light")], width=12, lg=6),
                    dbc.Col([dbc.Card(
                        [dbc.CardHeader(html.H6("时序活动对齐图", className="mb-0 fw-bold")),
                         dbc.CardBody(dcc.Loading(dcc.Graph(id='t2-timeline', style={"height": "400px"})))],
                        className="shadow-sm border-0 bg-light")], width=12, lg=6)
                ]),

                # =====================================================
                # 2.2 核心异常事件复盘
                # =====================================================

                html.H3(
                    "2.2 核心异常事件复盘",
                    id="section-2-2",
                    className="mt-5 mb-3 pt-3 border-top"
                ),

                html.P(
                    "进一步利用该时空对齐系统验证仅依靠消费流水发现的可疑活动，将刷卡时点与车载定位信息进行融合分析，具体如下所示。",
                    className="text-muted"
                ),

                # =====================================================
                # 2.2.1 凌晨3点异常交易验证
                # =====================================================

                html.H4(
                    "2.2.1 凌晨3点异常交易验证",
                    id="section-2-2-1",
                    className="mt-4 mb-2"
                ),

                html.P(
                    "结合车辆信息验证，我们发现1月12日、1月19日凌晨3点发生的交易均没有车辆信息记录，这种在公共交通停运期且缺乏车辆定位信息的情况下，密集信用卡划扣的行为呈现出极高的可疑性。",
                    className="text-muted mb-4"
                ),

                # ==========================
                # 1月12日
                # ==========================

                html.H5(
                    "2.2.1.1 1月12日凌晨3点单笔交易",
                    id="section-2-2-1-1",
                    className="mt-3 mb-3 fw-bold"
                ),

                dbc.Row([

                    dbc.Col([

                        dbc.Card([

                            dbc.CardHeader(
                                html.H6(
                                    "地理空间映射图",
                                    className="mb-0 fw-bold"
                                )
                            ),

                            dbc.CardBody([

                                dcc.Graph(
                                    id='map-112',
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )

                            ])

                        ], className="shadow-sm border-0 bg-light")

                    ], width=12, lg=6),

                    dbc.Col([

                        dbc.Card([

                            dbc.CardHeader(
                                html.H6(
                                    "时序活动对齐图",
                                    className="mb-0 fw-bold"
                                )
                            ),

                            dbc.CardBody([

                                dcc.Graph(
                                    id='time-112',
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )

                            ])

                        ], className="shadow-sm border-0 bg-light")

                    ], width=12, lg=6)

                ], className="mb-4"),

                # ==========================
                # 1月19日
                # ==========================

                html.H5(
                    "2.2.1.2 1月19日凌晨3点集群交易",
                    id="section-2-2-1-2",
                    className="mt-4 mb-3 fw-bold"
                ),

                dbc.Row([

                    dbc.Col([

                        dbc.Card([

                            dbc.CardHeader(
                                html.H6(
                                    "地理空间映射图",
                                    className="mb-0 fw-bold"
                                )
                            ),

                            dbc.CardBody([

                                dcc.Graph(
                                    id='map-119',
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )

                            ])

                        ], className="shadow-sm border-0 bg-light")

                    ], width=12, lg=6),

                    dbc.Col([

                        dbc.Card([

                            dbc.CardHeader(
                                html.H6(
                                    "时序活动对齐图",
                                    className="mb-0 fw-bold"
                                )
                            ),

                            dbc.CardBody([

                                dcc.Graph(
                                    id='time-119',
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )

                            ])

                        ], className="shadow-sm border-0 bg-light")

                    ], width=12, lg=6)

                ], className="mb-4"),
                # =====================================================
                # 2.2.2 瞬移异常事件再验证
                # =====================================================

                html.H4(
                    "2.2.2 瞬移异常事件再验证",
                    id="section-2-2-2",
                    className="mt-4 mb-2"
                ),

                html.P(
                    "在任务一中，我们通过交易流水识别出了多起明显违反物理移动规律的异常消费记录，现进一步结合车辆GPS轨迹进行联合验证，以确认这些异常是否能够通过正常出行行为解释。",
                    className="text-muted mb-4"
                ),

                # =====================================================
                # 6816
                # =====================================================

                html.H5(
                    "2.2.2.1 1月13日信用卡6816轨迹",
                    id="section-2-2-2-1",
                    className="fw-bold mt-4"
                ),

                html.P(
                    "2014年1月13日上午，信用卡6816连续出现两笔关键交易。该卡首先于 07:43 在 Brew've Been Served 完成消费,随后 08:01 又在 Kronos Mart 产生第二笔交易,然而车辆 20 的 GPS 与停车记录显示，其仅在 07:51 前后发生过一次短暂停留，之后便继续沿既定路线行驶,车辆活动轨迹未覆盖两处，推测其信用卡存在被他人使用的情况。",
                    className="text-muted"
                ),

                dbc.Row([

                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6("地理空间映射图", className="mb-0 fw-bold")),
                            dbc.CardBody(
                                dcc.Graph(
                                    id="map-6816",
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )
                            )
                        ], className="shadow-sm border-0 bg-light")
                    ], width=6),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6("时序活动对齐图", className="mb-0 fw-bold")),
                            dbc.CardBody(
                                dcc.Graph(
                                    id="time-6816",
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )
                            )
                        ], className="shadow-sm border-0 bg-light")
                    ], width=6)

                ], className="mb-4"),

                # =====================================================
                # 9551
                # =====================================================

                html.H5(
                    "2.2.2.2 1月13日信用卡9551轨迹",
                    id="section-2-2-2-2",
                    className="fw-bold mt-4"
                ),

                html.P(
                    "信用卡9551于2014年1月13日全天产生两笔瞬移消费记录，上午时段的交易虽然与车辆 1 的轨迹重合故暂时认定为正常出行活动。然而其晚间时段出现了明显的时空矛盾：19:20 该信用卡在 Drydo's Autosupply n'More 产生消费记录，而车辆 1 在该时刻附近并无对应轨迹；仅10分钟后的 19:30，信用卡又出现在 Ouzeri Elian 完成另一笔交易，此时车辆轨迹却恰好出现在后者附近，说明交易记录与车辆活动记录之间存在明显断裂，进一步验证了任务一识别出的异常时空行为并非数据误差，而是信用卡脱离持有人控制、被多人共享使用的高风险信号。",
                    className="text-muted"
                ),

                dbc.Row([

                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6("地理空间映射图", className="mb-0 fw-bold")),
                            dbc.CardBody(
                                dcc.Graph(
                                    id="map-9551",
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )
                            )
                        ], className="shadow-sm border-0 bg-light")
                    ], width=6),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6("时序活动对齐图", className="mb-0 fw-bold")),
                            dbc.CardBody(
                                dcc.Graph(
                                    id="time-9551",
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )
                            )
                        ], className="shadow-sm border-0 bg-light")
                    ], width=6)

                ], className="mb-4"),

                # =====================================================
                # 7108
                # =====================================================

                html.H5(
                    "2.2.2.3 1月16日信用卡7108轨迹",
                    id="section-2-2-2-3",
                    className="fw-bold mt-4"
                ),

                html.P(
                    "信用卡 7108 于 2014 年 1 月 16 日共发生三笔消费记录，结合车辆 12 的行驶轨迹分析发现：上午 07:30 在 Kronos Mart 的消费发生时，车辆 12 于当日中午 12 点左右才途经此处，仅 07:44 在 Hallowed Grounds 的消费与车辆轨迹匹配，存在信用卡代刷或多人共用行为的可能。",
                    className="text-muted"
                ),

                dbc.Row([

                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6("地理空间映射图", className="mb-0 fw-bold")),
                            dbc.CardBody(
                                dcc.Graph(
                                    id="map-7108",
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )
                            )
                        ], className="shadow-sm border-0 bg-light")
                    ], width=6),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6("时序活动对齐图", className="mb-0 fw-bold")),
                            dbc.CardBody(
                                dcc.Graph(
                                    id="time-7108",
                                    style={"height": "320px"},
                                    config={"displayModeBar": True}
                                )
                            )
                        ], className="shadow-sm border-0 bg-light")
                    ], width=6)

                ], className="mb-4"),

                # --- 2.3 Discrepancy Summary ---
                html.H3(
                    "2.3 跨源数据偏差量化汇总",
                    id="section-2-3",
                    className="mt-5 mb-3 pt-3 border-top"
                ),
                dbc.Card(dbc.CardBody([

                    html.H6(
                        "偏差评价体系构建",
                        className="fw-bold text-primary"
                    ),

                    html.P(
                        "为量化信用卡交易行为与车辆活动轨迹之间的一致性，本研究构建了人车偏离距离指标，根据交易发生时间匹配对应车辆最近GPS记录，并计算车辆位置与消费地点之间的空间距离。当偏离距离小于0.5km时，认定为正常消费行为；当偏离距离超过0.5km时，认定为存在明显空间断层；若交易记录未关联任何福利卡信息，则进一步标记为高风险隐匿行为。",
                        className="text-muted mb-4"
                    ),

                    dbc.Card([
                        dbc.CardHeader(
                            html.H6(
                                "物理空间背离与交易金额偏差量化视图",
                                className="mb-0 fw-bold"
                            )
                        ),
                        dbc.CardBody(
                            dcc.Loading(
                                dcc.Graph(id='t2-macro-discrepancy-scatter')
                            )
                        )
                    ], className="shadow-sm border-0 mb-4 bg-white"),

                    html.H6(
                        "异常模式识别",
                        className="fw-bold text-danger"
                    ),

                    html.P(
                        "从全量交易分布可以观察到，大多数异常交易金额集中于0~100美元区间，但存在两笔接近200美元的高额异常交易，其对应时间均为1月19日凌晨异常交易事件。进一步结合2.2节验证结果发现，红色高风险预警点主要来源于凌晨异常消费与瞬移消费事件，表现出明显的人车分离特征。同时，中风险空间断层交易也主要集中于100美元以下区间，说明异常行为更倾向于通过中小额度交易降低被关注概率。相比之下，除凌晨异常交易外，其余大额消费记录大多处于安全区域，人车轨迹能够保持较高一致性。",
                        className="text-muted mb-4"
                    ),

                    dbc.Alert([

                        html.H5(
                            "重点关注对象",
                            className="fw-bold mb-3 text-white"
                        ),

                        html.P(
                            "综合信用卡消费行为、车辆GPS轨迹验证以及福利卡关联关系分析结果，以下对象同时具备多重异常特征，应作为后续调查重点：",
                            className="mb-3 text-white"
                        ),

                        html.Ul([
                            html.Li("8156、3484、8332：凌晨异常交易核心参与对象。"),
                            html.Li("9551：连续跨区域消费且车辆轨迹无法解释，同时参与凌晨异常交易。"),
                            html.Li("6816、7108：车辆离开后仍产生消费记录，疑似信用卡借用或代刷。")
                        ], className="mb-0 text-white")

                    ],
                        style={
                            "backgroundColor": "#6C757D",
                            "border": "none",
                            "borderRadius": "10px"
                        },
                        className="mb-0 shadow-sm")

                ]), className="mb-5 shadow-sm border-0 bg-light")

            ], width=9, className="ps-5")
        ])
    ])


# ==========================================
# Callbacks
# ==========================================
@callback(
    Output('t2-car-dropdown', 'value'),
    Output('t2-info-board', 'children'),
    Input('t2-cc-dropdown', 'value')
)
def auto_match_car_and_update_board(selected_cc):
    if not selected_cc:
        return 'ALL', dbc.Alert([html.I(className="bi bi-info-circle-fill me-2"),
                                 "请在上方选择一张待查证的信用卡。"], color="secondary", className="mb-0 py-2")

    # 根据极简版字典获取车辆ID
    if selected_cc in cc_match_dict:
        matched_car = cc_match_dict[selected_cc]

        if matched_car is not None:
            return matched_car, dbc.Alert([
                html.I(className="bi bi-robot me-2"), html.Strong("智能绑定："),
                f"系统已查明信用卡 {selected_cc} 对应车辆 {matched_car}，正以此排查人车分离嫌疑。"
            ], style={"backgroundColor": "#6C757D", "color": "white"}, className="mb-0 py-2 border-0")
        else:
            return 'ALL', dbc.Alert([
                html.I(className="bi bi-exclamation-triangle-fill me-2"), html.Strong("无车轨迹警报："),
                f"信用卡 {selected_cc} 无物理绑定轨迹记录，面板已重置为全局模式。"
            ], color="warning", className="mb-0 py-2 border-start border-warning border-4")

    return 'ALL', dbc.Alert([html.I(className="bi bi-exclamation-triangle-fill me-2"),
                             f"系统中未找到信用卡 {selected_cc} 的匹配关系，重置为全局模式。"],
                            color="warning", className="mb-0 py-2")


@callback(
    [Output('t2-map', 'figure'), Output('t2-timeline', 'figure')],
    [Input('t2-date-dropdown', 'value'), Input('t2-car-dropdown', 'value'), Input('t2-cc-dropdown', 'value'),
     Input('t2-time-slider', 'value')]
)
def update_dashboard(selected_date, selected_car, selected_cc, time_range):
    map_fig = go.Figure()
    time_fig = go.Figure()

    if not selected_date: return map_fig, time_fig

    df_gps = gps_data[gps_data['Timestamp'].dt.strftime('%Y-%m-%d') == selected_date].copy()
    df_cc_day = cc_data[cc_data['timestamp'].dt.strftime('%Y-%m-%d') == selected_date].copy()

    if not df_gps.empty:
        df_gps['hour_float'] = df_gps['Timestamp'].dt.hour + df_gps['Timestamp'].dt.minute / 60.0
        start_time, end_time = time_range
        df_gps_filtered = df_gps[(df_gps['hour_float'] >= start_time) & (df_gps['hour_float'] <= end_time)]
    else:
        df_gps_filtered = pd.DataFrame()

    if not df_gps_filtered.empty:
        if selected_car == 'ALL':
            for car_id in df_gps_filtered['id'].unique():
                car_track = df_gps_filtered[df_gps_filtered['id'] == car_id].sort_values('Timestamp')
                map_fig.add_trace(go.Scatter(x=car_track['long'], y=car_track['lat'], mode='lines',
                                             line=dict(color='rgba(230, 126, 34, 0.4)', width=1.5), hoverinfo='none'))
        else:
            car_track = df_gps_filtered[df_gps_filtered['id'] == selected_car].sort_values('Timestamp')
            if not car_track.empty:
                map_fig.add_trace(go.Scatter(x=car_track['long'], y=car_track['lat'], mode='lines+markers',
                                             line=dict(color='#E67E22', width=3), marker=dict(size=5, color='#D35400'),
                                             text=car_track['Timestamp'].dt.strftime('%H:%M:%S'), hoverinfo='text',
                                             name=f'车辆 {selected_car}'))

    if selected_cc and not df_cc_day.empty:
        df_target_cc = df_cc_day[df_cc_day['last4ccnum'].astype(str).str.replace('.0', '') == selected_cc]
        lats, lons, texts = [], [], []
        for _, row in df_target_cc.iterrows():
            loc = row['location']
            if loc in LOCATION_COORDS:
                lats.append(LOCATION_COORDS[loc]['lat'])
                lons.append(LOCATION_COORDS[loc]['lon'])
                texts.append(f"💳 时间: {row['timestamp'].strftime('%H:%M:%S')}<br>地点: {loc}")
        if lats:
            map_fig.add_trace(go.Scatter(x=lons, y=lats, mode='markers',
                                         marker=dict(size=20, color='red', symbol='star',
                                                     line=dict(width=2, color='white')), text=texts, hoverinfo='text',
                                         name=f'信用卡 {selected_cc}'))

    map_fig.add_layout_image(dict(source="/assets/MC2-tourist.jpg", xref="x", yref="y", x=MAP_BOUNDS["x_range"][0],
                                  y=MAP_BOUNDS["y_range"][1], sizex=MAP_BOUNDS["x_range"][1] - MAP_BOUNDS["x_range"][0],
                                  sizey=MAP_BOUNDS["y_range"][1] - MAP_BOUNDS["y_range"][0], sizing="stretch",
                                  layer="below"))
    map_fig.update_layout(xaxis=dict(range=MAP_BOUNDS["x_range"], visible=False),
                          yaxis=dict(range=MAP_BOUNDS["y_range"], visible=False), margin=dict(l=0, r=0, t=0, b=0),
                          plot_bgcolor='#2C3E50', showlegend=False)

    y_cc = f'信用卡 {selected_cc}' if selected_cc else '未指定信用卡'
    if selected_car != 'ALL' and not df_gps_filtered.empty:
        car_track = df_gps_filtered[df_gps_filtered['id'] == selected_car]
        time_fig.add_trace(
            go.Scatter(x=car_track['Timestamp'], y=[f'车辆 {selected_car}'] * len(car_track), mode='markers',
                       marker=dict(color='orange', symbol='line-ns', line=dict(width=2, color='orange'), size=20),
                       name='GPS记录定位', hoverinfo='x'))

    if selected_cc and not df_cc_day.empty:
        df_target_cc = df_cc_day[df_cc_day['last4ccnum'].astype(str).str.replace('.0', '') == selected_cc]
        if not df_target_cc.empty:
            time_fig.add_trace(go.Scatter(x=df_target_cc['timestamp'], y=[y_cc] * len(df_target_cc), mode='markers',
                                          marker=dict(color='red', size=16, symbol='star'),
                                          text=df_target_cc['location'],
                                          hovertemplate="<b>%{x}</b><br>地点: %{text}<extra></extra>",
                                          name='交易时点'))

    time_fig.update_layout(xaxis=dict(title="24小时时间轴", type='date',
                                      range=[pd.to_datetime(f"{selected_date} 00:00:00"),
                                             pd.to_datetime(f"{selected_date} 23:59:59")], tickformat="%H:%M"),
                           yaxis=dict(showgrid=True), margin=dict(l=10, r=10, t=30, b=30), plot_bgcolor='white',
                           hovermode='closest', showlegend=False)
    return map_fig, time_fig


@callback(Output('t2-macro-discrepancy-scatter', 'figure'), Input('t2-date-dropdown', 'value'))
def update_macro_scatter(selected_date):
    if not selected_date or cc_data.empty: return go.Figure().update_layout(title="正在等待数据接入...")
    df_cc_day = cc_data[cc_data['timestamp'].dt.strftime('%Y-%m-%d') == selected_date].copy()
    df_gps_day = gps_data[gps_data['Timestamp'].dt.strftime('%Y-%m-%d') == selected_date].copy()

    scatter_rows = []
    for _, cc_row in df_cc_day.iterrows():
        # 获取纯文本卡号
        cc_num = str(cc_row['last4ccnum']).replace('.0', '').strip()

        # 从字典极简获取车号，绝不会再报 NameError
        car_id = cc_match_dict.get(cc_num, None)

        loc_name = cc_row['location']
        dist_km = 0.0
        status_label = "常规匹配：人车时空一致"

        if car_id is not None and not df_gps_day.empty:
            car_gps = df_gps_day[df_gps_day['id'] == car_id]
            if not car_gps.empty:
                time_diffs = (car_gps['Timestamp'] - cc_row['timestamp']).abs()
                idx = time_diffs.idxmin()
                if time_diffs.loc[idx].total_seconds() <= 1800:
                    closest_gps = car_gps.loc[idx]
                    if loc_name in LOCATION_COORDS:
                        slat, slon = LOCATION_COORDS[loc_name]['lat'], LOCATION_COORDS[loc_name]['lon']
                        dist_km = np.sqrt(((slat - closest_gps['lat']) * 111.0) ** 2 + (
                                (slon - closest_gps['long']) * 111.0 * np.cos(np.radians(slat))) ** 2)

        if dist_km > 0.5: status_label = "空间断层：发生交易但专属车辆缺位"
        loy_val = str(cc_row.get('loyaltynum', '')).strip()
        if not loy_val or loy_val == 'nan' or 'NaN' in loy_val: status_label = "高危隐匿：刻意遗弃会员折扣记录"

        scatter_rows.append({'金额': cc_row['price'], '人车偏离物理距离_公里': round(dist_km, 2), '消费场所': loc_name,
                             '具体时点': cc_row['timestamp'].strftime('%H:%M'), '关联卡号': cc_num,
                             '逻辑定性': status_label})

    if not scatter_rows: return go.Figure().update_layout(title="无相关的匹配交易数据可供渲染")

    fig = px.scatter(pd.DataFrame(scatter_rows), x="金额", y="人车偏离物理距离_公里", color="逻辑定性",
                     color_discrete_map={"常规匹配：人车时空一致": "rgba(46, 204, 113, 0.6)",
                                         "空间断层：发生交易但专属车辆缺位": "#E67E22",
                                         "高危隐匿：刻意遗弃会员折扣记录": "#C0392B"},
                     category_orders={"逻辑定性": ["常规匹配：人车时空一致",
                                                   "空间断层：发生交易但专属车辆缺位",
                                                   "高危隐匿：刻意遗弃会员折扣记录"]},
                     hover_data=["具体时点", "消费场所", "关联卡号"])
    fig.update_traces(marker=dict(size=11, line=dict(width=1, color='white')))
    fig.update_layout(xaxis_title="发生交易划扣额度 单位美元", yaxis_title="人车物理测算距离 单位公里",
                      hovermode="closest", plot_bgcolor='white', paper_bgcolor='white',
                      margin=dict(l=50, r=30, t=15, b=40), height=380,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None))
    fig.add_shape(type="line", x0=0, y0=0.5, x1=df_cc_day['price'].max() * 1.05, y1=0.5,
                  line=dict(color="#7F8C8D", dash="dot", width=1.5))
    return fig


@callback(
    [Output('map-112', 'figure'), Output('time-112', 'figure'),
     Output('map-119', 'figure'), Output('time-119', 'figure')],
    Input('section-2-2-1', 'id')
)
def render_event_graphs(_):

    def build_event_pair(date_str, people):

        map_fig = go.Figure()
        time_fig = go.Figure()

        # =========================
        # 地图底图
        # =========================
        map_fig.add_layout_image(
            dict(
                source="/assets/MC2-tourist.jpg",
                xref="x",
                yref="y",
                x=MAP_BOUNDS["x_range"][0],
                y=MAP_BOUNDS["y_range"][1],
                sizex=MAP_BOUNDS["x_range"][1] - MAP_BOUNDS["x_range"][0],
                sizey=MAP_BOUNDS["y_range"][1] - MAP_BOUNDS["y_range"][0],
                sizing="stretch",
                layer="below"
            )
        )

        # =========================
        # 每个人
        # =========================
        for person in people:

            car_id = person["car"]
            cc_id = str(person["cc"])
            color = person["color"]

            # ---------------------
            # GPS
            # ---------------------
            car_track = gps_data[
                (gps_data["Timestamp"].dt.strftime('%Y-%m-%d') == date_str)
                &
                (gps_data["id"] == car_id)
            ].sort_values("Timestamp")

            if not car_track.empty:

                # 地图轨迹
                map_fig.add_trace(
                    go.Scatter(
                        x=car_track["long"],
                        y=car_track["lat"],
                        mode="lines",
                        line=dict(
                            color=color,
                            width=4
                        ),
                        hoverinfo="skip",
                        showlegend=False
                    )
                )

                # 时间轴（完全参考2.1）
                time_fig.add_trace(
                    go.Scatter(
                        x=car_track["Timestamp"],
                        y=[f"车辆 {car_id}"] * len(car_track),
                        mode="markers",
                        marker=dict(
                            color=color,
                            symbol="line-ns",
                            size=20,
                            line=dict(
                                width=2,
                                color=color
                            )
                        ),
                        hoverinfo="x",
                        showlegend=False
                    )
                )

            # ---------------------
            # 信用卡
            # ---------------------
            cc_tr = cc_data[
                (cc_data["timestamp"].dt.strftime('%Y-%m-%d') == date_str)
                &
                (
                    cc_data["last4ccnum"]
                    .astype(str)
                    .str.replace(".0", "")
                    == cc_id
                )
            ].copy()

            if not cc_tr.empty:

                lons = []
                lats = []
                texts = []

                for _, row in cc_tr.iterrows():

                    loc = row["location"]

                    if loc in LOCATION_COORDS:

                        lons.append(
                            LOCATION_COORDS[loc]["lon"]
                        )

                        lats.append(
                            LOCATION_COORDS[loc]["lat"]
                        )

                        texts.append(
                            f"{row['timestamp'].strftime('%H:%M:%S')}<br>{loc}"
                        )

                # 地图星号
                if len(lons) > 0:

                    map_fig.add_trace(
                        go.Scatter(
                            x=lons,
                            y=lats,
                            mode="markers",
                            marker=dict(
                                size=18,
                                color=color,
                                symbol="star",
                                line=dict(
                                    width=2,
                                    color="white"
                                )
                            ),
                            text=texts,
                            hoverinfo="text",
                            showlegend=False
                        )
                    )

                # 时间轴星号
                time_fig.add_trace(
                    go.Scatter(
                        x=cc_tr["timestamp"],
                        y=[f"信用卡 {cc_id}"] * len(cc_tr),
                        mode="markers",
                        marker=dict(
                            size=16,
                            color=color,
                            symbol="star"
                        ),
                        text=cc_tr["location"],
                        hovertemplate=
                        "<b>%{x}</b><br>地点:%{text}<extra></extra>",
                        showlegend=False
                    )
                )

        # =========================
        # 地图样式
        # =========================
        map_fig.update_layout(
            xaxis=dict(
                range=MAP_BOUNDS["x_range"],
                visible=False
            ),
            yaxis=dict(
                range=MAP_BOUNDS["y_range"],
                visible=False
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False
        )

        # =========================
        # 时间轴样式
        # =========================
        time_fig.update_layout(
            xaxis=dict(
                type="date",
                tickformat="%H:%M",
                title="",
                range=[
                    pd.to_datetime(f"{date_str} 00:00:00"),
                    pd.to_datetime(f"{date_str} 23:59:59")
                ]
            ),
            yaxis=dict(
                type="category",
                showgrid=True
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=10, t=0, b=30),
            showlegend=False
        )

        return map_fig, time_fig

    people_112 = [
        {
            "car": 32,
            "cc": "8156",
            "color": "#E67E22"
        }
    ]

    people_119 = [
        {
            "car": 1,
            "cc": "3484",
            "color": "#1F77B4"
        },
        {
            "car": 23,
            "cc": "9551",
            "color": "#FF7F0E"
        },
        {
            "car": 10,
            "cc": "8332",
            "color": "#D62728"
        }
    ]

    m1, t1 = build_event_pair(
        "2014-01-12",
        people_112
    )

    m2, t2 = build_event_pair(
        "2014-01-19",
        people_119
    )

    return m1, t1, m2, t2

@callback(
    [
        Output('map-6816', 'figure'),
        Output('time-6816', 'figure'),

        Output('map-9551', 'figure'),
        Output('time-9551', 'figure'),

        Output('map-7108', 'figure'),
        Output('time-7108', 'figure')
    ],
    Input('section-2-2-2', 'id')
)
def render_spacetime_cases(_):

    def build_pair(date_str, car_id, cc_id, color):

        map_fig = go.Figure()
        time_fig = go.Figure()

        map_fig.add_layout_image(
            dict(
                source="/assets/MC2-tourist.jpg",
                xref="x",
                yref="y",
                x=MAP_BOUNDS["x_range"][0],
                y=MAP_BOUNDS["y_range"][1],
                sizex=MAP_BOUNDS["x_range"][1] - MAP_BOUNDS["x_range"][0],
                sizey=MAP_BOUNDS["y_range"][1] - MAP_BOUNDS["y_range"][0],
                sizing="stretch",
                layer="below"
            )
        )

        # GPS轨迹
        car_track = gps_data[
            (gps_data["Timestamp"].dt.strftime('%Y-%m-%d') == date_str)
            &
            (gps_data["id"] == car_id)
        ].sort_values("Timestamp")

        if not car_track.empty:

            map_fig.add_trace(
                go.Scatter(
                    x=car_track["long"],
                    y=car_track["lat"],
                    mode="lines",
                    line=dict(
                        color=color,
                        width=4
                    ),
                    hoverinfo="skip",
                    showlegend=False
                )
            )

            time_fig.add_trace(
                go.Scatter(
                    x=car_track["Timestamp"],
                    y=[f"车辆 {car_id}"] * len(car_track),
                    mode="markers",
                    marker=dict(
                        color=color,
                        symbol="line-ns",
                        size=20,
                        line=dict(
                            width=2,
                            color=color
                        )
                    ),
                    hoverinfo="x",
                    showlegend=False
                )
            )

        # 信用卡交易
        cc_tr = cc_data[
            (cc_data["timestamp"].dt.strftime('%Y-%m-%d') == date_str)
            &
            (
                cc_data["last4ccnum"]
                .astype(str)
                .str.replace(".0", "")
                == str(cc_id)
            )
        ].copy()

        if not cc_tr.empty:

            lons = []
            lats = []
            texts = []

            for _, row in cc_tr.iterrows():

                loc = row["location"]

                if loc in LOCATION_COORDS:

                    lons.append(
                        LOCATION_COORDS[loc]["lon"]
                    )

                    lats.append(
                        LOCATION_COORDS[loc]["lat"]
                    )

                    texts.append(
                        f"{row['timestamp'].strftime('%H:%M:%S')}<br>{loc}"
                    )

            if len(lons) > 0:

                map_fig.add_trace(
                    go.Scatter(
                        x=lons,
                        y=lats,
                        mode="markers",
                        marker=dict(
                            size=18,
                            color="red",
                            symbol="star",
                            line=dict(
                                width=2,
                                color="white"
                            )
                        ),
                        text=texts,
                        hoverinfo="text",
                        showlegend=False
                    )
                )

            time_fig.add_trace(
                go.Scatter(
                    x=cc_tr["timestamp"],
                    y=[f"信用卡 {cc_id}"] * len(cc_tr),
                    mode="markers",
                    marker=dict(
                        size=16,
                        color="red",
                        symbol="star"
                    ),
                    text=cc_tr["location"],
                    hovertemplate=
                    "<b>%{x}</b><br>地点:%{text}<extra></extra>",
                    showlegend=False
                )
            )

        map_fig.update_layout(
            xaxis=dict(
                range=MAP_BOUNDS["x_range"],
                visible=False
            ),
            yaxis=dict(
                range=MAP_BOUNDS["y_range"],
                visible=False
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False
        )

        time_fig.update_layout(
            xaxis=dict(
                type="date",
                tickformat="%H:%M",
                range=[
                    pd.to_datetime(f"{date_str} 00:00:00"),
                    pd.to_datetime(f"{date_str} 23:59:59")
                ]
            ),
            yaxis=dict(
                type="category",
                showgrid=True
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=10, t=0, b=30),
            showlegend=False
        )

        return map_fig, time_fig

    m6816, t6816 = build_pair(
        "2014-01-13",
        20,
        "6816",
        "#1F77B4"
    )

    m9551, t9551 = build_pair(
        "2014-01-13",
        1,
        "9551",
        "#FF7F0E"
    )

    m7108, t7108 = build_pair(
        "2014-01-16",
        12,
        "7108",
        "#D62728"
    )

    return (
        m6816, t6816,
        m9551, t9551,
        m7108, t7108
    )