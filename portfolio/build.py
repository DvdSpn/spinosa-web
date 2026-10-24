# Genera la versione anteprima (immagini incorporate) e il sito da pubblicare (immagini come file)
import base64, os, re
src = open('src.html').read()
IMGS = {'__BURGER__':'burger.jpg','__EMIBI__':'emibi.jpg','__DAVIDE__':'davide.jpg','__DEMO__':'demo.jpg'}
art, dep = src, src
for k, f in IMGS.items():
    if k in src:
        mime = 'image/jpeg'
        art = art.replace(k, f'data:{mime};base64,' + base64.b64encode(open('img/'+f,'rb').read()).decode())
        dep = dep.replace(k, 'img/'+f)
open('anteprima.html','w').write(art)
i, j = dep.index('<style>'), dep.index('</style>') + 8
doc = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       + dep[:j] + '\n<link rel="icon" href="favicon.svg">\n</head>\n<body>\n' + dep[j:] + '\n</body>\n</html>\n')
os.makedirs('../sito/img', exist_ok=True)
open('../sito/index.html','w').write(doc)
for f in IMGS.values():
    if os.path.exists('img/'+f): open('../sito/img/'+f,'wb').write(open('img/'+f,'rb').read())
print('ok')
