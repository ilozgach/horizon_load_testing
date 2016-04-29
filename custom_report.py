import json
import os
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


class CustomReport:
    def __init__(self):
        self.results = {}

    def add_result(self, horizon_page, nof_instances, load_time):
        if horizon_page not in self.results:
            self.results[horizon_page] = {}
        if nof_instances not in self.results[horizon_page]:
            self.results[horizon_page][nof_instances] = {}
            self.results[horizon_page][nof_instances]["times"] = []
        self.results[horizon_page][nof_instances]["times"].append(load_time)

    def write_results(self):


        for horizon_page in self.results:
            for nof_instances in self.results[horizon_page]:
                sum = 0
                for time in self.results[horizon_page][nof_instances]["times"]:
                    sum += time
                self.results[horizon_page][nof_instances]["avg"] = sum / len(self.results[horizon_page][nof_instances]["times"])

        suffix = (str(datetime.datetime.now())).replace(" ", "_").replace(":", "-")
        dirname = "horizon_load_test_{}".format(suffix)
        results_dir = os.path.join(os.getcwd(), dirname)
        os.mkdir(results_dir)
        json_results_file = os.path.join(results_dir, "results.json")

        with open(json_results_file, "w") as file:
            file.write(json.dumps(self.results))
