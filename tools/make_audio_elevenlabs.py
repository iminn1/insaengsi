#!/usr/bin/env python3
"""
ElevenLabs 로 시 전문과 날짜별 구절 낭독 MP3 생성 → audio/eleven/

준비:
  pip install requests
  export ELEVENLABS_API_KEY=sk_...        (ElevenLabs 프로필 → API Keys)

사용 (저장소 루트에서):
  python3 tools/make_audio_elevenlabs.py --voice <VOICE_ID> --sample   # 첫 문단만 생성해 들어보기 (약 150자)
  python3 tools/make_audio_elevenlabs.py --voice <VOICE_ID>            # 전체 생성 (약 3,600자)

옵션:
  --model eleven_multilingual_v2 (기본) | eleven_v3 | eleven_turbo_v2_5
  --speed 0.9 (0.7~1.2, 기본 0.9 = 조금 느리게)
  --stability 0.6  --style 0.15
"""
import argparse, json, os, subprocess, sys, pathlib, time
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "audio" / "eleven"
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"

def load_program():
    js = (ROOT / "days.js").read_text(encoding="utf-8")
    out = subprocess.run(["node", "-e", "globalThis.window=globalThis;" + js + ";console.log(JSON.stringify(window.PROGRAM))"],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)

def tts(text, path, a, key):
    body = {
        "text": text,
        "model_id": a.model,
        "voice_settings": {"stability": a.stability, "similarity_boost": 0.8, "style": a.style, "use_speaker_boost": True, "speed": a.speed},
    }
    for attempt in range(3):
        r = requests.post(API.format(voice=a.voice), headers={"xi-api-key": key, "Content-Type": "application/json"}, json=body, timeout=180)
        if r.status_code == 200:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(r.content)
            print(f"  wrote {path.relative_to(ROOT)} ({len(r.content)//1024} KB, {len(text)}자)")
            return
        print(f"  ! {r.status_code}: {r.text[:200]}  (재시도 {attempt+1}/3)")
        time.sleep(3)
    sys.exit("생성 실패")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True, help="ElevenLabs Voice ID")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--speed", type=float, default=0.9)
    ap.add_argument("--stability", type=float, default=0.6)
    ap.add_argument("--style", type=float, default=0.15)
    ap.add_argument("--sample", action="store_true")
    a = ap.parse_args()
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY 환경변수가 필요합니다.")
    P = load_program()
    PAUSE = ' <break time="1.2s" /> '   # 문단 사이 쉼
    if a.sample:
        tts(P["poem"][0] + PAUSE + P["poem"][1], OUT / "sample.mp3", a, key)
        print("sample 완료 → audio/eleven/sample.mp3 를 들어보세요")
        return
    full = P["poemTitle"] + "." + PAUSE + P["author"] + "." + PAUSE + PAUSE.join(P["poem"])
    total = len(full)
    jobs = [(full, OUT / "full.mp3")]
    for d in P["days"]:
        if d.get("full") or not d.get("text"):
            continue
        jobs.append((d["text"], OUT / f"day-{d['day']:02d}.mp3"))
        total += len(d["text"])
    print(f"총 {len(jobs)}개 파일, 약 {total}자 (ElevenLabs 크레딧 소모량)")
    for text, path in jobs:
        tts(text, path, a, key)
    print("done")

if __name__ == "__main__":
    main()
