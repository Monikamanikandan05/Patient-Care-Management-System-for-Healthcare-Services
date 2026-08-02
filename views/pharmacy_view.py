"""
pharmacy_view.py
Patient-facing pharmacy storefront — browse medicines, cart, checkout, orders.
"""
import os
from datetime import date
import streamlit as st
from core.database import SessionLocal
from services.pharmacy_service import (
    get_all_medicines, get_categories, get_patient_orders, place_order, seed_medicines
)

# Absolute base path for images
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _abs_img(image_path: str) -> str:
    """Convert relative image_path to absolute filesystem path."""
    if not image_path:
        return ""
    return os.path.join(_BASE, image_path.replace("/", os.sep))


def _stock_badge(qty: int) -> str:
    if qty == 0:
        return "<span style='background:#ef444422;color:#ef4444;padding:3px 12px;border-radius:20px;font-size:.75rem;font-weight:700;'>❌ Out of Stock</span>"
    if qty <= 20:
        return f"<span style='background:#f59e0b22;color:#f59e0b;padding:3px 12px;border-radius:20px;font-size:.75rem;font-weight:700;'>⚠️ Low Stock ({qty} left)</span>"
    return f"<span style='background:#22c55e22;color:#22c55e;padding:3px 12px;border-radius:20px;font-size:.75rem;font-weight:700;'>✅ In Stock ({qty})</span>"


def _expiry_badge(expiry_date_val) -> str:
    """Return a colored HTML badge based on expiry proximity."""
    if not expiry_date_val:
        return ""
    today_d = date.today()
    days_left = (expiry_date_val - today_d).days
    if days_left < 0:
        return "<span style='background:#ef444422;color:#ef4444;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:700;'>❌ EXPIRED</span>"
    if days_left <= 180:
        return f"<span style='background:#f59e0b22;color:#f59e0b;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:700;'>⚠️ Exp: {expiry_date_val.strftime('%b %Y')}</span>"
    return f"<span style='background:#22c55e22;color:#22c55e;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:700;'>✅ Exp: {expiry_date_val.strftime('%b %Y')}</span>"


def _display_medicine_image(med, width=None):
    """Display medicine image if the file exists, otherwise a styled placeholder."""
    img_abs = _abs_img(med.image_path)
    if img_abs and os.path.exists(img_abs):
        if width:
            st.image(img_abs, width=width)
        else:
            st.image(img_abs, use_container_width=True)
    else:
        cat_emoji = {
            "Cardiology":    "❤️",
            "Antibiotics":   "🧬",
            "Cough & Cold":  "🍃",
            "Cholesterol":   "🫀",
            "Thyroid":       "🦋",
            "Diabetes":      "💉",
            "Ophthalmology": "👁️",
            "Pain Relief":   "🩹",
            "Dermatology":   "🧴",
        }.get(med.category or "", "💊")
        st.markdown(
            f"""<div style='background:linear-gradient(135deg,{med.color_theme}22,{med.color_theme}08);
                border:2px solid {med.color_theme}55;border-radius:12px;
                height:130px;display:flex;flex-direction:column;align-items:center;
                justify-content:center;gap:6px;'>
                <span style='font-size:2.8rem;'>{cat_emoji}</span>
                <span style='font-size:.7rem;color:{med.color_theme};font-weight:700;'>{med.category}</span>
            </div>""",
            unsafe_allow_html=True,
        )


