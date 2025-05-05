import sys
import os
import h5py
import numpy as np
import plotly
import plotly.tools as tls
import matplotlib.pyplot as plt
import time
import datetime

sys.path.append('.')

# LOAD CALIBRATION DATA
global distance, amplitude, temperature, modulation_frequency_mhz

directory = 'scripts/data'
file_names = os.listdir(directory)
latest_file = file_names[-1]

with h5py.File(f'{directory}/{latest_file}', 'r') as file:
    group = file['data']
    waferID_chipID = np.array(group['waferID_chipID']) #['wafer ID', 'chip ID']
    distance = np.array(group['distance']) #['row', 'col', 'frame', 'dllStep']
    amplitude = np.array(group['amplitude']) #['row', 'col', 'frame', 'dllStep']
    temperature = np.array(group['temperature']) #['frame', 'dllStep']
    temperature_target_for_calibration_deg = np.array(group['calibration_temperature'])
    modulation_frequency_mhz = np.array(group['modulation_frequency'])

# CALCULATE UNAMBIGUITY
distance_unambiguity = int((299792458 * (1/modulation_frequency_mhz*1e-3)) / 2)
print(f"Ambiguity Range = (299'792'458 * 1/{modulation_frequency_mhz}MHz) / 2 = {distance_unambiguity} mm")


# SPATIAL AND TEMPORAL MEAN
distance_mean_t = np.nanmean(distance, axis=2)
distance_mean_ts = np.nanmean(distance_mean_t, axis=(0,1))
amplitude_mean_t = np.nanmean(amplitude, axis=2)
amplitude_mean_ts = np.nanmean(amplitude_mean_t, axis=(0,1))
temperature_mean_t = np.nanmean(temperature, axis=0)


# CORRECT WRAP AROUND AND OFFSET
distance_diff = np.insert(np.diff(distance,axis=-1),0,0,axis=-1)
mask_true_where_is_a_huge_difference = np.less(distance_diff, -3)
mask_sum_of_gradient = np.cumsum(mask_true_where_is_a_huge_difference, axis=-1)
distance_wrapAround_corrected = distance + mask_sum_of_gradient * distance_unambiguity

distance_raw_mean_t = np.nanmean(distance, axis=2)
distance_raw_mean_ts = np.nanmean(distance_raw_mean_t, axis=(0,1))
distance_wrapAround_and_offset_corrected = distance_wrapAround_corrected - distance_raw_mean_ts[0]

distance_wrapAround_and_offset_corrected_mean_t = np.nanmean(distance_wrapAround_and_offset_corrected, axis=2)
distance_wrapAround_and_offset_corrected_mean_ts = np.nanmean(distance_wrapAround_and_offset_corrected_mean_t, axis=(0,1))

# DISTANCE ERROR
idx_closest_dll_step_to_unambiguity = np.argmin(np.abs(distance_wrapAround_and_offset_corrected_mean_ts - distance_unambiguity))
closest_measured_distance_to_unambiguity_range = distance_wrapAround_and_offset_corrected_mean_ts[idx_closest_dll_step_to_unambiguity]

dll_step_mm = closest_measured_distance_to_unambiguity_range / (idx_closest_dll_step_to_unambiguity)
reference_distance = np.arange(0, dll_step_mm * distance.shape[-1], dll_step_mm)

DRNU_LUT_t = distance_wrapAround_and_offset_corrected_mean_t - reference_distance
DRNU_LUT_ts = np.nanmean(DRNU_LUT_t, axis=(0,1))

# STORE DATA INTO FILE
now = datetime.datetime.now()
formatted_date = now.strftime("%Y%m%d_%H%M")

filename = f'scripts/data/{formatted_date}_LUT_{modulation_frequency_mhz}MHz.h5'
with h5py.File(filename, 'w') as f:
    group = f.create_group('data')
    group.create_dataset('waferID_chipID', data=waferID_chipID)
    group.create_dataset('DRNU_LUT', data=DRNU_LUT_t)
    group.create_dataset('DRNU_LUT_offset', data=distance_raw_mean_ts[0])
    group.create_dataset('temperature', data=temperature)
    group.create_dataset('calibration_temperature', data=temperature_target_for_calibration_deg)
    group.create_dataset('modulation_frequency', data=modulation_frequency_mhz)
    group.create_dataset('dll_step_size', data=dll_step_mm)


# PLOT
plt.rcParams['axes.grid'] = True
fig, ax = plt.subplots(5,1, figsize=(20,15))

ax[0].set_title('amplitude')
ax[0].plot(amplitude_mean_t.transpose(2,0,1).reshape(amplitude.shape[-1], -1),'.', linewidth=2)
ax[0].plot(amplitude_mean_ts, linewidth=3, color='r')
ax[0].set_ylabel('DN')

ax[1].set_title('distance raw')
ax[1].plot(distance_mean_t.transpose(2,0,1).reshape(distance.shape[-1], -1),'.', linewidth=2)
ax[1].plot(distance_mean_ts, linewidth=3, color='r')
ax[1].set_ylabel('MM')

ax[2].set_title('distance corrected wrap around and offset')
ax[2].plot(distance_wrapAround_and_offset_corrected_mean_t.transpose(2,0,1).reshape(distance.shape[-1], -1),'.', linewidth=2)
ax[2].plot(distance_wrapAround_and_offset_corrected_mean_ts, linewidth=3, color='r')
ax[2].set_ylabel('MM')

ax[3].set_title('distance error')
ax[3].plot(DRNU_LUT_t.transpose(2,0,1).reshape(distance.shape[-1], -1),'.', linewidth=2)
ax[3].plot(DRNU_LUT_ts, linewidth=3, color='r')
ax[3].set_ylabel('MM')

ax[4].set_title('calibration temperature')
ax[4].plot(temperature.transpose(1,0),'*', linewidth=2)
ax[4].plot(temperature_mean_t, linewidth=3, color='r')
ax[4].set_ylabel('°C')
ax[4].set_xlabel('dll step')

fig.suptitle(f"Calculate DRNU; wafer ID: {waferID_chipID[0]}, chip ID: {waferID_chipID[1]}")
plt.show()

plotly_fig = tls.mpl_to_plotly(fig)
plotly.offline.plot(plotly_fig, filename =  f'scripts/plots/{time.strftime("%Y%m%d_%H%M")}_calc_plot_DRNU_fig.html', auto_open=False)