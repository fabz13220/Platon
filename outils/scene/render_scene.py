"""Mini-scène BLIZ : python3 render_scene.py script.json out.mp4"""
import json,sys,os,math,random,wave,subprocess
import numpy as np
from playwright.sync_api import sync_playwright
FPS=30;SR=44100
S=json.load(open(sys.argv[1],encoding='utf-8'));out=sys.argv[2]
total=S['beats'][-1]['t1']
buf=np.zeros(int((total+0.5)*SR),dtype=np.float32)
def mix(at,a,g=1.0):
    i=int(at*SR);j=min(len(buf),i+len(a));buf[i:j]+=g*a[:j-i]
def tone(f0,f1,d,amp,dec):
    n=int(d*SR);t=np.arange(n)/SR;f=np.linspace(f0,f1,n);ph=2*np.pi*np.cumsum(f)/SR
    return amp*np.sin(ph)*np.exp(-t/dec)
rng=np.random.default_rng(3)
def noise(d,amp):
    n=int(d*SR);e=np.sin(np.linspace(0,np.pi,n));x=rng.uniform(-1,1,n)
    x=np.convolve(x,np.ones(6)/6,'same');return amp*x*e
for b in S['beats']:
    mix(b['t0'],noise(0.22,0.18))                       # whoosh à chaque changement
    if b.get('cap'):
        toks=__import__('re').findall(r'\*[^*]+\*|\S+',b['cap'])
        for k,w in enumerate(toks):
            hl=w.startswith('*')
            mix(b['t0']+0.05+k*b.get('gap',0.2),tone(900 if hl else 620,300,0.07,0.32 if hl else 0.2,0.03))
    if b.get('big'):
        seg=(b['t1']-b['t0'])/len(b['big'])
        for k in range(len(b['big'])):mix(b['t0']+k*seg,tone(1200 if k<len(b['big'])-1 else 1600,1100,0.12,0.3,0.05))
    if b.get('flash'):
        mix(b['t0'],tone(140,45,0.6,0.7,0.18));mix(b['t0'],noise(0.3,0.25))
    if b.get('point') is not None:
        for j in range(3):mix(b['t0']+0.15+j*0.12,tone(500+j*150,900+j*150,0.09,0.25,0.04))
# musique douce (même recette validée que make_ad.py), plus présente
src=open('/home/claude/bliz/make_ad.py').read()
mus=src[src.index('# musique douce'):src.index("with wave.open('/tmp/music.wav'")]
ns={'dur':total};exec('import numpy as np\n'+mus,ns);m=ns['a']/np.abs(ns['a']).max()*0.30
buf[:min(len(buf),len(m))]+=m[:min(len(buf),len(m))]
buf/=max(1.0,np.abs(buf).max()/0.95)
wav=out.replace('.mp4','_a.wav')
with wave.open(wav,'w') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((buf*32000).astype(np.int16).tobytes())
ff=subprocess.Popen(['ffmpeg','-v','error','-y','-f','image2pipe','-framerate',str(FPS),'-i','-','-i',wav,'-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',out],stdin=subprocess.PIPE)
with sync_playwright() as p:
    br=p.chromium.launch(executable_path=os.environ.get('PW_EXE') or None)
    pg=br.new_page(viewport={'width':1080,'height':1920})
    pg.goto('file://'+os.path.abspath(os.path.join(os.path.dirname(__file__),'scene.html')))
    pg.evaluate('document.fonts.ready');pg.evaluate('s=>setup(s)',S)
    n=int(total*FPS)
    for f in range(n):
        pg.evaluate('t=>render(t)',f/FPS);ff.stdin.write(pg.screenshot(type='jpeg',quality=92))
    br.close()
ff.stdin.close();ff.wait();os.remove(wav);print(out,round(total,1),'s')
