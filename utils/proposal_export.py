"""DOCX and Markdown exporters for the Shiraz Azad University proposal form."""
from __future__ import annotations

import html
from pathlib import Path


def _rtl_paragraph(paragraph):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    ppr = paragraph._p.get_or_add_pPr()
    bidi = ppr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}bidi")
    if bidi is None:
        from docx.oxml import OxmlElement
        bidi = OxmlElement("w:bidi")
        ppr.append(bidi)
    bidi.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "1")


def _rtl_run(run, bold=False, size=11):
    from docx.shared import Pt
    run.bold = bold
    run.font.name = "B Nazanin"
    run.font.size = Pt(size)
    rpr = run._element.get_or_add_rPr()
    from docx.oxml import OxmlElement
    rtl = OxmlElement("w:rtl")
    rtl.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "1")
    rpr.append(rtl)


def _add_text(doc, text, bold=False, size=11):
    if not text:
        text = "—"
    for line in str(text).splitlines():
        p = doc.add_paragraph()
        _rtl_paragraph(p)
        _rtl_run(p.add_run(line), bold=bold, size=size)


def _add_heading(doc, title, level=1):
    p = doc.add_paragraph()
    _rtl_paragraph(p)
    _rtl_run(p.add_run(title), bold=True, size=16 if level == 1 else 13)


def _add_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = str(header)
        for p in cell.paragraphs:
            _rtl_paragraph(p)
            for run in p.runs:
                _rtl_run(run, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value or "—")
            for p in cells[i].paragraphs:
                _rtl_paragraph(p)
                for run in p.runs:
                    _rtl_run(run)
    doc.add_paragraph()


