import pandas as pd

def calc_peak(df):
    # 日時型に変換
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 時間だけ取り出す
    df["hour"] = df["timestamp"].dt.hour

    # 時間帯ごとの出現回数
    hour_count = df["hour"].value_counts().sort_index()

    # ピーク時間帯
    peak_hour = hour_count.idxmax()
    peak_count = hour_count.max()

    return peak_hour, peak_count, hour_count


# 単体実行時のみ動作確認
if __name__ == "__main__":
    df = pd.read_csv("detections.csv")

    peak_hour, peak_count, hour_count = calc_peak(df)

    print({
        "peak_hour": int(peak_hour),
        "peak_count": int(peak_count),
        "hour_count": hour_count.to_dict()
    })