import pandas as pd
from save_log import save_daily_analysis

from appearance import calc_peak
from habituation import calc_familiarity_scores
from trap import calc_trap_score
from save_log import save_weekly_analysis
from save_log import save_monthly_analysis
from save_log import save_yearly_analysis



def run_daily_batch():

    # CSV読み込み
    df = pd.read_csv("animal_log.csv")

    # timestampを日時型に変換
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 最新日のデータを取得
    target_date = df["timestamp"].dt.date.max()

    today_data = df[
        df["timestamp"].dt.date == target_date
    ]

    # 動物ごとに集計
    for animal in today_data["animal_type"].unique():

        animal_data = today_data[
            today_data["animal_type"] == animal
        ]

        total_count = len(animal_data)

        average_stay_time = (
            animal_data["stay_duration"].mean()
        )

        # 仮の警戒レベル
        if total_count >= 10:
            alert_level = "HIGH"
        elif total_count >= 5:
            alert_level = "MEDIUM"
        else:
            alert_level = "LOW"

        save_daily_analysis(
            str(target_date),
            animal,
            total_count,
            round(average_stay_time, 2),
            alert_level
        )

def run_weekly_batch():

    df = pd.read_csv("animal_log.csv")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    latest_date = df["timestamp"].max()

    week_data = df[
        df["timestamp"] >= latest_date - pd.Timedelta(days=7)
    ]


    for animal in week_data["animal_type"].unique():

        animal_data = week_data[
            week_data["animal_type"] == animal
        ].copy()


        # 出没ピーク
        peak_hour, peak_count, hour_count = calc_peak(animal_data)


        # 慣れ度
        daily_score, weekly_score, monthly_score, yearly_score = (
            calc_familiarity_scores(animal_data)
        )


        # 罠スコア
        trap_score, level = calc_trap_score(animal_data)

        
        # 保存
        save_weekly_analysis(
            str(latest_date.date()),
            animal,
            peak_hour,
            "未計算",
            weekly_score,
            trap_score,
            level
        )






def run_monthly_batch():

    df = pd.read_csv("animal_log.csv")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 最新月
    latest_month = df["timestamp"].dt.to_period("M").max()

    month_data = df[
        df["timestamp"].dt.to_period("M") == latest_month
    ]


    results = []

    for device in month_data["device_id"].unique():

        device_data = month_data[
            month_data["device_id"] == device
        ]

        total_count = len(device_data)

        monkey_count = len(
            device_data[
                device_data["animal_type"] == "サル"
            ]
        )

        boar_count = len(
            device_data[
                device_data["animal_type"] == "イノシシ"
            ]
        )


        # 簡易スコア
        trap_score = total_count / len(month_data)


        results.append([
            str(latest_month),
            device,
            total_count,
            monkey_count,
            boar_count,
            trap_score
        ])


    # スコア順ランキング
    results.sort(
        key=lambda x: x[5],
        reverse=True
    )


    for rank, row in enumerate(results, start=1):
        row.append(rank)

        save_monthly_analysis(
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6]
        )


    return results


def run_yearly_batch():

    df = pd.read_csv("animal_log.csv")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 最新年
    latest_year = df["timestamp"].dt.year.max()

    year_data = df[
        df["timestamp"].dt.year == latest_year
    ]


    results = []

    for device in year_data["device_id"].unique():

        device_data = year_data[
            year_data["device_id"] == device
        ]

        total_count = len(device_data)

        monkey_count = len(
            device_data[
                device_data["animal_type"] == "サル"
            ]
        )

        boar_count = len(
            device_data[
                device_data["animal_type"] == "イノシシ"
            ]
        )


        # 簡易罠スコア
        trap_score = total_count / len(year_data)


        results.append([
            latest_year,
            device,
            total_count,
            monkey_count,
            boar_count,
            trap_score
        ])


    # スコア順ランキング
    results.sort(
        key=lambda x: x[5],
        reverse=True
    )


    for rank, row in enumerate(results, start=1):

        row.append(rank)

        save_yearly_analysis(
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6]
        )


    return results





import sys


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("指定してください: daily / weekly / monthly / yearly")
        exit()

    mode = sys.argv[1]

    if mode == "daily":
        run_daily_batch()

    elif mode == "weekly":
        run_weekly_batch()

    elif mode == "monthly":
        run_monthly_batch()

    elif mode == "yearly":
        run_yearly_batch()

    else:
        print("unknown mode")