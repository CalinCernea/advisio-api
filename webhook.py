"""
ADVISIO — Stripe Webhook Handler
==================================
Primește evenimentul `checkout.session.completed` de la Stripe
după ce clientul plătește 97 USD.
Extrage metadata (email + audit_url) și delegă trimiterea emailului
către Google Apps Script (care folosește GmailApp — fără SMTP blocat).

Configurare env vars:
    STRIPE_WEBHOOK_SECRET → whsec_... (din Stripe Dashboard → Webhooks)
    APPS_SCRIPT_URL       → URL-ul de deployment al Apps Script (doPost)
    APPS_SCRIPT_SECRET    → advisio_as_secret_2026 (același ca în Code.gs)
"""
import os
import requests
import stripe
from flask import Blueprint, request, jsonify

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
stripe_webhook = Blueprint("stripe_webhook", __name__)

WEBHOOK_SECRET     = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
APPS_SCRIPT_URL    = os.environ.get("APPS_SCRIPT_URL", "")
APPS_SCRIPT_SECRET = os.environ.get("APPS_SCRIPT_SECRET", "advisio_as_secret_2026")


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
        metadata = session.get("metadata") or {}

        # Fallback: citim metadata de pe PaymentLink dacă nu e pe session
        if not metadata.get("audit_url"):
            payment_link_id = session.get("payment_link")
            if payment_link_id:
                try:
                    pl = stripe.PaymentLink.retrieve(payment_link_id)
                    metadata = pl.metadata or {}
                    print(f"Metadata recuperată de pe PaymentLink {payment_link_id}")
                except Exception as e:
                    print(f"Nu am putut recupera PaymentLink metadata: {e}")

        email     = metadata.get("email") or session.get("customer_details", {}).get("email", "")
        biz_name  = metadata.get("bizName", "restaurantul tău")
        audit_url = metadata.get("audit_url", "")

        print(f"Webhook primit — email: {email} | biz: {biz_name} | audit_url: {audit_url[:60] if audit_url else 'LIPSĂ'}")

        if email and audit_url:
            try:
                send_via_apps_script(email, biz_name, audit_url)
            except Exception as e:
                print(f"Apps Script error: {e}")
        else:
            print(f"Webhook: date lipsă — email={email}, audit_url prezent={bool(audit_url)}")

    # Răspundem imediat 200 către Stripe — nu așteptăm emailul
    return jsonify({"received": True}), 200


def send_via_apps_script(email: str, biz_name: str, audit_url: str):
    """
    Trimite un POST către Google Apps Script care va folosi GmailApp
    pentru a trimite emailul cu auditul complet.
    Apps Script rulează pe serverele Google — fără restricții SMTP.
    """
    if not APPS_SCRIPT_URL:
        print("APPS_SCRIPT_URL nu este setat — emailul nu poate fi trimis!")
        return

    payload = {
        "action":   "send_audit_email",
        "secret":   APPS_SCRIPT_SECRET,
        "email":    email,
        "bizName":  biz_name,
        "auditUrl": audit_url,
    }

    response = requests.post(
        APPS_SCRIPT_URL,
        json=payload,
        timeout=30,
    )

    if response.status_code == 200:
        result = response.json()
        if result.get("sent"):
            print(f"✓ Email audit trimis via Apps Script către {email}")
        else:
            print(f"Apps Script response neașteptat: {result}")
    else:
        print(f"Apps Script error: HTTP {response.status_code} — {response.text[:200]}")
        raise Exception(f"Apps Script HTTP {response.status_code}")
