import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from matplotlib.ticker import ScalarFormatter

# Data setup with labels reflecting the number of invocations
entries = ['10 invocations', '100 invocations', '1000 invocations']
entries_numeric = np.array([10, 100, 1000])  # Numerical values for operations and plotting
times_test1 = [21.650659, 22.599093, 20.234344, 22.523980, 25.938245]
times_test2 = [108.48, 107.247297, 111.123458, 102.873233, 109.21343]
times_test3 = [2115.991799, 2075.981333, 2185.287363, 2126.2132379, 2142.1231267]

# Calculate the averages for each test set
average_test1 = sum(times_test1) / len(times_test1)
average_test2 = sum(times_test2) / len(times_test2)
average_test3 = sum(times_test3) / len(times_test3)
averages = [average_test1, average_test2, average_test3]

# Linear regression for a logarithmic scale best fit line
log_entries = np.log(entries_numeric).reshape(-1, 1)
log_averages = np.log(averages)
model = LinearRegression()
model.fit(log_entries, log_averages)
predicted_line = np.exp(model.predict(log_entries))

# Visualization setup
fig, axs = plt.subplots(1, 2, figsize=(14, 6))

# Bar chart for average response times
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
bars = axs[0].bar(entries, averages, color=colors)
axs[0].set_xlabel('Number of Invocations')
axs[0].set_ylabel('Average Response Time (seconds)')
axs[0].set_title('Average Response Times by Invocation Count')
axs[0].set_yscale('log')
axs[0].yaxis.set_major_formatter(ScalarFormatter())

# Labels on bars
for bar, avg in zip(bars, averages):
    axs[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{round(avg, 2)}s',
                ha='center', va='bottom', fontsize=10, color='black', fontweight='bold')

# Scatter plot for individual response times
for i, times in enumerate([times_test1, times_test2, times_test3]):
    axs[1].scatter([entries_numeric[i]] * len(times), times, color=colors[i], marker='o', label=entries[i], s=120, alpha=0.6, edgecolors='w')
axs[1].set_xlabel('Number of Invocations')
axs[1].set_ylabel('Individual Response Times (seconds)')
axs[1].set_title('Detailed Response Times by Invocation Count')
axs[1].set_yscale('log')
axs[1].yaxis.set_major_formatter(ScalarFormatter())
axs[1].grid(True, which='both', linestyle='--', linewidth=0.5)
axs[1].legend()

# Best fit line for the scatter plot
axs[1].plot(entries_numeric, predicted_line, 'r-', label='Best Fit Line')
axs[1].legend()

# Show the plot
plt.tight_layout()
plt.savefig('graph.png', format='png', dpi=300)
