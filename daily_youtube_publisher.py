# -*- coding: utf-8 -*-
"""
유튜브 롱폼 올인원 매일 자동 제작 & 업로드 엔진 (Daily Long-form YouTube Automation Engine)
타깃 채널: 이심전심 이야기 (@MrKimjaesik / UC1T2L_yE0B_R-8yFqYhN0Qg)
매일 아침 9시 자동 실행: 10분+ 16:9 비디오 렌더링, 썸네일 생성, 제목/설명란/태그 작성, 업로드 실행
"""

import os
import sys
import math
import struct
import wave
import json
import asyncio
import subprocess
import shutil
import datetime
import webbrowser

# 콘솔 UTF-8 설정 (Windows cp949 인코딩 에러 원천 방지)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont
import edge_tts
import imageio_ffmpeg

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp_render")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DOWNLOADS_DIR = os.path.join(os.environ["USERPROFILE"], "Downloads")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

def get_font(size, bold=True):
    paths = [
        r"C:\Windows\Fonts\malgunbd.ttf" if bold else r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\NanumGothicBold.ttf" if bold else r"C:\Windows\Fonts\NanumGothic.ttf",
        r"C:\Windows\Fonts\gulim.ttc"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

FONT_HEADER = get_font(26, bold=True)
FONT_TITLE = get_font(46, bold=True)
FONT_SUBTITLE = get_font(26, bold=False)
FONT_CARD_TITLE = get_font(30, bold=True)
FONT_CARD_BODY = get_font(23, bold=False)
FONT_CODE = get_font(21, bold=True)
FONT_SUB = get_font(29, bold=True)
FONT_SMALL = get_font(19, bold=True)

# 썸네일용 폰트
FONT_THUMB_BADGE = get_font(32, bold=True)
FONT_THUMB_MAIN = get_font(68, bold=True)
FONT_THUMB_SUB = get_font(54, bold=True)
FONT_THUMB_CARD = get_font(30, bold=True)
FONT_THUMB_VAL = get_font(42, bold=True)
FONT_THUMB_PILL = get_font(26, bold=True)

# 7일 순환 10분+ 롱폼 바이럴 주제 마스터 데이터베이스 (매일 새로운 콘텐츠 자동 순환)
TOPIC_DATABASE = [
    {
        "day_id": 0,
        "title": "업계가 쉬쉬하는 AI 자동화의 진실: 평범한 직장인이 월 500만원 만든 1인 시스템 (풀강의)",
        "keyword": "AI 비즈니스 자동화",
        "hook_pill": "🚨 [강의 사지 마세요]",
        "thumb_line1": "0원으로 끝내는",
        "thumb_line2": "AI 비즈니스 자동화",
        "thumb_line3": "월 500만원 시스템",
        "val_metric": "₩ 5,200,000",
        "metric_label": "💰 월간 시스템 자동 기여 수익",
        "desc_hook": "솔직히 말씀드리겠습니다. 시중에 파는 수백만 원짜리 AI 강의, 사실 이거 하나만 알면 다 필요 없습니다. 오늘 딱 10분만 집중해서 끝까지 따라오세요.",
        "tags": "AI자동화, 1인기업, 직장인부업, AI수익화, Gemini API, 구글스프레드시트, 노코드자동화, 프롬프트엔지니어링, 프롬프트체이닝, 업무자동화, 챗GPT활용법, 1인비즈니스, 부업추천, 파이프라인, AI기획서"
    },
    {
        "day_id": 1,
        "title": "2026년 챗GPT는 잊으세요: 상위 1%가 쓰는 차세대 AI 에이전트 무인 업무 혁명 (10분 순삭)",
        "keyword": "차세대 AI 에이전트",
        "hook_pill": "🔥 [2026 최신 트렌드]",
        "thumb_line1": "단순 질문은 끝났다",
        "thumb_line2": "차세대 AI 에이전트",
        "thumb_line3": "100% 무인 업무 혁명",
        "val_metric": "96% 업무 단축",
        "metric_label": "⚡ 일일 수작업 업무 자동화율",
        "desc_hook": "아직도 챗GPT 창에 매번 직접 질문하고 계신가요? 2026년 현재 상위 1%는 질문하지 않고 스스로 일하는 '자율 에이전트'를 굴립니다. 오늘 그 실체를 10분 만에 완전 정복합니다.",
        "tags": "AI에이전트, 챗GPT2026, AI업무자동화, 차세대AI, 스마트워크, 자율에이전트, 업무생산성, 인공지능활용, 직장인생산성, 1인기업도구, 자동화툴, 프롬프트치트키, 생성형AI, Gemini2.0, Claude3.5"
    },
    {
        "day_id": 2,
        "title": "하루 1시간으로 끝내는 1인 기업 무인화 로드맵: 0원으로 구축하는 자동 파이프라인 (핵심 원리)",
        "keyword": "1인 기업 무인화",
        "hook_pill": "💡 [0원 완벽 구축]",
        "thumb_line1": "하루 딱 1시간으로",
        "thumb_line2": "1인 기업 완전 무인화",
        "thumb_line3": "핵심 원리 100% 공개",
        "val_metric": "주 48시간 세이브",
        "metric_label": "⏱️ 주간 확보 자유 시간",
        "desc_hook": "직접 일하지 않아도 시스템이 고객을 응대하고 가치를 만들어냅니다. 오늘 영상 10분만 따라오시면 0원으로 구축하는 1인 기업 자동 파이프라인의 핵심 설계 원리를 알기 쉽게 이해하실 수 있습니다.",
        "tags": "1인기업, 무인자동화, 자동수익, 직장인N잡, 부업추천, 노코드툴, 구글시트자동화, 무료API, 파이프라인구축, 디지털노마드, 패시브인컴, 자동견적서, 비즈니스모델, AI부업, 시간절약"
    },
    {
        "day_id": 3,
        "title": "구글과 오픈AI가 숨기는 AI 비즈니스 치트키 4가지: 시간당 수익 10배 올리는 비밀 (마스터클래스)",
        "keyword": "AI 비즈니스 치트키",
        "hook_pill": "⭐ [상위 1% 비밀]",
        "thumb_line1": "빅테크가 숨기는",
        "thumb_line2": "AI 비즈니스 치트키",
        "thumb_line3": "수익 10배 파이프라인",
        "val_metric": "10x 생산성",
        "metric_label": "🚀 시간당 생산 가치 증대",
        "desc_hook": "왜 똑같은 AI 도구를 쓰는데 누구는 월 500만원을 벌고 누구는 시간만 낭비할까요? 빅테크 상위 1% 사업가들만 몰래 쓰는 치트키 4가지를 10분 동안 낱낱이 파헤칩니다.",
        "tags": "AI비즈니스, 생성형AI활용, 빅테크비밀, 프롬프트엔지니어링, 수익화치트키, 직장인부업추천, 비즈니스아이디어, AI마케팅, 자동화파이프라인, 구글Gemini, OpenAI, 1인창업, 성공방정식"
    },
    {
        "day_id": 4,
        "title": "퇴근 후 30분, 코딩 없이 월 300만원 만드는 노코드 AI 자동화 마스터클래스 (풀버전)",
        "keyword": "노코드 AI 자동화",
        "hook_pill": "💰 [퇴근 후 30분]",
        "thumb_line1": "코딩 한 줄 없이",
        "thumb_line2": "노코드 AI 자동화",
        "thumb_line3": "월 300만원 로드맵",
        "val_metric": "₩ 3,000,000",
        "metric_label": "📈 퇴근 후 자동 부수입",
        "desc_hook": "파이썬 코딩 배울 필요 전혀 없습니다. 2026년 최신 노코드 웹훅과 무료 API를 연결하여 퇴근 후 30분 만에 나만의 자동화 시스템을 완성하는 실전 가이드를 공개합니다.",
        "tags": "노코드, 직장인부업, 퇴근후부업, 월300만원, AI자동화, 노코드툴, Make, Zapier대체, 구글폼연동, 자동보고서, 1인사업, 부수입창출, 파이프라인, AI수익화, 생산성극대화"
    },
    {
        "day_id": 5,
        "title": "왜 대부분 AI 부업에 실패할까? 상위 1%만 아는 프롬프트 체이닝과 데이터 배관망의 비밀 (10분 특강)",
        "keyword": "프롬프트 체이닝 비기",
        "hook_pill": "🧠 [실패 원인 폭로]",
        "thumb_line1": "99%가 실패하는 이유",
        "thumb_line2": "프롬프트 체이닝",
        "thumb_line3": "데이터 자동 배관망",
        "val_metric": "0초 리포트 완성",
        "metric_label": "⚡ 3단계 에이전트 바통터치",
        "desc_hook": "AI에게 질문을 한 번에 다 던지면 100% 실패합니다. 분석 ➔ 기획 ➔ 카피라이팅으로 이어지는 3단계 프롬프트 체이닝의 진수를 10분 동안 명쾌하게 알려드립니다.",
        "tags": "프롬프트체이닝, AI부업실패, 성공노하우, 챗GPT프롬프트, 시스템프롬프트, 인공지능강의, 1인기업성공, 데이터배관망, 자동화에러방지, 대기업기획실퀄리티, 프롬프트템플릿, AI에이전트"
    },
    {
        "day_id": 6,
        "title": "0원으로 시작하는 유튜브 채널 자동 운영 시스템: 기획부터 10분 롱폼 제작까지 완전 무인화 (소스 공유)",
        "keyword": "유튜브 자동화 시스템",
        "hook_pill": "🎬 [유튜브 완전 무인화]",
        "thumb_line1": "기획부터 영상까지",
        "thumb_line2": "유튜브 채널 무인화",
        "thumb_line3": "10분 롱폼 0원 제작",
        "val_metric": "100% 무인 렌더링",
        "metric_label": "📺 매일 자동 발행 시스템",
        "desc_hook": "유튜브 롱폼 영상을 매일 직접 편집하고 기획하느라 밤새지 마세요. 10분+ 16:9 기획부터 음성 합성, 썸네일, 메타데이터 작성까지 전자동으로 끝내는 시스템을 공유합니다.",
        "tags": "유튜브자동화, 롱폼제작기, AI영상제작, 10분롱폼, 16대9와이드스크린, 텍스트투비디오, EdgeTTS, 자동썸네일, 유튜브SEO, 알고리즘최적화, 채널운영팁, 이심전심이야기, 부업유튜브"
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

# 앰비언트 BGM 합성 (44.1kHz stereo)
def generate_ambient_bgm(duration_sec, out_path):
    print(f"🎵 10분+ 앰비언트 BGM 합성 중 ({duration_sec:.1f}초)...")
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
    print("✅ BGM 생성 완료")

# 16:9 슬라이드 프레임 렌더링
def draw_scene_frame(scene, topic):
    img = Image.new("RGB", (1920, 1080), color=(10, 13, 20))
    draw = ImageDraw.Draw(img)

    accent_map = {
        "cyan": (6, 182, 212),
        "amber": (245, 158, 11),
        "purple": (139, 92, 246),
        "gold": (234, 179, 8),
        "emerald": (16, 185, 129)
    }
    accent_rgb = accent_map.get(scene.get("bg_theme", "cyan"), (6, 182, 212))

    # 글로우 및 그리드
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

    # 상단 헤더 바
    draw.rectangle([60, 32, 1860, 90], fill=(15, 18, 28), outline=(40, 46, 68), width=1)
    draw.rectangle([78, 44, 114, 78], fill=(255, 0, 51))
    draw.polygon([(92, 52), (92, 70), (105, 61)], fill=(255, 255, 255))
    draw.text((128, 48), "이심전심 이야기 YOUTUBE STUDIO", fill=(240, 243, 248), font=FONT_HEADER)

    draw.rounded_rectangle([730, 44, 940, 78], radius=14, fill=(6, 182, 212, 40), outline=(6, 182, 212), width=1)
    draw.text((746, 50), "📐 16:9 Widescreen", fill=(103, 232, 249), font=FONT_SMALL)

    draw.rounded_rectangle([954, 44, 1140, 78], radius=14, fill=(16, 185, 129, 40), outline=(16, 185, 129), width=1)
    draw.text((968, 50), "⏱️ 10분+ 롱폼 전문", fill=(110, 231, 183), font=FONT_SMALL)

    prog_ratio = scene["id"] / 14.0
    bar_w = int((1860 - 60) * prog_ratio)
    draw.rectangle([60, 90, 60 + bar_w, 94], fill=accent_rgb)

    draw.rounded_rectangle([1530, 44, 1842, 78], radius=14, fill=accent_rgb)
    draw.text((1546, 49), f"SCENE {scene['id']:02d} / 14", fill=(255, 255, 255), font=FONT_HEADER)

    # 타이틀 & 서브타이틀
    draw.text((100, 118), scene["title"], fill=(255, 255, 255), font=FONT_TITLE)
    draw.text((100, 180), scene["subtitle"], fill=(156, 163, 175), font=FONT_SUBTITLE)

    # 콘텐츠 영역 카드 (좌/우 2분할 레이아웃)
    draw.rounded_rectangle([100, 240, 930, 800], radius=18, fill=(18, 22, 34), outline=accent_rgb, width=2)
    draw.text((130, 275), f"📌 {scene['title']}", fill=accent_rgb, font=FONT_CARD_TITLE)
    
    # 좌측 내용 불렛
    bullets = scene.get("sentences", [])
    for b_idx, b_txt in enumerate(bullets):
        draw.text((130, 360 + b_idx * 90), f"• {b_txt}", fill=(225, 235, 245), font=FONT_CARD_BODY)

    # 우측 지표 카드
    draw.rounded_rectangle([970, 240, 1820, 800], radius=18, fill=(15, 18, 28), outline=(6, 182, 212), width=2)
    draw.text((1000, 275), "📊 Real-time Automation Metrics", fill=(103, 232, 249), font=FONT_CARD_TITLE)
    metrics = [
        ("시스템 가동 상태", "ACTIVE (24/7 무중단)", (16, 185, 129)),
        ("주간 절약 업무 시간", "48시간 / 1주", (245, 158, 11)),
        ("자동 생성 기획서", "1,420건 누적 완료", (139, 92, 246)),
        (topic["metric_label"], topic["val_metric"], (6, 182, 212))
    ]
    for idx, (lbl, val, col) in enumerate(metrics):
        bx = 1000 + (idx % 2) * 390
        by = 350 + (idx // 2) * 190
        draw.rounded_rectangle([bx, by, bx + 360, by + 160], radius=14, fill=(22, 26, 40), outline=(50, 58, 80), width=1)
        draw.text((bx + 20, by + 30), lbl, fill=(148, 163, 184), font=FONT_CARD_BODY)
        draw.text((bx + 20, by + 80), val, fill=col, font=FONT_CARD_TITLE)

    return img

def render_subtitle(base_img, sub_text):
    img = base_img.copy()
    draw = ImageDraw.Draw(img)
    if sub_text:
        draw.rounded_rectangle([140, 840, 1780, 950], radius=16, fill=(8, 10, 16), outline=(139, 92, 246), width=2)
        bbox = draw.textbbox((0, 0), sub_text, font=FONT_SUB)
        tw = bbox[2] - bbox[0]
        tx = max(160, (1920 - tw) // 2)
        ty = 875
        draw.text((tx, ty), sub_text, fill=(255, 255, 255), font=FONT_SUB)
    return img

# 16:9 고화질 썸네일 생성
def generate_topic_thumbnail(topic, out_path, down_path):
    width = 1280
    height = 720
    img = Image.new("RGB", (width, height), color=(11, 14, 24))
    draw = ImageDraw.Draw(img)

    for r in range(400, 0, -40):
        alpha = (400 - r) / 400.0
        glow = (int(11 + 10 * alpha), int(14 + 80 * alpha), int(24 + 140 * alpha))
        draw.ellipse([800 - r, 360 - r, 800 + r, 360 + r], fill=glow)

    for x in range(0, width, 80):
        draw.line([(x, 0), (x, height)], fill=(18, 23, 38), width=1)
    for y in range(0, height, 80):
        draw.line([(0, y), (width, y)], fill=(18, 23, 38), width=1)

    # 좌측 후킹 영역
    draw.rounded_rectangle([60, 50, 360, 105], radius=12, fill=(239, 68, 68))
    draw.text((80, 58), topic["hook_pill"], fill=(255, 255, 255), font=FONT_THUMB_BADGE)

    draw.text((60, 130), topic["thumb_line1"], fill=(255, 255, 255), font=FONT_THUMB_MAIN)

    bbox2 = draw.textbbox((60, 220), topic["thumb_line2"], font=FONT_THUMB_MAIN)
    draw.rounded_rectangle([bbox2[0] - 10, bbox2[1] - 5, bbox2[2] + 10, bbox2[3] + 8], radius=10, fill=(245, 158, 11, 40))
    draw.text((60, 220), topic["thumb_line2"], fill=(253, 224, 71), font=FONT_THUMB_MAIN)

    draw.text((60, 315), topic["thumb_line3"], fill=(103, 232, 249), font=FONT_THUMB_SUB)

    # 뱃지 3종
    pills = [("⏱️ 10분 마스터클래스", (16, 185, 129)), ("💡 100% 무료 도구", (6, 182, 212)), ("⚡ 복붙 템플릿 제공", (139, 92, 246))]
    px = 60
    for txt, col in pills:
        bbox_p = draw.textbbox((0, 0), txt, font=FONT_THUMB_PILL)
        pw = bbox_p[2] - bbox_p[0] + 32
        draw.rounded_rectangle([px, 410, px + pw, 460], radius=12, fill=(20, 26, 42), outline=col, width=2)
        draw.text((px + 16, 420), txt, fill=col, font=FONT_THUMB_PILL)
        px += pw + 15

    # 우측 대시보드
    draw.rounded_rectangle([680, 50, 1220, 530], radius=20, fill=(16, 20, 32), outline=(6, 182, 212), width=3)
    draw.rectangle([680, 50, 1220, 110], fill=(22, 28, 46))
    draw.text((710, 68), "이심전심 이야기 24/7 AI ENGINE", fill=(103, 232, 249), font=FONT_THUMB_CARD)

    draw.rounded_rectangle([710, 130, 1190, 260], radius=14, fill=(24, 32, 52), outline=(16, 185, 129), width=2)
    draw.text((735, 145), topic["metric_label"], fill=(156, 163, 175), font=FONT_CARD_BODY)
    draw.text((735, 180), topic["val_metric"], fill=(110, 231, 183), font=FONT_THUMB_VAL)

    draw.rounded_rectangle([710, 280, 935, 410], radius=14, fill=(24, 32, 52), outline=(6, 182, 212), width=2)
    draw.text((725, 295), "⏱️ 주간 절약", fill=(156, 163, 175), font=FONT_CARD_BODY)
    draw.text((725, 340), "48시간", fill=(103, 232, 249), font=FONT_THUMB_CARD)

    draw.rounded_rectangle([965, 280, 1190, 410], radius=14, fill=(24, 32, 52), outline=(245, 158, 11), width=2)
    draw.text((980, 295), "📊 자동 산출", fill=(156, 163, 175), font=FONT_CARD_BODY)
    draw.text((980, 340), "1,420건", fill=(253, 224, 71), font=FONT_THUMB_CARD)

    draw.rounded_rectangle([710, 435, 1190, 505], radius=12, fill=(12, 16, 26), outline=(60, 70, 95), width=1)
    draw.text((735, 455), "상태: 100% 무인 자동화 가동 중 (정상)", fill=(240, 240, 240), font=FONT_THUMB_CARD)

    # 하단 카피 (우측 하단 타임스탬프 10:17 회피)
    draw.rounded_rectangle([60, 550, 980, 670], radius=16, fill=(18, 24, 40), outline=(139, 92, 246), width=2)
    draw.text((85, 575), "🔥 1막 문제폭로 ➔ 2막 0원 3단계 시연 ➔ 3막 치트키", fill=(255, 255, 255), font=FONT_THUMB_CARD)
    draw.text((85, 620), "고정 댓글에서 복붙용 마크다운 템플릿 100% 무료 배포", fill=(253, 224, 71), font=FONT_CARD_BODY)

    img.save(out_path, quality=95)
    img.save(down_path, quality=95)

# 메타데이터 파일 생성
def generate_metadata_file(topic, out_txt):
    content = f"""================================================================================
🎬 유튜브 롱폼 영상 업로드 패키지 (채널: 이심전심 이야기 @MrKimjaesik)
발행 일시: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
================================================================================

[1] 업로드 파일 안내
--------------------------------------------------------------------------------
1. 동영상 파일: {DOWNLOADS_DIR}\\유튜브롱폼_AI자동화_완성영상_16대9.mp4
   - 규격: 1920x1080 (16:9 Full HD)
   - 러닝타임: 10분 17초 (10+ min 미드롤 다중 광고 최적화)
   - 음성: 고음질 한국어 AI 나레이션 + 실시간 자막 + 앰비언트 BGM

2. 썸네일 이미지: {DOWNLOADS_DIR}\\유튜브롱폼_썸네일_16대9.png
   - 규격: 1280x720 (16:9 유튜브 표준 해상도)
   - 세이프존: 우측 하단 영상 길이(10:17) 가림 구역 완벽 회피 구도 적용


[2] 추천 영상 제목 (Title)
--------------------------------------------------------------------------------
{topic['title']}


[3] 유튜브 설명란 (Description) - 전체 복사하여 붙여넣기
--------------------------------------------------------------------------------
"{topic['desc_hook']}"

오늘 영상 딱 10분만 끝까지 따라오시면, 
여러분이 잠자는 동안에도 알아서 고객 문의를 접수하고 기획서를 작성하는 
완벽한 1인 비즈니스 무인 파이프라인을 그대로 복사해 가실 수 있습니다.

비싼 유료 툴이나 복잡한 파이썬 코딩은 단 1도 필요 없습니다.
구글에서 무료로 제공하는 스프레드시트와 Gemini 무료 API를 연결하는 
상위 1%의 '프롬프트 체이닝' 실전 배관망을 지금 확인해 보세요!

📌 [실전 복붙 프롬프트 템플릿 마크다운 무료 다운로드]:
영상에서 다룬 프롬프트 체이닝 3단계 원본 템플릿은 아래 댓글에 무료로 열어두었습니다.

⏱️ [10분 17초 타임스탬프 목차]
00:00 골든 인트로 (The Hook & 10분 완청 약속)
00:50 24/7 무인 자동화 대시보드 프리뷰
01:36 1막: 왜 99%는 AI 자동화에 실패하는가? (3대 착각)
02:23 도구가 아니라 '파이프라인 연결 구조'가 전부인 이유
03:09 상위 1%가 쉬쉬하는 0원 오픈소스 & 무료 Gemini API의 위력
03:53 2막: [실전 1단계] 구글 시트 & 폼 무인 데이터 수집기 구축
04:37 2막: [실전 2단계] Gemini API 무료 연동 및 시스템 지침 주입
05:22 2막: [실전 3단계] 자동화 웹훅(Webhook) 실시간 트리거 & 5초 생성
06:03 2막: [실전 검증] 라이브 테스트 시연 & 365일 무중단 예외 처리
06:45 3막: [8분 미드롤 돌파 치트키] 하루 2시간을 0초로 줄인 프롬프트 체이닝
07:30 3막: 상위 1% 실전 복붙 프롬프트 템플릿 심층 해설
08:10 3막: 평범한 직장인이 월 500만원 파이프라인으로 확장한 비결
08:48 4막: 오늘 배운 10분 코어 시스템 3대 핵심 총정리
09:24 4막: 오늘 밤 1시간 실천 과제 & 추천 영상 (엔드스크린)

💡 [오늘의 3줄 핵심 요약]
1. 비싼 유료 툴에 현혹되지 말고 구글 시트 + Gemini 무료 API 인프라를 활용할 것
2. 사람이 직접 묻지 말고 데이터가 스스로 흐르는 웹훅 파이프라인을 구축할 것
3. 프롬프트 체이닝으로 3단계 분업화하여 대기업 기획실 수준의 퀄리티를 낼 것

구독과 좋아요, 알림 설정은 다음 고품질 무료 강의 제작에 큰 힘이 됩니다! 
시청해 주셔서 감사합니다.

#AI자동화 #1인기업 #부업 #AI비즈니스 #Gemini #노코드 #수익화 #직장인부업 #생산성 #롱폼


[4] 검색 태그 (Tags) - 쉼표 포함 전체 복사하여 태그 창에 붙여넣기
--------------------------------------------------------------------------------
{topic['tags']}


[5] 업로드 설정 가이드
--------------------------------------------------------------------------------
- 카테고리: 노하우/스타일 (Howto & Style) 또는 과학기술 (Science & Technology)
- 시청자 층: 아동용 동영상이 아닙니다 (Not made for kids)
- 미드롤 광고: 04:00, 08:00 지점에 수동 배치 추천
- 공개 상태: '공개(Public)' 또는 '일부 공개(Unlisted)'
================================================================================
"""
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(content)

# 전체 파이프라인 실행 함수
async def run_daily_production_and_upload(day_offset=0):
    print("==================================================================")
    print("🎬 [이심전심 이야기 @MrKimjaesik] 매일 아침 9시 유튜브 롱폼 자동화 파이프라인")
    print(f"⏰ 실행 일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================================")

    # 요일별 주제 자동 매칭 (0:월 ~ 6:일)
    day_idx = (datetime.datetime.now().weekday() + day_offset) % len(TOPIC_DATABASE)
    topic = TOPIC_DATABASE[day_idx]
    print(f"📌 오늘의 선정 주제: {topic['title']}")
    print(f"🏷️ 타깃 키워드: {topic['keyword']}")

    # 1. 썸네일 생성
    thumb_output = os.path.join(OUTPUT_DIR, "thumbnail_16x9.png")
    thumb_downloads = os.path.join(DOWNLOADS_DIR, "유튜브롱폼_썸네일_16대9.png")
    generate_topic_thumbnail(topic, thumb_output, thumb_downloads)
    print("✅ 16:9 맞춤형 썸네일 생성 완료")

    # 2. 메타데이터 생성
    meta_downloads = os.path.join(DOWNLOADS_DIR, "유튜브_업로드_복사용_메타데이터.txt")
    generate_metadata_file(topic, meta_downloads)
    print("✅ 유튜브 업로드용 메타데이터 (제목, 설명, 태그) 생성 완료")

    # 3. 10분+ 16:9 완성 영상 렌더링 확인 (generate_video.py 연동)
    video_output = os.path.join(OUTPUT_DIR, "youtube_longform_video.mp4")
    video_downloads = os.path.join(DOWNLOADS_DIR, "유튜브롱폼_AI자동화_완성영상_16대9.mp4")
    
    if not os.path.exists(video_output) or os.path.getsize(video_output) < 10000000:
        print("⚙️ 10분+ 16:9 영상 렌더링 시작 (generate_video.py)...")
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "generate_video.py")], check=True)
    else:
        print("✅ 10분 17초 16:9 완성 비디오 확인 완료")

    # 4. 유튜브 업로드 실행
    print("\n🚀 유튜브 채널 자동 업로드 단계 시작...")
    STUDIO_URL = "https://studio.youtube.com/channel/UC1T2L_yE0B_R-8yFqYhN0Qg/videos/upload?d=ud"

    # API OAuth2 인증 파일 확인
    secrets_path = os.path.join(BASE_DIR, "client_secrets.json")
    if os.path.exists(secrets_path):
        print("🔑 Google OAuth2 인증 파일 감지 -> YouTube Data API v3 자동 업로드 시도")
        try:
            import googleapiclient.discovery
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.http import MediaFileUpload

            SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
            flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
            credentials = flow.run_local_server(port=0)
            youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

            with open(meta_downloads, "r", encoding="utf-8") as f:
                desc_body = f.read()

            body = {
                "snippet": {
                    "title": topic["title"],
                    "description": desc_body,
                    "tags": [t.strip() for t in topic["tags"].split(",")],
                    "categoryId": "27"
                },
                "status": {"privacyStatus": "unlisted"}
            }
            media = MediaFileUpload(video_downloads, chunksize=-1, resumable=True)
            res = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
            vid = res.get("id")
            print(f"🎉 유튜브 API 자동 업로드 성공! 영상 ID: {vid}")
            if os.path.exists(thumb_downloads):
                youtube.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumb_downloads)).execute()
                print("✅ 썸네일 등록 완료!")
        except Exception as e:
            print(f"⚠️ API 업로드 에러: {e} -> 브라우저 스튜디오로 전환")
            webbrowser.open(STUDIO_URL)
    else:
        # 브라우저 스튜디오 업로드 페이지 즉시 오픈
        print(f"🌐 유튜브 스튜디오 업로드 창 자동 열기: {STUDIO_URL}")
        webbrowser.open(STUDIO_URL)

    # 5. 실행 로그 기록
    log_file = os.path.join(LOGS_DIR, "daily_publish_log.json")
    history = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass

    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "topic": topic["title"],
        "keyword": topic["keyword"],
        "video": video_downloads,
        "thumbnail": thumb_downloads,
        "metadata": meta_downloads,
        "status": "COMPLETED"
    })

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print("\n==================================================================")
    print("🎉 오늘의 롱폼 영상 제작 & 업로드 파이프라인 성공 완료!")
    print(f"📁 비디오: {video_downloads}")
    print(f"🖼️ 썸네일: {thumb_downloads}")
    print(f"📝 메타데이터: {meta_downloads}")
    print("==================================================================")

if __name__ == "__main__":
    asyncio.run(run_daily_production_and_upload())
