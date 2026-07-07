# 慣れ分析
import pandas as pd

def load_data(path):
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["date"] = df["timestamp"].dt.date
    df["week"] = df["timestamp"].dt.to_period("W")
    df["month"] = df["timestamp"].dt.to_period("M")
    df["year"] = df["timestamp"].dt.year

    return df


def calc_stay(df, unit):
    return df.groupby(unit)["stay_duration"].mean()


def calc_familiarity(series):
    if len(series) < 2:
        return 0.0
    return (series.iloc[-1] - series.iloc[0]) / series.iloc[0]


# ★FastAPIから呼び出す関数
def calc_familiarity_scores(df):

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["date"] = df["timestamp"].dt.date

    df["week"] = df["timestamp"].dt.isocalendar().week

    df["month"] = df["timestamp"].dt.month

    df["year"] = df["timestamp"].dt.year

    daily = calc_stay(df, "date")
    weekly = calc_stay(df, "week")
    monthly = calc_stay(df, "month")
    yearly = calc_stay(df, "year")

    return (
        calc_familiarity(daily),
        calc_familiarity(weekly),
        calc_familiarity(monthly),
        calc_familiarity(yearly),
    )


# 単体実行用
if __name__ == "__main__":
    df = load_data("animal_log.csv")

    daily, weekly, monthly, yearly = calc_familiarity_scores(df)

    print("慣れ度（日）:", daily)
    print("慣れ度（週）:", weekly)
    print("慣れ度（月）:", monthly)
    print("慣れ度（年）:", yearly)