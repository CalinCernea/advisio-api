"""
ADVISIO — Generator conținut AI cu Claude + Web Search
========================================================
1. Caută date reale despre restaurant via web search Anthropic (Haiku)
2. Generează audit personalizat bazat pe datele reale găsite (Sonnet)
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
    Caută date reale despre restaurant folosind web search Claude.
    Folosește agentic loop — continuă până când Claude termină cu un răspuns text final.
    """
    print(f"🔍 Căutăm date reale pentru: {biz} ({city})")

    research_prompt = f"""Caută informații reale și concrete despre restaurantul "{biz}" din {city}, România.

Caută pe:
1. TripAdvisor — rating exact, număr recenzii, poziție în clasamentul local, recenzii recente pozitive și negative
2. Google Maps — rating exact, număr recenzii, program, adresă
3. Instagram — numele contului, număr followeri, număr postări
4. Facebook — număr followeri, check-in-uri
5. Site-ul oficial dacă există

Returnează TOATE datele găsite cu cifre exacte. Dacă nu găsești ceva, spune "negăsit"."""

    messages = [{"role": "user", "content": research_prompt}]
    tools    = [{"type": "web_search_20250305", "name": "web_search"}]

    # Agentic loop — Claude poate face mai multe search-uri
    for _ in range(5):  # max 5 iterații
        response = get_client().messages.create(
            model=MODEL_RESEARCH,
            max_tokens=2000,
            tools=tools,
            messages=messages,
        )

        # Dacă s-a terminat cu text → returnăm rezultatul
        if response.stop_reason == "end_turn":
            result_text = ""
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    result_text += block.text
            print(f"✓ Research complet pentru {biz} ({len(result_text)} caractere)")
            return result_text

        # Dacă a folosit tool-uri → adăugăm rezultatele și continuăm
        if response.stop_reason == "tool_use":
            # Adăugăm răspunsul asistentului în conversație
            messages.append({"role": "assistant", "content": response.content})

            # Construim tool_result pentru fiecare tool_use block
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # Web search returnează rezultatele în block.content dacă există
                    # altfel Claude le procesează intern
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     "Search efectuat.",
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        # Alt stop reason — ieșim
        break

    # Fallback — extragem orice text disponibil din ultimul răspuns
    result_text = ""
    for block in response.content:
        if hasattr(block, "text") and block.text:
            result_text += block.text

    print(f"✓ Research finalizat pentru {biz} ({len(result_text)} caractere)")
    return result_text or f"Nu s-au găsit date specifice pentru {biz} din {city}."


