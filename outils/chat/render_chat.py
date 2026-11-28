"""Format soigné « conversation » : python3 render_chat.py script.json out.mp4
beats : say/cap/glow/hl + ev:[{at, in|out|seen|typing|notif|head|shake, who, body, dur}] + duck/flash/end"""
import json,sys,os,wave,subprocess
import numpy as np
from playwright.sync_api import sync_playwright
FPS=30;SR=44100
S=json.load(open(sys.argv[1],encoding='utf-8'));out=sys.argv[2];total=S['beats'][-1]['t1']
ev=[]
for b in S['beats']:
    for e in b.get('ev',[]):e=dict(e);e['t']=b['t0']+e.pop('at',0);ev.append(e)
ev.sort(key=lambda e:e['t']);S['events']=ev
buf=np.zeros(int((total+0.5)*SR),dtype=np.float32);rng=np.random.default_rng(7)
def mix(at,a):
    i=int(at*SR);j=min(len(buf),i+len(a));buf[i:j]+=a[:j-i]
def tone(f0,f1,d,amp,dec):
    n=int(d*SR);t=np.arange(n)/SR;ph=2*np.pi*np.cumsum(np.linspace(f0,f1,n))/SR;return amp*np.sin(ph)*np.exp(-t/dec)
def buzz(d,amp):
    n=int(d*SR);t=np.arange(n)/SR;x=np.sign(np.sin(2*np.pi*165*t))*0.5+np.sin(2*np.pi*82*t);env=np.minimum(1,np.minimum(t,d-t)/0.01);return amp*x*env
for e in ev:
    if e.get('out'):mix(e['t'],tone(500,1100,0.09,0.35,0.04))
    if e.get('in'):mix(e['t'],tone(880,880,0.12,0.25,0.05));mix(e['t']+0.08,tone(1320,1320,0.16,0.22,0.06))
    if e.get('notif'):mix(e['t'],buzz(0.16,0.22));mix(e['t']+0.24,buzz(0.16,0.22))
    if e.get('shake'):mix(e['t'],tone(110,38,0.8,0.85,0.25))
    if e.get('seen'):mix(e['t'],tone(2000,2000,0.03,0.12,0.01))
for b in S['beats']:
    if b.get('flash'):mix(b['t0'],tone(120,40,0.7,0.6,0.2))
src=open('/home/claude/bliz/make_ad.py').read();mus=src[src.index('# musique douce'):src.index("with wave.open('/tmp/music.wav'")]
ns={'dur':total};exec('import numpy as np\n'+mus,ns);m=ns['a']/np.abs(ns['a']).max()*S.get('music',0.14)
g=np.ones(len(m))
for b in S['beats']:
    if b.get('duck'):
        i,j=int(b['t0']*SR),int(b['t1']*SR);g[i:j]=0.0
g=np.convolve(g,np.ones(int(0.15*SR))/int(0.15*SR),'same')
L=min(len(buf),len(m));buf[:L]+=(m*g)[:L]
if S.get('voice_wav'):
    with wave.open(S['voice_wav']) as w:
        v=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768;vr=w.getframerate()
    v=np.interp(np.arange(0,len(v),vr/SR),np.arange(len(v)),v);v=v/np.abs(v).max()*0.9;mix(S.get('voice_at',0),v)
buf/=max(1.0,np.abs(buf).max()/0.95)
wav='/tmp/chat_a.wav'
with wave.open(wav,'w') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((buf*32000).astype(np.int16).tobytes())
ff=subprocess.Popen(['ffmpeg','-v','error','-y','-f','image2pipe','-framerate',str(FPS),'-i','-','-i',wav,'-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',out],stdin=subprocess.PIPE)
with sync_playwright() as p:
    br=p.chromium.launch(executable_path=os.environ.get('PW_EXE') or None,args=['--allow-file-access-from-files'])
    pg=br.new_page(viewport={'width':1080,'height':1920})
    pg.goto('file://'+os.path.join(os.path.dirname(os.path.abspath(__file__)),'chat.html'))
    pg.evaluate('document.fonts.ready');pg.evaluate('s=>setup(s)',S)
    for f in range(int(total*FPS)):
        pg.evaluate('t=>render(t)',f/FPS);ff.stdin.write(pg.screenshot(type='jpeg',quality=92))
    br.close()
ff.stdin.close();ff.wait();print(out,round(total,1),'s')
