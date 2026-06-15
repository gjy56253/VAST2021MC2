import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

dash.register_page(__name__, path='/data-preparation', name='数据处理', order=2)

# ==========================================
# 终极坐标字典 [GPS 聚类与人工精调]
# ==========================================
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
    "Daily Dealz": {"lat": None, "lon": None},
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


# ==========================================
# 绘制最终的坐标分布验证图
# ==========================================
def create_calibration_map():
    lats, lons, names = [], [], []
    for name, coords in LOCATION_COORDS.items():
        if coords['lat'] is not None and coords['lon'] is not None:
            lats.append(coords['lat'])
            lons.append(coords['lon'])
            names.append(name)

    fig = go.Figure()

    fig.add_layout_image(
        dict(
            source="/assets/MC2-tourist.jpg",
            xref="x", yref="y",
            x=24.82450, y=36.09550,
            sizex=0.0855, sizey=0.0505,
            sizing="stretch",
            layer="below"
        )
    )

    fig.add_trace(go.Scatter(
        x=lons, y=lats,
        mode="text",
        text=["📍"] * len(lons),
        textfont=dict(size=24),
        textposition="top center",
        customdata=names,
        hovertemplate="<b>%{customdata}</b><br>Lat: %{y}<br>Lon: %{x}<extra></extra>"
    ))

    fig.update_layout(
        xaxis=dict(range=[24.82450, 24.91000], visible=False),
        yaxis=dict(range=[36.04500, 36.09550], visible=False),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=550,
        showlegend=False,
        plot_bgcolor="white"
    )
    return fig


# 歧义数据展示表格组件 [完美适配导航栏配色版]
ambiguity_table = dbc.Table(
    [
        html.Thead(
            html.Tr([
                # 表头使用与导航栏一致的高级灰青色 #7a8b8c
                html.Th("日期", className="text-center py-3",
                        style={"backgroundColor": "#7a8b8c", "color": "white", "border": "none"}),
                html.Th("交易地点", className="text-center py-3",
                        style={"backgroundColor": "#7a8b8c", "color": "white", "border": "none"}),
                html.Th("消费金额", className="text-center py-3",
                        style={"backgroundColor": "#7a8b8c", "color": "white", "border": "none"}),
                html.Th("信用卡记录 [时间]", className="text-center py-3",
                        style={"backgroundColor": "#7a8b8c", "color": "white", "border": "none"}),
                html.Th("同行会员卡记录", className="text-center py-3",
                        style={"backgroundColor": "#7a8b8c", "color": "white", "border": "none"})
            ])
        ),
        html.Tbody([
            html.Tr([
                # 强制将与代码块完全一致的背景色 #f0f7f4 赋予每一个 TD 单元格
                html.Td("2014-01-09", className="text-center align-middle", style={"backgroundColor": "#f0f7f4"}),
                html.Td("Guy's Gyros", className="text-center align-middle fw-bold",
                        style={"backgroundColor": "#f0f7f4", "color": "#2c3e50"}),
                html.Td("$8.23", className="text-center align-middle", style={"backgroundColor": "#f0f7f4"}),
                html.Td("7889 [20:23] 与 5368 [20:38]", className="text-center align-middle",
                        style={"backgroundColor": "#f0f7f4"}),
                html.Td("L2247 与 L6119", className="text-center align-middle", style={"backgroundColor": "#f0f7f4"})
            ]),
            html.Tr([
                # 纯白交替行
                html.Td("2014-01-09", className="text-center align-middle", style={"backgroundColor": "#ffffff"}),
                html.Td("Katerina's Cafe", className="text-center align-middle fw-bold",
                        style={"backgroundColor": "#ffffff", "color": "#2c3e50"}),
                html.Td("$26.60", className="text-center align-middle", style={"backgroundColor": "#ffffff"}),
                html.Td("5921 [19:30] 与 4948 [20:06]", className="text-center align-middle",
                        style={"backgroundColor": "#ffffff"}),
                html.Td("L9406 与 L3295", className="text-center align-middle", style={"backgroundColor": "#ffffff"})
            ]),
            html.Tr([
                # 再次使用代码块背景色 #f0f7f4
                html.Td("2014-01-11", className="text-center align-middle", style={"backgroundColor": "#f0f7f4"}),
                html.Td("Hippokampos", className="text-center align-middle fw-bold",
                        style={"backgroundColor": "#f0f7f4", "color": "#2c3e50"}),
                html.Td("$63.21", className="text-center align-middle", style={"backgroundColor": "#f0f7f4"}),
                html.Td("4795 [19:29] 与 8332 [19:45]", className="text-center align-middle",
                        style={"backgroundColor": "#f0f7f4"}),
                html.Td("L2070 与 L8566", className="text-center align-middle", style={"backgroundColor": "#f0f7f4"})
            ]),
        ])
    ],
    bordered=False,
    hover=True,
    responsive=True,
    className="mb-4 shadow-sm",
    style={"fontSize": "0.95rem", "border": "1px solid #dce8e2", "borderRadius": "8px", "overflow": "hidden"}
)

