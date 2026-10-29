"""Generate the test material derived from corpus/facts.yaml:
  - corpus/docs/it-manuale-operativo.md  (long document, ~25k words, with planted "needle" facts)
  - corpus/images/*.png                   (scanned invoice, filled-in form, chart, table, rating plate)

The generated content is test data and is written in Italian on purpose (the fictional company's
operations manual and paperwork). Random seed is fixed, so the output is reproducible.
Fonts are read from C:/Windows/Fonts (Arial, Courier New); change FONT_DIR on other systems.

Usage: python scripts/build_corpus.py
"""
import random
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
F = yaml.safe_load((ROOT / "corpus/facts.yaml").read_text(encoding="utf-8"))
random.seed(20261020)

FONT_DIR = Path("C:/Windows/Fonts")

# PIL draws text in white when no fill is given: make (near-)black the default.
_orig_text = ImageDraw.ImageDraw.text


def _text(self, xy, text, fill=None, font=None, **kw):
    return _orig_text(self, xy, text, fill=(20, 20, 20) if fill is None else fill, font=font, **kw)


ImageDraw.ImageDraw.text = _text


def font(name="arial.ttf", size=22):
    return ImageFont.truetype(str(FONT_DIR / name), size)


# ----------------------------------------------------------------------------
# OPERATIONS MANUAL (long document)
# ----------------------------------------------------------------------------
TOPICS = [
    ("Caldaie murali a gas a condensazione", "caldaia", ["scambiatore primario", "bruciatore premiscelato", "ventilatore", "sifone condensa", "valvola gas", "pressostato fumi", "sonda NTC mandata"]),
    ("Caldaie a basamento e generatori di potenza", "generatore", ["bruciatore ad aria soffiata", "camera di combustione", "turbolatori", "termostato di sicurezza", "pompa di ricircolo", "vaso di espansione"]),
    ("Centrali termiche condominiali", "centrale termica", ["collettore di mandata", "pompe gemellari", "valvole miscelatrici", "contabilizzatori", "vaso di espansione", "rilevatore gas"]),
    ("Pompe di calore aria-acqua RX AIR", "pompa di calore", ["compressore inverter", "valvola a 4 vie", "batteria evaporante", "ventilatore EC", "sonda di sbrinamento", "scheda inverter", "flussostato"]),
    ("Unità split e multisplit", "unità split", ["filtro aria", "batteria interna", "pompa di scarico condensa", "motore flap", "unità esterna", "valvola di espansione elettronica"]),
    ("Sistemi VRF e chiller per il terziario", "chiller", ["compressori scroll", "condensatore", "evaporatore a piastre", "pressostati HP/LP", "scheda di controllo", "unità esterna"]),
    ("Gas refrigeranti e normativa F-gas", "circuito frigorifero", ["gruppo manometrico", "bilancia", "stazione di recupero", "pompa del vuoto", "cercafughe elettronico", "bombola di recupero"]),
    ("Produzione acqua calda sanitaria e bollitori", "bollitore", ["anodo di magnesio", "serpentino", "valvola di sicurezza", "termostato", "valvola miscelatrice termostatica", "ricircolo"]),
    ("Impianti solari termici", "collettore solare", ["glicole", "vaso di espansione solare", "centralina differenziale", "pompa circuito solare", "valvola di sfiato", "sonda collettore"]),
    ("Quadri elettrici di comando e protezione", "quadro elettrico", ["interruttore generale", "differenziali", "contattori", "relè termici", "morsettiere", "scaricatori di sovratensione"]),
    ("Unità di trattamento aria e ventilazione", "UTA", ["filtri G4/F7", "recuperatore di calore", "batterie caldo/freddo", "ventilatori plug-fan", "serrande", "sonde di temperatura e umidità"]),
    ("Documentazione, libretto di impianto ed emergenze", "impianto", ["libretto di impianto", "rapporto di controllo efficienza energetica", "registro F-gas", "registro verifiche elettriche", "schede di sicurezza", "piano di emergenza"]),
]
SUBS = ["Descrizione e principio di funzionamento", "Manutenzione programmata e controlli periodici", "Diagnosi dei guasti e interventi correttivi"]

AGHI = {a["sezione"]: a["fatto"] for a in F["manuale_operativo"]["aghi"]}

