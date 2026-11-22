"""Filme une vraie partie de BLIZ (Qui pourrait, Épicé, sans questions sexe) -> app_rec/*.webm"""
from playwright.sync_api import sync_playwright
import sys, glob, os
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=__import__('os').environ.get('PW_EXE') or None)
    ctx=b.new_context(viewport={'width':430,'height':932},device_scale_factor=1,is_mobile=True,has_touch=True,
                      record_video_dir='app_rec',record_video_size={'width':430,'height':932})
    pg=ctx.new_page()
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    pg.get_by_text('Qui pourrait').first.click(); pg.wait_for_timeout(700)
    inp=pg.locator('input:visible').first
    for n in ['Léa','Yanis','Inès','Noah']:
        inp.fill(n); pg.get_by_text('Ajouter').first.click(); pg.wait_for_timeout(250)
    pg.locator('button:visible').last.click(); pg.wait_for_timeout(700)
    pg.get_by_text('Épicé').first.click(); pg.wait_for_timeout(300)
    pg.get_by_text('Désactivées').first.click(); pg.wait_for_timeout(300)
    pg.get_by_text("C'est parti").first.click(); pg.wait_for_timeout(1500)
    import time
    if pg.get_by_text('Je connais').count(): pg.get_by_text('Je connais').first.click(); pg.wait_for_timeout(600)
    t0=time.time()
    for i in range(4):
        pg.wait_for_timeout(1300)
        pg.get_by_text('3, 2, 1').first.click(force=True)
        pg.wait_for_timeout(2600)
        pg.get_by_text('Suivante').first.click()
    pg.wait_for_timeout(800)
    open('app_rec/t0.txt','w').write(str(t0))
    ctx.close(); b.close()
print(sorted(glob.glob('app_rec/*.webm'), key=os.path.getmtime)[-1])
