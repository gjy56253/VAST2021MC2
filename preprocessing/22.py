import pandas as pd
import plotly.graph_objects as go
import os

# 配置路径：脚本在 preprocessing/，地图和数据在 ../
DATA_DIR = '../data'
ASSETS_DIR = '../assets'
# 你需要确保这个字典在你这里依然可以访问，如果不行，请将其复制过来
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
    "Daily Dealz": {"lat": None, "lon": None},  # 在线消费，无物理坐标
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


def plot_verify_match(cc_id, car_id):
    # 1. 加载数据
    cc_df = pd.read_csv(os.path.join(DATA_DIR, 'cc_data.csv'), encoding='latin1')
    gps_df = pd.read_csv(os.path.join(DATA_DIR, 'gps.csv'), encoding='latin1')

    # 时间格式化
    cc_time_col = 'timestamp' if 'timestamp' in cc_df.columns else 'tiemstamp'
    cc_df['timestamp'] = pd.to_datetime(cc_df[cc_time_col])
    gps_df['Timestamp'] = pd.to_datetime(gps_df['Timestamp'])

    # 2. 提取数据
    cc_txns = cc_df[cc_df['last4ccnum'] == cc_id].sort_values('timestamp')
    car_traj = gps_df[gps_df['id'] == car_id].sort_values('Timestamp')

    # 3. 绘图
    fig = go.Figure()

    # 加载底图
    map_img = os.path.join(ASSETS_DIR, 'MC2-tourist.jpg')
    fig.add_layout_image(
        dict(source=map_img, xref="x", yref="y", x=24.82450, y=36.09550,
             sizex=0.0855, sizey=0.0505, sizing="stretch", layer="below"))

    # 画车辆轨迹 (蓝色虚线)
    fig.add_trace(go.Scatter(
        x=car_traj['long'], y=car_traj['lat'], mode='lines',
        line=dict(color='blue', width=2, dash='dot'), name=f'Car {car_id}'))

    # 画消费点 (红色圆点)
    cc_lats = [LOCATION_COORDS[loc]['lat'] for loc in cc_txns['location'] if loc in LOCATION_COORDS]
    cc_lons = [LOCATION_COORDS[loc]['lon'] for loc in cc_txns['location'] if loc in LOCATION_COORDS]

    fig.add_trace(go.Scatter(
        x=cc_lons, y=cc_lats, mode='markers',
        marker=dict(size=10, color='red'), name=f'CC {cc_id}'))

    fig.update_layout(
        title=f"验证：信用卡 {cc_id} 与 车辆 {car_id} 轨迹叠加",
        xaxis=dict(range=[24.82450, 24.91000], visible=False),
        yaxis=dict(range=[36.04500, 36.09550], visible=False),
        margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=600
    )

    # 这里直接弹出浏览器窗口显示图表
    fig.show()


# 使用示例
if __name__ == "__main__":
    plot_verify_match(6901, 13)