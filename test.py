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
plt.bar(x, values)

# horizontal line indicating the threshold
ax.plot([0., 4.5], [threshold, threshold], "k--")

pp.savefig()
plt.close()



plt.figure(2)
plt.plot([1,2,3,4,5,6,7,8,9])
plt.ylabel('some numbers')

pp.savefig()
plt.close()

pp.close()