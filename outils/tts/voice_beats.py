"""Génère la voix Kokoro phrase par phrase et cale les beats du JSON dessus.
usage: voice_beats.py in.json out.json out.wav  (chaque beat a "say")"""
import json,sys,numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
k=Kokoro('/home/claude/tts/kokoro.onnx','/home/claude/tts/voices.bin')
d=json.load(open(sys.argv[1]));SR=24000;t=0.15;parts=[np.zeros(int(0.15*SR),np.float32)]
for b in d['beats']:
    s,sr=k.create(b['say'],voice='ff_siwis',speed=d.get('speed',1.1),lang='fr-fr')
    s=np.trim_zeros(np.where(np.abs(s)<0.01,0,s))  if False else s
    dur=len(s)/sr;pause=b.get('pause',0.18)
    b['t0']=round(t,3);b['t1']=round(t+dur+pause,3)
    n=max(1,len((b.get('cap') or 'x').split()));b['gap']=round(min(0.3,dur*0.85/n),3)
    parts+= [s.astype(np.float32),np.zeros(int(pause*SR),np.float32)];t+=dur+pause
last=d['beats'][-1];last['t1']=round(t+0.8,3);parts.append(np.zeros(int(0.8*SR),np.float32))
a=np.concatenate(parts);sf.write(sys.argv[3],a,SR,subtype='PCM_16')
d['voice_wav']=sys.argv[3];d['voice_at']=0;d['music']=0.16
json.dump(d,open(sys.argv[2],'w'),ensure_ascii=False,indent=0);print('total',round(t+0.8,1))
