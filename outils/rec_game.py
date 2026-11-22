"""Filme une partie d'un jeu « à cartes » de BLIZ. usage: rec_game.py "<nom du jeu>" <nb_cartes> <secondes_par_carte> outdir
Épicé, questions ex/sexe désactivées, prénoms fictifs. Écrit outdir/start.txt = seconde où la 1re carte apparaît."""
import sys, time
from playwright.sync_api import sync_playwright
game, n, per, out = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':430,'height':932},is_mobile=True,has_touch=True,record_video_dir=out,record_video_size={'width':430,'height':932})
    pg=ctx.new_page(); T0=time.time()
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    el=pg.get_by_text(game).first; el.scroll_into_view_if_needed(); el.click(); pg.wait_for_timeout(800)
    if pg.locator('input:visible').count():
        for nm in ['Léa','Yanis','Inès','Noah']:
            pg.locator('input:visible').first.fill(nm); pg.get_by_text('Ajouter').first.click(); pg.wait_for_timeout(200)
        pg.locator('button:visible').last.click(); pg.wait_for_timeout(800)
    for t in ['Épicé','Désactivées',"C'est parti",'Je connais']:
        if pg.get_by_text(t).count(): pg.get_by_text(t).first.click(); pg.wait_for_timeout(450)
    pg.wait_for_timeout(500); start=time.time()-T0
    for i in range(n):
        pg.wait_for_timeout(int(per*1000))
        if i<n-1: pg.get_by_text('Suivante').first.click()
    pg.wait_for_timeout(500); ctx.close(); b.close()
open(out+'/start.txt','w').write(f'{start:.2f}'); print('start',round(start,2))
