# VAST 2021 MC2 可视化分析系统
本项目基于Python Dash构建的交互式可视化分析平台完成VAST 2021 Mini-Challenge 2。

## 项目介绍
本项目针对GAStech员工失踪案，整合了信用卡交易数据、GPS轨迹数据和员工信息数据，通过多维度可视化分析，还原事件全貌，识别异常行为和可疑人员。

## 功能特点
- 员工轨迹时空可视化
- 信用卡交易异常检测
- 人员关系网络分析
- 交互式筛选与钻取

## 技术栈
- Python 3.10+
- Dash & Dash Bootstrap Components
- Pandas & NumPy
- Plotly

## 运行方式
1. 安装依赖：`pip install -r requirements.txt`
2. 运行应用：`python app.py`
3. 打开浏览器访问：http://127.0.0.1:8050