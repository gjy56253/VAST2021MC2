import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/', name='首页', order=0)

layout = html.Div([
    # 使用 85vh (视口高度的85%) 和 flex 布局，确保所有内容刚好在一屏内垂直居中
    dbc.Container([
        html.Div([
            # --- 1. 顶部标签 ---
            html.Span("VAST CHALLENGE 2021 • MINI CHALLENGE 2",
                      className="badge bg-dark mb-4 px-3 py-2 text-uppercase tracking-wide"),

            # --- 2. 大标题 ---
            html.H1("GAStech员工失踪案",
                    className="display-4 fw-bold text-dark mb-3"),

            # --- 3. 副标题 ---
            # 增加 mx-auto 和 maxWidth 以固定副标题宽度
            html.P("消费追踪与可疑行为识别",
                   className="text-secondary fw-light mb-5 mx-auto",
                   style={"fontSize": "1.8rem", "maxWidth": "800px"}),

            # --- 4. 引言 (The Hook - 严谨分析版) ---
            html.P(
                "一场寻常的公司庆祝活动后，多名 GASTech 员工离奇失踪，案件调查一度陷入僵局。幸运的是，我们掌握了案发前两周内该公司的车辆 GPS 轨迹，以及相关的信用卡与会员卡交易记录。本系统将以数据可视化为核心手段，对这些时空与消费数据进行交叉印证，旨在精准还原每位员工在失踪前的真实活动轨迹，直观地揭示潜在的异常行为与隐秘的聚集模式，用客观的数据网络为还原事件真相提供关键线索。",
                className="text-muted mx-auto",
                style={"maxWidth": "1000px", "fontSize": "1.25rem", "lineHeight": "1.9", "textAlign": "justify"}
            ),
        ], className="text-center w-100"),

        # --- 5. 底部信息框 (浅绿色调) ---
        html.Div([
            # 内部文本强制左对齐 (text-start)
            html.Div([
                html.P([html.Strong("课程名称："), "数据可视化"], className="mb-2 text-dark fs-5"),
                html.P([html.Strong("团队作者："), "高嘉钰、周雨欣、杨彤、张倚晨、贺祥宇"], className="mb-2 text-dark fs-5"),
                html.P([html.Strong("发布日期："), "2026年6月12日"], className="mb-0 text-dark fs-5"),
            ], className="text-start")

            # 方框整体居中 (mx-auto)，并设置与副标题一致的宽度 (maxWidth: 600px)
        ], className="mt-5 py-4 px-5 rounded-3 shadow-sm mx-auto",
            style={"width": "100%", "maxWidth": "600px", "backgroundColor": "#f0f7f4"})

    ], className="d-flex flex-column justify-content-center align-items-center", style={"height": "85vh"})
])