import os

from dotenv import load_dotenv
import assemblyai as aai

import utils

# load environment variables
load_dotenv()

aai.settings.api_key = os.environ.get('ASSEMBLYAI_API_KEY')

# ensure all required environment variables are available
if not aai.settings.api_key:
    raise RuntimeError("Missing ASSEMBLYAI_API_KEY")

# instantiate AssemblyAI transcriber with multichannel speech-to-text enabled
config = aai.TranscriptionConfig(multichannel=True)
transcriber = aai.Transcriber(config=config)

def main():
    # combine all participant audio files into a single audio file
    path = "combined_audio.m4a"
    utils.combine_tracks(path, dir="recordings")
    
    # send to AssemblyAI for multichannel speech-to-text and print the results
    transcript = transcriber.transcribe(path)
    print(f"Number of channels: {transcript.json_response["audio_channels"]}")
    for utt in transcript.utterances:
        print(utt)

if __name__ == "__main__":
    main()
