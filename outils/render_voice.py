"""Render a BLIZ « J'ai déjà / J'ai jamais » video from a JSON content file.
usage: python3 render.py content.json out.mp4
"""
import json, sys, subprocess, wave, struct, math, random
from playwright.sync_api import sync_playwright

FPS = 30
raw = open(sys.argv[1], encoding="utf-8").read().replace("« ", "«\u00a0").replace(" »", "\u00a0»").replace(" ?", "\u00a0?")
content = json.loads(raw)
out = sys.argv[2]

WORD_GAP = 0.07
import os, re, tempfile
import numpy as np
VOICE = "/home/claude/voices/fr-siwis-medium.onnx"
TMP = tempfile.mkdtemp()
_n = [0]
def tts(text):
    if NOVOICE:
        d=max(0.9,len(text)/16.0); return np.zeros(int(d*22050),dtype=np.float32), d
    """Synthesise text, return (samples float32 @22050, seconds)."""
    clean = re.sub(r"[«»👇👍👎]", "", text).replace(" ", " ")
    clean = re.sub(r"\btel\b", "téléphone", clean)
    _n[0] += 1
    path = f"{TMP}/v{_n[0]}.wav"
    subprocess.run(["python3", "-m", "piper", "-m", VOICE, "--length-scale", "0.74",
                    "--noise-scale", "0.6", "-f", path], input=clean.encode(), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a, len(a) / 22050
NOVOICE = bool(content.get("novoice"))
voice_clips = []   # (start_time, samples)
LEAD = 0.15
scenes, events, t = [], [], 0.0

def add(scene, dur):
    global t
    scene["start"], scene["end"] = t, t + dur
    scenes.append(scene)
    t += dur

# intro
idur = 0


items = content["items"][:7]
for n, (main, punch) in enumerate(items, 1):
    words = main.split(" ")
    v, S = tts(f"{main}... {punch} !")
    frac = len(main) / (len(main) + len(punch))
    speak_main = S * frac
    gap = min(WORD_GAP * 1.6, speak_main / max(1, len(words)))
    wordAt = [LEAD + k * gap for k in range(len(words))]
    if n == 1:
        wordAt = [-1.0] * len(words)  # visible dès la 1re image
    boxAt = LEAD + speak_main + 0.05
    btnAt = max(boxAt + 0.3, LEAD + S - 0.1)
    voice_clips.append((t + LEAD, v))
    EMO = [["😂","💀","😳"],["🫣","😭","🤣"],["😅","👀","💀"],["🤡","😂","😬"],["😳","🙈","😂"]]
    QUIPS = ["Avoue !", "Classique !", "Menteur !", "Tout le monde !", "Sérieux ?", "Oh non...", "Grillé !", "Pas toi ?"]
    if n % 2 == 0:
        qv, qd = tts(random.Random(n * 7 + len(main)).choice(QUIPS))
        voice_clips.append((t + btnAt + 0.15, qv))
    add({"talkStart": LEAD, "talkEnd": LEAD + S, "mood": "sus" if n % 3 == 0 else "laugh", "emos": EMO[n % len(EMO)], "type": "q", "words": words, "box": punch, "wordAt": wordAt, "boxAt": boxAt,
         "btnAt": btnAt, "barAt": btnAt + 0.1, "n": n}, btnAt + 1.35)

ov, odur = tts(content["outro_q"] + " " + content["outro_cta"])
voice_clips.append((t + 0.3, ov))
add({"type": "outro", "words": [], "box": None, "wordAt": [], "boxAt": 0, "btnAt": None,
     "barAt": None, "n": None, "q": content["outro_q"], "cta": content["outro_cta"],
     "tag": "Un seul tel pour toute la bande", "talkStart": 0.3, "talkEnd": 0.3 + odur}, max(3.4, odur + 1.0))

total = t
for s in scenes:
    for a in s["wordAt"]:
        events.append((s["start"] + a, "pop"))
    if s.get("box"):
        events.append((s["start"] + s["boxAt"], "ding"))
        events.append((s["start"] + s["boxAt"] + 0.05, "whoosh"))
    if s.get("btnAt") is not None:
        events.append((s["start"] + s["btnAt"], "whoosh"))
    if s["type"] == "outro":
        events.append((s["start"], "ding"))

# ---- audio (synthesised, royalty-free) ----
SR = 44100
buf = [0.0] * int((total + 0.5) * SR)
def mix(start, samples):
    i0 = int(start * SR)
    for i, v in enumerate(samples):
        if i0 + i < len(buf):
            buf[i0 + i] += v
def pop():
    n = int(0.06 * SR); f0 = random.uniform(650, 850)
    return [0.35 * math.sin(2 * math.pi * (f0 + 900 * (1 - i / n)) * i / SR) * (1 - i / n) ** 3 for i in range(n)]
def ding():
    n = int(0.45 * SR)
    return [0.28 * (math.sin(2 * math.pi * 1318 * i / SR) + 0.5 * math.sin(2 * math.pi * 1976 * i / SR)) * math.exp(-i / (0.09 * SR)) for i in range(n)]
def whoosh():
    n = int(0.25 * SR); r = random.Random(1)
    return [0.12 * r.uniform(-1, 1) * math.sin(math.pi * i / n) for i in range(n)]
for at, kind in events:
    mix(at, {"pop": pop, "ding": ding, "whoosh": whoosh}[kind]())
sfx = np.array(buf, dtype=np.float32) * 0.45
if NOVOICE:
    src=open('/home/claude/bliz/make_ad.py').read()
    mus=src[src.index('# musique douce'):src.index("with wave.open('/tmp/music.wav'")]
    _ns={'dur':total}; exec('import numpy as np\n'+mus,_ns)
    m=_ns['a']/np.abs(_ns['a']).max()*0.35
    sfx[:min(len(sfx),len(m))]+=m[:min(len(sfx),len(m))]
mixbuf = sfx.copy()
for st, a in voice_clips:
    up = np.interp(np.arange(0, len(a), 0.5), np.arange(len(a)), a)  # 22050 -> 44100
    up = up / (np.abs(up).max() + 1e-9) * 0.9
    i0 = int(st * SR); i1 = min(len(mixbuf), i0 + len(up))
    mixbuf[i0:i1] += up[: i1 - i0]
mixbuf = mixbuf / max(1.0, np.abs(mixbuf).max() / 0.97)
wav = out.replace(".mp4", "_mix.wav")
with wave.open(wav, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mixbuf * 32000).astype(np.int16).tobytes())

# ---- video ----
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                       "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file:///home/claude/bliz/template.html")
    pg.evaluate("document.fonts.ready")
    pg.evaluate("tl => setup(tl)", {"scenes": scenes, "total": len(items), "hook": content.get("hook", "Plus de 4/7 = t'es grillé 💀"), "btnA": content.get("btnA"), "btnB": content.get("btnB"), "nostore": content.get("nostore", False)})
    nframes = int(total * FPS)
    for f in range(nframes):
        pg.evaluate("t => render(t)", f / FPS)
        ff.stdin.write(pg.screenshot(type="jpeg", quality=93))
    b.close()
ff.stdin.close(); ff.wait()
print(f"{out}: {total:.1f}s, {nframes} frames")
