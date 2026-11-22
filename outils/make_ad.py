"""Pub BLIZ avec vraie partie filmée. usage: make_ad.py rec.webm start dur hook sous_titre out.mp4"""
import sys, subprocess, numpy as np, wave
from PIL import Image, ImageDraw
rec, start, dur, hook, sub, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
W,H=1080,1920; PW,PH=640,1387; X,Y=(W-PW)//2,360; R=56
m=Image.new('L',(PW,PH),0); ImageDraw.Draw(m).rounded_rectangle([0,0,PW-1,PH-1],R,fill=255); m.save('/tmp/mask.png')
bz=Image.new('RGBA',(PW+36,PH+36),(0,0,0,0)); ImageDraw.Draw(bz).rounded_rectangle([0,0,PW+35,PH+35],R+18,fill=(22,10,40,255)); bz.save('/tmp/bezel.png')
# musique douce synthétisée libre de droits : accords tenus + arpège léger, pas de basse carrée ni de bruit
SR=44100; n=int((dur+0.5)*SR); t=np.arange(n)/SR; a=np.zeros(n); bar=2.4
chords=[[220.0,261.6,329.6],[174.6,220.0,261.6],[261.6,329.6,392.0],[196.0,246.9,293.7]]  # Am F C G
for i in range(int(dur/bar)+1):
    s=int(i*bar*SR); L=min(n-s,int(bar*SR))
    if L<=0: break
    x=np.arange(L)/SR; env=np.minimum(1,x/0.3)*np.minimum(1,(bar-x)/0.4)
    for f in chords[i%4]:
        a[s:s+L]+=0.12*np.sin(2*np.pi*f*x)*env + 0.04*np.sin(2*np.pi*2*f*x)*env
    for k,f in enumerate(chords[i%4]*2):
        o=s+int(k*bar/6*SR); Lk=min(n-o,int(0.6*SR))
        if Lk<=0: continue
        y=np.arange(Lk)/SR
        a[o:o+Lk]+=0.10*np.sin(2*np.pi*f*2*y)*np.exp(-y/0.25)
    k0=int(s); Lkk=min(n-k0,int(0.25*SR)); y=np.arange(Lkk)/SR
    a[k0:k0+Lkk]+=0.25*np.sin(2*np.pi*(45+40*np.exp(-y/0.04))*y)*np.exp(-y/0.12)
a=a/np.abs(a).max()*0.55
with wave.open('/tmp/music.wav','w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a*32000).astype(np.int16).tobytes())
F='/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
def esc(s): return s.replace("\\","\\\\").replace(":","\\:").replace("'","\u2019")
fc=(f"gradients=s={W}x{H}:c0=0xff8a4c:c1=0xff2d8a:c2=0x6a2bff:duration={dur}:speed=0.04[bg];"
    f"[0:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,fps=30,scale={PW}:{PH},format=rgba[r];"
    f"[2:v]format=gray[mk];[r][mk]alphamerge[rr];"
    f"[bg][3:v]overlay={X-18}:{Y-18}[b1];[b1][rr]overlay={X}:{Y}:shortest=1[b2];"
    f"[b2]drawtext=fontfile={F}:text='{esc(hook)}':fontsize=64:fontcolor=white:x=(w-text_w)/2:y=140:shadowcolor=black@0.3:shadowy=5,"
    f"drawtext=fontfile={F}:text='{esc(sub)}':fontsize=40:fontcolor=white@0.95:x=(w-text_w)/2:y=240,"
    f"drawbox=x=170:y=1790:w=740:h=96:color=0x1a0b2e@1:t=fill,"
    f"drawtext=fontfile={F}:text='BLIZ  ·  Gratuit sur l’App Store':fontsize=42:fontcolor=0xffd23f:x=(w-text_w)/2:y=1819[out]")
subprocess.run(["ffmpeg","-v","error","-y","-i",rec,"-i","/tmp/music.wav","-i","/tmp/mask.png","-i","/tmp/bezel.png",
  "-filter_complex",fc,"-map","[out]","-map","1:a","-t",str(dur),"-c:v","libx264","-preset","medium","-crf","21","-pix_fmt","yuv420p",
  "-c:a","aac","-b:a","160k","-movflags","+faststart",out],check=True)
print(out)