INTRO = [
    "Questa sezione descrive le attività che il tecnico deve svolgere su {comp} durante le visite programmate e in caso di chiamata per guasto.",
    "Le indicazioni che seguono si applicano a tutti gli impianti con {comp} gestiti dalla sede di Macerata e dalla filiale di Leicester, salvo diversa indicazione del costruttore.",
    "Il tecnico deve leggere questa sezione prima del primo intervento su {comp} e consultarla ogni volta che si presenta un'anomalia non prevista.",
    "In caso di conflitto tra queste istruzioni e il manuale del costruttore, prevale sempre il manuale del costruttore; segnalare il conflitto al Responsabile tecnico.",
]
BODY = [
    "Prima di intervenire su {parte}, verificare che l'impianto sia spento e che le parti in tensione siano sezionate secondo la procedura PR-07.",
    "Il controllo visivo di {parte} deve evidenziare eventuali tracce di corrosione, perdite, surriscaldamento o rumori anomali; ogni anomalia va annotata sul rapporto di intervento.",
    "La pulizia di {parte} va eseguita con i prodotti indicati nella scheda tecnica, evitando solventi aggressivi che possono danneggiare guarnizioni e rivestimenti.",
    "Dopo ogni intervento su {parte}, eseguire una prova di funzionamento di almeno 15 minuti e registrare i parametri di esercizio nel libretto di impianto.",
    "La sostituzione di {parte} richiede ricambi originali o equivalenti approvati; i ricambi non conformi fanno decadere la garanzia e vanno rifiutati.",
    "Il tecnico senior è l'unico autorizzato a tarare {parte}; il tecnico junior può eseguire solo la pulizia e il controllo visivo sotto supervisione.",
    "Le misure su {parte} si eseguono con strumenti tarati entro i 12 mesi; la data di taratura va riportata sul rapporto.",
    "Se {parte} presenta un guasto ricorrente (più di due interventi in sei mesi), aprire una segnalazione al Responsabile tecnico per valutare la sostituzione dell'intero componente o dell'apparecchio.",
    "Non modificare mai le impostazioni di fabbrica di {parte} senza autorizzazione scritta del cliente e annotazione sul libretto.",
    "Per gli impianti con contratto di manutenzione, il controllo di {parte} rientra nelle 4 visite annuali incluse nel canone; per gli altri clienti è fatturato a listino.",
]
ERRORI = [
    "dimenticare di riaprire le valvole di intercettazione dopo l'intervento",
    "non verificare la tenuta dopo la sostituzione di una guarnizione",
    "compilare il rapporto di intervento senza riportare i valori misurati",
    "usare un ricambio di modello diverso senza verificarne la compatibilità",
    "lasciare il cliente senza spiegazione delle operazioni svolte e delle raccomandazioni",
    "non fotografare la targhetta dell'apparecchio prima di ordinare i ricambi",
    "scambiare le sonde di mandata e ritorno durante il rimontaggio",
    "non ripristinare i parametri del cronotermostato dopo il test",
]
PARAM_POOL = [
    ("Temperatura di mandata riscaldamento", "35-55 °C (bassa temperatura) / 60-75 °C (radiatori)"),
    ("Delta T mandata/ritorno", "5-10 °C a regime"),
    ("Pressione gas alla rampa (metano)", "17-25 mbar"),
    ("CO nei fumi (secchi, 0% O2)", "< 400 ppm; oltre 1.000 ppm fermare l'apparecchio"),
    ("Temperatura fumi condensazione", "40-70 °C"),
    ("Surriscaldamento (superheat)", "5-10 K"),
    ("Sottoraffreddamento (subcooling)", "3-8 K"),
    ("Pressione di evaporazione R-32", "7-9 bar a 7 °C esterni"),
    ("Assorbimento compressore", "entro ±10% della targa"),
    ("Portata aria UTA", "entro ±15% di progetto"),
    ("Resistenza di isolamento", "> 1 MΩ a 500 V"),
    ("Tempo di intervento differenziale 30 mA", "< 300 ms"),
    ("Temperatura ACS all'uscita del miscelatore", "45-50 °C"),
    ("Percentuale glicole circuito solare", "30-40% (protezione fino a -15/-22 °C)"),
]