def render_pharmacy_view():
    db = SessionLocal()
    try:
        seed_medicines(db)
        user = st.session_state.user

        st.markdown(
            """
            <div style="background:linear-gradient(135deg,rgba(16,185,129,.18),rgba(16,185,129,.03));
                        border:1px solid rgba(16,185,129,.35);border-radius:16px;
                        padding:22px 28px;margin-bottom:24px;">
                <h2 style="margin:0;color:#fff;">🛒 <span style="color:#10b981;">Online Pharmacy</span></h2>
                <p style="margin:6px 0 0;color:#9ca3af;font-size:.95rem;">
                    Browse certified medicines &nbsp;·&nbsp; Add to cart &nbsp;·&nbsp; Buy instantly &nbsp;·&nbsp; Order online
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Cart count badge in header
        cart = st.session_state.get("pharma_cart", {})
        cart_count = sum(v["quantity"] for v in cart.values())
        if cart_count > 0:
            st.markdown(
                f"<div style='text-align:right;margin-top:-16px;margin-bottom:12px;'>"
                f"<span style='background:#10b981;color:#fff;padding:4px 16px;border-radius:20px;font-weight:700;'>🛒 {cart_count} item(s) in cart</span></div>",
                unsafe_allow_html=True,
            )

        tab_store, tab_cart, tab_orders = st.tabs([
            "🏪 Browse Medicines",
            f"🛒 My Cart ({cart_count})" if cart_count > 0 else "🛒 My Cart",
            "📦 My Orders"
        ])

        # ─────────────────────────────────────────────────────────────────────
        # TAB 1: Browse
        # ─────────────────────────────────────────────────────────────────────
        with tab_store:
            col_search, col_cat = st.columns([2, 1])
            with col_search:
                search_raw = st.text_input("🔍 Search medicines", placeholder="e.g. Paracetamol, Antibiotic, Insulin…", key="pharma_search")
            with col_cat:
                cats = ["All Categories"] + get_categories(db)
                sel_cat = st.selectbox("Category", cats, key="pharma_cat")

            all_medicines = get_all_medicines(db)

            # ── Live autocomplete suggestions ──────────────────────────────
            search = search_raw.strip()
            if search and len(search) >= 1:
                suggestions = [
                    m for m in all_medicines
                    if search.lower() in m.name.lower()
                    or search.lower() in (m.generic_name or "").lower()
                ]
                if suggestions:
                    st.markdown("<div style='font-size:0.8rem;color:#10b981;font-weight:700;margin:4px 0 2px 0;'>📋 Matching medicines — click to select:</div>", unsafe_allow_html=True)
                    sug_cols = st.columns(min(len(suggestions), 4))
                    for idx, s in enumerate(suggestions[:8]):
                        with sug_cols[idx % min(len(suggestions), 4)]:
                            if st.button(f"💊 {s.name}", key=f"pharma_sug_btn_{s.id}_{idx}", use_container_width=True):
                                st.session_state["pharma_search"] = s.name
                                st.rerun()

            medicines = all_medicines
            if search:
                medicines = [m for m in medicines
                             if search.lower() in m.name.lower()
                             or search.lower() in (m.generic_name or "").lower()
                             or search.lower() in (m.category or "").lower()]
            if sel_cat != "All Categories":
                medicines = [m for m in medicines if m.category == sel_cat]

            if not medicines:
                st.markdown(
                    "<div style='text-align:center;padding:40px;background:rgba(255,255,255,.03);"
                    "border-radius:14px;border:1px dashed rgba(255,255,255,.08);margin-top:10px;'>"
                    "<div style='font-size:2.5rem;'>🔍</div>"
                    "<div style='color:#9ca3af;font-size:1rem;font-weight:600;margin-top:10px;'>"
                    f"No medicines found for <b style='color:#fff;'>'{search}'</b></div>"
                    "<div style='color:#6b7280;font-size:.85rem;margin-top:6px;'>Try a different keyword or browse all categories</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
            else:
                count_html = (
                    f"<p style='color:#9ca3af;font-size:.9rem;'>"
                    f"<span style='color:#10b981;font-weight:700;'>{len(medicines)}</span> medicine(s) "
                    + (f"matching <b style='color:#fff;'>'{search}'</b>" if search else "available")
                    + "</p>"
                )
                st.markdown(count_html, unsafe_allow_html=True)

                cols = st.columns(3)
                for idx, med in enumerate(medicines):
                    with cols[idx % 3]:
                        with st.container():
                            is_expired = med.expiry_date and (med.expiry_date - date.today()).days < 0

                            # Card top border
                            st.markdown(
                                f"""<div style="background:rgba(255,255,255,.04);
                                    border:1px solid {med.color_theme}44;
                                    border-top:4px solid {med.color_theme};
                                    border-radius:14px;padding:14px 14px 6px 14px;
                                    margin-bottom:4px;">
                                    <div style="display:flex;justify-content:space-between;
                                        align-items:center;margin-bottom:10px;">
                                        <span style="background:{med.color_theme}22;color:{med.color_theme};
                                            padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:700;">
                                            {med.category or 'General'}
                                        </span>
                                        {"<span style='font-size:.7rem;color:#a78bfa;font-weight:600;'>Rx</span>" if med.requires_prescription else "<span style='font-size:.7rem;color:#34d399;'>OTC</span>"}
                                    </div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                            _display_medicine_image(med)

                            # Dates row
                            dates_html = ""
                            if med.manufacture_date:
                                dates_html += f"<span style='font-size:.7rem;color:#6b7280;'>🏭 Mfg: {med.manufacture_date.strftime('%b %Y')}</span>"
                            if med.expiry_date:
                                dates_html += f"&nbsp;&nbsp;{_expiry_badge(med.expiry_date)}"

                            st.markdown(
                                f"""<div style="padding:10px 4px 4px 4px;">
                                    <div style="font-weight:700;color:#fff;font-size:.95rem;
                                        margin-bottom:2px;line-height:1.3;">{med.name}</div>
                                    <div style="color:#9ca3af;font-size:.78rem;margin-bottom:6px;">
                                        {med.generic_name or ''} &nbsp;·&nbsp; {med.unit}
                                    </div>
                                    <div style="margin-bottom:6px;">{_stock_badge(med.stock_qty)}</div>
                                    <div style="margin-bottom:6px;">{dates_html}</div>
                                    <div style="font-size:1.3rem;font-weight:900;
                                        color:{med.color_theme};margin:8px 0 4px 0;">
                                        ${float(med.price):.2f}
                                    </div>
                                    <div style="color:#6b7280;font-size:.78rem;margin-bottom:10px;
                                        line-height:1.4;">
                                        {(med.description[:85] + '…') if med.description and len(med.description) > 85 else (med.description or '')}
                                    </div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                            if med.stock_qty > 0 and not is_expired:
                                qty = st.number_input(
                                    "Quantity", min_value=1,
                                    max_value=min(med.stock_qty, 20),
                                    value=1, step=1,
                                    key=f"qty_browse_{med.id}",
                                    label_visibility="collapsed"
                                )
                                btn_col1, btn_col2 = st.columns(2)
                                with btn_col1:
                                    if st.button("🛒 Add to Cart", key=f"add_{med.id}",
                                                 use_container_width=True):
                                        cart = st.session_state.get("pharma_cart", {})
                                        mid = str(med.id)
                                        if mid in cart:
                                            cart[mid]["quantity"] = min(
                                                cart[mid]["quantity"] + qty, med.stock_qty
                                            )
                                        else:
                                            cart[mid] = {
                                                "medicine_id": med.id,
                                                "name": med.name,
                                                "price": float(med.price),
                                                "unit": med.unit,
                                                "quantity": qty,
                                                "color": med.color_theme,
                                                "image_path": med.image_path or "",
                                            }
                                        st.session_state["pharma_cart"] = cart
                                        st.success(f"✅ {med.name} added!")
                                with btn_col2:
                                    if st.button("⚡ Buy Now", key=f"buynow_{med.id}",
                                                 use_container_width=True, type="primary"):
                                        try:
                                            order = place_order(db, user["id"], [
                                                {"medicine_id": med.id, "quantity": qty}
                                            ])
                                            st.success(
                                                f"🎉 Order #{order.id} placed! "
                                                f"**{med.name}** × {qty} — "
                                                f"**${float(order.total_amount):.2f}**"
                                            )
                                            st.balloons()
                                            st.rerun()
                                        except ValueError as e:
                                            st.error(str(e))
                            elif is_expired:
                                st.button("❌ Expired", disabled=True,
                                          use_container_width=True,
                                          key=f"exp_{med.id}")
                            else:
                                st.button("Out of Stock", disabled=True,
                                          use_container_width=True,
                                          key=f"oos_{med.id}")

                            st.markdown("<div style='margin-bottom:16px;'></div>",
                                        unsafe_allow_html=True)

        # ─────────────────────────────────────────────────────────────────────
        # TAB 2: Cart
        # ─────────────────────────────────────────────────────────────────────
        with tab_cart:
            cart = st.session_state.get("pharma_cart", {})

            if not cart:
                st.markdown(
                    """<div style="text-align:center;padding:70px 20px;">
                        <div style="font-size:4rem;">🛒</div>
                        <div style="color:#9ca3af;font-size:1.1rem;margin-top:16px;font-weight:600;">Your cart is empty</div>
                        <div style="color:#6b7280;font-size:.9rem;margin-top:8px;">Go to Browse Medicines to add items</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("### 🛒 Your Cart")
                total = 0.0
                remove_keys = []

                for mid, item in list(cart.items()):
                    subtotal = item["price"] * item["quantity"]
                    total += subtotal

                    col_img, col_info, col_remove = st.columns([1, 5, 1])
                    with col_img:
                        img_abs = _abs_img(item.get("image_path", ""))
                        if img_abs and os.path.exists(img_abs):
                            st.image(img_abs, width=75)
                        else:
                            st.markdown(
                                f"<div style='width:75px;height:75px;background:{item['color']}22;"
                                f"border:2px solid {item['color']}55;border-radius:10px;"
                                f"display:flex;align-items:center;justify-content:center;"
                                f"font-size:1.8rem;'>💊</div>",
                                unsafe_allow_html=True,
                            )
                    with col_info:
                        st.markdown(
                            f"""<div style="background:rgba(255,255,255,.04);
                                border:1px solid {item['color']}44;
                                border-left:4px solid {item['color']};
                                border-radius:10px;padding:12px 16px;">
                                <div style="font-weight:700;color:#fff;font-size:.95rem;">{item['name']}</div>
                                <div style="color:#9ca3af;font-size:.8rem;margin-bottom:8px;">{item['unit']}</div>
                                <div style="display:flex;justify-content:space-between;align-items:center;">
                                    <span style="color:#10b981;font-weight:700;">
                                        ${item['price']:.2f} × {item['quantity']}
                                    </span>
                                    <span style="color:#fff;font-weight:900;font-size:1.05rem;">
                                        ${subtotal:.2f}
                                    </span>
                                </div>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                    with col_remove:
                        if st.button("🗑️", key=f"remove_{mid}",
                                     help="Remove from cart"):
                            remove_keys.append(mid)

                    st.markdown("<div style='margin-bottom:8px;'></div>",
                                unsafe_allow_html=True)

                for k in remove_keys:
                    del cart[k]
                st.session_state["pharma_cart"] = cart
                if remove_keys:
                    st.rerun()

                # Order total
                st.markdown(
                    f"""<div style="background:linear-gradient(135deg,rgba(16,185,129,.18),rgba(16,185,129,.04));
                        border:1px solid rgba(16,185,129,.4);border-radius:14px;
                        padding:20px 24px;margin-top:20px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <div style="color:#9ca3af;font-size:.85rem;">Order Total</div>
                                <div style="font-size:1.9rem;font-weight:900;color:#10b981;">${total:.2f}</div>
                            </div>
                            <div style="color:#9ca3af;font-size:.9rem;">{sum(v['quantity'] for v in cart.values())} item(s)</div>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                st.markdown("<br>", unsafe_allow_html=True)
                col_clear, col_checkout = st.columns([1, 2])
                with col_clear:
                    if st.button("🗑️ Clear Cart", use_container_width=True):
                        st.session_state["pharma_cart"] = {}
                        st.rerun()
                with col_checkout:
                    if st.button("✅ Place Order Now", use_container_width=True,
                                 type="primary"):
                        cart_items = [
                            {"medicine_id": v["medicine_id"], "quantity": v["quantity"]}
                            for v in cart.values()
                        ]
                        try:
                            order = place_order(db, user["id"], cart_items)
                            st.session_state["pharma_cart"] = {}
                            st.success(
                                f"🎉 Order #{order.id} placed! "
                                f"Total: **${float(order.total_amount):.2f}**"
                            )
                            st.balloons()
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

        # ─────────────────────────────────────────────────────────────────────
        # TAB 3: My Orders
        # ─────────────────────────────────────────────────────────────────────
        with tab_orders:
            st.markdown("### 📦 My Order History")
            orders = get_patient_orders(db, user["id"])

            if not orders:
                st.markdown(
                    """<div style="text-align:center;padding:70px 20px;">
                        <div style="font-size:4rem;">📦</div>
                        <div style="color:#9ca3af;font-size:1.1rem;margin-top:16px;font-weight:600;">No orders yet</div>
                        <div style="color:#6b7280;font-size:.9rem;margin-top:8px;">Your pharmacy orders will appear here</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"<p style='color:#9ca3af;'>{len(orders)} order(s)</p>",
                            unsafe_allow_html=True)
                status_colors = {
                    "Pending":   "#f59e0b",
                    "Confirmed": "#3b82f6",
                    "Delivered": "#22c55e",
                    "Cancelled": "#ef4444",
                }
                status_icons = {
                    "Pending":   "⏳",
                    "Confirmed": "✅",
                    "Delivered": "🚚",
                    "Cancelled": "❌",
                }
                for order in orders:
                    sc = status_colors.get(order.status, "#9ca3af")
                    si = status_icons.get(order.status, "📋")
                    with st.expander(
                        f"Order #{order.id}  ·  "
                        f"{order.created_at.strftime('%d %b %Y, %I:%M %p')}  ·  "
                        f"${float(order.total_amount):.2f}  ·  {si} {order.status}"
                    ):
                        for it in order.items:
                            med = it.medicine
                            st.markdown(
                                f"""<div style="display:flex;justify-content:space-between;
                                    padding:8px 14px;background:rgba(255,255,255,.04);
                                    border-radius:8px;margin-bottom:6px;align-items:center;">
                                    <span style="color:#fff;font-weight:600;">
                                        💊 {med.name if med else 'Unknown'}
                                    </span>
                                    <span style="color:#9ca3af;font-size:.85rem;">
                                        Qty: {it.quantity} × ${float(it.unit_price):.2f}
                                    </span>
                                    <span style="color:#10b981;font-weight:700;">
                                        ${float(it.unit_price * it.quantity):.2f}
                                    </span>
                                </div>""",
                                unsafe_allow_html=True,
                            )
                        st.markdown(
                            f"""<div style="display:flex;justify-content:space-between;
                                align-items:center;margin-top:12px;padding:12px;
                                background:rgba(255,255,255,.03);border-radius:8px;">
                                <span style="background:{sc}22;color:{sc};padding:4px 14px;
                                    border-radius:20px;font-size:.82rem;font-weight:700;">
                                    {si} {order.status}
                                </span>
                                <span style="font-size:1.1rem;font-weight:900;color:#fff;">
                                    Total: <span style="color:{sc};">${float(order.total_amount):.2f}</span>
                                </span>
                            </div>""",
                            unsafe_allow_html=True,
                        )

    finally:
        db.close()


def render_doctor_pharmacy_view():
    """Doctor-facing read-only pharmacy reference view."""
    db = SessionLocal()
    try:
        seed_medicines(db)
        from services.pharmacy_service import get_all_orders
        from models.models import PharmacyOrder

        st.markdown(
            """
            <div style="background:linear-gradient(135deg,rgba(59,130,246,.18),rgba(59,130,246,.03));
                        border:1px solid rgba(59,130,246,.35);border-radius:16px;
                        padding:22px 28px;margin-bottom:24px;">
                <h2 style="margin:0;color:#fff;">🩺 <span style="color:#3b82f6;">Hospital Pharmacy Reference</span> <span style="font-size:.85rem;background:#3b82f633;color:#60a5fa;padding:4px 12px;border-radius:20px;margin-left:10px;">Read-Only Mode</span></h2>
                <p style="margin:6px 0 0;color:#9ca3af;font-size:.95rem;">
                    Inspect available pharmacy stock, generic formulations, pricing, and batch dates to assist with patient prescriptions.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_inventory, tab_orders = st.tabs([
            "💊 Inventory & Stock Lookup",
            "🧾 Patient Orders Log"
        ])

        with tab_inventory:
            col_search, col_cat = st.columns([2, 1])
            with col_search:
                search_raw = st.text_input("🔍 Search medicines", placeholder="e.g. Paracetamol, Antibiotic, Metformin…", key="doc_pharma_search")
            with col_cat:
                cats = ["All Categories"] + get_categories(db)
                sel_cat = st.selectbox("Category", cats, key="doc_pharma_cat")

            all_medicines = get_all_medicines(db, include_inactive=False)

            # ── Live autocomplete suggestions ──────────────────────────────
            search = search_raw.strip()
            if search and len(search) >= 1:
                suggestions = [
                    m for m in all_medicines
                    if search.lower() in m.name.lower()
                    or search.lower() in (m.generic_name or "").lower()
                ]
                if suggestions:
                    st.markdown("<div style='font-size:0.8rem;color:#3b82f6;font-weight:700;margin:4px 0 2px 0;'>📋 Matching medicines — click to select:</div>", unsafe_allow_html=True)
                    sug_cols = st.columns(min(len(suggestions), 4))
                    for idx, s in enumerate(suggestions[:8]):
                        with sug_cols[idx % min(len(suggestions), 4)]:
                            if st.button(f"💊 {s.name}", key=f"doc_pharma_sug_btn_{s.id}_{idx}", use_container_width=True):
                                st.session_state["doc_pharma_search"] = s.name
                                st.rerun()

            medicines = all_medicines
            if search:
                medicines = [m for m in medicines
                             if search.lower() in m.name.lower()
                             or search.lower() in (m.generic_name or "").lower()
                             or search.lower() in (m.category or "").lower()]
            if sel_cat != "All Categories":
                medicines = [m for m in medicines if m.category == sel_cat]

            if not medicines:
                st.markdown(
                    "<div style='text-align:center;padding:40px;background:rgba(255,255,255,.03);"
                    "border-radius:14px;border:1px dashed rgba(255,255,255,.08);margin-top:10px;'>"
                    "<div style='font-size:2.5rem;'>🔍</div>"
                    "<div style='color:#9ca3af;font-size:1rem;font-weight:600;margin-top:10px;'>"
                    f"No medicines found for <b style='color:#fff;'>'{search}'</b></div>"
                    "<div style='color:#6b7280;font-size:.85rem;margin-top:6px;'>Try a different keyword or browse all categories</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
            else:
                count_html = (
                    f"<p style='color:#9ca3af;font-size:.9rem;'>"
                    f"<span style='color:#3b82f6;font-weight:700;'>{len(medicines)}</span> medicine(s) in active inventory"
                    + (f" matching <b style='color:#fff;'>'{search}'</b>" if search else "")
                    + "</p>"
                )
                st.markdown(count_html, unsafe_allow_html=True)

                cols = st.columns(3)
                for idx, med in enumerate(medicines):
                    with cols[idx % 3]:
                        with st.container():
                            is_expired = med.expiry_date and (med.expiry_date - date.today()).days < 0

                            st.markdown(
                                f"""<div style="background:rgba(255,255,255,.04);
                                    border:1px solid {med.color_theme}44;
                                    border-top:4px solid {med.color_theme};
                                    border-radius:14px;padding:14px 14px 6px 14px;
                                    margin-bottom:4px;">
                                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                                        <span style="background:{med.color_theme}22;color:{med.color_theme};
                                            padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:700;">
                                            {med.category or 'General'}
                                        </span>
                                        {"<span style='font-size:.7rem;color:#a78bfa;font-weight:600;'>Rx Required</span>" if med.requires_prescription else "<span style='font-size:.7rem;color:#34d399;'>OTC</span>"}
                                    </div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                            _display_medicine_image(med)

                            dates_html = ""
                            if med.manufacture_date:
                                dates_html += f"<span style='font-size:.7rem;color:#6b7280;'>🏭 Mfg: {med.manufacture_date.strftime('%b %Y')}</span>"
                            if med.expiry_date:
                                dates_html += f"&nbsp;&nbsp;{_expiry_badge(med.expiry_date)}"

                            st.markdown(
                                f"""<div style="padding:10px 4px 10px 4px;">
                                    <div style="font-weight:700;color:#fff;font-size:.95rem;margin-bottom:2px;">{med.name}</div>
                                    <div style="color:#9ca3af;font-size:.78rem;margin-bottom:6px;">
                                        <b>Generic:</b> {med.generic_name or 'N/A'} &nbsp;·&nbsp; {med.unit}
                                    </div>
                                    <div style="margin-bottom:6px;">{_stock_badge(med.stock_qty)}</div>
                                    <div style="margin-bottom:6px;">{dates_html}</div>
                                    <div style="font-size:1.1rem;font-weight:800;color:{med.color_theme};margin-top:6px;">
                                        ${float(med.price):.2f} <span style="font-size:.75rem;color:#9ca3af;font-weight:400;">/ {med.unit}</span>
                                    </div>
                                    <div style="color:#6b7280;font-size:.78rem;margin-top:6px;line-height:1.4;">
                                        {med.description or ''}
                                    </div>
                                </div>""",
                                unsafe_allow_html=True,
                            )
                            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

        with tab_orders:
            st.markdown("#### 🧾 All Patient Pharmacy Orders (Read-Only)")
            all_orders = get_all_orders(db)
            if not all_orders:
                st.info("No patient pharmacy orders placed yet.")
            else:
                from models.models import User
                status_colors = {"Pending": "#f59e0b", "Confirmed": "#3b82f6", "Delivered": "#22c55e", "Cancelled": "#ef4444"}
                status_icons  = {"Pending": "⏳", "Confirmed": "✅", "Delivered": "🚚", "Cancelled": "❌"}

                for order in all_orders:
                    patient = db.query(User).filter(User.id == order.patient_id).first()
                    sc = status_colors.get(order.status, "#9ca3af")
                    si = status_icons.get(order.status, "📋")
                    with st.expander(
                        f"Order #{order.id}  ·  Patient: {patient.full_name if patient else 'Unknown'}  ·  "
                        f"${float(order.total_amount):.2f}  ·  {si} {order.status}  ·  "
                        f"{order.created_at.strftime('%d %b %Y, %I:%M %p')}"
                    ):
                        for it in order.items:
                            med = it.medicine
                            st.markdown(
                                f"""<div style="display:flex;justify-content:space-between;
                                    padding:8px 14px;background:rgba(255,255,255,.04);
                                    border-radius:8px;margin-bottom:6px;align-items:center;">
                                    <span style="color:#fff;font-weight:600;">💊 {med.name if med else 'Unknown'}</span>
                                    <span style="color:#9ca3af;font-size:.85rem;">Qty: {it.quantity} × ${float(it.unit_price):.2f}</span>
                                    <span style="color:#10b981;font-weight:700;">${float(it.unit_price * it.quantity):.2f}</span>
                                </div>""",
                                unsafe_allow_html=True,
                            )
                        st.markdown(
                            f"""<div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;padding:10px;background:rgba(255,255,255,.03);border-radius:8px;">
                                <span style="background:{sc}22;color:{sc};padding:4px 14px;border-radius:20px;font-size:.82rem;font-weight:700;">{si} {order.status}</span>
                                <span style="font-size:1.05rem;font-weight:800;color:#fff;">Total: <span style="color:{sc};">${float(order.total_amount):.2f}</span></span>
                            </div>""",
                            unsafe_allow_html=True,
                        )

    finally:
        db.close()

