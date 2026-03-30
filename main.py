"""
ADVISIO API — Railway Microservice
====================================
Endpoints:
    POST /generate  → primește datele restaurantului, generează Teaser + Audit Complet,
                       le urcă pe Cloudinary, returnează link-urile + Stripe Payment Link
    GET  /health    → status check
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os, traceback

from pdf_teaser import build_teaser
from pdf_audit import build_audit
from drive_upload import upload_to_drive
from stripe_link import create_payment_link
from webhook import stripe_webhook
from ai_generator import enrich_restaurant_data

app = Flask(__name__)
CORS(app)
app.register_blueprint(stripe_webhook)

API_SECRET = os.environ.get("API_SECRET", "")


def verify_secret(req):
    return req.headers.get("X-API-Secret") == API_SECRET


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Advisio PDF API"})


@app.route("/generate", methods=["POST"])
def generate():
    # ── Autentificare ──────────────────────────────────────────────
    if API_SECRET and not verify_secret(request):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    # ── Date restaurant ────────────────────────────────────────────
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"success": False, "error": "Invalid JSON"}), 400

    required = ["name", "email", "city", "bizName"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "error": f"Câmpuri lipsă: {missing}"}), 400

    # ── Construim obiectul R de bază ───────────────────────────────
    R = build_restaurant_data(data)

    # ── Îmbogățim R cu conținut generat de Claude AI ───────────────
    R = enrich_restaurant_data(R)

    try:
        folder_name = f"Advisio — {R['bizName']} ({R['city']})"

        # ── PASUL 1: Generăm PDF-urile fără stripe_url (primul pass) ──
        # Scopul: obținem audit_url pentru Payment Link
        teaser_bytes_v1 = build_teaser(R)
        audit_bytes_v1  = build_audit(R)

        # ── PASUL 2: Urcăm pe Cloudinary ──────────────────────────────
        teaser_url = upload_to_drive(
            teaser_bytes_v1,
            f"Teaser_{safe(R['bizName'])}.pdf",
            folder_name,
        )
        audit_url = upload_to_drive(
            audit_bytes_v1,
            f"Audit_{safe(R['bizName'])}.pdf",
            folder_name,
        )

        # ── PASUL 3: Creăm Payment Link Stripe cu audit_url în metadata ──
        payment_url = create_payment_link(R, audit_url)

        # ── PASUL 4: Acum că avem stripe_url, regenerăm PDF-urile ──────
        # Butonul din PDF va conține linkul real de plată
        R["stripe_url"]  = payment_url
        R["payment_url"] = payment_url

        teaser_bytes_v2 = build_teaser(R)
        audit_bytes_v2  = build_audit(R)

        # ── PASUL 5: Re-uploadăm PDF-urile finale (overwrite=True) ─────
        teaser_url = upload_to_drive(
            teaser_bytes_v2,
            f"Teaser_{safe(R['bizName'])}.pdf",
            folder_name,
        )
        audit_url = upload_to_drive(
            audit_bytes_v2,
            f"Audit_{safe(R['bizName'])}.pdf",
            folder_name,
        )

        return jsonify({
            "success":     True,
            "teaser_url":  teaser_url,
            "audit_url":   audit_url,
            "payment_url": payment_url,
            "bizName":     R["bizName"],
            "email":       R["email"],
        })

    except Exception as err:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(err)}), 500


# ── Helpers ────────────────────────────────────────────────────────────

def safe(name):
    """Nume sigur pentru fișiere."""
    return "".join(c for c in name if c.isalnum() or c in " _-").strip().replace(" ", "_")


def build_restaurant_data(data):
    """
    Construiește dicționarul R de bază.
    Câmpurile de conținut sunt placeholder-uri — vor fi suprascrise de enrich_restaurant_data().
    """
    biz  = data.get("bizName", data.get("biz", "Restaurant"))
    city = data.get("city", "România")

    return {
        # ── Identitate ──────────────────────────────────────────────
        "bizName":  biz,
        "name":     biz,
        "subtitle": city,
        "address":  f"{city} | Restaurant",
        "email":    data.get("email", ""),
        "city":     city,
        "type":     data.get("type", "restaurant"),
        "theme":    data.get("theme", "navy_gold"),

        # ── Stripe — completat după create_payment_link() ───────────
        "stripe_url":  "",
        "payment_url": "",
        "price":       "97 USD",

        # ── Placeholder stats — suprascrise de AI ───────────────────
        "stats": [
            ("—", "Rating TripAdvisor"),
            ("—", "Poziție locală"),
            ("—", "Followeri Instagram"),
            ("—", "Facebook fans"),
        ],

        # ── Placeholder conținut — suprascris de AI ─────────────────
        "emotional_hook": f"{biz} merită o prezență digitală la fel de bună ca experiența din restaurant.",

        "s1_subtitle": f"Ce am descoperit despre {biz} în urma cercetării noastre directe",
        "s1_body": [
            f"<b>{biz}</b> este analizat de echipa Advisio. "
            f"Raportul complet va fi disponibil în 24-48 de ore.",
        ],
        "s1_attn": (
            "ATENȚIE — Analiză în curs:",
            f"Echipa Advisio cercetează prezența online a {biz} pe TripAdvisor, "
            f"Google, Instagram și Facebook.",
        ),
        "s1_metrics": [
            ("Prezență online", "În analiză", "Optimizat în 30 zile", "CRITICĂ"),
            ("Social media",   "În analiză", "Strategie activă",     "RIDICATĂ"),
            ("Recenzii",       "În analiză", "80%+ reply rate",       "RIDICATĂ"),
        ],

        "s2_subtitle":  f"Sarcini repetitive identificate pentru {biz}",
        "losses":       [],
        "total_manual": "—",
        "total_ai":     "—",

        "s3_subtitle": f"Selecție specifică pentru {biz}",
        "tools": [
            (
                "ChatGPT", "chatgpt.com", "Gratuit",
                "Răspunsuri profesionale la recenzii, postări social media, texte promovare.",
                "Recenzii, Social Media",
            ),
            (
                "Claude", "claude.ai", "Gratuit (Pro $20/lună opțional)",
                "Rescriere meniu cu storytelling culinar, strategii de creștere Instagram.",
                "Meniu, Strategie",
            ),
            (
                "ManyChat", "manychat.com", "Gratuit până la 1.000 contacte",
                "Răspunde automat la DM-uri despre rezervări, program și meniu — 24/7.",
                "DM-uri automate",
            ),
        ],

        "s4_subtitle": f"Trei acțiuni prioritare pentru {biz}",
        "s4_intro":    f"{biz} poate implementa AI în operațiunile zilnice în 30 de zile.",
        "weeks":       [],

        "s5_subtitle": "Dacă preferi să nu construiești tu sistemul de la zero",
        "s5_intro": (
            f"Raportul de față îți arată exact ce trebuie făcut pentru {biz}. "
            f"Dacă preferi să primești totul gata, personalizat, în 48 de ore:"
        ),
        "deliverables": [
            (
                "20 răspunsuri la recenzii scrise complet",
                "În tonul profesional specific restaurantului tău, pentru toate situațiile.",
            ),
            (
                "Calendar de conținut 30 de zile complet scris",
                "Postări finalizate pentru Instagram și Facebook, cu hashtag-uri locale.",
            ),
            (
                "5 template-uri DM bilingve (RO/EN) gata de salvat",
                "Pentru rezervări, program, evenimente, meniu și direcții.",
            ),
            (
                "Meniu principal rescris cu storytelling culinar",
                "Toate preparatele principale cu descrieri narative, gata de publicat.",
            ),
            (
                "Materiale campanie recenzii",
                "Card bilingv gata de tipărit + script verbal + instrucțiuni QR code.",
            ),
        ],
        "urgency_lines": [
            f"{biz} pierde clienți în fiecare zi din cauza prezenței digitale neoptimizate.",
            "Fiecare răspuns neprofesional la o recenzie este citit de sute de potențiali clienți.",
            "Pachetul include toate materialele gata de folosit în 48 de ore.",
        ],
        "s5_closing": (
            "Aceasta nu este o vânzare cu presiune. Raportul conține tot ce ai nevoie pentru a face "
            "singur. Dacă preferi să nu pierzi timp, accesează butonul de mai sus."
        ),

        "cta_price": "GRATUIT",
    }


@app.route("/pdf/<path:public_id>/<filename>", methods=["GET"])
def serve_pdf(public_id, filename):
    """Proxy PDF de pe Cloudinary — compatibil iOS/Safari."""
    import requests as req
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{public_id}"
    r = req.get(url, timeout=30)
    if r.status_code != 200:
        return jsonify({"error": "PDF not found"}), 404
    from flask import Response
    return Response(
        r.content,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf",
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
