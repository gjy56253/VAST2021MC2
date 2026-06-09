import pandas as pd

gps = pd.read_csv("gps.csv")

gps["Timestamp"] = pd.to_datetime(gps["Timestamp"])

pool_cars = [101, 104, 105, 106, 107]

gps = gps[gps["id"].isin(pool_cars)].copy()

gps["hour"] = gps["Timestamp"].dt.hour
gps["date"] = gps["Timestamp"].dt.date

print("=" * 80)
print("共享公务车非工作时间使用统计")
print("=" * 80)

for car in pool_cars:

    df = gps[gps["id"] == car]

    total = len(df)

    off_work = df[
        (df["hour"] < 7)
        |
        (df["hour"] >= 20)
    ]

    print()
    print(f"车辆 {car}")
    print(f"总GPS记录数: {total}")
    print(f"非工作时间记录数: {len(off_work)}")

    if total > 0:
        print(
            f"占比: {len(off_work)/total:.2%}"
        )

    if len(off_work) > 0:

        print("最早非工作时间记录:")

        print(
            off_work[
                ["Timestamp", "lat", "long"]
            ]
        )

print()
print("=" * 80)