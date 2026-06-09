# tasks/task5.py
from dash import html, dcc
import dash_bootstrap_components as dbc


def get_layout():
    return html.Div([
        html.H3("Task 5: 综合推理与案件还原", className="mt-4 text-info"),
        html.P("综合前述模块的分析结果，还原案件的完整时间线与主要嫌疑人画像。"),
        html.Hr(),

        dbc.Card([
            dbc.CardHeader(html.H5("1. 案件核心时间线梳理", className="mb-0")),
            dbc.CardBody([
                html.P("融合 GPS、信用卡和社交网络数据，生成最终的故事线。"),

                dbc.Card(dbc.CardBody("图表占位符：甘特图 (Gantt Chart) 或 交互式时间轴"),
                         className="bg-light mt-3 mb-3 text-center"),

                dbc.Alert([
                    html.H6("💡 最终结论：", className="alert-heading"),
                    "经过全面可视分析，我们认为主要嫌疑人为 [特定员工/群体]，其核心作案逻辑如下..."
                ], color="dark", className="mb-0")
            ])
        ], className="mb-4 shadow-sm"),
    ])