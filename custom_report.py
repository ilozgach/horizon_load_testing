import json

import os
import datetime


class CustomReport:
    def __init__(self):
        self.results = {}

    def add_result(self, horizon_page, nof_instances, load_time):
        if horizon_page not in self.results:
            self.results[horizon_page] = {}
        if nof_instances not in self.results[horizon_page]:
            self.results[horizon_page][nof_instances] = []
        self.results[horizon_page][nof_instances].append(load_time)

    def write_results(self):
        suffix = (str(datetime.datetime.now())).replace(" ", "_").replace(":", "-")
        dirname = "horizon_load_test_{}".format(suffix)
        results_dir = os.path.join(os.getcwd(), dirname)
        os.mkdir(results_dir)
        json_results_file = os.path.join(results_dir, "results.json")

        with open(json_results_file, "w") as file:
            file.write(json.dumps(self.results))
