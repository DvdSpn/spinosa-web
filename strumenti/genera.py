#!/usr/bin/env python3
"""Genera la landing page di un ristorante da un file JSON.

Uso:
    python3 strumenti/genera.py clienti/demo-trattoria.json sito/demo/trattoria

Il file JSON contiene tutto quello che cambia da cliente a cliente: nome, contatti,
orari, menu, recensioni, foto e colori. Il risultato e' una cartella con index.html
(e le foto, se ci sono) pronta da pubblicare.

Campi facoltativi utili per le anteprime:
- "prezzo" di un piatto: se manca, il piatto compare senza prezzo.
- "solo_telefono": true quando il locale ha solo un numero fisso; il pulsante
  principale diventa "Chiama per prenotare" e sparisce WhatsApp.
- "etichetta_whatsapp" / "etichetta_breve": testo dei pulsanti WhatsApp (di base
  "Prenota su WhatsApp" e "Prenota"); per pizzerie e asporto usa "Ordina su WhatsApp" e "Ordina".
- "logo": percorso del file del logo (relativo al JSON); compare in alto nella
  sezione principale, su un riquadro chiaro, sopra il nome del locale.
"""
import html, json, os, shutil, sys, urllib.parse

GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
E = lambda s: html.escape(str(s), quote=True)

ICONE = {
    "tel": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    "wa": '<path d="M20.5 11.6a8.4 8.4 0 0 1-12.4 7.4L3.5 20.5l1.6-4.4A8.4 8.4 0 1 1 20.5 11.6z"/>',
    "map": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "star": '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
    "menu": '<path d="M5 6h14M5 12h14M5 18h10"/>',
}
def icona(n, cls="ico"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONE[n]}</svg>')

def euro(v):
    """Prezzo all'italiana: 14 -> "14 €", 6.5 -> "6,50 €"; un testo (es. "55 €/kg") resta com'e'."""
    if isinstance(v, str):
        return v
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return (s[:-3] if s.endswith(",00") else s) + " €"

def riassunto_orari(orari):
    chiusi = [GIORNI[i] for i in range(7) if not orari.get(str(i))]
    pranzo = any(any(int(f[0][:2]) < 16 for f in orari.get(str(i), [])) for i in range(7))
    cena = any(any(int(f[0][:2]) >= 17 for f in orari.get(str(i), [])) for i in range(7))
    parti = []
    if pranzo and cena: parti.append("Pranzo e cena")
    elif pranzo: parti.append("Solo pranzo")
    elif cena: parti.append("Solo cena")
    if len(chiusi) == 1: parti.append(("chiuso la " if chiusi[0] == "Domenica" else "chiuso il ") + chiusi[0].lower())
    elif chiusi: parti.append("chiuso " + ", ".join(c.lower() for c in chiusi))
    return " · ".join(parti)

