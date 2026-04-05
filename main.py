"""
ADVISIO API — Railway Microservice
====================================
Endpoints:
    POST /generate  → generează Teaser + Audit, le urcă pe Supabase,
                       returnează link-urile + Stripe Payment Link
    GET  /download  → proxy PDF cu forțare download
    GET  /health    → status check
"""

from flask import Flask, request, jsonify, Response, abort
from flask_cors import CORS
import os, traceback, requests as req

from pdf_teaser import build_teaser
from pdf_audit import build_audit
from drive_upload import upload_to_drive
from stripe_link import create_payment_link
from webhook import stripe_webhook
from ai_generator import enrich_restaurant_data
from text_utils import clean_dict, clean  # ← curățare diacritice

app = Flask(__name__)
CORS(app)
app.register_blueprint(stripe_webhook)

API_SECRET = os.environ.get("API_SECRET", "")


def verify_secret(r):
    return r.headers.get("X-API-Secret") == API_SECRET


# ════════════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ════════════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Advisio PDF API"})


# ════════════════════════════════════════════════════════════════════
#  DOWNLOAD PROXY
# ════════════════════════════════════════════════════════════════════

@app.route("/download", methods=["GET"])
def download_pdf():
    url      = request.args.get("url", "").strip()
    filename = request.args.get("filename", "Teaser_Advisio.pdf").strip()

    if not url:
        abort(400)
    if "supabase.co" not in url:
        abort(403)

    try:
        r = req.get(url, timeout=30)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    if r.status_code != 200:
        return jsonify({"error": f"HTTP {r.status_code}"}), 404

    return Response(
        r.content,
        mimetype="application/octet-stream",
        headers={
            "Content-Disposition":    f'attachment; filename="{filename}"',
            "Content-Type":           "application/octet-stream",
            "Cache-Control":          "no-cache",
            "X-Content-Type-Options": "nosniff",
        }
    )


# ════════════════════════════════════════════════════════════════════
#  GENERATE
# ════════════════════════════════════════════════════════════════════

@app.route("/generate", methods=["POST"])
def generate():
    if API_SECRET and not verify_secret(request):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"success": False, "error": "Invalid JSON"}), 400

    required = ["name", "email", "city", "bizName"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "error": f"Campuri lipsa: {missing}"}), 400

    # Construim R de bază
    R = build_restaurant_data(data)

    # Îmbogățim cu AI
    try:
        R = enrich_restaurant_data(R)
        print(f"[generate] enrich OK — losses: {len(R.get('losses', []))}")
    except Exception as enrich_err:
        print(f"[generate] EROARE enrich: {enrich_err}")
        traceback.print_exc()

    # ── Curățăm TOATE diacriticele din R pentru ReportLab ─────────
    R = protect_theme(R)

    try:
        folder_name = f"Advisio -- {R['bizName']} ({R['city']})"

        # PASUL 1: PDF-uri fără stripe_url
        teaser_bytes_v1 = build_teaser(R)
        audit_bytes_v1  = build_audit(R)

        # PASUL 2: Upload Supabase
        teaser_url = upload_to_drive(teaser_bytes_v1, f"Teaser_{safe(R['bizName'])}.pdf", folder_name)
        audit_url  = upload_to_drive(audit_bytes_v1,  f"Audit_{safe(R['bizName'])}.pdf",  folder_name)

        # PASUL 3: Payment Link cu sheet_row în metadata
        payment_url = create_payment_link(R, audit_url)

        # PASUL 4: Regenerăm cu stripe_url real
        R["stripe_url"]  = payment_url
        R["payment_url"] = payment_url

        teaser_bytes_v2 = build_teaser(R)
        audit_bytes_v2  = build_audit(R)

        # PASUL 5: Re-upload final
        teaser_url = upload_to_drive(teaser_bytes_v2, f"Teaser_{safe(R['bizName'])}.pdf", folder_name)
        audit_url  = upload_to_drive(audit_bytes_v2,  f"Audit_{safe(R['bizName'])}.pdf",  folder_name)

        # URL proxy download forțat
        base_url     = os.environ.get("RAILWAY_URL", "https://advisio-api-production.up.railway.app")
        biz_safe     = safe(R["bizName"])
        download_url = (
            f"{base_url}/download"
            f"?url={req.utils.quote(teaser_url, safe='')}"
            f"&filename=Teaser_Advisio_{biz_safe}.pdf"
        )

        return jsonify({
            "success":      True,
            "teaser_url":   teaser_url,
            "download_url": download_url,
            "audit_url":    audit_url,
            "payment_url":  payment_url,
            "bizName":      R["bizName"],
            "email":        R["email"],
        })

    except Exception as err:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(err)}), 500


