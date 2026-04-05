"""
ADVISIO — Generator continut AI cu Claude + Web Search
========================================================
1. Cauta date reale despre restaurant via web search Anthropic (Haiku)
2. Genereaza audit personalizat bazat pe datele reale gasite (Sonnet)
"""
import os
import json
import time
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
    print(f"Cautam date reale pentru: {biz} ({city})")

    research_prompt = f'''Cauta informatii reale despre restaurantul "{biz}" din {city}, Romania.

Cauta SPECIFIC pentru {city}. Daca gasesti rezultate pentru alt oras, ignora-le.

Returneaza datele gasite:
1. TripAdvisor "{biz}" {city} — rating, numar recenzii, pozitie clasament, 1 recenzie negativa recenta
2. Google Maps "{biz}" {city} — rating, numar recenzii
3. Instagram — cont oficial, numar followeri, numar postari
4. Facebook — pagina oficiala, numar like-uri/followeri
5. Site oficial — adresa, program, tip bucatarie
6. Personalitate vizuala — culori dominante, stil estetic, atmosfera

Daca nu gasesti date pentru o platforma, scrie "negasit pe [platforma]".
Returneaza DOAR date pentru {biz} din {city}.'''

    messages = [{"role": "user", "content": research_prompt}]
    tools    = [{"type": "web_search_20250305", "name": "web_search"}]
    response = None

    for _ in range(8):
        response = get_client().messages.create(
            model=MODEL_RESEARCH,
            max_tokens=2000,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            result_text = ""
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    result_text += block.text
            print(f"Research complet pentru {biz} ({len(result_text)} caractere)")
            return result_text

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": "Continua cu analiza si returneaza datele gasite."})
            continue

        break

    result_text = ""
    if response:
        for block in response.content:
            if hasattr(block, "text") and block.text:
                result_text += block.text

    print(f"Research finalizat pentru {biz} ({len(result_text)} caractere)")
    return result_text or f"Nu s-au gasit date specifice pentru {biz} din {city}."


def call_with_retry(fn, max_retries=4, base_delay=15):
    """Apeleaza fn() cu retry + exponential backoff la 429."""
    for attempt in range(max_retries):
        try:
            return fn()
        except anthropic.RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait = base_delay * (2 ** attempt)  # 15, 30, 60, 120 sec
            print(f"Rate limit 429 — asteptam {wait}s (incercare {attempt+1}/{max_retries})...")
            time.sleep(wait)
        except Exception:
            raise


def generate_audit_content(biz: str, city: str, biz_type: str, research_data: str) -> dict:

    prompt = f'''Esti consultant marketing digital pentru restaurante din Romania.

Ai cercetat "{biz}" din {city} si ai gasit:

---
{research_data}
---

Genereaza audit AI bazat EXCLUSIV pe datele de mai sus.
Cifre negasite → "N/A" sau estimare cu "~".

Raspunde DOAR cu JSON valid, fara text inainte/dupa, fara markdown, fara backticks.

{{"theme":{{"bg":"hex fundal inchis specific restaurantului","accent":"hex accent brand","accent_lt":"hex foarte deschis al accentului","row_hdr":"hex header tabel","urgent":"#C0392B","btn_bg":"hex buton","btn_brd":"hex bordura buton"}},"emotional_hook":"mesaj motivational {biz} max 100 caractere fara diacritice","stats":[["4.2 stele","Rating TripAdvisor"],["#5","din X restaurante {city}"],["1.2K","Followeri Instagram"],["3.5K","Facebook fans"]],"s1_subtitle":"Ce am descoperit despre {biz} in urma cercetarii","s1_body":["Paragraf 1 cu cifre reale 2-3 propozitii.","Paragraf 2 situatia digitala cu probleme concrete.","Paragraf 3 concluzie si oportunitate."],"s1_attn":["ATENTIE - Oportunitate critica:","Descriere concreta pentru {biz}."],"s1_metrics":[["Reply rate recenzii","situatie reala","target 90 zile","CRITICA"],["Followeri Instagram","cifra reala","target crestere","RIDICATA"],["Prezenta Google","situatie reala","optimizare target","RIDICATA"],["Social media","situatie reala","target","MEDIE"],["Recenzii noi","rata actuala","rata target","MEDIE"]],"losses":[{{"num":"01","title":"Problema 1 specifica","body":"Descriere 2-3 propozitii cu cifre.","manual":"X h/sapt.","ai":"Y min","saving":"-Z min","review_bad":"Recenzie negativa reala sau exemplu realist.","review_manager":null,"review_good":"Raspuns profesional AI pentru {biz}.","example_box":null,"before_after":null,"cta_text":"Text CTA."}},{{"num":"02","title":"Problema 2","body":"Descriere 2-3 propozitii.","manual":"X h/sapt.","ai":"Y min","saving":"-Z min","review_bad":null,"review_manager":null,"review_good":null,"example_box":["Postare Instagram {biz}","Text postare cu emoji #hashtag #{city}"],"before_after":null,"cta_text":"Text CTA."}},{{"num":"03","title":"Problema 3","body":"Descriere 2-3 propozitii.","manual":"X h/sapt.","ai":"Y min","saving":"-Z min","review_bad":null,"review_manager":null,"review_good":null,"example_box":null,"before_after":[["Descriere meniu actuala","Descriere rescrisa cu storytelling"],["Al doilea preparat plat","Al doilea preparat cu poveste"]],"cta_text":"Text CTA."}},{{"num":"04","title":"Problema 4","body":"Descriere 2-3 propozitii.","manual":"X h/sapt.","ai":"Y min","saving":"-Z min","review_bad":null,"review_manager":null,"review_good":null,"example_box":["Template DM rezervare {biz}","Buna ziua! Pentru rezervari la {biz}: data ora nr persoane. Confirmam in 30 min!"],"before_after":null,"cta_text":"Text CTA."}},{{"num":"05","title":"Problema 5","body":"Descriere 2-3 propozitii.","manual":"X h/sapt.","ai":"Y min","saving":"-Z min","review_bad":null,"review_manager":null,"review_good":null,"example_box":["Card recenzii bilingv {biz}","RO: La {biz} lasati o recenzie pe Google [QR]\\nEN: At {biz} leave a review on Google [QR]"],"before_after":null,"cta_text":"Text CTA final."}}],"total_manual":"~12h/sapt.","total_ai":"~1.5h/sapt.","s2_subtitle":"Sarcini repetitive pentru {biz}","s3_subtitle":"Selectie specifica pentru {biz}","s4_subtitle":"Trei actiuni prioritare pentru {biz}","s4_intro":"Intro specific {biz} bazat pe datele gasite.","weeks":[["SAPTAMANA 1","URGENT: Prima actiune critica",[{{"day":"Luni - 30 min","action":"Actiune concreta {biz}","note":"Nota practica"}},{{"day":"Miercuri - 20 min","action":"A doua actiune","note":"Nota"}},{{"day":"Vineri - 15 min","action":"A treia actiune","note":"Nota"}}]],["SAPTAMANILE 2-3","Social media activ + automatizari",[{{"day":"Luni S2 - 30 min","action":"Actiune social media","note":"Nota"}},{{"day":"Miercuri S2 - 25 min","action":"Configurare automatizari","note":"Nota"}},{{"day":"Luni S3 - 20 min","action":"Extindere strategie","note":"Nota"}}]],["SAPTAMANA 4","Campanie recenzii + evaluare",[{{"day":"Luni - 25 min","action":"Campanie recenzii Google","note":"Nota"}},{{"day":"Miercuri - 20 min","action":"Rescriere meniu online","note":"Nota"}},{{"day":"Vineri - 15 min","action":"Evaluare rezultate","note":"Nota"}}]]],"s5_subtitle":"Daca preferi sa nu construiesti sistemul de la zero","s5_intro":"Intro specific {biz} relevant pentru situatia lor.","urgency_lines":["Linie urgenta 1 cu cifre reale {biz}.","Linie urgenta 2 specifica situatiei.","Linie urgenta 3 motivationala."],"s5_closing":"Closing specific {biz} profesional fara presiune."}}

TEMA CULORI — alege in functie de tipul restaurantului:
- Berarie/rustic → bg #1A0F0A accent #C17F3E
- Elegant/teatru → bg #0D1B2A accent #C9A84C
- Fine dining/organic → bg #0F2016 accent #C9A84C
- Wine bar/romantic → bg #2C0F1A accent #C9A84C
- Modern/urban → bg #1C1C1E accent albastru/verde neon
- Traditional romanesc → bg #1A0A00 accent #A0251A
- Sushi/japonez → bg #0A0A0A accent #CC2200
- Mediterranean/italian → bg #0A1628 accent #C4622D

accent_lt = versiune foarte deschisa (aproape alba) a accentului.
row_hdr = varianta medie a bg-ului.

IMPORTANT: JSON valid, fara diacritice, fara apostrofuri simple in valori.'''

    def do_call():
        return get_client().messages.create(
            model=MODEL_GENERATE,
            max_tokens=5000,
            messages=[{"role": "user", "content": prompt}],
        )

    message = call_with_retry(do_call)

    raw = message.content[0].text.strip()

    # Scoatem markdown daca exista
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    # Extragem de la primul { pana la ultimul }
    start_idx = raw.find("{")
    end_idx   = raw.rfind("}")
    if start_idx != -1 and end_idx != -1:
        raw = raw[start_idx : end_idx + 1]

    raw = raw.replace('\x00', '').strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        err_pos = e.pos or 0
        snippet = raw[max(0, err_pos-80) : err_pos+80]
        print(f"JSON parse FAIL la char {err_pos}: ...{snippet}...")
        raise


def enrich_restaurant_data(R: dict) -> dict:
    biz      = R.get("bizName", R.get("name", "Restaurant"))
    city     = R.get("city", "Romania")
    biz_type = R.get("type", "restaurant")

    try:
        research_data = research_restaurant(biz, city)

        print(f"Generare audit AI pentru: {biz} ({city})")
        ai_data = generate_audit_content(biz, city, biz_type, research_data)

        fields = [
            "theme",
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

        print(f"Audit personalizat generat cu succes pentru: {biz}")
        if isinstance(R.get("theme"), dict):
            print(f"Tema custom: bg={R['theme'].get('bg')} accent={R['theme'].get('accent')}")

    except json.JSONDecodeError as e:
        print(f"Eroare parsare JSON pentru {biz}: {e} — se folosesc placeholder-urile")
    except Exception as e:
        print(f"Eroare generare AI pentru {biz}: {e} — se folosesc placeholder-urile")

    return R
