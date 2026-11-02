#!/usr/bin/env python3
"""
배경음악(원곡 앰비언트 패드) 합성 → audio/bgm.mp3 (끊김 없이 반복되는 루프).
의존: numpy, ffmpeg. 실행: python3 tools/make_bgm.py
다른 곡으로 바꾸려면 audio/bgm.mp3 만 교체하면 됩니다 (앱은 loop 재생, 낮은 음량).
"""
import numpy as np, subprocess, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parent.parent
SR = 44100
CHORD_SEC = 10.0
# D major 계열의 느린 진행 (주파수 Hz) — 저음 + 중음 + 고음의 열린 보이싱
def n(name):
    names = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}
    p, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[p] + (o - 4) * 12 - 9) / 12)
PROG = [
    ['D2', 'A3', 'F#4', 'C#5', 'E5'],   # Dmaj9
    ['B1', 'F#3', 'D4', 'A4', 'C#5'],   # Bm9
    ['G2', 'D3', 'B3', 'F#4', 'A4'],    # Gmaj7(9)
    ['A2', 'E3', 'C#4', 'G4', 'B4'],    # A9
    ['F#2', 'C#3', 'A3', 'E4', 'G#4'],  # F#m9
    ['G2', 'D3', 'B3', 'F#4', 'E5'],    # Gmaj13
    ['D2', 'A3', 'F#4', 'C#5', 'E5'],   # Dmaj9
    ['A2', 'E3', 'C#4', 'G4', 'B4'],    # A9
]
total = CHORD_SEC * len(PROG)
t = np.arange(int(SR * total)) / SR
out = np.zeros_like(t)

def pad(freq, start, dur, amp):
    i0, i1 = int(start * SR), int((start + dur) * SR)
    tt = np.arange(i1 - i0) / SR
    # 두 개의 미세 디튠 톤 + 옥타브 위 희미하게 → 따뜻한 패드
    sig = (np.sin(2*np.pi*freq*tt) + np.sin(2*np.pi*freq*1.003*tt + 1.0)) * 0.5
    sig += 0.15 * np.sin(2*np.pi*freq*2*tt)
    # 느린 어택/릴리즈 (코드 겹침)
    env = np.minimum(1, tt / 3.0) * np.minimum(1, (dur - tt) / 3.0)
    env = np.clip(env, 0, 1) ** 1.5
    # 아주 느린 떨림
    env *= 1 + 0.06 * np.sin(2*np.pi*0.11*tt + freq)
    out[i0:i1] += amp * sig * env

for k, chord in enumerate(PROG):
    start = k * CHORD_SEC
    for j, name in enumerate(chord):
        f = n(name)
        amp = [0.35, 0.22, 0.18, 0.14, 0.10][j]
        # 코드 경계에서 2초 겹치게
        pad(f, start, min(CHORD_SEC + 2.0, total - start), amp)

# 루프 이음새: 끝 4초를 앞 4초와 크로스페이드
x = int(4 * SR)
fade = np.linspace(0, 1, x)
head = out[:x].copy()
out[-x:] = out[-x:] * (1 - fade) + head * fade
out = out[: len(out) - 0]
# 가벼운 로우패스(고음 부드럽게): 단순 이동평균
k = 24
out = np.convolve(out, np.ones(k) / k, mode='same')
out = out / np.max(np.abs(out)) * 0.6
pcm = (out * 32767).astype(np.int16)
raw = ROOT / 'audio' / 'bgm.raw'
raw.write_bytes(pcm.tobytes())
mp3 = ROOT / 'audio' / 'bgm.mp3'
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', str(raw),
                '-codec:a', 'libmp3lame', '-b:a', '80k', str(mp3)], check=True)
raw.unlink()
print('wrote', mp3, f'{mp3.stat().st_size//1024} KB, {total:.0f}s loop')
