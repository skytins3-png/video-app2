# GPT 가사 영상 만들기

Streamlit entry point: `app.py`; system dependency: `ffmpeg` (packages.txt).

GPT-4.1 interprets lyrics into a structured storyboard. GPT Image 1 generates or
edits one image per scene, optionally using a reference photo. FFmpeg applies slow
zoom and fades, joins the scenes, and adds the uploaded song. Output is 720p MP4.
This is an animated image montage, not generated actor motion or lip synchronization.
The existing video/audio merger remains available in a separate mode.

## Setup

Install requirements and run `streamlit run app.py`. Supply an OpenAI API key in the
session password field. Keys are never written to disk or committed. The storyboard
and image requests use the key's separate API billing. No image calls start until
the generation button is pressed. Requests use max_retries=0 to avoid automatic
paid retries. Completed scene images are reused on subsequent button presses.

## Limits and validation

- Up to 320 seconds, one image per 8-second scene.
- Reference photo identity consistency is not guaranteed.
- Exact alignment with sung words is not implemented.
- Audio uses AAC 320k without EQ, compression or normalization.
- Session refresh/restart can lose job state. Download the result promptly.
- A failed/timed-out image request may have incurred charges; manual retry may bill again.
- Local UI, mocked API/resume behavior and FFmpeg tested. Real paid generation is
  unverified because no API key is available in the execution environment.

Official docs:
https://developers.openai.com/api/docs/guides/structured-outputs
https://developers.openai.com/api/reference/resources/images/methods/generate
