import io
from datetime import datetime
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw total page numbers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages after page 1)
        if self._pageNumber > 1:
            self.drawString(36, self._pagesize[1] - 25, "Real Estate Management System — Report")
            self.drawRightString(self._pagesize[0] - 36, self._pagesize[1] - 25, datetime.now().strftime("%d/%m/%Y %H:%M"))
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(36, self._pagesize[1] - 30, self._pagesize[0] - 36, self._pagesize[1] - 30)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(self._pagesize[0] - 36, 18, footer_text)
        self.drawString(36, 18, f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')} | Confidential")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 28, self._pagesize[0] - 36, 28)
        self.restoreState()


def get_report_styles():
    base_styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=base_styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4,
    )
    
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=base_styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=10,
    )

    kpi_label = ParagraphStyle(
        'KPILabel',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748b'),
        alignment=1, # Center
    )
    
    kpi_value = ParagraphStyle(
        'KPIValue',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
    )
    
    th_style = ParagraphStyle(
        'TH',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    td_style = ParagraphStyle(
        'TD',
        parent=base_styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b'),
    )

    td_bold = ParagraphStyle(
        'TDBold',
        parent=td_style,
        fontName='Helvetica-Bold',
    )

    td_notes = ParagraphStyle(
        'TDNotes',
        parent=base_styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#475569'),
    )

    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'kpi_label': kpi_label,
        'kpi_value': kpi_value,
        'th': th_style,
        'td': td_style,
        'td_bold': td_bold,
        'td_notes': td_notes,
    }


def build_kpi_block(kpi_items, styles, total_width=770):
    """
    kpi_items: list of (label, value_str, optional_color)
    """
    if not kpi_items:
        return []
    
    col_width = total_width / len(kpi_items)
    data = [[
        Paragraph(item[0].upper(), styles['kpi_label']) for item in kpi_items
    ], [
        Paragraph(item[1], ParagraphStyle(
            f'KPIVal_{i}',
            parent=styles['kpi_value'],
            textColor=colors.HexColor(item[2]) if len(item) > 2 else colors.HexColor('#0f172a')
        )) for i, item in enumerate(kpi_items)
    ]]
    
    t = Table(data, colWidths=[col_width] * len(kpi_items))
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return [t, Spacer(1, 14)]


