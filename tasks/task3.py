# tasks/task3.py
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 强制接管底层 JSON 引擎，彻底消除 orjson 报错
import plotly.io as pio
pio.json.config.default_engine = 'json'

# ==========================================
# 0. 跨源安全数据加载
# ==========================================
def safe_read_csv(file_path):
    try:
        return pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception:
        try:
            return pd.read_csv(file_path, encoding='gbk')
        except Exception:
            return pd.read_csv(file_path, encoding='latin1')

# 加载我们在 preprocessing 中提前算好的特征宽表
try:
    df_certain = safe_read_csv('data/task3_certain_mapping.csv')
    df_uncertain = safe_read_csv('data/task3_uncertain_mapping.csv')

    for df in [df_certain, df_uncertain]:
        if not df.empty:
            if 'last4ccnum' in df.columns:
                df['last4ccnum'] = df['last4ccnum'].astype(str).str.replace('.0', '', regex=False)
            if 'loyaltynum' in df.columns:
                df['loyaltynum'] = df['loyaltynum'].astype(str).str.replace('.0', '', regex=False)

    # 动态提取部门供控制台筛选
    all_depts = ['所有关联记录']
    if 'CurrentEmploymentType' in df_certain.columns:
        depts = df_certain['CurrentEmploymentType'].dropna().unique().tolist()
        all_depts.extend([d for d in depts if d not in ['未知', '跨部门调用', 'nan']])
except Exception as e:
    print(f"数据加载警告: {e}")
    df_certain = pd.DataFrame()
    df_uncertain = pd.DataFrame()
    all_depts = ['所有关联记录']


# ==========================================
# 1. 桑基图构建引擎
# ==========================================
def build_sankey_fig(df, use_probability_color=False):
    if df.empty:
        return go.Figure().update_layout(title="暂无映射数据", plot_bgcolor='white', paper_bgcolor='white')

    cc_nodes = sorted(df['last4ccnum'].unique().tolist())
    name_nodes = sorted(df['FullName'].unique().tolist())
    loyalty_nodes = sorted(df['loyaltynum'].unique().tolist())

    # 规范化标签
    cc_labels = [f"CC: {c}" for c in cc_nodes]
    name_labels = [f"Emp: {n}" for n in name_nodes]
    loy_labels = [f"Loyalty: {l}" for l in loyalty_nodes]

    all_labels = cc_labels + name_labels + loy_labels
    node_map = {label: i for i, label in enumerate(all_labels)}

    sources, targets, values, link_colors = [], [], [], []

    # 统一的基础色调（深灰蓝），依靠 Alpha 通道体现概率深浅
    base_r, base_g, base_b = 52, 152, 219  # 对应 #3498db

    # 第一层：CC -> Employee
    for _, row in df.iterrows():
        s = node_map[f"CC: {row['last4ccnum']}"]
        t = node_map[f"Emp: {row['FullName']}"]
        sources.append(s)
        targets.append(t)

        val = row['Match_Count'] if 'Match_Count' in df.columns and pd.notna(row['Match_Count']) else 1
        values.append(val)

        if use_probability_color and 'Car_Share_Prob' in row:
            # 概率决定不透明度，不区别人名颜色
            alpha = max(0.15, min(float(row['Car_Share_Prob']), 0.95))
            link_colors.append(f"rgba({base_r}, {base_g}, {base_b}, {alpha})")
        else:
            # 确定性区域用浅灰色半透明连线 (与 task1 风格统一)
            link_colors.append("rgba(134, 153, 165, 0.5)")

    # 第二层：Employee -> Loyalty
    for _, row in df.iterrows():
        s = node_map[f"Emp: {row['FullName']}"]
        t = node_map[f"Loyalty: {row['loyaltynum']}"]
        sources.append(s)
        targets.append(t)

        val = row['Match_Count'] if 'Match_Count' in df.columns and pd.notna(row['Match_Count']) else 1
        values.append(val)

        if use_probability_color and 'Loyalty_Share_Prob' in row:
            alpha = max(0.15, min(float(row['Loyalty_Share_Prob']), 0.95))
            link_colors.append(f"rgba({base_r}, {base_g}, {base_b}, {alpha})")
        else:
            link_colors.append("rgba(134, 153, 165, 0.5)")

    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=25, thickness=12,
            line=dict(color="white", width=4),
            label=all_labels,
            color="#D5D8DC"
        ),
        link=dict(
            source=sources, target=targets, value=values, color=link_colors
        )
    )])

    fig.update_layout(
        height=550,
        margin=dict(l=80, r=80, t=30, b=30),
        font=dict(color="#2C3E50", size=12, family="Arial"),
        plot_bgcolor='white', paper_bgcolor='white'
    )
    return fig


