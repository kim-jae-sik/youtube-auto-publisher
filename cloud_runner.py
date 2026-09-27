# -*- coding: utf-8 -*-
"""
24/7 클라우드 무인 롱폼 영상 기획·렌더링 & 유튜브 전체공개 자동 업로더
(24/7 Cloud YouTube Long-form Autonomous Publisher)
PC가 꺼져 있어도 클라우드(GitHub Actions, AWS, VPS 등)에서 100% 무인 작동
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

# UTF-8 출력 보장
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont
import edge_tts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp_cloud_render")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# FFmpeg 실행 파일 감지 (시스템 ffmpeg 우선, 없으면 imageio_ffmpeg)
FFMPEG_EXE = shutil.which("ffmpeg")
if not FFMPEG_EXE:
    try:
        import imageio_ffmpeg
        FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        FFMPEG_EXE = "ffmpeg"

# 폰트 로드 (Windows 및 Linux/Ubuntu 클라우드 겸용)
def get_cloud_font(size, bold=True):
    font_candidates = [
        # Windows
        r"C:\Windows\Fonts\malgunbd.ttf" if bold else r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\NanumGothicBold.ttf" if bold else r"C:\Windows\Fonts\NanumGothic.ttf",
        # Linux / Ubuntu (GitHub Actions)
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for p in font_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

FONT_HEADER = get_cloud_font(28, bold=True)
FONT_TITLE = get_cloud_font(48, bold=True)
FONT_SUBTITLE = get_cloud_font(26, bold=False)
FONT_CARD_TITLE = get_cloud_font(32, bold=True)
FONT_CARD_BODY = get_cloud_font(26, bold=True)
FONT_SUB = get_cloud_font(36, bold=True)
FONT_SMALL = get_cloud_font(20, bold=True)

FONT_THUMB_BADGE = get_cloud_font(32, bold=True)
FONT_THUMB_MAIN = get_cloud_font(68, bold=True)
FONT_THUMB_SUB = get_cloud_font(54, bold=True)
FONT_THUMB_CARD = get_cloud_font(30, bold=True)
FONT_THUMB_VAL = get_cloud_font(42, bold=True)
FONT_THUMB_PILL = get_cloud_font(26, bold=True)

# 24시간 시간별 순환 10분+ 롱폼 바이럴 주제 데이터베이스
HOURLY_TOPICS = [
    {
        "title": "2026년 챗GPT는 잊으세요: 상위 1%가 쓰는 차세대 AI 에이전트 무인 업무 혁명 (풀강의)",
        "keyword": "차세대 AI 에이전트",
        "hook_pill": "🔥 [2026 최신 트렌드]",
        "thumb_line1": "단순 질문은 끝났다",
        "thumb_line2": "차세대 AI 에이전트",
        "thumb_line3": "100% 무인 업무 혁명",
        "val_metric": "96% 업무 단축",
        "metric_label": "⚡ 일일 수작업 업무 자동화율",
        "tags": ["AI에이전트", "챗GPT2026", "AI업무자동화", "차세대AI", "자율에이전트", "생산성", "이심전심이야기"]
    },
    {
        "title": "업계가 쉬쉬하는 AI 자동화의 진실: 평범한 직장인이 월 500만원 만든 1인 시스템 (풀강의)",
        "keyword": "AI 비즈니스 자동화",
        "hook_pill": "🚨 [강의 사지 마세요]",
        "thumb_line1": "0원으로 끝내는",
        "thumb_line2": "AI 비즈니스 자동화",
        "thumb_line3": "월 500만원 시스템",
        "val_metric": "₩ 5,200,000",
        "metric_label": "💰 월간 시스템 자동 기여 수익",
        "tags": ["AI자동화", "1인기업", "직장인부업", "Gemini", "노코드", "업무자동화", "파이프라인"]
    },
    {
        "title": "하루 1시간으로 끝내는 1인 기업 완전 무인화 로드맵: 0원으로 구축하는 자동 파이프라인 (핵심 원리)",
        "keyword": "1인 기업 무인화",
        "hook_pill": "💡 [0원 완벽 구축]",
        "thumb_line1": "하루 딱 1시간으로",
        "thumb_line2": "1인 기업 완전 무인화",
        "thumb_line3": "핵심 원리 100% 공개",
        "val_metric": "주 48시간 세이브",
        "metric_label": "⏱️ 주간 확보 자유 시간",
        "tags": ["1인기업", "무인자동화", "자동수익", "직장인N잡", "구글시트자동화", "디지털노마드"]
    },
    {
        "title": "구글과 오픈AI가 숨기는 AI 비즈니스 치트키 4가지: 시간당 수익 10배 올리는 비밀 (마스터클래스)",
        "keyword": "AI 비즈니스 치트키",
        "hook_pill": "⭐ [상위 1% 비밀]",
        "thumb_line1": "빅테크가 숨기는",
        "thumb_line2": "AI 비즈니스 치트키",
        "thumb_line3": "수익 10배 파이프라인",
        "val_metric": "10x 생산성",
        "metric_label": "🚀 시간당 생산 가치 증대",
        "tags": ["AI비즈니스", "생성형AI활용", "프롬프트엔지니어링", "수익화치트키", "1인창업"]
    },
    {
        "title": "퇴근 후 30분, 코딩 없이 월 300만원 만드는 노코드 AI 자동화 마스터클래스 (풀버전)",
        "keyword": "노코드 AI 자동화",
        "hook_pill": "💰 [퇴근 후 30분]",
        "thumb_line1": "코딩 한 줄 없이",
        "thumb_line2": "노코드 AI 자동화",
        "thumb_line3": "월 300만원 로드맵",
        "val_metric": "₩ 3,000,000",
        "metric_label": "📈 퇴근 후 자동 부수입",
        "tags": ["노코드", "직장인부업", "퇴근후부업", "AI자동화", "부수입창출", "생산성극대화"]
    },
    {
        "title": "왜 대부분 AI 부업에 실패할까? 상위 1%만 아는 프롬프트 체이닝과 데이터 배관망의 비밀 (10분 특강)",
        "keyword": "프롬프트 체이닝 비기",
        "hook_pill": "🧠 [실패 원인 폭로]",
        "thumb_line1": "99%가 실패하는 이유",
        "thumb_line2": "프롬프트 체이닝",
        "thumb_line3": "데이터 자동 배관망",
        "val_metric": "0초 리포트 완성",
        "metric_label": "⚡ 3단계 에이전트 바통터치",
        "tags": ["프롬프트체이닝", "AI부업실패", "성공노하우", "챗GPT프롬프트", "데이터배관망"]
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

# 앰비언트 BGM 합성
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

# 한글 텍스트 자동 줄바꿈 함수 (박스 넘침 완전 방지)
def wrap_text(draw, text, font, max_width):
    lines = []
    words = text.split(" ")
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            w_bbox = draw.textbbox((0, 0), word, font=font)
            if w_bbox[2] - w_bbox[0] > max_width:
                cur_chars = ""
                for char in word:
                    t_chars = cur_chars + char
                    if draw.textbbox((0, 0), t_chars, font=font)[2] <= max_width:
                        cur_chars = t_chars
                    else:
                        lines.append(cur_chars)
                        cur_chars = char
                current_line = cur_chars
            else:
                current_line = word
    if current_line:
        lines.append(current_line)
    return lines

# 16:9 슬라이드 프레임 렌더링 (영문/깨진 이모지 완전 삭제 & 고가독성 한글화 & 자동 줄바꿈)
def draw_scene_frame(scene, topic):
    img = Image.new("RGB", (1920, 1080), color=(10, 14, 23))
    draw = ImageDraw.Draw(img)

    accent_map = {
        "cyan": (6, 182, 212),
        "amber": (245, 158, 11),
        "purple": (139, 92, 246),
        "gold": (234, 179, 8),
        "emerald": (16, 185, 129)
    }
    accent_rgb = accent_map.get(scene.get("bg_theme", "cyan"), (6, 182, 212))

    # 부드러운 배경 앰비언트 글로우
    for r in range(450, 0, -50):
        glow_color = (
            int(10 + accent_rgb[0] * 0.08 * (1 - r / 450)),
            int(14 + accent_rgb[1] * 0.08 * (1 - r / 450)),
            int(23 + accent_rgb[2] * 0.08 * (1 - r / 450))
        )
        draw.ellipse([960 - r * 2, 540 - r, 960 + r * 2, 540 + r], fill=glow_color)

    # 1. 상단 바: 영문 및 깨진 이모지 완전 삭제! 깔끔한 채널 브랜드 & 진행 상황만 표시
    draw.rectangle([60, 30, 1860, 86], fill=(16, 22, 36), outline=(45, 55, 75), width=1)
    draw.rectangle([78, 42, 114, 74], fill=(255, 0, 51))
    draw.polygon([(92, 50), (92, 66), (105, 58)], fill=(255, 255, 255))
    draw.text((128, 44), "이심전심 이야기", fill=(255, 255, 255), font=FONT_HEADER)

    # 우측 상단 씬 회차 뱃지
    draw.rounded_rectangle([1600, 42, 1842, 74], radius=10, fill=accent_rgb)
    draw.text((1626, 45), f"제 {scene['id']:02d} 화 / 총 14 화", fill=(255, 255, 255), font=FONT_HEADER)

    # 상단 진행 바
    prog_ratio = scene["id"] / 14.0
    bar_w = int((1860 - 60) * prog_ratio)
    draw.rectangle([60, 86, 1860, 90], fill=(30, 40, 60))
    draw.rectangle([60, 86, 60 + bar_w, 90], fill=accent_rgb)

    # 2. 메인 타이틀 & 서브타이틀 (굵고 선명한 화이트/실버)
    draw.text((80, 115), scene["title"], fill=(255, 255, 255), font=FONT_TITLE)
    draw.text((80, 175), scene["subtitle"], fill=(203, 213, 225), font=FONT_SUBTITLE)

    # 3. 좌측 카드: 핵심 강의 및 원리 해설 (자동 줄바꿈으로 박스 넘침 100% 방지)
    draw.rounded_rectangle([80, 230, 1060, 820], radius=18, fill=(18, 24, 38), outline=accent_rgb, width=2)
    draw.text((115, 260), "📌 핵심 내용 및 실전 분석", fill=accent_rgb, font=FONT_CARD_TITLE)

    cur_y = 330
    for sent in scene.get("sentences", []):
        draw.text((115, cur_y), "•", fill=accent_rgb, font=FONT_CARD_BODY)
        lines = wrap_text(draw, sent, FONT_CARD_BODY, 890)
        for l in lines:
            draw.text((145, cur_y), l, fill=(255, 255, 255), font=FONT_CARD_BODY)
            cur_y += 38
        cur_y += 16

    # 4. 우측 카드: 핵심 체크 포인트 (불필요한 영어 지표 삭제, 가독성 높은 한글 카드)
    draw.rounded_rectangle([1100, 230, 1840, 820], radius=18, fill=(15, 20, 32), outline=(139, 92, 246), width=2)
    draw.text((1135, 260), "⚡ 핵심 체크 포인트 (Key Insights)", fill=(196, 181, 253), font=FONT_CARD_TITLE)

    boxes = [
        ("💡 오늘의 핵심 키워드", topic.get("keyword", "AI 비즈니스"), (253, 224, 71)),
        ("🎯 시스템 기대 효과", topic.get("val_metric", "업무 90% 이상 단축"), (52, 211, 153)),
        ("🔄 코어 연결 방식", "구글 시트 + Gemini 무료 API 인프라", (103, 232, 249)),
        ("📢 시청 가이드", "화면 속 작동 원리를 바탕으로 직접 실습해 보세요", (244, 114, 182))
    ]

    for idx, (lbl, val, col) in enumerate(boxes):
        by = 330 + idx * 115
        draw.rounded_rectangle([1135, by, 1805, by + 95], radius=12, fill=(24, 30, 48), outline=(60, 72, 100), width=1)
        draw.text((1155, by + 15), lbl, fill=(160, 174, 192), font=FONT_SUBTITLE)
        val_lines = wrap_text(draw, val, FONT_CARD_BODY, 620)
        for vl_i, vl in enumerate(val_lines[:2]):
            draw.text((1155, by + 50 + vl_i * 30), vl, fill=col, font=FONT_CARD_BODY)

    return img

# 하단 자막 렌더링 (굵은 36pt 노란색 고대비 & 긴 문장 자동 2줄 중앙 정렬)
def render_subtitle(base_img, sub_text):
    img = base_img.copy()
    draw = ImageDraw.Draw(img)
    if sub_text:
        lines = wrap_text(draw, sub_text, FONT_SUB, 1600)
        card_h = 100 if len(lines) <= 1 else 135
        card_y = 850 if len(lines) <= 1 else 830
        draw.rounded_rectangle([100, card_y, 1820, card_y + card_h], radius=16, fill=(10, 14, 22), outline=(253, 224, 71), width=2)
        start_y = card_y + (28 if len(lines) <= 1 else 18)
        for l_idx, line in enumerate(lines[:2]):
            bbox = draw.textbbox((0, 0), line, font=FONT_SUB)
            tw = bbox[2] - bbox[0]
            tx = (1920 - tw) // 2
            draw.text((tx, start_y + l_idx * 48), line, fill=(255, 235, 59), font=FONT_SUB)
    return img

# 16:9 썸네일 생성
def generate_thumbnail(topic, out_path):
    width, height = 1280, 720
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

    draw.rounded_rectangle([60, 50, 360, 105], radius=12, fill=(239, 68, 68))
    draw.text((80, 58), topic["hook_pill"], fill=(255, 255, 255), font=FONT_THUMB_BADGE)

    draw.text((60, 130), topic["thumb_line1"], fill=(255, 255, 255), font=FONT_THUMB_MAIN)

    bbox2 = draw.textbbox((60, 220), topic["thumb_line2"], font=FONT_THUMB_MAIN)
    draw.rounded_rectangle([bbox2[0] - 10, bbox2[1] - 5, bbox2[2] + 10, bbox2[3] + 8], radius=10, fill=(245, 158, 11, 40))
    draw.text((60, 220), topic["thumb_line2"], fill=(253, 224, 71), font=FONT_THUMB_MAIN)

    draw.text((60, 315), topic["thumb_line3"], fill=(103, 232, 249), font=FONT_THUMB_SUB)

    pills = [("⏱️ 10분 마스터클래스", (16, 185, 129)), ("💡 100% 무료 도구", (6, 182, 212)), ("⚡ 24/7 클라우드 무인화", (139, 92, 246))]
    px = 60
    for txt, col in pills:
        bbox_p = draw.textbbox((0, 0), txt, font=FONT_THUMB_PILL)
        pw = bbox_p[2] - bbox_p[0] + 32
        draw.rounded_rectangle([px, 410, px + pw, 460], radius=12, fill=(20, 26, 42), outline=col, width=2)
        draw.text((px + 16, 420), txt, fill=col, font=FONT_THUMB_PILL)
        px += pw + 15

    draw.rounded_rectangle([680, 50, 1220, 530], radius=20, fill=(16, 20, 32), outline=(6, 182, 212), width=3)
    draw.rectangle([680, 50, 1220, 110], fill=(22, 28, 46))
    draw.text((710, 68), "이심전심 이야기 CLOUD ENGINE", fill=(103, 232, 249), font=FONT_THUMB_CARD)

    draw.rounded_rectangle([710, 130, 1190, 260], radius=14, fill=(24, 32, 52), outline=(16, 185, 129), width=2)
    draw.text((735, 145), topic["metric_label"], fill=(156, 163, 175), font=FONT_CARD_BODY)
    draw.text((735, 180), topic["val_metric"], fill=(110, 231, 183), font=FONT_THUMB_VAL)

    draw.rounded_rectangle([710, 280, 935, 410], radius=14, fill=(24, 32, 52), outline=(6, 182, 212), width=2)
    draw.text((725, 295), "⏱️ 주간 절약", fill=(156, 163, 175), font=FONT_CARD_BODY)
    draw.text((725, 340), "54시간", fill=(103, 232, 249), font=FONT_THUMB_CARD)

    draw.rounded_rectangle([965, 280, 1190, 410], radius=14, fill=(24, 32, 52), outline=(245, 158, 11), width=2)
    draw.text((980, 295), "📊 무인 가동", fill=(156, 163, 175), font=FONT_CARD_BODY)
    draw.text((980, 340), "100%", fill=(253, 224, 71), font=FONT_THUMB_CARD)

    draw.rounded_rectangle([710, 435, 1190, 505], radius=12, fill=(12, 16, 26), outline=(60, 70, 95), width=1)
    draw.text((735, 455), "상태: 클라우드 무인 자동화 가동 중 (정상)", fill=(240, 240, 240), font=FONT_THUMB_CARD)

    # 하단 카피 (우측 하단 타임스탬프 세이프존 회피)
    draw.rounded_rectangle([60, 550, 980, 670], radius=16, fill=(18, 24, 40), outline=(139, 92, 246), width=2)
    draw.text((85, 575), "🔥 1막 문제폭로 ➔ 2막 0원 3단계 시연 ➔ 3막 치트키", fill=(255, 255, 255), font=FONT_THUMB_CARD)
    draw.text((85, 620), "화면 속 핵심 파이프라인 작동 원리와 구조를 알기 쉽게 해설", fill=(253, 224, 71), font=FONT_CARD_BODY)

    img.save(out_path, quality=95)

# 14개 마스터 씬 대본 생성 (10분+ 분량 보장)
def get_master_scenes(topic):
    title = topic["title"]
    kw = topic["keyword"]
    return [
        {
            "id": 1,
            "title": f"골든 인트로: {kw}의 충격적 실체",
            "subtitle": "수백만 원짜리 유료 강의에 속지 않고 1인 비즈니스를 완벽히 자동화하는 실전 공식",
            "script": f"솔직히 말씀드리겠습니다. 시중에 넘쳐나는 수백만 원짜리 AI 강의, 사실 오늘 말씀드릴 이 코어 시스템 하나만 알면 99%는 결제하실 필요가 전혀 없습니다. 저 역시 처음에는 유명하다는 고가의 유료 툴들을 닥치는 대로 구독하고 밤을 새워가며 복잡한 코딩을 공부했습니다. 하지만 돌아온 것은 매달 빠져나가는 수십만 원의 청구서와 실무에 쓰지도 못하는 복잡한 코드뿐이었습니다. 오늘 영상 딱 10분만 집중해서 끝까지 따라오세요. 비싼 외주 없이 무료 도구만으로 자동으로 굴러가는 1인 무인 시스템의 모든 것을 가감 없이 투명하게 공개하겠습니다.",
            "sentences": [
                "시중에 넘쳐나는 수백만 원짜리 AI 강의, 사실 이거 하나만 알면 다 필요 없습니다.",
                "저 역시 고가의 툴들을 구독하고 밤새 코딩을 공부했지만 결과는 처참했습니다.",
                "돌아온 것은 매달 빠져나가는 수십만 원의 청구서와 복잡한 툴뿐이었습니다.",
                "오늘 영상 딱 10분만 집중해서 끝까지 따라오세요. 100% 무료 도구의 모든 것을 공개합니다."
            ],
            "bg_theme": "cyan"
        },
        {
            "id": 2,
            "title": "10분 완청 약속: 완벽한 1인 비즈니스 파이프라인",
            "subtitle": "잠자는 동안에도 고객을 응대하고 기획서를 작성하는 24/7 무인 자동화 대시보드",
            "script": f"오늘 여러분이 이 영상에서 가져가실 결과물은 단순한 이론이 아닙니다. 지금 보시는 화면처럼, 여러분이 잠을 자거나 본업에 집중하고 있는 동안에도 알아서 고객의 문의를 접수하고, Gemini AI가 맞춤형 제안서를 단 5초 만에 작성하며, 최종 보고서까지 고객에게 자동으로 발송하는 완벽한 100% 무인화 파이프라인입니다. 특히 영상 8분 지점에서는 오늘 소개할 자동화의 핵심인 프롬프트 체이닝 설계 비법을 화면을 통해 상세히 해설해 드릴 예정이니, 단 1초도 놓치지 마시고 채널 고정해 주시기 바랍니다. 준비되셨다면, 지금 바로 1막으로 출발하겠습니다.",
            "sentences": [
                "오늘 여러분이 얻어가실 결과물은 단순한 이론이 결코 아닙니다.",
                "잠을 자거나 본업에 집중하는 동안에도 고객 문의를 24시간 자동 접수합니다.",
                "Gemini AI가 맞춤형 제안서를 5초 만에 작성하고 최종 보고서까지 자동 발송합니다.",
                "영상 8분 지점에서 프롬프트 체이닝 설계 핵심 비법을 공개하니 채널 고정해 주세요!"
            ],
            "bg_theme": "cyan"
        },
        {
            "id": 3,
            "title": f"1막: 왜 99%는 {kw}에 실패하는가?",
            "subtitle": "초보자들이 가장 많이 빠지는 3대 치명적 착각과 고비용의 늪",
            "script": f"본격적인 실전 구축에 들어가기에 앞서, 왜 99%의 사람들이 {kw}에 야심 차게 도전했다가 포기하는지 그 근본적인 이유를 반드시 짚고 넘어가야 합니다. 첫 번째 착각은 바로 비싼 유료 툴을 많이 구독할수록 자동화가 잘 될 것이라는 환상입니다. 매달 수십만 원씩 나가는 툴들을 무리하게 엮어두면, 툴 하나만 에러가 발생해도 전체 시스템이 그대로 마비됩니다. 두 번째 착각은 전문 프로그래밍 언어를 배워야 한다는 강박입니다. 하지만 2026년 현재, 노코드 API와 웹훅 연동 기술은 이미 기존의 코딩을 완벽하게 대체했습니다.",
            "sentences": [
                f"왜 99%의 사람들은 {kw}에 도전했다가 중간에 포기하고 말까요?",
                "첫 번째 착각: 비싼 유료 툴을 많이 구독해야만 자동화가 완성된다는 환상입니다.",
                "여러 툴을 무리하게 엮어두면 하나만 에러가 나도 전체 시스템이 마비됩니다.",
                "두 번째 착각: 코딩을 배워야 한다는 강박이지만, 노코드 API가 이미 대체했습니다."
            ],
            "bg_theme": "amber"
        },
        {
            "id": 4,
            "title": "1막: 도구가 아니라 파이프라인의 연결 구조가 전부다",
            "subtitle": "단순한 1회성 질문에서 벗어나 데이터가 스스로 흐르는 자동 배관망 구축",
            "script": "세 번째이자 가장 치명적인 착각은 바로 챗GPT 대화창에 매번 사람이 직접 들어가서 질문을 던지는 수작업입니다. 많은 분들이 이것을 AI 자동화라고 부르지만, 냉정하게 말해 그것은 그저 질문하는 대상을 포털 검색에서 AI로 바꾼 것에 불과합니다. 진정한 자동화란 질문을 사람이 직접 던지는 것이 아닙니다. 고객이 폼을 작성하는 순간, 그 원천 데이터가 파이프라인을 타고 스스로 AI에게 전달되어 결과물이 생성되는 일련의 연결 구조를 만드는 것입니다. 즉, 개별 도구가 중요한 것이 아니라 도구와 도구를 잇는 배관 시스템이 핵심입니다.",
            "sentences": [
                "가장 치명적인 착각은 챗GPT 대화창에 매번 직접 질문을 입력하는 수작업입니다.",
                "그것은 자동화가 아니라 질문 대상을 포털 검색에서 AI로 바꾼 것에 불과합니다.",
                "진정한 자동화란 사람이 개입하지 않아도 데이터가 스스로 흐르는 연결 구조입니다.",
                "개별 도구의 화려함이 중요한 것이 아니라, 도구를 잇는 배관 시스템이 핵심입니다."
            ],
            "bg_theme": "amber"
        },
        {
            "id": 5,
            "title": "1막: 상위 1%가 절대 가르쳐주지 않는 무료 인프라의 위력",
            "subtitle": "구글 스프레드시트와 Gemini 무료 API로 완성하는 0원 인프라",
            "script": "그렇다면 상위 1%의 사업가들은 왜 이런 진실을 대중에게 쉬쉬할까요? 바로 수백만 원짜리 컨설팅 강의와 유료 솔루션을 계속 판매해야 하기 때문입니다. 하지만 오늘 제가 단언컨대, 구글에서 전 세계인에게 무료로 제공하는 스프레드시트와 구글 폼, 그리고 월 수천만 토큰까지 무료 할당량을 제공하는 구글 Gemini API만 활용해도 월 매출 수천만 원 규모의 1인 비즈니스를 빈틈없이 지탱할 수 있습니다. 1원도 결제할 필요가 없는 이 강력한 무료 인프라의 3단계 실전 연결법을 이제 2막에서 직접 하나씩 보여드리겠습니다.",
            "sentences": [
                "상위 1% 사업가들은 왜 이런 간단하고 강력한 진실을 대중에게 쉬쉬할까요?",
                "바로 수백만 원짜리 유료 강의와 고가의 솔루션을 판매해야 하기 때문입니다.",
                "구글 스프레드시트와 무료 Gemini API만으로도 수천만 원 비즈니스를 지탱할 수 있습니다.",
                "단 1원도 들지 않는 강력한 무료 인프라의 3단계 실전 연결법을 지금 공개합니다."
            ],
            "bg_theme": "amber"
        },
        {
            "id": 6,
            "title": "2막: [1단계] 무인 데이터 수집기 구축",
            "subtitle": "고객 문의를 0.1초 만에 데이터베이스로 정돈하는 자동 클렌징 수식",
            "script": "자, 이제 본격적인 2막 실전 시연입니다. 첫 번째 단계는 무인 데이터 수집기의 구축입니다. 고객이 웹사이트나 블로그에서 문의 양식을 제출하면, 그 내용이 0.1초 만에 구글 스프레드시트의 행으로 깔끔하게 정돈되어 실시간으로 쌓이도록 만듭니다. 이때 가장 중요한 핵심 노하우는 고객이 입력한 주관식 텍스트에서 불필요한 공백을 제거하고 핵심 요구사항 키워드만 정규화하는 데이터 클렌징 수식을 걸어두는 것입니다. 이 간단한 1단계 세팅 하나만으로도 뒤이어 전달될 AI의 응답 품질이 300% 이상 비약적으로 향상됩니다.",
            "sentences": [
                "본격적인 2막 실전 시연, 첫 번째 단계는 무인 데이터 수집기 구축입니다.",
                "고객이 문의 양식을 제출하면 0.1초 만에 구글 시트 행으로 깔끔하게 정리됩니다.",
                "불필요한 공백을 제거하고 핵심 키워드만 추출하는 데이터 클렌징 수식이 핵심입니다.",
                "이 간단한 세팅 하나만으로도 뒤이어 생성될 AI 결과물의 품질이 300% 급상승합니다."
            ],
            "bg_theme": "purple"
        },
        {
            "id": 7,
            "title": "2막: [2단계] Gemini API 무료 연동 및 시스템 지침 주입",
            "subtitle": "구글 AI 스튜디오 무료 키 발급 및 할루시네이션 0% 시스템 지침 설계",
            "script": "두 번째 단계는 수집된 데이터의 두뇌 역할을 담당할 Gemini API의 연동입니다. 구글 AI 스튜디오에 접속하시면 클릭 세 번 만에 개인 API 키를 무료로 즉시 발급받을 수 있습니다. 여기서 상위 1%의 비결이 등장하는데요. 단순히 AI에게 답변을 요구하는 것이 아니라, 시스템 지침에 엄격한 출력 형식과 비즈니스 페르소나를 사전에 주입하는 것입니다. 예를 들어 마크다운 테이블 규격과 3단 구조 보고서 형식을 고정해 두면, 할루시네이션 없이 100% 실무에 즉시 쓸 수 있는 고품질 기획서가 출력됩니다.",
            "sentences": [
                "두 번째 단계는 전체 파이프라인의 두뇌 역할을 담당할 Gemini API의 연동입니다.",
                "구글 AI 스튜디오에서 클릭 세 번이면 개인 무료 API 키를 즉시 발급받을 수 있습니다.",
                "시스템 지침에 엄격한 출력 형식과 전문 비즈니스 페르소나를 사전에 주입합니다.",
                "마크다운 테이블과 3단 보고서 형식을 지정하면 할루시네이션 0%의 결과가 나옵니다."
            ],
            "bg_theme": "purple"
        },
        {
            "id": 8,
            "title": "2막: [3단계] 자동화 웹훅 트리거 및 5초 리포트 생성",
            "subtitle": "데이터 발생 즉시 AI를 자동 호출하여 맞춤형 기획안을 즉각 산출하는 시스템",
            "script": "세 번째 단계는 수집된 데이터와 두뇌를 실시간으로 이어주는 웹훅 트리거 연결입니다. 무료 웹훅 서비스를 활용하여, 구글 시트에 새 데이터가 입력되는 이벤트가 발생하는 즉시 Gemini API를 백그라운드에서 호출하도록 설정합니다. 보시는 것처럼 사람이 아무것도 누르지 않아도, 고객의 문의가 들어오자마자 5초 만에 2,000자 분량의 심층 비즈니스 컨설팅 리포트가 생성되어 시트의 결과 칼럼에 자동으로 기입됩니다. 이 모든 정교한 과정이 일어나는 데 걸리는 시간은 단 5초에 불과합니다.",
            "sentences": [
                "세 번째 단계는 수집된 데이터와 두뇌를 실시간으로 이어주는 웹훅 트리거 연결입니다.",
                "구글 시트에 새 데이터가 입력되는 즉시 Gemini API를 백그라운드에서 자동 호출합니다.",
                "사람이 아무것도 누르지 않아도 단 5초 만에 2,000자 분량의 심층 리포트가 생성됩니다.",
                "모든 결과물은 구글 스프레드시트의 지정된 결과 칼럼에 실시간으로 자동 기입됩니다."
            ],
            "bg_theme": "purple"
        },
        {
            "id": 9,
            "title": "2막: [실전 검증] 라이브 테스트 및 365일 무결점 가동",
            "subtitle": "실제 라이브 테스트 시연 및 3회 자동 재시도 로직으로 365일 무중단 가동",
            "script": "지금 보시는 화면이 실제 라이브 테스트 화면입니다. 가상의 고객이 복잡한 프로젝트 기획 문의를 접수하자, 화면 오른쪽에서 실시간으로 데이터가 파싱되고 완벽한 16:9 규격 맞춤 기획안이 생성되는 모습을 생생하게 확인하실 수 있습니다. 만에 하나 인터넷 연결이 불안정하거나 API 응답이 지연되더라도, 자동 재시도 로직을 3회 설정해 두면 1년 365일 24시간 동안 단 한 번의 데이터 누락도 없이 무결점으로 작동합니다. 이것이 바로 여러분만의 충실한 24시간 디지털 직원이 탄생하는 순간입니다.",
            "sentences": [
                "지금 화면에 보시는 것이 실제 운영 중인 라이브 자동화 테스트 화면입니다.",
                "고객 문의 접수와 동시에 실시간 데이터 파싱 및 완벽한 기획안 생성이 이뤄집니다.",
                "3회 자동 재시도 로직을 탑재하여 네트워크 지연에도 단 한 건의 누락 없이 작동합니다.",
                "여러분이 잠자는 시간에도 쉬지 않고 일하는 충실한 24시간 디지털 직원이 완성됩니다."
            ],
            "bg_theme": "purple"
        },
        {
            "id": 10,
            "title": "3막: [8분 미드롤 돌파] 하루 2시간을 0초로 줄인 프롬프트 체이닝",
            "subtitle": "단일 프롬프트의 한계를 극복하고 대기업 기획실 수준으로 끌어올리는 비밀",
            "script": "오래 기다리셨습니다. 10분 영상의 클라이맥스, 3막의 핵심 비밀 치트키를 지금 공개합니다. 하루 2시간 이상 걸리던 분석과 작성 작업을 단 0초로 단축시킨 결정적 기술은 바로 프롬프트 체이닝입니다. 대부분의 초보자들은 하나의 프롬프트에 모든 요구사항을 다 쏟아붓고 엉성한 답변을 받지만, 고수들은 작업을 3단계로 정밀하게 쪼갭니다. 1차 분석 에이전트가 고객의 문제를 파악하고, 2차 기획 에이전트가 전략을 수립하며, 3차 카피라이터가 최종 문서를 다듬는 체인 구조를 설계하는 것입니다.",
            "sentences": [
                "오래 기다리셨습니다! 10분 영상의 클라이맥스, 3막의 핵심 비밀 치트키를 공개합니다.",
                "하루 2시간의 작업을 단 0초로 줄여준 결정적 기술은 바로 '프롬프트 체이닝'입니다.",
                "초보자들은 한 번에 모든 걸 질문하지만, 고수들은 작업을 3단계로 분업화합니다.",
                "1차 문제 분석 ➔ 2차 전략 수립 ➔ 3차 문서 완성으로 이어지는 바통 터치 시스템입니다."
            ],
            "bg_theme": "gold"
        },
        {
            "id": 11,
            "title": "3막: [원리 해설] 프롬프트 체이닝 구조와 핵심 작동 원리",
            "subtitle": "화면 속 3단계 분업화 프롬프트 설계 구조와 AI 에이전트 협업 분석",
            "script": "지금 화면에 표시해 드리는 구조가 바로 프롬프트 체이닝의 핵심입니다. 별도의 복잡한 템플릿을 찾아 헤매실 필요 없이, 화면에 보이는 것처럼 각 단계별로 AI의 역할을 분담해 주는 원리만 이해하시면 됩니다. 1단계에서 분석하고, 2단계에서 전략을 세우며, 3단계에서 최종 문서를 작성하도록 바통을 넘겨주는 구조입니다. 화면의 예시를 잘 눈여겨보시고 여러분의 아이디어에 맞게 응용해 보시기 바랍니다.",
            "sentences": [
                "지금 화면에 보이는 구조가 바로 프롬프트 체이닝의 핵심 작동 원리입니다.",
                "별도의 템플릿 파일 없이도 화면 속 3단계 역할 분담 구조만 이해하시면 충분합니다.",
                "1단계 분석 ➔ 2단계 전략 ➔ 3단계 문서 작성으로 이어지는 바통 터치 방식입니다.",
                "화면에 나오는 구조를 참고하여 여러분만의 독창적인 자동화에 응용해 보세요."
            ],
            "bg_theme": "gold"
        },
        {
            "id": 12,
            "title": f"3막: 평범한 직장인이 월 500만원 파이프라인으로 확장한 비결",
            "subtitle": "단순 업무 효율화를 넘어 실제 현금 흐름을 창출하는 3단계 비즈니스 모델",
            "script": f"그렇다면 이 시스템을 통해 평범한 직장인이 어떻게 퇴근 후 월 500만 원의 추가 수익을 만들었을까요? 비결은 단순한 내부 업무 자동화에서 멈추지 않고, 이 파이프라인을 크몽이나 숨고 같은 플랫폼의 맞춤형 자동 견적 서비스, 그리고 기업 대상 전문 리서치 자동 생성 솔루션으로 상품화했기 때문입니다. 내가 직접 시간을 쓰지 않아도 시스템이 가치를 만들어내기 때문에, 고객이 1명이든 100명이든 동일한 품질의 서비스를 즉각 공급하며 안정적인 수익 파이프라인을 완성할 수 있었습니다.",
            "sentences": [
                "평범한 직장인이 어떻게 퇴근 후 이 시스템으로 월 500만 원의 추가 수익을 만들었을까요?",
                "단순 업무 자동화에 그치지 않고, 자동 견적 서비스와 기업 맞춤 솔루션으로 상품화했습니다.",
                "내가 시간을 쓰지 않아도 시스템이 24시간 가치와 결과물을 자동으로 생산해 냅니다.",
                "고객이 100명으로 늘어나도 동일한 품질을 즉시 공급하며 안정적 수익을 창출합니다."
            ],
            "bg_theme": "gold"
        },
        {
            "id": 13,
            "title": "4막: 오늘 배운 10분 코어 시스템 3대 핵심 총정리",
            "subtitle": "비싼 툴 배제, 데이터 연결 구조 집중, 프롬프트 체이닝 3원칙",
            "script": "오늘 10분 동안 긴 호흡으로 쉼 없이 달려온 핵심 내용을 딱 3줄로 완벽히 요약해 드리겠습니다. 첫째, 비싼 유료 툴에 현혹되지 말고 구글 시트와 Gemini 무료 API라는 가장 강력한 무료 인프라를 활용할 것. 둘째, 단순 1회성 질문이 아닌 데이터가 스스로 흐르는 웹훅 파이프라인을 구축할 것. 셋째, 프롬프트 체이닝을 통해 1인 기업 수준을 뛰어넘는 고품질의 결과물을 자동 생성할 것. 이 세 가지만 기억하시면 여러분의 비즈니스는 완전히 새로워집니다.",
            "sentences": [
                "오늘 10분 동안 함께 살펴본 핵심 내용을 딱 3줄로 완벽하게 총정리합니다.",
                "첫째, 유료 툴에 현혹되지 말고 구글 시트와 Gemini 무료 API 무료 인프라를 활용할 것.",
                "둘째, 단순 질문이 아닌 데이터가 스스로 흐르는 웹훅 파이프라인을 구축할 것.",
                "셋째, 프롬프트 체이닝을 통해 대기업 수준의 고품질 결과물을 자동 생성할 것."
            ],
            "bg_theme": "emerald"
        },
        {
            "id": 14,
            "title": "4막: 액션 플랜 & 엔드스크린 추천 영상 연계",
            "subtitle": "오늘 밤 1시간 실천 과제 및 우측 상단 실전 수익화 5단계 연계 시청",
            "script": "오늘 영상을 시청하신 후 뒤로 미루지 마시고, 오늘 밤 딱 1시간만 투자해서 오늘 영상에서 보여드린 전체 시스템 연결 흐름을 머릿속으로 정리해 보세요. 오늘 파이프라인의 기초를 완성하셨다면, 이제 이 시스템에 실제 첫 유료 고객을 유치하는 구체적인 마케팅 5단계가 궁금하실 텐데요. 지금 화면 우측 상단에 뜨는 추천 영상에서 바로 이어지는 실전 수익화 전략을 상세히 다루었으니 지금 바로 클릭해서 이어서 시청해 보시기 바랍니다. 구독과 좋아요 부탁드리며, 시청해 주셔서 대단히 감사합니다.",
            "sentences": [
                "미루지 마시고 오늘 배운 전체 시스템 연결 흐름을 머릿속으로 차근차근 정리해 보세요.",
                "파이프라인을 구축했다면, 이제 실제 첫 유료 고객을 모으는 마케팅이 필요합니다.",
                "화면 우측 상단에 뜨는 추천 영상에서 '실전 수익화 5단계'를 지금 바로 확인해 보세요!",
                "구독과 알림 설정 잊지 마시고, 10분 동안 끝까지 시청해 주셔서 진심으로 감사합니다!"
            ],
            "bg_theme": "emerald"
        }
    ]

# 비디오 렌더링 함수
async def render_video(topic, out_mp4):
    print("==============================================================")
    print(f"🎬 10분+ 16:9 비디오 클라우드 렌더링 시작: {topic['title']}")
    print("==============================================================")
    scenes = get_master_scenes(topic)
    scene_clips = []
    total_audio_sec = 0.0

    for s in scenes:
        sid = s["id"]
        sc_audio = os.path.join(TEMP_DIR, f"sc_{sid}.mp3")
        comm = edge_tts.Communicate(s["script"], "ko-KR-SunHiNeural", rate="-14%")
        await comm.save(sc_audio)
        dur = get_audio_duration(sc_audio)
        total_audio_sec += dur

        base_frame = draw_scene_frame(s, topic)
        sentences = s["sentences"]
        dur_per_sent = dur / max(1, len(sentences))

        concat_txt = os.path.join(TEMP_DIR, f"sc_{sid}_concat.txt")
        frame_paths = []
        with open(concat_txt, "w", encoding="utf-8") as f:
            for st_i, sent in enumerate(sentences):
                f_img = render_subtitle(base_frame, sent)
                f_path = os.path.join(TEMP_DIR, f"sc_{sid}_f{st_i}.png")
                f_img.save(f_path)
                frame_paths.append(f_path)
                clean_f = os.path.abspath(f_path).replace("\\", "/")
                f.write(f"file '{clean_f}'\n")
                f.write(f"duration {dur_per_sent:.3f}\n")
            if frame_paths:
                clean_last = os.path.abspath(frame_paths[-1]).replace("\\", "/")
                f.write(f"file '{clean_last}'\n")

        sc_video = os.path.join(TEMP_DIR, f"sc_{sid}_clip.mp4")
        cmd_enc = [
            FFMPEG_EXE, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-i", sc_audio,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-r", "24",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            sc_video
        ]
        subprocess.run(cmd_enc, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        scene_clips.append(sc_video)

    # 10분 돌파 보장 엔드스크린 씬
    if total_audio_sec < 618.0:
        needed_outro = 618.0 - total_audio_sec
        outro_frame_path = os.path.join(TEMP_DIR, "outro_endscreen.png")
        outro_base = draw_scene_frame(scenes[-1], topic)
        outro_frame = render_subtitle(outro_base, "👉 우측 상단 추천 영상을 클릭하여 '실전 고객 유치 5단계'를 이어서 시청하세요!")
        outro_frame.save(outro_frame_path)

        outro_clip = os.path.join(TEMP_DIR, "outro_clip.mp4")
        cmd_outro = [
            FFMPEG_EXE, "-y",
            "-loop", "1",
            "-i", outro_frame_path,
            "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-r", "24",
            "-t", f"{needed_outro:.2f}",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            outro_clip
        ]
        subprocess.run(cmd_outro, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        scene_clips.append(outro_clip)
        total_audio_sec += needed_outro

    master_concat = os.path.join(TEMP_DIR, "master_concat.txt")
    with open(master_concat, "w", encoding="utf-8") as f:
        for sc in scene_clips:
            clean_sc = os.path.abspath(sc).replace("\\", "/")
            f.write(f"file '{clean_sc}'\n")

    master_speech = os.path.join(TEMP_DIR, "master_speech.mp4")
    cmd_cat = [FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", master_concat, "-c", "copy", master_speech]
    subprocess.run(cmd_cat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    bgm_path = os.path.join(TEMP_DIR, "master_bgm.wav")
    generate_ambient_bgm(total_audio_sec + 5.0, bgm_path)

    print("🎧 앰비언트 BGM 오디오 믹싱 중...")
    cmd_final = [
        FFMPEG_EXE, "-y",
        "-i", master_speech,
        "-i", bgm_path,
        "-filter_complex", "[0:a]volume=1.0[v];[1:a]volume=0.12[b];[v][b]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        out_mp4
    ]
    subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    final_dur = get_audio_duration(out_mp4)
    print(f"✅ 비디오 렌더링 완료: {final_dur:.1f}초 ({final_dur/60:.1f}분)")
    return final_dur

# 유튜브 공식 API 전체공개(PUBLIC) 자동 업로드
def upload_to_youtube_public(video_path, thumb_path, topic):
    print("\n🚀 유튜브 Data API v3 '전체 공개(PUBLIC)' 업로드 시작...")
    
    # 환경변수 또는 로컬 토큰 파일 확인
    client_id = os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("YT_REFRESH_TOKEN")

    token_file = os.path.join(BASE_DIR, "youtube_token.json")
    if not (client_id and client_secret and refresh_token) and os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                tdata = json.load(f)
                client_id = tdata.get("client_id")
                client_secret = tdata.get("client_secret")
                refresh_token = tdata.get("refresh_token")
        except Exception:
            pass

    if not (client_id and client_secret and refresh_token):
        print("⚠️ [안내] 클라우드 무인 업로드를 위한 YouTube OAuth 토큰이 설정되지 않았습니다.")
        print("👉 'python get_youtube_token.py'를 최초 1회 실행하여 토큰을 발급받으세요.")
        return False

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )

        youtube = build("youtube", "v3", credentials=creds)

        desc = f"""{topic['title']}