# ════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════

def safe(name):
    return "".join(c for c in name if c.isalnum() or c in " _-").strip().replace(" ", "_")

def protect_theme(R: dict) -> dict:
    theme_backup = R.get("theme")
    R = clean_dict(R)
    if isinstance(theme_backup, dict):
        R["theme"] = theme_backup
    return R

def build_restaurant_data(data):
    biz  = data.get("bizName", data.get("biz", "Restaurant"))
    city = data.get("city", "Romania")

    return {
        "bizName":   biz,
        "name":      biz,
        "subtitle":  city,
        "address":   f"{city} | Restaurant",
        "email":     data.get("email", ""),
        "city":      city,
        "type":      data.get("type", "restaurant"),
        "theme":     data.get("theme", "navy_gold"),
        "sheet_row": data.get("sheet_row", ""),
        "stripe_url":  "",
        "payment_url": "",
        "price":       "97 USD",
        "stats": [
            ("—", "Rating TripAdvisor"),
            ("—", "Pozitie locala"),
            ("—", "Followeri Instagram"),
            ("—", "Facebook fans"),
        ],
        "emotional_hook": f"{biz} merita o prezenta digitala la fel de buna ca experienta din restaurant.",
        "s1_subtitle": f"Ce am descoperit despre {biz} in urma cercetarii noastre directe",
        "s1_body": [
            f"<b>{biz}</b> este analizat de echipa Advisio. Raportul complet va fi disponibil in 24-48 de ore.",
        ],
        "s1_attn": (
            "ATENTIE — Analiza in curs:",
            f"Echipa Advisio cerceteaza prezenta online a {biz} pe TripAdvisor, Google, Instagram si Facebook.",
        ),
        "s1_metrics": [
            ("Prezenta online", "In analiza", "Optimizat in 30 zile", "CRITICA"),
            ("Social media",   "In analiza", "Strategie activa",     "RIDICATA"),
            ("Recenzii",       "In analiza", "80%+ reply rate",       "RIDICATA"),
        ],
        "s2_subtitle":  f"Sarcini repetitive identificate pentru {biz}",
        "losses":       [],
        "total_manual": "—",
        "total_ai":     "—",
        "s3_subtitle": f"Selectie specifica pentru {biz}",
        "tools": [
            ("ChatGPT", "chatgpt.com", "Gratuit",
             "Raspunsuri profesionale la recenzii, postari social media, texte promovare.",
             "Recenzii, Social Media"),
            ("Claude", "claude.ai", "Gratuit (Pro $20/luna optional)",
             "Rescriere meniu cu storytelling culinar, strategii de crestere Instagram.",
             "Meniu, Strategie"),
            ("ManyChat", "manychat.com", "Gratuit pana la 1.000 contacte",
             "Raspunde automat la DM-uri despre rezervari, program si meniu — 24/7.",
             "DM-uri automate"),
        ],
        "s4_subtitle": f"Trei actiuni prioritare pentru {biz}",
        "s4_intro":    f"{biz} poate implementa AI in operatiunile zilnice in 30 de zile.",
        "weeks":       [],
        "s5_subtitle": "Daca preferi sa nu construiesti tu sistemul de la zero",
        "s5_intro": (
            f"Raportul de fata iti arata exact ce trebuie facut pentru {biz}. "
            f"Daca preferi sa primesti totul gata, personalizat, in 48 de ore:"
        ),
        "deliverables": [
            ("20 raspunsuri la recenzii scrise complet",
             "In tonul profesional specific restaurantului tau, pentru toate situatiile."),
            ("Calendar de continut 30 de zile complet scris",
             "Postari finalizate pentru Instagram si Facebook, cu hashtag-uri locale."),
            ("5 template-uri DM bilingve (RO/EN) gata de salvat",
             "Pentru rezervari, program, evenimente, meniu si directii."),
            ("Meniu principal rescris cu storytelling culinar",
             "Toate preparatele principale cu descrieri narative, gata de publicat."),
            ("Materiale campanie recenzii",
             "Card bilingv gata de tiparit + script verbal + instructiuni QR code."),
        ],
        "urgency_lines": [
            f"{biz} pierde clienti in fiecare zi din cauza prezentei digitale neoptimizate.",
            "Fiecare raspuns neprofesional la o recenzie este citit de sute de potentiali clienti.",
            "Pachetul include toate materialele gata de folosit in 48 de ore.",
        ],
        "s5_closing": (
            "Aceasta nu este o vanzare cu presiune. Raportul contine tot ce ai nevoie pentru a face "
            "singur. Daca preferi sa nu pierzi timp, acceseaza butonul de mai sus."
        ),
        "cta_price": "GRATUIT",
    }


