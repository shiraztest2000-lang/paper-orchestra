import os,sys
from contextlib import redirect_stdout,redirect_stderr
def root_dir(): return getattr(sys,"_MEIPASS",os.path.dirname(os.path.abspath(__file__)))
def worker():
 p=os.environ.get("SHZ_PAPERORCHESTRA_LOG"); stream=open(p,"a",encoding="utf-8",buffering=1) if p else sys.stdout
 try:
  with redirect_stdout(stream),redirect_stderr(stream):
   sys.path.insert(0,root_dir()); import paper_writing_cli
   sys.argv=["paper_writing_cli.py"]+sys.argv[2:]; paper_writing_cli.main()
  return 0
 except SystemExit as e: return int(e.code or 0)
 except Exception:
  import traceback; traceback.print_exc(file=stream); return 1
 finally:
  if stream is not sys.stdout: stream.close()
if __name__=="__main__" and len(sys.argv)>1 and sys.argv[1]=="--worker": raise SystemExit(worker())
from PySide6.QtCore import QProcess,QTimer,Qt,QProcessEnvironment
from PySide6.QtGui import QFont
from PySide6.QtWidgets import *
APP="SHZ PaperOrchestra"
def data_dir():
 p=os.path.join(os.environ.get("APPDATA",os.path.expanduser("~")),APP); os.makedirs(p,exist_ok=True); return p
class Settings(QDialog):
 def __init__(self,parent=None):
  super().__init__(parent); self.setWindowTitle("تنظیم کلیدهای API"); self.fields={}; form=QFormLayout()
  for k,n in [("GEMINI_API_KEY","Gemini"),("OPENAI_API_KEY","OpenAI"),("SEMANTIC_SCHOLAR_API_KEY","Semantic Scholar"),("VERTEX_AI_PROJECT","Vertex project"),("VERTEX_AI_LOCATION","Vertex location")]:
   e=QLineEdit(os.environ.get(k,""))
   if "KEY" in k:e.setEchoMode(QLineEdit.EchoMode.Password)
   self.fields[k]=e; form.addRow(n,e)
  b=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel); b.accepted.connect(self.save); b.rejected.connect(self.reject)
  l=QVBoxLayout(self); l.addLayout(form); l.addWidget(QLabel("کلیدها فقط در پروفایل محلی ویندوز ذخیره می‌شوند.")); l.addWidget(b)
 def save(self):
  with open(os.path.join(data_dir(),".env"),"w",encoding="utf-8") as f:
   for k,e in self.fields.items():
    v=e.text().strip(); f.write(k+"="+v+"\n")
    if v:os.environ[k]=v
    else:os.environ.pop(k,None)
  self.accept()