# ==========================================
# 2. 布局模块 (Layout)
# ==========================================
def get_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H5("目录", className="fw-bold mb-3"),
                    html.Ul([
                        # 3.1 一级目录
                        html.Li(html.A("3.1 确定性身份解耦", href="#section-3-1",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        html.Ul([
                            html.Li(html.A("3.1.1 完美映射拓扑", href="#section-3-1-1",
                                           className="text-decoration-none text-muted")),
                        ], className="list-unstyled ms-3"),

                        # 3.2 一级目录
                        html.Li(html.A("3.2 不确定性推演", href="#section-3-2",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        html.Ul([
                            html.Li(html.A("3.2.1 异常类别宏观树状图", href="#section-3-2-1",
                                           className="text-decoration-none text-muted")),
                            html.Li(html.A("3.2.2 概率流向异质关联拓扑", href="#section-3-2-2",
                                           className="text-decoration-none text-muted")),
                            html.Li(html.A("3.2.3 幽灵集群审计报告", href="#section-3-2-3",
                                           className="text-decoration-none text-muted")),
                        ], className="list-unstyled ms-3"),

                        # 3.3 一级目录
                        html.Li(html.A("3.3 不确定性分析", href="#section-3-3",
                                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
                        html.Ul([
                            html.Li(html.A("3.3.1 数据不确定性", href="#section-3-3-1",
                                           className="text-decoration-none text-muted")),
                            html.Li(html.A("3.3.2 方法不确定性", href="#section-3-3-2",
                                           className="text-decoration-none text-muted")),
                        ], className="list-unstyled ms-3"),
                    ], className="list-unstyled")
                ], className="sticky-top pt-4")
            ], width=3, className="border-end border-light pe-4"),

            dbc.Col([
                html.H2("任务三：持卡人识别与不确定性量化", className="mb-4 mt-4 text-primary"),
                html.Hr(),

                # --- 3.1 确定性身份解耦 ---
                html.H3("3.1 确定性身份解耦", id="section-3-1", className="mb-3"),
                html.P(
                    "基于底层物理轨迹与财务交易频次的双向约束，我们在排除车辆互换及积分卡交叉干扰后，过滤提取出了完全符合官方记录的一对一映射清单，构成系统判定的铁证白名单。",
                    className="text-justify text-muted"
                ),

                # 3.1.1 完美映射拓扑
                html.H4("3.1.1 完美映射拓扑", id="section-3-1-1", className="mt-4 mb-3"),
                dbc.Card(dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("选择部门：", className="fw-bold"),
                            dcc.Dropdown(
                                id='task3-dept-dropdown',
                                options=[{'label': d, 'value': d} for d in all_depts],
                                value='所有关联记录',
                                clearable=False,
                                className="mb-3"
                            )
                        ], width=6)
                    ]),
                    dcc.Loading(dcc.Graph(id='task3-certain-sankey'))
                ]), className="mb-5 shadow-sm border-0 bg-light"),

                html.H3("3.2 不确定性推演", id="section-3-2", className="mt-5 mb-3 pt-3 border-top"),
                html.H4("3.2.1 异常类别宏观树状图", id="section-3-2-1", className="mt-4 mb-3"),
                dbc.Card(dbc.CardBody([
                    dcc.Loading(dcc.Graph(id='task3-uncertain-treemap')),
                    html.Hr(),
                    html.P("系统检测出的不确定性事件在宏观上可划分为四个特征区域", className="fw-bold mb-2"),
                    html.P("浅橙色区块表示物理轨迹异常，对应员工私下借用专属车辆与代刷行为；浅红色区块表示双重高危异常，揭示车辆与信用卡同时发生跨界共享的复杂关联；浅蓝色区块表示财务逻辑异常，反映信用卡与会员积分卡的交叉互用及信息隐匿现象；灰色区块代表幽灵与公共资源集群，归纳了由于使用公共卡车或无可见轨迹而无法进行独立空间定位的样本集合。", className="text-muted small")
                ]), className="mb-5 bg-light"),

                # 3.2.2 概率流向异质关联拓扑
                html.H4("3.2.2 概率流向异质关联拓扑", id="section-3-2-2", className="mt-4 mb-3"),
                html.P(
                    "本拓扑图全面连接了物理轨迹与财务流水中存在多维从属可能性的矛盾节点，为直观呈现推断置信度的量化衰减，采用流向线条的透明度深浅映射该关联的数学概率，其中路径色阶越深表明该信用卡、员工姓名与福利卡之间的多重对齐概率越高，置信度越强；相反，半透明的微弱流向则提示该链路属于偶发性异常或低置信度的跨界噪音，为后续的深层审计提供了全局流向依据。",
                    className="text-justify text-muted"
                ),
                dbc.Card(dbc.CardBody([
                    dcc.Loading(dcc.Graph(id='task3-uncertain-sankey',
                                          config={'toImageButtonOptions': {'format': 'png', 'scale': 3}}))
                ]), className="mb-5 shadow-sm border-0 bg-white"),

                # 3.2.3 幽灵集群审计报告
                html.H4("3.2.3 幽灵集群审计报告", id="section-3-2-3", className="mt-4 mb-3"),
                html.P(
                    "我们在人事记录中发现了 9 名未分配私家车的基层或现场员工，统内恰好残留了 7 张属于公共卡车的信用卡，以及 2 张彻底不产生任何轨迹的信用卡。",
                    className="text-justify text-muted"
                ),
                dbc.Card(dbc.CardBody([
                    html.H6("车辆未分配引起的底层系统数据盲区", className="fw-bold text-secondary mb-3"),
                    html.P(
                        "这 9 张无法定位具体车主的信用卡数量与公司内没有车的 9 名员工实现了数字对齐，但由于卡车属于多人多部门混合调度资源且无轨迹人员不可见，导致数据无法在此集群内部进行进一步的 1对1 解耦。",
                        className="text-muted"),

                    html.Div([
                        html.Strong("被审计无车人员九人名单"), html.Br(),
                        "Albina Prasert, Benito Corrales, Claudio Carriara, Henk Bodrogi, Isia Vann, Irene Vance 属于公共卡车调用群体",
                        html.Br(),
                        "Marelisa Shavan, Adra Ganes, Lucas Alcazar 属于无可见轨迹群体"
                    ], className="p-3 bg-white border rounded small text-dark mb-0")
                ]), className="mb-5 shadow-sm border-0 bg-light border-start border-secondary border-4"),

                # --- 3.3 不确定性分析 (Uncertainty Analysis) ---
                html.H3("3.3 不确定性分析", id="section-3-3", className="mt-5 mb-3 pt-3 border-top"),

                # 3.3.1 数据不确定性
                html.H4("3.3.1 数据不确定性", id="section-3-3-1", className="mt-4 mb-3"),
                html.Ul([
                    html.Li([
                        html.Span("档案与实际基数偏差：", className="fw-bold"),
                        "系统中活跃的信用卡数量远超公司官方登记的员工总数。这种基数不对等暗示了潜在的新员工登记遗漏或外部人员用卡现象，导致部分资产在物理上无法找到合法的归属锚点。"
                    ], className="mb-2"),
                    html.Li([
                        html.Span("底层物理轨迹盲区：", className="fw-bold"),
                        "部分人员未被分配车辆或完全没有产生任何可用的 GPS 定位记录，这种幽灵数据的存在使得底层验证依据完全缺失，无法为财务消费提供时空碰撞比对。"
                    ])
                ], className="text-muted"),

                # 3.3.2 方法不确定性
                html.H4("3.3.2 方法不确定性", id="section-3-3-2", className="mt-4 mb-3"),
                html.Ul([
                    html.Li([
                        html.Span("时空圈定匹配的局限性：", className="fw-bold"),
                        "模型通过设定空间半径与时间窗口来强制关联车辆与消费行为，但离散的消费记录密度远低于高频的 GPS 轨迹，其颗粒度差异极易导致偶然的路过或短暂停靠被算法误判为实质关联，难以做到绝对精准的验证。"
                    ], className="mb-2"),
                    html.Li([
                        html.Span("共享资源分配的逻辑妥协：", className="fw-bold"),
                        "对于公共卡车等共享资产，在缺乏具体驾驶员交接日志的情况下，算法只能采取均分概率或集群锁定的方式进行推演，该妥协无法将具体的异常消费行为绝对锁定到单一嫌疑人身上。"
                    ], className="mb-2"),
                    html.Li([
                        html.Span("代持与互借行为的判定模糊：", className="fw-bold"),
                        "系统主要依赖物理重合率和财务共现频次来量化推断归属，但难以从纯数据角度绝对区分偶然的私下借车借卡与有预谋的身份交叉伪装。"
                    ])
                ], className="text-muted")
            ], width=9, className="ps-5")
        ])
    ])