📢 [시청 안내 공지]
본 영상은 AI 자동화 시스템의 핵심 원리와 흐름을 알기 쉽게 해설해 드리는 영상입니다.
별도의 원본 템플릿, 프롬프트 다운로드 파일, 소스 코드는 제공하지 않으니, 
영상 화면의 내용을 참고하여 시청해 주시기 바랍니다. 감사합니다!

"솔직히 말씀드리겠습니다. 시중에 파는 수백만 원짜리 AI 강의, 사실 오늘 말씀드릴 이 코어 시스템 하나만 알면 99%는 결제하실 필요가 없습니다."

⏱️ [10분 타임스탬프 목차]
00:00 골든 인트로 (The Hook & 10분 완청 약속)
00:50 24/7 무인 자동화 대시보드 프리뷰
01:36 1막: 왜 99%는 실패하는가?
02:23 도구가 아니라 '파이프라인 연결 구조'가 전부인 이유
03:09 상위 1%가 쉬쉬하는 0원 오픈소스 & 무료 API의 위력
03:53 2막: [실전 1단계] 구글 시트 & 폼 무인 데이터 수집기 구축
04:37 2막: [실전 2단계] Gemini API 무료 연동 및 시스템 지침 주입
05:22 2막: [실전 3단계] 자동화 웹훅 트리거 & 5초 생성
06:03 2막: [실전 검증] 라이브 테스트 시연 & 365일 무중단 예외 처리
06:45 3막: [8분 미드롤 돌파 치트키] 하루 2시간을 0초로 줄인 프롬프트 체이닝
07:30 3막: [핵심 원리] 상위 1% 프롬프트 체이닝 분업화 구조 해설
08:10 3막: 평범한 직장인이 월 500만원 파이프라인으로 확장한 비결
08:48 4막: 오늘 배운 10분 코어 시스템 3대 핵심 총정리
09:24 4막: 오늘 밤 1시간 실천 과제 & 추천 영상 (엔드스크린)

