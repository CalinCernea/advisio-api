"""
ADVISIO — Generator Teaser PDF (returneaza bytes)
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus.flowables import Flowable
import io

THEMES = {
    "navy_gold": {
        "bg":        "#0D1B2A",
        "accent":    "#C9A84C",
        "accent_lt": "#F7F0E0",
        "row_hdr":   "#1A2E45",
        "urgent":    "#C0392B",
        "btn_bg":    "#C9A84C",
        "btn_brd":   "#A8873A",
    },
    "dark_copper": {
        "bg":        "#1A0F0A",
        "accent":    "#C17F3E",
        "accent_lt": "#F5E6D0",
        "row_hdr":   "#3D2A1A",
        "urgent":    "#C0392B",
        "btn_bg":    "#C17F3E",
        "btn_brd":   "#9E6530",
    },
    "forest_gold": {
        "bg":        "#0F2016",
        "accent":    "#C9A84C",
        "accent_lt": "#F0F5E8",
        "row_hdr":   "#1A3A25",
        "urgent":    "#C0392B",
        "btn_bg":    "#C9A84C",
        "btn_brd":   "#A8873A",
    },
    "burgundy": {
        "bg":        "#2C0F1A",
        "accent":    "#C9A84C",
        "accent_lt": "#FDF0F5",
        "row_hdr":   "#4A1A2E",
        "urgent":    "#C0392B",
        "btn_bg":    "#C9A84C",
        "btn_brd":   "#A8873A",
    },
}


def build_teaser(R: dict) -> bytes:
    T = THEMES.get(R.get("theme", "navy_gold"), THEMES["navy_gold"])
    BG      = colors.HexColor(T["bg"])
    ACC     = colors.HexColor(T["accent"])
    ACC_LT  = colors.HexColor(T["accent_lt"])
    ROW_HDR = colors.HexColor(T["row_hdr"])
    URG_CLR = colors.HexColor(T["urgent"])
    BTN_BG  = colors.HexColor(T["btn_bg"])
    BTN_BRD = colors.HexColor(T["btn_brd"])
    ROW_ALT = colors.HexColor("#F4F2EE")
    TEXT_D  = colors.HexColor("#1A1A1A")
    TEXT_M  = colors.HexColor("#555555")
    TEXT_L  = colors.HexColor("#888888")
    WHITE   = colors.white
    GREEN   = colors.HexColor("#1A6B3A")
    GOLD_BOX = colors.HexColor("#FFFBF0")
    GOLD_BRD = colors.HexColor("#C9A84C")

    W, H = A4
    MARGIN = 15 * mm
    CW = W - 2 * MARGIN

    biz  = R.get("name", R.get("bizName", "Restaurant"))
    city = R.get("subtitle", R.get("city", "Romania"))

    def sp(h=8):
        return Spacer(1, h)

    def hr():
        return HRFlowable(width="100%", thickness=1, color=ACC,
                          spaceAfter=6, spaceBefore=6)

    def S(n, **k):
        d = dict(fontName='Helvetica', fontSize=10, textColor=TEXT_D,
                 leading=15, spaceAfter=4)
        d.update(k)
        return ParagraphStyle(n, **d)

    body   = S('body')
    bold_s = S('bold', fontName='Helvetica-Bold')

    def hf(c, doc):
        pg = doc.page
        c.saveState()
        if pg == 1:
            c.setFillColor(BG)
            c.rect(0, 0, W, H, fill=1, stroke=0)
            c.setFillColor(ACC)
            c.rect(0, H - 6 * mm, W, 6 * mm, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#0A1015"))
            c.rect(0, 0, W, 22 * mm, fill=1, stroke=0)
        else:
            c.setFillColor(BG)
            c.rect(0, H - 14 * mm, W, 14 * mm, fill=1, stroke=0)
            c.setFillColor(ACC)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(15 * mm, H - 9 * mm, "AUDIT AI RESTAURANT — PREVIEW GRATUIT")
            c.setFillColor(WHITE)
            c.setFont("Helvetica", 7)
            c.drawRightString(W - 15 * mm, H - 9 * mm, f"{biz} | {city}")
            c.setFillColor(ACC)
            c.rect(0, H - 6 * mm, W, 6 * mm, fill=1, stroke=0)
        c.setFillColor(TEXT_L)
        c.setFont("Helvetica", 7)
        c.drawString(15 * mm, 8 * mm, f"Preview gratuit — Pregatit exclusiv pentru {biz}")
        c.drawCentredString(W / 2, 8 * mm, "Advisio AI Audit | 2026")
        c.drawRightString(W - 15 * mm, 8 * mm, f"Pagina {pg - 1}")
        c.restoreState()

    def sec_hdr(num, title, sub):
        return [
            Paragraph(f"SECTIUNEA {num}",
                      S('sl', fontName='Helvetica-Bold', fontSize=8,
                        textColor=ACC, leading=12, spaceAfter=2)),
            Paragraph(title,
                      S('st', fontName='Helvetica-Bold', fontSize=26,
                        textColor=TEXT_D, leading=32, spaceAfter=6)),
            hr(),
            Paragraph(sub,
                      S('ss', fontSize=10, textColor=TEXT_M,
                        leading=14, spaceAfter=10, alignment=TA_LEFT)),
            sp(6),
        ]

    def tt(m, a, sv):
        lbl = S('l', fontSize=8, textColor=TEXT_M, leading=11,
                alignment=TA_CENTER, spaceAfter=0)
        ac = T["accent"]
        d = [
            [Paragraph("Timp manual / sapt.", lbl),
             Paragraph("Cu AI", lbl),
             Paragraph("Economie / sapt.", lbl)],
            [Paragraph(f'<font size="20" color="{ac}"><b>{m}</b></font>',
                       S('v', alignment=TA_CENTER, spaceAfter=0)),
             Paragraph(f'<font size="20" color="{ac}"><b>{a}</b></font>',
                       S('v', alignment=TA_CENTER, spaceAfter=0)),
             Paragraph(f'<font size="20"><b>{sv}</b></font>',
                       S('v', alignment=TA_CENTER, spaceAfter=0))],
        ]
        t = Table(d, colWidths=[CW / 3] * 3)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ROW_ALT),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ]))
        return t

    def lh(num, title):
        t = Table([[
            Paragraph(num,
                      S('bn', fontName='Helvetica-Bold', fontSize=28,
                        textColor=ACC, leading=30, spaceAfter=0)),
            Paragraph(title,
                      S('bt', fontName='Helvetica-Bold', fontSize=13,
                        textColor=TEXT_D, leading=16, spaceAfter=0)),
        ]], colWidths=[18 * mm, CW - 18 * mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ]))
        return t

    def rbox(text, bg=None, brd=None):
        if bg is None:
            bg = colors.HexColor("#FFF0F0")
        if brd is None:
            brd = URG_CLR
        t = Table([[Paragraph(
            text,
            S('rq', fontName='Helvetica-Oblique', fontSize=9.5,
              textColor=colors.HexColor("#444444"), leading=14,
              spaceAfter=0, alignment=TA_LEFT),
        )]], colWidths=[CW])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg),
            ('LINEBEFORE', (0, 0), (0, -1), 4, brd),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        return t

    def ibox(lbl, txt, bg=None, brd=None):
        if bg is None:
            bg = ACC_LT
        if brd is None:
            brd = ACC
        t = Table([[[
            Paragraph(lbl,
                      S('il', fontName='Helvetica-Bold', fontSize=9,
                        textColor=TEXT_D, leading=13, spaceAfter=2)),
            Paragraph(txt,
                      S('iv', fontSize=9, textColor=TEXT_M,
                        leading=13, spaceAfter=0, alignment=TA_LEFT)),
        ]]], colWidths=[CW])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg),
            ('LINEBEFORE', (0, 0), (0, -1), 3, brd),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        return t

    def attn(b, n):
        t = Table([[Paragraph(
            f'<b>{b}</b> {n}',
            S('ab', fontSize=9, textColor=colors.HexColor("#5A4000"),
              leading=14, spaceAfter=0),
        )]], colWidths=[CW])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), GOLD_BOX),
            ('LINEBEFORE', (0, 0), (0, -1), 4, GOLD_BRD),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, GOLD_BRD),
        ]))
        return t

    def metrics_tbl(rows):
        hdr = ['Indicator', 'Situatia actuala', 'Target 90 zile', 'Urgenta']
        uc  = {
            'CRITICA':  URG_CLR,
            'RIDICATA': colors.HexColor("#E67E22"),
            'MEDIE':    GREEN,
        }
        cw2 = [CW * p for p in [0.26, 0.30, 0.25, 0.19]]
        hs = ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9,
                            textColor=WHITE, leading=13)
        cs = ParagraphStyle('tc', fontSize=9, textColor=TEXT_D, leading=13)
        td = [[Paragraph(h, hs) for h in hdr]]
        for r in rows:
            clr   = uc.get(r[3], TEXT_D)
            hex_c = clr.hexval()[2:]
            td.append([
                Paragraph(r[0], cs),
                Paragraph(r[1], cs),
                Paragraph(r[2], cs),
                Paragraph(f'<font color="#{hex_c}"><b>{r[3]}</b></font>', cs),
            ])
        t = Table(td, colWidths=cw2)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ROW_HDR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        return t

    class Btn(Flowable):
        def __init__(self, tbl, url, w):
            Flowable.__init__(self)
            self.tbl = tbl; self.url = url; self.w = w; self._h = 52

        def wrap(self, aw, ah):
            self.tbl.wrapOn(self.canv, aw, ah)
            _w, h = self.tbl.wrap(aw, ah)
            self._h = h
            return aw, h

        def draw(self):
            self.tbl.drawOn(self.canv, 0, 0)
            self.canv.linkURL(self.url, (0, 0, self.w, self._h),
                              relative=1, thickness=0)

    def cover():
        s = []
        s.append(sp(70))
        s.append(Paragraph(biz,
                            S('ct', fontName='Helvetica-Bold', fontSize=42,
                              textColor=WHITE, leading=48, spaceAfter=4)))
        s.append(Paragraph(city,
                            S('cs', fontName='Helvetica-Bold', fontSize=20,
                              textColor=ACC, leading=26, spaceAfter=4)))
        s.append(sp(4))
        addr = R.get("address", city)
        s.append(Paragraph(addr,
                            S('cm', fontSize=11,
                              textColor=colors.HexColor("#AAAAAA"),
                              leading=15, spaceAfter=8)))
        s.append(HRFlowable(width="100%", thickness=1, color=ACC,
                             spaceAfter=10, spaceBefore=6))
        badge = Table([[Paragraph(
            "PREVIEW GRATUIT",
            S('badge', fontName='Helvetica-Bold', fontSize=9,
              textColor=colors.HexColor("#0D1B2A"), leading=11,
              spaceAfter=0, alignment=TA_CENTER),
        )]], colWidths=[42 * mm])
        badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), ACC),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        s.append(badge)
        s.append(sp(10))
        s.append(Paragraph("Raport de Audit AI",
                            S('rt', fontName='Helvetica-Bold', fontSize=13,
                              textColor=WHITE, leading=18, spaceAfter=10)))
        hook = R.get("emotional_hook",
                     f"{biz} merita o prezenta digitala la fel de buna ca experienta din restaurant.")
        hook_tbl = Table([[Paragraph(
            f'<i>{hook}</i>',
            S('hook', fontName='Helvetica-Oblique', fontSize=12,
              textColor=ACC, leading=18, spaceAfter=0, alignment=TA_LEFT),
        )]], colWidths=[CW])
        hook_tbl.setStyle(TableStyle([
            ('LINEBEFORE', (0, 0), (0, -1), 3, ACC),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0A1015")),
        ]))
        s.append(hook_tbl)
        s.append(sp(24))

        sb  = ParagraphStyle('sb', fontName='Helvetica-Bold', fontSize=26,
                             textColor=ACC, leading=30, spaceAfter=0,
                             alignment=TA_CENTER)
        sl2 = ParagraphStyle('sl2', fontSize=8,
                             textColor=colors.HexColor("#BBBBBB"),
                             leading=11, spaceAfter=0, alignment=TA_CENTER)

        def lighten(hex_c, amt=20):
            h = hex_c.lstrip('#')
            return '#' + ''.join(
                '%02x' % min(255, int(h[i:i+2], 16) + amt)
                for i in (0, 2, 4)
            )

        card_dark = colors.HexColor(lighten(T["bg"], 20))
        stats = R.get("stats", [
            ("—", "Rating TripAdvisor"),
            ("—", "Pozitie locala"),
            ("—", "Followeri Instagram"),
            ("—", "Facebook fans"),
        ])
        r1 = [Paragraph(v, sb) for v, _ in stats]
        r2 = [Paragraph(l, sl2) for _, l in stats]
        cw = CW / len(stats)
        t = Table([r1, r2], colWidths=[cw] * len(stats))
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), card_dark),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(lighten(T["bg"], 35))),
            ('TOPPADDING', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('TOPPADDING', (0, 1), (-1, 1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        s.append(t)
        s.append(sp(165))

        cfl = ParagraphStyle('cfl', fontName='Helvetica-Bold', fontSize=8,
                             textColor=WHITE, leading=12, spaceAfter=2)
        cfv = ParagraphStyle('cfv', fontSize=8,
                             textColor=colors.HexColor("#CCCCCC"),
                             leading=12, spaceAfter=2)
        fd = [
            [Paragraph("PREGATIT PENTRU", cfl),
             Paragraph(f"{biz} | {city}", cfv)],
            [Paragraph("PREGATIT DE", cfl),
             Paragraph("Advisio AI Audit | 2026", cfv)],
        ]
        ft = Table(fd, colWidths=[40 * mm, CW - 40 * mm])
        ft.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        s.append(ft)
        s.append(PageBreak())
        return s

    def cta_page():
        s = []
        s.append(sp(20))
        s.append(Paragraph(
            "Acesta este doar preview-ul.",
            S('ctat', fontName='Helvetica-Bold', fontSize=22,
              textColor=TEXT_D, leading=28, spaceAfter=8, alignment=TA_LEFT),
        ))
        s.append(Paragraph(
            "Auditul complet contine inca 7 pagini:",
            S('ctasub', fontSize=13, textColor=TEXT_M,
              leading=18, spaceAfter=12, alignment=TA_LEFT),
        ))
        s.append(sp(6))
        items = [
            ("\u2746", "3 pierderi de timp suplimentare",
             "cu exemple generate specifice pentru restaurantul tau"),
            ("\u2746", "Instrumentele AI recomandate",
             "gratuite sau aproape gratuite — fara cunostinte tehnice"),
            ("\u2746", "Planul de actiune 30 de zile",
             "saptamana cu saptamana, actiune cu actiune"),
            ("\u2746", "Diagnosticul complet al prezentei digitale",
             "cu toate datele si prioritatile"),
        ]
        ac = T["accent"]
        for icon, title2, desc2 in items:
            rt = Table([[
                Paragraph(f'<font color="{ac}">{icon}</font>',
                          S('ic', fontSize=14, textColor=ACC,
                            leading=18, spaceAfter=0, alignment=TA_CENTER)),
                [Paragraph(title2,
                           S('it', fontName='Helvetica-Bold', fontSize=10,
                             textColor=TEXT_D, leading=14, spaceAfter=2)),
                 Paragraph(desc2,
                           S('id', fontSize=9, textColor=TEXT_M,
                             leading=13, spaceAfter=0, alignment=TA_LEFT))],
            ]], colWidths=[10 * mm, CW - 10 * mm])
            rt.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor("#EEEEEE")),
            ]))
            s.append(rt)

        s.append(sp(20))
        payment_url = R.get("stripe_url", R.get("payment_url", "#"))
        urg_content = [
            Paragraph(
                f"Auditul complet pentru {biz} este gata de livrat.",
                S('u1', fontSize=9.5, textColor=colors.HexColor("#DDDDDD"),
                  leading=14, spaceAfter=6),
            ),
            Paragraph(
                "Fiecare zi fara o prezenta digitala optimizata inseamna "
                "clienti pierduti in favoarea competitiei.",
                S('u2', fontSize=9.5, textColor=colors.HexColor("#DDDDDD"),
                  leading=14, spaceAfter=6),
            ),
            Paragraph(
                "Auditul complet iti arata exact cum sa rezolvi asta.",
                S('u3', fontName='Helvetica-Bold', fontSize=10,
                  textColor=ACC, leading=14, spaceAfter=0),
            ),
        ]
        urg_tbl = Table([[urg_content]], colWidths=[CW])
        urg_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG),
            ('BOX', (0, 0), (-1, -1), 2, ACC),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ]))
        s.append(urg_tbl)
        s.append(sp(16))

        bl1 = ParagraphStyle('bl1', fontName='Helvetica-Bold', fontSize=15,
                             textColor=BG, leading=20, spaceAfter=0,
                             alignment=TA_CENTER)
        bl2 = ParagraphStyle('bl2', fontSize=9,
                             textColor=colors.HexColor("#1A1A1A"),
                             leading=13, spaceAfter=0, alignment=TA_CENTER)
        bd = Table([[[
            Paragraph("VREAU AUDITUL COMPLET — 97 USD", bl1),
            sp(3),
            Paragraph(
                "Click aici \u2192 plata cu cardul \u2192 primesti auditul complet imediat dupa plata",
                bl2,
            ),
        ]]], colWidths=[CW])
        bd.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BTN_BG),
            ('BOX', (0, 0), (-1, -1), 2, BTN_BRD),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ]))
        s.append(Btn(bd, payment_url, CW))
        s.append(sp(10))
        s.append(Paragraph(
            "O singura plata de 97 USD. Fara abonament. Primesti auditul complet imediat dupa plata.",
            S('note', fontSize=8.5, textColor=TEXT_L,
              leading=13, spaceAfter=0, alignment=TA_CENTER),
        ))
        return s

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=20 * mm, bottomMargin=16 * mm,
        title=f"Audit AI Preview — {biz}",
    )
    s = []
    s += cover()

    # S1
    s += sec_hdr("1", "Prezentarea Restaurantului", R.get("s1_subtitle", ""))
    for para in R.get("s1_body", []):
        s.append(Paragraph(para, body))
    s.append(sp(10))
    s.append(metrics_tbl(R.get("s1_metrics", [])))
    s.append(sp(10))
    if R.get("s1_attn"):
        s.append(attn(*R["s1_attn"]))
    s.append(PageBreak())

    # S2 — primele 2 pierderi
    s += sec_hdr("2", "Cele Mai Mari 5 Pierderi de Timp", R.get("s2_subtitle", ""))
    s.append(Paragraph(
        "<b>Previzualizare:</b> mai jos gasesti primele 2 din cele 5 pierderi de timp "
        "identificate. Auditul complet contine toate 5 — cu exemple generate si solutiile concrete.",
        S('pn', fontSize=9.5, textColor=colors.HexColor("#555555"),
          leading=14, spaceAfter=10, alignment=TA_LEFT,
          fontName='Helvetica-Oblique'),
    ))
    losses = R.get("losses", [])
    preview_losses = losses[:2] if len(losses) >= 2 else losses
    for i, loss in enumerate(preview_losses):
        s.append(lh(loss["num"], loss["title"]))
        s.append(sp(6))
        s.append(Paragraph(loss["body"], body))
        s.append(sp(6))
        s.append(tt(loss["manual"], loss["ai"], loss["saving"]))
        s.append(sp(8))
        if loss.get("review_bad"):
            s.append(Paragraph("Iata recenzia reala si raspunsul actual vs. varianta profesionala:", bold_s))
            s.append(rbox(loss["review_bad"]))
        if loss.get("review_manager"):
            s.append(sp(4))
            s.append(Paragraph("Raspuns actual (extras):", bold_s))
            s.append(rbox(loss["review_manager"],
                          bg=colors.HexColor("#FFF8F0"),
                          brd=colors.HexColor("#E67E22")))
        if loss.get("review_good"):
            s.append(sp(4))
            s.append(Paragraph("Raspuns generat de AI — gata de publicat:", bold_s))
            s.append(rbox(loss["review_good"],
                          bg=colors.HexColor("#EAF5EE"), brd=GREEN))
        if loss.get("example_box"):
            s.append(Paragraph("Iata o postare gata de publicat:", bold_s))
            s.append(sp(4))
            s.append(ibox(*loss["example_box"]))
        if i < len(preview_losses) - 1:
            s.append(sp(14))

    s.append(sp(16))
    cutoff = Table([[Paragraph(
        "· · · · · · · · · · · · · · CONTINUA IN AUDITUL COMPLET · · · · · · · · · · · · · ·",
        S('cut', fontName='Helvetica-Bold', fontSize=9,
          textColor=ACC, leading=14, spaceAfter=0, alignment=TA_CENTER),
    )]], colWidths=[CW])
    cutoff.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7F0E0")),
        ('BOX', (0, 0), (-1, -1), 1, ACC),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    s.append(cutoff)
    s.append(PageBreak())
    s += cta_page()

    doc.build(s, onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()
