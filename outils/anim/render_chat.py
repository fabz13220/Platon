"""Mini-histoire animée façon conversation de groupe -> mp4. usage: render_chat.py story.json out.mp4"""
import json,sys,subprocess,re
from playwright.sync_api import sync_playwright
sys.path.insert(0,'/home/claude/bliz')
st=json.load(open(sys.argv[1],encoding='utf-8')); out=sys.argv[2]; FPS=30
t=0.6; cols={'Inès':'#ff9f0a','Léa':'#ff375f','Noah':'#30d158','Yanis':'#64d2ff'}
for m in st['msgs']:
    t+=0.9 if m.get('me') else 1.1
    t+=len(m['txt'])/38.0
    m['at']=round(t,2); m['c']=cols.get(m.get('who',''),'#bf5af2')
endAt=t+1.6; total=endAt+3.2; st['endAt']=endAt
# musique douce reprise de make_ad.py
src=open('/home/claude/bliz/make_ad.py').read()
mus=src[src.index('# musique douce'):src.index("with wave.open('/tmp/music.wav'")]
ns={'dur':total}; exec('import numpy as np, wave\n'+mus,ns)
import numpy as np, wave
a=ns['a']
for m in st['msgs']:  # petit "pop" de notification à chaque message
    s=int(m['at']*44100); L=int(0.08*44100); x=np.arange(L)/44100
    if s+L<len(a): a[s:s+L]+=0.25*np.sin(2*np.pi*(1200 if m.get('me') else 900)*x)*np.exp(-x/0.03)
a=a/np.abs(a).max()*0.6
with wave.open('/tmp/chat.wav','w') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(44100);w.writeframes((a*32000).astype(np.int16).tobytes())
ff=subprocess.Popen(["ffmpeg","-v","error","-y","-f","image2pipe","-framerate",str(FPS),"-i","-","-i","/tmp/chat.wav","-c:v","libx264","-preset","medium","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",out],stdin=subprocess.PIPE)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1080,'height':1920})
    pg.goto('file:///home/claude/bliz/anim/chat.html'); pg.evaluate('document.fonts.ready'); pg.evaluate('s=>setup(s)',st)
    for f in range(int(total*FPS)):
        pg.evaluate('t=>render(t)',f/FPS); ff.stdin.write(pg.screenshot(type='jpeg',quality=92))
    b.close()
ff.stdin.close(); ff.wait(); print(out, round(total,1),'s')
