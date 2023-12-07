import time
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import glob
import tkinter as tk
from tkinter import filedialog
from natsort import natsorted

# List of empty values to store unique numbers
unique_y_values = []
unique_x_values = []
y_list = []
x_list = []
raman_files = []

# Create a tkinter root window
root = tk.Tk()
root.withdraw()

# Open File Explorer for folder selection
folder_path = filedialog.askdirectory(title="Select a folder")

# Search for .txt files in  selected folder
if folder_path:
    raman_files = natsorted(glob.glob(os.path.join(folder_path, '*.txt')))
else:
    print("No folder selected.")

# Close the tkinter root window
root.destroy()

# Record start time from folder is chosen
start_time = time.time()

# Find x- and y- coordinates from file names (values found after "__X_" and "__Y_", respectively)
y_pattern = r'__Y_(-?\d+(?:\.\d+)?)'
x_pattern = r'__X_(-?\d+(?:\.\d+)?)'

# Gather all the x- and y- coordinates values
for file_names in raman_files:
    y_matches = re.findall(y_pattern, file_names)
    x_matches = re.findall(x_pattern, file_names)

    for y_match in y_matches:
        y_value = float(y_match)
        unique_y_values.append(y_value)
        y_list.append(y_value)

    for x_match in x_matches:
        x_value = float(x_match)
        unique_x_values.append(x_value)
        x_list.append(x_value)

# Sorting the x- and y- coordinates values and removing duplicates
unique_y_values = list(natsorted(set(unique_y_values)))
unique_x_values = list(natsorted(set(unique_x_values)))

# Mapping location and calculation preparation
column = 0  # First location of column
row = 0  # First location of row
y_previous = unique_y_values[0]  # First y-coordinate values
x_value = unique_x_values  # List of unique x-coordinate values
y_value = unique_y_values  # List of unique y-coordinate values
x_list = x_list  # List of x-coordinate values from all files, including duplicates, in the order they are read
y_list = y_list  # List of y-coordinate values from all files, including duplicates, in the order they are read
Total = 0  # Starting value for "total number of files read"
raw_map_data = [[None] * len(unique_x_values) for _ in range(len(unique_y_values))]  # Empty array to store calculated data

# Script that iterates through each individual file in sequence, computes the D/G ratio, and stores the calculated values in an array
for i in range(len(raman_files)):
    df = pd.read_csv(raman_files[i], sep='\t', header=None)  # Reading data columns in selected .txt file
    raman_shift = df.iloc[:, 0]  # Storing Raman Shift data in selected .txt file
    intensity = df.iloc[:, 1]  # Storing Intensity data in selected .txt file

    Total = Total + 1  # Increment and print number of files read
    print(f'Total Files Analysed: {Total}')

    d_peak_position = (1300 < raman_shift) & (raman_shift < 1400)  # Find D-peak region
    d_peak = intensity[d_peak_position]  # Retrieve intensity values from the D-peak region
    d_peak_max = np.max(savgol_filter(d_peak, window_length=5, polyorder=2))  # Determine the maximum D-peak intensity value from the smoothed data
    d_peak_min = np.min(savgol_filter(d_peak, window_length=5, polyorder=2))  # Determine the minimum D-peak intensity value from the smoothed data
    d_peak_intensity = d_peak_max - d_peak_min  # Calculate D-peak intensity

    g_peak_position = (1500 < raman_shift) & (raman_shift < 1700)  # Find G-peak region
    g_peak = intensity[g_peak_position]  # Retrieve intensity values from the G-peak region
    g_peak_max = np.max(savgol_filter(g_peak, window_length=5, polyorder=2))  # Determine the maximum G-peak intensity value from the smoothed data
    g_peak_min = np.min(savgol_filter(g_peak, window_length=5, polyorder=2))  # Determine the minimum G-peak intensity value from the smoothed data
    g_peak_intensity = g_peak_max - g_peak_min  # Calculate G-peak intensity

    d_g_ratio = d_peak_intensity / g_peak_intensity  # Calculate D-peak intensity and G-peak intensity ratio (D/G Ratio)

    if y_previous == y_list[i]:
        raw_map_data[row][column] = d_g_ratio   # If y-coordinate match with the previous y-coordinate value, then add D/G Ratio to array
        column = column + 1  # Move to the next column in the data array
    else:
        row = row + 1  # If y-coordinates do not match with the previous y-coordinate value, move to the next row in the data array
        column = 0  # Move to the first column in the data array in the new row
        raw_map_data[row][column] = d_g_ratio  # Add D/G Ratio to array
        column = column + 1  # Move to the next column in the data array
        y_previous = y_list[i]  # Change the previous y-coordinate value to the current one

# Map Plotting Preparation - Determining the size of the x-axis and y-axis values
raw_map_data_array = np.array(raw_map_data)
matrix_size = raw_map_data_array.shape
x_length = matrix_size[1]
y_length = matrix_size[0]
x_width = np.max(unique_x_values) - np.min(unique_x_values)
y_width = np.max(unique_y_values) - np.min(unique_y_values)
x_axis = np.linspace(0, x_width, num=x_length)
y_axis = np.linspace(0, y_width, num=y_length)

# Map Plotting Preparation - Determining the tick locations
x_ticks = np.linspace(0, x_width, num=10)
y_ticks = np.linspace(0, y_width, num=10)
colour_bar_ticks = np.linspace(np.min(raw_map_data_array), np.max(raw_map_data_array), num=10)
colour_bar_label = "$I_{D}/I_{G}$ Ratio"

# Plotting Map
plt.figure()
plt.contourf(x_axis, y_axis, raw_map_data, 500, cmap='rainbow')
plt.gca().set_aspect('equal')
plt.xticks(x_ticks, fontsize=15)
plt.yticks(y_ticks, fontsize=15)
plt.xlabel('Length, \u03BCm', fontsize=15)
plt.ylabel('Length, \u03BCm', fontsize=15)
colour_bar = plt.colorbar(ticks=colour_bar_ticks, format="%.2f")
colour_bar.ax.tick_params(labelsize=15)
colour_bar.set_label(colour_bar_label, fontsize=15)
plt.box(True)

# Record the end time
end_time = time.time()

# Calculate the execution time and convert to minutes and seconds
execution_time = end_time - start_time
minutes = int(execution_time // 60)
seconds = execution_time % 60

# Display the execution time in minutes and seconds
print(f"\nElapsed time is: {minutes} minutes and {seconds:.2f} seconds")

# Display plot
plt.show()
