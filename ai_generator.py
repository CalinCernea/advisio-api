"""
ADVISIO — Generator conținut AI cu Claude
==========================================
Generează conținutul personalizat al auditului pentru fiecare restaurant.
Folosește Claude claude-sonnet-4-20250514 via Anthropic API.
"""
import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def generate_audit_content(biz: str, city: str, biz_type: str = "restaurant") -> dict:
    """
    Generează conținutul complet al auditului pentru un restaurant.
    Returnează un dict cu toate câmpurile necesare pentru build_restaurant_data().
    """

    prompt = f"""Ești un consultant de marketing digital specializat în restaurante din România.
Generează un audit AI complet și REALIST pentru următorul restaurant:

Nume restaurant: {biz}
Oraș: {city}
Tip: {biz_type}

Răspunde DOAR cu un obiect JSON valid, fără text înainte sau după, fără markdown, fără ```json.
Structura JSON trebuie să fie EXACT aceasta:

{{
  "emotional_hook": "un mesaj motivațional specific pentru {biz}, max 120 caractere",
  "stats": [
    ["4.2", "Rating TripAdvisor"],
    ["#8", "Poziție locală"],
    ["1.2K", "Followeri Instagram"],
    ["850", "Facebook fans"]
  ],
  "s1_body": [
    "Paragraf 1 despre {biz} — prezentare generală, 2-3 propoziții specifice.",
    "Paragraf 2 — situația digitală actuală, puncte slabe identificate."
  ],
  "s1_attn": [
    "ATENȚIE — Prioritate identificată:",
    "Descriere concretă a problemei principale găsite pentru {biz} în {city}."
  ],
  "s1_metrics": [
    ["Prezență online", "Neoptimizată", "Top 3 local în 90 zile", "CRITICĂ"],
    ["Social media", "Sub medie", "200 followeri/lună", "RIDICATĂ"],
    ["Recenzii Google", "Fără răspunsuri", "80% răspuns în 24h", "RIDICATĂ"]
  ],
  "losses": [
    {{
      "num": "01",
      "title": "Titlu problemă 1 specifică pentru {biz}",
      "body": "Descriere detaliată a problemei, 2-3 propoziții. Specifică pentru un restaurant din {city}.",
      "manual": "4h/săpt.",
      "ai": "30 min",
      "saving": "3.5h",
      "review_bad": "Exemplu recenzie negativă realistă primită de un restaurant similar.",
      "review_manager": "Răspuns slab/neprofesional la recenzie — exemplu realist.",
      "review_good": "Răspuns profesional generat de AI — complet, empatic, specific pentru {biz}.",
      "example_box": null,
      "before_after": null,
      "cta_text": null
    }},
    {{
      "num": "02",
      "title": "Titlu problemă 2 specifică pentru {biz}",
      "body": "Descriere detaliată a problemei 2, 2-3 propoziții.",
      "manual": "3h/săpt.",
      "ai": "20 min",
      "saving": "2.5h",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": ["Postare Instagram generată pentru {biz}", "Textul complet al postării, specific restaurantului, cu emoji-uri și hashtag-uri locale pentru {city}."],
      "before_after": null,
      "cta_text": null
    }},
    {{
      "num": "03",
      "title": "Titlu problemă 3",
      "body": "Descriere problemă 3.",
      "manual": "2h/săpt.",
      "ai": "15 min",
      "saving": "1.5h",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": null,
      "before_after": [
        ["Descriere meniu actuală — scurtă și neinspirantă", "Descriere rescrisă cu storytelling culinar — atractivă și specifică"],
        ["Al doilea preparat — descriere plată", "Al doilea preparat — rescris cu ingrediente și poveste"]
      ],
      "cta_text": null
    }},
    {{
      "num": "04",
      "title": "Titlu problemă 4",
      "body": "Descriere problemă 4.",
      "manual": "2h/săpt.",
      "ai": "15 min",
      "saving": "1.5h",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": ["DM template rezervare pentru {biz}", "Bună ziua! Vă mulțumim pentru mesaj. Pentru rezervări la {biz} vă rugăm să ne spuneți: data, ora și numărul de persoane. Vă confirmăm în maxim 30 de minute! 🍽️"],
      "before_after": null,
      "cta_text": null
    }},
    {{
      "num": "05",
      "title": "Titlu problemă 5",
      "body": "Descriere problemă 5.",
      "manual": "1.5h/săpt.",
      "ai": "10 min",
      "saving": "1h",
      "review_bad": null,
      "review_manager": null,
      "review_good": null,
      "example_box": null,
      "before_after": null,
      "cta_text": "Text motivațional final pentru a implementa soluția AI pentru această problemă."
    }}
  ],
  "total_manual": "12.5h/săpt.",
  "total_ai": "1.5h/săpt.",
  "weeks": [
    [
      "SĂPTĂMÂNA 1",
      "Fundația digitală",
      [
        {{"day": "Ziua 1-2", "action": "Acțiune concretă specifică pentru {biz}", "note": "Notă practică de implementare"}},
        {{"day": "Ziua 3-4", "action": "A doua acțiune", "note": "Notă"}},
        {{"day": "Ziua 5-7", "action": "A treia acțiune", "note": "Notă"}}
      ]
    ],
    [
      "SĂPTĂMÂNA 2",
      "Activarea social media",
      [
        {{"day": "Ziua 8-10", "action": "Acțiune social media pentru {biz}", "note": "Notă"}},
        {{"day": "Ziua 11-14", "action": "Altă acțiune", "note": "Notă"}}
      ]
    ],
    [
      "SĂPTĂMÂNA 3-4",
      "Automatizare și scalare",
      [
        {{"day": "Ziua 15-21", "action": "Implementare automatizări", "note": "Notă"}},
        {{"day": "Ziua 22-30", "action": "Măsurare și optimizare", "note": "Notă"}}
      ]
    ]
  ],
  "urgency_lines": [
    "Linie urgență 1 specifică pentru {biz}.",
    "Linie urgență 2.",
    "Linie urgență 3."
  ]
}}

IMPORTANT:
- Tot conținutul trebuie să fie în română
- Fii specific pentru {biz} din {city} — nu generic
- Cifrele din stats trebuie să fie realiste pentru un restaurant din România
- Recenziile și răspunsurile trebuie să sune natural, ca scrise de oameni reali
- Răspunsul tău trebuie să fie DOAR JSON valid, nimic altceva"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Curăță orice markdown rămas
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def enrich_restaurant_data(R: dict) -> dict:
    """
    Îmbogățește dicționarul R cu conținut generat de AI.
    Dacă generarea eșuează, R rămâne cu placeholder-urile originale.
    """
    biz      = R.get("bizName", R.get("name", "Restaurant"))
    city     = R.get("city", "România")
    biz_type = R.get("type", "restaurant")

    try:
        print(f"Generare conținut AI pentru: {biz} ({city})")
        ai_data = generate_audit_content(biz, city, biz_type)

        # Suprascrie câmpurile din R cu cele generate de AI
        fields = [
            "emotional_hook", "stats", "s1_body", "s1_attn", "s1_metrics",
            "losses", "total_manual", "total_ai", "weeks", "urgency_lines",
        ]
        for field in fields:
            if field in ai_data and ai_data[field]:
                R[field] = ai_data[field]

        # Reconstruiește s1_attn ca tuplu (build_audit îl folosește cu *)
        if isinstance(R.get("s1_attn"), list) and len(R["s1_attn"]) == 2:
            R["s1_attn"] = tuple(R["s1_attn"])

        print(f"✓ Conținut AI generat cu succes pentru: {biz}")

    except json.JSONDecodeError as e:
        print(f"Eroare parsare JSON de la Claude pentru {biz}: {e}")
    except Exception as e:
        print(f"Eroare generare AI pentru {biz}: {e} — se folosesc placeholder-urile")

    return R
