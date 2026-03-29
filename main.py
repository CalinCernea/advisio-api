"""
ADVISIO API — Railway Microservice
====================================
Endpoints:
POST /generate → primește datele restaurantului, generează Teaser + Audit Complet,
le urcă pe Google Drive, returnează link-urile + Stripe Payment Link
GET /health → status check
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, io, json, traceback
from pdf_teaser import build_teaser
from pdf_audit import build_audit
from drive_upload import upload_to_drive
from stripe_link import create_payment_link
from webhook import stripe_webhook
app = Flask(__name__)
CORS(app)
app.register_blueprint(stripe_webhook)
API_SECRET = os.environ.get("API_SECRET", "") # setat în Railway env vars
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
# ── Construim obiectul R pentru generatoarele PDF ──────────────
R = build_restaurant_data(data)
try:
# 1. Generează Teaser PDF
teaser_bytes = build_teaser(R)
# 2. Generează Audit Complet PDF
audit_bytes = build_audit(R)
# 3. Urcă pe Google Drive (în folder per restaurant)
folder_name = f"Advisio — {R['bizName']} ({R['city']})"
teaser_url = upload_to_drive(teaser_bytes, f"Teaser_{safe(R['bizName'])}.pdf", folder_audit_url = upload_to_drive(audit_bytes, f"Audit_{safe(R['bizName'])}.pdf", folder_# 4. Creează Payment Link Stripe unic (97 USD)
payment_url = create_payment_link(R, audit_url)
return jsonify({
"success": True,
"teaser_url": teaser_url,
"audit_url": audit_url,
"payment_url": payment_url,
"bizName": R["bizName"],
"email": R["email"],
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
Construiește dicționarul R complet pentru generatoarele PDF.
Câmpurile OBLIGATORII vin din formular.
Câmpurile de CONȚINUT (s1_body, losses etc.) sunt generate de AI
sau completate manual ulterior — pentru MVP folosim placeholders.
"""
biz = data.get("bizName", data.get("biz", "Restaurant"))
city = data.get("city", "România")
return {
# ── Identitate ──────────────────────────────────────────────
"bizName": biz,
"name": biz,
"subtitle": city,
"address": f"{city} | Restaurant",
"email": data.get("email", ""),
"city": city,
"theme": data.get("theme", "navy_gold"),
# ── Stripe (completat după ce payment link e creat) ─────────
"stripe_url": data.get("stripe_url", ""),
"price": "247 USD",
# ── Stats copertă (din formular sau defaults) ───────────────
"stats": data.get("stats", [
("—", "Rating TripAdvisor"),
("—", "Poziție locală"),
("—", "Followeri Instagram"),
("—", "Facebook fans"),
]),
# ── Secțiunea 1 ─────────────────────────────────────────────
"s1_subtitle": f"Ce am descoperit despre {biz} în urma cercetării noastre directe",
"s1_body": data.get("s1_body", [
f"<b>{biz}</b> este analizat de echipa Advisio. "
f"Raportul complet va fi disponibil în 24-48 de ore.",
]),
"s1_attn": data.get("s1_attn", (
"ATENȚIE — Analiză în curs:",
f"Echipa Advisio cercetează prezența online a {biz} pe TripAdvisor, Google, Instagram )),
"s1_metrics": data.get("s1_metrics", [
("Prezență online", "În analiză", "Optimizat în 30 zile", "CRITICĂ"),
("Social media", "În analiză", "Strategie activă", "RIDICATĂ"),
("Recenzii", "În analiză", "80%+ reply rate", "RIDICATĂ"),
]),
# ── Secțiunea 2 ─────────────────────────────────────────────
"s2_subtitle": f"Sarcini repetitive identificate pentru {biz}",
"losses": data.get("losses", []),
"total_manual": data.get("total_manual", "—"),
"total_ai": data.get("total_ai", "—"),
# ── Secțiunea 3 ─────────────────────────────────────────────
"s3_subtitle": f"Selecție specifică pentru {biz}",
"tools": data.get("tools", [
("ChatGPT", "chatgpt.com", "Gratuit",
"Răspunsuri profesionale la recenzii, postări social media, texte promovare.",
"Recenzii, Social Media"),
("Claude", "claude.ai", "Gratuit (Pro $20/lună opțional)",
"Rescriere meniu cu storytelling culinar, strategii de creștere Instagram.",
"Meniu, Strategie"),
("ManyChat", "manychat.com", "Gratuit până la 1.000 contacte",
"Răspunde automat la DM-uri despre rezervări, program și meniu — 24/7.",
"DM-uri automate"),
]),
# ── Secțiunea 4 ─────────────────────────────────────────────
"s4_subtitle": f"Trei acțiuni prioritare pentru {biz}",
"s4_intro": f"{biz} poate implementa AI în operațiunile zilnice în 30 de zile.",
"weeks": data.get("weeks", []),
# ── Secțiunea 5 ─────────────────────────────────────────────
"s5_subtitle": "Dacă preferi să nu construiești tu sistemul de la zero",
"s5_intro": f"Raportul de față îți arată exact ce trebuie făcut pentru {biz}. "
f"Dacă preferi să primești totul gata, personalizat, în 48 de ore:",
"deliverables": data.get("deliverables", [
("20 răspunsuri la recenzii scrise complet",
"În tonul profesional specific restaurantului tău, pentru toate situațiile: pozitive, ("Calendar de conținut 30 de zile complet scris",
"Postări finalizate pentru Instagram și Facebook, cu hashtag-uri locale și orele ("5 template-uri DM bilingve (RO/EN) gata de salvat",
"Pentru rezervări, program, evenimente, meniu și direcții."),
("Meniu principal rescris cu storytelling culinar",
"Toate preparatele principale cu descrieri narative, gata de publicat pe site."),
("Materiale campanie recenzii",
"Card bilingv gata de tipărit + script verbal + instrucțiuni QR code."),
]),
"urgency_lines": data.get("urgency_lines", [
f"{biz} pierde clienți în fiecare zi din cauza prezenței digitale neoptimizate.",
"Fiecare răspuns neprofesional la o recenzie este citit de sute de potențiali clienți.",
"Pachetul include toate materialele gata de folosit în 48 de ore.",
]),
"s5_closing": (
"Aceasta nu este o vânzare cu presiune. Raportul conține tot ce ai nevoie pentru "Dacă preferi să nu pierzi timp, accesează butonul de mai sus."
),
# ── Teaser specific ─────────────────────────────────────────
"emotional_hook": data.get("emotional_hook",
f"{biz} merită o prezență digitală la fel de bună ca experiența din restaurant."),
"cta_price": "GRATUIT",
}
if __name__ == "__main__":
port = int(os.environ.get("PORT", 8080))
app.run(host="0.0.0.0", port=port, debug=False)
