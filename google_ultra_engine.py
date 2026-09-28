# -*- coding: utf-8 -*-
"""
Google AI Ultra 통합 엔진 (Shared Engine for all 5 projects)
============================================================
- Gemini 3.1 Pro Preview:  최상위 대본/기획/리서치 생성 (Ultra 전용)
- Gemini 3 Pro Image:      최상위 AI 이미지 생성 (Nano Banana Pro)
- Veo 3.1:                 최상위 AI 비디오 클립 생성
- Gemini 3.8 Flash:        고속 텍스트 생성 (보조)
"""

import os
import sys
import time
import base64
import json
from pathlib import Path

# UTF-8 강제 설정
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google import genai
from google.genai import types

# .env에서 API 키 로드 시도
def _load_api_key():
    """여러 프로젝트의 .env에서 GEMINI_API_KEY를 탐색"""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    # 프로젝트 디렉토리들의 .env에서 탐색
    search_dirs = [
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent / "engineering-shorts-pipeline",
        Path(__file__).resolve().parent / "blog_auto",
        Path(__file__).resolve().parent / "timelayer_studio",
        Path(__file__).resolve().parent / "youtube_longform_generator",
    ]
    for d in search_dirs:
        env_file = d / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
    return ""

API_KEY = _load_api_key()
_client = None

def get_client():
    global _client
    if _client is None:
        if not API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        _client = genai.Client(api_key=API_KEY)
    return _client


# ──────────────────────────────────────────────────────────────
# 1. 텍스트 생성 (대본/기획/리서치)
# ──────────────────────────────────────────────────────────────
MODEL_MAPPINGS = {
    "gemini-2.5-flash": "gemini-3.8-flash",
    "gemini-2.5-pro": "gemini-3.1-pro-preview",
    "gemini-2.5-flash-lite": "gemini-3.1-flash-lite",
    "gemini-flash": "gemini-3.8-flash",
    "gemini-pro": "gemini-3.1-pro-preview",
}

def resolve_model_name(model: str) -> str:
    """구버전 모델명을 최신 Google AI Ultra 지원 모델명으로 안전하게 매핑"""
    return MODEL_MAPPINGS.get(model, model)

def generate_text(
    prompt: str,
    system_instruction: str = "",
    model: str = "gemini-3.1-pro-preview",
    temperature: float = 0.9,
    response_mime_type: str = None,
    max_output_tokens: int = 8192,
) -> str:
    """Gemini 최상위 모델 텍스트 생성 (기본: 3.1 Pro Preview, 폴백: 3.8 Flash)"""
    client = get_client()
    target_model = resolve_model_name(model)
    
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    if system_instruction:
        config.system_instruction = system_instruction
    if response_mime_type:
        config.response_mime_type = response_mime_type

    try:
        response = client.models.generate_content(
            model=target_model,
            contents=prompt,
            config=config,
        )
        return response.text
    except Exception as e:
        # 404나 특정 모델 에러 시 최신 플래그십 폴백
        print(f"⚠️ 모델 {target_model} 호출 실패 ({e}). gemini-3.8-flash로 자동 전환합니다.")
        fallback_model = "gemini-3.8-flash" if target_model != "gemini-3.8-flash" else "gemini-3.1-pro-preview"
        response = client.models.generate_content(
            model=fallback_model,
            contents=prompt,
            config=config,
        )
        return response.text


def generate_json(
    prompt: str,
    system_instruction: str = "",
    model: str = "gemini-3.1-pro-preview",
) -> dict:
    """Gemini JSON 모드 생성"""
    text = generate_text(
        prompt=prompt,
        system_instruction=system_instruction,
        model=model,
        response_mime_type="application/json",
    )
    # JSON 파싱 (마크다운 코드블록 제거)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text)


