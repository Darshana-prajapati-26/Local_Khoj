from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import HttpResponse
from .models import Order, OrderItem, Coupon, Payment
from cart.models import Cart
from core.models import Notification
from django.conf import settings
import hmac, hashlib
import stripe
try:
    import razorpay
except Exception:
    razorpay = None


@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or cart.items.count() == 0:
        return redirect("cart_view")

    total = cart.get_total()
    
    if request.method == "POST":
        code = request.POST.get("coupon") or ""
        delivery_name = request.POST.get("delivery_name")
        delivery_phone = request.POST.get("delivery_phone")
        delivery_address = request.POST.get("delivery_address")
        
        discount = 0
        applied_coupon = None
        if code:
            c = Coupon.objects.filter(code=code, active=True).first()
            if c:
                if c.type == "percent":
                    discount = total * (c.value / 100)
                else:
                    discount = c.value
                if discount > total:
                    discount = total
                applied_coupon = c

        is_service = any(item.service for item in cart.items.all())

        order = Order.objects.create(
            user=request.user, 
            total_amount=total - discount,
            delivery_name=delivery_name,
            delivery_phone=delivery_phone,
            delivery_address=delivery_address,
            is_service_order=is_service
        )
        
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                service=item.service,
                quantity=item.quantity,
                price=item.get_unit_price()
            )
            # ── Deduct stock for products ──
            if item.product:
                product = item.product
                product.stock = max(0, product.stock - item.quantity)
                product.save(update_fields=['stock'])

                # Notify vendor if stock is low (≤ 5)
                LOW_STOCK_THRESHOLD = 5
                if product.stock <= LOW_STOCK_THRESHOLD:
                    Notification.objects.create(
                        user=product.store.vendor,
                        notification_type='system',
                        title=f'Low stock alert: {product.name}',
                        body=(
                            f'Only {product.stock} unit{"s" if product.stock != 1 else ""} left for '
                            f'"{product.name}". Please restock soon.'
                        ),
                        related_store=product.store,
                    )

        cart.items.all().delete()

        if applied_coupon:
            applied_coupon.used_count = (applied_coupon.used_count or 0) + 1
            applied_coupon.save()

        # Default to COD/Pending for this simplified flow
        Payment.objects.create(user=request.user, provider="cod", amount=order.total_amount, order=order, status="pending")
        Notification.objects.create(
            user=request.user,
            notification_type='payment',
            title="Order placed successfully",
            body=f"Order #{order.id} has been placed. Total: ₹{order.total_amount}",
            link_url=f"/orders/order/{order.id}/"
        )
        django_messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect("order_detail", order_id=order.id)
    
    return redirect("cart_view")



@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = Payment.objects.filter(order=order).order_by("-id").first()
    return render(request, "orders/order_detail.html", {"order": order, "payment": payment})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "orders/order_history.html", {"orders": orders})


