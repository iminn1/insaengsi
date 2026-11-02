#!/usr/bin/env python3
"""
days.js 의 시 전문과 날짜별 구절을 고품질 신경망 음성(MP3)으로 생성합니다.

사용법 (저장소 루트에서):
  pip install edge-tts
  python3 tools/make_audio.py            # 두 음성 모두 생성
  python3 tools/make_audio.py --sample   # 첫 문단만 두 음성으로 생성 (비교용)

출력:
  audio/sunhi/full.mp3, audio/sunhi/day-02.mp3 … day-15.mp3   (여성)
  audio/injoon/full.mp3, audio/injoon/day-02.mp3 … day-15.mp3 (남성)
"""
import asyncio, json, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOICES = {"sunhi": "ko-KR-SunHiNeural", "injoon": "ko-KR-InJoonNeural"}
RATE = "-12%"   # 묵상용으로 조금 느리게
PAUSE = " … "   # 문단 사이 짧은 쉼 (TTS가 쉼표/말줄임에서 숨을 고름)

def load_program():
    js = (ROOT / "days.js").read_text(encoding="utf-8")
    out = subprocess.run(["node", "-e", "globalThis.window=globalThis;" + js + ";console.log(JSON.stringify(window.PROGRAM))"],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)

async def synth(text, voice, path):
    import edge_tts
    path.parent.mkdir(parents=True, exist_ok=True)
    com = edge_tts.Communicate(text, voice, rate=RATE)
    await com.save(str(path))
    print("  wrote", path.relative_to(ROOT), f"({path.stat().st_size//1024} KB)")

async def main():
    sample = "--sample" in sys.argv
    P = load_program()
    jobs = []
    full_text = P["poemTitle"] + "." + PAUSE + P["author"] + "." + PAUSE + PAUSE + PAUSE.join(P["poem"])
    for key, voice in VOICES.items():
        d = ROOT / "audio" / key
        if sample:
            jobs.append(synth(P["poem"][0], voice, d / "sample.mp3"))
            continue
        jobs.append(synth(full_text, voice, d / "full.mp3"))
        for day in P["days"]:
            if day.get("full") or not day.get("text"):
                continue
            jobs.append(synth(day["text"], voice, d / f"day-{day['day']:02d}.mp3"))
    # 서버 부담을 줄이기 위해 3개씩 순차 실행
    for i in range(0, len(jobs), 3):
        await asyncio.gather(*jobs[i:i+3])
    print("done")

if __name__ == "__main__":
    asyncio.run(main())
