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
        ("۱. اطلاعات مربوط به دانشجو", "مشخصات دانشجو طبق اطلاعات واردشده؛ موارد نامعلوم خالی است."),
        ("۲. اطلاعات مربوط به استاد راهنما", "نام استاد راهنما: " + data.get("supervisor", "") + "\nسایر سوابق و مشخصات اداری استاد: نیازمند تکمیل توسط گروه آموزشی."),
        ("۳. اطلاعات مربوط به استاد مشاور", "نام استاد مشاور: " + data.get("advisor", "") + "\nسایر مشخصات اداری استاد مشاور: نیازمند تکمیل توسط گروه آموزشی."),
        ("۴. اطلاعات مربوط به پایان‌نامه", "عنوان فارسی: " + title + "\nعنوان انگلیسی: " + data.get("title_en", "") + "\nرشته: " + data.get("field", "") + "\nگرایش: " + data.get("specialization", "") + "\nمقطع: " + data.get("degree", "کارشناسی ارشد") + "\nنوع تحقیق: " + data.get("research_type", "") + "\nزبان: " + data.get("language", "فارسی") + "\nتعداد واحد: " + data.get("credits", "") + "\nپرسش اصلی: " + data.get("main_question", "")),
        ("۵. بیان مسئله تحقیق", data.get("problem_statement", "")),
        ("۶. اهمیت و ضرورت انجام تحقیق", data.get("significance", "")),
        ("۷. مرور ادبیات و سوابق مربوط", data.get("literature_review", "")),
        ("۸. جنبه جدید بودن و نوآوری", data.get("novelty", "")),
        ("۹. کلمات کلیدی به فارسی", data.get("keywords_fa", "")),
        ("۱۰. کلمات کلیدی به انگلیسی", data.get("keywords_en", "")),
        ("۱۱. اهداف مشخص تحقیق", data.get("objectives", "")),
        ("۱۲. نام بهره‌وران", data.get("beneficiaries", "")),
        ("۱۳. سؤال‌های تحقیق", data.get("research_questions", "")),
        ("۱۴. فرضیه‌های تحقیق", data.get("hypotheses", "")),
        ("۱۵. تعریف واژه‌ها و اصطلاحات فنی و تخصصی", data.get("definitions", "")),
        ("۱۶. فهرست منابع و مآخذ", ""),
        ("۱۷. پایش آزاد", data.get("free_pajesh", "")),
        ("۱۸. جدول زمان‌بندی", ""),
        ("۱۹. روش‌شناسی تحقیق", "\n".join([
            "نوع روش تحقیق: " + data.get("method_type", ""),
            "روش گردآوری اطلاعات: " + data.get("data_collection", ""),
            "ابزار گردآوری اطلاعات: " + data.get("instruments", ""),
            "روش تجزیه و تحلیل: " + data.get("analysis_method", ""),
            "جامعه و نمونه: " + data.get("population_sample", ""),
            "معیارهای ورود و خروج: " + data.get("inclusion_exclusion", ""),
            "ملاحظات اخلاقی: " + data.get("ethical_notes", ""),
            "محدودیت‌ها: " + data.get("limitations", ""),
        ])),
        ("۲۰. جدول متغیرها", ""),
        ("۲۱. هزینه‌های تحقیق پایان‌نامه", data.get("budget_note", "")),
        ("۲۲. تأیید طرح توسط استادان راهنما و مشاور", "نام، تاریخ و امضا: پس از بررسی حضوری تکمیل شود."),
        ("۲۳. ضمایم", "فرم‌های تعهد دانشجو و استادان، اطلاعات تکمیلی، کدهای اداری و سایر پیوست‌ها باید از نسخه رسمی دانشگاه تکمیل شوند."),
    ]
    for heading, body in sections:
        _add_heading(doc, heading, 1)
        if body:
            _add_text(doc, body)
        if heading.startswith("۱."):
            _add_table(doc, ["مشخصات دانشجو", "اطلاعات"], [
                ["نام و نام خانوادگی", data.get("student", "")],
                ["شماره دانشجویی", data.get("student_number", "")],
                ["رشته و گرایش", (data.get("field", "") + " ـ " + data.get("specialization", "")).strip(" ـ")],
                ["مقطع", data.get("degree", "کارشناسی ارشد")],
                ["دانشکده", data.get("college", "")],
            ])
        if heading.startswith("۱۶."):
            rows = []
            for item in data.get("references", []):
                rows.append([item.get("id", ""), ", ".join(item.get("authors") or []),
                    item.get("year", ""), item.get("title", ""), item.get("venue", ""),
                    item.get("doi", ""), item.get("url", "")])
            _add_table(doc, ["ردیف", "نویسندگان", "سال", "عنوان", "نشریه/منبع", "DOI", "پیوند"],
                rows or [["", "", "", "منبعی ثبت نشده", "", "", ""]])
        if heading.startswith("۱۸."):
            rows = [[x.get("stage", ""), x.get("start_month", ""), x.get("end_month", "")]
                for x in data.get("timeline", []) if isinstance(x, dict)]
            _add_table(doc, ["مرحله", "از ماه", "تا ماه"],
                rows or [["مطالعات کتابخانه‌ای", "۱", "۲"], ["جمع‌آوری اطلاعات", "۳", "۴"],
                         ["تحلیل داده‌ها", "۵", "۶"], ["نگارش و دفاع", "۷", "۸"]])
        if heading.startswith("۲۰."):
            rows = [[x.get(k, "") for k in ["name", "role", "type", "measurement", "scale"]]
                for x in data.get("variables", []) if isinstance(x, dict)]
            _add_table(doc, ["عنوان متغیر", "نقش متغیر", "نوع متغیر", "نحوه اندازه‌گیری", "مقیاس"],
                rows or [["نیازمند تعیین بر اساس طرح نهایی", "", "", "", ""]])
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
    parts = ['<html><head><meta charset="utf-8"><style>@page{size:A4;margin:18mm}body{font-family:Arial,"Tahoma";direction:rtl;text-align:right;font-size:10pt;line-height:1.7}h1,h2{color:#17365d}h2{font-size:13pt;border-bottom:1px solid #bbb;padding-bottom:3px}table{width:100%;border-collapse:collapse;margin:8px 0 18px}td,th{border:1px solid #777;padding:5px;text-align:right;vertical-align:top} .ltr{direction:ltr;text-align:left}</style></head><body>']
    def para(value):
        return esc(str(value or "نیازمند تکمیل")).replace("\n", "<br>")
    parts.append("<h1>دانشگاه آزاد اسلامی ـ واحد شیراز</h1><h2>فرم طرح تحقیق پایان‌نامه</h2>")
    parts.append("<h2>" + para(data.get("title_fa") or "پیش‌نویس پروپوزال") + "</h2>")
    parts.append("<p class='ltr'>" + para(data.get("title_en", "")) + "</p>")
    parts.append("<h2>۱ تا ۳. اطلاعات دانشجو و استادان</h2><table>")
    for label, key in [("نام دانشجو","student"),("شماره دانشجویی","student_number"),
        ("مقطع","degree"),("رشته","field"),("گرایش","specialization"),
        ("دانشکده","college"),("استاد راهنما","supervisor"),("استاد مشاور","advisor"),
        ("تعداد واحد","credits")]:
        parts.append("<tr><th>" + label + "</th><td>" + para(data.get(key, "")) + "</td></tr>")
    parts.append("</table>")
    labels = [
        ("research_type","۴. نوع تحقیق"),("main_question","۴. پرسش اصلی تحقیق"),
        ("problem_statement","۵. بیان مسئله"),("significance","۶. اهمیت و ضرورت"),
        ("literature_review","۷. مرور ادبیات و سوابق"),("novelty","۸. نوآوری"),
        ("keywords_fa","۹. کلیدواژه‌های فارسی"),("keywords_en","۱۰. کلیدواژه‌های انگلیسی"),
        ("objectives","۱۱. اهداف مشخص"),("beneficiaries","۱۲. بهره‌وران"),
        ("research_questions","۱۳. سؤالات تحقیق"),("hypotheses","۱۴. فرضیه‌ها"),
        ("definitions","۱۵. تعاریف تخصصی"),("free_pajesh","۱۷. پایش آزاد"),
        ("method_type","۱۹. الف) نوع روش تحقیق"),("data_collection","۱۹. ب) روش گردآوری اطلاعات"),
        ("instruments","۱۹. ج) ابزار گردآوری اطلاعات"),("analysis_method","۱۹. د) روش تجزیه و تحلیل"),
        ("population_sample","جامعه و نمونه پیشنهادی"),("inclusion_exclusion","معیارهای ورود و خروج"),
        ("ethical_notes","ملاحظات اخلاقی"),("limitations","محدودیت‌ها"),
    ]
    for key, label in labels:
        parts.append("<h2>" + label + "</h2><p>" + para(data.get(key, "")) + "</p>")
    parts.append("<h2>۱۶. فهرست منابع و مآخذ</h2><ol>")
    for item in data.get("references", []):
        authors = ", ".join(item.get("authors") or [])
        ref = f"{authors} ({item.get('year','')}). {item.get('title','')}. {item.get('venue','')}."
        url = item.get("url") or ""
        parts.append("<li>" + esc(ref) + ((" <a href='" + esc(url) + "'>" + esc(url) + "</a>") if url else "") + "</li>")
    parts.append("</ol>")
    parts.append("<h2>۱۸. جدول زمان‌بندی</h2><table><tr><th>مرحله</th><th>از ماه</th><th>تا ماه</th></tr>")
    for row in data.get("timeline", []):
        if isinstance(row, dict):
            parts.append("<tr><td>" + para(row.get("stage")) + "</td><td>" + para(row.get("start_month")) + "</td><td>" + para(row.get("end_month")) + "</td></tr>")
    parts.append("</table><h2>۲۰. جدول متغیرها</h2><table><tr><th>عنوان متغیر</th><th>نقش</th><th>نوع</th><th>اندازه‌گیری</th><th>مقیاس</th></tr>")
    for row in data.get("variables", []):
        if isinstance(row, dict):
            parts.append("<tr>" + "".join("<td>" + para(row.get(key)) + "</td>" for key in ["name","role","type","measurement","scale"]) + "</tr>")
    parts.append("</table><h2>۲۱. هزینه‌های تحقیق</h2><p>" + para(data.get("budget_note")) + "</p>")
    parts.append("<h2>۲۲. تأیید طرح و امضاها</h2><p>پس از بررسی حضوری تکمیل شود.</p>")
    parts.append("<h2>۲۳. ضمایم</h2><p>فرم‌های تعهد، مشخصات تکمیلی، کدها و امضاها باید از نسخه رسمی دانشگاه تکمیل شوند.</p>")
    parts.append("<p><b>تذکر:</b> این فایل پیش‌نویس کمکی است، نه نسخه رسمی فرم دانشگاه. پیش از ثبت، منابع و روش باید راستی‌آزمایی و بخش‌های اداری تکمیل شوند.</p></body></html>")
    return "".join(parts)
