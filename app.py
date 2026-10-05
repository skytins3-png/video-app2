import os
import subprocess
import tempfile
import streamlit as st

st.set_page_config(page_title="영상+음원 합성기", page_icon="🎬", layout="centered")

st.markdown(
    """
    <style>
    .stButton>button { width: 100%; height: 3.5rem; font-size: 1.2rem; font-weight: bold; border-radius: 12px; background-color: #FF4B4B; color: white; }
    .stDownloadButton>button { width: 100%; height: 3.5rem; font-size: 1.2rem; font-weight: bold; border-radius: 12px; background-color: #0083B8; color: white; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🎬 영상 + 음원 모바일 합성기")
st.caption("스마트폰 영상과 노래를 올려 원클릭으로 합치세요.")

video_file = st.file_uploader("1️⃣ 무음 수채화 영상 선택 (MP4)", type=["mp4", "mov"])
audio_file = st.file_uploader(
    "2️⃣ 교체할 노래 파일 선택 (MP3/WAV)", type=["mp3", "wav", "m4a"]
)
loop_video = st.checkbox(
    "노래가 끝날 때까지 영상 자동 반복(Loop)", value=True
)

if video_file and audio_file:
  st.info("두 파일이 모두 선택되었습니다. 아래 합성 버튼을 눌러주세요.")
  if st.button("🚀 원본 소리 지우고 새 노래로 합성하기"):
    with st.spinner("영상을 합성하는 중입니다... 잠시만 기다려 주세요."):
      with tempfile.NamedTemporaryFile(
          delete=False, suffix=".mp4"
      ) as t_in_v:
        t_in_v.write(video_file.read())
        temp_video_path = t_in_v.name

      with tempfile.NamedTemporaryFile(
          delete=False, suffix=".mp3"
      ) as t_in_a:
        t_in_a.write(audio_file.read())
        temp_audio_path = t_in_a.name

      temp_output_path = tempfile.mktemp(suffix=".mp4")

      cmd = ["ffmpeg", "-y"]
      if loop_video:
        cmd.extend(["-stream_loop", "-1"])
      cmd.extend([
          "-i",
          temp_video_path,
          "-i",
          temp_audio_path,
          "-map",
          "0:v:0",
          "-map",
          "1:a:0",
          "-c:v",
          "copy",
          "-c:a",
          "aac",
          "-b:a",
          "192k",
          "-shortest",
          temp_output_path,
      ])

      try:
        subprocess.run(cmd, check=True)
        with open(temp_output_path, "rb") as f:
          output_bytes = f.read()
        st.success("✅ 합성이 완료되었습니다!")
        st.video(output_bytes)
        st.download_button(
            label="📥 완성된 영상 스마트폰에 저장하기",
            data=output_bytes,
            file_name="유튜브_완성본.mp4",
            mime="video/mp4",
        )
      except Exception as e:
        st.error(f"오류 발생: {e}")
      finally:
        for p in [temp_video_path, temp_audio_path, temp_output_path]:
          if os.path.exists(p):
            try:
              os.remove(p)
            except:
              pass