# ════════════════════════════════════════════════════════════════════
#  SEARCH — Cauta afaceri cu probleme digitale
# ════════════════════════════════════════════════════════════════════

@app.route("/search", methods=["POST"])
def search_businesses():
    if API_SECRET and not verify_secret(request):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"success": False, "error": "Invalid JSON"}), 400

    city     = data.get("city", "").strip()
    biz_type = data.get("bizType", "Restaurant").strip()
    criteria = data.get("criteria", [])

    if not city:
        return jsonify({"success": False, "error": "Campul city este obligatoriu"}), 400

    criteria_text = ", ".join(criteria) if criteria else "prezenta digitala slaba"

    prompt = f'''Cauta pe Google Maps, TripAdvisor, Facebook si Instagram afaceri de tip "{biz_type}" din {city}, Romania.

Identifica 6-10 afaceri REALE care au probleme digitale clare, in special: {criteria_text}.

Pentru fiecare afacere gasita, returneaza un JSON array cu obiecte avand exact aceasta structura:
[
  {{
    "name": "Numele afacerii",
    "address": "Adresa sau zona din oras",
    "email": "emailul de contact daca il gasesti, altfel string gol",
    "phone": "telefonul daca il gasesti, altfel string gol",
    "problems": ["problema 1 concreta", "problema 2 concreta"],
    "rating": "ex: 3.8 pe Google",
    "instagram": "ex: 800 followeri sau Absent",
    "tripadvisor": "ex: #12 din 45 sau Absent",
    "notes": "un rand scurt cu observatia principala"
  }}
]

IMPORTANT: Returneaza DOAR JSON valid, fara text inainte sau dupa, fara markdown, fara backticks.
Toate string-urile sa foloseasca ghilimele duble. Fara apostrofuri simple in interiorul valorilor.
Fara diacritice romanesti. Toate afacerile trebuie sa fie REALE si din {city}. Nu inventa date.'''

    try:
        import anthropic as _anthropic
        import json as _json

        client   = _anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        messages = [{"role": "user", "content": prompt}]
        tools    = [{"type": "web_search_20250305", "name": "web_search"}]
        response = None

        for _ in range(8):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                tools=tools,
                messages=messages,
            )
            if response.stop_reason == "end_turn":
                break
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": "Continua si returneaza JSON-ul final."})
                continue
            break

        # ── Colectam tot textul din raspuns ──────────────────────────
        result_text = ""
        if response:
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    result_text += block.text

        print(f"[search] Raw response ({len(result_text)} chars): {result_text[:300]}...")

        # ── Parsare robusta JSON ──────────────────────────────────────
        raw = result_text.strip()

        # 1. Scoatem blocurile markdown ```json ... ``` daca exista
        if "```" in raw:
            for part in raw.split("```"):
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("["):
                    raw = part
                    break

        # 2. Extragem de la primul [ pana la ultimul ]
        start_idx = raw.find("[")
        end_idx   = raw.rfind("]")

        if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
            print(f"[search] Nu s-a gasit array JSON valid. Raw: {result_text[:500]}")
            return jsonify({
                "success": False,
                "error":   "AI nu a returnat JSON valid — array negasit",
                "raw":     result_text[:500],
            }), 500

        raw = raw[start_idx : end_idx + 1]

        # 3. Curatam caractere problematice
        raw = raw.replace('\x00', '')   # null bytes
        raw = raw.replace('\r\n', ' ')  # CRLF in strings
        raw = raw.replace('\r', ' ')

        # 4. Parsare cu log detaliat la eroare
        try:
            results = _json.loads(raw)
        except _json.JSONDecodeError as parse_err:
            # Afisam contextul exact din jurul erorii
            err_pos     = parse_err.pos or 0
            snippet_start = max(0, err_pos - 80)
            snippet_end   = min(len(raw), err_pos + 80)
            snippet       = raw[snippet_start:snippet_end]

            print(f"[search] JSON parse FAIL la char {err_pos}: ...{snippet}...")
            return jsonify({
                "success":       False,
                "error":         f"JSON parse error: {str(parse_err)}",
                "error_pos":     err_pos,
                "error_snippet": snippet,
                "raw_preview":   raw[:1000],
            }), 500

        return jsonify({"success": True, "results": results, "count": len(results)})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
