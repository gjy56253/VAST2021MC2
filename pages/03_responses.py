# pages/03_responses.py
import dash
from dash import html
import dash_bootstrap_components as dbc

# 导入你们团队在 tasks 文件夹下写的 5 个积木模块
from tasks import task1, task2, task3, task4, task5

dash.register_page(__name__, name='问题求解', order=3)

# 布局变量
layout = html.Div([
    # 将标题居中并加粗
    html.H2("任务求解", className="mb-4 text-center fw-bold"),

    # 补充年份与具体挑战信息，转为中文并居中
    html.P(
        "以下为 VAST 2021 Mini Challenge 2 中所有任务的求解与分析。",
        className="text-center text-muted mb-4 fs-5"
    ),

    # 使用 Tabs 标签页
    # 增加 labelClassName="text-dark fw-bold" 使标签栏的文字变深且微微加粗
    dbc.Tabs([
        dbc.Tab(task1.get_layout(), label="任务一", labelClassName="text-dark fw-bold"),
        dbc.Tab(task2.get_layout(), label="任务二", labelClassName="text-dark fw-bold"),
        dbc.Tab(task3.get_layout(), label="任务三", labelClassName="text-dark fw-bold"),
        dbc.Tab(task4.get_layout(), label="任务四", labelClassName="text-dark fw-bold"),
        dbc.Tab(task5.get_layout(), label="任务五", labelClassName="text-dark fw-bold"),
    ], className="mt-4 shadow-sm p-3 bg-white rounded")
])