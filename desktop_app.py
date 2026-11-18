import os,sys
from contextlib import redirect_stdout,redirect_stderr
def root_dir(): return getattr(sys,"_MEIPASS",os.path.dirname(os.path.abspath(__file__)))
def worker():
 p=os.environ.get("SHZ_PAPERORCHESTRA_LOG"); stream=open(p,"a",encoding="utf-8",buffering=1) if p else sys.stdout
 try:
  with redirect_stdout(stream),redirect_stderr(stream):
   print("SHZ_PROGRESS:STARTUP",flush=True)
   sys.path.insert(0,root_dir()); import paper_writing_cli
   sys.argv=["paper_writing_cli.py"]+sys.argv[2:]; paper_writing_cli.main()
  return 0
 except SystemExit as e: return int(e.code or 0)
 except Exception:
  import traceback; traceback.print_exc(file=stream); return 1
 finally:
  if stream is not sys.stdout: stream.close()
if __name__=="__main__" and len(sys.argv)>1 and sys.argv[1]=="--worker": raise SystemExit(worker())
from PySide6.QtCore import QProcess,QTimer,Qt,QProcessEnvironment,QThread,Signal
from PySide6.QtGui import QFont, QDesktopServices, QPdfWriter, QTextDocument, QPageSize
from PySide6.QtCore import QUrl, QMarginsF
from PySide6.QtWidgets import *
APP="SHZ PaperOrchestra"
def data_dir():
 p=os.path.join(os.environ.get("APPDATA",os.path.expanduser("~")),APP); os.makedirs(p,exist_ok=True); return p
