"""Montage « vraie appli » : python3 render_clip.py script.json out.mp4"""
import json,sys,os,wave,subprocess,tempfile,re
import numpy as np
from playwright.sync_api import sync_playwright
FPS=30;SR=44100
S=json.load(open(sys.argv[1],encoding='utf-8'));out=sys.argv[2];total=S['beats'][-1]['t1']
TMP=tempfile.mkdtemp()
subprocess.run(['ffmpeg','-v','error','-i',S['src'],'-vf','fps=30,scale=800:-1','-q:v','3',TMP+'/f%05d.jpg'],check=True)
def frame_for(t):
    b=next((b for b in S['beats'] if b['t0']<=t<b['t1']),S['beats'][-1])
    if 'clip' not in b:return None
    a,z=b['clip'];D=b['t1']-b['t0'];st=a+(t-b['t0'])*min(1.0,(z-a)/D)
    return f"file://{TMP}/f{int(st*FPS)+1:05d}.jpg"
buf=np.zeros(int((total+0.5)*SR),dtype=np.float32);rng=np.random.default_rng(5)
def mix(at,a):
    i=int(at*SR);j=min(len(buf),i+len(a));buf[i:j]+=a[:j-i]
def noise(d,amp):
    n=int(d*SR);x=np.convolve(rng.uniform(-1,1,n),np.ones(8)/8,'same');return amp*x*np.sin(np.linspace(0,np.pi,n))
def tone(f0,f1,d,amp,dec):
    n=int(d*SR);t=np.arange(n)/SR;ph=2*np.pi*np.cumsum(np.linspace(f0,f1,n))/SR;return amp*np.sin(ph)*np.exp(-t/dec)
for b in S['beats']:
    mix(b['t0'],noise(0.2,0.12))
    if b.get('flash'):mix(b['t0'],tone(120,40,0.7,0.8,0.2))
if S.get('voice'):
    import soundfile  # noqa
src=open('/home/claude/bliz/make_ad.py').read();mus=src[src.index('# musique douce'):src.index("with wave.open('/tmp/music.wav'")]
ns={'dur':total};exec('import numpy as np\n'+mus,ns);m=ns['a']/np.abs(ns['a']).max()*S.get('music',0.32)
buf[:min(len(buf),len(m))]+=m[:min(len(buf),len(m))]
if S.get('voice_wav'):
    with wave.open(S['voice_wav']) as w:
        v=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768;vr=w.getframerate()
    v=np.interp(np.arange(0,len(v),vr/SR),np.arange(len(v)),v);v=v/np.abs(v).max()*0.9;mix(S.get('voice_at',0),v)
buf/=max(1.0,np.abs(buf).max()/0.95)
wav=TMP+'/a.wav'
with wave.open(wav,'w') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((buf*32000).astype(np.int16).tobytes())
ff=subprocess.Popen(['ffmpeg','-v','error','-y','-f','image2pipe','-framerate',str(FPS),'-i','-','-i',wav,'-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',out],stdin=subprocess.PIPE)
with sync_playwright() as p:
    br=p.chromium.launch(executable_path=os.environ.get('PW_EXE') or None,args=['--allow-file-access-from-files'])
    pg=br.new_page(viewport={'width':1080,'height':1920})
    pg.goto('file://'+os.path.join(os.path.dirname(os.path.abspath(__file__)),'clip.html'))
    pg.evaluate('document.fonts.ready');pg.evaluate('s=>setup(s)',S)
    for f in range(int(total*FPS)):
        t=f/FPS;pg.evaluate('([t,s])=>render(t,s)',[t,frame_for(t)]);pg.wait_for_function('()=>{const i=document.getElementById("im");return !i.getAttribute("src")||i.complete}')
        ff.stdin.write(pg.screenshot(type='jpeg',quality=92))
    br.close()
ff.stdin.close();ff.wait();print(out,round(total,1),'s')