def export_proposal_docx(data, output_path):
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)
    title = data.get("title_fa") or "پیش‌نویس پروپوزال پژوهشی"
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _rtl_paragraph(p)
    _rtl_run(p.add_run("دانشگاه آزاد اسلامی ـ واحد شیراز\nفرم طرح تحقیق پایان‌نامه کارشناسی ارشد"), bold=True, size=17)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _rtl_paragraph(p)
    _rtl_run(p.add_run(title), bold=True, size=16)
    _add_text(doc, "عنوان انگلیسی: " + (data.get("title_en") or ""))
    _add_table(doc, ["مشخصات", "اطلاعات"], [
        ["نام دانشجو", data.get("student", "")],
        ["شماره دانشجویی", data.get("student_number", "")],
        ["مقطع", data.get("degree", "کارشناسی ارشد")],
        ["رشته", data.get("field", "")],
        ["گرایش", data.get("specialization", "")],
        ["دانشکده", data.get("college", "")],
        ["استاد راهنما", data.get("supervisor", "")],
        ["استاد مشاور", data.get("advisor", "")],
        ["تعداد واحد پایان‌نامه", data.get("credits", "")],
    ])
    sections = [
        ("۱. اطلاعات مربوط به دانشجو و استادان", data.get("admin_note", "")),
        ("۲. اطلاعات مربوط به پایان‌نامه", "نوع تحقیق: " + data.get("research_type", "") + "\nزبان: " + data.get("language", "فارسی") + "\nپرسش اصلی: " + data.get("main_question", "")),
        ("۳. بیان مسئله تحقیق", data.get("problem_statement", "")),
        ("۴. اهمیت و ضرورت انجام تحقیق", data.get("significance", "")),
        ("۵. مرور ادبیات و سوابق مربوط", data.get("literature_review", "")),
        ("۶. جنبه جدید بودن و نوآوری", data.get("novelty", "")),
        ("۷. کلمات کلیدی فارسی", data.get("keywords_fa", "")),
        ("۸. کلمات کلیدی انگلیسی", data.get("keywords_en", "")),
        ("۹. اهداف مشخص تحقیق", data.get("objectives", "")),
        ("۱۰. نام بهره‌وران", data.get("beneficiaries", "")),
        ("۱۱. سؤال‌های تحقیق", data.get("research_questions", "")),
        ("۱۲. فرضیه‌های تحقیق", data.get("hypotheses", "")),
        ("۱۳. تعریف واژه‌ها و اصطلاحات تخصصی", data.get("definitions", "")),
        ("۱۴. فهرست منابع و مآخذ", ""),
        ("۱۵. پایش آزاد", data.get("free_pajesh", "")),
        ("۱۶. روش‌شناسی تحقیق", "\n".join([
            "نوع روش تحقیق: " + data.get("method_type", ""),
            "روش گردآوری اطلاعات: " + data.get("data_collection", ""),
            "ابزار گردآوری اطلاعات: " + data.get("instruments", ""),
            "روش تجزیه و تحلیل: " + data.get("analysis_method", ""),
            "جامعه و نمونه: " + data.get("population_sample", ""),
            "معیارهای ورود و خروج: " + data.get("inclusion_exclusion", ""),
        ])),
        ("۱۷. جدول زمان‌بندی", ""),
        ("۱۸. جدول متغیرها", ""),
        ("۱۹. هزینه‌های تحقیق پایان‌نامه", data.get("budget_note", "")),
        ("۲۰. ملاحظات اخلاقی و محدودیت‌ها", data.get("ethical_notes", "") + "\n" + data.get("limitations", "")),
        ("۲۱. تأیید طرح توسط استادان راهنما و مشاور", "نام و امضا و تاریخ: پس از بررسی حضوری تکمیل شود."),
        ("۲۲. ضمایم و فرم‌های اداری", "فرم‌های تعهد، مشخصات تکمیلی استادان، کدها، امضاها و تأییدهای اداری باید از نسخه رسمی دانشگاه تکمیل شوند."),
    ]
    for heading, body in sections:
        _add_heading(doc, heading, 1)
        if body:
            _add_text(doc, body)
        if heading.startswith("۱۴."):
            refs = data.get("references", [])
            rows = []
            for item in refs:
                authors = ", ".join(item.get("authors") or [])
                rows.append([
                    item.get("id", ""), authors, item.get("year", ""),
                    item.get("title", ""), item.get("venue", ""),
                    item.get("doi", ""), item.get("url", ""),
                ])
            _add_table(doc, ["ردیف", "نویسندگان", "سال", "عنوان", "نشریه/منبع", "DOI", "پیوند"], rows or [["", "", "", "منبعی ثبت نشده", "", "", ""]])
        if heading.startswith("۱۷."):
            rows = [[x.get("stage", ""), x.get("start_month", ""), x.get("end_month", "")] for x in data.get("timeline", []) if isinstance(x, dict)]
            _add_table(doc, ["مرحله", "از ماه", "تا ماه"], rows or [["مطالعات کتابخانه‌ای", "۱", "۲"], ["جمع‌آوری اطلاعات", "۳", "۴"], ["تحلیل داده‌ها", "۵", "۶"], ["نگارش و دفاع", "۷", "۸"]])
        if heading.startswith("۱۸."):
            rows = [[x.get(k, "") for k in ["name", "role", "type", "measurement", "scale"]] for x in data.get("variables", []) if isinstance(x, dict)]
            _add_table(doc, ["عنوان متغیر", "نقش متغیر", "نوع متغیر", "نحوه اندازه‌گیری", "مقیاس"], rows or [["نیازمند تعیین بر اساس طرح نهایی", "", "", "", ""]])
    _add_heading(doc, "تذکر مهم برای ثبت رسمی", 1)
    _add_text(doc, "این فایل پیش‌نویس کمکی است و جایگزین نسخه رسمی فرم دانشگاه نیست. مشخصات اداری، هزینه‌های واقعی، تأییدها و امضاها باید توسط دانشجو و واحد مربوط تکمیل شوند. همه منابع و روش پیشنهادی باید پیش از ثبت راستی‌آزمایی شوند.")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    return str(output_path)


