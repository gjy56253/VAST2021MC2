import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, name='系统总览', order=4)

layout = html.Div([
    html.H2("Storyboard"),
    html.P("总结与故事板建设中...")
])