layout = get_layout

# ==========================================
# 交互回调模块 (Callbacks)
# ==========================================
@callback(
    [
        Output('task3-certain-sankey', 'figure'),
        Output('task3-uncertain-treemap', 'figure'),
        Output('task3-uncertain-sankey', 'figure')
    ],
    [Input('task3-dept-dropdown', 'value')]
)
def update_task3_visuals(selected_dept):
    # --- 过滤逻辑 ---
    if not selected_dept or selected_dept == '所有关联记录':
        sub_certain = df_certain.copy() if not df_certain.empty else pd.DataFrame()
        sub_uncertain = df_uncertain.copy() if not df_uncertain.empty else pd.DataFrame()
    else:
        sub_certain = df_certain[df_certain['CurrentEmploymentType'] == selected_dept].copy()
        sub_uncertain = df_uncertain[df_uncertain['CurrentEmploymentType'] == selected_dept].copy()

    # --- 渲染图表 1: 确定性桑基图 ---
    fig_certain = build_sankey_fig(sub_certain, use_probability_color=False)

    # --- 渲染图表 2: 宏观树状图 (底层手动构建版，免疫 Pandas append 报错) ---
    if sub_uncertain.empty:
        fig_treemap = go.Figure().update_layout(title="暂无可分析的不确定样本", plot_bgcolor='white')
    else:
        tree_df = sub_uncertain.copy()

        def categorize_reason(reason):
            if not isinstance(reason, str): return "未知异常"
            if '幽灵' in reason or '卡车' in reason: return '幽灵与公共资源集群 (无法定位)'
            elif '一车' in reason and ('积分卡' in reason or '无会员卡' in reason): return '双重高危异常 (车+卡均跨界共享)'
            elif '一车' in reason: return '物理轨迹异常 (私下借车代刷)'
            elif '积分卡' in reason or '无会员卡' in reason: return '财务逻辑异常 (卡片交叉互用/隐匿)'
            return '其他异常'

        tree_df['Macro_Category'] = tree_df['Uncertainty_Reason'].apply(categorize_reason)
        tree_df['CurrentEmploymentType'] = tree_df['CurrentEmploymentType'].fillna('外包/未分配部门')
        tree_df['FullName'] = tree_df['FullName'].fillna('未知员工档案')

        # ==== 核心防爆层：纯手工 Python 遍历构建树状层级，彻底告别 px.treemap ====
        labels, parents, ids, values, colors = [], [], [], [], []

        # 1. 调优色板：使用低饱和度的莫兰迪高级色系，视觉更舒适
        color_map = {
            '幽灵与公共资源集群 (无法定位)': '#D5DBDB',  # 浅灰绿
            '双重高危异常 (车+卡均跨界共享)': '#F5B7B1',  # 柔和樱桃红
            '物理轨迹异常 (私下借车代刷)': '#FAD7A1',  # 奶油浅橙
            '财务逻辑异常 (卡片交叉互用/隐匿)': '#AED6F1',  # 清新天蓝
            '全量异常图谱': '#FFFFFF'  # 根节点设为纯白，消灭丑陋的底色
        }

        # 根节点
        labels.append("全量异常图谱")
        parents.append("")
        ids.append("全量异常图谱")
        values.append(len(tree_df))
        colors.append(color_map['全量异常图谱'])

        # 层级1: 异常分类
        for cat, cat_df in tree_df.groupby('Macro_Category'):
            labels.append(cat)
            parents.append("全量异常图谱")
            ids.append(f"全量异常图谱/{cat}")
            values.append(len(cat_df))
            colors.append(color_map.get(cat, '#BDC3C7'))

            # 层级2: 部门
            for dept, dept_df in cat_df.groupby('CurrentEmploymentType'):
                labels.append(dept)
                parents.append(f"全量异常图谱/{cat}")
                ids.append(f"全量异常图谱/{cat}/{dept}")
                values.append(len(dept_df))
                colors.append(color_map.get(cat, '#BDC3C7'))

                # 层级3: 员工名
                for name, name_df in dept_df.groupby('FullName'):
                    labels.append(name)
                    parents.append(f"全量异常图谱/{cat}/{dept}")
                    ids.append(f"全量异常图谱/{cat}/{dept}/{name}")
                    values.append(len(name_df))
                    colors.append(color_map.get(cat, '#BDC3C7'))

                    # 层级4: 叶子节点 (信用卡号)
                    for _, row in name_df.iterrows():
                        cc = 'CC-' + str(row['last4ccnum'])
                        labels.append(cc)
                        parents.append(f"全量异常图谱/{cat}/{dept}/{name}")
                        ids.append(f"全量异常图谱/{cat}/{dept}/{name}/{cc}")
                        values.append(1)
                        colors.append(color_map.get(cat, '#BDC3C7'))

        fig_treemap = go.Figure(go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            marker_colors=colors,
            branchvalues="total",
            textinfo="label+value",
            # 2. 字体优化：缩小字体至 11px，改为深青灰色，防止挤压换行
            textfont=dict(size=11, color="#2C3E50"),
            # 3. 边框与间距优化：统一纯白分割线，去掉嵌套的绿色感
            marker=dict(line=dict(color='white', width=2)),
            tiling=dict(pad=3)  # 增加内部方块的呼吸感间距
        ))

        # 4. 彻底去掉多余的四周留白边距
        fig_treemap.update_layout(
            margin=dict(t=30, l=0, r=0, b=0),
            height=500,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
    # --- 渲染图表 3: 不确定性概率桑基图 ---
    fig_uncertain_sankey = build_sankey_fig(sub_uncertain, use_probability_color=True)

    return fig_certain, fig_treemap, fig_uncertain_sankey