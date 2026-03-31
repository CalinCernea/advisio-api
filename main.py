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
    R = enrich_restaurant_data(R)

    # ── Curățăm TOATE diacriticele din R pentru ReportLab ─────────
    R = clean_dict(R)

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
