"""
ADVISIO — Stripe Payment Link
================================
Creează un Payment Link unic per restaurant (97 USD).
Adaugă metadata cu bizName, audit_url și sheet_row astfel încât
webhook-ul să știe ce audit să trimită și ce rând să actualizeze după plată.

Configurare env vars:
    STRIPE_SECRET_KEY → sk_live_... sau sk_test_...
    STRIPE_PRICE_ID   → price_... (creat o singură dată în Stripe Dashboard)
"""
import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")


def create_payment_link(R: dict, audit_url: str) -> str:
    if not stripe.api_key:
        raise ValueError("STRIPE_SECRET_KEY nu este setat.")
    if not PRICE_ID:
        raise ValueError("STRIPE_PRICE_ID nu este setat.")

    biz_name  = R.get("bizName", "Restaurant")
    email     = R.get("email", "")
    city      = R.get("city", "")
    sheet_row = str(R.get("sheet_row", ""))  # rândul din Google Sheet

    link = stripe.PaymentLink.create(
        line_items=[{"price": PRICE_ID, "quantity": 1}],
        metadata={
            "bizName":   biz_name,
            "email":     email,
            "city":      city,
            "audit_url": audit_url,
            "sheet_row": sheet_row,  # ← pentru actualizare status după plată
        },
        after_completion={
            "type": "redirect",
            "redirect": {
                "url": f"https://advisio-landing.vercel.app/confirmare?biz={biz_name}"
            },
        },
    )
    return link.url
