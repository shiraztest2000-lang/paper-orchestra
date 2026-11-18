"""Proposal drafting engine using public scholarly metadata and the configured LLM."""
import json
import os

def _parse_json(raw):
    value = (raw or "").strip()
    fence = chr(96) * 3
    if value.startswith(fence):
        value = value[len(fence):].strip()
        if value.endswith(fence):
            value = value[:-len(fence)].strip()
        if value.lower().startswith("json"):
            value = value[4:].strip()
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        start, end = value.find("{"), value.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("پاسخ مدل ساختار JSON معتبر نداشت.")
        data = json.loads(value[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("ساختار پاسخ پروپوزال معتبر نیست.")
    return data

def _text(value):
    if isinstance(value, list):
        return "\n".join("• " + str(x) for x in value if str(x).strip())
    return str(value or "").strip()

def generate_proposal(topic, metadata, cutoff_date=None, max_sources=20, progress_callback=None):
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("موضوع پژوهش را وارد کنید.")
    def progress(msg):
        if progress_callback:
            progress_callback(msg)
    progress("در حال جستجوی منابع علمی آزاد…")
    from utils.literature_search import search_academic_candidates
    found = search_academic_candidates(topic, cutoff_date=cutoff_date, limit=max_sources)
    if not found:
        raise ValueError("منبع علمی پیدا نشد؛ موضوع را با کلیدواژه‌های دقیق‌تر امتحان کنید.")
    sources = []
    for index, item in enumerate(found, 1):
        sources.append({
            "id": index, "title": item.get("title", ""), "year": item.get("year", ""),
            "authors": item.get("authors", []), "venue": item.get("venue", ""),
            "doi": item.get("doi", ""), "url": item.get("url", ""),
            "indexed_by": item.get("sources", []), "open_access": item.get("open_access"),
        })
    prompt = f"""
تو پژوهشگر دانشگاهی و متخصص روش تحقیق هستی. برای فرم طرح تحقیق پایان‌نامه کارشناسی ارشد دانشگاه آزاد اسلامی واحد شیراز، پیش‌نویس کامل فارسی تهیه کن.
موضوع: {topic}
اطلاعات واقعی کاربر: {json.dumps(metadata, ensure_ascii=False)}
منابع بازیابی‌شده: {json.dumps(sources, ensure_ascii=False)}
قواعد:
- فقط JSON معتبر برگردان.
- فقط از منابع ورودی استفاده کن؛ ارجاعات درون متن [1]، [2] و ... و فقط با idهای همین فهرست باشد. مقاله، نویسنده، DOI، آمار یا نتیجه جعل نکن.
- اگر اطلاعات کتاب‌شناختی موجود نیست، خالی بگذار. منابع را در پیشینه مقایسه و تحلیل کن.
- مسئله، شکاف، ضرورت، نوآوری، اهداف، پرسش‌ها، فرضیه‌ها و روش‌شناسی باید با هم سازگار باشند.
- روش، جامعه، نمونه، ابزار، روایی و پایایی را در صورت نبود اطلاعات، پیشنهادی و نیازمند تأیید اعلام کن؛ فرضیه را برای پژوهش کیفی/اکتشافی تحمیل نکن.
- جدول زمان‌بندی بر حسب ماه باشد، تاریخ قطعی نساز. هزینه‌ها را عددسازی نکن.
- مشخصات هویتی، شماره دانشجویی، نام استاد، تاریخ تصویب و امضا را فقط از ورودی بگیر؛ موارد نامعلوم خالی بمانند.
- بخش پایش آزاد را فقط در حد اطلاعات قابل استنتاج پیشنهاد بده و باقی را نیازمند تکمیل توسط دانشجو بنویس.
- خروجی پیش‌نویس است و پیش از ثبت باید دانشجو و استاد راهنما بازبینی کنند.
ساختار JSON:
{{
"title_fa":"","title_en":"","research_type":"","language":"فارسی","main_question":"",
"problem_statement":"","significance":"","literature_review":"","novelty":"",
"keywords_fa":"","keywords_en":"","objectives":"","beneficiaries":"",
"research_questions":"","hypotheses":"","definitions":"","method_type":"",
"data_collection":"","instruments":"","analysis_method":"","population_sample":"",
"inclusion_exclusion":"","free_pajesh":"","limitations":"","ethical_notes":"",
"timeline":[{{"stage":"","start_month":"","end_month":""}}],
"variables":[{{"name":"","role":"","type":"","measurement":"","scale":""}}]
}}
"""
    progress("منابع پیدا شد؛ در حال تدوین پروپوزال با مدل انتخاب‌شده…")
    from utils.provider_config import get_provider, is_openai_compatible
    provider = get_provider()
    model = os.environ.get("SHZ_LLM_MODEL", "").strip()
    if not model:
        raise ValueError("مدل هوش مصنوعی تنظیم نشده است.")
    if provider == "gemini":
        from utils.gemini_utils import call_gemini_with_text_prompt
        response = call_gemini_with_text_prompt(prompt, model, result_parsing_func=lambda x: x,
            check_parsed_response_not_none=False, max_retries=2, generation_configs={"temperature": 0.25})
    elif is_openai_compatible(provider):
        from utils.openai_utils import call_openai_models_with_text_prompt
        response = call_openai_models_with_text_prompt(prompt, model, result_parsing_func=lambda x: x,
            check_parsed_response_not_none=False, max_retries=2, generation_configs={"temperature": 0.25})
    else:
        raise ValueError("ارائه‌دهنده برای تولید پروپوزال پشتیبانی نمی‌شود.")
    raw = response.get("raw_response", "") if isinstance(response, dict) else str(response)
    payload = _parse_json(raw)
    progress("در حال آماده‌سازی خروجی و فهرست منابع…")
    keys = [
        "title_fa","title_en","research_type","language","main_question","problem_statement",
        "significance","literature_review","novelty","keywords_fa","keywords_en","objectives",
        "beneficiaries","research_questions","hypotheses","definitions","method_type",
        "data_collection","instruments","analysis_method","population_sample",
        "inclusion_exclusion","free_pajesh","limitations","ethical_notes"
    ]
    result = {key: _text(payload.get(key)) for key in keys}
    result.update(metadata)
    result["timeline"] = payload.get("timeline", [])
    result["variables"] = payload.get("variables", [])
    result["references"] = sources
    result["budget_note"] = "هزینه‌ها و منابع تأمین بودجه باید بر اساس برآورد واقعی دانشجو تکمیل شود."
    result["admin_note"] = "اطلاعات هویتی و اداری نامعلوم، امضاها، تاریخ تصویب، شماره بایگانی و تأییدها خالی گذاشته شده‌اند."
    return result, sources
