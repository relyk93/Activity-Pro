import stripe
import streamlit as st

def _get_stripe_key() -> str:
    try:
        return st.secrets.get("STRIPE_SECRET_KEY", "")
    except Exception:
        return ""

def _get_price_id() -> str:
    try:
        return st.secrets.get("STRIPE_PRICE_ID", "")
    except Exception:
        return ""

def _get_publishable_key() -> str:
    try:
        return st.secrets.get("STRIPE_PUBLISHABLE_KEY", "")
    except Exception:
        return ""

def stripe_configured() -> bool:
    return bool(_get_stripe_key() and _get_price_id())

def create_checkout_session(facility_name: str, admin_email: str, app_url: str) -> str | None:
    """Create a Stripe Checkout Session and return the URL."""
    key = _get_stripe_key()
    price_id = _get_price_id()
    if not key or not price_id:
        return None

    stripe.api_key = key
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=admin_email or None,
            metadata={"facility_name": facility_name},
            success_url=f"{app_url}?stripe_success=1&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{app_url}?stripe_cancelled=1",
            allow_promotion_codes=True,
        )
        return session.url
    except stripe.StripeError as e:
        st.error(f"Stripe error: {e.user_message}")
        return None

def verify_checkout_session(session_id: str) -> dict | None:
    """Verify a completed Checkout Session and return subscription info."""
    key = _get_stripe_key()
    if not key:
        return None

    stripe.api_key = key
    try:
        session = stripe.checkout.Session.retrieve(session_id, expand=["subscription"])
        if session.payment_status == "paid":
            sub = session.subscription
            return {
                "stripe_customer_id":     session.customer,
                "stripe_subscription_id": sub.id if sub else None,
                "status":                 sub.status if sub else "active",
                "current_period_end":     sub.current_period_end if sub else None,
            }
    except stripe.StripeError:
        pass
    return None

def create_portal_session(customer_id: str, app_url: str) -> str | None:
    """Create a Stripe Customer Portal session (manage/cancel subscription)."""
    key = _get_stripe_key()
    if not key or not customer_id:
        return None

    stripe.api_key = key
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=app_url,
        )
        return session.url
    except stripe.StripeError:
        return None
