"""
ADVISIO — Generator continut AI cu Claude + Web Search
========================================================
1. Cauta date reale despre restaurant via web search Anthropic (Haiku)
2. Genereaza audit personalizat bazat pe datele reale gasite (Sonnet)
"""
import os
import json
import anthropic

_client = None

def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    return _client

MODEL_RESEARCH = "claude-haiku-4-5-20251001"
MODEL_GENERATE = "claude-sonnet-4-6"


def research_restaurant(biz: str, city: str) -> str:
    """
    Cauta date reale despre restaurant folosind web search Claude Haiku.
    Foloseste agentic loop pana cand Claude returneaza text final.
    """
    print(f"Cautam date reale pentru: {biz} ({city})")

    research_prompt = f"""Cauta informatii reale si concrete despre restaurantul "{biz}" din {city}, Romania.

IMPORTANT: Cauta SPECIFIC pentru {city} — nu alt oras. Daca gasesti rezultate pentru alt oras, ignora-le complet.

Cauta urmatoarele si returneaza cifre exacte:
1. TripAdvisor "{biz}" {city} — rating exact (ex: 4.3 stele), numar recenzii, pozitie in clasament local (ex: #5 din 89 restaurante {city}), copiaza 1-2 recenzii negative recente si raspunsul managerului daca exista
2. Google Maps "{biz}" {city} — rating exact, numar recenzii Google
3. Instagram — cauta contul oficial al restaurantului {biz} din {city}, numar followeri exact, numar postari
4. Facebook — pagina oficiala {biz} {city}, numar like-uri/followeri, numar check-in-uri
5. Site oficial daca exista — adresa, program, tip bucatarie

Daca nu gasesti date pentru o platforma, scrie explicit "negasit pe [platforma]".
Returneaza DOAR date pentru {biz} din {city}, nu pentru alte restaurante cu nume similar din alte orase."""

    messages = [{"role": "user", "content": research_prompt}]
    tools    = [{"type": "web_search_20250305", "name": "web_search"}]
    response = None

    # Agentic loop — Claude poate face mai multe search-uri
    for _ in range(5):
        response = get_client().messages.create(
            model=MODEL_RESEARCH,
            max_tokens=2000,
            tools=tools,
            messages=messages,
        )

        # S-a terminat cu text final
        if response.stop_reason == "end_turn":
            result_text = ""
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    result_text += block.text
            print(f"Research complet pentru {biz} ({len(result_text)} caractere)")
            return result_text

        # A folosit tool-uri → continuam conversatia
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     "Search efectuat.",
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        break

    # Fallback — extragem orice text din ultimul raspuns
    result_text = ""
    if response:
        for block in response.content:
            if hasattr(block, "text") and block.text:
                result_text += block.text

    print(f"Research finalizat pentru {biz} ({len(result_text)} caractere)")
    return result_text or f"Nu s-au gasit date specifice pentru {biz} din {city}."