class Settings(QDialog):
 PROVIDERS={
  "gemini":{"name":"Google Gemini","url":"https://aistudio.google.com/app/apikey","key":"GEMINI_API_KEY","free":"Google AI Studio برای برخی مدل‌ها سهمیه رایگان دارد. سهمیه و دسترسی به کشور و شرایط حساب وابسته است."},
  "openrouter":{"name":"OpenRouter Free","url":"https://openrouter.ai/keys","key":"OPENROUTER_API_KEY","free":"حالت رایگان OpenRouter بدون خرید اعتبار و بدون کارت بانکی قابل شروع است. از مدل openrouter/free استفاده می‌کنیم؛ سقف رایگان فعلی ۵۰ درخواست در روز است و ممکن است ظرفیت مدل‌ها تغییر کند."},
  "groq":{"name":"Groq","url":"https://console.groq.com/keys","key":"GROQ_API_KEY","free":"Groq ممکن است برای حساب‌های واجد شرایط سهمیه رایگان محدود ارائه کند."},
  "cerebras":{"name":"Cerebras","url":"https://cloud.cerebras.ai/platform","key":"CEREBRAS_API_KEY","free":"شرایط دسترسی و سهمیه رایگان را در پنل رسمی Cerebras بررسی کنید."},
  "deepseek":{"name":"DeepSeek","url":"https://platform.deepseek.com/api_keys","key":"DEEPSEEK_API_KEY","free":"قبل از استفاده، قیمت و اعتبار حساب را در پنل رسمی بررسی کنید؛ رایگان بودن تضمین‌شده نیست."},
  "together":{"name":"Together AI","url":"https://api.together.ai/settings/api-keys","key":"TOGETHER_API_KEY","free":"اعتبار آزمایشی یا سهمیه رایگان ممکن است به شرایط حساب وابسته باشد."},
  "openai":{"name":"OpenAI","url":"https://platform.openai.com/api-keys","key":"OPENAI_API_KEY","free":"استفاده از API معمولاً هزینه دارد و اشتراک ChatGPT به‌معنی اعتبار API نیست."},
  "openai-compatible":{"name":"سرویس ابری سفارشی","url":"","key":"SHZ_LLM_API_KEY","free":"نشانی HTTPS و کلید را فقط از ارائه‌دهنده سرویس خود دریافت کنید."},
 }
 DEFAULT_MODELS={"gemini":"gemini-2.5-flash-lite","openrouter":"openrouter/free","groq":"","cerebras":"","deepseek":"","together":"","openai":"","openai-compatible":""}
 def __init__(self,parent=None):
  super().__init__(parent); self.setWindowTitle("راهنمای راه‌اندازی اتصال هوش مصنوعی"); self.resize(650,500); self.step=0; self.tested=False; self.discovered=[]
  self.stack=QStackedWidget(); root=QVBoxLayout(self)
  self.heading=QLabel(); self.heading.setStyleSheet("font-size:18px;font-weight:bold;color:#214b91")
  self.progress=QLabel(); self.progress.setStyleSheet("color:#53647d")
  root.addWidget(self.heading); root.addWidget(self.progress); root.addWidget(self.stack,1)
  # Step 1: choose a provider.
  page=QWidget(); lay=QVBoxLayout(page)
  lay.addWidget(QLabel("برای اتصال مستقیم، یک سرویس ابری انتخاب کنید. هیچ مدل یا سرور محلی نصب نمی‌شود و برنامه به سرور اختصاصی SHZ متصل نخواهد شد."))
  self.provider=QComboBox()
  for key,item in self.PROVIDERS.items(): self.provider.addItem(item["name"],key)
  current=os.environ.get("SHZ_LLM_PROVIDER","gemini"); idx=self.provider.findData(current)
  if idx>=0:self.provider.setCurrentIndex(idx)
  self.mode_group=QButtonGroup(self)
  self.standard_mode=QRadioButton("گزینه ۱ ـ اتصال به سرویس هوش مصنوعی (ممکن است پولی باشد)")
  self.free_mode=QRadioButton("گزینه ۲ ـ هوش مصنوعی رایگان OpenRouter (نیازمند حساب و کلید API)")
  self.no_account_mode=QRadioButton("گزینه ۳ ـ جستجوی علمی کاملاً رایگان، بدون ثبت‌نام و بدون کلید API")
  for button in (self.standard_mode,self.free_mode,self.no_account_mode): self.mode_group.addButton(button); lay.addWidget(button)
  saved_no_account=os.environ.get("SHZ_NO_ACCOUNT_MODE","").strip().lower() in {"1","true","yes","on"}
  saved_free=os.environ.get("SHZ_FREE_MODE","").strip().lower() in {"1","true","yes","on"}
  (self.no_account_mode if saved_no_account else self.free_mode if saved_free else self.standard_mode).setChecked(True)
  lay.addWidget(QLabel("در گزینهٔ سوم، جست‌وجو در پایگاه‌های علمی مستقیماً و بدون حساب کاربری انجام می‌شود. این گزینه برای کشف مقاله و دریافت اطلاعات کتاب‌شناختی است؛ تولید متن با هوش مصنوعی در آن فعال نیست."))
  self.free_note=QLabel("در این حالت فقط OpenRouter Free و مدل openrouter/free فعال است. برای ساخت کلید API باید حساب رایگان بسازید؛ اطلاعات کارت بانکی وارد نکنید. سهمیه محدود است و پس از اتمام آن، برنامه متوقف می‌شود و به مدل پولی تغییر مسیر نمی‌دهد.")
  self.free_note.setWordWrap(True); lay.addWidget(self.free_note)
  lay.addWidget(self.provider)
  lay.addWidget(QLabel("در گزینهٔ اول، رایگان بودن سایر سرویس‌دهنده‌ها تضمین نمی‌شود."))
  self.stack.addWidget(page)
  # Step 2: account registration.
  page=QWidget(); lay=QVBoxLayout(page)
  lay.addWidget(QLabel("مرحله ۲ ـ ساخت حساب و دریافت کلید"))
  self.account_info=QLabel(); self.account_info.setWordWrap(True); lay.addWidget(self.account_info)
  self.open_account=QPushButton("باز کردن صفحه رسمی ثبت‌نام / دریافت کلید در مرورگر")
  self.open_account.clicked.connect(self.open_provider_page); lay.addWidget(self.open_account)
  lay.addWidget(QLabel("در صفحه رسمی سرویس‌دهنده وارد حساب شوید، بخش API Keys را باز کنید و یک کلید جدید بسازید. سپس به این برنامه برگردید. رمز حساب یا اطلاعات ورودتان را در برنامه وارد نکنید."))
  lay.addStretch(); self.stack.addWidget(page)
  # Step 3: enter key and model.
  page=QWidget(); lay=QFormLayout(page)
  self.key_label=QLabel("کلید API"); self.api_key=QLineEdit(); self.api_key.setEchoMode(QLineEdit.EchoMode.Password); self.api_key.setPlaceholderText("کلید را اینجا وارد کنید")
  self.reveal=QCheckBox("نمایش کلید"); self.reveal.toggled.connect(lambda on:self.api_key.setEchoMode(QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
  keybox=QVBoxLayout(); keybox.addWidget(self.api_key); keybox.addWidget(self.reveal)
  keywrap=QWidget(); keywrap.setLayout(keybox); lay.addRow(self.key_label,keywrap)
  self.endpoint=QLineEdit(); self.endpoint.setPlaceholderText("https://api.example.com/v1"); lay.addRow("نشانی API سفارشی",self.endpoint)
  self.endpoint_label=QLabel("فقط برای سرویس سفارشی لازم است."); lay.addRow("",self.endpoint_label)
  self.model=QComboBox(); self.model.setEditable(True); self.model.addItems(["gemini-2.5-flash-lite","openrouter/free"]); lay.addRow("مدل هوش مصنوعی",self.model)
  lay.addRow("",QLabel("نام مدل را می‌توانید دستی وارد کنید. برای ارائه‌دهنده‌های سازگار، در مرحله بعد فهرست مدل‌ها دریافت می‌شود."))
  self.stack.addWidget(page)
  # Step 4: verify and save.
  page=QWidget(); lay=QVBoxLayout(page)
  lay.addWidget(QLabel("مرحله ۴ ـ آزمایش اتصال و ثبت تنظیمات"))
  lay.addWidget(QLabel("برنامه کلید را با API رسمی سرویس‌دهنده آزمایش می‌کند. در صورت موفقیت، مدل‌های در دسترس نمایش داده می‌شوند و سپس می‌توانید تنظیمات را ذخیره کنید."))
  self.test_result=QLabel("هنوز اتصالی آزمایش نشده است."); self.test_result.setWordWrap(True); lay.addWidget(self.test_result)
  self.test_button=QPushButton("آزمایش اتصال و دریافت مدل‌ها"); self.test_button.clicked.connect(self.test_connection); lay.addWidget(self.test_button)
  lay.addStretch(); self.stack.addWidget(page)
  nav=QHBoxLayout(); self.back=QPushButton("مرحله قبل"); self.next=QPushButton("مرحله بعد"); self.finish=QPushButton("ذخیره تنظیمات و پایان"); self.cancel=QPushButton("لغو")
  self.back.clicked.connect(self.previous_step); self.next.clicked.connect(self.next_step); self.finish.clicked.connect(self.save); self.cancel.clicked.connect(self.reject)
  nav.addWidget(self.back); nav.addStretch(); nav.addWidget(self.cancel); nav.addWidget(self.next); nav.addWidget(self.finish); root.addLayout(nav)
  self.provider.currentIndexChanged.connect(self.provider_changed)
  self.standard_mode.toggled.connect(self.apply_mode)
  self.free_mode.toggled.connect(self.apply_mode)
  self.no_account_mode.toggled.connect(self.apply_mode)
  self.api_key.textChanged.connect(self.invalidate_test); self.endpoint.textChanged.connect(self.invalidate_test); self.model.currentTextChanged.connect(self.invalidate_test)
  self._load_current(); self.apply_mode(); self.show_step(0)
 def apply_mode(self,*args):
  current=self.provider.currentData()
  if current and (current!="openrouter" or not hasattr(self,"_last_provider")): self._last_provider=current
  no_account=self.no_account_mode.isChecked()
  free=self.free_mode.isChecked()
  allowed={"openrouter"} if free else set(self.PROVIDERS)
  preferred="openrouter" if free else getattr(self,"_last_provider","gemini")
  self.provider.blockSignals(True); self.provider.clear()
  for key,item in self.PROVIDERS.items():
   if key in allowed:self.provider.addItem(item["name"],key)
  index=self.provider.findData(preferred)
  self.provider.setCurrentIndex(max(index,0)); self.provider.blockSignals(False)
  self.provider.setEnabled(not no_account and not free)
  self.free_note.setVisible(free)
  self.model.setEditable(not free)
  self.provider_changed()
  if free:self.model.setCurrentIndex(0)
  self.update_buttons()
 def _load_current(self):
  provider=self.provider.currentData(); item=self.PROVIDERS.get(provider,self.PROVIDERS["gemini"])
  self.api_key.setText(os.environ.get(item["key"],""))
  self.endpoint.setText(os.environ.get("SHZ_LLM_BASE_URL","") if provider=="openai-compatible" else "")
  self.model.setCurrentText(os.environ.get("SHZ_LLM_MODEL",self.DEFAULT_MODELS.get(provider,"")))
 def provider_changed(self):
  provider=self.provider.currentData(); item=self.PROVIDERS[provider]
  self.account_info.setText(f"سرویس انتخاب‌شده: {item['name']}\n\n{item['free']}\n\n۱) صفحه رسمی را باز کنید. ۲) حساب بسازید یا وارد شوید. ۳) از بخش API Keys کلید بسازید. ۴) کلید را کپی و در مرحله بعد وارد کنید.\n\nبرنامه رمز عبور حساب شما را نمی‌خواهد.")
  self.open_account.setVisible(bool(item["url"]))
  self.key_label.setText("کلید API حساب " + item["name"])
  custom=provider=="openai-compatible"; self.endpoint.setVisible(custom); self.endpoint_label.setVisible(custom)
  self.tested=False; self.test_result.setText("برای این سرویس هنوز اتصال آزمایش نشده است.")
  self.model.clear(); self.model.addItems([self.DEFAULT_MODELS.get(provider,"")])
  self.model.setEditable(not self.free_mode.isChecked())
  self._load_current(); self.update_buttons()
 def open_provider_page(self):
  url=self.PROVIDERS[self.provider.currentData()]["url"]
  if url:QDesktopServices.openUrl(QUrl(url))
 def show_step(self,n):
  self.step=n; self.stack.setCurrentIndex(n)
  names=["انتخاب سرویس‌دهنده","ثبت‌نام و دریافت کلید","وارد کردن کلید و مدل","آزمایش و ذخیره"]
  self.heading.setText(names[n]); self.progress.setText(f"گام {n+1} از ۴")
  self.update_buttons()
 def update_buttons(self):
  no_account=self.no_account_mode.isChecked()
  self.back.setEnabled(self.step>0 and not no_account)
  self.next.setVisible(self.step<3 and not no_account)
  self.finish.setVisible(self.step==3 or (self.step==0 and no_account))
  self.finish.setText("شروع جستجوی رایگان" if no_account else "ذخیره تنظیمات و پایان")
  self.finish.setEnabled((self.step==0 and no_account) or (self.step==3 and self.tested))
 def invalidate_test(self,*args):
  self.tested=False
  if self.step==3:self.test_result.setText("اطلاعات اتصال تغییر کرده است؛ دوباره آزمایش کنید.")
  self.update_buttons()
 def next_step(self):
  if self.step==2:
   provider=self.provider.currentData()
   if not self.api_key.text().strip():QMessageBox.warning(self,"کلید API لازم است","طبق راهنمای مرحله ۲ کلید API را دریافت و در این قسمت وارد کنید."); return
   if provider=="openai-compatible" and not self.endpoint.text().strip():QMessageBox.warning(self,"نشانی سرویس لازم است","نشانی HTTPS سرویس سفارشی را وارد کنید."); return
  if self.step<3:self.show_step(self.step+1)
 def previous_step(self):
  if self.step>0:self.show_step(self.step-1)
 def _apply_temporary(self):
  provider=self.provider.currentData(); item=self.PROVIDERS[provider]
  os.environ["SHZ_LLM_PROVIDER"]=provider
  os.environ["SHZ_FREE_MODE"]="true" if self.free_mode.isChecked() else "false"
  os.environ["SHZ_NO_ACCOUNT_MODE"]="false"
  # Keep credentials for other providers so users can switch without re-entering keys.
  os.environ[item["key"]]=self.api_key.text().strip()
  if provider=="openai-compatible":os.environ["SHZ_LLM_BASE_URL"]=self.endpoint.text().strip()
  else:os.environ.pop("SHZ_LLM_BASE_URL",None)
  os.environ["SHZ_LLM_MODEL"]=self.model.currentText().strip()
 def test_connection(self):
  self._apply_temporary(); self.test_button.setEnabled(False); self.test_result.setText("در حال ارتباط با سرویس‌دهنده…"); QApplication.processEvents()
  provider=self.provider.currentData()
  try:
   if self.free_mode.isChecked():
    from utils.provider_config import list_compatible_models
    discovered=list_compatible_models("openrouter")
    models=["openrouter/free"] + sorted(m for m in discovered if m.endswith(":free"))
    ok=True
    msg="اتصال به OpenRouter موفق بود؛ فقط مسیر مدل‌های رایگان در دسترس است."
   elif provider=="gemini":
    from utils.provider_config import test_gemini_connection
    ok,msg,models=test_gemini_connection()
   else:
    from utils.provider_config import list_compatible_models
    models=list_compatible_models(provider); ok=bool(models)
    msg=f"اتصال موفق بود؛ {len(models)} مدل از سرویس‌دهنده دریافت شد." if ok else "اتصال برقرار شد اما فهرست مدلی دریافت نشد."
   if ok:
    self.discovered=models
    current=self.model.currentText().strip()
    self.model.clear(); self.model.addItems(models)
    default="openrouter/free" if self.free_mode.isChecked() else self.DEFAULT_MODELS.get(provider,"")
    if self.free_mode.isChecked():
     self.model.setEditable(False)
     self.model.setCurrentText("openrouter/free")
    elif current=="openrouter/free" and provider=="openrouter":self.model.setCurrentText(current)
    elif current in models:self.model.setCurrentText(current)
    elif default in models:self.model.setCurrentText(default)
    elif models:self.model.setCurrentIndex(0)
    if not self.model.currentText().strip():ok=False; msg+=" نام مدل را وارد کنید."
   self.tested=ok; self.test_result.setText(("✓ " if ok else "✕ ")+msg)
   self.test_result.setStyleSheet("color:#18733b;font-weight:bold" if ok else "color:#a12b2b")
  except Exception as exc:
   self.tested=False; self.test_result.setText("✕ اتصال ناموفق بود.\n"+str(exc)); self.test_result.setStyleSheet("color:#a12b2b")
  finally:self.test_button.setEnabled(True); self.update_buttons()
 def save_no_account_mode(self):
  os.environ["SHZ_NO_ACCOUNT_MODE"]="true"
  os.environ["SHZ_FREE_MODE"]="false"
  os.environ["SHZ_SETUP_COMPLETED"]="true"
  keys=["SHZ_LLM_PROVIDER","SHZ_LLM_BASE_URL","SHZ_LLM_MODEL","SHZ_FREE_MODE","SHZ_NO_ACCOUNT_MODE","SHZ_SETUP_COMPLETED","VERTEX_AI_PROJECT","VERTEX_AI_LOCATION"]
  path=os.path.join(data_dir(),".env"); temporary=path+".tmp"
  try:
   with open(temporary,"w",encoding="utf-8",newline="\n") as f:
    for key in keys:
     value=os.environ.get(key,"").replace("\r","").replace("\n","")
     f.write(key+"="+value+"\n")
    f.flush(); os.fsync(f.fileno())
   os.replace(temporary,path)
   with open(path,"r",encoding="utf-8") as f: saved=f.read()
   if "SHZ_NO_ACCOUNT_MODE=true\n" not in saved or "SHZ_SETUP_COMPLETED=true\n" not in saved:
    raise OSError("حالت جستجوی بدون ثبت‌نام پس از ذخیره‌سازی قابل تأیید نیست.")
  except Exception as exc:
   try:
    if os.path.exists(temporary): os.remove(temporary)
   except OSError: pass
   QMessageBox.critical(self,"ذخیره تنظیمات ناموفق","حالت جستجوی رایگان ذخیره نشد؛ پنجره باز می‌ماند.\n"+str(exc)); return
  parent=self.parent()
  if parent and hasattr(parent,"activate_no_account_mode"): parent.activate_no_account_mode(False)
  QMessageBox.information(self,"حالت رایگان فعال شد","جستجوی مقالات علمی بدون ثبت‌نام، کلید API یا پرداخت فعال شد. تولید متن با هوش مصنوعی در این حالت غیرفعال است.")
  self.accept()
 def save(self):
  if self.no_account_mode.isChecked():
   self.save_no_account_mode(); return
  if not self.tested:
   QMessageBox.warning(self,"آزمایش لازم است","قبل از ذخیره، اتصال را با موفقیت آزمایش کنید."); return
  self._apply_temporary()
  os.environ["SHZ_SETUP_COMPLETED"]="true"
  from utils.secure_store import SECRET_ENV_KEYS, save_secure_secrets
  keys=["SHZ_LLM_PROVIDER","SHZ_LLM_BASE_URL","SHZ_LLM_MODEL","SHZ_FREE_MODE","SHZ_NO_ACCOUNT_MODE","SHZ_SETUP_COMPLETED","VERTEX_AI_PROJECT","VERTEX_AI_LOCATION"]
  path=os.path.join(data_dir(),".env")
  temporary=path+".tmp"
  try:
   save_secure_secrets({key:os.environ.get(key,"") for key in SECRET_ENV_KEYS})
   with open(temporary,"w",encoding="utf-8",newline="\n") as f:
    for key in keys:
     value=os.environ.get(key,"").replace("\r","").replace("\n","")
     f.write(key+"="+value+"\n")
    f.flush()
    os.fsync(f.fileno())
   os.replace(temporary,path)
   with open(path,"r",encoding="utf-8") as f:
    saved=f.read()
   if "SHZ_LLM_PROVIDER="+os.environ.get("SHZ_LLM_PROVIDER","")+"\n" not in saved:
    raise OSError("تنظیم سرویس‌دهنده پس از ذخیره‌سازی قابل تأیید نیست.")
   if "SHZ_LLM_MODEL="+os.environ.get("SHZ_LLM_MODEL","")+"\n" not in saved:
    raise OSError("تنظیم مدل پس از ذخیره‌سازی قابل تأیید نیست.")
  except Exception as exc:
   try:
    if os.path.exists(temporary): os.remove(temporary)
   except OSError: pass
   QMessageBox.critical(self,"ذخیره تنظیمات ناموفق",
    "تنظیمات کامل ذخیره نشد؛ پنجره باز می‌ماند.\nجزئیات: "+str(exc))
   return
  parent=self.parent()
  if parent and hasattr(parent,"model"): parent.model.setCurrentText(os.environ.get("SHZ_LLM_MODEL",""))
  QMessageBox.information(self,"ذخیره موفق",
   "تنظیمات و کلید API در محل امن ذخیره و تنظیمات اتصال بررسی شد.\nاکنون پنجره بسته می‌شود.")
  self.accept()

class LiteratureSearchWorker(QThread):
 results_ready=Signal(object,str)
 def __init__(self,query,cutoff,sources,limit=20):
  super().__init__(); self.query=query; self.cutoff=cutoff; self.sources=sources; self.limit=limit
 def run(self):
  try:
   from utils.literature_search import search_academic_candidates
   results=search_academic_candidates(self.query,self.cutoff,self.limit,self.sources)
   self.results_ready.emit(results,"")
  except Exception as exc:
   self.results_ready.emit([],"خطا در جستجوی منابع: "+str(exc))

class ProposalWorker(QThread):
 progress=Signal(str)
 results_ready=Signal(object,object,str)
 def __init__(self,topic,metadata,cutoff):
  super().__init__(); self.topic=topic; self.metadata=metadata; self.cutoff=cutoff
 def run(self):
  try:
   from utils.proposal_builder import generate_proposal
   data,sources=generate_proposal(self.topic,self.metadata,self.cutoff,20,self.progress.emit)
   self.results_ready.emit(data,sources,"")
  except Exception as exc:
   self.results_ready.emit(None,[],str(exc))

class Window(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle(APP); self.resize(1080,760); self.proc=None; self.log_path=None; self.offset=0
  ep=os.path.join(data_dir(),".env")
  from utils.secure_store import migrate_legacy_env, load_secure_secrets
  try:
   migrate_legacy_env(ep)
   if os.path.isfile(ep):
    from dotenv import load_dotenv; load_dotenv(ep,override=True)
   os.environ.update(load_secure_secrets())
  except Exception as exc:
   QMessageBox.warning(self,"ذخیره امن کلیدها", "خواندن مخزن امن ویندوز ناموفق بود. کلیدها بارگذاری نشدند.\\n"+str(exc))
  w=QWidget(); v=QVBoxLayout(w); h=QHBoxLayout(); t=QLabel(APP); t.setStyleSheet("font-size:22px;font-weight:bold;color:#214b91")
  h.addWidget(t); h.addStretch(); h.addWidget(QLabel("سامانه هوشمند پژوهش و نگارش مقاله")); v.addLayout(h)
  tabs=QTabWidget(); self.tabs=tabs; p=QWidget(); pv=QVBoxLayout(p); g=QGroupBox("مشخصات پروژه"); f=QGridLayout(g)
  self.name=QLineEdit("پژوهش جدید"); self.template=QComboBox(); self.template.addItems(self.templates())
  self.model=QComboBox(); self.model.setEditable(True); self.model.addItems(["gemini-2.5-flash-lite","openrouter/free","nvidia/nemotron-3-super-120b-a12b:free","gpt-oss-120b"]); self.model.setCurrentText(os.environ.get("SHZ_LLM_MODEL","gemini-2.5-flash-lite"))
  free_mode=os.environ.get("SHZ_FREE_MODE","").strip().lower() in {"1","true","yes","on"}
  if free_mode:
   self.model.clear(); self.model.addItem("openrouter/free"); self.model.setEditable(False)
  self.cutoff=QLineEdit(); self.cutoff.setPlaceholderText("2026-11"); self.plot=QCheckBox("فعال‌سازی عامل تولید شکل و نمودار (مصرف API بیشتر)"); self.plot.setChecked(False)
  self.plot.setEnabled(not free_mode)
  if free_mode:self.plot.setToolTip("در حالت کاملاً رایگان، تولید تصویر و نمودار با سرویس‌های غیررایگان غیرفعال است.")
  for args in [(QLabel("نام پروژه"),0,0),(self.name,0,1),(QLabel("قالب"),0,2),(self.template,0,3),(QLabel("مدل"),1,0),(self.model,1,1),(QLabel("تاریخ قطع منابع"),1,2),(self.cutoff,1,3),(self.plot,2,1)]: f.addWidget(*args)
  pv.addWidget(g); pv.addWidget(QLabel("حالت کم‌مصرف: تولید نمودار به‌صورت پیش‌فرض خاموش است تا درخواست‌های اضافی و هزینه API کاهش یابد.")); row=QHBoxLayout(); a=QGroupBox("ایده پژوهش"); al=QVBoxLayout(a); self.idea=QPlainTextEdit(); self.idea.setPlaceholderText("ایده، مسئله، پرسش و نوآوری پژوهش…"); al.addWidget(self.idea)
  b=QGroupBox("گزارش آزمایش (اختیاری)"); bl=QVBoxLayout(b); self.notes=QPlainTextEdit(); self.notes.setPlaceholderText("اگر آزمایش انجام داده‌اید، روش، داده‌ها، نتایج و مشاهدات را وارد کنید. اگر هنوز داده‌ای ندارید، این قسمت را خالی بگذارید؛ برنامه مقاله را بدون ادعای نتایج تجربی آماده می‌کند."); bl.addWidget(self.notes); row.addWidget(a); row.addWidget(b); pv.addLayout(row,1)
  buttons=QHBoxLayout(); s=QPushButton("راهنمای گام‌به‌گام اتصال هوش مصنوعی"); s.clicked.connect(self.open_setup_wizard)
  self.go=QPushButton("شروع تولید مقاله"); self.go.clicked.connect(self.start); self.stop=QPushButton("توقف"); self.stop.setEnabled(False); self.stop.clicked.connect(self.cancel)
  buttons.addWidget(s); buttons.addStretch(); buttons.addWidget(self.stop); buttons.addWidget(self.go); pv.addLayout(buttons); tabs.addTab(p,"پروژه جدید")
  # No-account scholarly search is available independently of any AI provider.
  research=QWidget(); rv=QVBoxLayout(research)
  rv.addWidget(QLabel("جستجوی مقالات علمی از پایگاه‌های عمومی؛ بدون ساخت حساب، بدون کلید API و بدون پرداخت."))
  rv.addWidget(QLabel("منابع: OpenAlex، Crossref، Europe PMC و arXiv. نتایج شامل اطلاعات کتاب‌شناختی و لینک منبع هستند؛ دسترسی به متن کامل به مجوز ناشر یا وضعیت دسترسی آزاد مقاله بستگی دارد."))
  search_row=QHBoxLayout(); self.literature_query=QLineEdit(); self.literature_query.setPlaceholderText("موضوع یا کلیدواژه پژوهش را وارد کنید…")
  self.literature_cutoff=QLineEdit(); self.literature_cutoff.setPlaceholderText("سال آخر، مثلاً 2026"); self.literature_cutoff.setMaximumWidth(130)
  self.literature_search_button=QPushButton("جستجوی رایگان")
  self.literature_search_button.clicked.connect(self.search_literature)
  search_row.addWidget(self.literature_query,1); search_row.addWidget(self.literature_cutoff); search_row.addWidget(self.literature_search_button); rv.addLayout(search_row)
  source_row=QHBoxLayout(); self.literature_sources={}
  for key,label in [("openalex","OpenAlex"),("crossref","Crossref"),("europepmc","Europe PMC / PubMed"),("arxiv","arXiv")]:
   check=QCheckBox(label); check.setChecked(True); self.literature_sources[key]=check; source_row.addWidget(check)
  source_row.addStretch(); rv.addLayout(source_row)
  self.literature_status=QLabel("آماده جستجو؛ نیازی به ثبت‌نام یا کلید API نیست."); rv.addWidget(self.literature_status)
  self.literature_results=QListWidget(); self.literature_results.itemDoubleClicked.connect(self.open_literature_result); rv.addWidget(self.literature_results,1)
  rv.addWidget(QLabel("برای بازکردن صفحه مقاله، روی نتیجه دوبار کلیک کنید."))
  tabs.addTab(research,"جستجوی مقالات رایگان")
  # Research proposal completion based on the uploaded Shiraz Azad form.
  proposal=QWidget(); proposal_outer=QVBoxLayout(proposal); proposal_scroll=QScrollArea(); proposal_scroll.setWidgetResizable(True)
  proposal_body=QWidget(); proposal_form=QVBoxLayout(proposal_body)
  proposal_form.addWidget(QLabel("موضوع پژوهش را وارد کنید؛ برنامه منابع علمی را جستجو می‌کند و پیش‌نویس بخش‌های فرم ۱۰ دانشگاه آزاد واحد شیراز را با ارجاع به منابع می‌سازد."))
  pf=QGridLayout()
  self.proposal_topic=QLineEdit(); self.proposal_topic.setPlaceholderText("موضوع یا عنوان اولیه پژوهش")
  self.proposal_field=QLineEdit(); self.proposal_field.setPlaceholderText("رشته تحصیلی")
  self.proposal_specialization=QLineEdit(); self.proposal_specialization.setPlaceholderText("گرایش")
  self.proposal_degree=QComboBox(); self.proposal_degree.addItems(["کارشناسی ارشد","دکتری تخصصی","دکتری حرفه‌ای"])
  self.proposal_student=QLineEdit(); self.proposal_student.setPlaceholderText("نام دانشجو (اختیاری)")
  self.proposal_student_number=QLineEdit(); self.proposal_student_number.setPlaceholderText("شماره دانشجویی (اختیاری)")
  self.proposal_college=QLineEdit(); self.proposal_college.setPlaceholderText("دانشکده")
  self.proposal_supervisor=QLineEdit(); self.proposal_supervisor.setPlaceholderText("استاد راهنما")
  self.proposal_advisor=QLineEdit(); self.proposal_advisor.setPlaceholderText("استاد مشاور")
  self.proposal_credits=QLineEdit(); self.proposal_credits.setPlaceholderText("تعداد واحد پایان‌نامه")
  self.proposal_method=QComboBox(); self.proposal_method.addItems(["پیشنهاد روش متناسب با موضوع","کمی","کیفی","آمیخته","مروری / کتابخانه‌ای","نظری"])
  self.proposal_population=QLineEdit(); self.proposal_population.setPlaceholderText("جامعه یا میدان پژوهش، در صورت مشخص بودن")
  self.proposal_cutoff=QLineEdit(); self.proposal_cutoff.setPlaceholderText("سال آخر منابع، مثلاً 2026")
  for label,widget,r,c in [
   ("موضوع پژوهش",self.proposal_topic,0,0),("رشته",self.proposal_field,1,0),("گرایش",self.proposal_specialization,1,1),
   ("مقطع",self.proposal_degree,2,0),("روش ترجیحی",self.proposal_method,2,1),
   ("جامعه/میدان پژوهش",self.proposal_population,3,0),("سال آخر منابع",self.proposal_cutoff,3,1)]:
   pf.addWidget(QLabel(label),r,c*2); pf.addWidget(widget,r,c*2+1)
  proposal_form.addLayout(pf)
  proposal_form.addWidget(QLabel("توضیحات تکمیلی: مسئله، متغیرها، محل اجرا، محدودیت‌ها یا اطلاعاتی که باید در تدوین لحاظ شوند"))
  self.proposal_context=QPlainTextEdit(); self.proposal_context.setMaximumHeight(110)
  self.proposal_context.setPlaceholderText("اطلاعات واقعی را وارد کنید. موارد نامعلوم حدس زده نمی‌شوند.")
  proposal_form.addWidget(self.proposal_context)
  proposal_buttons=QHBoxLayout()
  self.proposal_generate=QPushButton("جستجوی منابع و تکمیل پروپوزال")
  self.proposal_generate.clicked.connect(self.generate_proposal_clicked)
  self.proposal_approve=QPushButton("تأیید محتوای پروپوزال و آماده‌سازی خروجی"); self.proposal_approve.setEnabled(False); self.proposal_approve.clicked.connect(self.approve_proposal_for_export)
  self.proposal_export_docx=QPushButton("خروجی Word"); self.proposal_export_docx.setEnabled(False); self.proposal_export_docx.clicked.connect(self.export_proposal_word)
  self.proposal_export_pdf=QPushButton("خروجی PDF"); self.proposal_export_pdf.setEnabled(False); self.proposal_export_pdf.clicked.connect(self.export_proposal_pdf)
  self.proposal_export_md=QPushButton("خروجی Markdown"); self.proposal_export_md.setEnabled(False); self.proposal_export_md.clicked.connect(self.export_proposal_markdown)
  proposal_buttons.addWidget(self.proposal_generate); proposal_buttons.addWidget(self.proposal_approve); proposal_buttons.addWidget(self.proposal_export_docx); proposal_buttons.addWidget(self.proposal_export_pdf); proposal_buttons.addWidget(self.proposal_export_md)
  proposal_form.addLayout(proposal_buttons)
  self.proposal_status=QLabel("برای تولید پیش‌نویس، اتصال هوش مصنوعی را در گزینهٔ اول یا دوم راه‌اندازی کنید. جستجوی منابع از پایگاه‌های عمومی و بدون کلید API انجام می‌شود.")
  self.proposal_status.setWordWrap(True); proposal_form.addWidget(self.proposal_status)
  self.proposal_progress=QProgressBar(); self.proposal_progress.setRange(0,1); self.proposal_progress.setValue(0); proposal_form.addWidget(self.proposal_progress)
  self.proposal_preview=QPlainTextEdit(); self.proposal_preview.setReadOnly(True); self.proposal_preview.setPlaceholderText("پیش‌نمایش پروپوزال پس از تکمیل در این قسمت نمایش داده می‌شود.")
  proposal_form.addWidget(self.proposal_preview,1)
  proposal_scroll.setWidget(proposal_body); proposal_outer.addWidget(proposal_scroll)
  self.proposal_data=None; self.proposal_worker=None; self.proposal_approved=False
  tabs.addTab(proposal,"تکمیل پروپوزال")
  q=QWidget(); qv=QVBoxLayout(q); self.status=QLabel("آماده"); self.bar=QProgressBar(); self.bar.setRange(0,5); self.output=QPlainTextEdit(); self.output.setReadOnly(True)
  self.open=QPushButton("باز کردن پوشه خروجی"); self.open.setEnabled(False); self.open.clicked.connect(lambda:os.startfile(self.run_dir) if self.run_dir else None)
  qv.addWidget(self.status); qv.addWidget(self.bar); qv.addWidget(self.output,1); qv.addWidget(self.open); tabs.addTab(q,"گزارش اجرا"); v.addWidget(tabs); self.setCentralWidget(w); self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
  self.setStyleSheet("QMainWindow,QWidget{background:#f4f6fa;color:#172033;font-size:10pt} QLineEdit,QPlainTextEdit,QComboBox{background:white;border:1px solid #ccd4e0;border-radius:6px;padding:6px} QGroupBox{border:1px solid #ccd4e0;border-radius:8px;margin-top:10px;padding:10px} QPushButton{padding:9px;background:#e4eaf3;border-radius:6px}")
  self.timer=QTimer(self); self.timer.setInterval(500); self.timer.timeout.connect(self.poll)
  from utils.provider_config import validate_provider_config
  provider=os.environ.get("SHZ_LLM_PROVIDER","gemini")
  ready,_=validate_provider_config(provider)
  no_account=os.environ.get("SHZ_NO_ACCOUNT_MODE","").strip().lower() in {"1","true","yes","on"}
  setup_completed=os.environ.get("SHZ_SETUP_COMPLETED","").strip().lower() in {"1","true","yes","on"}
  if no_account:self.activate_no_account_mode()
  elif not setup_completed or not ready:QTimer.singleShot(350,self.open_setup_wizard)
 def open_setup_wizard(self):
  dialog=Settings(self)
  dialog.exec()
  self.go.setEnabled(True); self.go.setToolTip("")
  self.proposal_generate.setEnabled(True); self.proposal_generate.setToolTip("")
  no_account=os.environ.get("SHZ_NO_ACCOUNT_MODE","").strip().lower() in {"1","true","yes","on"}
  free_mode=os.environ.get("SHZ_FREE_MODE","").strip().lower() in {"1","true","yes","on"}
  if no_account:
   self.activate_no_account_mode()
  elif free_mode:
   self.model.clear(); self.model.addItem("openrouter/free"); self.model.setEditable(False)
   self.plot.setChecked(False); self.plot.setEnabled(False)
   self.plot.setToolTip("در حالت کاملاً رایگان، تولید تصویر و نمودار با سرویس‌های غیررایگان غیرفعال است.")
  else:
   self.model.setEditable(True)
   self.model.setCurrentText(os.environ.get("SHZ_LLM_MODEL",self.model.currentText()))
   self.plot.setEnabled(True)
 def activate_no_account_mode(self,switch_tab=True):
  os.environ["SHZ_NO_ACCOUNT_MODE"]="true"
  self.go.setEnabled(False)
  self.go.setToolTip("در گزینهٔ بدون ثبت‌نام، فقط جست‌وجو و گردآوری منابع علمی فعال است؛ برای نگارش با هوش مصنوعی باید گزینهٔ اتصال هوش مصنوعی را انتخاب کنید.")
  self.proposal_generate.setEnabled(False)
  self.proposal_generate.setToolTip("تولید متن پروپوزال به مدل هوش مصنوعی نیاز دارد؛ گزینهٔ اول یا دوم را انتخاب کنید.")
  self.proposal_status.setText("گزینهٔ سوم فعال است: جستجوی منابع رایگان و بدون ثبت‌نام در دسترس است؛ برای تکمیل خودکار پروپوزال، اتصال هوش مصنوعی را فعال کنید.")
  self.plot.setChecked(False); self.plot.setEnabled(False)
  self.literature_status.setText("حالت سوم فعال است: جست‌وجوی علمی بدون حساب، کلید API یا پرداخت. تولید متن با هوش مصنوعی غیرفعال است.")
  if switch_tab:self.tabs.setCurrentIndex(1)
 def show_literature_tab(self):
  self.tabs.setCurrentIndex(1)
 def search_literature(self):
  query=self.literature_query.text().strip()
  if not query:
   QMessageBox.information(self,"موضوع جستجو","ابتدا موضوع یا کلیدواژه مقاله را وارد کنید."); return
  sources=[key for key,check in self.literature_sources.items() if check.isChecked()]
  if not sources:
   QMessageBox.information(self,"انتخاب منبع","حداقل یک پایگاه علمی را انتخاب کنید."); return
  cutoff=self.literature_cutoff.text().strip() or None
  self.literature_results.clear()
  self.literature_search_button.setEnabled(False)
  self.literature_status.setText("در حال جستجو در پایگاه‌های انتخاب‌شده…")
  self.literature_worker=LiteratureSearchWorker(query,cutoff,sources,20)
  self.literature_worker.results_ready.connect(self.on_literature_results)
  self.literature_worker.start()
 def on_literature_results(self,results,error):
  self.literature_search_button.setEnabled(True)
  if error:
   self.literature_status.setText(error); return
  for paper in results:
   sources=", ".join(paper.get("sources",[]))
   item=QListWidgetItem(f"{paper.get('year','')} | {paper.get('title','')}  [{sources}]")
   item.setData(Qt.ItemDataRole.UserRole,paper.get("url",""))
   item.setToolTip(paper.get("reason",""))
   self.literature_results.addItem(item)
  self.literature_status.setText(f"{len(results)} نتیجه پیدا شد. نتایج تکراری بین پایگاه‌ها ادغام شده‌اند.")
 def open_literature_result(self,item):
  url=item.data(Qt.ItemDataRole.UserRole)
  if url: QDesktopServices.openUrl(QUrl(url))
 def generate_proposal_clicked(self):
  if os.environ.get("SHZ_NO_ACCOUNT_MODE","").strip().lower() in {"1","true","yes","on"}:
   QMessageBox.information(self,"نیاز به اتصال هوش مصنوعی","گزینهٔ سوم فقط جستجوی علمی بدون ثبت‌نام است و تولید متن هوش مصنوعی ندارد. برای تکمیل خودکار فرم، گزینهٔ اول یا دوم را در راه‌اندازی انتخاب کنید."); return
  topic=self.proposal_topic.text().strip()
  if not topic:
   QMessageBox.warning(self,"موضوع لازم است","موضوع پژوهش را وارد کنید."); return
  from utils.provider_config import validate_provider_config
  provider=os.environ.get("SHZ_LLM_PROVIDER","gemini")
  valid,message=validate_provider_config(provider)
  if not valid:
   QMessageBox.warning(self,"تنظیمات اتصال",message+"\nابتدا اتصال هوش مصنوعی را از راهنمای راه‌اندازی تنظیم کنید."); return
  metadata={
   "degree":self.proposal_degree.currentText(),"field":self.proposal_field.text().strip(),
   "specialization":self.proposal_specialization.text().strip(),"student":self.proposal_student.text().strip(),
   "student_number":self.proposal_student_number.text().strip(),"college":self.proposal_college.text().strip(),
   "supervisor":self.proposal_supervisor.text().strip(),"advisor":self.proposal_advisor.text().strip(),
   "credits":self.proposal_credits.text().strip(),"preferred_method":self.proposal_method.currentText(),
   "population_hint":self.proposal_population.text().strip(),"additional_context":self.proposal_context.toPlainText().strip(),
  }
  self.proposal_generate.setEnabled(False); self.proposal_approve.setEnabled(False); self.proposal_export_docx.setEnabled(False); self.proposal_export_pdf.setEnabled(False); self.proposal_export_md.setEnabled(False); self.proposal_approved=False
  self.proposal_progress.setRange(0,0); self.proposal_status.setText("در حال شروع جستجو و تدوین…"); self.proposal_preview.clear()
  self.proposal_worker=ProposalWorker(topic,metadata,self.proposal_cutoff.text().strip() or None)
  self.proposal_worker.progress.connect(self.proposal_status.setText)
  self.proposal_worker.results_ready.connect(self.on_proposal_ready)
  self.proposal_worker.start()
 def on_proposal_ready(self,data,sources,error):
  self.proposal_progress.setRange(0,1); self.proposal_progress.setValue(1); self.proposal_generate.setEnabled(True)
  if error:
   self.proposal_status.setText("تکمیل پروپوزال ناموفق بود: "+error); return
  self.proposal_data=data
  from utils.proposal_export import proposal_markdown
  self.proposal_preview.setPlainText(proposal_markdown(data))
  self.proposal_status.setText(f"پیش‌نویس آماده شد؛ {len(sources)} رکورد منبع بازیابی شد. ابتدا متن را بررسی کنید؛ خروجی گرفتن فقط پس از تأیید شما فعال می‌شود.")
  self.proposal_approve.setEnabled(True)
 def approve_proposal_for_export(self):
  if not self.proposal_data:return
  answer=QMessageBox.question(self,"تأیید پروپوزال","آیا محتوای علمی پروپوزال را تأیید می‌کنید؟\n\nپس از تأیید، می‌توانید مشخصات فردی و اداری را برای درج در فایل وارد کنید یا همه آن‌ها را خالی بگذارید تا پس از چاپ تکمیل شوند.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.Yes)
  if answer!=QMessageBox.StandardButton.Yes:return
  details={}
  fill=QMessageBox.question(self,"مشخصات نسخه چاپی","آیا می‌خواهید مشخصات فردی و اداری (نام، شماره دانشجویی، استادان، دانشکده، سال و تاریخ و...) را اکنون وارد کنید؟\n\nاگر «خیر» را بزنید، این قسمت‌ها در فایل خروجی کاملاً خالی می‌مانند.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
  if fill==QMessageBox.StandardButton.Yes:
   dialog=QDialog(self); dialog.setWindowTitle("مشخصات اختیاری نسخه چاپی"); dialog.resize(460,420)
   form=QFormLayout(dialog); fields={}
   for key,label in [("student","نام و نام خانوادگی دانشجو"),("student_number","شماره دانشجویی"),("college","دانشکده"),("supervisor","نام استاد راهنما"),("advisor","نام استاد مشاور"),("credits","تعداد واحد پایان‌نامه"),("academic_year","سال تحصیلی"),("submission_date","تاریخ تکمیل / چاپ")]:
    field=QLineEdit(); field.setText(str(self.proposal_data.get(key,"") or "")); fields[key]=field; form.addRow(label,field)
   note=QLabel("تمام این موارد اختیاری‌اند. می‌توانید بعضی فیلدها را خالی بگذارید. محل امضا، مهر و تأیید دانشگاه همیشه خالی می‌ماند.")
   note.setWordWrap(True); form.addRow(note)
   buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
   if dialog.exec()!=QDialog.DialogCode.Accepted:return
   details={key:field.text().strip() for key,field in fields.items()}
  else:
   details={key:"" for key in ["student","student_number","college","supervisor","advisor","credits","academic_year","submission_date"]}
  self.proposal_data.update(details); self.proposal_approved=True
  self.proposal_preview.setPlainText(__import__("utils.proposal_export",fromlist=["proposal_markdown"]).proposal_markdown(self.proposal_data))
  self.proposal_approve.setEnabled(False)
  self.proposal_export_docx.setEnabled(True); self.proposal_export_pdf.setEnabled(True); self.proposal_export_md.setEnabled(True)
  self.proposal_status.setText("پروپوزال تأیید شد؛ خروجی‌ها فعال شدند. مشخصات انتخاب‌شده درج شده و بخش‌های امضا و تأیید اداری خالی می‌مانند.")
 def export_proposal_word(self):
  if not self.proposal_data:return
  path,_=QFileDialog.getSaveFileName(self,"ذخیره پروپوزال Word","پروپوزال.docx","Word (*.docx)")
  if not path:return
  if not path.lower().endswith(".docx"):path+=".docx"
  try:
   from utils.proposal_export import export_proposal_docx
   export_proposal_docx(self.proposal_data,path)
   self.proposal_status.setText("فایل Word ذخیره شد: "+path)
  except Exception as exc:QMessageBox.critical(self,"خطا در خروجی Word",str(exc))
 def export_proposal_pdf(self):
  if not self.proposal_data:return
  path,_=QFileDialog.getSaveFileName(self,"ذخیره پروپوزال PDF","پروپوزال.pdf","PDF (*.pdf)")
  if not path:return
  if not path.lower().endswith(".pdf"):path+=".pdf"
  try:
   from utils.proposal_export import proposal_html
   writer=QPdfWriter(path); writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4)); writer.setResolution(96)
   from PySide6.QtGui import QTextDocument
   doc=QTextDocument(); doc.setDefaultFont(QFont("Arial",10)); doc.setHtml(proposal_html(self.proposal_data)); doc.print_(writer)
   self.proposal_status.setText("فایل PDF ذخیره شد: "+path)
  except Exception as exc:QMessageBox.critical(self,"خطا در خروجی PDF",str(exc))
 def export_proposal_markdown(self):
  if not self.proposal_data:return
  path,_=QFileDialog.getSaveFileName(self,"ذخیره پروپوزال Markdown","پروپوزال.md","Markdown (*.md)")
  if not path:return
  if not path.lower().endswith(".md"):path+=".md"
  try:
   from utils.proposal_export import proposal_markdown
   with open(path,"w",encoding="utf-8") as f:f.write(proposal_markdown(self.proposal_data))
   self.proposal_status.setText("فایل Markdown ذخیره شد: "+path)
  except Exception as exc:QMessageBox.critical(self,"خطا در خروجی Markdown",str(exc))
 def templates(self):
  p=os.path.join(root_dir(),"templates")
  return sorted(x for x in os.listdir(p) if os.path.isfile(os.path.join(p,x,"template.tex"))) if os.path.isdir(p) else ["cvpr2025","iclr2025"]
 def start(self):
  if os.environ.get("SHZ_NO_ACCOUNT_MODE","").strip().lower() in {"1","true","yes","on"}:
   QMessageBox.information(self,"حالت جستجوی بدون ثبت‌نام","در گزینهٔ سوم، جست‌وجو و گردآوری منابع علمی رایگان است؛ تولید مقاله با هوش مصنوعی نیازمند انتخاب یکی از دو حالت اتصال هوش مصنوعی است."); return
  project_title=self.name.text().strip(); idea=self.idea.toPlainText().strip(); notes=self.notes.toPlainText().strip()
  idea_was_generated = not bool(idea)
  if not project_title: QMessageBox.warning(self,"نام پروژه لازم است","ابتدا نام پروژه را وارد کنید."); return
  if not idea:
   idea=(
    "عنوان اولیه پژوهش: "+project_title+"\\n\\n"
    "دستور تدوین ایده پژوهش بر اساس عنوان:\\n"
    "با تکیه بر عنوان بالا، مسئله پژوهش، اهمیت و ضرورت مطالعه، شکاف پژوهشی قابل بررسی، "
    "هدف کلی، اهداف اختصاصی، پرسش‌های پژوهش و در صورت پشتیبانی شواهد، فرضیه‌های قابل آزمون را "
    "به‌صورت علمی و منسجم صورت‌بندی کن. موضوع، جامعه، متغیرها و دامنه مطالعه را فقط تا حدی "
    "استنباط کن که عنوان اجازه می‌دهد؛ هر مورد مبهم را به‌عنوان فرض اولیه یا نیازمند تأیید مشخص کن. "
    "هیچ داده، نتیجه، نمونه، روش اجراشده یا یافته‌ای را جعل نکن. اگر اطلاعات کافی برای تعیین "
    "روش‌شناسی وجود ندارد، چند گزینه روش‌شناختی مناسب را با ذکر پیش‌فرض‌ها پیشنهاد بده. "
    "مقاله را متناسب با ماهیت واقعی کار (مروری، نظری، پروپوزال یا تجربی) طراحی کن و میان "
    "پیشنهاد پژوهش و نتایج حاصل از پژوهش انجام‌شده تمایز روشن بگذار.\\n\\n"
    "توجه: این ایده به‌صورت خودکار و صرفاً از عنوان پروژه ساخته شده و باید در مراحل پژوهش "
    "با شواهد علمی و اطلاعات واقعی تکمیل و راستی‌آزمایی شود."
   )
   self.idea.setPlainText(idea)
  ep=os.path.join(data_dir(),".env")
  if os.path.isfile(ep):
   from dotenv import load_dotenv; load_dotenv(ep,override=True)
  from utils.provider_config import validate_provider_config
  provider=os.environ.get("SHZ_LLM_PROVIDER","gemini")
  valid,message=validate_provider_config(provider)
  if not valid: QMessageBox.warning(self,"تنظیمات ارائه‌دهنده",message); return
  model_name=self.model.currentText().strip()
  if not model_name: QMessageBox.warning(self,"مدل مشخص نشده","نام مدل را انتخاب یا وارد کنید."); return
  os.environ["SHZ_LLM_MODEL"]=model_name
  from datetime import datetime
  safe="".join(c if c.isalnum() or c in "-_ " else "_" for c in self.name.text()).strip().replace(" ","_")
  base=os.path.join(os.path.expanduser("~"),"Documents",APP,"Projects"); os.makedirs(base,exist_ok=True)
  self.run_dir=os.path.join(base,safe+"_"+datetime.now().strftime("%Y%m%d_%H%M%S")); raw=os.path.join(self.run_dir,"raw_materials"); os.makedirs(os.path.join(raw,"figures"),exist_ok=True)
  open(os.path.join(raw,"idea_sparse.md"),"w",encoding="utf-8").write(idea)
  if not notes:
   notes=("No experimental data, methods, or results have been provided at this stage. "
          "Treat this as a proposal, conceptual, or literature-review paper as appropriate. "
          "Do not invent experiments, measurements, datasets, statistical results, or empirical findings. "
          "Clearly distinguish proposed future work from completed research.")
  open(os.path.join(raw,"experimental_log.md"),"w",encoding="utf-8").write(notes)
  self.log_path=os.path.join(self.run_dir,"desktop-run.log"); self.offset=0; self.output.clear(); self.bar.setValue(0)
  args=["--worker","--raw_materials_dir",raw,"--output_dir",self.run_dir,"--latex_template_dir",os.path.join(root_dir(),"templates",self.template.currentText()),"--writer_model_name",self.model.currentText(),"--reflection_model_name",self.model.currentText(),"--idea_filename","idea_sparse.md","--experimental_log_filename","experimental_log.md"]
  if self.cutoff.text().strip():args+=["--research_cutoff",self.cutoff.text().strip()]
  if self.plot.isChecked():args+=["--use_plotting","true","--plotting_model_name",self.model.currentText()]
  pe=QProcessEnvironment.systemEnvironment()
  for k,val in os.environ.items():pe.insert(k,val)
  pe.insert("SHZ_PAPERORCHESTRA_LOG",self.log_path); self.proc=QProcess(self); self.proc.setProgram(sys.executable);
  if not getattr(sys,"frozen",False): args.insert(0,os.path.abspath(__file__))
  self.proc.setArguments(args); self.proc.setWorkingDirectory(root_dir()); self.proc.setProcessEnvironment(pe); self.proc.started.connect(self.process_started); self.proc.finished.connect(self.finished); self.proc.errorOccurred.connect(self.process_error)
  self.status.setText("در حال راه‌اندازی موتور پژوهش…"); self.bar.setRange(0,5); self.bar.setValue(0)
  self.output.appendPlainText("درخواست تولید ثبت شد؛ در حال راه‌اندازی فرایند مستقل پژوهش…")
  if idea_was_generated:
   self.output.appendPlainText("ایده پژوهش خالی بود؛ یک چارچوب اولیه بر اساس نام پروژه ساخته و در فایل ایده ذخیره شد.")
  self.tabs.setCurrentIndex(3)
  self.go.setEnabled(False); self.stop.setEnabled(True); self.timer.start(); self.proc.start()
 def poll(self):
  if not self.log_path:return
  if not os.path.isfile(self.log_path):
   if self.proc and self.proc.state()!=QProcess.ProcessState.NotRunning:self.status.setText("موتور فعال است؛ در حال آماده‌سازی گزارش اجرا…")
   return
  with open(self.log_path,"r",encoding="utf-8",errors="replace") as f:f.seek(self.offset); chunk=f.read(); self.offset=f.tell()
  if chunk:
   self.output.moveCursor(self.output.textCursor().MoveOperation.End); self.output.insertPlainText(chunk)
   stages=[("SHZ_PROGRESS:OUTLINE",1,"عامل طراحی ساختار مقاله"),("SHZ_PROGRESS:LITERATURE",2,"عامل جست‌وجو و مرور منابع"),("SHZ_PROGRESS:PLOTTING",3,"عامل تولید شکل‌ها و نمودارها"),("SHZ_PROGRESS:WRITING",4,"عامل نگارش بخش‌های مقاله"),("SHZ_PROGRESS:REFINEMENT",5,"عامل بازبینی و آماده‌سازی خروجی")]
   for mark,n,label in stages:
    if mark in chunk:self.bar.setValue(max(n,self.bar.value())); self.status.setText(label)
 def process_started(self):
  self.status.setText("موتور اجرا شد؛ در انتظار شروع مرحله اول…"); self.bar.setValue(1)
 def process_error(self,error):
  if self.proc:
   detail=self.proc.errorString(); self.status.setText("خطا در اجرای موتور"); self.output.appendPlainText("خطای فرایند: "+detail)
   if error==QProcess.ProcessError.FailedToStart:
    self.timer.stop(); self.go.setEnabled(True); self.stop.setEnabled(False); self.proc=None
 def finished(self,code,status):
  self.timer.stop(); self.poll(); self.go.setEnabled(True); self.stop.setEnabled(False); self.open.setEnabled(bool(self.run_dir and os.path.isdir(self.run_dir)))
  if code==0:
   self.bar.setValue(5); self.status.setText("تولید مقاله با موفقیت پایان یافت"); self.output.appendPlainText("\nفرایند با موفقیت پایان یافت.")
  else:
   self.status.setText("تولید مقاله با خطا متوقف شد؛ گزارش اجرا را بررسی کنید."); self.output.appendPlainText(f"\nفرایند با کد خروج {code} پایان یافت؛ جزئیات خطا در گزارش بالا آمده است.")
  self.proc=None
 def cancel(self):
  if self.proc and self.proc.state()!=QProcess.ProcessState.NotRunning:
   self.proc.terminate()
   if not self.proc.waitForFinished(4000):self.proc.kill()
  self.timer.stop(); self.go.setEnabled(True); self.stop.setEnabled(False); self.status.setText("اجرا متوقف شد؛ فایل‌های میانی حفظ شدند.")
 def closeEvent(self,event):
  if self.proc and self.proc.state()!=QProcess.ProcessState.NotRunning:
   if QMessageBox.question(self,"اجرا فعال است","فرایند متوقف و برنامه بسته شود؟")!=QMessageBox.StandardButton.Yes:event.ignore(); return
   self.cancel()
  event.accept()
def main():
 app=QApplication(sys.argv); app.setFont(QFont("Segoe UI",10)); win=Window(); win.show(); return app.exec()
if __name__=="__main__":raise SystemExit(main())