def proposal_markdown(data):
    lines = ["# " + (data.get("title_fa") or "پیش‌نویس پروپوزال"), "",
             "**عنوان انگلیسی:** " + data.get("title_en", ""), ""]
    keys = [
        ("problem_statement", "بیان مسئله"), ("significance", "اهمیت و ضرورت"),
        ("literature_review", "مرور ادبیات و پیشینه"), ("novelty", "نوآوری"),
        ("objectives", "اهداف"), ("beneficiaries", "بهره‌وران"),
        ("research_questions", "سؤالات"), ("hypotheses", "فرضیه‌ها"),
        ("definitions", "تعاریف تخصصی"), ("free_pajesh", "پایش آزاد"),
        ("method_type", "نوع روش"), ("data_collection", "گردآوری اطلاعات"),
        ("instruments", "ابزار"), ("analysis_method", "تحلیل اطلاعات"),
        ("population_sample", "جامعه و نمونه"), ("inclusion_exclusion", "معیارهای ورود و خروج"),
        ("ethical_notes", "اخلاق پژوهش"), ("limitations", "محدودیت‌ها"),
    ]
    for key, label in keys:
        lines.extend(["## " + label, "", data.get(key, "") or "نیازمند تکمیل", ""])
    lines.extend(["## منابع", ""])
    for item in data.get("references", []):
        authors = ", ".join(item.get("authors") or [])
        lines.append(f"- {authors} ({item.get('year','')}). {item.get('title','')}. {item.get('venue','')}. {item.get('doi','')} {item.get('url','')}")
    return "\n".join(lines)


def proposal_html(data):
    esc = html.escape
    parts = ['<html><head><meta charset="utf-8"><style>body{font-family:Arial,"Tahoma";direction:rtl;text-align:right;font-size:11pt;line-height:1.8}h1,h2{color:#17365d}table{width:100%;border-collapse:collapse}td,th{border:1px solid #777;padding:5px;text-align:right} .ltr{direction:ltr;text-align:left}</style></head><body>']
    parts.append("<h1>دانشگاه آزاد اسلامی ـ واحد شیراز</h1><h2>" + esc(data.get("title_fa") or "پیش‌نویس پروپوزال") + "</h2>")
    parts.append("<p class='ltr'>" + esc(data.get("title_en", "")) + "</p>")
    labels = [
        ("problem_statement","بیان مسئله"),("significance","اهمیت و ضرورت"),
        ("literature_review","مرور ادبیات و سوابق"),("novelty","نوآوری"),
        ("keywords_fa","کلیدواژه‌های فارسی"),("keywords_en","کلیدواژه‌های انگلیسی"),
        ("objectives","اهداف"),("beneficiaries","بهره‌وران"),
        ("research_questions","سؤالات"),("hypotheses","فرضیه‌ها"),
        ("definitions","تعاریف تخصصی"),("free_pajesh","پایش آزاد"),
        ("method_type","نوع روش تحقیق"),("data_collection","گردآوری اطلاعات"),
        ("instruments","ابزار گردآوری"),("analysis_method","روش تحلیل"),
        ("population_sample","جامعه و نمونه"),("inclusion_exclusion","معیارهای ورود و خروج"),
        ("ethical_notes","ملاحظات اخلاقی"),("limitations","محدودیت‌ها"),
    ]
    for key, label in labels:
        text = esc(data.get(key, "") or "نیازمند تکمیل").replace("\n", "<br>")
        parts.append("<h2>" + label + "</h2><p>" + text + "</p>")
    parts.append("<h2>منابع</h2><ol>")
    for item in data.get("references", []):
        authors = ", ".join(item.get("authors") or [])
        ref = f"{authors} ({item.get('year','')}). {item.get('title','')}. {item.get('venue','')}."
        url = item.get("url") or ""
        parts.append("<li>" + esc(ref) + ((" <a href='" + esc(url) + "'>" + esc(url) + "</a>") if url else "") + "</li>")
    parts.append("</ol><p><b>تذکر:</b> پیش‌نویس نیازمند بازبینی علمی و تکمیل فرم‌های اداری است.</p></body></html>")
    return "".join(parts)