def genera(d, out):
    c = d.get("colori", {})
    col = {
        "carta": c.get("carta", "#f6f4ee"), "inchiostro": c.get("inchiostro", "#1d211c"),
        "primario": c.get("primario", "#1f3a2e"), "su_primario": c.get("su_primario", "#f6f4ee"),
        "accento": c.get("accento", "#e0a43a"), "linea": c.get("linea", "#ddd8cb"),
        "tenue": c.get("tenue", "#5e6359"),
    }
    tel = d["telefono"].replace(" ", "")
    tel_link = "tel:" + (tel if tel.startswith("+") else "+39" + tel)
    wa_num = d.get("whatsapp", d["telefono"]).replace(" ", "").replace("+", "")
    if not wa_num.startswith("39"): wa_num = "39" + wa_num
    wa_link = "https://wa.me/" + wa_num + "?text=" + urllib.parse.quote(d.get("messaggio_whatsapp", f"Ciao, vorrei prenotare un tavolo da {d['nome']}"))
    maps_link = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(f"{d['nome']} {d['indirizzo']}")
    if d.get("maps_link"): maps_link = d["maps_link"]
    demo = d.get("demo")
    solo_tel = bool(d.get("solo_telefono"))
    et_wa = d.get("etichetta_whatsapp", "Prenota su WhatsApp")
    et_breve = d.get("etichetta_breve", "Prenota")

    # Pulsanti: WhatsApp quando c'e' un cellulare, altrimenti la chiamata
    if solo_tel:
        azioni_hero = (f'<a class="btn btn-acc" href="{E(tel_link)}">{icona("tel")}Chiama per prenotare</a>'
                       f'<a class="btn btn-bordo" href="#menu">Vedi il menu</a>')
        barra_html = (f'<a href="#menu">{icona("menu")}Menu</a>'
                      f'<a class="princ" href="{E(tel_link)}">{icona("tel")}Prenota</a>'
                      f'<a href="{E(maps_link)}" target="_blank" rel="noopener">{icona("map")}Mappa</a>')
    else:
        azioni_hero = (f'<a class="btn btn-acc" href="{E(wa_link)}" target="_blank" rel="noopener">{icona("wa")}{E(et_wa)}</a>'
                       f'<a class="btn btn-bordo" href="{E(tel_link)}">{icona("tel")}Chiama</a>'
                       f'<a class="btn btn-bordo" href="#menu">Vedi il menu</a>')
        barra_html = (f'<a href="{E(tel_link)}">{icona("tel")}Chiama</a>'
                      f'<a class="princ" href="{E(wa_link)}" target="_blank" rel="noopener">{icona("wa")}{E(et_breve)}</a>'
                      f'<a href="{E(maps_link)}" target="_blank" rel="noopener">{icona("map")}Mappa</a>')

    # Lavagna dei piatti del giorno
    lavagna = ""
    if d.get("piatti_del_giorno"):
        righe = "".join(f'<li><span>{E(p["nome"])}</span><span class="prezzo">{E(euro(p["prezzo"]))}</span></li>' for p in d["piatti_del_giorno"])
        lavagna = f'''
  <section class="lavagna-sez" id="oggi" aria-labelledby="t-oggi">
    <div class="wrap">
      <div class="lavagna">
        <h2 id="t-oggi">Oggi in cucina</h2>
        <ul>{righe}</ul>
        <p class="nota-lavagna">{E(d.get("nota_lavagna", "Cambia ogni giorno, chiedi al tavolo."))}</p>
      </div>
    </div>
  </section>'''

    # Menu
    sezioni = []
    for s in d["menu"]:
        voci = []
        for v in s["piatti"]:
            desc = f'<p class="desc">{E(v["descrizione"])}</p>' if v.get("descrizione") else ""
            tag = "".join(f'<span class="tag">{E(t)}</span>' for t in v.get("etichette", []))
            prezzo = (f'<span class="punti" aria-hidden="true"></span><span class="prezzo">{E(euro(v["prezzo"]))}</span>'
                      if v.get("prezzo") is not None else "")
            voci.append(f'<li class="piatto"><div class="riga"><h4>{E(v["nome"])}</h4>{prezzo}</div>'
                        f'{desc}{tag and f"<div class=tags>{tag}</div>"}</li>')
        sezioni.append(f'<div class="portata"><h3>{E(s["nome"])}</h3><ul>{"".join(voci)}</ul></div>')
    note_menu = " · ".join(E(n) for n in d.get("note_menu", []))
    titolo_menu = d.get("titolo_menu", "Il menu")

    # Foto
    galleria = ""
    if d.get("foto"):
        figs = "".join(f'<figure><img src="foto/{E(os.path.basename(f["file"]))}" alt="{E(f["alt"])}" loading="lazy"></figure>' for f in d["foto"])
        galleria = f'''
  <section id="foto" aria-labelledby="t-foto">
    <div class="wrap"><h2 id="t-foto" class="tit">Il locale e i piatti</h2></div>
    <div class="galleria">{figs}</div>
  </section>'''

    # Recensioni
    recensioni = ""
    r = d.get("recensioni")
    if r:
        carte = "".join(
            f'<figure class="rec"><div class="stelle" aria-label="{q.get("stelle",5)} stelle su 5">{icona("star","st") * int(q.get("stelle",5))}</div>'
            f'<blockquote>{E(q["testo"])}</blockquote><figcaption>{E(q["autore"])}</figcaption></figure>' for q in r.get("elenco", []))
        sintesi = ""
        if r.get("voto"):
            sintesi = f'<p class="voto"><strong>{E(r["voto"])}</strong> su Google · {E(r["numero"])} recensioni</p>'
        avviso = f'<p class="avviso-demo">{E(r["avviso"])}</p>' if r.get("avviso") else ""
        griglia = f'<div class="recs">{carte}</div>' if carte else ""
        recensioni = f'''
  <section id="recensioni" aria-labelledby="t-rec">
    <div class="wrap">
      <h2 id="t-rec" class="tit">Cosa dicono di noi</h2>
      {sintesi}
      {griglia}
      {avviso}
      <a class="link" href="{E(r.get("link", maps_link))}" target="_blank" rel="noopener">Leggi tutte le recensioni su Google</a>
    </div>
  </section>'''

    # Orari
    orari = d["orari"]
    righe_orari = "".join(
        f'<tr data-g="{i}"><th scope="row">{GIORNI[i]}</th><td>{" · ".join(f"{a}–{b}" for a, b in orari.get(str(i), [])) or "Chiuso"}</td></tr>'
        for i in range(7))

    banda_demo = ""
    if demo:
        banda_demo = (f'<div class="banda-demo"><div class="wrap"><span>{E(demo["testo"])}</span>'
                      f'<a href="{E(demo["link"])}" target="_blank" rel="noopener">{E(demo["azione"])}</a></div></div>')
    robots = '<meta name="robots" content="noindex, nofollow">' if (demo or d.get("anteprima")) else '<meta name="robots" content="index, follow">'
    descrizione_meta = d.get("descrizione_meta", f'{d["nome"]} a {d["citta"]}: {d["sottotitolo"]}. Menu, orari e prenotazioni.')
    iniziale = d.get("iniziale", d["nome"].split()[-1][0])
    marchio = E(d["nome"])
    logo_hero = (f'<img class="logo-hero" src="{E(os.path.basename(d["logo"]))}" alt="Logo di {E(d["nome"])}">'
                 if d.get("logo") else "")

    pagina = f'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(d["nome"])} · {E(d["citta"])}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{E(descrizione_meta)}">
{robots}
<meta name="theme-color" content="{col["primario"]}">
<meta property="og:title" content="{E(d["nome"])}">
<meta property="og:description" content="{E(d["sottotitolo"])}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='{urllib.parse.quote(col["primario"])}'/%3E%3Ctext x='32' y='45' text-anchor='middle' font-family='Georgia,serif' font-size='36' fill='{urllib.parse.quote(col["accento"])}'%3E{E(iniziale)}%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Young+Serif&family=Albert+Sans:wght@400;500;600;700&family=Caveat:wght@500;700&display=swap">
<style>
/* Modello ristorante di Spinosa Web: una colonna, menu come carta stampata, azioni sempre a portata di pollice */
:root {{
  --carta: {col["carta"]}; --inchiostro: {col["inchiostro"]}; --tenue: {col["tenue"]}; --linea: {col["linea"]};
  --primario: {col["primario"]}; --su-primario: {col["su_primario"]}; --accento: {col["accento"]};
  --f-titoli: "Young Serif", Georgia, "Times New Roman", serif;
  --f-testo: "Albert Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --f-mano: "Caveat", "Segoe Print", "Bradley Hand", cursive;
  color-scheme: light;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{ margin: 0; background: var(--carta); color: var(--inchiostro); font: 400 17px/1.55 var(--f-testo); -webkit-font-smoothing: antialiased; }}
img {{ max-width: 100%; display: block; }}
a {{ color: inherit; }}
:focus-visible {{ outline: 3px solid var(--accento); outline-offset: 3px; border-radius: 6px; }}
.wrap {{ max-width: 980px; margin: 0 auto; padding-left: max(18px, env(safe-area-inset-left, 0px)); padding-right: max(18px, env(safe-area-inset-right, 0px)); }}
h1, h2, h3, h4 {{ margin: 0; text-wrap: balance; }}
p {{ margin: 0; }}
.tit {{ font: 400 clamp(1.9rem, 4.5vw, 2.6rem)/1.1 var(--f-titoli); margin-bottom: 26px; }}
.ico {{ width: 20px; height: 20px; flex: none; }}

.banda-demo {{ background: var(--inchiostro); color: var(--carta); font-size: 0.9rem; }}
.banda-demo .wrap {{ display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center; justify-content: center; padding-block: 9px; text-align: center; }}
.banda-demo a {{ color: var(--accento); font-weight: 600; }}

.testata {{ background: var(--primario); color: var(--su-primario); }}
.testata .wrap {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-block: 14px; }}
.marchio {{ font: 400 1.15rem/1 var(--f-titoli); text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }}
.logo-hero {{ width: clamp(110px, 28vw, 150px); height: auto; aspect-ratio: auto; background: #fff; padding: 10px; border-radius: 16px; box-shadow: 0 10px 24px -14px rgba(0,0,0,.5); }}
.stato {{ white-space: nowrap; display: inline-flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 600; padding: 6px 12px; border-radius: 999px; border: 1px solid color-mix(in srgb, var(--su-primario) 30%, transparent); }}
.stato::before {{ content: ""; width: 8px; height: 8px; border-radius: 50%; background: #9aa39a; }}
.stato.aperto::before {{ background: #5fd38a; box-shadow: 0 0 0 3px rgba(95,211,138,.25); }}
.stato.chiuso::before {{ background: #e07a6a; }}

.hero {{ background: var(--primario); color: var(--su-primario); padding-block: clamp(40px, 9vw, 96px) clamp(48px, 9vw, 104px); }}
.hero .wrap {{ display: grid; gap: 20px; }}
.zona {{ font-size: 0.82rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--accento); }}
.hero h1 {{ font: 400 clamp(2.6rem, 11vw, 6.4rem)/0.95 var(--f-titoli); letter-spacing: -0.01em; }}
.hero .sotto {{ font-size: clamp(1.1rem, 2.4vw, 1.3rem); max-width: 34ch; opacity: 0.9; }}
.azioni {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 6px; }}
.btn {{ display: inline-flex; align-items: center; gap: 9px; padding: 14px 20px; border-radius: 999px; font: 600 1rem/1 var(--f-testo); text-decoration: none; border: 1.5px solid transparent; }}
.btn-acc {{ background: var(--accento); color: var(--inchiostro); }}
.btn-bordo {{ border-color: color-mix(in srgb, var(--su-primario) 45%, transparent); color: var(--su-primario); }}
.btn-acc:hover {{ filter: brightness(1.05); }}
.btn-bordo:hover {{ background: color-mix(in srgb, var(--su-primario) 10%, transparent); }}
.info-rapida {{ font-size: 0.95rem; opacity: 0.8; }}

section {{ padding-block: clamp(52px, 8vw, 88px); }}
section + section {{ border-top: 1px solid var(--linea); }}
.lavagna-sez + section {{ border-top: 0; }}

.lavagna-sez {{ padding-block: 0; border: 0 !important; margin-top: -36px; }}
.lavagna {{ position: relative; background: #2b2f2b; color: #f1efe6; border-radius: 14px; padding: 26px 26px 22px; border: 10px solid #6b4e33;
  box-shadow: 0 22px 40px -26px rgba(0,0,0,.6); max-width: 560px; }}
.lavagna h2 {{ font: 700 2rem/1 var(--f-mano); color: var(--accento); margin-bottom: 12px; }}
.lavagna ul {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }}
.lavagna li {{ display: flex; justify-content: space-between; gap: 16px; font: 500 1.45rem/1.25 var(--f-mano); }}
.lavagna .prezzo {{ white-space: nowrap; }}
.nota-lavagna {{ margin-top: 12px; font: 500 1.1rem/1.2 var(--f-mano); opacity: 0.75; }}

.menu-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 380px), 1fr)); gap: 34px 56px; }}
.portata h3 {{ font: 400 1.5rem/1.2 var(--f-titoli); color: var(--primario); padding-bottom: 10px; margin-bottom: 6px; border-bottom: 2px solid var(--inchiostro); }}
.portata ul {{ list-style: none; margin: 0; padding: 0; }}
.piatto {{ padding-block: 13px; border-bottom: 1px solid var(--linea); }}
.riga {{ display: flex; align-items: baseline; gap: 10px; }}
.riga h4 {{ font: 600 1.05rem/1.3 var(--f-testo); }}
.punti {{ flex: 1; border-bottom: 2px dotted var(--linea); transform: translateY(-4px); min-width: 16px; }}
.prezzo {{ font-weight: 700; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.desc {{ color: var(--tenue); font-size: 0.95rem; margin-top: 3px; max-width: 46ch; }}
.tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 7px; }}
.tag {{ font-size: 0.75rem; font-weight: 600; letter-spacing: 0.04em; padding: 3px 9px; border-radius: 999px; background: color-mix(in srgb, var(--primario) 10%, transparent); color: var(--primario); }}
.note-menu {{ margin-top: 28px; color: var(--tenue); font-size: 0.92rem; }}

