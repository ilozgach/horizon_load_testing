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
        suffix = (str(datetime.datetime.now())).replace(" ", "_").replace(":", "-")
        dirname = "horizon_load_test_{}".format(suffix)
        results_dir = os.path.join(os.getcwd(), dirname)
        os.mkdir(results_dir)
        json_results_file = os.path.join(results_dir, "results.json")
        pdf_results_file = os.path.join(results_dir, "results.pdf")
        pp = PdfPages(pdf_results_file)

        for horizon_page in self.results:
            for nof_instances in self.results[horizon_page]:
                total = 0
                for time in self.results[horizon_page][nof_instances]["times"]:
                    total += time
                avg_time = total / len(self.results[horizon_page][nof_instances]["times"])
                self.results[horizon_page][nof_instances]["avg"] = avg_time

                values = self.results[horizon_page][nof_instances]["times"]
                title = "page - {}, nof instances - {}".format(horizon_page, nof_instances)
                x = range(len(values))

                plt.bar(x, values)
                plt.plot([0, len(values)], [avg_time, avg_time], "k--")
                plt.ylabel("time (sec)")
                plt.title(title)
                plt.tick_params(axis='x', which='both', bottom='off', top='off', labelbottom='off')
                yticks = [0, min(values), avg_time, max(values)]
                plt.yticks(yticks)
                pp.savefig()
                plt.close()

        pp.close()

        with open(json_results_file, "w") as file:
            file.write(json.dumps(self.results))
