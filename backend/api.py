from fastapi import FastAPI
from appearance import calc_peak
from habituation import load_data, calc_familiarity_scores
from trap import calc_trap_score
import pandas as pd


app = FastAPI()

@app.get("/")
def root():
    return {"message": "Backend API"}

@app.get("/appearance")
def appearance():
    df = pd.read_csv("animal_log.csv")

    peak_hour, peak_count, hour_count = calc_peak(df)

    return {
        "peak_hour": int(peak_hour),
        "peak_count": int(peak_count),
        "hour_count": hour_count.to_dict()
    }

@app.get("/habituation")
def habituation():

    df = load_data("animal_log.csv")

    daily, weekly, monthly, yearly = calc_familiarity_scores(df)

    return {
        "familiarity_daily_score": daily,
        "familiarity_weekly_score": weekly,
        "familiarity_monthly_score": monthly,
        "familiarity_yearly_score": yearly
    }


@app.get("/trap")
def trap():

    df = pd.read_csv("animal_log.csv")

    trap_score, level = calc_trap_score(df)

    return {
        "trap_score": trap_score,
        "level": level
    }