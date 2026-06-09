import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# 1. 初始化 Dash 应用
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY]
)

# 2. 构建顶部导航栏 (Navbar)
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(page['name'], href=page['relative_path']))
        # 提取所有页面，并根据 order 参数从小到大强制排序
        for page in sorted(dash.page_registry.values(), key=lambda page: page.get("order", 99))
    ],
    brand="VAST 2021 - GAStech 失踪案调查系统",
    brand_href="/",
    color="dark",
    dark=True,
    fluid=True,
)

# 3. 构建总体布局
app.layout = html.Div([
    navbar,
    dbc.Container([
        dash.page_container
    ], fluid=True, className="py-4")
])

if __name__ == '__main__':
    app.run(debug=True, port=8050)