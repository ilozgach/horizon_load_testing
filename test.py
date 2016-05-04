import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

pp = PdfPages('multipage.pdf')

y = [3, 10, 7, 5, 3, 4.5, 6, 8.1]
N = len(y)
x = range(N)
width = 1/1.5
plt.bar(x, y)

pp.savefig()
plt.close()




threshold = 43.0
values = [30., 87.3, 99.9, 33.33, 50.0]
x = range(len(values))

# split it up
above_threshold = [0 if x - threshold < 0 else x - threshold for x in values]
print above_threshold
below_threshold = [threshold if x > threshold else x for x in values]
print below_threshold

# and plot it
# fig, ax = plt.subplots()
# ax.bar(x, below_threshold)
# ax.bar(x, above_threshold, bottom=below_threshold)
plt.bar(range(len(values)), values)

# horizontal line indicating the threshold
plt.plot([0, len(values)], [threshold, threshold], "k--")
plt.ylabel("time (sec)")
plt.title("Time of page trololo")
plt.tick_params(axis='x', which='both', bottom='off', top='off', labelbottom='off')
#plt.annotate('avg', xy=(0, threshold), xytext=(len(values) / 5, threshold + 10), arrowprops=dict(facecolor='black', shrink=0.05))
yticks = [0, threshold, max(values)]
for i in range(1, 4):
	yticks.append(0 + i * int(max(values) / 5))
yticks = sorted(yticks)
plt.yticks(yticks)

pp.savefig()
plt.close()



plt.figure(2)
plt.plot([1,2,3,4,5,6,7,8,9])
plt.ylabel('some numbers')

pp.savefig()
plt.close()

pp.close()