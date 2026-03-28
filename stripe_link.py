"""
ADVISIO — Stripe Payment Link
================================
Creează un Payment Link unic per restaurant (97 USD).
Adaugă metadata cu bizName și audit_url astfel încât
webhook-ul să știe ce audit să trimită după plată.
Configurare env vars:
STRIPE_SECRET_KEY → sk_live_... sau sk_test_...
STRIPE_PRICE_ID → price_... (creat o singură dată în Stripe Dashboard)
"""
import os
import stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
# ID-ul prețului de 97 USD creat în Stripe Dashboard
# Îl creezi o singură dată: Products → Add Product → $97 → one time
PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")
def create_payment_link(R: dict, audit_url: str) -> str:
"""
Creează un Stripe Payment Link unic pentru restaurantul din R.
Returnează URL-ul payment link-ului.
"""
if not stripe.api_key:
raise ValueError("STRIPE_SECRET_KEY nu este setat.")
if not PRICE_ID:
raise ValueError("STRIPE_PRICE_ID nu este setat.")
biz_name = R.get("bizName", "Restaurant")
email = R.get("email", "")
city = R.get("city", "")
# Creează Payment Link cu metadata
# metadata e returnat în webhook după plată
link = stripe.PaymentLink.create(
line_items=[{"price": PRICE_ID, "quantity": 1}],
metadata={
"bizName": biz_name,
"email": email,
"city": city,
"audit_url": audit_url, # URL-ul auditului complet de pe Drive
},
# Pre-completează emailul clientului dacă știm adresa
# (necesită Stripe Checkout, nu Payment Links simple — comentat)
# customer_email=email,
# După plată redirect pe pagina de confirmare
after_completion={
"type": "redirect",
"redirect": {
"url": f"https://advisio-landing.vercel.app/confirmare?biz={biz_name}"
},
},
)
return link.url