@login_required
def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
    except Exception:
        return HttpResponse("PDF generation library missing", status=500)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # ── Palette ────────────────────────────────────────────────
    C_CYAN    = colors.HexColor('#00d2ff')
    C_BLUE    = colors.HexColor('#3a7bd5')
    C_DARK    = colors.HexColor('#0a0b10')
    C_DARK2   = colors.HexColor('#111827')
    C_SLATE   = colors.HexColor('#1e293b')
    C_BODY    = colors.HexColor('#334155')
    C_MUTED   = colors.HexColor('#64748b')
    C_LIGHT   = colors.HexColor('#f8fafc')
    C_BORDER  = colors.HexColor('#e2e8f0')
    C_GREEN   = colors.HexColor('#10b981')
    C_YELLOW  = colors.HexColor('#f59e0b')
    C_WHITE   = colors.white
    C_L1      = colors.HexColor('#00a8ff')   # L
    C_L2      = colors.HexColor('#0097e6')   # c
    C_L3      = colors.HexColor('#44bd32')   # a
    C_L4      = colors.HexColor('#4cd137')   # l
    C_HINDI   = colors.HexColor('#00c8f0')   # खोज

    # ── Helpers ────────────────────────────────────────────────
    def draw_logo_header(cx, cy, eng_size=22, hin_size=14):
        """Draw  L○cal  on one line, खोज below — white/coloured version for dark bg."""
        # L
        c.setFont("Helvetica-Bold", eng_size)
        c.setFillColor(C_L1)
        c.drawString(cx, cy, "L")
        x = cx + c.stringWidth("L", "Helvetica-Bold", eng_size)
        # ○ (search circle)
        si = int(eng_size * 0.82)
        c.setFont("Helvetica-Bold", si)
        c.setFillColor(C_WHITE)
        c.drawString(x, cy + 1, "\u25cb")
        x += c.stringWidth("\u25cb", "Helvetica-Bold", si)
        # cal
        c.setFont("Helvetica-Bold", eng_size)
        c.setFillColor(C_L2); c.drawString(x, cy, "c"); x += c.stringWidth("c","Helvetica-Bold",eng_size)
        c.setFillColor(C_L3); c.drawString(x, cy, "a"); x += c.stringWidth("a","Helvetica-Bold",eng_size)
        c.setFillColor(C_L4); c.drawString(x, cy, "l")
        # खोज  (romanised since PDF can't embed Devanagari without TTF)
        # We render it as stylised "Khoj" with a dot above to hint at Hindi
        c.setFont("Helvetica-Bold", hin_size)
        c.setFillColor(C_HINDI)
        c.drawString(cx + c.stringWidth("L","Helvetica-Bold",eng_size) + 2,
                     cy - hin_size - 2, "Khoj")

    def draw_logo_watermark(cx, cy, eng_size=70, hin_size=42, alpha=0.045):
        """Centred diagonal watermark — two lines: L○cal / Khoj."""
        c.saveState()
        c.setFillColor(C_CYAN)
        c.setFillAlpha(alpha)
        c.translate(cx, cy)
        c.rotate(32)
        c.setFont("Helvetica-Bold", eng_size)
        c.drawCentredString(0, 20, "L\u25cbcal")
        c.setFont("Helvetica-Bold", hin_size)
        c.drawCentredString(0, 20 - eng_size - 4, "Khoj")
        c.restoreState()

    # ── WATERMARK (drawn first so everything else is on top) ───
    draw_logo_watermark(W / 2, H / 2)

    # ── HEADER BAND ────────────────────────────────────────────
    HEADER_H = 1.55 * inch
    c.setFillColor(C_DARK)
    c.rect(0, H - HEADER_H, W, HEADER_H, fill=1, stroke=0)
    # Cyan top stripe
    c.setFillColor(C_CYAN)
    c.rect(0, H - 3, W, 3, fill=1, stroke=0)
    # Blue bottom stripe
    c.setFillColor(C_BLUE)
    c.rect(0, H - HEADER_H, W, 2, fill=1, stroke=0)

    # Logo (top-left of header)
    draw_logo_header(0.45 * inch, H - 0.72 * inch, eng_size=22, hin_size=13)

    # Tagline
    c.setFont("Helvetica", 7.5)
    c.setFillColor(C_MUTED)
    c.drawString(0.45 * inch, H - 1.22 * inch, "Find Everything Near You  \u2022  localkhoj.com")

    # INVOICE title
    c.setFont("Helvetica-Bold", 34)
    c.setFillColor(C_CYAN)
    c.drawRightString(W - 0.45 * inch, H - 0.72 * inch, "INVOICE")

    # Order number + date
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(C_WHITE)
    c.drawRightString(W - 0.45 * inch, H - 0.98 * inch, f"Order  #{order.id:04d}")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(C_MUTED)
    c.drawRightString(W - 0.45 * inch, H - 1.14 * inch,
                      f"Date: {order.created_at.strftime('%d %b, %Y')}")

    # Status pill
    st = order.status
    pill_col = C_GREEN if st in ('delivered','completed') else \
               C_CYAN  if st in ('shipped','out_for_delivery') else \
               C_YELLOW
    c.setFillColor(pill_col)
    st_label = order.get_status_display().upper()
    st_w = c.stringWidth(st_label, "Helvetica-Bold", 7.5) + 14
    pill_x = W - 0.45 * inch - st_w
    c.roundRect(pill_x, H - 1.42 * inch, st_w, 13, 4, fill=1, stroke=0)
    c.setFillColor(C_DARK)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(pill_x + 7, H - 1.34 * inch, st_label)

    # ── BILL TO / SHIP TO ──────────────────────────────────────
    INFO_Y = H - 1.85 * inch
    BOX_H  = 0.95 * inch
    BOX_W  = 2.9 * inch
    GAP    = 0.25 * inch

    for i, (label, col, name, line2, line3) in enumerate([
        ("BILL TO", C_CYAN,
         order.user.get_full_name() or order.user.username,
         order.user.email or "—", ""),
        ("SHIP TO", C_BLUE,
         order.delivery_name or order.user.username,
         order.delivery_phone or "—",
         (order.delivery_address or "")[:50]),
    ]):
        bx = 0.45 * inch + i * (BOX_W + GAP)
        # Card bg
        c.setFillColor(C_LIGHT)
        c.roundRect(bx, INFO_Y - BOX_H + 0.1*inch, BOX_W, BOX_H, 6, fill=1, stroke=0)
        # Left accent
        c.setFillColor(col)
        c.roundRect(bx, INFO_Y - BOX_H + 0.1*inch, 3.5, BOX_H, 3, fill=1, stroke=0)
        # Label
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(col)
        c.drawString(bx + 10, INFO_Y, label)
        # Name
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(C_SLATE)
        c.drawString(bx + 10, INFO_Y - 14, name[:36])
        # Lines
        c.setFont("Helvetica", 8.5)
        c.setFillColor(C_MUTED)
        c.drawString(bx + 10, INFO_Y - 27, line2[:40])
        if line3:
            c.drawString(bx + 10, INFO_Y - 40, line3)

    # ── TABLE ──────────────────────────────────────────────────
    TBL_Y = INFO_Y - BOX_H - 0.2 * inch
    ROW_H = 20
    COL_QTY  = 0.45 * inch
    COL_DESC = 1.1  * inch
    COL_UP   = W - 1.9 * inch
    COL_TOT  = W - 0.45 * inch

    # Table header
    c.setFillColor(C_DARK2)
    c.rect(0.45 * inch, TBL_Y - 4, W - 0.9 * inch, ROW_H, fill=1, stroke=0)
    c.setFillColor(C_CYAN)
    c.rect(0.45 * inch, TBL_Y - 4, 4, ROW_H, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(C_WHITE)
    c.drawString(COL_QTY + 6, TBL_Y + 4, "QTY")
    c.drawString(COL_DESC, TBL_Y + 4, "DESCRIPTION")
    c.drawRightString(COL_UP, TBL_Y + 4, "UNIT PRICE")
    c.drawRightString(COL_TOT, TBL_Y + 4, "TOTAL")

    y = TBL_Y - 4  # cursor below header

    # Group items by store
    by_store = {}
    for item in order.items.all():
        st_obj = (item.product.store if item.product else None) or \
                 (item.service.store if item.service else None)
        sid = st_obj.id if st_obj else 0
        if sid not in by_store:
            by_store[sid] = {'store': st_obj, 'items': []}
        by_store[sid]['items'].append(item)

    grand = 0.0
    row_idx = 0

    for sid, grp in by_store.items():
        st_obj = grp['store']

        # Store sub-header
        y -= ROW_H
        if y < 1.9 * inch:
            c.showPage(); y = H - 0.6 * inch
            draw_logo_watermark(W/2, H/2)

        c.setFillColor(colors.HexColor('#eef6ff'))
        c.rect(0.45*inch, y-3, W-0.9*inch, ROW_H-2, fill=1, stroke=0)
        c.setFillColor(C_BLUE)
        c.rect(0.45*inch, y-3, 3, ROW_H-2, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(C_BLUE)
        c.drawString(COL_DESC, y+5, f"Store: {st_obj.name if st_obj else 'Local Khoj'}")
        if st_obj and st_obj.phone:
            c.setFont("Helvetica", 7.5)
            c.setFillColor(C_MUTED)
            c.drawRightString(COL_TOT, y+5, st_obj.phone)

        for item in grp['items']:
            y -= ROW_H
            if y < 1.9 * inch:
                c.showPage(); y = H - 0.6 * inch
                draw_logo_watermark(W/2, H/2)

            # Alternating row
            if row_idx % 2 == 0:
                c.setFillColor(C_LIGHT)
                c.rect(0.45*inch, y-3, W-0.9*inch, ROW_H-1, fill=1, stroke=0)
            row_idx += 1

            name = item.product.name if item.product else item.service.name
            up   = float(item.price)
            tot  = float(item.get_total_price())
            grand += tot

            c.setFont("Helvetica", 9)
            c.setFillColor(C_BODY)
            c.drawString(COL_QTY + 6, y+5, str(item.quantity))
            c.drawString(COL_DESC, y+5, name[:52])
            c.setFillColor(C_MUTED)
            c.drawRightString(COL_UP, y+5, f"\u20b9{up:,.2f}")
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(C_SLATE)
            c.drawRightString(COL_TOT, y+5, f"\u20b9{tot:,.2f}")

        # Row separator
        y -= 4
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.4)
        c.line(0.45*inch, y, W-0.45*inch, y)

    # ── TOTALS ─────────────────────────────────────────────────
    y -= 18
    if y < 2.2 * inch:
        c.showPage(); y = H - 0.6 * inch
        draw_logo_watermark(W/2, H/2)

    BOX_TW = 2.7 * inch
    BOX_TX = W - 0.45 * inch - BOX_TW
    disc   = grand - float(order.total_amount)

    # Totals card bg
    tot_rows = 3 if disc > 0.01 else 2
    tot_bh   = tot_rows * 18 + 30
    c.setFillColor(colors.HexColor('#f0f9ff'))
    c.roundRect(BOX_TX, y - tot_bh + 10, BOX_TW, tot_bh, 8, fill=1, stroke=0)
    c.setFillColor(C_CYAN)
    c.roundRect(BOX_TX, y - tot_bh + 10, 3.5, tot_bh, 4, fill=1, stroke=0)

    # Subtotal
    c.setFont("Helvetica", 9)
    c.setFillColor(C_MUTED)
    c.drawString(BOX_TX + 12, y, "Subtotal")
    c.setFillColor(C_BODY)
    c.drawRightString(W - 0.45*inch, y, f"\u20b9{grand:,.2f}")

    if disc > 0.01:
        y -= 18
        c.setFont("Helvetica", 9)
        c.setFillColor(C_MUTED)
        c.drawString(BOX_TX + 12, y, "Discount")
        c.setFillColor(C_GREEN)
        c.drawRightString(W - 0.45*inch, y, f"- \u20b9{disc:,.2f}")

    # Divider
    y -= 10
    c.setStrokeColor(C_CYAN)
    c.setLineWidth(0.8)
    c.line(BOX_TX + 12, y, W - 0.45*inch, y)

    # Grand total
    y -= 16
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(C_SLATE)
    c.drawString(BOX_TX + 12, y, "GRAND TOTAL")
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(C_CYAN)
    c.drawRightString(W - 0.45*inch, y, f"\u20b9{float(order.total_amount):,.2f}")

    # ── FOOTER ─────────────────────────────────────────────────
    FY = 0.85 * inch
    c.setFillColor(C_DARK)
    c.rect(0, 0, W, FY + 0.08*inch, fill=1, stroke=0)
    c.setFillColor(C_CYAN)
    c.rect(0, FY + 0.08*inch, W, 1.5, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(C_CYAN)
    c.drawString(0.45*inch, FY - 2, "TERMS & CONDITIONS")
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor('#94a3b8'))
    c.drawString(0.45*inch, FY - 13, "1. Payment is due within 15 days of order placement.")
    c.drawString(0.45*inch, FY - 23, "2. This is a computer-generated invoice and requires no signature.")

    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(C_WHITE)
    c.drawRightString(W - 0.45*inch, FY - 2, "Thank you for shopping with Local Khoj!")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(C_MUTED)
    c.drawRightString(W - 0.45*inch, FY - 14, "support@localkhoj.com  \u2022  localkhoj.com")

    # Page number
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor('#475569'))
    c.drawCentredString(W / 2, 0.28*inch, "Page 1  \u2022  Generated by Local Khoj")

    c.showPage()
    c.save()
    buf.seek(0)
    resp = HttpResponse(buf.read(), content_type="application/pdf")
    resp['Content-Disposition'] = f'inline; filename="LocalKhoj_Invoice_{order.id:04d}.pdf"'
    return resp


