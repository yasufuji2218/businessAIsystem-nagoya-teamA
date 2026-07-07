import csv

def save_daily_analysis(date, animal, total_count, average_stay_time, alert_level):
    with open("daily_analysis.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            date,
            animal,
            total_count,
            average_stay_time,
            alert_level
        ])


def save_weekly_analysis(week, animal, peak_hour, peak_day, familiarity_score, trap_score, level):
    with open("weekly_analysis.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([week, animal, peak_hour, peak_day, familiarity_score, trap_score, level])



def save_monthly_analysis(
    month,
    device_id,
    total_count,
    monkey_count,
    boar_count,
    trap_score,
    rank
):
    with open(
        "monthly_analysis.csv",
        "a",
        newline="",
        encoding="utf-8"
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            month,
            device_id,
            total_count,
            monkey_count,
            boar_count,
            trap_score,
            rank
        ])

def save_yearly_analysis(
    year,
    device_id,
    total_count,
    monkey_count,
    boar_count,
    trap_score,
    rank
):
    with open(
        "yearly_analysis.csv",
        "a",
        newline="",
        encoding="utf-8"
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            year,
            device_id,
            total_count,
            monkey_count,
            boar_count,
            trap_score,
            rank
        ])




