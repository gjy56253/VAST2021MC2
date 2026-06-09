import geopandas as gpd
import fiona
from shapely.geometry import shape
import os


def process_geospatial_data():
    # 使用 ../ 退回项目根目录，然后再进入 data/Geospatial
    folder_path = "../data/Geospatial"

    tasks = {
        "Abila": {
            "input": os.path.join(folder_path, "Abila.shp"),
            "output": os.path.join(folder_path, "Abila.geojson")
        },
        "Kronos_Island": {
            "input": os.path.join(folder_path, "Kronos_Island.shp"),
            "output": os.path.join(folder_path, "Kronos_Island.geojson")
        }
    }

    # 遍历所有地区，逐个处理
    for place_name, paths in tasks.items():
        input_shp = paths["input"]
        output_json = paths["output"]

        print(f"\n[{place_name}] 开始执行逐行安全读取与清洗...")
        print(f" -> 目标路径: {input_shp}")

        # 增加一步路径检查
        if not os.path.exists(input_shp):
            print(f"[错误] 找不到文件: {input_shp}")
            print("💡 提示：请确保你的终端当前正处于 preprocessing 文件夹中运行此脚本！")
            continue

        valid_records = []

        try:
            # 使用 fiona 打开文件
            with fiona.open(input_shp) as src:
                crs = src.crs  # 提取原始坐标系

                # 逐行读取排雷
                for i, feature in enumerate(src):
                    try:
                        # 尝试解析几何形状
                        geom = shape(feature['geometry'])

                        # 如果形状有效且非空，则保留数据
                        if geom.is_valid and not geom.is_empty:
                            valid_records.append(feature)

                    except Exception as e:
                        print(f"  -> 拦截: 丢弃 {place_name} 第 {i} 行的脏数据 - {e}")

            # 数据清洗完毕，重新打包
            print(f"[{place_name}] 读取完毕，共保留 {len(valid_records)} 条健康数据。")
            gdf = gpd.GeoDataFrame.from_features(valid_records, crs=crs)

            # 导出为前端可用的 GeoJSON
            gdf.to_file(output_json, driver="GeoJSON")
            print(f"[{place_name}] 成功！已生成: {output_json}")

        except Exception as main_e:
            print(f"[{place_name}] 发生全局严重错误: {main_e}")


if __name__ == "__main__":
    process_geospatial_data()