import os
import shutil

import ffmpeg


def combine_tracks(filepath="combined_audio.m4a", dir="tmp", safe=True):
    if safe and os.path.exists(filepath):
        raise FileExistsError(f"The file '{filepath}' already exists.")
        
    input_files = [os.path.join(dir, file) for file in os.listdir(dir) if file.endswith('.m4a')]
    if not input_files:
        raise ValueError("No input files found in the 'tmp' directory.")

    inputs = [ffmpeg.input(file) for file in input_files]

    # Dynamically generate `-map` arguments for separate tracks
    map_args = []
    for i in range(len(inputs)):
        map_args.extend(["-map", f"{i}:a"])

    ffmpeg_command = (
        ffmpeg
        .output(*inputs, filepath, **{'loglevel': 'error'})
        .global_args(*map_args)
    )

    if not safe:
        ffmpeg_command = ffmpeg_command.overwrite_output()

    try:
        ffmpeg_command.run()
    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if e.stderr else f"No detailed error message available. Raw error: {str(e)}"
        raise RuntimeError(f"FFmpeg error: {error_message}") from e
