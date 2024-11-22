import os
import shutil

import ffmpeg


def combine_tracks(filepath="combined_audio.m4a", dir="tmp"):
    # List input files from the 'tmp' directory
    input_files = [os.path.join(dir, file) for file in os.listdir(dir) if file.endswith('.m4a')]
    if not input_files:
        raise ValueError("No input files found in the 'tmp' directory.")

    inputs = [ffmpeg.input(file) for file in input_files]
    num_inputs = len(input_files)

    if len(input_files) == 1:
        shutil.copy(input_files[0], filepath)
        return
    elif len(input_files) == 2:
        join_filter = f'[0:a][1:a]join=inputs={num_inputs}[a]'
    else:
        # ffmpeg incorrectly assumes 2 channel => stereo rather than dual mono in case of two files
        join_filter = f'[0:a][1:a]join=inputs={num_inputs}:channel_layout={num_inputs}.0[a]'

    # Run the ffmpeg command to combine the tracks
    try:
        a = ffmpeg.output(*inputs, filepath, filter_complex=join_filter, **{'loglevel': 'error', 'map': '[a]'}).compile()
        print(a)
        return a
    except ffmpeg.Error as e:
        # Check if stderr is None or empty and raise more detailed error
        error_message = e.stderr.decode() if e.stderr else f"No detailed error message available. Raw error: {str(e)}"
        print(f"FFmpeg Error: {error_message}")  # Print the error message to help with debugging
        raise RuntimeError(f"FFmpeg error: {error_message}") from e
