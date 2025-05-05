import h5py
import os
from glob import glob

"""
    sample script to analyze data recored using the GUI
"""


def analyze_hdf5_file(filepath: str):

    print(f"\n--- Analyzing: {os.path.basename(filepath)} ---")

    with h5py.File(filepath, 'r') as f:

        # Meta data
        print("Metadata:")
        for key, value in f.attrs.items():
            print(f"  {key}: {value}")

        if 'frames' not in f or 'timestamps' not in f:
            print("Missing 'frames' or 'timestamps' dataset.")
            return

        # DCS data
        frames = f['frames']
        timestamps = f['timestamps']
        frame_count = frames.shape[0]
        timestamp_count = timestamps.shape[0]

        print("\nData Summary:")
        print(f" Total Frames: {frame_count}")
        print(f" Total timestamps: {timestamp_count}")
        print(f" Frame Shape: {frames.shape[1:]}")

        if frame_count != timestamp_count:
            print(" Frames and timestamps count do not align.")
        else:
            print(" Frames and timestamps are aligned.")


def analyze_all_hdf5_files(dir):
    if not os.path.isdir(dir):
        print(f"dir: '{dir}' does not exist.")
        return

    files = sorted(glob(os.path.join(dir, "*.h5")))
    if not files:
        print(f"No .h5 files found in the dir: {dir}")
        return

    for filepath in files:
        analyze_hdf5_file(filepath)

    print("\n--- End of Analysis ---")


if __name__ == "__main__":
    analyze_all_hdf5_files(dir="captured_data")
