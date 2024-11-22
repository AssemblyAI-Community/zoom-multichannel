import os

from dotenv import load_dotenv
import assemblyai as aai

import utils
from utils.zoom import ZoomClient

# load environment variables
load_dotenv()

# assign to variables
ZOOM_ACCOUNT_ID = os.environ.get('ZOOM_ACCOUNT_ID')
ZOOM_CLIENT_ID = os.environ.get('ZOOM_CLIENT_ID')
ZOOM_CLIENT_SECRET = os.environ.get('ZOOM_CLIENT_SECRET')
aai.settings.api_key = os.environ.get('ASSEMBLYAI_API_KEY')

# ensure all required environment variables are available
if not all([ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, aai.settings.api_key]):
    raise RuntimeError(
        "Missing one or more required environment variables: "
        "ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ASSEMBLYAI_API_KEY"
    )

# instantiate Zoom client to interact with Zoom API
client = ZoomClient(account_id=ZOOM_ACCOUNT_ID, client_id=ZOOM_CLIENT_ID, client_secret=ZOOM_CLIENT_SECRET)

# instantiate AssemblyAI transcriber with multichannel speech-to-text enabled
config = aai.TranscriptionConfig(multichannel=True)
transcriber = aai.Transcriber(config=config)

def main():
    # download each participant audio files for the most recent Zoom meeting
    params = {'from': '2024-11-14'}  # query parameters for Zoom API request
    meets = client.get_recordings(params=params)
    meeting_uuid = meets["meetings"][0]["uuid"]
    client.download_participant_audio_files(meeting_uuid)
    
    # combine all participant audio files into a single audio file
    path = "combined_audio.m4a"
    utils.combine_tracks(path, dir="tmp")
    
    # send to AssemblyAI for multichannel speech-to-text and print the results
    transcript = transcriber.transcribe(path)
    print(f"Number of channels: {transcript.json_response["audio_channels"]}")
    for utt in transcript.utterances:
        print(utt)

if __name__ == "__main__":
    main()