# ==========================================
# 1. TRANSACTIONS REPORT
# ==========================================
def generate_transactions_pdf(transactions_qs, filter_summary="", grand_total=Decimal('0.00')):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = get_report_styles()
    story = []

    # Title & Subtitle
    story.append(Paragraph("Transactions Report", styles['title']))
    sub_text = f"Generated on {datetime.now().strftime('%d/%m/%Y at %I:%M %p')}"
    if filter_summary:
        sub_text += f" &bull; Active Filters: {filter_summary}"
    story.append(Paragraph(sub_text, styles['subtitle']))

    # Financial Summaries
    total_count = transactions_qs.count()
    rec_sum = Decimal('0.00')
    paid_sum = Decimal('0.00')
    for tx in transactions_qs:
        amt = tx.amount or Decimal('0.00')
        if tx.transaction_type == 'Received':
            rec_sum += amt
        else:
            paid_sum += amt

    kpis = [
        ("Total Transactions", str(total_count)),
        ("Total Received", f"₹{rec_sum:,.2f}", "#16a34a"),
        ("Total Paid", f"₹{paid_sum:,.2f}", "#dc2626"),
        ("Net Position", f"₹{(rec_sum - paid_sum):,.2f}", "#2563eb"),
    ]
    story.extend(build_kpi_block(kpis, styles))

    # Table columns: Date(60), Type(55), Purpose(90), Contact/Party(95), Project(75), Method(60), Ref(60), Amount(70), Notes(205) = 770 total width
    col_widths = [60, 55, 90, 95, 75, 60, 60, 70, 205]
    headers = ["Date", "Type", "Purpose", "Contact / Party", "Project", "Method", "Reference", "Amount", "Associated Notes & Details"]

    table_data = [[Paragraph(h, styles['th']) for h in headers]]

    for tx in transactions_qs:
        tx_date = tx.date or tx.transaction_date
        d_str = tx_date.strftime("%d/%m/%Y") if tx_date else "-"
        
        type_color = "#16a34a" if tx.transaction_type == 'Received' else "#dc2626"
        type_p = Paragraph(f"<font color='{type_color}'><b>{tx.transaction_type}</b></font>", styles['td'])
        
        purpose_str = tx.payment_type or "-"
        if tx.payment_type_other_reason:
            purpose_str += f"<br/><font size='7' color='#64748b'>{tx.payment_type_other_reason}</font>"
        purpose_p = Paragraph(purpose_str, styles['td'])
        
        contact_name = tx.contact.name if tx.contact else (tx.paid_by or "-")
        contact_p = Paragraph(contact_name, styles['td'])
        
        proj_name = tx.project.project_name if tx.project else (tx.project_or_deal or "-")
        proj_p = Paragraph(proj_name, styles['td'])
        
        method_p = Paragraph(tx.payment_method or "-", styles['td'])
        ref_p = Paragraph(tx.reference or "-", styles['td'])
        
        amt_p = Paragraph(f"<font color='{type_color}'><b>₹{tx.amount:,.2f}</b></font>", styles['td_bold'])
        
        notes_text = tx.notes or "None"
        if tx.paid_by and tx.paid_by != contact_name:
            notes_text = f"Paid/Rec By: {tx.paid_by}. {notes_text}"
        notes_p = Paragraph(notes_text, styles['td_notes'])

        table_data.append([
            Paragraph(d_str, styles['td_bold']),
            type_p,
            purpose_p,
            contact_p,
            proj_p,
            method_p,
            ref_p,
            amt_p,
            notes_p
        ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))
    table.setStyle(TableStyle(t_style))
    story.append(table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 2. EXPENSES REPORT
# ==========================================
def generate_expenses_pdf(expenses_qs, filter_summary=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = get_report_styles()
    story = []

    story.append(Paragraph("Expenses Report", styles['title']))
    sub_text = f"Generated on {datetime.now().strftime('%d/%m/%Y at %I:%M %p')}"
    if filter_summary:
        sub_text += f" &bull; Active Filters: {filter_summary}"
    story.append(Paragraph(sub_text, styles['subtitle']))

    total_count = expenses_qs.count()
    paid_sum = Decimal('0.00')
    pending_sum = Decimal('0.00')
    for e in expenses_qs:
        amt = e.amount or Decimal('0.00')
        if e.status == 'Paid':
            paid_sum += amt
        else:
            pending_sum += amt

    kpis = [
        ("Total Expenses", str(total_count)),
        ("Total Paid", f"₹{paid_sum:,.2f}", "#16a34a"),
        ("Pending Payables", f"₹{pending_sum:,.2f}", "#dc2626"),
        ("Grand Total", f"₹{(paid_sum + pending_sum):,.2f}", "#0f172a"),
    ]
    story.extend(build_kpi_block(kpis, styles))

    # Columns: Date(60), Category(80), Description(140), Paid To(85), Paid By(85), Method(60), Status(55), Amount(70), Notes(135) = 770
    col_widths = [60, 80, 140, 85, 85, 60, 55, 70, 135]
    headers = ["Date", "Category", "Description", "Paid To", "Paid By", "Method", "Status", "Amount", "Attached Notes & Project"]

    table_data = [[Paragraph(h, styles['th']) for h in headers]]

    for e in expenses_qs:
        e_date = e.expense_date or e.date
        d_str = e_date.strftime("%d/%m/%Y") if e_date else "-"
        cat_str = e.get_category_display() if hasattr(e, 'get_category_display') else str(e.category or "-")
        
        status_color = "#16a34a" if e.status == 'Paid' else "#d97706"
        status_p = Paragraph(f"<font color='{status_color}'><b>{e.status or 'Paid'}</b></font>", styles['td'])
        
        notes_str = e.notes or "None"
        if e.project:
            notes_str = f"Project: {e.project.project_name}. {notes_str}"
        elif e.project_or_deal:
            notes_str = f"Ref: {e.project_or_deal}. {notes_str}"

        table_data.append([
            Paragraph(d_str, styles['td_bold']),
            Paragraph(cat_str, styles['td']),
            Paragraph(e.description or "-", styles['td']),
            Paragraph(e.paid_to or "-", styles['td']),
            Paragraph(e.paid_by or "-", styles['td']),
            Paragraph(e.payment_method or "-", styles['td']),
            status_p,
            Paragraph(f"<font color='#dc2626'><b>₹{e.amount:,.2f}</b></font>", styles['td_bold']),
            Paragraph(notes_str, styles['td_notes'])
        ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))
    table.setStyle(TableStyle(t_style))
    story.append(table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 3. CONTACTS REPORT
# ==========================================
def generate_contacts_pdf(contacts_qs, filter_summary=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = get_report_styles()
    story = []

    story.append(Paragraph("Contacts Report", styles['title']))
    sub_text = f"Generated on {datetime.now().strftime('%d/%m/%Y at %I:%M %p')}"
    if filter_summary:
        sub_text += f" &bull; Active Filters: {filter_summary}"
    story.append(Paragraph(sub_text, styles['subtitle']))

    total_count = contacts_qs.count()
    partners_count = contacts_qs.filter(contact_type='Partner').count()
    customers_count = contacts_qs.filter(contact_type='Customer').count()
    brokers_count = contacts_qs.filter(contact_type='Broker').count()

    kpis = [
        ("Total Contacts", str(total_count)),
        ("Partners", str(partners_count), "#2563eb"),
        ("Customers", str(customers_count), "#16a34a"),
        ("Brokers / Landowners", f"{brokers_count} Brokers", "#d97706"),
    ]
    story.extend(build_kpi_block(kpis, styles))

    # Columns: Name(110), Type(70), Mobile(80), WhatsApp(80), Email(100), Location(90), Project(80), Notes & Address(160) = 770
    col_widths = [110, 70, 80, 80, 100, 90, 80, 160]
    headers = ["Contact Name", "Type", "Mobile", "WhatsApp", "Email", "Location", "Project", "Notes & Full Address"]

    table_data = [[Paragraph(h, styles['th']) for h in headers]]

    for c in contacts_qs:
        type_str = c.contact_type or "Other"
        if c.ownership_percentage and c.ownership_percentage > 0:
            type_str += f" ({c.ownership_percentage}%)"
            
        notes_arr = []
        if c.address:
            notes_arr.append(f"Address: {c.address}")
        if c.notes:
            notes_arr.append(f"Notes: {c.notes}")
        combined_notes = " | ".join(notes_arr) if notes_arr else "None"

        table_data.append([
            Paragraph(f"<b>{c.name}</b>", styles['td']),
            Paragraph(type_str, styles['td_bold']),
            Paragraph(c.mobile or "-", styles['td']),
            Paragraph(c.whatsapp or "-", styles['td']),
            Paragraph(c.email or "-", styles['td']),
            Paragraph(c.location or "-", styles['td']),
            Paragraph(c.project.project_name if c.project else "-", styles['td']),
            Paragraph(combined_notes, styles['td_notes'])
        ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))
    table.setStyle(TableStyle(t_style))
    story.append(table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 4. SITES INVENTORY REPORT
# ==========================================
def generate_sites_pdf(sites_qs, filter_summary=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = get_report_styles()
    story = []

    story.append(Paragraph("Sites Inventory Report", styles['title']))
    sub_text = f"Generated on {datetime.now().strftime('%d/%m/%Y at %I:%M %p')}"
    if filter_summary:
        sub_text += f" &bull; Active Filters: {filter_summary}"
    story.append(Paragraph(sub_text, styles['subtitle']))

    total_count = sites_qs.count()
    sold_count = sites_qs.filter(status='Sold').count()
    avail_count = sites_qs.filter(status='Available').count()
    booked_count = sites_qs.filter(status='Booked').count()
    total_val = Decimal('0.00')
    total_rec = Decimal('0.00')
    total_bal = Decimal('0.00')
    for s in sites_qs:
        total_val += (s.price or Decimal('0.00'))
        total_rec += (s.amount_received or Decimal('0.00'))
        total_bal += (s.balance or Decimal('0.00'))

    kpis = [
        ("Total Units", f"{total_count} ({sold_count} Sold, {booked_count} Booked, {avail_count} Avail)"),
        ("Total Inventory Value", f"₹{total_val:,.2f}", "#2563eb"),
        ("Total Received", f"₹{total_rec:,.2f}", "#16a34a"),
        ("Outstanding Balance", f"₹{total_bal:,.2f}", "#dc2626"),
    ]
    story.extend(build_kpi_block(kpis, styles))

    # Columns: Site #(50), Project(75), Area/Dims(70), Facing/Road(70), Status(55), Price(65), Customer(80), Received(60), Balance(60), Dates & Notes(185) = 770
    col_widths = [50, 75, 70, 70, 55, 65, 80, 60, 60, 185]
    headers = ["Site #", "Project", "Area / Dims", "Facing / Road", "Status", "Price", "Customer", "Received", "Balance", "Dates, Notes & Remarks"]

    table_data = [[Paragraph(h, styles['th']) for h in headers]]

    for s in sites_qs:
        status_colors = {
            'Sold': '#16a34a',
            'Booked': '#d97706',
            'Available': '#2563eb',
            'Blocked': '#6b7280',
            'Cancelled': '#dc2626'
        }
        col = status_colors.get(s.status, '#0f172a')
        status_p = Paragraph(f"<font color='{col}'><b>{s.status}</b></font>", styles['td'])
        
        area_dims = f"{s.area or '-'}"
        if s.dimensions:
            area_dims += f"<br/><font size='7' color='#64748b'>{s.dimensions}</font>"
            
        facing_road = f"{s.facing or '-'}"
        if s.road_width:
            facing_road += f"<br/><font size='7' color='#64748b'>{s.road_width} road</font>"

        cust_str = s.customer.name if s.customer else "-"
        
        dates_notes_arr = []
        if s.booking_date:
            dates_notes_arr.append(f"Booked: {s.booking_date.strftime('%d/%m/%Y')}")
        if s.sold_date:
            dates_notes_arr.append(f"Sold: {s.sold_date.strftime('%d/%m/%Y')}")
        if s.notes:
            dates_notes_arr.append(f"Notes: {s.notes}")
        combined_dn = " | ".join(dates_notes_arr) if dates_notes_arr else "None"

        table_data.append([
            Paragraph(f"<b>{s.site_number}</b>", styles['td']),
            Paragraph(s.project.project_name if s.project else "-", styles['td']),
            Paragraph(area_dims, styles['td']),
            Paragraph(facing_road, styles['td']),
            status_p,
            Paragraph(f"₹{s.price:,.2f}", styles['td_bold']),
            Paragraph(cust_str, styles['td']),
            Paragraph(f"<font color='#16a34a'>₹{s.amount_received:,.2f}</font>", styles['td']),
            Paragraph(f"<font color='#dc2626'>₹{s.balance:,.2f}</font>", styles['td_bold']),
            Paragraph(combined_dn, styles['td_notes'])
        ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))
    table.setStyle(TableStyle(t_style))
    story.append(table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 5. LEADS REPORT
# ==========================================
def generate_leads_pdf(leads_qs, filter_summary=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = get_report_styles()
    story = []

    story.append(Paragraph("Leads Report", styles['title']))
    sub_text = f"Generated on {datetime.now().strftime('%d/%m/%Y at %I:%M %p')}"
    if filter_summary:
        sub_text += f" &bull; Active Filters: {filter_summary}"
    story.append(Paragraph(sub_text, styles['subtitle']))

    total_count = leads_qs.count()
    converted_count = leads_qs.filter(status='Converted').count()
    active_count = leads_qs.exclude(status__in=['Converted', 'Not Interested', 'Lost']).count()

    kpis = [
        ("Total Leads", str(total_count)),
        ("Active Pipeline Leads", str(active_count), "#2563eb"),
        ("Converted Deals", str(converted_count), "#16a34a"),
        ("Conversion Rate", f"{int((converted_count / total_count * 100)) if total_count else 0}%", "#d97706"),
    ]
    story.extend(build_kpi_block(kpis, styles))

    # Columns: Name(110), Phone(80), Status(65), Lead Type(75), Project/Prop(95), Source(70), Next Follow-up(85), Notes & Details(190) = 770
    col_widths = [110, 80, 65, 75, 95, 70, 85, 190]
    headers = ["Lead Name", "Phone", "Status", "Lead Type", "Interested Property", "Source", "Next Follow-up", "Notes & Location"]

    table_data = [[Paragraph(h, styles['th']) for h in headers]]

    for l in leads_qs:
        follow_str = l.next_follow_up.strftime("%d/%m/%Y %I:%M %p") if l.next_follow_up else "-"
        prop_str = l.interested_property or (l.project.project_name if l.project else "-")
        
        status_color = "#16a34a" if l.status == 'Converted' else ("#dc2626" if l.status in ['Lost', 'Not Interested'] else "#2563eb")
        status_p = Paragraph(f"<font color='{status_color}'><b>{l.status}</b></font>", styles['td'])
        
        notes_arr = []
        if l.location:
            notes_arr.append(f"Loc: {l.location}")
        if l.notes:
            notes_arr.append(f"Notes: {l.notes}")
        combined_notes = " | ".join(notes_arr) if notes_arr else "None"

        table_data.append([
            Paragraph(f"<b>{l.name}</b>", styles['td']),
            Paragraph(l.phone or "-", styles['td']),
            status_p,
            Paragraph(l.lead_type or "-", styles['td']),
            Paragraph(prop_str, styles['td']),
            Paragraph(l.source or "-", styles['td']),
            Paragraph(follow_str, styles['td_bold']),
            Paragraph(combined_notes, styles['td_notes'])
        ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))
    table.setStyle(TableStyle(t_style))
    story.append(table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 6. DEALS REPORT
# ==========================================
def generate_deals_pdf(deals_qs, filter_summary=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = get_report_styles()
    story = []

    story.append(Paragraph("Land Deals Report", styles['title']))
    sub_text = f"Generated on {datetime.now().strftime('%d/%m/%Y at %I:%M %p')}"
    if filter_summary:
        sub_text += f" &bull; Active Filters: {filter_summary}"
    story.append(Paragraph(sub_text, styles['subtitle']))

    total_count = deals_qs.count()
    active_deals = deals_qs.exclude(status__in=['Deal Closed', 'Deal Cancelled', 'Deal Lost'])
    pipeline_val = Decimal('0.00')
    closed_val = Decimal('0.00')
    for d in deals_qs:
        price = d.negotiated_price or d.expected_price or Decimal('0.00')
        if d.status == 'Deal Closed':
            closed_val += price
        elif d.status not in ['Deal Cancelled', 'Deal Lost']:
            pipeline_val += price

    kpis = [
        ("Total Deals", str(total_count)),
        ("Active Pipeline Value", f"₹{pipeline_val:,.2f}", "#2563eb"),
        ("Closed Deals Value", f"₹{closed_val:,.2f}", "#16a34a"),
        ("Active Deals Count", str(active_deals.count()), "#d97706"),
    ]
    story.extend(build_kpi_block(kpis, styles))

    # Columns: Deal Name(110), Landowner/Broker(100), Location/Survey(95), Area(60), Status(75), Expected(65), Negotiated(65), Next Follow(75), Notes(125) = 770
    col_widths = [110, 100, 95, 60, 75, 65, 65, 75, 125]
    headers = ["Deal Name", "Landowner / Broker", "Location / Survey #", "Area", "Status", "Expected", "Negotiated", "Next Follow-up", "Notes & Remarks"]

    table_data = [[Paragraph(h, styles['th']) for h in headers]]

    for d in deals_qs:
        owner_broker = d.landowner.name if d.landowner else "-"
        if d.broker:
            owner_broker += f"<br/><font size='7' color='#64748b'>Broker: {d.broker.name}</font>"

        loc_survey = d.location or "-"
        if d.survey_number:
            loc_survey += f"<br/><font size='7' color='#64748b'>Sy #{d.survey_number}</font>"

        status_color = "#16a34a" if d.status == 'Deal Closed' else ("#dc2626" if d.status in ['Deal Cancelled', 'Deal Lost'] else "#2563eb")
        status_p = Paragraph(f"<font color='{status_color}'><b>{d.status}</b></font>", styles['td'])

        exp_str = f"₹{d.expected_price:,.2f}" if d.expected_price else "-"
        neg_str = f"₹{d.negotiated_price:,.2f}" if d.negotiated_price else "-"
        follow_str = d.next_follow_up.strftime("%d/%m/%Y") if d.next_follow_up else "-"

        table_data.append([
            Paragraph(f"<b>{d.deal_name}</b>", styles['td']),
            Paragraph(owner_broker, styles['td']),
            Paragraph(loc_survey, styles['td']),
            Paragraph(d.land_area or "-", styles['td']),
            status_p,
            Paragraph(exp_str, styles['td']),
            Paragraph(neg_str, styles['td_bold']),
            Paragraph(follow_str, styles['td']),
            Paragraph(d.notes or "None", styles['td_notes'])
        ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))
    table.setStyle(TableStyle(t_style))
    story.append(table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
