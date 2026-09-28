# -*- coding: utf-8 -*-
"""
Google AI Ultra & Edge-TTS 기반 다국어 자동 더빙 및 자막 통합 엔진
(Multilingual Audio Dubbing & Subtitle Engine)
- 지원 언어: 영어(en), 스페인어(es), 일본어(ja), 중국어(zh)
- 고품질 구어체 번역: Gemini 3.1 Pro Preview (Human-Touch 다큐 스타일)
- 원어민 성우 음성: Edge-TTS Neural Voices
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# UTF-8 출력 보장
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import edge_tts
from pathlib import Path

# Google Ultra 엔진 연동
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import google_ultra_engine
    ULTRA_AVAILABLE = True
except ImportError:
    ULTRA_AVAILABLE = False

VOICE_MAP = {
    "en": "en-US-ChristopherNeural",   # 미국 내셔널지오그래픽 다큐 남성 톤
    "es": "es-ES-AlvaroNeural",        # 스페인/남미 다큐 중후한 남성 톤
    "ja": "ja-JP-KeitaNeural",         # 일본 NHK 다큐 남성 톤
    "zh": "zh-CN-YunxiNeural",         # 중국 다큐 남성 톤
}

LANG_NAMES = {
    "en": "영어 (English)",
    "es": "스페인어 (Spanish)",
    "ja": "일본어 (Japanese)",
    "zh": "중국어 (Chinese)"
}

class MultilingualDubbingEngine:
    def __init__(self):
        self.ultra = google_ultra_engine if ULTRA_AVAILABLE else None

    def translate_metadata(self, title: str, description: str) -> dict:
        """
        유튜브 동영상 제목과 핵심 설명을 영어, 스페인어, 일본어로 현지화 번역
        YouTube Data API v3 'localizations' 규격에 맞춤 반환
        """
        if not self.ultra:
            return {}

        prompt = f"""
다음 유튜브 한국어 다큐멘터리 제목과 설명을 영어(en), 스페인어(es), 일본어(ja)로 현지화 번역하십시오.
단순 번역이 아닌, 해외 유튜브 시청자들의 클릭률(CTR)과 호기심을 극대화하는 자연스러운 다큐멘터리 스타일로 작성하십시오.

[원문 제목]
{title}

[원문 설명 요약]
{description[:800]}

다음 JSON 규격으로만 응답하십시오:
{{
  "en": {{
    "title": "영어 제목 (100자 이내)",
    "description": "영어 설명문"
  }},
  "es": {{
    "title": "스페인어 제목 (100자 이내)",
    "description": "스페인어 설명문"
  }},
  "ja": {{
    "title": "일본어 제목 (100자 이내)",
    "description": "일본어 설명문"
  }}
}}
"""
        try:
            res = self.ultra.generate_json(
                prompt=prompt,
                system_instruction="You are a professional multilingual media localization producer for National Geographic and BBC documentaries.",
                model="gemini-3.1-pro-preview"
            )
            return res
        except Exception as e:
            print(f"⚠️ 다국어 메타데이터 번역 실패 ({e})")
            return {}

    def translate_script_scenes(self, scenes: list, target_lang: str) -> list:
        """
        각 씬의 한국어 내레이션을 대상 언어로 자연스럽게 번역
        """
        if not self.ultra:
            return scenes

        lang_name = LANG_NAMES.get(target_lang, target_lang)
        print(f"🌐 [{lang_name}] {len(scenes)}개 씬 다큐멘터리 대본 번역 중...")

        # 배치 번역 요청
        scene_inputs = []
        for idx, sc in enumerate(scenes):
            scene_inputs.append({
                "id": sc.get("id", idx + 1),
                "text": sc.get("narration") or sc.get("script", "")
            })

        prompt = f"""
다음은 롱폼 다큐멘터리의 각 장면별 한국어 내레이션입니다.
이 내레이션들을 {lang_name}로 자연스럽고 생생한 구어체 다큐멘터리 스타일로 번역해 주십시오.
원문의 감정, 호흡, 훅을 그대로 살려 원어민 시청자가 몰입할 수 있도록 번역하십시오.

[한국어 내레이션 목록]
{json.dumps(scene_inputs, ensure_ascii=False, indent=2)}

다음 JSON 배열 규격으로만 응답하십시오:
[
  {{"id": 1, "translated_text": "번역된 내레이션"}},
  ...
]
"""
        try:
            translated_list = self.ultra.generate_json(
                prompt=prompt,
                system_instruction="You are an award-winning voiceover localization scriptwriter.",
                model="gemini-3.1-pro-preview"
            )
            # 매핑
            trans_dict = {item["id"]: item["translated_text"] for item in translated_list if "id" in item and "translated_text" in item}
            
            result_scenes = []
            for idx, sc in enumerate(scenes):
                sc_id = sc.get("id", idx + 1)
                new_sc = dict(sc)
                if sc_id in trans_dict:
                    new_sc["translated_text"] = trans_dict[sc_id]
                else:
                    new_sc["translated_text"] = sc.get("narration") or sc.get("script", "")
                result_scenes.append(new_sc)
            return result_scenes
        except Exception as e:
            print(f"⚠️ 다국어 대본 번역 실패 ({e})")
            return scenes

    async def render_dubbed_audio_async(self, text: str, voice: str, output_path: Path):
        """Edge-TTS 비동기 음성 합성"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tts = edge_tts.Communicate(text, voice)
        await tts.save(str(output_path))

    def generate_full_dubbing(self, scenes: list, target_lang: str, output_audio_path: Path) -> Path:
        """
        특정 언어로 번역된 대본 전체를 하나의 고품질 더빙 오디오 트랙으로 합성
        """
        voice = VOICE_MAP.get(target_lang, "en-US-ChristopherNeural")
        lang_name = LANG_NAMES.get(target_lang, target_lang)
        print(f"🎙️ [{lang_name}] 원어민 성우({voice}) 오디오 더빙 트랙 렌더링 중...")

        full_text = " ".join(sc.get("translated_text", sc.get("narration", "")) for sc in scenes)
        asyncio.run(self.render_dubbed_audio_async(full_text, voice, output_audio_path))
        print(f"✅ [{lang_name}] 더빙 오디오 트랙 생성 완료: {output_audio_path.name} ({output_audio_path.stat().st_size / 1024:.1f} KB)")
        return output_audio_path

    def generate_multilingual_srt(self, original_srt_cues: list, translated_scenes: list, output_srt_path: Path) -> Path:
        """
        타임코드를 유지한 다국어 SRT 자막 파일 생성
        """
        output_srt_path.parent.mkdir(parents=True, exist_ok=True)
        # 타임스탬프 포맷
        def fmt_ts(sec):
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            ms = int((sec - int(sec)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        with open(output_srt_path, "w", encoding="utf-8") as f:
            for idx, sc in enumerate(translated_scenes, 1):
                # 씬 타임스탬프 또는 cues 기반
                start = sc.get("start", (idx - 1) * 25.0)
                end = sc.get("end", start + sc.get("duration", 25.0))
                text = sc.get("translated_text", "")
                f.write(f"{idx}\n")
                f.write(f"{fmt_ts(start)} --> {fmt_ts(end)}\n")
                f.write(f"{text}\n\n")

        print(f"✅ 다국어 SRT 자막 생성 완료: {output_srt_path.name}")
        return output_srt_path