@login_required
def pay_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # ── Brand colours ──────────────────────────────────────────
    CYAN      = colors.HexColor('#00d2ff')
    DARK_BLUE = colors.HexColor('#3a7bd5')
    DARK_BG   = colors.HexColor('#0a0b10')
    SLATE     = colors.HexColor('#334155')
    MUTED     = colors.HexColor('#64748b')
    GREEN     = colors.HexColor('#38ef7d')
    WHITE     = colors.white
    LIGHT_BG  = colors.HexColor('#f0f9ff')
    BORDER    = colors.HexColor('#e2e8f0')

    # ── Helper: draw the "Local खोज" logo in text ──────────────
    def draw_logo(p, x, y, size=22):
        """Draw the stylised Local Khoj logo at (x,y) with given font size."""
        # "L" in cyan
        p.setFont("Helvetica-Bold", size)
        p.setFillColor(colors.HexColor('#00a8ff'))
        p.drawString(x, y, "L")
        lw = p.stringWidth("L", "Helvetica-Bold", size)

        # Search circle (○) in dark
        p.setFont("Helvetica-Bold", int(size * 0.85))
        p.setFillColor(colors.HexColor('#1e293b'))
        p.drawString(x + lw, y + 1, "○")
        ow = p.stringWidth("○", "Helvetica-Bold", int(size * 0.85))

        # "cal" in blue
        p.setFont("Helvetica-Bold", size)
        p.setFillColor(colors.HexColor('#0097e6'))
        p.drawString(x + lw + ow, y, "c")
        cw = p.stringWidth("c", "Helvetica-Bold", size)
        p.setFillColor(colors.HexColor('#44bd32'))
        p.drawString(x + lw + ow + cw, y, "a")
        aw = p.stringWidth("a", "Helvetica-Bold", size)
        p.setFillColor(colors.HexColor('#4cd137'))
        p.drawString(x + lw + ow + cw + aw, y, "l")

        # "खोज" below in gradient-like blue
        p.setFont("Helvetica-Bold", int(size * 0.65))
        p.setFillColor(colors.HexColor('#00a8ff'))
        p.drawString(x + lw + 4, y - int(size * 0.75), "Khoj")

    # ── WATERMARK (centre of page, very light) ─────────────────
    p.saveState()
    p.setFillColor(colors.HexColor('#00d2ff'))
    p.setFillAlpha(0.04)
    p.setFont("Helvetica-Bold", 90)
    p.translate(w / 2, h / 2)
    p.rotate(35)
    p.drawCentredString(0, 0, "LOCAL KHOJ")
    p.setFont("Helvetica-Bold", 40)
    p.drawCentredString(0, -80, "INVOICE")
    p.restoreState()

    # ── HEADER BAND ────────────────────────────────────────────
    # Dark gradient band at top
    p.setFillColor(DARK_BG)
    p.rect(0, h - 1.6 * inch, w, 1.6 * inch, fill=1, stroke=0)

    # Cyan accent stripe at very top
    p.setFillColor(CYAN)
    p.rect(0, h - 4, w, 4, fill=1, stroke=0)

    # Logo in header (white version)
    p.saveState()
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor('#00a8ff'))
    p.drawString(0.5 * inch, h - 0.85 * inch, "L")
    lw = p.stringWidth("L", "Helvetica-Bold", 24)
    p.setFillColor(WHITE)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(0.5 * inch + lw, h - 0.83 * inch, "○")
    ow = p.stringWidth("○", "Helvetica-Bold", 20)
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor('#0097e6'))
    p.drawString(0.5 * inch + lw + ow, h - 0.85 * inch, "c")
    cw = p.stringWidth("c", "Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor('#44bd32'))
    p.drawString(0.5 * inch + lw + ow + cw, h - 0.85 * inch, "a")
    aw = p.stringWidth("a", "Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor('#4cd137'))
    p.drawString(0.5 * inch + lw + ow + cw + aw, h - 0.85 * inch, "l")
    # Khoj subtitle
    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(colors.HexColor('#00a8ff'))
    p.drawString(0.5 * inch + lw + 4, h - 1.1 * inch, "Khoj")
    p.restoreState()

    # Tagline under logo
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawString(0.5 * inch, h - 1.35 * inch, "Find Everything Near You")

    # INVOICE title (right side)
    p.setFont("Helvetica-Bold", 36)
    p.setFillColor(CYAN)
    p.drawRightString(w - 0.5 * inch, h - 0.85 * inch, "INVOICE")

    # Order meta (right side)
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(WHITE)
    p.drawRightString(w - 0.5 * inch, h - 1.1 * inch, f"Order #{order.id:04d}")
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.HexColor('#94a3b8'))
    p.drawRightString(w - 0.5 * inch, h - 1.28 * inch, f"Date: {order.created_at.strftime('%d %b, %Y')}")

    # Status badge
    status_color = GREEN if order.status in ('delivered', 'completed') else colors.HexColor('#ffd200')
    p.setFillColor(status_color)
    p.setFont("Helvetica-Bold", 8)
    status_text = order.get_status_display().upper()
    sw = p.stringWidth(status_text, "Helvetica-Bold", 8)
    badge_x = w - 0.5 * inch - sw - 12
    p.roundRect(badge_x - 6, h - 1.52 * inch, sw + 12, 14, 4, fill=1, stroke=0)
    p.setFillColor(DARK_BG)
    p.drawString(badge_x, h - 1.44 * inch, status_text)

    # ── BILL TO / SHIP TO ──────────────────────────────────────
    y_info = h - 2.1 * inch

    # Section backgrounds
    p.setFillColor(LIGHT_BG)
    p.roundRect(0.4 * inch, y_info - 0.85 * inch, 2.8 * inch, 1.05 * inch, 6, fill=1, stroke=0)
    p.roundRect(3.4 * inch, y_info - 0.85 * inch, 3.2 * inch, 1.05 * inch, 6, fill=1, stroke=0)

    # Left accent bars
    p.setFillColor(CYAN)
    p.rect(0.4 * inch, y_info - 0.85 * inch, 3, 1.05 * inch, fill=1, stroke=0)
    p.setFillColor(DARK_BLUE)
    p.rect(3.4 * inch, y_info - 0.85 * inch, 3, 1.05 * inch, fill=1, stroke=0)

    # BILL TO
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(CYAN)
    p.drawString(0.6 * inch, y_info, "BILL TO")
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(SLATE)
    p.drawString(0.6 * inch, y_info - 16, order.user.get_full_name() or order.user.username)
    p.setFont("Helvetica", 9)
    p.setFillColor(MUTED)
    p.drawString(0.6 * inch, y_info - 30, order.user.email or "—")

    # SHIP TO
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(DARK_BLUE)
    p.drawString(3.6 * inch, y_info, "SHIP TO")
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(SLATE)
    p.drawString(3.6 * inch, y_info - 16, order.delivery_name or order.user.username)
    p.setFont("Helvetica", 9)
    p.setFillColor(MUTED)
    p.drawString(3.6 * inch, y_info - 30, order.delivery_phone or "—")
    # Wrap address
    addr = order.delivery_address or "—"
    if len(addr) > 45:
        p.drawString(3.6 * inch, y_info - 44, addr[:45])
        p.drawString(3.6 * inch, y_info - 57, addr[45:90])
    else:
        p.drawString(3.6 * inch, y_info - 44, addr)

    # ── TABLE HEADER ───────────────────────────────────────────
    y = y_info - 1.1 * inch

    # Header background
    p.setFillColor(DARK_BG)
    p.rect(0.4 * inch, y - 6, w - 0.8 * inch, 22, fill=1, stroke=0)

    # Cyan left accent on header
    p.setFillColor(CYAN)
    p.rect(0.4 * inch, y - 6, 4, 22, fill=1, stroke=0)

    p.setFont("Helvetica-Bold", 9)
    p.setFillColor(WHITE)
    p.drawString(0.65 * inch, y + 4, "QTY")
    p.drawString(1.3 * inch, y + 4, "DESCRIPTION")
    p.drawRightString(w - 1.8 * inch, y + 4, "UNIT PRICE")
    p.drawRightString(w - 0.5 * inch, y + 4, "TOTAL")

    y -= 6  # move below header

    # ── TABLE ROWS ─────────────────────────────────────────────
    items_by_store = {}
    for item in order.items.all():
        store = None
        if item.product and item.product.store:
            store = item.product.store
        elif item.service and item.service.store:
            store = item.service.store
        sid = store.id if store else 0
        if sid not in items_by_store:
            items_by_store[sid] = {'store': store, 'items': []}
        items_by_store[sid]['items'].append(item)

    total_items_amount = 0
    row_alt = False

    for sid, data in items_by_store.items():
        store = data['store']
        items = data['items']

        y -= 22
        if y < 1.8 * inch:
            p.showPage()
            y = h - 0.8 * inch

        # Store sub-header
        p.setFillColor(colors.HexColor('#f0f9ff'))
        p.rect(0.4 * inch, y - 4, w - 0.8 * inch, 18, fill=1, stroke=0)
        p.setFillColor(CYAN)
        p.rect(0.4 * inch, y - 4, 3, 18, fill=1, stroke=0)
        p.setFont("Helvetica-Bold", 9)
        p.setFillColor(DARK_BLUE)
        store_name = store.name if store else "Local Khoj"
        p.drawString(0.65 * inch, y + 2, f"Store: {store_name}")
        if store and store.phone:
            p.setFont("Helvetica", 8)
            p.setFillColor(MUTED)
            p.drawRightString(w - 0.5 * inch, y + 2, store.phone)

        for item in items:
            y -= 22
            if y < 1.8 * inch:
                p.showPage()
                y = h - 0.8 * inch

            # Alternating row background
            if row_alt:
                p.setFillColor(colors.HexColor('#f8fafc'))
                p.rect(0.4 * inch, y - 5, w - 0.8 * inch, 20, fill=1, stroke=0)
            row_alt = not row_alt

            name = item.product.name if item.product else item.service.name
            unit_price = float(item.price)
            line_total = float(item.get_total_price())
            total_items_amount += line_total

            p.setFont("Helvetica", 9)
            p.setFillColor(SLATE)
            p.drawString(0.65 * inch, y + 2, str(item.quantity))
            p.drawString(1.3 * inch, y + 2, name[:55])
            p.setFont("Helvetica", 9)
            p.drawRightString(w - 1.8 * inch, y + 2, f"Rs. {unit_price:,.2f}")
            p.setFont("Helvetica-Bold", 9)
            p.setFillColor(DARK_BLUE)
            p.drawRightString(w - 0.5 * inch, y + 2, f"Rs. {line_total:,.2f}")

        # Thin separator after store group
        y -= 8
        p.setStrokeColor(BORDER)
        p.setLineWidth(0.5)
        p.line(0.4 * inch, y, w - 0.4 * inch, y)

    # ── TOTALS BOX ─────────────────────────────────────────────
    y -= 20
    if y < 2.2 * inch:
        p.showPage()
        y = h - 0.8 * inch

    # Totals background
    box_h = 80
    p.setFillColor(colors.HexColor('#f0f9ff'))
    p.roundRect(w - 3.2 * inch, y - box_h + 10, 2.8 * inch, box_h, 8, fill=1, stroke=0)
    p.setFillColor(CYAN)
    p.roundRect(w - 3.2 * inch, y - box_h + 10, 3, box_h, 8, fill=1, stroke=0)

    # Subtotal
    p.setFont("Helvetica", 9)
    p.setFillColor(MUTED)
    p.drawString(w - 3.0 * inch, y, "Subtotal")
    p.setFont("Helvetica", 9)
    p.setFillColor(SLATE)
    p.drawRightString(w - 0.5 * inch, y, f"Rs. {total_items_amount:,.2f}")

    # Discount (if any)
    discount = float(total_items_amount) - float(order.total_amount)
    if discount > 0.01:
        y -= 16
        p.setFont("Helvetica", 9)
        p.setFillColor(MUTED)
        p.drawString(w - 3.0 * inch, y, "Discount")
        p.setFillColor(GREEN)
        p.drawRightString(w - 0.5 * inch, y, f"- Rs. {discount:,.2f}")

    # Divider
    y -= 10
    p.setStrokeColor(CYAN)
    p.setLineWidth(1)
    p.line(w - 3.0 * inch, y, w - 0.5 * inch, y)

    # Grand Total
    y -= 18
    p.setFont("Helvetica-Bold", 13)
    p.setFillColor(DARK_BLUE)
    p.drawString(w - 3.0 * inch, y, "GRAND TOTAL")
    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(CYAN)
    p.drawRightString(w - 0.5 * inch, y, f"Rs. {float(order.total_amount):,.2f}")

    # ── FOOTER ─────────────────────────────────────────────────
    footer_y = 0.9 * inch

    # Footer band
    p.setFillColor(DARK_BG)
    p.rect(0, 0, w, footer_y + 0.1 * inch, fill=1, stroke=0)
    p.setFillColor(CYAN)
    p.rect(0, footer_y + 0.1 * inch, w, 2, fill=1, stroke=0)

    # Terms
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(CYAN)
    p.drawString(0.5 * inch, footer_y - 2, "TERMS & CONDITIONS")
    p.setFont("Helvetica", 7.5)
    p.setFillColor(colors.HexColor('#94a3b8'))
    p.drawString(0.5 * inch, footer_y - 14, "1. Payment is due within 15 days of order placement.")
    p.drawString(0.5 * inch, footer_y - 25, "2. This is a computer-generated invoice and requires no signature.")

    # Thank you (right)
    p.setFont("Helvetica-Bold", 9)
    p.setFillColor(WHITE)
    p.drawRightString(w - 0.5 * inch, footer_y - 2, "Thank you for shopping with Local Khoj!")
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawRightString(w - 0.5 * inch, footer_y - 15, "support@localkhoj.com  |  localkhoj.com")

    # Page number
    p.setFont("Helvetica", 7)
    p.setFillColor(colors.HexColor('#475569'))
    p.drawCentredString(w / 2, 0.3 * inch, "Page 1")

    # ── WATERMARK LOGO (subtle, centre) ────────────────────────
    # Already drawn at the top — second smaller one near bottom
    p.saveState()
    p.setFillColor(CYAN)
    p.setFillAlpha(0.03)
    p.setFont("Helvetica-Bold", 55)
    p.translate(w / 2, h / 2 - 1.5 * inch)
    p.rotate(35)
    p.drawCentredString(0, 0, "LOCAL KHOJ")
    p.restoreState()

    p.showPage()
    p.save()

    buffer.seek(0)
    resp = HttpResponse(buffer.read(), content_type="application/pdf")
    resp['Content-Disposition'] = f'inline; filename="LocalKhoj_Invoice_{order.id}.pdf"'
    return resp


@login_required
def pay_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    key_id = getattr(settings, "RAZORPAY_KEY_ID", None)
    stripe_pk = getattr(settings, "STRIPE_PUBLISHABLE_KEY", None)
    amount_paise = int(float(order.total_amount) * 100)
    razorpay_order = None
    if razorpay and key_id and getattr(settings, "RAZORPAY_KEY_SECRET", None):
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": str(order.id),
            "payment_capture": 1
        })
    return render(
        request,
        "orders/pay.html",
        {
            "order": order,
            "amount_paise": amount_paise,
            "key_id": key_id,
            "stripe_pk": stripe_pk,
            "razorpay_order_id": (razorpay_order or {}).get("id"),
        }
    )


