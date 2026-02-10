import sys
import json
import os

if __name__ == "__main__":
    ensemble_path = sys.argv[1]
    sim_threshold = sys.argv[2]

    year_day_time_list = ensemble_path.split(".")[0].split("/")[-1].split("_")
    print(year_day_time_list)
    year = year_day_time_list[0]
    day = year_day_time_list[1]
    time = year_day_time_list[2]
    print(year, day, time)

    f = open(ensemble_path)
    data = json.load(f)
    for i, entry in data.items():
        algo_name = entry['algo_name']
        print(algo_name)

        submitCommand = "python extractARAxis.py " + algo_name + " " + year + " " + day + " " + time + " " + sim_threshold
        os.system(submitCommand)