# ==========================================
# 左侧导航栏定义
# ==========================================
sidebar = html.Div([
    html.H5("目录", className="fw-bold mb-3", style={"color": "black"}),
    html.Ul([
        html.Li(html.A("1. 空间数据处理与地图校准", href="#section-1",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Ul([
            html.Li(html.A("1.1 数据清洗与格式转换", href="#section-1-1",
                           className="text-decoration-none text-muted d-block mt-2 mb-1")),
            html.Li(html.A("1.2 旅游地图坐标对齐", href="#section-1-2",
                           className="text-decoration-none text-muted d-block")),
        ], className="list-unstyled ms-3"),

        html.Li(html.A("2. 财务数据融合", href="#section-2",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Ul([
            html.Li(html.A("2.1 笛卡尔积隔离", href="#section-2-1",
                           className="text-decoration-none text-muted d-block mt-2 mb-1")),
            html.Li(html.A("2.2 消费记录对齐", href="#section-2-2",
                           className="text-decoration-none text-muted d-block mt-2 mb-1")),
        ], className="list-unstyled ms-3"),

        html.Li(html.A("3. 地标经纬度确认", href="#section-3",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Ul([
            html.Li(html.A("3.1 聚类与时空匹配", href="#section-3-1",
                           className="text-decoration-none text-muted d-block mt-2 mb-1")),
            html.Li(html.A("3.2 人工校准", href="#section-3-2",
                           className="text-decoration-none text-muted d-block")),
        ], className="list-unstyled ms-3"),

        html.Li(html.A("4. 消费与车辆信息对齐", href="#section-4",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Ul([
            html.Li(html.A("4.1 消费流水与物理轨迹绑定", href="#section-4-1",
                           className="text-decoration-none text-muted d-block mt-2 mb-1")),
            html.Li(html.A("4.2 人事特征注入与交叉验证", href="#section-4-2",
                           className="text-decoration-none text-muted d-block")),
        ], className="list-unstyled ms-3"),

        html.Li(html.A("5. 非正式社交网络构建", href="#section-5",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Ul([
            html.Li(html.A("5.1 成员密切关系衡量", href="#section-5-1",
                           className="text-decoration-none text-muted d-block mt-2 mb-1")),
            html.Li(html.A("5.2 非正式群体聚类", href="#section-5-2",
                           className="text-decoration-none text-muted d-block")),
        ], className="list-unstyled ms-3"),
    ], className="list-unstyled")
], className="sticky-top pt-4")


# ==========================================
# 代码块组件
# ==========================================
def render_code_block(code_text):
    return html.Pre(
        html.Code(code_text, className="language-python"),
        className="p-3 rounded-3 mt-3 mb-4 shadow-sm",
        style={
            "backgroundColor": "#f0f7f4",
            "color": "#2c3e50",
            "overflowX": "auto",
            "fontSize": "0.9rem",
            "border": "1px solid #dce8e2"
        }
    )


# 代码片段保留原始英文逻辑标识
code_sanitization = """# Extracting valid geometries and converting to GeoJSON
valid_records = []
with fiona.open(input_shp) as src:
    crs = src.crs 
    for i, feature in enumerate(src):
        try:
            geom = shape(feature['geometry'])
            if geom.is_valid and not geom.is_empty:
                valid_records.append(feature)
        except Exception as e:
            print(f"Dropped corrupted data at row {i}")

gdf = gpd.GeoDataFrame.from_features(valid_records, crs=crs)
gdf.to_file(output_json, driver="GeoJSON")"""

code_calibration = """// Interactive Leaflet calibration logic for the unreferenced JPEG
let bounds = [ [36.04500, 36.04500], [36.09550,  24.91000] ];
const touristMap = L.imageOverlay('./MC2-tourist.jpg', bounds, { opacity: 0.5 }).addTo(map);

for(let i = 0; i < data.length; i += 500) {
    if(data[i].lat && data[i].long) {
        L.circleMarker([data[i].lat, data[i].long], {
            radius: 2, color: '#0055ff', stroke: false
        }).addTo(map);
    }
}"""

code_fusion = """# Aligning temporal dimensions for fusion
cc_df['Date'] = cc_df['timestamp'].apply(lambda x: str(x).split(' ')[0])
loyalty_df.rename(columns={'timestamp': 'Date'}, inplace=True)

# Executing Left Join using a composite key
matched_df = pd.merge(
    cc_df,
    loyalty_df,
    on=['Date', 'location', 'price'],
    how='outer'
)
matched_df.drop_duplicates(inplace=True)"""

code_gps_clustering = """# Extract stay duration and build temporal collision matrix
time_start = stay['start_time'] - pd.Timedelta(seconds=600)
time_end = stay['end_time'] + pd.Timedelta(seconds=600)

# Intersect GPS window with credit card transactions
mask = (cc_df['timestamp'] >= time_start) & (cc_df['timestamp'] <= time_end)
transactions = cc_df[mask]

# Accumulate matches to establish one mapping
for _, txn in transactions.iterrows():
    j = all_locations.index(txn['location'])
    match_matrix[cluster_id][j] += 1"""

code_collision = """
for cc_id in unique_ccs:
    target_txns = cc_df[cc_df['last4ccnum'] == cc_id]
    for car_id in all_cars:
        car_gps = gps_df[gps_df['id'] == car_id]

        merged = pd.merge_asof(
            target_txns, car_gps,
            left_on='timestamp', right_on='Timestamp',
            direction='nearest', tolerance=pd.Timedelta('15min')
        )
        valid_matches = merged.dropna(subset=['Timestamp']).copy()

        hits = 0
        if not valid_matches.empty:
            valid_matches['dist'] = calculate_distance(
                valid_matches['cc_lat'], valid_matches['cc_lon'],
                valid_matches['gps_lat'], valid_matches['gps_lon']
            )
            hits = (valid_matches['dist'] <= 0.25).sum()

        hit_matrix.append({'CC_ID': cc_id, 'Car_ID': car_id, 'Hits': hits, 'Hit_Rate': hits/len(target_txns)})

df_company = df_hits[df_hits['Car_ID'].isin(company_cars)].sort_values(by=['Hit_Rate', 'Hits'], ascending=[False, False])
"""

code_personnel = """
valid_personnel = personnel_df.dropna(subset=['CarID']).drop_duplicates(subset=['CarID'])
car_info_map = valid_personnel.set_index('CarID')[['FullName', 'CurrentEmploymentType']].to_dict('index')

final_rows = []
for _, row in result_df.iterrows():
    car_id = row['Matched_CarID']

    if pd.isna(car_id):
        row['FullName'] = '无车基层员工'    
        row['Vehicle_Type'] = '无关联车辆'
    elif car_id in truck_ids:
        row['FullName'] = '未定业务人员'   
        row['Vehicle_Type'] = '公共卡车'
    else:
        p_info = car_info_map.get(car_id, {})
        row['FullName'] = p_info.get('FullName', '系统外人员')
        row['Vehicle_Type'] = '公司专属配车'

    final_rows.append(row)
"""

code_relationship = """def calculate_edge_weight(loc_norm, travel_norm, consume_norm, dept_a, dept_b):
    base_score = 0.4 * loc_norm + 0.4 * travel_norm + 0.2 * consume_norm

    if dept_a == dept_b and dept_a != '未知部门':
        structure_factor = 0.8
    else:
        structure_factor = 1.2

    return base_score * structure_factor"""

code_clustering = """G = nx.Graph()
for _, row in strong_relation.iterrows():
    G.add_edge(row['source'], row['target'], weight=row['score'])

deg_dict = dict(G.degree(weight='weight'))
between_dict = nx.betweenness_centrality(G, weight='weight')

communities_list = [list(c) for c in greedy_modularity_communities(G)]"""

# ==========================================
# 右侧主体内容定义
# ==========================================
main_content = html.Div([
    html.H2("数据准备与预处理", className="fw-bold text-center mb-5", style={"color": "black"}),

    # --- Section 1 ---
    html.H4("1. 空间数据处理与地图校准", id="section-1",
            className="fw-bold mb-4 border-bottom pb-2", style={"color": "black"}),
    html.P(
        "本次挑战提供了传统格式的地理空间数据以及一张缺乏空间参照系静态旅游地图，为实现基于网页的交互式可视分析系统构建，我们执行了以下两个关键的空间数据预处理步骤：",
        className="text-muted mb-4", style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.1rem"}),

    html.H5("1.1 数据清洗与格式转换", id="section-1-1", className="fw-bold mt-4 mb-3",
            style={"color": "black"}),
    html.P(
        "我们利用空间处理计算包对阿比拉市的原始矢量文件进行解析，现实世界的数据往往存在拓扑异常，因此我们部署了逐行校验机制以拦截并丢弃损坏或空缺的几何对象，将空间数据最终被转换为适合前端渲染的规范格式。",
        className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),
    render_code_block(code_sanitization),

    html.H5("1.2 旅游地图坐标对齐", id="section-1-2", className="fw-bold mt-5 mb-3",
            style={"color": "black"}),
    html.P(
        "为攻克静态旅游地图缺乏内在的地理坐标系统这一难题，我们开发了专门的交互式校准控制台。通过将旅游地图作为具有可调透明度的图层叠加至标准底图上方，并映射清洗后的路网与高频轨迹散点，对其边界进行了人工平移与拉伸微调，为后续精准的空间图表渲染确立了严密的边界坐标基准。",
        className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),
    render_code_block(code_calibration),

    html.P("经过高精度校准的地理对齐结果展示如下：",
           className="text-muted mt-2 mb-3", style={"textAlign": "justify", "lineHeight": "1.8"}),
    html.Div(html.Img(src="/assets/position_matching.png", className="img-fluid rounded shadow-sm border"),
             className="text-center mb-5"),

    # --- Section 2 ---
    html.H4("2. 财务数据融合", id="section-2", className="fw-bold mb-4 mt-5 border-bottom pb-2",
            style={"color": "black"}),

    html.H5("2.1 笛卡尔积隔离", id="section-2-1", className="fw-bold mt-4 mb-3",
            style={"color": "black"}),
    html.P(
        "会员卡记录仅保留了消费日期参数而完全缺失具体时间戳，若机械地依据日期地点与金额进行数据连接，同一时空下相同金额的多笔独立消费极易触发笛卡尔积乘数效应。通过全局遍历检索，我们成功捕获了三组高度相似的歧义账单数据：",
        className="text-muted mb-3", style={"textAlign": "justify", "lineHeight": "1.8"}),

    # 插入歧义表格
    ambiguity_table,

    html.P(
        "为保障网络关系推断算法的绝对纯净度，我们在正式合并操作前已将上述高风险交叉数据予以提取并执行物理隔离，避免虚假映射对后续社交网络挖掘造成污染。",
        className="text-muted mb-4", style={"textAlign": "justify", "lineHeight": "1.8"}),

    html.H5("2.2 消费记录对齐", id="section-2-2", className="fw-bold mt-4 mb-3",
            style={"color": "black"}),
    html.P(
        "信用卡日志与会员卡流水各自具备独立的标识符，基于单人单卡对的基本推演准则，这些割裂的交易流必须被锚定至统一实体以构建完整的消费特征画像。在清除了潜在的歧义碰撞后，我们针对时间维度进行日期提取，随后结合地点、金额形成复合主键，执行外联结以整合异构数据集。",
        className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),
    render_code_block(code_fusion),

    # --- Section 3 ---
    html.H4("3. 地标经纬度确认", id="section-3", className="fw-bold mb-4 mt-5 border-bottom pb-2",
            style={"color": "black"}),

    html.H5("3.1 聚类与时空匹配", id="section-3-1", className="fw-bold mt-4 mb-3",
            style={"color": "black"}),
    html.P(
        "为了逆向推断未标识商铺的精确坐标，我们深度挖掘了公司车辆的连续运行轨迹，基于速度低于特定阈值且驻留时间符合物理常识的运动学规则提取有效停车点，随后引入无监督聚类算法提炼出三十余个稳定的地理质心，并结合动态驻留时间窗口与信用卡交易时间戳构建的时空碰撞矩阵实现了物理空间坐标到商铺名称的映射。",
        className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),
    render_code_block(code_gps_clustering),

    html.H5("3.2 人工校准", id="section-3-2", className="fw-bold mt-5 mb-3",
            style={"color": "black"}),
    html.P(
        "受制于地理临近性干扰，纯算法聚类不可避免地会引入特定拓扑失真现象，如紧邻商铺的质心合并或交通拥堵点误判。在此数据背景下，我们执行了系统性的人工参数修正，以最大化弥补时空关联分析的断层。",
        className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),

    dbc.Card(
        dbc.CardBody(
            dcc.Graph(figure=create_calibration_map(), config={'displayModeBar': False})
        ),
        className="mb-5 shadow-sm border-0 bg-light"
    ),

    # --- Section 4 ---
    html.H4("4. 消费与车辆信息对齐", id="section-4", className="fw-bold mb-4 mt-5 border-bottom pb-2",
            style={"color": "black"}),

    html.H5("4.1 消费流水与物理轨迹绑定", id="section-4-1", className="fw-bold mt-4 mb-3",
            style={"color": "black"}),
    html.P(
        "基于前期提炼的商铺精准经纬度坐标，我们引入了时空双重约束的匹配逻辑。首先，设定 15 分钟的动态容差窗口，提取距离交易时点最近的车辆定位数据；随后，计算交易商铺与此时车辆的物理直线距离，当两者距离小于 0.25 公里时，系统判定发生一次有效空间重合。通过将全量信用卡与车辆进行全排列交叉比对，计算每一种组合的时空重合率，从而构建出底层关联概率矩阵。",
        className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),
    html.P(
        "深入分析数据结构发现，系统中包含 35 辆员工专属私家车和 5 辆可被多人调用的公共卡车（101、104、105、106、107号），而活跃信用卡达 55 张。基于此特征，我们确立了分层匹配规则：第一步，针对 35 辆专属配车，提取重合率最高的记录确立基准绑定；第二步，对剩余 20 张卡片进行剥离——若匹配至卡车，则归类为公共卡车调用；若高频重合已绑定的私家车，则认定为次级卡从属绑定，推测存在卡片私下互借的异常行为；若彻底无物理轨迹匹配，则锁定为未匹配车辆员工。",
        className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),
    render_code_block(code_collision),

    html.H5("4.2 人事特征注入与交叉验证", id="section-4-2", className="fw-bold mt-5 mb-3",
            style={"color": "black"}),
    html.P(
        "为进一步还原映射关系的业务属性，我们将前置的纯时空推演模型与人事档案 car-assignments.csv 进行了特征注入对接，人事数据显示 GAStech 公司中恰好有 9 名员工未被分配专属车辆。",
        className="text-muted mb-2", style={"textAlign": "justify", "lineHeight": "1.8"}),
    html.P(
        "匹配过程未输入任何人事先验知识的前提下，4.1 节识别出有 7 张卡片属于公共卡车调用，2 张卡片属于未分配车辆，两者合计恰好对齐这 9 名特殊员工。这一底层物理轨迹推演与上层人事档案记录构成了强有力的闭环印证，证明了我们重构映射字典的极高精准度。",
        className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),
    render_code_block(code_personnel),

    # --- Section 5 ---
    html.H4("5. 非正式社交网络构建", id="section-5", className="fw-bold mb-4 mt-5 border-bottom pb-2",
            style={"color": "black"}),

    html.H5("5.1 成员密切关系衡量", id="section-5-1", className="fw-bold mt-4 mb-3",
            style={"color": "black"}),
    html.P(
        "基于员工的物理驻留轨迹同行记录以及线下联合财务消费频率，我们通过归一化处理构建了多维度的基础社交联系得分。为了将正常的业务往来与私人社交区分开，我们仅考虑非工作时间，并引入了组织架构滤波机制,当识别到两名员工隶属同一业务部门时，系统会对其基础得分乘以零点八的折损系数，以剔除日常工作带来的数据噪音；反之，若两人跨越部门建制产生高频交集，系统则赋予一点二倍的权重奖励，借此精准剥离出隐藏在企业正式架构下的非正式人际纽带。",
        className="text-muted", style={"textAlign": "justify", "lineHeight": "1.8"}),
    render_code_block(code_relationship),

    html.H5("5.2 非正式群体聚类", id="section-5-2", className="fw-bold mt-5 mb-3",
            style={"color": "black"}),
    html.P(
        "完成全量员工两两之间的密切度量化后，系统截取得分排名前百分之二十五的强关联数据作为拓扑结构的有效边构建无向加权网络模型，并引入了基于模块度最大化的贪心算法，在没有任何先验标签的干预下自底向上地发掘网络中高度内聚的私人圈层。同时，系统计算了每个节点的度数与介数中心性，以量化该员工在非正式群体内部的枢纽价值与信息控制力。",
        className="text-muted mb-2", style={"textAlign": "justify", "lineHeight": "1.8"}),
    render_code_block(code_clustering),



], className="px-md-4 mb-5")

# ==========================================
# 整体页面布局组合
# ==========================================
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(sidebar, width=3, className="border-end border-light pe-4 d-none d-md-block"),
            dbc.Col(main_content, width=9)
        ], className="my-5")
    ], fluid=False, style={"maxWidth": "1200px"})
])