💡 [오늘의 3줄 핵심 요약]
1. 비싼 유료 툴에 현혹되지 말고 구글 시트 + Gemini 무료 API 인프라를 활용할 것
2. 사람이 직접 묻지 말고 데이터가 스스로 흐르는 웹훅 파이프라인을 구축할 것
3. 프롬프트 체이닝으로 3단계 분업화하여 대기업 기획실 수준의 퀄리티를 낼 것

구독과 좋아요, 알림 설정 부탁드립니다!
#AI자동화 #1인기업 #부업 #AI비즈니스 #노코드 #생산성
"""

        body = {
            "snippet": {
                "title": topic["title"],
                "description": desc,
                "tags": topic["tags"],
                "categoryId": "27"  # Howto & Style
            },
            "status": {
                "privacyStatus": "public",  # 전체 공개
                "selfDeclaredMadeForKids": False
            }
        }

        print("📤 유튜브에 비디오 스트림 전송 중 (전체 공개)...")
        media = MediaFileUpload(video_path, chunksize=1024*1024*4, resumable=True)
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        
        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                print(f"   진행률: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        print(f"🎉 유튜브 전체 공개 업로드 대성공! 영상 ID: {video_id}")
        print(f"🔗 유튜브 영상 바로보기: https://youtu.be/{video_id}")

        if os.path.exists(thumb_path):
            print("🖼️ 16:9 썸네일 등록 중...")
            youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb_path)).execute()
            print("✅ 썸네일 등록 완료!")

        return True
    except Exception as e:
        print(f"❌ 유튜브 API 업로드 실패: {e}")
        return False

# 메인 엔트리포인트
async def main():
    print("==================================================================")
    print("☁️ 24/7 클라우드 무인 유튜브 롱폼 자동화 엔진 가동")
    print(f"⏰ 현재 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================================")

    # 1시간마다 또는 스케줄마다 주제 순환
    hour_idx = datetime.datetime.now().hour % len(HOURLY_TOPICS)
    topic = HOURLY_TOPICS[hour_idx]
    print(f"📌 오늘의 클라우드 선정 주제: {topic['title']}")

    # 1. 썸네일 렌더링
    thumb_path = os.path.join(OUTPUT_DIR, "cloud_thumbnail.png")
    generate_thumbnail(topic, thumb_path)
    print("✅ 16:9 썸네일 생성 완료")

    # 2. 비디오 렌더링 (10분+)
    video_path = os.path.join(OUTPUT_DIR, "cloud_video_10min.mp4")
    dur = await render_video(topic, video_path)

    # 3. 유튜브 전체 공개 업로드 실행
    success = upload_to_youtube_public(video_path, thumb_path, topic)

    # 4. 실행 로그 저장
    log_file = os.path.join(LOGS_DIR, "cloud_publish_log.json")
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
        "duration_sec": dur,
        "video": video_path,
        "thumbnail": thumb_path,
        "upload_status": "PUBLIC_SUCCESS" if success else "NEEDS_AUTH"
    })

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print("==================================================================")
    print("🏁 클라우드 무인 발행 작업 종료")
    print("==================================================================")

if __name__ == "__main__":
    asyncio.run(main())