def para(sentences, n, **kw):
    picks = random.sample(sentences, n)
    return " ".join(s.format(**kw) for s in picks)


def section(num, topic, comp, parts, sub):
    out = [f"## {num}. {topic} — {sub}\n"]
    out.append(para(INTRO, 2, comp=comp) + "\n")
    for i in range(4):
        p = para(BODY, 3, parte=random.choice(parts))
        if num in AGHI and i == 1:
            p = p + " Nota operativa: " + AGHI[num] + "."
        out.append(p + "\n")
    out.append("**Checklist:**\n")
    for part in random.sample(parts, min(6, len(parts))):
        out.append(f"- [ ] {random.choice(['Verifica', 'Pulizia', 'Controllo', 'Prova di funzionamento', 'Misura'])} {part}")
    out.append("\n**Parametri di riferimento:**\n\n| Parametro | Valore |\n|---|---|")
    for k, v in random.sample(PARAM_POOL, 4):
        out.append(f"| {k} | {v} |")
    out.append("\n**Errori comuni da evitare:**\n")
    for e in random.sample(ERRORI, 3):
        out.append(f"- {e}")
    out.append("\n" + para(BODY, 2, parte=random.choice(parts)) + "\n")
    return "\n".join(out)


def build_manual():
    m = F["manuale_operativo"]
    lines = [f"# {m['titolo']}\n", f"**Rossi Impianti Srl** · Revisione {m['revisione']} · {m['data']} · Responsabile: Davide Marinelli\n",
             "Questo manuale raccoglie le istruzioni operative per la manutenzione degli impianti termici, di climatizzazione ed elettrici gestiti da Rossi Impianti Srl e dalla filiale Rossi Installations Ltd. È organizzato per tipologia di impianto; ogni tipologia ha tre sezioni: funzionamento, manutenzione programmata, diagnosi guasti.\n",
             "## Indice\n"]
    num = 0
    for topic, _, _ in TOPICS:
        for sub in SUBS:
            num += 1
            lines.append(f"{num}. {topic} — {sub}")
    lines.append("\n---\n")
    num = 0
    for topic, comp, parts in TOPICS:
        for sub in SUBS:
            num += 1
            lines.append(section(num, topic, comp, parts, sub))
    text = "\n".join(lines)
    path = ROOT / "corpus/docs/it-manuale-operativo.md"
    path.write_text(text, encoding="utf-8")
    words = len(text.split())
    print(f"manual: {num} sections, {words} words, needles in sections {sorted(AGHI)} -> {path.name}")


# ----------------------------------------------------------------------------
# IMAGES
# ----------------------------------------------------------------------------
def scanify(img, angle=1.2, noise=12):
    """Simulate a scan: slight rotation, light grey background, noise, mild blur."""
    img = img.convert("RGB")
    bg = Image.new("RGB", (img.width + 80, img.height + 80), (236, 234, 228))
    bg.paste(img, (40, 40))
    bg = bg.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(200, 198, 192))
    px = bg.load()
    for _ in range(bg.width * bg.height // 6):
        x, y = random.randrange(bg.width), random.randrange(bg.height)
        r, g, b = px[x, y]
        d = random.randint(-noise, noise)
        px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))
    return bg.filter(ImageFilter.GaussianBlur(0.6))


def text_block(draw, xy, lines, f, gap=8, fill=(20, 20, 20)):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=f, fill=fill)
        y += f.size + gap
    return y


