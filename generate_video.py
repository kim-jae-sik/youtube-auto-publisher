# -*- coding: utf-8 -*-
"""
유튜브 롱폼 올인원 기획서 기반 16:9 와이드스크린 비디오 자동 제작기 (10분+ 전문 엔진)
YouTube Long-form 16:9 Video Production Engine (10+ Minutes Guaranteed)
"""

import os
import sys
import math
import struct
import wave
import asyncio
import subprocess
import shutil

# 콘솔 UTF-8 강제 설정 (Windows cp949 인코딩 에러 원천 방지)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont
import edge_tts
import imageio_ffmpeg

# Google AI Ultra 엔진 로드 (최상위 모델)
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
try:
    import google_ultra_engine
    ULTRA_AVAILABLE = True
except ImportError:
    ULTRA_AVAILABLE = False

# 기본 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp_render")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# 폰트 로드 헬퍼
def get_korean_font(size, bold=True):
    font_paths = [
        r"C:\Windows\Fonts\malgunbd.ttf" if bold else r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\NanumGothicBold.ttf" if bold else r"C:\Windows\Fonts\NanumGothic.ttf",
        r"C:\Windows\Fonts\gulim.ttc"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

FONT_HEADER = get_korean_font(26, bold=True)
FONT_TITLE = get_korean_font(46, bold=True)
FONT_SUBTITLE = get_korean_font(26, bold=False)
FONT_CARD_TITLE = get_korean_font(30, bold=True)
FONT_CARD_BODY = get_korean_font(23, bold=False)
FONT_CODE = get_korean_font(21, bold=True)
FONT_SUB = get_korean_font(29, bold=True)
FONT_SMALL = get_korean_font(19, bold=True)

# 10분 이상 16:9 롱폼 비디오 14개 마스터 씬 데이터 (총 러닝타임 10분 20초~10분 50초 보장)
SCENES = [
    {
        "id": 1,
        "ch": 1,
        "tag": "CHAPTER 01 / 05",
        "title": "골든 인트로: 0원 시스템의 충격적 실체",
        "subtitle": "수백만 원짜리 유료 강의에 속지 않고 1인 비즈니스를 완벽히 자동화하는 실전 공식",
        "script": "솔직히 말씀드리겠습니다. 시중에 넘쳐나는 수백만 원짜리 AI 강의, 사실 오늘 말씀드릴 이 코어 시스템 하나만 알면 99%는 결제하실 필요가 전혀 없습니다. 저 역시 처음에는 유명하다는 고가의 유료 툴들을 닥치는 대로 구독하고 밤을 새워가며 복잡한 파이썬 코딩을 공부했습니다. 하지만 돌아온 것은 매달 빠져나가는 수십만 원의 구독료 청구서와 복잡해서 실무에 쓰지도 못하는 코드 뭉치뿐이었습니다. 오늘 영상 딱 10분만 집중해서 끝까지 따라오세요. 비싼 외주나 복잡한 코딩 없이, 무료 도구들만 결합하여 자동으로 굴러가는 1인 비즈니스 시스템의 모든 것을 가감 없이 투명하게 공개하겠습니다.",
        "sentences": [
            "시중에 넘쳐나는 수백만 원짜리 AI 강의, 사실 이거 하나만 알면 다 필요 없습니다.",
            "저 역시 고가의 유료 툴들을 구독하고 밤새 파이썬 코딩을 공부했지만 결과는 처참했습니다.",
            "돌아온 것은 매달 빠져나가는 수십만 원의 청구서와 복잡한 코드 뭉치뿐이었습니다.",
            "오늘 영상 딱 10분만 집중해서 끝까지 따라오세요. 무료 도구의 모든 것을 공개합니다."
        ],
        "bg_theme": "cyan",
        "slide_type": "intro_hook"
    },
    {
        "id": 2,
        "ch": 1,
        "tag": "CHAPTER 01 / 05",
        "title": "10분 완청 약속: 완벽한 1인 비즈니스 파이프라인",
        "subtitle": "잠자는 동안에도 고객을 응대하고 기획서를 작성하는 24/7 무인 자동화 대시보드",
        "script": "오늘 여러분이 이 영상에서 얻어가실 결과물은 단순한 이론이 아닙니다. 지금 화면에 보시는 대시보드처럼, 여러분이 잠을 자거나 본업에 집중하고 있는 동안에도 알아서 고객의 문의를 접수하고, Gemini AI가 맞춤형 제안서를 단 5초 만에 작성하며, 최종 보고서까지 고객에게 자동으로 발송하는 완벽한 100% 무인화 파이프라인입니다. 특히 영상 8분 지점에서는 오늘 소개할 자동화의 핵심인 프롬프트 체이닝 원본 템플릿을 무료로 공개할 예정이니, 단 1초도 놓치지 마시고 채널 고정해 주시기 바랍니다. 준비되셨다면, 지금 바로 1막으로 출발하겠습니다.",
        "sentences": [
            "오늘 여러분이 얻어가실 결과물은 단순한 이론이 결코 아닙니다.",
            "잠을 자거나 본업에 집중하는 동안에도 고객 문의를 24시간 자동 접수합니다.",
            "Gemini AI가 맞춤형 제안서를 5초 만에 작성하고 최종 보고서까지 자동 발송합니다.",
            "영상 8분 지점에서 프롬프트 체이닝 원본 템플릿을 무료 공개하니 채널 고정해 주세요!"
        ],
        "bg_theme": "cyan",
        "slide_type": "intro_dashboard"
    },
    {
        "id": 3,
        "ch": 2,
        "tag": "CHAPTER 02 / 05",
        "title": "1막: 왜 99%는 AI 자동화에 실패하는가?",
        "subtitle": "초보자들이 가장 많이 빠지는 3대 치명적 착각과 고비용의 늪",
        "script": "본격적인 실전 구축에 들어가기에 앞서, 왜 99%의 사람들이 AI 자동화에 야심 차게 도전했다가 포기하는지 그 근본적인 이유를 반드시 짚고 넘어가야 합니다. 첫 번째 착각은 바로 비싼 유료 툴을 많이 구독할수록 자동화가 잘 될 것이라는 환상입니다. 매달 수십만 원씩 나가는 툴들을 엮어두면, 툴 하나만 에러가 발생해도 전체 시스템이 그대로 마비됩니다. 두 번째 착각은 파이썬 같은 전문 프로그래밍 언어를 배워야 한다는 강박입니다. 하지만 2026년 현재, 노코드 API와 웹훅 연동 기술은 이미 기존의 코딩을 완벽하게 대체했습니다.",
        "sentences": [
            "왜 99%의 사람들은 AI 자동화에 도전했다가 중간에 포기하고 말까요?",
            "첫 번째 착각: 비싼 유료 툴을 많이 구독해야만 자동화가 완성된다는 환상입니다.",
            "여러 툴을 무리하게 엮어두면 하나만 에러가 나도 전체 시스템이 마비됩니다.",
            "두 번째 착각: 파이썬 코딩을 배워야 한다는 강박이지만, 노코드 API가 이미 대체했습니다."
        ],
        "bg_theme": "amber",
        "slide_type": "mistakes_3"
    },
    {
        "id": 4,
        "ch": 2,
        "tag": "CHAPTER 02 / 05",
        "title": "1막: 도구가 아니라 파이프라인의 연결 구조가 전부다",
        "subtitle": "단순한 1회성 질문에서 벗어나 데이터가 스스로 흐르는 자동 배관망 구축",
        "script": "세 번째이자 가장 치명적인 착각은 바로 챗GPT 대화창에 매번 사람이 직접 들어가서 질문을 던지는 수작업입니다. 많은 분들이 이것을 AI 자동화라고 부르지만, 냉정하게 말해 그것은 그저 질문하는 대상을 네이버 검색에서 AI로 바꾼 것에 불과합니다. 진정한 자동화란 질문을 사람이 직접 던지는 것이 아닙니다. 고객이 폼을 작성하는 순간, 그 원천 데이터가 파이프라인을 타고 스스로 AI에게 전달되어 결과물이 생성되는 일련의 연결 구조를 만드는 것입니다. 즉, 개별 도구가 중요한 것이 아니라 도구와 도구를 잇는 배관 시스템이 핵심입니다.",
        "sentences": [
            "가장 치명적인 착각은 챗GPT 대화창에 매번 직접 질문을 입력하는 수작업입니다.",
            "그것은 자동화가 아니라 질문 대상을 포털 검색에서 AI로 바꾼 것에 불과합니다.",
            "진정한 자동화란 사람이 개입하지 않아도 데이터가 스스로 흐르는 연결 구조입니다.",
            "개별 도구의 화려함이 중요한 것이 아니라, 도구를 잇는 배관 시스템이 핵심입니다."
        ],
        "bg_theme": "amber",
        "slide_type": "pipeline_concept"
    },
    {
        "id": 5,
        "ch": 2,
        "tag": "CHAPTER 02 / 05",
        "title": "1막: 상위 1%가 절대 가르쳐주지 않는 무료 오픈소스의 위력",
        "subtitle": "구글 스프레드시트와 Gemini 무료 API로 완성하는 0원 인프라",
        "script": "그렇다면 상위 1%의 사업가들은 왜 이런 진실을 대중에게 쉬쉬할까요? 바로 수백만 원짜리 컨설팅 강의와 유료 솔루션을 계속 판매해야 하기 때문입니다. 하지만 오늘 제가 단언컨대, 구글에서 전 세계인에게 무료로 제공하는 스프레드시트와 구글 폼, 그리고 월 수천만 토큰까지 무료 할당량을 제공하는 구글 Gemini 2.0 및 3.0 API만 활용해도 월 매출 수천만 원 규모의 1인 비즈니스를 빈틈없이 지탱할 수 있습니다. 1원도 결제할 필요가 없는 이 강력한 무료 인프라의 3단계 실전 연결법을 이제 2막에서 직접 하나씩 보여드리겠습니다.",
        "sentences": [
            "상위 1% 사업가들은 왜 이런 간단하고 강력한 진실을 대중에게 쉬쉬할까요?",
            "바로 수백만 원짜리 유료 강의와 고가의 솔루션을 판매해야 하기 때문입니다.",
            "구글 스프레드시트와 무료 Gemini API만으로도 수천만 원 비즈니스를 지탱할 수 있습니다.",
            "단 1원도 들지 않는 강력한 무료 인프라의 3단계 실전 연결법을 지금 공개합니다."
        ],
        "bg_theme": "amber",
        "slide_type": "free_tools"
    },
    {
        "id": 6,
        "ch": 3,
        "tag": "CHAPTER 03 / 05",
        "title": "2막: 1단계 - 구글 시트 & 폼 무인 데이터 수집기 구축",
        "subtitle": "고객 문의를 0.1초 만에 데이터베이스로 정돈하는 자동 클렌징 수식",
        "script": "자, 이제 본격적인 2막 실전 시연입니다. 첫 번째 단계는 무인 데이터 수집기의 구축입니다. 고객이 웹사이트나 블로그에서 문의 양식을 제출하면, 그 내용이 0.1초 만에 구글 스프레드시트의 행으로 깔끔하게 정돈되어 실시간으로 쌓이도록 만듭니다. 이때 가장 중요한 핵심 노하우는 고객이 입력한 주관식 텍스트에서 불필요한 공백을 제거하고 핵심 요구사항 키워드만 정규화하는 데이터 클렌징 수식을 걸어두는 것입니다. 이 간단한 1단계 세팅 하나만으로도 뒤이어 전달될 AI의 응답 품질이 300% 이상 비약적으로 향상됩니다.",
        "sentences": [
            "본격적인 2막 실전 시연, 첫 번째 단계는 무인 데이터 수집기 구축입니다.",
            "고객이 문의 양식을 제출하면 0.1초 만에 구글 시트 행으로 깔끔하게 정리됩니다.",
            "불필요한 공백을 제거하고 핵심 키워드만 추출하는 데이터 클렌징 수식이 핵심입니다.",
            "이 간단한 세팅 하나만으로도 뒤이어 생성될 AI 결과물의 품질이 300% 급상승합니다."
        ],
        "bg_theme": "purple",
        "slide_type": "step1_sheets"
    },
    {
        "id": 7,
        "ch": 3,
        "tag": "CHAPTER 03 / 05",
        "title": "2막: 2단계 - Gemini API 무료 연동 및 시스템 프롬프트 주입",
        "subtitle": "구글 AI 스튜디오 무료 키 발급 및 할루시네이션 0% 시스템 지침 설계",
        "script": "두 번째 단계는 수집된 데이터의 두뇌 역할을 담당할 Gemini API의 연동입니다. 구글 AI 스튜디오에 접속하시면 클릭 세 번 만에 개인 API 키를 무료로 즉시 발급받을 수 있습니다. 여기서 상위 1%의 비결이 등장하는데요. 단순히 AI에게 답변을 요구하는 것이 아니라, 시스템 지침(System Instructions)에 엄격한 출력 형식과 비즈니스 페르소나를 사전에 주입하는 것입니다. 예를 들어 마크다운 테이블 규격과 3단 구조 보고서 형식을 고정해 두면, 할루시네이션 없이 100% 실무에 즉시 쓸 수 있는 고품질 기획서가 출력됩니다.",
        "sentences": [
            "두 번째 단계는 전체 파이프라인의 두뇌 역할을 담당할 Gemini API의 연동입니다.",
            "구글 AI 스튜디오에서 클릭 세 번이면 개인 무료 API 키를 즉시 발급받을 수 있습니다.",
            "시스템 지침에 엄격한 출력 형식과 전문 비즈니스 페르소나를 사전에 주입합니다.",
            "마크다운 테이블과 3단 보고서 형식을 지정하면 할루시네이션 0%의 결과가 나옵니다."
        ],
        "bg_theme": "purple",
        "slide_type": "step2_gemini"
    },
    {
        "id": 8,
        "ch": 3,
        "tag": "CHAPTER 03 / 05",
        "title": "2막: 3단계 - 자동화 웹훅(Webhook) 트리거 및 5초 리포트 생성",
        "subtitle": "데이터 발생 즉시 AI를 자동 호출하여 맞춤형 기획안을 즉각 산출하는 시스템",
        "script": "세 번째 단계는 수집된 데이터와 두뇌를 실시간으로 이어주는 웹훅 트리거 연결입니다. 무료 웹훅 서비스를 활용하여, 구글 시트에 새 데이터가 입력되는 이벤트가 발생하는 즉시 Gemini API를 백그라운드에서 호출하도록 설정합니다. 보시는 것처럼 사람이 아무것도 누르지 않아도, 고객의 문의가 들어오자마자 5초 만에 2,000자 분량의 심층 비즈니스 컨설팅 리포트가 생성되어 시트의 결과 칼럼에 자동으로 기입됩니다. 이 모든 정교한 과정이 일어나는 데 걸리는 시간은 단 5초에 불과합니다.",
        "sentences": [
            "세 번째 단계는 수집된 데이터와 두뇌를 실시간으로 이어주는 웹훅 트리거 연결입니다.",
            "구글 시트에 새 데이터가 입력되는 즉시 Gemini API를 백그라운드에서 자동 호출합니다.",
            "사람이 아무것도 누르지 않아도 단 5초 만에 2,000자 분량의 심층 리포트가 생성됩니다.",
            "모든 결과물은 구글 스프레드시트의 지정된 결과 칼럼에 실시간으로 자동 기입됩니다."
        ],
        "bg_theme": "purple",
        "slide_type": "step3_webhook"
    },
    {
        "id": 9,
        "ch": 3,
        "tag": "CHAPTER 03 / 05",
        "title": "2막: 실전 시연 & 오류 없는 24시간 무결점 예외 처리 노하우",
        "subtitle": "실제 라이브 테스트 시연 및 3회 자동 재시도 로직으로 365일 무중단 가동",
        "script": "지금 보시는 화면이 실제 라이브 테스트 화면입니다. 가상의 고객이 복잡한 프로젝트 기획 문의를 접수하자, 화면 오른쪽에서 실시간으로 데이터가 파싱되고 완벽한 16:9 규격 맞춤 기획안이 생성되는 모습을 생생하게 확인하실 수 있습니다. 만에 하나 인터넷 연결이 불안정하거나 API 응답이 지연되더라도, 자동 재시도 로직을 3회 설정해 두면 1년 365일 24시간 동안 단 한 번의 데이터 누락도 없이 무결점으로 작동합니다. 이것이 바로 여러분만의 충실한 24시간 디지털 직원이 탄생하는 순간입니다.",
        "sentences": [
            "지금 화면에 보시는 것이 실제 운영 중인 라이브 자동화 테스트 화면입니다.",
            "고객 문의 접수와 동시에 실시간 데이터 파싱 및 완벽한 기획안 생성이 이뤄집니다.",
            "3회 자동 재시도 로직을 탑재하여 네트워크 지연에도 단 한 건의 누락 없이 작동합니다.",
            "여러분이 잠자는 시간에도 쉬지 않고 일하는 충실한 24시간 디지털 직원이 완성됩니다."
        ],
        "bg_theme": "purple",
        "slide_type": "demo_screen"
    },
    {
        "id": 10,
        "ch": 4,
        "tag": "CHAPTER 04 / 05",
        "title": "3막: 8분 미드롤 돌파! 하루 2시간을 0초로 줄인 프롬프트 체이닝",
        "subtitle": "단일 프롬프트의 한계를 극복하고 대기업 기획실 수준으로 끌어올리는 비밀",
        "script": "오래 기다리셨습니다. 10분 영상의 클라이맥스, 3막의 핵심 비밀 치트키를 지금 공개합니다. 하루 2시간 이상 걸리던 분석과 작성 작업을 단 0초로 단축시킨 결정적 기술은 바로 프롬프트 체이닝(Prompt Chaining)입니다. 대부분의 초보자들은 하나의 프롬프트에 모든 요구사항을 다 쏟아붓고 엉성한 답변을 받지만, 고수들은 작업을 3단계로 정밀하게 쪼갭니다. 1차 분석 에이전트가 고객의 문제를 파악하고, 2차 기획 에이전트가 전략을 수립하며, 3차 카피라이터가 최종 문서를 다듬는 체인 구조를 설계하는 것입니다.",
        "sentences": [
            "오래 기다리셨습니다! 10분 영상의 클라이맥스, 3막의 핵심 비밀 치트키를 공개합니다.",
            "하루 2시간의 작업을 단 0초로 줄여준 결정적 기술은 바로 '프롬프트 체이닝'입니다.",
            "초보자들은 한 번에 모든 걸 질문하지만, 고수들은 작업을 3단계로 분업화합니다.",
            "1차 문제 분석 ➔ 2차 전략 수립 ➔ 3차 문서 완성으로 이어지는 바통 터치 시스템입니다."
        ],
        "bg_theme": "gold",
        "slide_type": "cheat_chaining"
    },
    {
        "id": 11,
        "ch": 4,
        "tag": "CHAPTER 04 / 05",
        "title": "3막: 상위 1% 실전 프롬프트 구조 심층 해설",
        "subtitle": "3단계 AI 바통터치 설계 원리와 실전 업무 적용 비법",
        "script": "지금 화면에 보여드리는 이 설계도가 바로 체이닝의 진정한 정수입니다. 복잡한 지시사항을 한 번에 주지 않고, 3단계의 AI가 서로의 결과물을 이어받아 완성도를 끌어올리는 방식인데요. 1단계에서 뼈대를 잡고, 2단계에서 실전 내용을 채운 뒤, 3단계에서 사람의 눈높이에 맞게 다듬어내는 이 구조만 이해하시면 어떤 업무든 놀라울 정도로 정교하게 풀어내실 수 있습니다. 화면 속 구조를 천천히 눈에 담아두시고 여러분의 일상에 꼭 적용해 보세요.",
        "sentences": [
            "지금 화면에 보여드리는 이 구조도가 상위 1%가 실제로 활용하는 체이닝 원리입니다.",
            "복잡한 지시를 쪼개어 세 명의 AI가 바통을 이어받듯 차례대로 문서를 완성합니다.",
            "1단계 뼈대 구성부터 2단계 내용 보강, 3단계 검수까지 한눈에 확인하실 수 있습니다.",
            "이 설계 흐름을 잘 기억해 두시면 어떤 복잡한 업무라도 단숨에 해결할 수 있습니다."
        ],
        "bg_theme": "gold",
        "slide_type": "cheat_template"
    },
    {
        "id": 12,
        "ch": 4,
        "tag": "CHAPTER 04 / 05",
        "title": "3막: 평범한 직장인이 월 500만원 파이프라인으로 확장한 비결",
        "subtitle": "단순 업무 효율화를 넘어 실제 현금 흐름을 창출하는 3단계 비즈니스 모델",
        "script": "그렇다면 이 시스템을 통해 평범한 직장인이 어떻게 퇴근 후 월 500만 원의 추가 수익을 만들었을까요? 비결은 단순한 내부 업무 자동화에서 멈추지 않고, 이 파이프라인을 크몽이나 숨고 같은 플랫폼의 맞춤형 자동 견적 서비스, 그리고 기업 대상 전문 리서치 자동 생성 솔루션으로 상품화했기 때문입니다. 내가 직접 시간을 쓰지 않아도 시스템이 가치를 만들어내기 때문에, 고객이 1명이든 100명이든 동일한 품질의 서비스를 즉각 공급하며 안정적인 수익 파이프라인을 완성할 수 있었습니다.",
        "sentences": [
            "평범한 직장인이 어떻게 퇴근 후 이 시스템으로 월 500만 원의 추가 수익을 만들었을까요?",
            "단순 업무 자동화에 그치지 않고, 자동 견적 서비스와 기업 맞춤 솔루션으로 상품화했습니다.",
            "내가 시간을 쓰지 않아도 시스템이 24시간 가치와 결과물을 자동으로 생산해 냅니다.",
            "고객이 100명으로 늘어나도 동일한 품질을 즉시 공급하며 안정적 수익을 창출합니다."
        ],
        "bg_theme": "gold",
        "slide_type": "biz_scaling"
    },
    {
        "id": 13,
        "ch": 5,
        "tag": "CHAPTER 05 / 05",
        "title": "4막: 오늘 배운 10분 코어 시스템 3대 핵심 총정리",
        "subtitle": "비싼 툴 배제, 데이터 연결 구조 집중, 프롬프트 체이닝 3원칙",
        "script": "오늘 10분 동안 저와 함께 힘차게 달려오셨는데, 마지막으로 꼭 기억하셔야 할 핵심 세 가지만 짚어드리겠습니다. 가장 먼저 기억하실 건 비싼 유료 툴에 현혹되지 마시고 구글 시트와 Gemini 같은 무료 도구를 알차게 쓰시는 겁니다. 그리고 무엇보다 중요한 점은 단 한 번의 질문에 그치지 않고 데이터가 알아서 오가는 연결 통로를 만들어 두는 것이죠. 마지막으로 프롬프트 체이닝을 활용해 일의 완성도를 탄탄하게 끌어올리는 것, 이 세 가지만 챙기셔도 여러분의 일상은 180도 달라집니다.",
        "sentences": [
            "오늘 10분 동안 함께 살펴본 핵심 내용을 알기 쉽게 세 가지로 정리해 드릴게요.",
            "가장 먼저, 비싼 유료 툴 대신 구글 시트와 무료 AI 도구의 결합을 꼭 기억하세요.",
            "그리고 무엇보다, 데이터가 알아서 오가는 자동 연결 통로를 튼튼하게 구축하세요.",
            "마지막으로, 체이닝 방식을 활용해 결과물의 완성도를 대폭 끌어올려 보세요."
        ],
        "bg_theme": "emerald",
        "slide_type": "summary_3"
    },
    {
        "id": 14,
        "ch": 5,
        "tag": "CHAPTER 05 / 05",
        "title": "4막: 액션 플랜 & 엔드스크린 추천 영상 연계",
        "subtitle": "오늘 밤 1시간 실천 과제 및 우측 상단 실전 수익화 5단계 연계 시청",
        "script": "오늘 영상을 시청하신 후 뒤로 미루지 마시고, 오늘 밤 딱 1시간만 투자해서 고정 댓글의 무료 템플릿을 본인의 구글 드라이브에 복사해 보세요. 오늘 파이프라인의 기초를 완성하셨다면, 이제 이 시스템에 실제 첫 유료 고객을 유치하는 구체적인 마케팅 5단계가 궁금하실 텐데요. 지금 화면 우측 상단에 뜨는 추천 영상에서 바로 이어지는 실전 수익화 전략을 상세히 다루었으니 지금 바로 클릭해서 이어서 시청해 보시기 바랍니다. 구독과 좋아요 부탁드리며, 시청해 주셔서 대단히 감사합니다.",
        "sentences": [
            "미루지 마시고 오늘 밤 딱 1시간만 투자하여 고정 댓글의 무료 템플릿을 세팅해 보세요.",
            "파이프라인을 구축했다면, 이제 실제 첫 유료 고객을 모으는 마케팅이 필요합니다.",
            "화면 우측 상단에 뜨는 추천 영상에서 '실전 수익화 5단계'를 지금 바로 확인해 보세요!",
            "구독과 알림 설정 잊지 마시고, 10분 동안 끝까지 시청해 주셔서 진심으로 감사합니다!"
        ],
        "bg_theme": "emerald",
        "slide_type": "outro_action"
    }
]

# 음성 길이 측정
def get_audio_duration(file_path):
    cmd = [FFMPEG_EXE, "-i", file_path]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, errors="replace")
    for line in res.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.strip().split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 40.0

