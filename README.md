# 가사로 AI 영상 만들기

Streamlit entry point: `app.py`. System dependency: `ffmpeg` (packages.txt).

Lyrics are interpreted into a storyboard by Gemini 2.5 Flash. Each shot is generated
as an actual 8-second Veo 3.1 video. FFmpeg normalizes and joins shots, removes their
generated sound, and optionally adds the uploaded song. Output is 720p MP4.
The existing video/audio merger remains available as a separate mode.

## Setup

Install requirements and run `streamlit run app.py`. Enter a Gemini API key with
billing and Veo access in the app's password field. Keys are session-only and are
never committed or written to disk. GitHub access does not grant Gemini API access.
No paid generation starts until the explicit video generation button is pressed.
Review the displayed total generation seconds and official pricing first.

## Limits and verification

- Up to 320 seconds, generated as ceil(duration/8) independently billed shots.
- Optional photo is each shot's first frame, not guaranteed identity consistency.
- The storyboard covers the narrative; exact lyric-to-vocal alignment is not implemented.
- Audio is encoded to AAC 320k without EQ, compression, normalization or other effects.
- Operation IDs prevent implicit resubmission while the Streamlit session remains alive.
- Refresh/server restart can lose in-memory job state. Download completed output promptly.
- API failures do not fall back to fake or stock footage.
- Live paid Gemini/Veo generation requires an account key and was not verified during implementation.

Official API reference: https://ai.google.dev/gemini-api/docs/veo