# ──────────────────────────────────────────────────────────────
# 2. 이미지 생성 (Gemini Flash Image)
# ──────────────────────────────────────────────────────────────
def generate_image(
    prompt: str,
    output_path: str | Path,
    model: str = "gemini-3-pro-image",
    width: int = 1920,
    height: int = 1080,
    retry: int = 3,
) -> Path:
    """
    Gemini Pro Image (최상위) 모델을 사용하여 최고 품질 이미지를 생성합니다.
    Google AI Ultra 계정의 높은 할당량을 활용합니다.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    client = get_client()

    # 고품질 프롬프트 강화
    enhanced_prompt = (
        f"Generate a high-quality photorealistic image: {prompt}. "
        f"Ultra-detailed, 8K resolution, cinematic lighting, professional photography."
    )

    for attempt in range(retry):
        try:
            response = client.models.generate_content(
                model=model,
                contents=enhanced_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            # 응답에서 이미지 데이터 추출
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    img_data = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    # 리사이즈 (필요시)
                    try:
                        from PIL import Image
                        with Image.open(output_path) as im:
                            if im.size != (width, height):
                                im_resized = im.resize((width, height), Image.Resampling.LANCZOS)
                                im_resized.save(output_path, quality=95)
                    except ImportError:
                        pass
                    print(f"✅ [Google Ultra] 이미지 생성 성공: {output_path.name}")
                    return output_path

            print(f"⚠️ 이미지 데이터가 응답에 없음 (시도 {attempt+1}/{retry})")
        except Exception as e:
            wait_sec = (attempt + 1) * 3
            print(f"⚠️ 이미지 생성 실패 ({e}) - {wait_sec}초 후 재시도 ({attempt+1}/{retry})")
            time.sleep(wait_sec)

    # 최종 실패 시 프로시저럴 폴백
    print(f"⚠️ Google Ultra 이미지 생성 최종 실패, 로컬 폴백 생성: {output_path.name}")
    _create_fallback_image(output_path, prompt[:60], width, height)
    return output_path


def _create_fallback_image(output_path: Path, title: str, width: int, height: int):
    """오프라인 시 대체 이미지 생성"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (width, height), color=(15, 20, 30))
        draw = ImageDraw.Draw(img)
        # 그라데이션 배경
        for y in range(height):
            ratio = y / height
            r = int(10 + ratio * 25)
            g = int(15 + ratio * 40)
            b = int(25 + ratio * 55)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        # 타이틀
        try:
            font = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 36)
        except Exception:
            font = ImageFont.load_default()
        draw.text((width // 2, height // 2), title, fill=(200, 210, 230), font=font, anchor="mm")
        img.save(output_path, quality=95)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────
# 3. 비디오 클립 생성 (Veo 3.1)
# ──────────────────────────────────────────────────────────────
def generate_video_clip(
    prompt: str,
    output_path: str | Path,
    model: str = "veo-3.1-generate-preview",
    duration_sec: int = 8,
    aspect_ratio: str = "16:9",
    max_wait_sec: int = 300,
) -> Path | None:
    """
    Veo 3.1을 사용하여 AI 비디오 클립을 생성합니다.
    Google AI Ultra 계정에서만 사용 가능합니다.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    client = get_client()

    enhanced_prompt = (
        f"{prompt}. "
        f"Cinematic quality, smooth camera movement, professional documentary style, 4K."
    )

    try:
        print(f"🎬 [Veo 3.1] 비디오 클립 생성 시작 ({duration_sec}초, {aspect_ratio})...")
        operation = client.models.generate_videos(
            model=model,
            prompt=enhanced_prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=1,
            ),
        )

        # 비동기 완료 대기
        elapsed = 0
        poll_interval = 10
        while not operation.done:
            time.sleep(poll_interval)
            elapsed += poll_interval
            if elapsed > max_wait_sec:
                print(f"⚠️ Veo 타임아웃 ({max_wait_sec}초 초과)")
                return None
            operation = client.operations.get(operation)
            if elapsed % 30 == 0:
                print(f"   ⏳ Veo 렌더링 중... ({elapsed}초 경과)")

        # 결과 비디오 저장
        if operation.response and operation.response.generated_videos:
            video = operation.response.generated_videos[0]
            if hasattr(video, "video") and video.video:
                video_data = client.files.download(file=video.video)
                with open(output_path, "wb") as f:
                    f.write(video_data)
                print(f"✅ [Veo 3.1] 비디오 클립 생성 완료: {output_path.name}")
                return output_path

        print(f"⚠️ Veo 응답에 비디오 데이터 없음")
        return None

    except Exception as e:
        print(f"⚠️ Veo 비디오 생성 실패: {e}")
        return None


# ──────────────────────────────────────────────────────────────
# 4. 유틸리티
# ──────────────────────────────────────────────────────────────
def check_ultra_status():
    """Google AI Ultra 최상위 모델 연결 상태 확인"""
    try:
        client = get_client()
        # 최상위 모델 텍스트 생성 테스트
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents="Say 'Ultra OK' in Korean",
        )
        print(f"✅ Gemini 3.1 Pro Preview (최상위 텍스트): {response.text.strip()}")
        
        # 사용 가능한 최상위 모델 목록
        top_models = {
            "📝 텍스트": "gemini-3.1-pro-preview",
            "🖼️ 이미지": "gemini-3-pro-image",
            "🎬 비디오": "veo-3.1-generate-preview",
            "⚡ 고속":   "gemini-3.8-flash",
        }
        print("\n  📋 적용된 최상위 모델:")
        for role, model_name in top_models.items():
            print(f"    {role}: {model_name}")
        
        return True
    except Exception as e:
        print(f"❌ Google AI Ultra 연결 실패: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  🔑 Google AI Ultra 최상위 모델 엔진 상태 점검")
    print("=" * 60)
    print(f"  API Key: ...{API_KEY[-6:]}" if API_KEY else "  API Key: NOT SET")
    check_ultra_status()