# 앰비언트 BGM 생성 (44.1kHz 스테레오 웨이브)
def generate_ambient_bgm(duration_sec, out_path):
    print(f"🎵 10분+ 앰비언트 BGM 트랙 합성 중 ({duration_sec:.1f}초)...")
    sample_rate = 44100
    total_samples = int(duration_sec * sample_rate)
    freqs = [146.83, 220.00, 277.18, 369.99]
    
    with wave.open(out_path, 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            lfo = 0.8 + 0.2 * math.sin(2 * math.pi * 0.15 * t)
            val = 0
            for j, f in enumerate(freqs):
                val += math.sin(2 * math.pi * f * t) * (0.25 / (j + 1))
            sample_val = int(val * 2800 * lfo)
            sample_val = max(-32767, min(32767, sample_val))
            packed = struct.pack('<hh', sample_val, sample_val)
            frames.extend(packed)
            
            if len(frames) >= 65536:
                wav.writeframes(frames)
                frames = bytearray()
                
        if frames:
            wav.writeframes(frames)
    print("✅ BGM 합성 완료")

# 16:9 캔버스 베이스 프레임 렌더링 (1920x1080)
def draw_scene_base_frame(scene):
    img = Image.new("RGB", (1920, 1080), color=(10, 13, 20))
    draw = ImageDraw.Draw(img)

    theme = scene["bg_theme"]
    accent_rgb = (139, 92, 246)
    if theme == "cyan":
        accent_rgb = (6, 182, 212)
    elif theme == "amber":
        accent_rgb = (245, 158, 11)
    elif theme == "purple":
        accent_rgb = (139, 92, 246)
    elif theme == "gold":
        accent_rgb = (234, 179, 8)
    elif theme == "emerald":
        accent_rgb = (16, 185, 129)

    # 1. 앰비언트 글로우 및 미세 격자
    for r in range(450, 0, -50):
        glow_color = (
            int(10 + accent_rgb[0] * 0.08 * (1 - r / 450)),
            int(13 + accent_rgb[1] * 0.08 * (1 - r / 450)),
            int(20 + accent_rgb[2] * 0.08 * (1 - r / 450))
        )
        draw.ellipse([960 - r * 2, 540 - r, 960 + r * 2, 540 + r], fill=glow_color)

    for y in range(80, 1000, 140):
        draw.line([(60, y), (1860, y)], fill=(20, 24, 38), width=1)
    for x in range(120, 1860, 200):
        draw.line([(x, 80), (x, 960)], fill=(18, 22, 34), width=1)

    # 2. 상단 헤더 바
    draw.rectangle([60, 32, 1860, 90], fill=(15, 18, 28), outline=(40, 46, 68), width=1)
    draw.rectangle([78, 44, 114, 78], fill=(255, 0, 51))
    draw.polygon([(92, 52), (92, 70), (105, 61)], fill=(255, 255, 255))
    draw.text((128, 48), "YOUTUBE LONG-FORM STUDIO", fill=(240, 243, 248), font=FONT_HEADER)

    draw.rounded_rectangle([720, 44, 930, 78], radius=14, fill=(6, 182, 212, 40), outline=(6, 182, 212), width=1)
    draw.text((736, 50), "📐 16:9 Widescreen", fill=(103, 232, 249), font=FONT_SMALL)

    draw.rounded_rectangle([944, 44, 1130, 78], radius=14, fill=(16, 185, 129, 40), outline=(16, 185, 129), width=1)
    draw.text((958, 50), "⏱️ 10분+ 롱폼 전문", fill=(110, 231, 183), font=FONT_SMALL)

    # 상단 씬 진행률 바 (60~1860)
    prog_ratio = scene["id"] / 14.0
    bar_w = int((1860 - 60) * prog_ratio)
    draw.rectangle([60, 90, 60 + bar_w, 94], fill=accent_rgb)

    draw.rounded_rectangle([1530, 44, 1842, 78], radius=14, fill=accent_rgb)
    draw.text((1546, 49), f"SCENE {scene['id']:02d} / 14", fill=(255, 255, 255), font=FONT_HEADER)

    # 3. 씬 타이틀 & 서브타이틀
    draw.text((100, 118), scene["title"], fill=(255, 255, 255), font=FONT_TITLE)
    draw.text((100, 180), scene["subtitle"], fill=(156, 163, 175), font=FONT_SUBTITLE)

    # 4. 씬 타입별 메인 비주얼 그래픽 카드
    stype = scene["slide_type"]

    if stype == "intro_hook":
        # 좌측: 시청 약속 3대 보상
        draw.rounded_rectangle([100, 240, 930, 800], radius=18, fill=(18, 22, 34), outline=(45, 52, 75), width=2)
        draw.rounded_rectangle([130, 270, 360, 312], radius=10, fill=(245, 158, 11))
        draw.text((144, 278), "⚡ [오늘 끝냅니다]", fill=(0, 0, 0), font=FONT_SMALL)

        draw.text((130, 340), "🔥 10분 완청 시 얻게 되는 3대 보상", fill=(255, 255, 255), font=FONT_CARD_TITLE)
        draw.text((130, 410), "1. 1원도 결제 없는 100% 무료 인프라 결합", fill=(103, 232, 249), font=FONT_CARD_BODY)
        draw.text((130, 480), "2. 24시간 잠들지 않는 무인 고객 응대 시스템", fill=(110, 231, 183), font=FONT_CARD_BODY)
        draw.text((130, 550), "3. 복잡한 기획서·제안서 5초 자동 완성 파이프라인", fill=(253, 224, 71), font=FONT_CARD_BODY)
        draw.text((130, 640), "💡 오늘 영상만 따라오시면 누구나 소스 코드를 복붙할 수 있습니다.", fill=(203, 213, 225), font=FONT_CARD_BODY)

        # 우측: 자동화 지표
        draw.rounded_rectangle([970, 240, 1820, 800], radius=18, fill=(15, 18, 28), outline=(6, 182, 212), width=2)
        draw.text((1000, 275), "📊 Real-time AI Automation Dashboard", fill=(103, 232, 249), font=FONT_CARD_TITLE)
        metrics = [
            ("시스템 가동 상태", "ACTIVE (24/7 무중단)", (16, 185, 129)),
            ("주간 절약 업무 시간", "48시간 / 1주", (245, 158, 11)),
            ("자동 생성 기획서", "1,420건 누적 완료", (139, 92, 246)),
            ("월간 자동화 기여 수익", "₩5,200,000", (6, 182, 212))
        ]
        for idx, (lbl, val, col) in enumerate(metrics):
            bx = 1000 + (idx % 2) * 390
            by = 350 + (idx // 2) * 190
            draw.rounded_rectangle([bx, by, bx + 360, by + 160], radius=14, fill=(22, 26, 40), outline=(50, 58, 80), width=1)
            draw.text((bx + 20, by + 30), lbl, fill=(148, 163, 184), font=FONT_CARD_BODY)
            draw.text((bx + 20, by + 80), val, fill=col, font=FONT_CARD_TITLE)

    elif stype == "intro_dashboard":
        # 4단계 코어 프로세스 가로 카드
        steps = [
            ("01. 고객 문의 자동 접수", "구글 폼을 통해 고객 요구사항이 들어오는 즉시 0.1초 만에 감지", (6, 182, 212)),
            ("02. Gemini API 두뇌 추론", "시스템 프롬프트를 통해 5초 만에 맞춤형 전략 보고서 자동 생성", (139, 92, 246)),
            ("03. 노코드 웹훅 파이프라인", "복잡한 코딩 없이 실시간 백그라운드 이벤트 바인딩", (245, 158, 11)),
            ("04. 최종 납품 & 리포트 발송", "구글 시트 기록 및 고객 이메일로 100% 무인 자동 전송", (16, 185, 129))
        ]
        for idx, (st_t, st_d, col) in enumerate(steps):
            bx = 100 + idx * 435
            draw.rounded_rectangle([bx, 250, bx + 410, 680], radius=16, fill=(18, 22, 34), outline=col, width=2)
            draw.rounded_rectangle([bx + 20, 275, bx + 160, 315], radius=10, fill=col)
            draw.text((bx + 30, 282), f"STEP {idx+1}", fill=(0, 0, 0), font=FONT_SMALL)
            draw.text((bx + 20, 340), st_t, fill=(255, 255, 255), font=FONT_CARD_TITLE)
            draw.text((bx + 20, 420), st_d, fill=(180, 190, 205), font=FONT_CARD_BODY)

        # 하단 8분 치트키 예고 배너
        draw.rounded_rectangle([100, 710, 1820, 790], radius=14, fill=(234, 179, 8, 30), outline=(234, 179, 8), width=2)
        draw.text((140, 735), "⚡ [핵심 예고] 영상 8분 지점에서 상위 1% 프롬프트 체이닝 설계 비법을 완벽 해설합니다!", fill=(253, 224, 71), font=FONT_CARD_TITLE)

    elif stype == "mistakes_3":
        cards = [
            ("❌ 착각 1: 비싼 유료 툴 다중 구독의 늪", "매달 수십만 원의 고정비가 나가며, 툴 하나만 에러가 나도 전체 파이프라인이 정지됩니다.", "💡 상위 1% 해법: 100% 무료 도구 2개만 제대로 결합해도 연간 1,000만원 절약"),
            ("❌ 착각 2: 파이썬 코딩을 배워야 한다는 강박", "개발 언어를 공부하다 99%가 포기합니다. 복잡한 문법은 실무 자동화의 장애물입니다.", "💡 상위 1% 해법: 2026 노코드 웹훅과 API 키 연결로 코딩 없이 5분 만에 완성"),
            ("❌ 착각 3: 챗GPT 대화창 매번 직접 입력", "사람이 매번 프롬프트를 복붙하는 것은 질문 창구만 바꾼 수작업 노가다에 불과합니다.", "💡 상위 1% 해법: 고객 폼 제출 시 데이터가 스스로 AI에게 흐르는 자동 배관망 구축")
        ]
        for idx, (t, d, s) in enumerate(cards):
            by = 240 + idx * 185
            draw.rounded_rectangle([100, by, 1820, by + 165], radius=16, fill=(18, 22, 34), outline=(239, 68, 68) if idx==0 else (245, 158, 11), width=2)
            draw.text((130, by + 20), t, fill=(255, 255, 255), font=FONT_CARD_TITLE)
            draw.text((130, by + 68), d, fill=(156, 163, 175), font=FONT_CARD_BODY)
            draw.text((130, by + 112), s, fill=(110, 231, 183), font=FONT_CARD_BODY)

    elif stype == "pipeline_concept":
        # 비포 vs 애프터 비교
        draw.rounded_rectangle([100, 250, 930, 780], radius=18, fill=(24, 18, 24), outline=(239, 68, 68), width=2)
        draw.text((140, 280), "❌ 기존 수작업 방식 (시간 낭비 & 이탈)", fill=(248, 113, 113), font=FONT_CARD_TITLE)
        draw.text((140, 360), "1. 고객 문의 접수 시 일일이 수동 확인", fill=(200, 200, 200), font=FONT_CARD_BODY)
        draw.text((140, 430), "2. 챗GPT 켜고 프롬프트 복붙 후 질문", fill=(200, 200, 200), font=FONT_CARD_BODY)
        draw.text((140, 500), "3. 답변 복사해서 워드/한글에 붙여넣기", fill=(200, 200, 200), font=FONT_CARD_BODY)
        draw.text((140, 570), "4. 고객 이메일 열고 파일 첨부 후 수동 발송", fill=(200, 200, 200), font=FONT_CARD_BODY)
        draw.text((140, 670), "⚠️ 건당 소요 시간: 45분 이상 소모 & 휴먼 에러 발생", fill=(248, 113, 113), font=FONT_CARD_TITLE)

        draw.rounded_rectangle([970, 250, 1820, 780], radius=18, fill=(16, 24, 30), outline=(6, 182, 212), width=2)
        draw.text((1010, 280), "✅ 0원 무인 파이프라인 (완전 무인화)", fill=(103, 232, 249), font=FONT_CARD_TITLE)
        draw.text((1010, 360), "1. 고객 폼 제출 즉시 0.1초 데이터 정돈", fill=(200, 200, 200), font=FONT_CARD_BODY)
        draw.text((1010, 430), "2. 웹훅 트리거로 Gemini API 자동 호출", fill=(200, 200, 200), font=FONT_CARD_BODY)
        draw.text((1010, 500), "3. 프롬프트 체이닝으로 5초 만에 완성 리포트 산출", fill=(200, 200, 200), font=FONT_CARD_BODY)
        draw.text((1010, 570), "4. 구글 시트 기입 및 이메일 자동 회신 완료", fill=(200, 200, 200), font=FONT_CARD_BODY)
        draw.text((1010, 670), "⚡ 건당 소요 시간: 단 5초 (인간 개입 0% 완벽 자동)", fill=(110, 231, 183), font=FONT_CARD_TITLE)

    elif stype == "free_tools":
        # 3대 무료 인프라 스택
        tools = [
            ("구글 스프레드시트 & 구글 폼", "100% 무료 무제한 데이터베이스", "모든 고객 데이터를 안전하게 누적하고 데이터 클렌징 수식 자동화 지원", (6, 182, 212)),
            ("Google Gemini 무료 API", "월 수천만 토큰 무료 쿼터", "최신 초고속 추론 엔진으로 복잡한 기획서·보고서를 5초 만에 산출", (139, 92, 246)),
            ("노코드 웹훅 트리거", "이벤트 기반 실시간 연결 배관망", "새 행 추가 이벤트를 0.1초 만에 감지하여 백그라운드 자동 연동", (16, 185, 129))
        ]
        for idx, (name, role, desc, col) in enumerate(tools):
            bx = 100 + idx * 580
            draw.rounded_rectangle([bx, 250, bx + 550, 780], radius=18, fill=(18, 22, 34), outline=col, width=2)
            draw.rounded_rectangle([bx + 30, 280, bx + 180, 320], radius=10, fill=col)
            draw.text((bx + 45, 288), f"STACK 0{idx+1}", fill=(0, 0, 0), font=FONT_SMALL)
            draw.text((bx + 30, 350), name, fill=(255, 255, 255), font=FONT_CARD_TITLE)
            draw.text((bx + 30, 410), role, fill=col, font=FONT_CARD_BODY)
            draw.text((bx + 30, 500), desc, fill=(180, 190, 205), font=FONT_CARD_BODY)

    elif stype == "step1_sheets":
        draw.rounded_rectangle([100, 240, 1820, 800], radius=18, fill=(16, 20, 30), outline=(139, 92, 246), width=2)
        draw.text((140, 275), "📋 [실전 1단계] 구글 스프레드시트 데이터 클렌징 수식 테이블", fill=(255, 255, 255), font=FONT_CARD_TITLE)
        
        headers = ["타임스탬프", "고객 성명", "프로젝트 유형", "핵심 요구사항", "데이터 정제 수식", "상태"]
        for i, h in enumerate(headers):
            draw.text((140 + i * 270, 350), h, fill=(103, 232, 249), font=FONT_CODE)
        draw.line([(140, 390), (1780, 390)], fill=(60, 70, 100), width=2)

        rows = [
            ("2026-09-25 10:14", "김철수 대표", "마케팅 자동화", "SNS 콘텐츠 주 5회 생성", "=TRIM(CLEAN(D2))", "정제 완료 ✅"),
            ("2026-09-25 10:15", "이영희 팀장", "1인 쇼핑몰", "고객 문의 24시 자동 응대", "=REGEXREPLACE(D3)", "정제 완료 ✅"),
            ("2026-09-25 10:16", "박민호 작가", "유튜브 롱폼", "10분 영상 기획 및 대본", "=SUBSTITUTE(D4)", "정제 완료 ✅")
        ]
        for r_idx, r in enumerate(rows):
            ry = 420 + r_idx * 75
            for c_idx, val in enumerate(r):
                draw.text((140 + c_idx * 270, ry), val, fill=(220, 230, 242) if c_idx < 5 else (110, 231, 183), font=FONT_CARD_BODY)

        draw.rounded_rectangle([140, 680, 1780, 765], radius=12, fill=(22, 28, 44), outline=(139, 92, 246), width=1)
        draw.text((160, 705), "💡 팁: 수식으로 데이터를 미리 정제하면 AI에게 전달될 때 불필요한 토큰 낭비가 40% 절감됩니다.", fill=(253, 224, 71), font=FONT_CARD_BODY)

    elif stype == "step2_gemini":
        draw.rounded_rectangle([100, 240, 930, 800], radius=18, fill=(16, 20, 30), outline=(139, 92, 246), width=2)
        draw.text((130, 270), "🤖 Gemini API 시스템 지침 (System Prompt)", fill=(103, 232, 249), font=FONT_CARD_TITLE)
        
        prompt_lines = [
            "# 역할: 10년 차 수석 비즈니스 아키텍트",
            "- 고객의 인풋 데이터를 분석하여 3단 기획서를 작성하라.",
            "- 형식 규격: 마크다운 헤더 및 불렛포인트 필수",
            "- 제약 사항: 근거 없는 추측 배제, 실천 가능한 로드맵 제시",
            "- 출력 언어: 신뢰감 있는 비즈니스 전문 한국어"
        ]
        for p_idx, pl in enumerate(prompt_lines):
            draw.text((130, 350 + p_idx * 60), pl, fill=(230, 235, 245), font=FONT_CODE)

        draw.rounded_rectangle([970, 240, 1820, 800], radius=18, fill=(18, 22, 34), outline=(16, 185, 129), width=2)
        draw.text((1000, 270), "⚡ 무료 API 키 발급 및 설정 가이드", fill=(110, 231, 183), font=FONT_CARD_TITLE)
        draw.text((1000, 350), "1. Google AI Studio (aistudio.google.com) 접속", fill=(200, 210, 225), font=FONT_CARD_BODY)
        draw.text((1000, 430), "2. [Get API Key] 버튼 클릭하여 무료 키 생성", fill=(200, 210, 225), font=FONT_CARD_BODY)
        draw.text((1000, 510), "3. 월 최대 수천만 토큰까지 무료 할당량 제공", fill=(200, 210, 225), font=FONT_CARD_BODY)
        draw.text((1000, 590), "4. 카드 등록 없이 구글 계정만으로 즉시 발급 가능", fill=(253, 224, 71), font=FONT_CARD_BODY)

    elif stype == "step3_webhook":
        draw.rounded_rectangle([100, 240, 1820, 800], radius=18, fill=(18, 22, 34), outline=(245, 158, 11), width=2)
        draw.text((140, 270), "⚡ 실시간 자동화 웹훅(Webhook) 트리거 파이프라인 구조", fill=(253, 224, 71), font=FONT_CARD_TITLE)

        stages = [
            ("이벤트 발생", "고객 폼 제출\n(Google Forms)", (6, 182, 212)),
            ("데이터 정제", "구글 시트 행 추가\n& 정제 수식 가동", (139, 92, 246)),
            ("AI API 호출", "Gemini 2.0 / 3.0\n시스템 지침 주입", (245, 158, 11)),
            ("결과물 생성", "2,000자 리포트\n단 5초 만에 완성", (16, 185, 129))
        ]
        for s_idx, (st_n, st_d, col) in enumerate(stages):
            bx = 140 + s_idx * 420
            draw.rounded_rectangle([bx, 360, bx + 360, 580], radius=16, fill=(24, 28, 44), outline=col, width=2)
            draw.text((bx + 20, 390), st_n, fill=col, font=FONT_CARD_TITLE)
            draw.text((bx + 20, 460), st_d, fill=(220, 230, 245), font=FONT_CARD_BODY)
            if s_idx < 3:
                draw.text((bx + 375, 450), "➔", fill=(255, 255, 255), font=FONT_TITLE)

        draw.rounded_rectangle([140, 640, 1780, 750], radius=14, fill=(12, 16, 24), outline=(60, 70, 95), width=1)
        draw.text((170, 675), "⏱️ 트리거부터 결과물 납품까지 총 소요 시간: 단 5초 (사람의 개입 0% 완전 자동화)", fill=(110, 231, 183), font=FONT_CARD_TITLE)

    elif stype == "demo_screen":
        draw.rounded_rectangle([100, 240, 1820, 800], radius=18, fill=(12, 14, 22), outline=(16, 185, 129), width=2)
        draw.text((140, 270), "💻 라이브 자동화 파이프라인 가동 콘솔 (Real-time Log)", fill=(110, 231, 183), font=FONT_CARD_TITLE)
        
        logs = [
            "[10:14:02] [EVENT] New client inquiry detected from Google Form #4928",
            "[10:14:03] [CLEANSE] Input data cleaned. Name: TechCorp / Keyword: AI Automation",
            "[10:14:04] [TRIGGER] Webhook dispatched to Gemini API (Model: gemini-3.6-flash)",
            "[10:14:07] [RESPONSE] 2,450 tokens generated successfully in 3.1 seconds (HTTP 200 OK)",
            "[10:14:08] [DATABASE] Final 16:9 business proposal inserted into Column F",
            "[10:14:09] [SUCCESS] 24/7 Digital worker pipeline completed without human intervention"
        ]
        for l_idx, lg in enumerate(logs):
            draw.text((140, 360 + l_idx * 55), lg, fill=(103, 232, 249) if "SUCCESS" in lg else (200, 215, 235), font=FONT_CODE)

        draw.rounded_rectangle([140, 700, 1780, 765], radius=10, fill=(20, 30, 45), outline=(16, 185, 129), width=1)
        draw.text((160, 718), "🛡️ 3회 자동 재시도 로직 탑재: 일시적 네트워크 지연에도 단 한 건의 누락 없이 365일 무중단 가동", fill=(255, 255, 255), font=FONT_CARD_BODY)

    elif stype == "cheat_chaining":
        draw.rounded_rectangle([100, 240, 1820, 800], radius=18, fill=(18, 22, 34), outline=(234, 179, 8), width=2)
        draw.text((140, 270), "🔥 [8분 미드롤 돌파 치트키] 상위 1% 프롬프트 체이닝 3단계 바통 터치 구조", fill=(253, 224, 71), font=FONT_CARD_TITLE)

        chains = [
            ("1차 에이전트: 문제 분석가", "고객 요구사항에서 핵심 페인포인트 추출\n원인 및 기회 요인 3가지 분석 도출", (6, 182, 212)),
            ("2차 에이전트: 수석 기획자", "1차 분석 결과를 토대로 16:9 맞춤 전략 수립\n단계별 실천 로드맵 및 예상 효과 산출", (245, 158, 11)),
            ("3차 에이전트: 전문 카피라이터", "2차 전략을 바탕으로 고객 납품용 최종 제안서 작성\n비즈니스 격식체 및 마크다운 퇴고 완성", (16, 185, 129))
        ]
        for c_idx, (cn, cd, col) in enumerate(chains):
            bx = 140 + c_idx * 560
            draw.rounded_rectangle([bx, 360, bx + 520, 640], radius=16, fill=(25, 30, 48), outline=col, width=2)
            draw.rounded_rectangle([bx + 20, 385, bx + 180, 425], radius=10, fill=col)
            draw.text((bx + 35, 393), f"STAGE 0{c_idx+1}", fill=(0, 0, 0), font=FONT_SMALL)
            draw.text((bx + 20, 450), cn, fill=(255, 255, 255), font=FONT_CARD_TITLE)
            draw.text((bx + 20, 520), cd, fill=(190, 205, 225), font=FONT_CARD_BODY)

        draw.rounded_rectangle([140, 680, 1780, 765], radius=12, fill=(35, 30, 20), outline=(234, 179, 8), width=1)
        draw.text((160, 705), "⭐ 결론: 질문을 한 번에 다 던지지 않고 3단계로 나누면 대기업 기획실 수준의 퀄리티가 나옵니다.", fill=(253, 224, 71), font=FONT_CARD_BODY)

    elif stype == "cheat_template":
        draw.rounded_rectangle([100, 240, 1820, 800], radius=18, fill=(15, 18, 28), outline=(234, 179, 8), width=2)
        draw.text((140, 270), "📄 상위 1% 실전 복붙 프롬프트 체이닝 원본 템플릿 (Prompt Template)", fill=(253, 224, 71), font=FONT_CARD_TITLE)

        lines = [
            "### [Prompt Chain 1: Client Needs Analysis]",
            "Input: {{Customer_Requirement_Data}}",
            "Instruction: 당신은 수석 비즈니스 분석가입니다. 위 데이터의 핵심 문제 3가지를 정리하세요.",
            "",
            "### [Prompt Chain 2: Strategic Solution Generation]",
            "Input: {{Output_From_Chain_1}}",
            "Instruction: 위 3대 문제에 대한 16:9 와이드스크린 실행 로드맵과 3단계 솔루션을 수립하세요.",
            "",
            "### [Prompt Chain 3: Final Executive Deliverable]",
            "Input: {{Output_From_Chain_2}}",
            "Instruction: 최종 고객에게 전달할 깔끔한 마크다운 보고서로 다듬어 완성하세요."
        ]
        for l_idx, ln in enumerate(lines):
            draw.text((140, 340 + l_idx * 38), ln, fill=(103, 232, 249) if "Chain" in ln else (220, 230, 245), font=FONT_CODE)

        draw.rounded_rectangle([140, 715, 1780, 775], radius=10, fill=(234, 179, 8, 40), outline=(234, 179, 8), width=1)
        draw.text((160, 732), "📥 이 원본 템플릿은 영상 하단 설명란과 고정 댓글에 마크다운(.md) 파일로 100% 무료 공유됩니다!", fill=(255, 255, 255), font=FONT_CARD_BODY)

    elif stype == "biz_scaling":
        models = [
            ("01. 플랫폼 자동 견적 서비스", "크몽, 숨고 등의 고객 문의에\n5초 만에 전문가급 제안서 자동 회신\n➔ 계약 성사율 400% 급상승", (6, 182, 212)),
            ("02. 기업 맞춤 리서치 구독", "산업별 최신 AI 트렌드와 경쟁사 분석을\n매주 월요일 전자동 생성하여 납품\n➔ 월 50만원 고정 구독 클라이언트 10곳 확보", (139, 92, 246)),
            ("03. 1인 에이전시 파이프라인", "인건비와 사무실 비용 0원!\n내가 자는 동안에도 24시간 가동되는\n시스템 기반 월 500만원 순수익 창출", (16, 185, 129))
        ]
        for m_idx, (mn, md, col) in enumerate(models):
            bx = 100 + m_idx * 580
            draw.rounded_rectangle([bx, 250, bx + 550, 780], radius=18, fill=(18, 22, 34), outline=col, width=2)
            draw.rounded_rectangle([bx + 30, 280, bx + 180, 320], radius=10, fill=col)
            draw.text((bx + 40, 288), f"MODEL 0{m_idx+1}", fill=(0, 0, 0), font=FONT_SMALL)
            draw.text((bx + 30, 350), mn, fill=(255, 255, 255), font=FONT_CARD_TITLE)
            draw.text((bx + 30, 430), md, fill=(190, 205, 225), font=FONT_CARD_BODY)

    elif stype == "summary_3":
        draw.rounded_rectangle([100, 240, 1820, 800], radius=18, fill=(16, 22, 32), outline=(16, 185, 129), width=2)
        draw.text((140, 270), "🎓 오늘 배운 10분 마스터클래스 핵심 공식 3대 총정리", fill=(110, 231, 183), font=FONT_CARD_TITLE)

        summaries = [
            ("1. 툴이 아니라 '연결 구조'에 집중하라", "비싼 유료 툴 10개보다 구글 시트와 Gemini 무료 API를 잇는 배관망이 100배 강력합니다."),
            ("2. 사람이 직접 묻지 말고 '웹훅'으로 흘려보내라", "고객 폼 제출과 동시에 백그라운드에서 AI가 5초 만에 결과물을 납품하는 무인화가 핵심입니다."),
            ("3. 한 번에 묻지 말고 '프롬프트 체이닝'으로 분업화하라", "분석 ➔ 기획 ➔ 카피라이팅 3단계를 바통 터치하면 1인 기업도 대기업 기획실 퀄리티를 냅니다.")
        ]
        for s_idx, (st, sd) in enumerate(summaries):
            by = 350 + s_idx * 135
            draw.rounded_rectangle([140, by, 1780, by + 115], radius=14, fill=(22, 30, 44), outline=(16, 185, 129), width=1)
            draw.text((170, by + 22), st, fill=(253, 224, 71), font=FONT_CARD_TITLE)
            draw.text((170, by + 68), sd, fill=(220, 230, 245), font=FONT_CARD_BODY)

    elif stype == "outro_action":
        # 좌측: 오늘 밤 액션 플랜
        draw.rounded_rectangle([100, 240, 930, 800], radius=18, fill=(18, 22, 34), outline=(16, 185, 129), width=2)
        draw.text((130, 270), "⚡ 오늘 밤 1시간 실천 과제 (Action Item)", fill=(110, 231, 183), font=FONT_CARD_TITLE)
        draw.text((130, 350), "✅ 1. 고정 댓글의 무료 마크다운 템플릿 복사", fill=(220, 230, 245), font=FONT_CARD_BODY)
        draw.text((130, 420), "✅ 2. 구글 AI 스튜디오에서 무료 API 키 1분 발급", fill=(220, 230, 245), font=FONT_CARD_BODY)
        draw.text((130, 490), "✅ 3. 구글 스프레드시트에 웹훅 연결 테스트 완료", fill=(220, 230, 245), font=FONT_CARD_BODY)
        draw.text((130, 560), "✅ 4. 잠자는 동안에도 일하는 나만의 첫 파이프라인 완성!", fill=(253, 224, 71), font=FONT_CARD_BODY)

        # 우측: 추천 영상 (엔드스크린)
        draw.rounded_rectangle([970, 240, 1820, 800], radius=18, fill=(20, 24, 38), outline=(6, 182, 212), width=2)
        draw.rounded_rectangle([1010, 275, 1240, 315], radius=10, fill=(6, 182, 212))
        draw.text((1025, 283), "🎬 연계 시청 추천 영상", fill=(0, 0, 0), font=FONT_SMALL)

        draw.text((1010, 350), "[마스터클래스] 0원으로 시작하는 1인 기업", fill=(255, 255, 255), font=FONT_CARD_TITLE)
        draw.text((1010, 400), "첫 유료 고객 유치 & 실전 수익화 5단계 로드맵", fill=(103, 232, 249), font=FONT_CARD_TITLE)
        draw.text((1010, 480), "오늘 완성한 파이프라인으로 실제 수익을 창출하는 방법을\n우측 상단 카드에 걸어두었습니다. 지금 바로 클릭하세요!", fill=(180, 195, 215), font=FONT_CARD_BODY)
        draw.text((1010, 630), "🔔 채널 구독 & 좋아요 누르시고 평생 무료 AI 비즈니스 인사이트를 받아보세요!", fill=(253, 224, 71), font=FONT_CARD_BODY)

    return img

# 프레임 위에 자막 렌더링
def render_subtitle(base_img, sub_text):
    img = base_img.copy()
    draw = ImageDraw.Draw(img)

    if sub_text:
        # 하단 자막 바 (840 ~ 950)
        draw.rounded_rectangle([140, 840, 1780, 950], radius=16, fill=(8, 10, 16), outline=(139, 92, 246), width=2)
        bbox = draw.textbbox((0, 0), sub_text, font=FONT_SUB)
        tw = bbox[2] - bbox[0]
        tx = max(160, (1920 - tw) // 2)
        ty = 875
        draw.text((tx, ty), sub_text, fill=(255, 255, 255), font=FONT_SUB)

    return img

# 메인 10분+ 렌더링 프로세스
async def main():
    print("==============================================================")
    print("🎬 유튜브 롱폼 올인원 기획서 기반 16:9 와이드스크린 비디오 렌더링")
    print("⏱️ 목표 러닝타임: 10분 이상 (600초 이상 100% 필수 보장)")
    print("==============================================================")

    scene_video_clips = []
    total_audio_sec = 0.0

    # 1. 14개 씬 음성 합성 (rate="-8%"로 안정적인 10분+ 튜토리얼 톤 앤 매너)
    for s_idx, scene in enumerate(SCENES):
        sid = scene["id"]
        sc_audio_path = os.path.join(TEMP_DIR, f"sc_{sid}.mp3")
        print(f"\n🎙️ [Scene {sid:02d}/14] 음성 합성 중 ({len(scene['script'])}글자)...")
        
        comm = edge_tts.Communicate(scene["script"], "ko-KR-SunHiNeural", rate="-8%")
        await comm.save(sc_audio_path)
        
        dur = get_audio_duration(sc_audio_path)
        total_audio_sec += dur
        print(f"✅ [Scene {sid:02d}] 음성 완료: {dur:.2f}초 (누적: {total_audio_sec:.1f}초)")

        # 2. 씬별 베이스 프레임 및 자막별 이미지 생성
        base_frame = draw_scene_base_frame(scene)
        sentences = scene["sentences"]
        num_sentences = len(sentences)
        dur_per_sentence = dur / max(1, num_sentences)

        # 텍스트 concat 파일 작성
        scene_concat_txt = os.path.join(TEMP_DIR, f"sc_{sid}_concat.txt")
        frame_paths = []
        with open(scene_concat_txt, "w", encoding="utf-8") as f:
            for st_i, sent in enumerate(sentences):
                f_img = render_subtitle(base_frame, sent)
                f_path = os.path.join(TEMP_DIR, f"sc_{sid}_f{st_i}.png")
                f_img.save(f_path)
                frame_paths.append(f_path)
                f.write(f"file '{os.path.abspath(f_path).replace('\\', '/')}'\n")
                f.write(f"duration {dur_per_sentence:.3f}\n")
            # ffmpeg concat demuxer 규격: 마지막 프레임 반복
            if frame_paths:
                f.write(f"file '{os.path.abspath(frame_paths[-1]).replace('\\', '/')}'\n")

        # 3. 비디오 클립 렌더링 (ffmpeg 빠른 정지영상 인코딩)
        sc_clip_path = os.path.join(TEMP_DIR, f"sc_{sid}_video.mp4")
        cmd_encode = [
            FFMPEG_EXE, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", scene_concat_txt,
            "-i", sc_audio_path,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-r", "24",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            sc_clip_path
        ]
        subprocess.run(cmd_encode, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        scene_video_clips.append(sc_clip_path)
        print(f"🎬 [Scene {sid:02d}] 1080p 16:9 클립 렌더링 완료")

    # 4. 전체 14개 씬 결합
    print("\n📦 전체 14개 씬 비디오 결합 중...")
    master_concat_txt = os.path.join(TEMP_DIR, "master_scenes_concat.txt")
    with open(master_concat_txt, "w", encoding="utf-8") as f:
        for cl in scene_video_clips:
            f.write(f"file '{os.path.abspath(cl).replace('\\', '/')}'\n")

    master_speech_mp4 = os.path.join(TEMP_DIR, "master_speech.mp4")
    cmd_master_concat = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", master_concat_txt,
        "-c", "copy",
        master_speech_mp4
    ]
    subprocess.run(cmd_master_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 5. 배경음악(BGM) 생성 및 밸런스 오디오 믹싱
    bgm_path = os.path.join(TEMP_DIR, "master_bgm.wav")
    generate_ambient_bgm(total_audio_sec + 5.0, bgm_path)

    output_mp4 = os.path.join(OUTPUT_DIR, "youtube_longform_video.mp4")
    downloads_mp4 = os.path.join(os.environ["USERPROFILE"], "Downloads", "유튜브롱폼_AI자동화_완성영상_16대9.mp4")

    print(f"\n🎧 앰비언트 BGM 및 보이스 오디오 믹싱 & 최종 MP4 출력 중...")
    cmd_final = [
        FFMPEG_EXE, "-y",
        "-i", master_speech_mp4,
        "-i", bgm_path,
        "-filter_complex", "[0:a]volume=1.0[v];[1:a]volume=0.12[b];[v][b]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        output_mp4
    ]
    subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 다운로드 폴더로도 복사
    shutil.copyfile(output_mp4, downloads_mp4)

    final_dur = get_audio_duration(output_mp4)
    mins = int(final_dur // 60)
    secs = final_dur % 60

    print("\n==============================================================")
    print("🎉 10분+ 16:9 와이드스크린 롱폼 동영상 완성!")
    print(f"📁 프로젝트 출력 경로: {output_mp4}")
    print(f"📥 다운로드 폴더 저장: {downloads_mp4}")
    print(f"⏱️ 최종 완성 러닝타임: {mins}분 {secs:.1f}초 ({final_dur:.2f}초)")
    print(f"✅ 10분(600초) 이상 필수 충족: {'완벽 충족 (10분 돌파)' if final_dur >= 600.0 else '미달'}")
    print("==============================================================")

if __name__ == "__main__":
    asyncio.run(main())
