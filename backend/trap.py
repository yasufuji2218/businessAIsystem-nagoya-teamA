#罠設置推奨スコア
import pandas as pd

def calc_trap_score(df):
    # 出現回数
    animal_count = df["animal_type"].value_counts()

    # スコア①：出現頻度
    animal_score = animal_count.max() / len(df)

    # スコア②：トレンド
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    half = len(df) // 2
    first_half = len(df.iloc[:half])
    second_half = len(df.iloc[half:])

    trend_score = (second_half - first_half) / max(first_half, 1)

    # スコア③：慣れ
    df["date"] = df["timestamp"].dt.date
    daily = df.groupby("date")["stay_duration"].mean()

    if len(daily) >= 2:
        familiarity_score = (daily.iloc[-1] - daily.iloc[0]) / daily.iloc[0]
    else:
        familiarity_score = 0

    # 合成スコア
    trap_score = (
        animal_score * 0.5 +
        trend_score * 0.3 +
        familiarity_score * 0.2
    )

    # レベル判定
    if trap_score >= 0.7:
        level = "HIGH"
    elif trap_score >= 0.4:
        level = "MEDIUM"
    else:
        level = "LOW"

    return trap_score, level


df = pd.read_csv("animal_log.csv")

trap_score, level = calc_trap_score(df)

print("trap_score:", trap_score)
print("level:", level)
