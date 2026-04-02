"""
ADVISIO — Generator Audit Complet (returneaza bytes)
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


def resolve_theme(R: dict) -> dict:
    """
    Accepta theme ca:
    - string:  "navy_gold", "dark_copper" etc.
    - dict:    {"bg": "#...", "accent": "#...", ...} — tema custom de la AI
    - lipsa:   fallback navy_gold
    """
    theme = R.get("theme", "navy_gold")
    if isinstance(theme, dict):
        default = THEMES["navy_gold"]
        return {k: theme.get(k, default[k]) for k in default}
    return THEMES.get(theme, THEMES["navy_gold"])


def build_audit(R: dict) -> bytes:
    T = resolve_theme(R)
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

    biz  = R.get("name", R.get("bizName", "Restaurant"))
    city = R.get("subtitle", R.get("city", "Romania"))

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
            c.drawString(15 * mm, H - 9 * mm, "AUDIT AI RESTAURANT")
            c.setFillColor(WHITE)
            c.setFont("Helvetica", 7)
            c.drawRightString(W - 15 * mm, H - 9 * mm, f"{biz} | {city}")
            c.setFillColor(ACC)
            c.rect(0, H - 6 * mm, W, 6 * mm, fill=1, stroke=0)
        c.setFillColor(TEXT_L)
        c.setFont("Helvetica", 7)
        c.drawString(15 * mm, 8 * mm, f"Confidential — Pregatit exclusiv pentru {biz}")
        c.drawCentredString(W / 2, 8 * mm, "Advisio AI Audit | 2026 | Confidential")
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

    def week_blk(lbl, title, days):
        hs = ParagraphStyle('wh', fontName='Helvetica-Bold', fontSize=10,
                            textColor=TEXT_D, leading=14, spaceAfter=0)
        ac = T["accent"]
        rows = [[Paragraph(f'<font color="{ac}">{lbl}</font> {title}', hs)]]
        for d in days:
            rows.append([[
                Paragraph(d['day'],
                          S('wd', fontName='Helvetica-Bold', fontSize=9,
                            textColor=TEXT_D, leading=13, spaceAfter=2)),
                Paragraph(d['action'],
                          S('wa', fontSize=9, textColor=TEXT_D,
                            leading=13, spaceAfter=2)),
                Paragraph(d['note'],
                          S('wn', fontSize=9, textColor=TEXT_M,
                            leading=13, spaceAfter=0)),
            ]])
        t = Table(rows, colWidths=[CW])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ACC_LT),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('LINEABOVE', (0, 0), (-1, 0), 1.5, ACC),
            ('LINEBELOW', (0, -1), (-1, -1), 1.5, ACC),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        return t

    def tcol(l1, v1, l2, v2):
        hw = CW / 2
        t = Table([[[
            Paragraph(l1, S('ls', fontSize=8, textColor=TEXT_M,
                            leading=11, spaceAfter=0)),
            Paragraph(f'<font size="18" color="#C0392B"><b>{v1}</b></font>',
                      S('v', alignment=TA_CENTER, spaceAfter=0)),
        ], [
            Paragraph(l2, S('ls2', fontSize=8, textColor=TEXT_M,
                            leading=11, spaceAfter=0)),
            Paragraph(f'<font size="18" color="#1A6B3A"><b>{v2}</b></font>',
                      S('v2', alignment=TA_CENTER, spaceAfter=0)),
        ]]], colWidths=[hw, hw])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#FDECEA")),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#EAF5EE")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return t

    def s5item(title, desc):
        ac = T["accent"]
        t = Table([[
            Paragraph(f'<font color="{ac}"><b>\u2192</b></font>',
                      S('arr', fontSize=10, spaceAfter=0)),
            [Paragraph(title,
                       S('s5t', fontName='Helvetica-Bold', fontSize=10,
                         textColor=TEXT_D, leading=14, spaceAfter=2)),
             Paragraph(desc,
                       S('s5b', fontSize=9.5, textColor=TEXT_M,
                         leading=14, spaceAfter=0))],
        ]], colWidths=[8 * mm, CW - 8 * mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor("#EEEEEE")),
        ]))
        return t

    def urgbox(lines, price):
        ps = [Paragraph(l, S('ub', fontSize=9.5,
                             textColor=colors.HexColor("#DDDDDD"),
                             leading=14, spaceAfter=6))
              for l in lines]
        ac = T["accent"]
        ps += [
            sp(8),
            Paragraph(price,
                      S('up', fontName='Helvetica-Bold', fontSize=14,
                        textColor=ACC, leading=18, spaceAfter=0,
                        alignment=TA_CENTER)),
        ]
        t = Table([[ps]], colWidths=[CW])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG),
            ('BOX', (0, 0), (-1, -1), 2, ACC),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ]))
        return t

    def ba_table(pairs):
        cw2 = [CW / 2, CW / 2]
        hs2 = ParagraphStyle('mh2', fontName='Helvetica-Bold',
                             fontSize=9, leading=13)
        cs2 = ParagraphStyle('mc2', fontName='Helvetica-Oblique',
                             fontSize=9, textColor=colors.HexColor("#333333"),
                             leading=13)
        rows = [[
            Paragraph('<font color="#C0392B">\u2717 Versiunea actuala</font>', hs2),
            Paragraph('<font color="#1A6B3A">\u2713 Versiunea cu storytelling (generata)</font>', hs2),
        ]]
        for before, after in pairs:
            rows.append([Paragraph(before, cs2), Paragraph(after, cs2)])
        t = Table(rows, colWidths=cw2)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#FDECEA")),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#EAF5EE")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
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
        s.append(Paragraph("Raport de Audit AI",
                            S('rt', fontName='Helvetica-Bold', fontSize=14,
                              textColor=WHITE, leading=18, spaceAfter=4)))
        s.append(Paragraph(
            "Diagnosticul prezentei digitale | Plan de actiune 30 de zile",
            S('cm2', fontSize=11, textColor=colors.HexColor("#AAAAAA"),
              leading=16, spaceAfter=30),
        ))
        s.append(sp(30))

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
        s.append(sp(200))

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

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=20 * mm, bottomMargin=16 * mm,
        title=f"Audit AI — {biz}",
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

    # S2
    s += sec_hdr("2", "Cele Mai Mari 5 Pierderi de Timp", R.get("s2_subtitle", ""))
    for i, loss in enumerate(R.get("losses", [])):
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
            s.append(Paragraph("Iata un exemplu generat gata de folosit:", bold_s))
            s.append(sp(4))
            s.append(ibox(*loss["example_box"]))
        if loss.get("before_after"):
            s.append(Paragraph("Iata diferenta concreta:", bold_s))
            s.append(sp(4))
            s.append(ba_table(loss["before_after"]))
        if loss.get("cta_text"):
            s.append(sp(6))
            s.append(Paragraph(loss["cta_text"], body))
        if i < len(R.get("losses", [])) - 1:
            s.append(sp(14))
        if i in (1, 3):
            s.append(PageBreak())

    s.append(sp(10))
    s.append(tcol(
        "Timp total pierdut / saptamana (actual)", R.get("total_manual", "—"),
        "Timp total cu AI / saptamana", R.get("total_ai", "—"),
    ))
    s.append(PageBreak())

    # S3
    s += sec_hdr("3", "Instrumentele AI Recomandate", R.get("s3_subtitle", ""))
    s.append(Paragraph(
        "Cele 3 instrumente de mai jos acopera toate sarcinile identificate. "
        "Nicio cunostinta tehnica necesara.",
        body,
    ))
    s.append(sp(10))
    il = S('inl', fontName='Helvetica-Bold', fontSize=11, textColor=WHITE,
           leading=14, alignment=TA_CENTER, spaceAfter=2)
    iu = S('inu', fontSize=8, textColor=ACC, leading=11, alignment=TA_CENTER)
    iv = S('iv', fontSize=9, textColor=TEXT_M, leading=13,
           spaceAfter=4, alignment=TA_LEFT)
    for nm, url_t, cost, desc, use in R.get("tools", []):
        row = [[[
            Paragraph(nm, il),
            Paragraph(url_t, iu),
        ], [
            Paragraph(f"<b>Cost:</b> {cost}", iv),
            Paragraph(f"<b>Ce face:</b> {desc}", iv),
            Paragraph(f"<b>Folosit pentru:</b> {use}",
                      S('iv2', fontSize=9, textColor=TEXT_M,
                        leading=13, spaceAfter=0)),
        ]]]
        t = Table(row, colWidths=[30 * mm, CW - 30 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), BG),
            ('BACKGROUND', (1, 0), (1, -1), ROW_ALT),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        s.append(t)
        s.append(sp(6))
    s.append(PageBreak())

    # S4
    s += sec_hdr("4", "Castigurile Tale Rapide in 30 de Zile", R.get("s4_subtitle", ""))
    s.append(Paragraph(R.get("s4_intro", ""), body))
    s.append(sp(10))
    for lbl2, title2, days2 in R.get("weeks", []):
        s.append(week_blk(lbl2, title2, days2))
        s.append(sp(8))
    s.append(PageBreak())

    # S5
    s += sec_hdr("5", "Pachetul Complet — Gata de Folosit in 48 de Ore", R.get("s5_subtitle", ""))
    s.append(Paragraph(R.get("s5_intro", ""), body))
    s.append(sp(10))
    for title2, desc2 in R.get("deliverables", []):
        s.append(s5item(title2, desc2))
    s.append(sp(14))
    s.append(urgbox(
        R.get("urgency_lines", []),
        f"Investitie: {R.get('price', '97 USD')} — o singura plata",
    ))
    s.append(sp(12))

    bl1 = ParagraphStyle('bl1', fontName='Helvetica-Bold', fontSize=14,
                         textColor=WHITE, leading=18, spaceAfter=0,
                         alignment=TA_CENTER)
    bl2 = ParagraphStyle('bl2', fontSize=9,
                         textColor=colors.HexColor("#FFF8DC"),
                         leading=13, spaceAfter=0, alignment=TA_CENTER)
    bd = Table([[[
        Paragraph(f"COMANDA PACHETUL — {R.get('price', '97 USD')}", bl1),
        sp(3),
        Paragraph("Click aici \u2192 plata cu cardul \u2192 primesti documentele in 48 de ore", bl2),
    ]]], colWidths=[CW])
    bd.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BTN_BG),
        ('BOX', (0, 0), (-1, -1), 2, BTN_BRD),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    stripe_url = R.get("stripe_url", "#")
    s.append(Btn(bd, stripe_url, CW))
    s.append(sp(10))
    s.append(Paragraph(R.get("s5_closing", ""), body))

    doc.build(s, onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()
