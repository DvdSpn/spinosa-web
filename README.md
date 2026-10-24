# Spinosa Web

Sito di Spinosa Web (Davide Spinosa): portfolio, demo e anteprime per i clienti, pubblicato su Cloudflare Workers.

## Indirizzi online

- Portfolio: https://spinosa-web.2006spinosadavide.workers.dev/
- Demo trattoria: https://spinosa-web.2006spinosadavide.workers.dev/demo/trattoria/
- Burger & Grill: https://sito-burger.2006spinosadavide.workers.dev/
- Emibi Beauté: https://sito-emibi.2006spinosadavide.workers.dev/

Ogni push su `main` ripubblica il sito su Cloudflare in automatico.

## Cartelle

```
sito/                  quello che va online (non modificarlo a mano: si rigenera)
  index.html           portfolio
  demo/trattoria/      demo del modello per ristoranti
  anteprime/<cliente>/ bozze per i prospect (non indicizzate su Google)
portfolio/             sorgente del portfolio (src.html, foto, build.py)
strumenti/genera.py    genera una landing per ristorante da un file JSON
clienti/               un file JSON per ogni cliente o demo
```

## Aggiornare il portfolio

```
cd portfolio && python3 build.py
```

## Creare l'anteprima per un nuovo ristorante

1. Copia `clienti/demo-trattoria.json` in `clienti/<nome-cliente>.json`.
2. Togli il blocco `demo`, metti `"anteprima": true` (aggiunge il noindex) e compila nome, contatti, orari, menu, recensioni reali e colori presi dal logo.
3. Metti le foto in `clienti/<nome-cliente>/` e elencale in `foto`.
4. Genera: `python3 strumenti/genera.py clienti/<nome-cliente>.json sito/anteprime/<nome-cliente>`
5. Pubblica: l'anteprima sarà su `/anteprime/<nome-cliente>/`.

Quando il cliente paga, il sito definitivo va su un progetto e un dominio suoi: togli `anteprima`, rigenera e pubblica in un repository dedicato.

## Pubblicazione

`npx wrangler deploy` dalla cartella principale, oppure collegando questo repository a Cloudflare Workers (si pubblica a ogni push).