class Window(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle(APP); self.resize(1080,760); self.proc=None; self.log_path=None; self.offset=0
  ep=os.path.join(data_dir(),".env")
  if os.path.isfile(ep):
   from dotenv import load_dotenv; load_dotenv(ep,override=True)
  w=QWidget(); v=QVBoxLayout(w); h=QHBoxLayout(); t=QLabel(APP); t.setStyleSheet("font-size:22px;font-weight:bold;color:#214b91")
  h.addWidget(t); h.addStretch(); h.addWidget(QLabel("سامانه هوشمند پژوهش و نگارش مقاله")); v.addLayout(h)
  tabs=QTabWidget(); p=QWidget(); pv=QVBoxLayout(p); g=QGroupBox("مشخصات پروژه"); f=QGridLayout(g)
  self.name=QLineEdit("پژوهش جدید"); self.template=QComboBox(); self.template.addItems(self.templates())
  self.model=QComboBox(); self.model.setEditable(True); self.model.addItems(["gemini-3.1-pro-preview","gemini-3-flash-preview","gpt-5"])
  self.cutoff=QLineEdit(); self.cutoff.setPlaceholderText("2026-11"); self.plot=QCheckBox("فعال‌سازی عامل تولید شکل و نمودار"); self.plot.setChecked(True)
  for args in [(QLabel("نام پروژه"),0,0),(self.name,0,1),(QLabel("قالب"),0,2),(self.template,0,3),(QLabel("مدل"),1,0),(self.model,1,1),(QLabel("تاریخ قطع منابع"),1,2),(self.cutoff,1,3),(self.plot,2,1)]: f.addWidget(*args)
  pv.addWidget(g); row=QHBoxLayout(); a=QGroupBox("ایده پژوهش"); al=QVBoxLayout(a); self.idea=QPlainTextEdit(); self.idea.setPlaceholderText("ایده، مسئله، پرسش و نوآوری پژوهش…"); al.addWidget(self.idea)
  b=QGroupBox("گزارش آزمایش"); bl=QVBoxLayout(b); self.notes=QPlainTextEdit(); self.notes.setPlaceholderText("روش، داده‌ها، نتایج و مشاهدات…"); bl.addWidget(self.notes); row.addWidget(a); row.addWidget(b); pv.addLayout(row,1)
  buttons=QHBoxLayout(); s=QPushButton("کلیدهای API"); s.clicked.connect(lambda:Settings(self).exec())
  self.go=QPushButton("شروع تولید مقاله"); self.go.clicked.connect(self.start); self.stop=QPushButton("توقف"); self.stop.setEnabled(False); self.stop.clicked.connect(self.cancel)
  buttons.addWidget(s); buttons.addStretch(); buttons.addWidget(self.stop); buttons.addWidget(self.go); pv.addLayout(buttons); tabs.addTab(p,"پروژه جدید")
  q=QWidget(); qv=QVBoxLayout(q); self.status=QLabel("آماده"); self.bar=QProgressBar(); self.bar.setRange(0,5); self.output=QPlainTextEdit(); self.output.setReadOnly(True)
  self.open=QPushButton("باز کردن پوشه خروجی"); self.open.setEnabled(False); self.open.clicked.connect(lambda:os.startfile(self.run_dir) if self.run_dir else None)
  qv.addWidget(self.status); qv.addWidget(self.bar); qv.addWidget(self.output,1); qv.addWidget(self.open); tabs.addTab(q,"گزارش اجرا"); v.addWidget(tabs); self.setCentralWidget(w); self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
  self.setStyleSheet("QMainWindow,QWidget{background:#f4f6fa;color:#172033;font-size:10pt} QLineEdit,QPlainTextEdit,QComboBox{background:white;border:1px solid #ccd4e0;border-radius:6px;padding:6px} QGroupBox{border:1px solid #ccd4e0;border-radius:8px;margin-top:10px;padding:10px} QPushButton{padding:9px;background:#e4eaf3;border-radius:6px}")
  self.timer=QTimer(self); self.timer.setInterval(700); self.timer.timeout.connect(self.poll)
 def templates(self):
  p=os.path.join(root_dir(),"templates")
  return sorted(x for x in os.listdir(p) if os.path.isfile(os.path.join(p,x,"template.tex"))) if os.path.isdir(p) else ["cvpr2025","iclr2025"]
 def start(self):
  idea=self.idea.toPlainText().strip(); notes=self.notes.toPlainText().strip()
  if not self.name.text().strip() or not idea or not notes: QMessageBox.warning(self,"اطلاعات ناقص","نام پروژه، ایده و گزارش آزمایش لازم است."); return
  ep=os.path.join(data_dir(),".env")
  if os.path.isfile(ep):
   from dotenv import load_dotenv; load_dotenv(ep,override=True)
  if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("VERTEX_AI_PROJECT")): QMessageBox.warning(self,"Gemini لازم است","عامل مرور منابع از ابزار جست‌وجوی Google استفاده می‌کند؛ کلید Gemini یا تنظیمات Vertex AI را وارد کنید."); return
  model_name=self.model.currentText().strip().lower()
  if any(tag in model_name for tag in ["gpt","o1","o3"]) and not os.environ.get("OPENAI_API_KEY"): QMessageBox.warning(self,"OpenAI لازم است","برای مدل انتخاب‌شده، OPENAI_API_KEY را نیز وارد کنید."); return
  from datetime import datetime
  safe="".join(c if c.isalnum() or c in "-_ " else "_" for c in self.name.text()).strip().replace(" ","_")
  base=os.path.join(os.path.expanduser("~"),"Documents",APP,"Projects"); os.makedirs(base,exist_ok=True)
  self.run_dir=os.path.join(base,safe+"_"+datetime.now().strftime("%Y%m%d_%H%M%S")); raw=os.path.join(self.run_dir,"raw_materials"); os.makedirs(os.path.join(raw,"figures"),exist_ok=True)
  open(os.path.join(raw,"idea_sparse.md"),"w",encoding="utf-8").write(idea); open(os.path.join(raw,"experimental_log.md"),"w",encoding="utf-8").write(notes)
  self.log_path=os.path.join(self.run_dir,"desktop-run.log"); self.offset=0; self.output.clear(); self.bar.setValue(0)
  args=["--worker","--raw_materials_dir",raw,"--output_dir",self.run_dir,"--latex_template_dir",os.path.join(root_dir(),"templates",self.template.currentText()),"--writer_model_name",self.model.currentText(),"--reflection_model_name",self.model.currentText(),"--idea_filename","idea_sparse.md","--experimental_log_filename","experimental_log.md"]
  if self.cutoff.text().strip():args+=["--research_cutoff",self.cutoff.text().strip()]
  if self.plot.isChecked():args+=["--use_plotting","true","--plotting_model_name",self.model.currentText()]
  pe=QProcessEnvironment.systemEnvironment()
  for k,val in os.environ.items():pe.insert(k,val)
  pe.insert("SHZ_PAPERORCHESTRA_LOG",self.log_path); self.proc=QProcess(self); self.proc.setProgram(sys.executable);
  if not getattr(sys,"frozen",False): args.insert(0,os.path.abspath(__file__))
  self.proc.setArguments(args); self.proc.setWorkingDirectory(root_dir()); self.proc.setProcessEnvironment(pe); self.proc.finished.connect(self.finished); self.proc.start()
  if not self.proc.waitForStarted(5000):QMessageBox.critical(self,"خطا","اجرای موتور ناموفق بود."); self.proc=None; return
  self.go.setEnabled(False); self.stop.setEnabled(True); self.timer.start(); self.status.setText("در حال اجرا…")
 def poll(self):
  if not self.log_path or not os.path.isfile(self.log_path):return
  with open(self.log_path,"r",encoding="utf-8",errors="replace") as f:f.seek(self.offset); chunk=f.read(); self.offset=f.tell()
  if chunk:
   self.output.moveCursor(self.output.textCursor().MoveOperation.End); self.output.insertPlainText(chunk)
   for mark,n,label in [("OutlineAgent",1,"طراحی ساختار"),("Starting Fast Hybrid Literature Agent",2,"مرور منابع"),("PlottingAgent",3,"تولید شکل"),("SectionWritingAgent",4,"نگارش بخش‌ها"),("ContentRefinementAgent",5,"بازبینی نهایی")]:
    if mark.lower() in chunk.lower():self.bar.setValue(max(n,self.bar.value())); self.status.setText(label)
 def finished(self,code,status):
  self.timer.stop(); self.poll(); self.go.setEnabled(True); self.stop.setEnabled(False); self.open.setEnabled(True); self.status.setText("پایان موفق" if code==0 else "پایان همراه خطا؛ گزارش را بررسی کنید."); self.proc=None
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