def img_fattura():
    ft = F["fatture"][0]
    az = F["azienda"]
    cl = F["clienti"][0]
    im = Image.new("RGB", (1240, 1754), "white")
    d = ImageDraw.Draw(im)
    d.text((80, 70), az["ragione_sociale"].upper(), font=font("arialbd.ttf", 40), fill=(20, 40, 90))
    text_block(d, (80, 125), [az["sede_legale"], f"P.IVA {az['piva']} · Tel. {az['telefono']}", f"PEC {az['pec']}"], font(size=22), fill=(60, 60, 60))
    d.text((800, 70), "FATTURA", font=font("arialbd.ttf", 44), fill=(20, 20, 20))
    text_block(d, (800, 130), [f"N. {ft['numero']}", f"Data: 15/09/2026"], font(size=26))
    d.rectangle((80, 280, 1160, 282), fill=(20, 40, 90))
    d.text((80, 310), "Spett.le", font=font(size=22), fill=(90, 90, 90))
    text_block(d, (80, 340), [cl["nome"], cl["sede"], "Rif. contratto 2026/114"], font("arialbd.ttf", 26))
    # line-item table
    y = 520
    d.rectangle((80, y, 1160, y + 50), fill=(230, 234, 242))
    for x, t in [(95, "Descrizione"), (760, "Q.tà"), (860, "Prezzo"), (1010, "Importo")]:
        d.text((x, y + 12), t, font=font("arialbd.ttf", 24))
    y += 70
    d.text((95, y), ft["descrizione"], font=font(size=24))
    d.text((760, y), "1", font=font(size=24))
    d.text((860, y), "450,00 €", font=font(size=24))
    d.text((1010, y), "450,00 €", font=font(size=24))
    y += 60
    d.text((95, y), "Punti vendita: Civitanova (2), Porto Recanati, Potenza Picena, Montecosaro, Recanati", font=font(size=20), fill=(90, 90, 90))
    d.line((80, 1000, 1160, 1000), fill=(150, 150, 150), width=2)
    text_block(d, (760, 1030), ["Imponibile", "IVA 22%", "TOTALE"], font("arialbd.ttf", 26), gap=18)
    text_block(d, (1010, 1030), ["450,00 €", "99,00 €", "549,00 €"], font("arialbd.ttf", 26), gap=18)
    text_block(d, (80, 1250), ["Modalità di pagamento: bonifico bancario 30 gg d.f.", f"Scadenza: 15/10/2026", f"IBAN: {ft['iban']}", "Banca: Banca di Credito Cooperativo di Macerata (immaginaria)"], font(size=24), gap=12)
    d.text((80, 1600), "Operazione soggetta a IVA ordinaria. Documento generato per test — azienda immaginaria.", font=font(size=18), fill=(120, 120, 120))
    scanify(im).save(ROOT / "corpus/images/fattura-FT-2026-0087-scansione.png")


def img_rapporto():
    im = Image.new("RGB", (1240, 1600), "white")
    d = ImageDraw.Draw(im)
    d.text((80, 60), "RAPPORTO DI INTERVENTO  —  MOD-04", font=font("arialbd.ttf", 36))
    d.text((80, 110), "Rossi Impianti Srl · Via dell'Industria 42, Macerata", font=font(size=22), fill=(80, 80, 80))
    hand = font("cour.ttf", 28)  # "handwritten" fields in a different typeface
    fields = [
        ("Data intervento", "24/09/2026"), ("Ora inizio / fine", "15:00 / 17:30"),
        ("Cliente", "Bianchi Supermercati Srl"), ("Sede / impianto", "P.V. Porto Recanati - chiller unita' esterna"),
        ("Contratto", "2026/114"), ("Tecnico", "Luca Fabbri"),
        ("Guasto segnalato", "Unita' esterna ferma, allarme E12 sul display"),
        ("Diagnosi", "Scheda inverter compressore in corto"),
        ("Intervento eseguito", "Sostituita scheda inverter cod. INV-2240-B, test 30 min OK"),
        ("Ricambi utilizzati", "1 x scheda inverter INV-2240-B"), ("Ore manodopera", "2,5"),
        ("Esito", "Impianto ripristinato e funzionante"),
        ("Prossimo controllo", "Dicembre 2026 (controllo straordinario gratuito)"),
    ]
    y = 190
    for k, v in fields:
        d.text((80, y), k + ":", font=font("arialbd.ttf", 24))
        d.line((400, y + 34, 1160, y + 34), fill=(170, 170, 170), width=1)
        d.text((410, y - 2), v, font=hand, fill=(30, 30, 110))
        y += 78
    d.text((80, y + 30), "Firma tecnico: L. Fabbri", font=hand, fill=(30, 30, 110))
    d.text((700, y + 30), "Firma cliente: M. Properzi (dir. P.V.)", font=hand, fill=(30, 30, 110))
    scanify(im, angle=-0.8).save(ROOT / "corpus/images/rapporto-intervento-2026-09-24.png")


