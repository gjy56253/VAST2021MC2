# tasks/task1.py
import dash
from dash import html, dcc, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ==========================================
# 坐标配置
# ==========================================
LOCATION_COORDS = {
    "Frydos Autosupply n' More": {"lat": 36.0592994, "lon": 24.9057484},
    "Ouzeri Elian": {"lat": 36.0531932, "lon": 24.8728752},
    "Katerina's Cafe": {"lat": 36.0551361, "lon": 24.8990536},
    "Hippokampos": {"lat": 36.0585, "lon": 24.899},
    "Kronos Mart": {"lat": 36.0667928, "lon": 24.8491001},
    "Hallowed Grounds": {"lat": 36.0655439, "lon": 24.8854923},
    "Brew've Been Served": {"lat": 36.0566627, "lon": 24.9029160},
    "Guy's Gyros": {"lat": 36.0591606, "lon": 24.8987103},
    "U-Pump": {"lat": 36.0683885, "lon": 24.8687553}
}


# ==========================================
# 布局模块 (Layout)
# ==========================================
def get_layout():
    # 提前把 ALL, Saturday, Else 这三个特殊选项放进列表里
    dropdown_options = [
        {'label': '所有日期', 'value': 'ALL'},
        {'label': '周末', 'value': 'Saturday'},
        {'label': '工作日', 'value': 'Else'}
    ]
    try:
        temp_df = pd.read_csv('data/cc_loyalty_matched.csv', encoding='latin1')
        unique_dates = sorted(temp_df['Date'].dropna().unique())
        for date in unique_dates:
            # 接着把每天的具体日期追加进去
            dropdown_options.append({'label': date, 'value': date})
    except:
        pass

    return html.Div([
        dbc.Row([
            # ==========================================
            # 左侧栏：文章目录 (已更新)
            # ==========================================
            dbc.Col([
                html.Div([
                    html.H5("目录", className="fw-bold mb-3"),
                    html.Ul([
                        html.Li(html.A("1.1 消费热点识别", href="#section-1-1",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        html.Li(html.A("1.2 异常行为检测", href="#section-1-2",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        html.Ul([
                            html.Li(html.A("1.2.1 卡片归属异常", href="#section-1-2-1",
                                           className="text-decoration-none text-muted")),
                            html.Li(html.A("1.2.2 消费金额异常", href="#section-1-2-2",
                                           className="text-decoration-none text-muted")),
                            html.Li(html.A("1.2.3 幽灵交易异常", href="#section-1-2-3",
                                           className="text-decoration-none text-muted")),
                            html.Li(html.A("1.2.4 时空逻辑悖论", href="#section-1-2-4",
                                           className="text-decoration-none text-muted")),
                        ], className="list-unstyled ms-3 mb-2"),
                        html.Li(html.A("1.3 数据修正建议", href="#section-1-3",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                    ], className="list-unstyled")
                ], className="sticky-top pt-4")
            ], width=3, className="border-end border-light pe-4"),

            # ==========================================
            # 右侧栏：正文内容
            # ==========================================
            dbc.Col([
                html.H2("任务一：消费热点分析与异常检测", className="mb-4 mt-4 text-primary"),
                html.Hr(),

                # --- 1.1 热点识别 ---
                html.H3("1.1 消费热点识别", id="section-1-1", className="mb-3"),
                html.P(
                    "基于交易记录热力图分析，所有日期的消费活动主要集中在非工作时间的餐饮场所，出现早、中、晚三个高峰，其中周末的消费时段则被压缩在13:00至20:00之间，整体上与日常消费模式相符合。基于此对局部进行观察，发现在1月12日与1月19日凌晨3:00的 Kronos Mart 均出现了违背常规逻辑的非营业时间异常交易。\n\n",
                    className="text-justify text-muted"
                ),
                dbc.Card(dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("选择日期筛选条件：", className="fw-bold"),
                            dcc.Dropdown(id='task1-freq-date-dropdown', options=dropdown_options, value='ALL',
                                         clearable=False, className="mb-3")
                        ], width=6)
                    ]),
                    dcc.Loading(dcc.Graph(id='task1-freq-heatmap-graph', config={'toImageButtonOptions': {'format': 'png', 'scale': 3}}))
                ]), className="mb-5 shadow-sm border-0 bg-light"),

                # --- 1.2 异常分析 ---
                html.H3("1.2 异常行为检测", id="section-1-2", className="mt-5 mb-3 pt-3 border-top"),
                # 颜色改为默认黑色

                # 1.2.1 Card Ownership Anomalies
                html.H4("1.2.1 卡片归属异常", id="section-1-2-1", className="mt-4 mb-3"),
                html.P(
                    "对非一对一卡片归属关系的深入调查揭示了两种显著的异常映射模式：其一是单张卡片被两张异类卡片交替使用的单向共用模式，其二是两对卡片在彼此之间完全交叉替换使用的对称互用模式，反映出潜在的有组织身份混淆策略。特别是针对对称互用模式，例如信用卡 4795 与 8332 呈现出频繁交叉共享会员卡 L8566 与 L2070 的现象，可合理推测持卡主体之间存在极其密切的非正式人际纽带。\n\n",
                    className="text-justify text-muted"
                ),
                dbc.Card(dbc.CardBody([
                    dcc.Dropdown(id='task1-network-filter', options=[{'label': '所有关联记录', 'value': 'ALL'},
                                                                     {'label': '仅显示异常记录', 'value': 'ANOMALIES'}],
                                 value='ANOMALIES', clearable=False, className="mb-3"),
                    # 将 config 放到 dcc.Graph 的括号里面
                    dcc.Loading(dcc.Graph(id='task1-sankey-graph',
                                          config={'toImageButtonOptions': {'format': 'png', 'scale': 3}}))
                ]), className="mb-5 shadow-sm border-0 bg-light"),

                # --- 1.2.2 隐秘资金与套现异常 ---
                html.H4("1.2.2 消费金额异常", id="section-1-2-2", className="mt-4 mb-3"),

                html.P(
                    "通过时间与空间的交叉比对，我们分离出359笔信用卡与会员卡扣款金额存在显著差异的记录。一个突出的异常出现在1月13日的 Frydos Autosupply n' More，信用卡 9551 扣款高达 10000.00 美元，而对应的会员卡记录仅为 87.57 美元。此外，时空对齐分析还揭示，1月14日在 Abila Airport，两张不同的信用卡 8642 与 2276 被同时关联至同一张会员卡 L7761。",
                    className="text-justify text-muted"
                ),

                # [对角线散点图]
                dbc.Card(dbc.CardBody([
                    dcc.Loading(dcc.Graph(id='task1-discrepancy-scatter-graph', config={'toImageButtonOptions': {'format': 'png', 'scale': 3}}))
                ]), className="mb-5 shadow-sm border-0 bg-white"),

                # 1.2.3 交易异常
                html.H4("1.2.3 幽灵交易异常", id="section-1-2-2", className="mt-4 mb-3"),

                # 第一段文字：说明热力图并引出异常交易
                html.P(
                    "通过生成交易金额热力图，我们观察到绝大多数消费均符合已识别的常规热点分布。然而，1月12日与1月19日凌晨3:00左右在 Kronos Mart 均出现了极度异常的交易集群，于是我们进一步对这些特定记录进行隔离与提取。\n\n",
                    className="text-justify text-muted"
                ),

                # 金额热力图
                dbc.Card(dbc.CardBody([
                    dcc.Dropdown(id='task1-date-dropdown', options=dropdown_options, value='ALL', clearable=False,
                                 className="mb-3"),
                    dcc.Loading(dcc.Graph(id='task1-heatmap-graph', config={'toImageButtonOptions': {'format': 'png', 'scale': 3}}))
                ]), className="mb-3 shadow-sm border-0 bg-light"),

                # 第二段文字：移动到热力图和表格之间，并去掉了红色 (text-danger) 和粗体 (fw-bold)
                html.P(
                    "可以发现这两次异常交易均缺乏对应的会员卡流水，且值得注意的是，其中包含信用卡 8332，该卡片此前已被证实卷入了高度可疑的交叉共享网络中。\n\n",
                    className="text-justify text-muted"
                ),

                # 幽灵交易表 (放在文字正下方)
                dbc.Card(dbc.CardBody(html.Div(id='task1-ghost-table-container')),
                         className="mb-5 shadow-sm border-0 bg-light"),

                # 1.2.4 瞬移悖论
                html.H4("1.2.4 时空逻辑悖论", id="section-1-2-3", className="mt-4 mb-3"),
                html.P(
                    "由于一人无法在短时间进行不同地点连续消费，于是对20分钟时间窗口内连续发生的交易进行空间映射分析，一共发现四起在物理现实中根本无法实现的跨城瞬移事件。其中最为可疑的是信用卡 9551 仅在1月13日当天就触发了两次这种违背空间规律的跳跃，同时该卡还卷入了前文提及的凌晨3:00幽灵交易事件，成为我们第一阶段最为怀疑的对象之一。\n\n",
                    className="text-justify text-muted"
                ),
                dbc.Card(dbc.CardBody([
                    dcc.Loading(dcc.Graph(id='task1-paradox-map-graph', config={'displayModeBar': True, 'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'], 'toImageButtonOptions': {'format': 'png', 'scale': 3}})),
                    html.Hr(className="my-4"),
                    html.Div(id='task1-paradox-table-container')
                ]), className="mb-5 shadow-sm border-0 bg-light"),

                # --- 1.3 修正措施 ---
                # --- 1.3 数据修正建议 ---
                html.H4("1.3 数据修正建议", id="section-1-3", className="mt-5 mb-3", style={'color': 'black'}),

                html.P([
                    "为消除数据盲区，我们提出以下两项数据库修正措施：", html.Br(),
                    "1. 引入车辆GPS数据，依据时间与空间维度而非精确金额进行记录对齐，以此捕获隐秘的套现行为并验证异常。",
                    html.Br(),
                    "2. 引入图论算法以识别高度对称交换集群中的共享卡片，推测交换使用卡片的真实对应关系。"
                ], className="text-justify text-muted"),

            ], width=9, className="ps-5")
        ])
    ])


