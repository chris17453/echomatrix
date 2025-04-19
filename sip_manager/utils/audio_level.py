#!/usr/bin/env python3

import argparse
import wave
import numpy as np
import os
import sys

def analyze_last_second(file_path, sample_duration=1.0):
    try:
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
            print("File is missing or too small.")
            return 0.0

        with wave.open(file_path, 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frame_rate = wf.getframerate()
            n_frames = wf.getnframes()

            frames_to_read = int(frame_rate * sample_duration)
            frames_to_read = min(frames_to_read, n_frames)

            wf.setpos(max(0, n_frames - frames_to_read))
            frames = wf.readframes(frames_to_read)

            if sample_width == 2:
                dtype = np.int16
            elif sample_width == 1:
                dtype = np.uint8
            elif sample_width == 4:
                dtype = np.int32
            else:
                print(f"Unsupported sample width: {sample_width}")
                return 0.0

            data = np.frombuffer(frames, dtype=dtype)

            if sample_width == 1:
                data = data - 128  # center 8-bit

            if channels > 1:
                data = data[::channels]  # use first channel

            if len(data) > 0:
                rms = np.sqrt(np.mean(np.square(data.astype(np.float32))))
                return rms
            else:
                return 0.0

    except Exception as e:
        print(f"Error analyzing audio: {e}")
        return 0.0

def main():
    parser = argparse.ArgumentParser(description="Analyze RMS of last 1s of a WAV file.")
    parser.add_argument("file", help="Path to the WAV file")
    args = parser.parse_args()

    rms = analyze_last_second(args.file)
    print(f"RMS Level: {rms:.2f}")

if __name__ == "__main__":
    main()
