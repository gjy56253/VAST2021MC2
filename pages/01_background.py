import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, name='项目背景', order=1)

# === 左侧导航栏定义 (无背景框，经典列表排版) ===
sidebar = html.Div([
    html.H5("目录", className="fw-bold mb-3", style={"color": "black"}),
    html.Ul([
        html.Li(html.A("1. 项目背景", href="#section-1-1",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Li(html.A("2. 任务分析", href="#section-1-2",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
        html.Li(html.A("3. 数据来源", href="#section-1-3",
                       className="text-decoration-none text-muted fw-bold d-block mt-3")),
    ], className="list-unstyled")
], className="sticky-top pt-4")

# === 右侧主体内容定义 ===
main_content = html.Div(
    [
        # 大标题：项目背景 (纯黑、加粗、居中)
        html.H2("项目背景", className="fw-bold text-center mb-5", style={"color": "black"}),

        # 1.1 事件背景 (纯黑标题)
        html.H4("1. 项目背景", id="section-1-1", className="fw-bold mb-3 border-bottom pb-2", style={"color": "black"}),
        html.P(
            "2014年1月，多名GAStech公司员工在阿比拉市的庆祝活动后失踪，尽管当地执法部门怀疑这涉及刑事案件，但调查工作遇到了严重的盲区：案发当天的车辆轨迹数据已被抹去。因此，调查人员目前仅能获取案发前两周，即2014年1月6日至2014年1月19日期间的财务交易流水与车辆行驶记录。",
            className="text-muted mb-5",
            style={"textAlign": "justify", "lineHeight": "1.8", "fontSize": "1.1rem"}
        ),

# === 在此插入图片 ===
        html.Div(
            html.Img(
                src="/assets/gastechlogo.png",
                style={"maxWidth": "100%", "maxHeight": "250px", "objectFit": "contain"}
            ),
            className="text-center mb-5" # 居中图片，并在下方留出 mb-5 的边距
        ),

        # 1.2 分析任务 (纯黑标题)
        html.H4("2. 任务分析", id="section-1-2", className="fw-bold mb-3 mt-5 border-bottom pb-2", style={"color": "black"}),
        html.P(
            "为了识别出各员工案发前的异常行为，我们的可视分析将围绕以下五个核心任务展开：",
            className="text-muted mb-3",
            style={"fontSize": "1.1rem"}
        ),
        html.Ul([
            html.Li([html.Strong("任务一：消费热点分析与异常检测。"), "我们通过分析信用卡与会员卡数据来识别高频消费地点与时间规律，在建立员工日常行为基线的基础之上，标记出初步的可疑迹象与潜在的数据异常行为。"], className="mb-3 text-muted", style={"textAlign": "justify", "lineHeight": "1.6"}),
            html.Li([html.Strong("任务二：时空对齐与跨源数据偏差分析。"), "我们将GPS车辆数据与财务流水进行整合以排查矛盾点，进而揭示员工物理位置与交易记录不符的具体情况，暴露出伪造的行动轨迹或隐秘活动。"], className="mb-3 text-muted", style={"textAlign": "justify", "lineHeight": "1.6"}),
            html.Li([html.Strong("任务三：持卡人识别与不确定性量化。"), "我们基于行为证据推断匿名信用卡与会员卡的真实归属者，从而将可疑行为锁定至具体个人，进一步排查潜在嫌疑人。"], className="mb-3 text-muted", style={"textAlign": "justify", "lineHeight": "1.6"}),
            html.Li([html.Strong("任务四：非正式社交网络分析。"), "我们排查GAStech员工之间潜在的非正式关系，构建出游离于正式企业架构之外的社交网络与利益联盟。"], className="mb-3 text-muted", style={"textAlign": "justify", "lineHeight": "1.6"}),
            html.Li([html.Strong("任务五：可疑活动定位。"), "我们锁定发生异常活动的具体地点并分析其内在逻辑，旨在找出与案件直接相关的集结地、秘密会面点或非法策划区域。"], className="mb-3 text-muted", style={"textAlign": "justify", "lineHeight": "1.6"}),
        ], className="mb-5"),

        # 1.3 数据来源 (纯黑标题)
        html.H4("3. 数据来源", id="section-1-3", className="fw-bold mb-3 mt-5 border-bottom pb-2", style={"color": "black"}),
        html.Ul([
            html.Li([html.Strong("财务交易流水："), "此类记录捕获了员工在当地商铺消费的时间与空间足迹，涵盖标准的信用卡支付记录以及Kronos Kares福利卡的使用情况。"], className="mb-3 text-muted", style={"textAlign": "justify", "lineHeight": "1.6"}),
            html.Li([html.Strong("车辆轨迹数据："), "该数据集记录了指定公司车辆在整个区域内连续的物理移动情况，包含随时间变化的精确地理坐标。"], className="mb-3 text-muted", style={"textAlign": "justify", "lineHeight": "1.6"}),
            html.Li([html.Strong("人员与车辆分配信息："), "这是一份详细记录企业组织架构的登记表，标明了具体员工及其分配到的公司车辆对应关系。"], className="mb-3 text-muted", style={"textAlign": "justify", "lineHeight": "1.6"}),
            html.Li([html.Strong("地理空间与地图文件："), "包含详细矢量形状文件与旅游地图的数字地图资源，勾勒出了阿比拉市与克罗诺斯地区的基础设施及重点关注区域。"], className="mb-3 text-muted", style={"textAlign": "justify", "lineHeight": "1.6"}),
        ], className="mb-5"),
    ],
    className="px-md-4"
)

# === 整体页面布局组合 ===
layout = html.Div([
    dbc.Container([
        dbc.Row([
            # 左列：套用你指定的宽度和右侧边框样式
            dbc.Col(sidebar, width=3, className="border-end border-light pe-4 d-none d-md-block"),
            # 右列：分配给主体文本
            dbc.Col(main_content, width=9)
        ], className="my-5")
    ], fluid=False, style={"maxWidth": "1200px"})
])