# ==========================================
# 回调逻辑模块 (保持原样)
# ==========================================
@callback(Output('task1-freq-heatmap-graph', 'figure'), Input('task1-freq-date-dropdown', 'value'))
def update_freq_heatmap(selected_date):
    try:
        import plotly.express as px
        df = pd.read_csv('data/cc_loyalty_matched.csv', encoding='latin1')

        # 智能识别列名大小写，防止 KeyError 崩溃
        date_col = 'Date' if 'Date' in df.columns else 'date'

        df['Hour'] = pd.to_datetime(df['timestamp']).dt.hour

        # 防御性判断：处理页面初次加载时下拉菜单值为空(None)的情况
        if not selected_date or selected_date == 'ALL':
            f_df = df
        elif selected_date == 'Saturday':
            # 兼容带破折号和带斜杠等多种可能的日期字符串格式
            saturdays = ['2014-01-11', '2014-01-18', '1/11/2014', '1/18/2014', '01/11/2014', '01/18/2014']
            f_df = df[df[date_col].isin(saturdays)]
        elif selected_date == 'Else':
            saturdays = ['2014-01-11', '2014-01-18', '1/11/2014', '1/18/2014', '01/11/2014', '01/18/2014']
            f_df = df[~df[date_col].isin(saturdays)]
        else:
            f_df = df[df[date_col] == selected_date]

        return px.density_heatmap(f_df, x="Hour", y="location", nbinsx=24, color_continuous_scale="Blues")

    except Exception as e:
        # 拦截致命错误，将其转换为图表标题显示，服务器不再崩溃
        import plotly.graph_objects as go
        return go.Figure().update_layout(title=f"⚠️ Frequency Chart Error: {str(e)}")