def generate_audit_content(biz: str, city: str, biz_type: str, research_data: str) -> dict:
    """
    Generează conținutul auditului bazat pe datele reale — model Sonnet.
    """

    prompt = f"""Ești un consultant de marketing digital specializat în restaurante din România.

Ai cercetat restaurantul "{biz}" din {city} și ai găsit următoarele date REALE:

---
{research_data}
---

Bazat EXCLUSIV pe datele de mai sus (nu inventa nimic), generează un audit AI complet.
Dacă o cifră nu a fost găsită în research, folosește "N/A" sau o estimare realistă marcată cu "~".

Răspunde DOAR cu un obiect JSON valid, fără text înainte sau după, fără markdown, fără ```json.

{{
  "emotional_hook": "mesaj motivațional specific pentru {biz}, max 120 caractere",
  "stats": [
    ["4.2 ★", "Rating TripAdvisor"],
    ["#5", "din X restaurante {city}"],
    ["1.2K", "Followeri Instagram"],
    ["3.5K", "Facebook fans"]
  ],
  "s1_subtitle": "Ce am descoperit despre {biz} în urma cercetării noastre directe",
  "s1_body": [
    "Paragraf 1 — prezentare generală cu cifre reale găsite.",
    "Paragraf 2 — situația digitală actuală cu probleme concrete.",
    "Paragraf 3 — concluzie și oportunitate principală."
  ],
  "s1_attn": [
    "ATENȚIE — Oportunitate critică identificată:",
    "Descriere concretă bazată pe datele reale găsite pentru {biz}."
  ],
  "s1_metrics": [
    ["Reply rate recenzii", "situatie reala gasita", "target 90 zile", "CRITICĂ"],
    ["Followeri Instagram", "cifra reala gasita", "target crestere", "RIDICATĂ"],
    ["Prezență Google", "situatie reala", "optimizare target", "RIDICATĂ"],
    ["Social media", "situatie reala", "target", "MEDIE"],
    ["Recenzii noi", "rata actuala", "rata target", "MEDIE"]
  ],
  "losses": [
    {{
      "num": "01",
      "title": "Problemă 1 specifică identificată în research",
      "body": "Descriere detaliată cu cifre concrete din research, 2-3 propoziții.",
      "manual": "X h/săpt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": "Recenzie negativă reală găsită sau exemplu realist.",
      "review_manager": null,
      "review_good": "Răspuns profesional AI specific pentru {biz}.",
      "example_box": null,
      "before_after": null,
      "cta_text": "Text CTA specific."
    }},
    {{
      "num": "02",
      "title": "Problemă 2 specifică pentru {biz}",
      "body": "Descriere detaliată, 2-3 propoziții.",
      "manual": "X h/săpt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": ["Postare Instagram pentru {biz}", "Text postare cu emoji și hashtag-uri #{city}"],
      "before_after": null,
      "cta_text": "Text CTA specific."
    }},
    {{
      "num": "03",
      "title": "Problemă 3 specifică pentru {biz}",
      "body": "Descriere detaliată, 2-3 propoziții.",
      "manual": "X h/săpt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": null,
      "before_after": [
        ["Descriere meniu actuală neinspirantă", "Descriere rescrisă cu storytelling culinar"],
        ["Al doilea preparat plat", "Al doilea preparat cu poveste"]
      ],
      "cta_text": "Text CTA specific."
    }},
    {{
      "num": "04",
      "title": "Problemă 4 specifică pentru {biz}",
      "body": "Descriere detaliată, 2-3 propoziții.",
      "manual": "X h/săpt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": ["Template DM rezervare {biz}", "Bună ziua! Pentru rezervări la {biz} vă rugăm: data, ora, nr. persoane. Confirmăm în 30 min! 🍽️"],
      "before_after": null,
      "cta_text": "Text CTA specific."
    }},
    {{
      "num": "05",
      "title": "Problemă 5 specifică pentru {biz}",
      "body": "Descriere detaliată, 2-3 propoziții.",
      "manual": "X h/săpt.",
      "ai": "Y min",
      "saving": "-Z min",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": ["Card recenzii bilingv {biz}", "🇷🇴 La {biz}! Lăsați o recenzie pe Google/TripAdvisor [QR]\\n🇬🇧 At {biz}! Leave a review on Google/TripAdvisor [QR]"],
      "before_after": null,
      "cta_text": "Text CTA motivațional final."
    }}
  ],
  "total_manual": "~12h/săpt.",
  "total_ai": "~1.5h/săpt.",
  "s2_subtitle": "Sarcini repetitive identificate — cu exemple reale pentru {biz}",
  "s3_subtitle": "Selecție specifică pentru {biz} — gratuite sau aproape gratuite",
  "s4_subtitle": "Trei acțiuni prioritare — specifice situației {biz}",
  "s4_intro": "Intro specific pentru {biz} bazat pe datele reale găsite.",
  "weeks": [
    [
      "SĂPTĂMÂNA 1",
      "URGENT: Prima acțiune critică pentru {biz}",
      [
        {{"day": "Luni — 30 min", "action": "Acțiune concretă pentru {biz}", "note": "Notă practică"}},
        {{"day": "Miercuri — 20 min", "action": "A doua acțiune", "note": "Notă"}},
        {{"day": "Vineri — 15 min", "action": "A treia acțiune", "note": "Notă"}}
      ]
    ],
    [
      "SĂPTĂMÂNILE 2-3",
      "Social media activ + automatizări",
      [
        {{"day": "Luni S2 — 30 min", "action": "Acțiune social media", "note": "Notă"}},
        {{"day": "Miercuri S2 — 25 min", "action": "Configurare automatizări", "note": "Notă"}},
        {{"day": "Luni S3 — 20 min", "action": "Extindere strategie", "note": "Notă"}}
      ]
    ],
    [
      "SĂPTĂMÂNA 4",
      "Campanie recenzii + evaluare",
      [
        {{"day": "Luni — 25 min", "action": "Campanie recenzii Google/TripAdvisor", "note": "Notă"}},
        {{"day": "Miercuri — 20 min", "action": "Rescriere meniu online", "note": "Notă"}},
        {{"day": "Vineri — 15 min", "action": "Evaluare rezultate", "note": "Notă"}}
      ]
    ]
  ],
  "s5_subtitle": "Dacă preferi să nu construiești tu sistemul de la zero",
  "s5_intro": "Intro specific pentru {biz} — relevant pentru situația lor concretă.",
  "urgency_lines": [
    "Linie urgență 1 cu cifre reale despre {biz}.",
    "Linie urgență 2 specifică situației găsite.",
    "Linie urgență 3 motivațională."
  ],
  "s5_closing": "Closing specific pentru {biz} — profesional, fără presiune."
}}

IMPORTANT:
- Folosește EXCLUSIV datele reale din research
- Dacă cifra nu e găsită → marchează cu ~ sau N/A
- Tot conținutul în română
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
    3. Îmbogățește dicționarul R
    """
    biz      = R.get("bizName", R.get("name", "Restaurant"))
    city     = R.get("city", "România")
    biz_type = R.get("type", "restaurant")

    try:
        research_data = research_restaurant(biz, city)

        print(f"🤖 Generare audit AI pentru: {biz} ({city})")
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

        if isinstance(R.get("s1_attn"), list) and len(R["s1_attn"]) == 2:
            R["s1_attn"] = tuple(R["s1_attn"])

        print(f"✓ Audit personalizat generat cu succes pentru: {biz}")

    except json.JSONDecodeError as e:
        print(f"⚠ Eroare parsare JSON pentru {biz}: {e} — se folosesc placeholder-urile")
    except Exception as e:
        print(f"⚠ Eroare generare AI pentru {biz}: {e} — se folosesc placeholder-urile")

    return R
