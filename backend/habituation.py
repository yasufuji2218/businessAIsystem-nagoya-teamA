#慣れ分析
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
    return (series.iloc[-1] - series.iloc[0]) / series.iloc[0]


def main():
    df = load_data("animal_log.csv")

    daily = calc_stay(df, "date")
    weekly = calc_stay(df, "week")
    monthly = calc_stay(df, "month")
    yearly = calc_stay(df, "year")

    print("慣れ度（デモ）:", calc_familiarity(daily))

    print("慣れ度（週）:", calc_familiarity(weekly))
    print("慣れ度（月）:", calc_familiarity(monthly))
    print("慣れ度（年）:", calc_familiarity(yearly))


if __name__ == "__main__":
    main()