@callback(
    Output('task1-sankey-graph', 'figure'),
    Input('task1-network-filter', 'value')
)
def update_sankey(filter_type):
    try:
        df = pd.read_csv('data/cc_loyalty_matched.csv', encoding='latin1')
    except:
        return go.Figure()

    mapped = df.dropna(subset=['loyaltynum']).copy()

    if filter_type == 'ANOMALIES':
        mapped = mapped[(mapped.groupby('last4ccnum')['loyaltynum'].transform('nunique') > 1) | (
                    mapped.groupby('loyaltynum')['last4ccnum'].transform('nunique') > 1)]

    links = mapped.groupby(['last4ccnum', 'loyaltynum']).size().reset_index(name='value')
    all_nodes = ["CC: " + str(cc) for cc in links['last4ccnum'].unique()] + ["Loyalty: " + str(loy) for loy in
                                                                             links['loyaltynum'].unique()]

    # 浅灰色极简节点
    node_color = "#D5D8DC"
    # 高级灰蓝半透明连线
    link_color = "rgba(134, 153, 165, 0.5)"

    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=25,
            thickness=12,  # 回归极细的节点，文字会自动停留在外侧
            line=dict(color="white", width=4),  # 保留纯白粗边框，这会在视觉上切断线条，形成镂空距离感
            label=all_nodes,
            color=node_color
        ),
        link=dict(
            source=[all_nodes.index("CC: " + str(c)) for c in links['last4ccnum']],
            target=[all_nodes.index("Loyalty: " + str(l)) for l in links['loyaltynum']],
            value=links['value'],
            color=link_color
        )
    )])

    # 增加左右 margin (l=80, r=80)，让外侧文字有充足的显示空间
    fig.update_layout(
        height=600,
        margin=dict(l=80, r=80, t=30, b=30),
        font=dict(color="#2C3E50", size=12, family="Arial"),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig


# ==========================================
# 交互逻辑模块: 1.2.2 隐秘资金套现 (对角线散点图) - 防爆精准排雷版
# ==========================================
@callback(
    Output('task1-discrepancy-scatter-graph', 'figure'),
    Input('task1-freq-date-dropdown', 'value')
)
def update_discrepancy_scatter(_):
    try:
        cc = pd.read_csv('data/cc_data.csv', encoding='latin1')
        loy = pd.read_csv('data/loyalty_data.csv', encoding='latin1')

        cc.columns = [col.lower() for col in cc.columns]
        loy.columns = [col.lower() for col in loy.columns]

        cc['timestamp'] = pd.to_datetime(cc['timestamp'])
        cc['date'] = cc['timestamp'].dt.date
        loy['date'] = pd.to_datetime(loy['timestamp']).dt.date

        # --- 【防爆核心代码：精准排雷法】 ---
        # 0. 增加临时唯一ID，方便追踪和剔除
        cc['tmp_cc_id'] = range(len(cc))
        loy['tmp_loy_id'] = range(len(loy))

        # 1. 寻找金额完全一致的“乖宝宝”（完美匹配的大部队）
        perfect_match = pd.merge(cc, loy, on=['date', 'location', 'price'], suffixes=('_cc', '_loy'))
        perfect_match['price_cc'] = perfect_match['price']
        perfect_match['price_loy'] = perfect_match['price']
        perfect_match['delta'] = 0.0

        # 2. 利用临时ID，从原数据中把“乖宝宝”剔除，留下金额对不上的“刺头”
        cc_leftovers = cc[~cc['tmp_cc_id'].isin(perfect_match['tmp_cc_id'])]
        loy_leftovers = loy[~loy['tmp_loy_id'].isin(perfect_match['tmp_loy_id'])]

        # 3. 仅对剩下的“刺头”进行放宽条件的日期+地点强制匹配
        anomalies = pd.merge(cc_leftovers, loy_leftovers, on=['date', 'location'], suffixes=('_cc', '_loy'))
        anomalies['delta'] = anomalies['price_cc'] - anomalies['price_loy']

        # 4. 强制去重，防止极少数“刺头”扎堆引发微型爆炸
        anomalies = anomalies.drop_duplicates(subset=['timestamp_cc', 'location', 'last4ccnum'])
        # -----------------------------------

        # 【核心分类】
        normal_df = perfect_match  # 正常交易 (灰色点)
        cashback_df = anomalies[anomalies['delta'] > 1.0]  # 异常A：信用卡刷得多（套现，铁锈红）
        split_df = anomalies[anomalies['delta'] < -1.0]  # 异常B：会员卡记录得多（混合支付，深橙色）

        # 动态计算图表的坐标轴最大值，防止红点被切出画面外
        max_cc = max(perfect_match['price_cc'].max(), anomalies['price_cc'].max()) if not anomalies.empty else \
        perfect_match['price_cc'].max()
        max_loy = max(perfect_match['price_loy'].max(), anomalies['price_loy'].max()) if not anomalies.empty else \
        perfect_match['price_loy'].max()
        max_val = max(max_cc, max_loy) * 1.05

    except Exception as e:
        print(f"Error in Scatter Plot: {e}")
        return go.Figure().update_layout(title="⚠️ Error: Requires cc_data.csv and loyalty_data.csv in data/ folder")

    fig = go.Figure()

    # 1. 正常数据点 (灰色)
    fig.add_trace(go.Scatter(
        x=normal_df['price_loy'], y=normal_df['price_cc'],
        mode='markers',
        name='Matched',
        marker=dict(color='rgba(149, 165, 166, 0.4)', size=7),
        hovertemplate="<b>Normal Transaction</b><br>CC: %{customdata[0]} | Loy: %{customdata[1]}<br>Location: %{customdata[2]}<br>Loyalty Price: $%{x}<br>Credit Card: $%{y}<extra></extra>",
        customdata=normal_df[['last4ccnum', 'loyaltynum', 'location']]
    ))

    # 2. 异常A: 套现数据点 (铁锈红，对角线上方)
    fig.add_trace(go.Scatter(
        x=cashback_df['price_loy'], y=cashback_df['price_cc'],
        mode='markers',
        name='Anomaly: CC > Loy',
        marker=dict(color='#C0392B', size=9, line=dict(color='white', width=1)),
        # 【修改点】：在悬停模板中加入 CC 和 Loy 的标识
        hovertemplate="<b>Cash-Back Anomaly!</b><br>CC: %{customdata[3]} | Loy: %{customdata[4]}<br>Location: %{customdata[0]}<br>Time: %{customdata[1]}<br>CC Price: $%{y}<br>Loyalty Price: $%{x}<br><b>Extracted Cash: $%{customdata[2]:.2f}</b><extra></extra>",
        # 【修改点】：将 last4ccnum 和 loyaltynum 传入 customdata 的第3和第4位
        customdata=cashback_df[['location', 'timestamp_cc', 'delta', 'last4ccnum', 'loyaltynum']]
    ))

    # 3. 异常B: 混合支付/积分盗用 (深橙色，对角线下方)
    split_df_display = split_df.copy()
    split_df_display['abs_delta'] = split_df_display['delta'].abs()

    fig.add_trace(go.Scatter(
        x=split_df['price_loy'], y=split_df['price_cc'],
        mode='markers',
        name='Anomaly: Loy > CC',
        marker=dict(color='#E67E22', size=9, line=dict(color='white', width=1)),
        # 【修改点】：同样加入卡号标识
        hovertemplate="<b>Split Payment Anomaly!</b><br>CC: %{customdata[3]} | Loy: %{customdata[4]}<br>Location: %{customdata[0]}<br>Time: %{customdata[1]}<br>CC Price: $%{y}<br>Loyalty Price: $%{x}<br><b>Hidden/Cash Paid: $%{customdata[2]:.2f}</b><extra></extra>",
        customdata=split_df_display[['location', 'timestamp_cc', 'abs_delta', 'last4ccnum', 'loyaltynum']]
    ))

    # 4. Y=X 基准辅助线
    fig.add_shape(
        type="line", x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color="#7F8C8D", dash="dash", width=1)
    )

    # 5. 布局美化
    fig.update_layout(
        xaxis_title="Loyalty Record Amount ($)",
        yaxis_title="Credit Card Charge Amount ($)",
        height=550,
        margin=dict(l=60, r=40, t=20, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white',

        # 将图例稳稳地固定在右上角，防止遮挡重要散点
        legend=dict(
            yanchor="top", y=0.99,
            xanchor="right", x=0.99,
            bgcolor="rgba(255,255,255,0.9)"
        ),

        xaxis=dict(showgrid=True, gridcolor='#F2F3F4', zerolinecolor='#E5E7E9', range=[0, max_val]),
        yaxis=dict(showgrid=True, gridcolor='#F2F3F4', zerolinecolor='#E5E7E9', range=[0, max_val])
    )

    return fig


@callback(Output('task1-heatmap-graph', 'figure'), Input('task1-date-dropdown', 'value'))
def update_heatmap(selected_date):
    try:
        import plotly.express as px
        df = pd.read_csv('data/cc_loyalty_matched.csv', encoding='latin1')
        date_col = 'Date' if 'Date' in df.columns else 'date'

        df['Hour'] = pd.to_datetime(df['timestamp']).dt.hour

        if not selected_date or selected_date == 'ALL':
            a_df = df
        elif selected_date == 'Saturday':
            saturdays = ['2014-01-11', '2014-01-18', '1/11/2014', '1/18/2014', '01/11/2014', '01/18/2014']
            a_df = df[df[date_col].isin(saturdays)]
        elif selected_date == 'Else':
            saturdays = ['2014-01-11', '2014-01-18', '1/11/2014', '1/18/2014', '01/11/2014', '01/18/2014']
            a_df = df[~df[date_col].isin(saturdays)]
        else:
            a_df = df[df[date_col] == selected_date]

        return px.density_heatmap(a_df, x="Hour", y="location", z="price", histfunc="sum", nbinsx=24,
                                  color_continuous_scale="YlOrRd")

    except Exception as e:
        import plotly.graph_objects as go
        return go.Figure().update_layout(title=f"⚠️ Price Chart Error: {str(e)}")


@callback(
    Output('task1-ghost-table-container', 'children'),
    [Input('task1-date-dropdown', 'value'),
     Input('task1-heatmap-graph', 'hoverData')]  # 核心引入：监听热力图的鼠标悬停交互数据
)
def update_ghost_table(selected_date, hover_data):
    try:
        df = pd.read_csv('data/cc_loyalty_matched.csv', encoding='latin1')
        date_col = 'Date' if 'Date' in df.columns else 'date'

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['Hour'] = df['timestamp'].dt.hour

        # 1. 联动过滤逻辑判断
        if hover_data and 'points' in hover_data and len(hover_data['points']) > 0:
            # 【状态 A：鼠标有悬停】从热力图传递的数据中提取当前色块的小时(x)和地点(y)
            target_hour = hover_data['points'][0]['x']
            target_loc = hover_data['points'][0]['y']

            # 基础日期过滤（确保与下拉菜单选择的范围同步）
            if not selected_date or selected_date == 'ALL':
                date_df = df
            elif selected_date == 'Saturday':
                saturdays = ['2014-01-11', '2014-01-18', '1/11/2014', '1/18/2014', '01/11/2014', '01/18/2014']
                date_df = df[df[date_col].isin(saturdays)]
            elif selected_date == 'Else':
                saturdays = ['2014-01-11', '2014-01-18', '1/11/2014', '1/18/2014', '01/11/2014', '01/18/2014']
                date_df = df[~df[date_col].isin(saturdays)]
            else:
                date_df = df[df[date_col] == selected_date]

            # 执行精确的时空碰撞过滤
            ghost_txns = date_df[(date_df['Hour'] == target_hour) & (date_df['location'] == target_loc)]

        else:
            # 【状态 B：默认初始状态】一打开页面没有任何悬停时，强制锁定 1月19日 凌晨3点 的这笔特殊交易
            jan_19_formats = ['2014-01-19', '1/19/2014', '01/19/2014']
            ghost_txns = df[(df[date_col].isin(jan_19_formats)) & (df['Hour'] == 3)]

        # 2. 排序与数据格式化
        ghost_txns = ghost_txns.sort_values('timestamp').copy()
        ghost_txns['timestamp'] = ghost_txns['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        ghost_txns['loyaltynum'] = ghost_txns['loyaltynum'].fillna('UNRECORDED (NaN)')

        # 3. 渲染数据表格
        return dash_table.DataTable(
            data=ghost_txns.to_dict('records'),
            columns=[{"name": i, "id": i} for i in ['timestamp', 'location', 'price', 'last4ccnum', 'loyaltynum']],
            style_header={
                'backgroundColor': '#ffe6e6',
                'color': '#8b0000',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'border': '1px solid #ffcccc'
            },
            style_cell={'textAlign': 'center', 'padding': '10px'},
            style_data={'border': '1px solid #ddd'},
            style_data_conditional=[
                # 只保留缺失会员卡的红色警告，删除了 8332 的黄色高亮
                {
                    'if': {'column_id': 'loyaltynum', 'filter_query': '{loyaltynum} = "UNRECORDED (NaN)"'},
                    'color': 'red',
                    'fontWeight': 'bold',
                    'backgroundColor': '#fff0f0'
                }
            ]
        )
    except Exception as e:
        return html.Div(f"⚠️ 联动表格渲染错误: {str(e)}", style={'color': 'red', 'padding': '20px'})


@callback([Output('task1-paradox-map-graph', 'figure'), Output('task1-paradox-table-container', 'children')],
          Input('task1-date-dropdown', 'value'))
def update_paradox_visuals(_):
    try:
        import plotly.graph_objects as go
        from dash import dash_table
        df = pd.read_csv('data/cc_loyalty_matched.csv', encoding='latin1')
    except:
        return go.Figure(), html.Div()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_cc = df.dropna(subset=['last4ccnum']).sort_values(['last4ccnum', 'timestamp']).copy()

    # 获取前一次交易的时间、地点，【新增】前一次交易的会员卡号
    df_cc['prev_time'] = df_cc.groupby('last4ccnum')['timestamp'].shift(1)
    df_cc['prev_loc'] = df_cc.groupby('last4ccnum')['location'].shift(1)
    df_cc['prev_loyalty'] = df_cc.groupby('last4ccnum')['loyaltynum'].shift(1)

    df_cc['time_diff'] = (df_cc['timestamp'] - df_cc['prev_time']).dt.total_seconds() / 60.0

    # 筛选 20 分钟以内的异常瞬移
    anomalies = df_cc[
        (df_cc['location'] != df_cc['prev_loc']) &
        (df_cc['time_diff'] <= 20) &
        (df_cc['time_diff'] > 0)
        ].copy()

    # 格式化数据，提升表格的美观度和可读性
    anomalies['loyaltynum'] = anomalies['loyaltynum'].fillna('N/A')
    anomalies['prev_loyalty'] = anomalies['prev_loyalty'].fillna('N/A')
    anomalies['timestamp'] = anomalies['timestamp'].dt.strftime('%m-%d %H:%M')
    anomalies['prev_time'] = anomalies['prev_time'].dt.strftime('%m-%d %H:%M')
    anomalies['time_diff'] = anomalies['time_diff'].round(1).astype(str) + ' min'

    # 绘制轨迹图
    fig = go.Figure()
    fig.add_layout_image(
        dict(source="/assets/MC2-tourist.jpg", xref="x", yref="y", x=24.82450, y=36.09550, sizex=0.0855, sizey=0.0505,
             sizing="stretch", layer="below"))

    for _, row in anomalies.iterrows():
        loc1, loc2 = row['prev_loc'], row['location']
        if loc1 in LOCATION_COORDS and loc2 in LOCATION_COORDS:
            fig.add_trace(
                go.Scatter(mode="lines+markers", x=[LOCATION_COORDS[loc1]['lon'], LOCATION_COORDS[loc2]['lon']],
                           y=[LOCATION_COORDS[loc1]['lat'], LOCATION_COORDS[loc2]['lat']],
                           marker={'size': 10, 'color': '#E74C3C'}, line={'color': '#E74C3C', 'width': 3},
                           name=f"CC: {row['last4ccnum']}"))

    fig.update_layout(xaxis=dict(range=[24.82450, 24.91000], visible=False),
                      yaxis=dict(range=[36.04500, 36.09550], visible=False), margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      height=450, showlegend=False)

    # 定义要展示的列，加入 prev_loyalty 和 loyaltynum 进行比对
    columns_to_show = ['last4ccnum', 'prev_time', 'prev_loc', 'prev_loyalty', 'timestamp', 'location', 'loyaltynum',
                       'time_diff']

    table = dash_table.DataTable(
        data=anomalies.to_dict('records'),
        columns=[{"name": i, "id": i} for i in columns_to_show],
        # 增加水平滚动保护，防止极端情况下撑破页面
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': '#34495E',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'fontSize': '13px'  # 【新增】表头字体稍微缩小
        },
        style_cell={
            'textAlign': 'center',
            'padding': '6px',  # 【修改】内边距从 10px 缩小到 6px，给数据腾出空间
            'fontSize': '12px',  # 【新增】将正文字体缩小为 12px
            'whiteSpace': 'normal',  # 【关键】允许超长文本（如地点名称）自动换行
            'height': 'auto'  # 【关键】配合换行使用，让行高自适应
        },
        style_data={'border': '1px solid #ddd'},
        style_data_conditional=[
            {'if': {'filter_query': '{last4ccnum} = 9551'}, 'backgroundColor': '#EBF5FB'}
        ]
    )
    return fig, table