def img_grafico():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    data = F["interventi_2026_mensili"]
    mesi = list(data.keys())
    vals = list(data.values())
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=120)
    bars = ax.bar(mesi, vals, color="#1e3a8a")
    bars[vals.index(max(vals))].set_color("#f59e42")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, str(v), ha="center", fontsize=11)
    ax.set_title("Rossi Impianti — Interventi mensili 2026 (gennaio-settembre)", fontsize=14)
    ax.set_ylabel("Numero interventi")
    ax.set_ylim(0, 110)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(ROOT / "corpus/images/grafico-interventi-2026.png")


def img_tabella():
    lst = F["listino_2026"]
    im = Image.new("RGB", (1100, 620), "white")
    d = ImageDraw.Draw(im)
    d.text((40, 30), "Listino manodopera 2026 — confronto Italia / UK", font=font("arialbd.ttf", 30))
    rows = [("Voce", "Italia (€)", "UK (£)"),
            ("Tecnico / Engineer, per ora", f"{lst['it']['tecnico_eur_h']},00", f"{lst['uk']['engineer_gbp_h']}.00"),
            ("Tecnico senior, per ora", f"{lst['it']['tecnico_senior_eur_h']},00", "—"),
            ("Diritto di chiamata / Call-out", f"{lst['it']['diritto_chiamata_eur']},00", f"{lst['uk']['call_out_gbp']}.00"),
            ("Maggiorazione festivi / Weekend uplift", "+50%", "+50%"),
            ("Chilometraggio oltre 30 km", "0,60 €/km", "n/a"),
            ("Manutenzione annuale caldaia (forfait)", "95,00", "—"),
            ("Manutenzione annuale pompa di calore ≤16 kW", "140,00", "—")]
    y = 100
    for i, (a, b, c) in enumerate(rows):
        if i == 0:
            d.rectangle((40, y - 8, 1060, y + 42), fill=(30, 58, 138))
            col = "white"; f = font("arialbd.ttf", 24)
        else:
            if i % 2 == 0:
                d.rectangle((40, y - 8, 1060, y + 42), fill=(240, 242, 248))
            col = (20, 20, 20); f = font(size=24)
        d.text((55, y), a, font=f, fill=col)
        d.text((640, y), b, font=f, fill=col)
        d.text((880, y), c, font=f, fill=col)
        y += 56
    d.text((40, y + 20), "Prezzi IVA/VAT esclusa. Validità: 01/01/2026 - 31/12/2026.", font=font(size=20), fill=(100, 100, 100))
    im.save(ROOT / "corpus/images/tabella-listino-2026.png")


def img_targhetta():
    im = Image.new("RGB", (900, 560), (200, 203, 208))
    d = ImageDraw.Draw(im)
    d.rectangle((20, 20, 880, 540), outline=(90, 90, 90), width=3, fill=(222, 224, 228))
    d.text((40, 35), "RX AIR SERIES", font=font("arialbd.ttf", 34), fill=(30, 30, 30))
    d.text((40, 80), "Air-to-water heat pump / Pompa di calore aria-acqua", font=font(size=20), fill=(60, 60, 60))
    rows = [("MODEL", "RX-16 AIR"), ("SERIAL NO.", "RX16-26-1183"), ("HEATING CAPACITY", "16.0 kW (A7/W35)"),
            ("COP", "4.45 (A7/W35)"), ("REFRIGERANT", "R-32  /  GWP 675"), ("CHARGE", "1.6 kg  (1.08 t CO2 eq)"),
            ("POWER SUPPLY", "400 V ~ 3N  50 Hz"), ("MAX CURRENT", "14.5 A"), ("MAX PRESSURE HP/LP", "4.15 / 2.5 MPa"),
            ("IP RATING", "IPX4"), ("MANUFACTURED", "2026-03")]
    y = 125
    for k, v in rows:
        d.text((40, y), k, font=font("arialbd.ttf", 20), fill=(40, 40, 40))
        d.text((380, y), v, font=font("cour.ttf", 22), fill=(10, 10, 10))
        y += 36
    im = im.rotate(-2, resample=Image.BICUBIC, fillcolor=(120, 120, 120))
    scanify(im, angle=0, noise=18).save(ROOT / "corpus/images/targhetta-RX-16-AIR.png")


if __name__ == "__main__":
    build_manual()
    for fn in (img_fattura, img_rapporto, img_grafico, img_tabella, img_targhetta):
        fn()
        print("image:", fn.__name__)
    print("done")