.galleria {{ display: flex; gap: 12px; overflow-x: auto; scroll-snap-type: x mandatory; padding-inline: max(18px, env(safe-area-inset-left, 0px)); padding-bottom: 8px; }}
.galleria figure {{ margin: 0; flex: 0 0 min(78vw, 340px); aspect-ratio: 4/5; border-radius: 14px; overflow: hidden; scroll-snap-align: start; }}
.galleria img {{ width: 100%; height: 100%; object-fit: cover; }}

.voto {{ margin: -12px 0 24px; color: var(--tenue); }}
.voto strong {{ color: var(--inchiostro); font-size: 1.3rem; }}
.recs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); gap: 16px; }}
.rec {{ margin: 0; background: #fff; border: 1px solid var(--linea); border-radius: 14px; padding: 20px; display: grid; gap: 10px; align-content: start; }}
.stelle {{ display: flex; gap: 2px; color: var(--accento); }}
.st {{ width: 17px; height: 17px; fill: currentColor; stroke: none; }}
.rec blockquote {{ margin: 0; font-size: 1rem; }}
.rec figcaption {{ color: var(--tenue); font-size: 0.88rem; }}
.avviso-demo {{ margin-top: 14px; font-size: 0.85rem; color: var(--tenue); }}
.link {{ display: inline-block; margin-top: 18px; font-weight: 600; text-underline-offset: 4px; }}

.dove {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr)); gap: 32px 56px; }}
.indirizzo {{ font-size: 1.15rem; margin-bottom: 18px; }}
.dove .btn {{ border-color: var(--inchiostro); color: var(--inchiostro); }}
.dove .btn:hover {{ background: #fff; }}
.contatti {{ display: flex; flex-wrap: wrap; gap: 10px; }}
table {{ width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }}
th, td {{ text-align: left; padding: 10px 0; border-bottom: 1px solid var(--linea); font-weight: 400; }}
td {{ text-align: right; }}
tr.oggi th, tr.oggi td {{ font-weight: 700; }}
tr.oggi th::after {{ content: " · oggi"; color: var(--primario); font-weight: 600; font-size: 0.85rem; }}

footer {{ background: var(--inchiostro); color: var(--carta); padding-block: 36px 110px; font-size: 0.92rem; }}
footer .wrap {{ display: grid; gap: 6px; }}
footer .firma {{ opacity: 0.6; margin-top: 10px; }}
footer .firma a {{ color: var(--carta); }}

.barra {{ position: fixed; left: 0; right: 0; bottom: 0; z-index: 20; display: grid; grid-template-columns: repeat(3, 1fr);
  background: var(--inchiostro); padding: 8px max(8px, env(safe-area-inset-left, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(8px, env(safe-area-inset-right, 0px)); gap: 6px; }}
.barra a {{ display: grid; justify-items: center; gap: 3px; padding: 8px 4px; color: var(--carta); text-decoration: none; font-size: 0.78rem; font-weight: 600; border-radius: 10px; }}
.barra a.princ {{ background: var(--accento); color: var(--inchiostro); }}
@media (max-width: 400px) {{ .stato {{ font-size: 0.76rem; padding: 5px 10px; }} .marchio {{ font-size: 1.02rem; }} }}
@media (min-width: 760px) {{ .barra {{ display: none; }} footer {{ padding-bottom: 40px; }} }}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
</style>
</head>
<body>
{banda_demo}
<header class="testata">
  <div class="wrap">
    <a class="marchio" href="#">{marchio}</a>
    <span class="stato" id="stato">{E(riassunto_orari(orari).split(" · ")[0])}</span>
  </div>
</header>
<main>
  <div class="hero">
    <div class="wrap">
      {logo_hero}
      <p class="zona">{E(d["zona"])}</p>
      <h1>{E(d["nome"])}</h1>
      <p class="sotto">{E(d["sottotitolo"])}</p>
      <div class="azioni">{azioni_hero}</div>
      <p class="info-rapida">{E(riassunto_orari(orari))} · {E(d["indirizzo"])}</p>
    </div>
  </div>
{lavagna}
  <section id="menu" aria-labelledby="t-menu">
    <div class="wrap">
      <h2 id="t-menu" class="tit">{E(titolo_menu)}</h2>
      <div class="menu-grid">{"".join(sezioni)}</div>
      <p class="note-menu">{note_menu}</p>
    </div>
  </section>
{galleria}
{recensioni}
  <section id="dove" aria-labelledby="t-dove">
    <div class="wrap dove">
      <div>
        <h2 id="t-dove" class="tit">Dove siamo</h2>
        <p class="indirizzo">{E(d["indirizzo"])}</p>
        <div class="contatti">
          <a class="btn" href="{E(maps_link)}" target="_blank" rel="noopener">{icona("map")}Indicazioni</a>
          <a class="btn" href="{E(tel_link)}">{icona("tel")}{E(d["telefono"])}</a>
        </div>
      </div>
      <div>
        <h2 class="tit">Orari</h2>
        <table id="orari"><tbody>{righe_orari}</tbody></table>
      </div>
    </div>
  </section>
</main>
<footer>
  <div class="wrap">
    <strong>{E(d["nome"])}</strong>
    <span>{E(d["indirizzo"])} · Tel. {E(d["telefono"])}</span>
    {f'<span>P.IVA {E(d["piva"])}</span>' if d.get("piva") else ""}
    <span class="firma">Sito realizzato da <a href="{E(d.get("credito_link", "https://spinosa-web.2006spinosadavide.workers.dev/"))}" target="_blank" rel="noopener">Spinosa Web</a></span>
  </div>
</footer>
<nav class="barra" aria-label="Azioni rapide">{barra_html}</nav>
<script>
(function () {{
  var ORARI = {json.dumps(orari)};
  try {{
    var parti = new Intl.DateTimeFormat("it-IT", {{ timeZone: "Europe/Rome", weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false }}).formatToParts(new Date());
    var mappa = {{ "lun": 0, "mar": 1, "mer": 2, "gio": 3, "ven": 4, "sab": 5, "dom": 6 }};
    var g, h = 0, m = 0;
    parti.forEach(function (p) {{ if (p.type === "weekday") g = mappa[p.value.slice(0, 3).toLowerCase()]; if (p.type === "hour") h = +p.value % 24; if (p.type === "minute") m = +p.value; }});
    var ora = h * 60 + m, min = function (s) {{ return +s.slice(0, 2) * 60 + +s.slice(3, 5); }};
    var riga = document.querySelector('#orari tr[data-g="' + g + '"]'); if (riga) riga.classList.add("oggi");
    var fasce = ORARI[String(g)] || [], el = document.getElementById("stato"), testo = "Chiuso ora", classe = "chiuso";
    for (var i = 0; i < fasce.length; i++) {{
      if (ora >= min(fasce[i][0]) && ora < min(fasce[i][1])) {{ testo = "Aperto · chiude alle " + fasce[i][1]; classe = "aperto"; break; }}
      if (ora < min(fasce[i][0])) {{ testo = "Chiuso · apre alle " + fasce[i][0]; break; }}
    }}
    el.textContent = testo; el.className = "stato " + classe;
  }} catch (e) {{}}
}})();
</script>
</body>
</html>
'''
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w").write(pagina)
    if d.get("logo"):
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(d["_file"])), d["logo"]), os.path.join(out, os.path.basename(d["logo"])))
    if d.get("foto"):
        os.makedirs(os.path.join(out, "foto"), exist_ok=True)
        base = os.path.dirname(os.path.abspath(d["_file"]))
        for f in d["foto"]:
            shutil.copy(os.path.join(base, f["file"]), os.path.join(out, "foto", os.path.basename(f["file"])))
    return os.path.join(out, "index.html")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    dati = json.load(open(sys.argv[1]))
    dati["_file"] = sys.argv[1]
    print(genera(dati, sys.argv[2]))