@login_required
def pay_verify(request):
    if request.method != "POST":
        return redirect("home")
    order_id = request.POST.get("order_id")
    payment_id = request.POST.get("razorpay_payment_id")
    razorpay_order_id = request.POST.get("razorpay_order_id")
    signature = request.POST.get("razorpay_signature")
    order = get_object_or_404(Order, id=order_id, user=request.user)

    secret = getattr(settings, "RAZORPAY_KEY_SECRET", None)
    key_id = getattr(settings, "RAZORPAY_KEY_ID", None)
    status = "failed"
    if razorpay and secret and key_id and payment_id and razorpay_order_id and signature:
        try:
            client = razorpay.Client(auth=(key_id, secret))
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            })
            status = "completed"
        except Exception:
            status = "failed"
    if status == "completed":
        Payment.objects.create(user=request.user, provider="razorpay", amount=order.total_amount, order=order, status="completed")
        Notification.objects.create(user=request.user, title="Payment successful", body=f"Order #{order.id}")
    else:
        Payment.objects.create(user=request.user, provider="razorpay", amount=order.total_amount, order=order, status="failed")
        Notification.objects.create(user=request.user, title="Payment failed", body=f"Order #{order.id}")
    return redirect("order_detail", order_id=order.id)


@login_required
def pay_stripe_create(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    secret = getattr(settings, "STRIPE_SECRET_KEY", None)
    pk = getattr(settings, "STRIPE_PUBLISHABLE_KEY", None)
    if not secret or not pk:
        return redirect("order_detail", order_id=order.id)
    stripe.api_key = secret
    success_url = request.build_absolute_uri(f"/orders/pay/stripe/complete/?order_id={order.id}&session_id={{CHECKOUT_SESSION_ID}}")
    cancel_url = request.build_absolute_uri(f"/orders/order/{order.id}/")
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "inr",
                "product_data": {"name": f"Order #{order.id}"},
                "unit_amount": int(float(order.total_amount) * 100),
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(order.id),
        customer_email=request.user.email or None,
    )
    return render(request, "orders/stripe_redirect.html", {"session_id": session.id, "stripe_pk": pk})


