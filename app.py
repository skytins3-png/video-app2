import math
import runpy
import tempfile
from pathlib import Path

import streamlit as st
from video_engine import advance_scene, assemble, duration, storyboard

st.set_page_config(page_title='가사로 영상 만들기', page_icon='🎬', layout='centered')
st.markdown('<style>.stButton>button,.stDownloadButton>button{width:100%;min-height:3rem}</style>', unsafe_allow_html=True)
mode = st.radio('작업 선택', ['GPT로 가사 영상 만들기', '기존 영상 + 음원 합치기'], horizontal=True)
if mode == '기존 영상 + 음원 합치기':
    runpy.run_path(str(Path(__file__).with_name('legacy_merger.py')))
    st.stop()

st.title('🎬 가사로 영상 만들기')
st.caption('GPT 가사 해석 → 장면 이미지 생성 → 확대·이동 효과와 노래 → MP4 저장')
st.info('OpenAI API 키로 GPT를 사용합니다. 가사 분석과 이미지 생성에는 별도 API 사용료가 발생합니다.')
key = st.text_input('OpenAI API 키', type='password', key='openai_api_key', help='이 브라우저 세션에서만 사용하며 코드나 파일에 저장하지 않습니다.')
lyrics = st.text_area('1. 가사 또는 만들고 싶은 이야기', height=240, max_chars=16000,
                      placeholder='가사를 여기에 붙여 넣으세요.')
photo = st.file_uploader('2. 인물·분위기 참고 사진 (선택)', type=['png', 'jpg', 'jpeg'])
st.caption('사진을 넣으면 장면 이미지 생성에 참고합니다. 완성본은 이미지에 확대·이동 효과를 준 영상이며, 인물의 동작을 생성하는 방식은 아닙니다.')
audio = st.file_uploader('3. 함께 넣을 노래 (선택)', type=['mp3', 'wav', 'm4a'])
aspect = st.selectbox('화면 비율', ['9:16', '16:9'])
style = st.selectbox('영상 분위기', ['영화 같은 실사', '서정적인 수채화 애니메이션', '따뜻한 여행 영상'])
seconds = st.slider('노래 없이 만들 때 영상 길이 (초)', 8, 320, 32, 8, disabled=audio is not None)
st.caption('노래를 올리면 그 길이에 맞춥니다(최대 5분 20초). 장면은 8초 단위입니다. 가사별 정밀한 노래 타이밍 정렬은 포함하지 않습니다.')

def client_for_session():
    from openai import OpenAI
    return OpenAI(api_key=key.strip(), timeout=180, max_retries=0)

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
            scene['destination'] = str(folder / f'scene_{i:03}.png')
        previous = st.session_state.get('job')
        if previous:
            previous['folder_obj'].cleanup()
        st.session_state.job = dict(provider='openai', scenes=scenes, folder_obj=folder_obj,
            folder=str(folder), seconds=seconds, aspect=aspect,
            reference=(photo.getvalue(), photo.type) if photo else None,
            audio=str(audio_path) if audio_path else None)
        st.session_state.pop('result', None)
    except Exception:
        folder_obj.cleanup()
        st.error('장면 구성에 실패했습니다. API 키·결제 연결·모델 이용 권한과 음원 형식을 확인해 주세요.')

job = st.session_state.get('job')
if job and job.get('provider') != 'openai':
    job['folder_obj'].cleanup()
    st.session_state.pop('job', None)
    st.session_state.pop('result', None)
    job = None
if job:
    st.subheader('만들 장면')
    st.caption('아래 구성은 분석 당시 입력 기준입니다. 입력을 바꿨다면 장면 구성을 다시 눌러주세요.')
    for i, scene in enumerate(job['scenes']):
        st.write(f"{i+1}. {scene['summary']}")
    st.write(f"총 {len(job['scenes'])}장면 · 이미지 {len(job['scenes'])}장 · 완성본 {job['seconds']:.1f}초")
    st.caption('장면 수만큼 이미지를 생성합니다. 생성 버튼을 누르면 표시된 전체 장면을 요청합니다.')
    st.link_button('OpenAI 공식 API 요금 확인', 'https://developers.openai.com/api/docs/pricing')
    if st.button('GPT 이미지 생성하고 MP4 만들기 / 이어서 만들기', disabled=not key.strip()):
        progress = st.progress(0)
        status = st.empty()
        try:
            with client_for_session() as client:
                for i, scene in enumerate(job['scenes']):
                    status.info(f"{i+1}/{len(job['scenes'])} 장면 생성 중… 이 화면을 열어 두세요.")
                    advance_scene(client, scene, job['aspect'], job['reference'])
                    progress.progress((i+1)/len(job['scenes']))
            status.info('장면을 연결하고 노래를 합치는 중…')
            st.session_state.result = assemble(job['scenes'], job['folder'],
                job['seconds'], job['aspect'], job['audio'])
            status.success('완성되었습니다. 아래에서 재생하고 저장하세요.')
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error('생성 또는 합성에 실패했습니다. API 이용 권한·잔액·네트워크를 확인해 주세요. 완성된 이미지는 같은 세션에서 재사용합니다. 실패한 요청을 다시 시도하면 추가 비용이 발생할 수 있습니다.')
    st.caption('새로고침하거나 앱이 재시작되면 작업 기록을 잃을 수 있습니다. 완성되면 바로 저장하세요.')
if st.session_state.get('result'):
    st.video(st.session_state.result)
    st.download_button('📥 완성된 MP4 저장', st.session_state.result,
                       file_name='가사_뮤직비디오.mp4', mime='video/mp4')
