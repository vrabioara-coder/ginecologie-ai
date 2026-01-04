import os
from openai import OpenAI

DEMO_MODE = False  # pune True dacă vrei doar demo fără OpenAI

# --- Simptome critice pentru urgență ---
URGENT_SYMPTOMS = [
    "contracții",
    "sângerare",
    "pierdere de lichid",
    "lichid amniotic",
    "ruptura membranelor",
    "mâncărime",
    "durere de cap",
    "diminuarea mișcărilor fetale"
]

# --- Recomandări generale ---
GENERAL_RECOMMENDATIONS = [
    {"category": "Hidratare", "icon": "💧", "color": "blue-100",
     "text": "Bea suficiente lichide pentru a preveni deshidratarea."},
    {"category": "Alimentație", "icon": "🥗", "color": "green-100",
     "text": "Mese mici și frecvente, evită alimentele grase sau picante."},
    {"category": "Odihnă", "icon": "😴", "color": "purple-100",
     "text": "Odihnește-te suficient, stresul poate agrava disconfortul."},
    {"category": "Îmbrăcăminte", "icon": "👚", "color": "yellow-100",
     "text": "Poartă haine lejere, confortabile."},
    {"category": "Băi", "icon": "🛁", "color": "pink-100",
     "text": "Băi calde pot ameliora pruritul și relaxa corpul."}
]

def generate_ai_recommendations(dpn: str, simptome: str, profil=None):
    """
    Primește săptămâna de sarcină (DPN), simptome și profil medical.
    Returnează dicționar cu recomandări urgente și generale.
    """
    simptome_lower = simptome.lower() if simptome else ""
    is_urgent = any(symptom in simptome_lower for symptom in URGENT_SYMPTOMS)

    # Context profil (text descriptiv)
    context_profil = ""
    if profil:
        context_profil = f"""
Profil medical pacientă:
- Vârstă: {profil.varsta if profil.varsta else 'necunoscută'}
- Grupa sanguină: {profil.grupa_sange if profil.grupa_sange else 'necunoscută'} Rh {profil.rh if profil.rh else 'necunoscut'}
- Sarcină cu risc: {"Da" if profil.sarcina_risc else "Nu"}
- Complicații: {profil.complicatii if profil.complicatii else "Niciuna"}
- Boli cunoscute: {profil.boli if profil.boli else "Nicio afecțiune raportată"}
- Medicație: {profil.medicatie_sarcina if profil.medicatie_sarcina else "Nicio medicație"}
- Fumătoare: {"Da" if profil.fumatoare else "Nu"}
- Consum alcool: {"Da" if profil.alcool else "Nu"}
- Istoric obstetrical: {profil.nr_sarcini if profil.nr_sarcini else 0} sarcini, {profil.nr_nasteri if profil.nr_nasteri else 0} nașteri
- Avorturi: {profil.avorturi if profil.avorturi else 0}
- DUM: {profil.dum if profil.dum else "necunoscută"}
- DPN: {profil.dpn if profil.dpn else "necunoscută"}
"""

    # --- Recomandări urgente ---
    urgent_list = []
    if is_urgent:
        urgent_list = [
            "Consult medical imediat: simptomele indicate pot semnala afecțiuni grave, contactați medicul obstetrician sau mergeți la urgențe.",
            "Monitorizare fetală: verificați starea fătului, mai ales dacă mișcările active sunt diminuate."
        ]

    # --- Recomandări generale ---
    general_list = GENERAL_RECOMMENDATIONS.copy()

    # --- DEMO sau fără OpenAI ---
    if DEMO_MODE or not os.getenv("OPENAI_API_KEY"):
        return {"urgent": urgent_list, "general": general_list}

    # --- Apel OpenAI ---
    try:
        client = OpenAI()
        prompt = f"""
Pacientă gravidă, săptămâna {dpn}.
Simptome: {simptome or 'Niciun simptom raportat'}

{context_profil}

Oferă recomandări critice dacă simptomele sunt periculoase și recomandări generale separate. Text clar, fără simboluri *, # sau Markdown.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ești un asistent medical educațional. Evidențiază urgențele separat, fără recomandări generale în ele."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        ai_text = response.choices[0].message.content if response.choices else ""
        if ai_text:
            urgent_list.append(ai_text)

    except Exception as e:
        urgent_list.append(f"Eroare AI: {str(e)}")

    return {"urgent": urgent_list, "general": general_list}