@login_required
def pay_stripe_complete(request):
    secret = getattr(settings, "STRIPE_SECRET_KEY", None)
    stripe.api_key = secret or ""
    session_id = request.GET.get("session_id")
    order_id = request.GET.get("order_id")
    order = get_object_or_404(Order, id=order_id, user=request.user)
    status = "failed"
    try:
        if session_id and secret:
            sess = stripe.checkout.Session.retrieve(session_id)
            if sess.get("payment_status") == "paid":
                status = "completed"
    except Exception:
        status = "failed"
    Payment.objects.create(user=request.user, provider="stripe", amount=order.total_amount, order=order, status=status)
    Notification.objects.create(user=request.user, title=("Payment successful" if status=="completed" else "Payment failed"), body=f"Order #{order.id}")
    return redirect("order_detail", order_id=order.id)


def pay_stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
    event = None
    if not endpoint_secret:
        return HttpResponse(status=400)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception:
        return HttpResponse(status=400)
    if event["type"] == "checkout.session.completed":
        sess = event["data"]["object"]
        order_id = sess.get("client_reference_id")
        user = request.user if request.user.is_authenticated else None
        try:
            order = Order.objects.get(id=int(order_id))
            Payment.objects.create(user=order.user, provider="stripe", amount=order.total_amount, order=order, status="completed")
            Notification.objects.create(user=order.user, title="Payment successful", body=f"Order #{order.id}")
        except Exception:
            pass
    return HttpResponse(status=200)
