import os
from openai import OpenAI

DEMO_MODE = False

# Simptome critice pentru urgență
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

# Recomandări generale cu simboluri
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

def get_ai_recommendation(saptamana, simptome):
    simptome_lower = simptome.lower()
    is_urgent = any(symptom in simptome_lower for symptom in URGENT_SYMPTOMS)

    # Dacă există simptome critice → returnăm doar text curat urgent, fără recomandări generale
    if is_urgent:
        urgent_text = [
            "Consult medical imediat: simptomele indicate pot semnala afecțiuni grave, contactați medicul obstetrician sau mergeți la urgențe.",
            "Monitorizare fetală: verificați starea fătului, mai ales dacă mișcările active sunt diminuate."
        ]
        return {"urgent": urgent_text, "general": GENERAL_RECOMMENDATIONS}

    # Demo mode sau fără cheie API → recomandări generale
    if DEMO_MODE or not os.getenv("OPENAI_API_KEY"):
        return {"urgent": [], "general": GENERAL_RECOMMENDATIONS}

    # Apel OpenAI API (dacă vrei răspuns AI)
    try:
        client = OpenAI()
        prompt = f"""
Pacientă gravidă, săptămâna {saptamana}.
Simptome: {simptome}

Oferă recomandări critice dacă simptomele sunt periculoase. Nu include recomandări generale în secțiunea critică. Returnează text clar, fără simboluri *, # sau Markdown.
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

        # Chiar dacă AI-ul returnează recomandări generale, noi le ignorăm în urgent
        return {"urgent": [response.choices[0].message.content], "general": GENERAL_RECOMMENDATIONS}

    except Exception as e:
        return {"urgent": [f"Eroare AI: {str(e)}"], "general": GENERAL_RECOMMENDATIONS}
