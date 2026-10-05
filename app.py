import math
import runpy
import tempfile
import time
from pathlib import Path

import streamlit as st
from video_engine import advance_scene, assemble, duration, storyboard

st.set_page_config(page_title='가사로 영상 만들기', page_icon='🎬', layout='centered')
st.markdown('<style>.stButton>button,.stDownloadButton>button{width:100%;min-height:3rem}</style>', unsafe_allow_html=True)
mode = st.radio('작업 선택', ['가사로 AI 영상 만들기', '기존 영상 + 음원 합치기'], horizontal=True)
if mode == '기존 영상 + 음원 합치기':
    runpy.run_path(str(Path(__file__).with_name('legacy_merger.py')))
    st.stop()

st.title('🎬 가사로 영상 만들기')
st.caption('가사 해석 → 장면별 움직이는 영상 생성 → 노래 합성 → MP4 저장')
st.info('Google Veo 생성용 API 키가 필요합니다. AI 생성에는 별도 사용료가 발생합니다. GitHub 연결 권한은 생성 서비스 이용권이 아닙니다.')
key = st.text_input('Gemini API 키', type='password', key='api_key', help='이 브라우저 세션에서만 사용하며 코드나 파일에 저장하지 않습니다.')
lyrics = st.text_area('1. 가사 또는 만들고 싶은 이야기', height=240, max_chars=16000,
                      placeholder='가사를 여기에 붙여 넣으세요.')
photo = st.file_uploader('2. 시작 장면 참고 사진 (선택)', type=['png', 'jpg', 'jpeg'])
st.caption('사진을 넣으면 각 장면의 시작 이미지로 사용합니다. 인물의 일관성과 장면 사이 연결은 생성 결과에 따라 달라집니다.')
audio = st.file_uploader('3. 함께 넣을 노래 (선택)', type=['mp3', 'wav', 'm4a'])
aspect = st.selectbox('화면 비율', ['9:16', '16:9'])
style = st.selectbox('영상 분위기', ['영화 같은 실사', '서정적인 수채화 애니메이션', '따뜻한 여행 영상'])
seconds = st.slider('노래 없이 만들 때 영상 길이 (초)', 8, 320, 32, 8, disabled=audio is not None)
st.caption('노래를 올리면 그 길이에 맞춥니다(최대 5분 20초). 장면은 8초 단위입니다. 가사별 정밀한 노래 타이밍 정렬은 포함하지 않습니다.')

def client_for_session():
    from google import genai
    return genai.Client(api_key=key.strip())

if st.button('가사 분석하고 장면 구성하기', disabled=not key.strip() or not lyrics.strip()):
    folder_obj = tempfile.TemporaryDirectory(prefix='lyrics_video_')
    folder = Path(folder_obj.name)
    try:
        audio_path = None
        if audio:
            audio_path = folder / ('song' + Path(audio.name).suffix.lower())
            audio_path.write_bytes(audio.getvalue())
            seconds = duration(audio_path)
        count = math.ceil(seconds / 8)
        with st.spinner('가사의 장소·상황·감정을 읽고 있습니다…'):
            with client_for_session() as client:
                scenes = storyboard(client, lyrics, count, style)
        for i, scene in enumerate(scenes):
            scene['destination'] = str(folder / f'raw_{i:03}.mp4')
        previous = st.session_state.get('job')
        if previous:
            previous['folder_obj'].cleanup()
        st.session_state.job = dict(scenes=scenes, folder_obj=folder_obj,
            folder=str(folder), seconds=seconds, aspect=aspect,
            reference=(photo.getvalue(), photo.type) if photo else None,
            audio=str(audio_path) if audio_path else None)
        st.session_state.pop('result', None)
    except Exception:
        folder_obj.cleanup()
        st.error('장면 구성에 실패했습니다. API 키·결제 연결·모델 이용 권한과 음원 형식을 확인해 주세요.')

job = st.session_state.get('job')
if job:
    st.subheader('만들 장면')
    st.caption('아래 구성은 분석 당시 입력 기준입니다. 입력을 바꿨다면 장면 구성을 다시 눌러주세요.')
    for i, scene in enumerate(job['scenes']):
        st.write(f"{i+1}. {scene['summary']}")
    st.write(f"총 {len(job['scenes'])}장면 · AI 생성 {len(job['scenes'])*8}초 · 완성본 {job['seconds']:.1f}초")
    st.caption('장면 수에 따라 영상 생성 비용이 커집니다. 생성 버튼을 누르면 이 전체 분량을 요청합니다.')
    st.link_button('Veo 공식 생성 요금 확인', 'https://ai.google.dev/gemini-api/docs/pricing#veo-3.1')
    if st.button('이 구성으로 유료 AI 영상 생성 / 이어서 확인', disabled=not key.strip()):
        progress = st.progress(0)
        status = st.empty()
        try:
            with client_for_session() as client:
                deadline = time.monotonic() + 600
                for i, scene in enumerate(job['scenes']):
                    status.info(f"{i+1}/{len(job['scenes'])} 장면 생성 중… 이 화면을 열어 두세요.")
                    while not advance_scene(client, scene, job['aspect'], job['reference']):
                        if time.monotonic() > deadline:
                            raise TimeoutError()
                        time.sleep(5)
                    progress.progress((i+1)/len(job['scenes']))
            status.info('장면을 연결하고 노래를 합치는 중…')
            st.session_state.result = assemble(job['scenes'], job['folder'],
                job['seconds'], job['aspect'], job['audio'])
            status.success('완성되었습니다. 아래에서 재생하고 저장하세요.')
        except TimeoutError:
            st.warning('생성이 계속 진행 중입니다. 같은 버튼으로 이어서 확인하세요. 접수된 장면은 다시 요청하지 않습니다.')
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error('생성 또는 합성에 실패했습니다. API 이용 권한·잔액·네트워크를 확인해 주세요. 접수된 작업은 같은 세션에서 이어서 확인할 수 있습니다.')
    st.caption('새로고침하거나 앱이 재시작되면 작업 기록을 잃을 수 있습니다. 완성되면 바로 저장하세요.')
if st.session_state.get('result'):
    st.video(st.session_state.result)
    st.download_button('📥 완성된 MP4 저장', st.session_state.result,
                       file_name='가사_뮤직비디오.mp4', mime='video/mp4')
