import json
from sys import argv

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

with open(argv[1], "r") as file:
    json_data = json.load(file)

pp = PdfPages(argv[2])
for horizon_page in json_data.keys():
    for nof_instances in json_data[horizon_page].keys():
        avg_time = float(json_data[horizon_page][nof_instances]["avg"])

        values = json_data[horizon_page][nof_instances]["times"]
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