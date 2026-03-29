"""
ADVISIO — Stripe Webhook Handler
==================================
Primește evenimentul `checkout.session.completed` de la Stripe
după ce clientul plătește 97 USD.
Extrage metadata (email + audit_url) și trimite emailul cu auditul complet.
Adaugă în main.py:
    from webhook import stripe_webhook
    app.register_blueprint(stripe_webhook)
Configurare env vars:
    STRIPE_WEBHOOK_SECRET → whsec_... (din Stripe Dashboard → Webhooks)
    GMAIL_USER            → advisioai@gmail.com
    GMAIL_APP_PASSWORD    → parola de aplicație Gmail (nu parola contului)
"""
import os, json, requests, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import stripe
from flask import Blueprint, request, jsonify

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
stripe_webhook = Blueprint("stripe_webhook", __name__)

WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
GMAIL_USER     = os.environ.get("GMAIL_USER", "advisioai@gmail.com")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
BRAND_NAME     = "Advisio"


@stripe_webhook.route("/webhook/stripe", methods=["POST"])
def handle_webhook():
    payload = request.data
    sig     = request.headers.get("Stripe-Signature", "")

    # Verifică semnătura Stripe
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Procesăm doar plățile confirmate
    if event["type"] == "checkout.session.completed":
        session  = event["data"]["object"]
        metadata = session.get("metadata", {})
        email    = metadata.get("email") or session.get("customer_details", {}).get("email")
        biz_name = metadata.get("bizName", "restaurantul tău")
        audit_url = metadata.get("audit_url", "")

        if email and audit_url:
            try:
                send_audit_email(email, biz_name, audit_url)
            except Exception as e:
                print(f"Email error: {e}")
                # Nu returnăm eroare către Stripe — Stripe va retry altfel
        else:
            print(f"Webhook: date lipsă — email={email}, audit_url={audit_url}")

    return jsonify({"received": True}), 200


def send_audit_email(to_email: str, biz_name: str, audit_url: str):
    """
    Trimite emailul cu auditul complet după plată.
    Atașează PDF-ul descărcat de pe Drive.
    """
    first_name = to_email.split("@")[0].capitalize()
    subject    = f"Auditul tău complet Advisio — {biz_name}"

    html = f"""<!DOCTYPE html>
<html lang="ro">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f2ede3;font-family:Georgia,'Times New Roman',serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f2ede3;padding:40px 16px;">
  <tr><td align="center">
    <table width="580" cellpadding="0" cellspacing="0" style="max-width:580px;width:100%;">

      <!-- HEADER -->
      <tr>
        <td style="background:#0f1b2d;border-radius:14px 14px 0 0;padding:28px 36px;">
          <div style="font-family:Georgia,serif;font-size:18px;font-weight:600;color:#ffffff;">Advisio</div>
          <div style="font-size:9px;font-family:Helvetica,Arial,sans-serif;letter-spacing:0.12em;color:#c9a84c;">AI AUDIT RESTAURANT</div>
        </td>
      </tr>

      <!-- BODY -->
      <tr>
        <td style="background:#0f1b2d;padding:36px;">
          <h1 style="font-family:Georgia,serif;font-size:26px;color:#ffffff;margin:0 0 16px;">
            Auditul complet pentru <em style="color:#e2c47a;">{biz_name}</em> este gata.
          </h1>
          <p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;color:rgba(255,255,255,0.6);line-height:1.6;margin:0 0 24px;">
            Bună {first_name},<br><br>
            Mulțumim pentru încredere. Găsești auditul complet atașat la acest email
            și disponibil pentru download la linkul de mai jos.
          </p>

          <!-- BUTON DOWNLOAD -->
          <table cellpadding="0" cellspacing="0">
            <tr>
              <td style="background:#c9a84c;border-radius:8px;padding:14px 28px;">
                <a href="{audit_url}"
                   style="font-family:Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;color:#0f1b2d;text-decoration:none;">
                  ↓ Descarcă Auditul Complet (PDF)
                </a>
              </td>
            </tr>
          </table>

          <p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;color:rgba(255,255,255,0.4);line-height:1.6;margin:24px 0 0;">
            Auditul include: diagnosticul complet al prezenței digitale, cele 5 pierderi de timp
            cu soluții AI, instrumentele recomandate și planul de acțiune pe 30 de zile.<br><br>
            Întrebări? Scrie-ne la advisioai@gmail.com
          </p>
        </td>
      </tr>

      <!-- FOOTER -->
      <tr>
        <td style="background:#0f1b2d;border-radius:0 0 14px 14px;padding:20px 36px;border-top:1px solid rgba(255,255,255,0.08);">
          <p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;color:rgba(255,255,255,0.3);margin:0;">
            Advisio AI Audit · 2026
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    text = (
        f"Bună {first_name},\n\n"
        f"Auditul complet pentru {biz_name} este gata.\n\n"
        f"Descarcă-l aici: {audit_url}\n\n"
        f"Întrebări? advisioai@gmail.com\n\nAdvisio AI Audit"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{BRAND_NAME} <{GMAIL_USER}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    # Atașează PDF-ul descărcat de pe Drive
    try:
        r = requests.get(audit_url, timeout=30)
        if r.status_code == 200:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(r.content)
            encoders.encode_base64(part)
            safe_name = "".join(c for c in biz_name if c.isalnum() or c in " _-").strip()
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="Audit_Advisio_{safe_name}.pdf"',
            )
            msg.attach(part)
    except Exception as e:
        print(f"Nu am putut atașa PDF-ul: {e} — emailul se trimite fără atașament")

    # Trimite via Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
    print(f"✓ Email audit trimis către {to_email} pentru {biz_name}")