def generate_audit_content(biz: str, city: str, biz_type: str, research_data: str) -> dict:
    """
    Genereaza continutul auditului bazat pe datele reale cercetate — model Sonnet.
    """

    prompt = f"""Esti un consultant de marketing digital specializat in restaurante din Romania.

Ai cercetat restaurantul "{biz}" din {city} si ai gasit urmatoarele date REALE:

---
{research_data}
---

Bazat EXCLUSIV pe datele de mai sus (nu inventa nimic), genereaza un audit AI complet.
Daca o cifra nu a fost gasita in research, foloseste "N/A" sau o estimare realista marcata cu "~".

Raspunde DOAR cu un obiect JSON valid, fara text inainte sau dupa, fara markdown, fara ```json.

{{
  "emotional_hook": "mesaj motivational specific pentru {biz}, max 120 caractere, fara diacritice",
  "stats": [
    ["4.2 stele", "Rating TripAdvisor"],
    ["#5", "din X restaurante {city}"],
    ["1.2K", "Followeri Instagram"],
    ["3.5K", "Facebook fans"]
  ],
  "s1_subtitle": "Ce am descoperit despre {biz} in urma cercetarii noastre directe",
  "s1_body": [
    "Paragraf 1 — prezentare generala cu cifre reale gasite, 2-3 propozitii SPECIFICE.",
    "Paragraf 2 — situatia digitala actuala cu probleme concrete identificate in research.",
    "Paragraf 3 — concluzie si oportunitate principala."
  ],
  "s1_attn": [
    "ATENTIE — Oportunitate critica identificata:",
    "Descriere concreta bazata pe datele reale gasite pentru {biz}."
  ],
  "s1_metrics": [
    ["Reply rate recenzii", "situatie reala gasita", "target 90 zile", "CRITICA"],
    ["Followeri Instagram", "cifra reala gasita", "target crestere", "RIDICATA"],
    ["Prezenta Google", "situatie reala", "optimizare target", "RIDICATA"],
    ["Social media", "situatie reala", "target", "MEDIE"],
    ["Recenzii noi", "rata actuala", "rata target", "MEDIE"]
  ],
  "losses": [
    {{
      "num": "01",
      "title": "Problema 1 specifica identificata in research",
      "body": "Descriere detaliata bazata pe datele reale, 2-3 propozitii cu cifre concrete.",
      "manual": "X h/sapt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": "Recenzie negativa reala gasita sau exemplu realist.",
      "review_manager": null,
      "review_good": "Raspuns profesional AI specific pentru {biz}.",
      "example_box": null,
      "before_after": null,
      "cta_text": "Text CTA specific."
    }},
    {{
      "num": "02",
      "title": "Problema 2 specifica pentru {biz}",
      "body": "Descriere detaliata, 2-3 propozitii.",
      "manual": "X h/sapt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": ["Postare Instagram pentru {biz}", "Text postare cu emoji si hashtag-uri #{city}"],
      "before_after": null,
      "cta_text": "Text CTA specific."
    }},
    {{
      "num": "03",
      "title": "Problema 3 specifica pentru {biz}",
      "body": "Descriere detaliata, 2-3 propozitii.",
      "manual": "X h/sapt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": null,
      "before_after": [
        ["Descriere meniu actuala scurta", "Descriere rescrisa cu storytelling culinar specific {biz}"],
        ["Al doilea preparat plat", "Al doilea preparat cu poveste si ingrediente"]
      ],
      "cta_text": "Text CTA specific."
    }},
    {{
      "num": "04",
      "title": "Problema 4 specifica pentru {biz}",
      "body": "Descriere detaliata, 2-3 propozitii.",
      "manual": "X h/sapt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": ["Template DM rezervare {biz}", "Buna ziua! Pentru rezervari la {biz} va rugam: data, ora, nr. persoane. Confirmam in 30 min!"],
      "before_after": null,
      "cta_text": "Text CTA specific."
    }},
    {{
      "num": "05",
      "title": "Problema 5 specifica pentru {biz}",
      "body": "Descriere detaliata, 2-3 propozitii.",
      "manual": "X h/sapt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": ["Card recenzii bilingv {biz}", "RO: La {biz}! Lasati o recenzie pe Google/TripAdvisor [QR]\\nEN: At {biz}! Leave a review on Google/TripAdvisor [QR]"],
      "before_after": null,
      "cta_text": "Text CTA motivational final."
    }}
  ],
  "total_manual": "~12h/sapt.",
  "total_ai": "~1.5h/sapt.",
  "s2_subtitle": "Sarcini repetitive identificate — cu exemple reale pentru {biz}",
  "s3_subtitle": "Selectie specifica pentru {biz} — gratuite sau aproape gratuite",
  "s4_subtitle": "Trei actiuni prioritare — specifice situatiei {biz}",
  "s4_intro": "Intro specific pentru {biz} bazat pe datele reale gasite.",
  "weeks": [
    [
      "SAPTAMANA 1",
      "URGENT: Prima actiune critica pentru {biz}",
      [
        {{"day": "Luni — 30 min", "action": "Actiune concreta specifica pentru {biz}", "note": "Nota practica"}},
        {{"day": "Miercuri — 20 min", "action": "A doua actiune", "note": "Nota"}},
        {{"day": "Vineri — 15 min", "action": "A treia actiune", "note": "Nota"}}
      ]
    ],
    [
      "SAPTAMANILE 2-3",
      "Social media activ + automatizari",
      [
        {{"day": "Luni S2 — 30 min", "action": "Actiune social media", "note": "Nota"}},
        {{"day": "Miercuri S2 — 25 min", "action": "Configurare automatizari", "note": "Nota"}},
        {{"day": "Luni S3 — 20 min", "action": "Extindere strategie", "note": "Nota"}}
      ]
    ],
    [
      "SAPTAMANA 4",
      "Campanie recenzii + evaluare",
      [
        {{"day": "Luni — 25 min", "action": "Campanie recenzii Google/TripAdvisor", "note": "Nota"}},
        {{"day": "Miercuri — 20 min", "action": "Rescriere meniu online", "note": "Nota"}},
        {{"day": "Vineri — 15 min", "action": "Evaluare rezultate", "note": "Nota"}}
      ]
    ]
  ],
  "s5_subtitle": "Daca preferi sa nu construiesti tu sistemul de la zero",
  "s5_intro": "Intro specific pentru {biz} — relevant pentru situatia lor concreta.",
  "urgency_lines": [
    "Linie urgenta 1 cu cifre reale despre {biz}.",
    "Linie urgenta 2 specifica situatiei gasite.",
    "Linie urgenta 3 motivationala."
  ],
  "s5_closing": "Closing specific pentru {biz} — profesional, fara presiune."
}}

IMPORTANT:
- Foloseste EXCLUSIV datele reale din research — nu inventa cifre
- Daca cifra nu e gasita → marcheza cu ~ sau N/A
- Tot continutul fara diacritice (fara a, i, s, t cu semne)
- JSON valid, nimic altceva"""

    message = get_client().messages.create(
        model=MODEL_GENERATE,
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def enrich_restaurant_data(R: dict) -> dict:
    """
    1. Research cu Haiku + web search
    2. Generare audit cu Sonnet
    3. Imbogateste dictionarul R
    """
    biz      = R.get("bizName", R.get("name", "Restaurant"))
    city     = R.get("city", "Romania")
    biz_type = R.get("type", "restaurant")

    try:
        research_data = research_restaurant(biz, city)

        print(f"Generare audit AI pentru: {biz} ({city})")
        ai_data = generate_audit_content(biz, city, biz_type, research_data)

        fields = [
            "emotional_hook", "stats",
            "s1_subtitle", "s1_body", "s1_attn", "s1_metrics",
            "s2_subtitle", "s3_subtitle",
            "losses", "total_manual", "total_ai",
            "s4_subtitle", "s4_intro", "weeks",
            "s5_subtitle", "s5_intro", "urgency_lines", "s5_closing",
        ]
        for field in fields:
            if field in ai_data and ai_data[field]:
                R[field] = ai_data[field]

        # s1_attn trebuie sa fie tuplu pentru build_audit
        if isinstance(R.get("s1_attn"), list) and len(R["s1_attn"]) == 2:
            R["s1_attn"] = tuple(R["s1_attn"])

        print(f"Audit personalizat generat cu succes pentru: {biz}")

    except json.JSONDecodeError as e:
        print(f"Eroare parsare JSON pentru {biz}: {e} — se folosesc placeholder-urile")
    except Exception as e:
        print(f"Eroare generare AI pentru {biz}: {e} — se folosesc placeholder-urile")

    return R
