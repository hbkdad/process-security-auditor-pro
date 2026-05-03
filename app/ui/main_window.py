import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading, time, json, csv, os, webbrowser, pyperclip
try:
    import pyperclip
except Exception:
    pyperclip = None

from app.core.config import APP_NAME, APP_VERSION, SCAN_INTERVAL_SECONDS
from app.services.scanner import scan_processes
from app.services.license_manager import load_license, save_license, validate_license
from app.services import updater

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x760")
        self.configure(bg="#0b1220")
        self.rows=[]
        self.scanning=False
        self.scan_thread=None
        self.license=load_license()
        self._build_style()
        self._build_ui()

    def _build_style(self):
        style=ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background="#111827", foreground="#e5e7eb", fieldbackground="#111827", rowheight=28)
        style.configure("Treeview.Heading", background="#1f2937", foreground="#93c5fd", font=("Segoe UI",10,"bold"))
        style.configure("TButton", padding=8)
        style.configure("TLabel", background="#0b1220", foreground="#e5e7eb")
        style.configure("TNotebook", background="#0b1220")
        style.configure("TNotebook.Tab", padding=[12,6])

    def _build_ui(self):
        top=tk.Frame(self,bg="#0b1220"); top.pack(fill="x", padx=12, pady=8)
        tk.Label(top,text="Process Security Auditor AV Pro",bg="#0b1220",fg="#38bdf8",font=("Segoe UI",18,"bold")).pack(side="left")
        self.license_lbl=tk.Label(top,text=f"Tier: {self.license.get('tier','lite').upper()}",bg="#0b1220",fg="#a7f3d0")
        self.license_lbl.pack(side="right")

        toolbar=tk.Frame(self,bg="#0b1220"); toolbar.pack(fill="x", padx=12)
        ttk.Button(toolbar,text="Start Live Protection",command=self.start_scan).pack(side="left", padx=4)
        ttk.Button(toolbar,text="Stop",command=self.stop_scan).pack(side="left", padx=4)
        ttk.Button(toolbar,text="Manual Scan",command=self.manual_scan).pack(side="left", padx=4)
        ttk.Button(toolbar,text="Export JSON",command=self.export_json).pack(side="left", padx=4)
        ttk.Button(toolbar,text="Export CSV",command=self.export_csv).pack(side="left", padx=4)
        ttk.Button(toolbar,text="Check Updates",command=self.check_updates).pack(side="left", padx=4)

        self.search=tk.StringVar()
        tk.Entry(toolbar,textvariable=self.search,bg="#111827",fg="#e5e7eb",insertbackground="#e5e7eb",width=38).pack(side="right", padx=4)
        ttk.Button(toolbar,text="Filter",command=self.refresh_table).pack(side="right", padx=4)

        cards= tk.Frame(self,bg="#0b1220"); cards.pack(fill="x", padx=12, pady=8)
        self.summary=tk.Label(cards,text="Ready. Click Manual Scan or Start Live Protection.",bg="#111827",fg="#e5e7eb",anchor="w",padx=12,pady=10)
        self.summary.pack(fill="x")

        nb=ttk.Notebook(self); nb.pack(fill="both",expand=True,padx=12,pady=8)
        tab1=tk.Frame(nb,bg="#0b1220"); tab2=tk.Frame(nb,bg="#0b1220"); tab3=tk.Frame(nb,bg="#0b1220")
        nb.add(tab1,text="Processes"); nb.add(tab2,text="License"); nb.add(tab3,text="Roadmap")

        cols=("verdict","score","pid","name","path","parent","user","hash")
        self.tree=ttk.Treeview(tab1,columns=cols,show="headings")
        for c in cols:
            self.tree.heading(c,text=c.upper(),command=lambda col=c:self.sort_by(col))
            self.tree.column(c,width=120 if c!="path" else 360)
        self.tree.pack(fill="both",expand=True)
        self.tree.bind("<Button-3>", self.context_menu)
        self.tree.bind("<Double-1>", self.show_details)

        self.menu=tk.Menu(self,tearoff=0)
        self.menu.add_command(label="Copy Row JSON",command=self.copy_row_json)
        self.menu.add_command(label="Copy Hash",command=lambda:self.copy_field("hash"))
        self.menu.add_command(label="Copy Path",command=lambda:self.copy_field("path"))
        self.menu.add_command(label="Open File Location",command=self.open_location)
        self.menu.add_command(label="Open VirusTotal",command=self.open_vt)

        tk.Label(tab2,text="Paste license key:",bg="#0b1220",fg="#e5e7eb").pack(anchor="w",padx=12,pady=8)
        self.license_text=tk.Text(tab2,height=6,bg="#111827",fg="#e5e7eb")
        self.license_text.pack(fill="x",padx=12)
        ttk.Button(tab2,text="Save License",command=self.save_license_ui).pack(anchor="w",padx=12,pady=8)

        roadmap="""Next antivirus-level upgrades:
- YARA rules engine
- Windows service background agent
- signed update channel
- rollback updater
- cloud business dashboard
- tamper-resistant logs
- scheduled scans
- ransomware canary-file detector
- USB/device monitoring
- email/webhook alerts
"""
        tk.Label(tab3,text=roadmap,bg="#0b1220",fg="#e5e7eb",justify="left",font=("Consolas",11)).pack(anchor="nw",padx=12,pady=12)

    def start_scan(self):
        if not self.license.get("features",{}).get("live_monitor"):
            messagebox.showinfo("Pro required","Live protection is a Pro feature.")
            return
        if self.scanning: return
        self.scanning=True
        self.scan_thread=threading.Thread(target=self.loop_scan,daemon=True)
        self.scan_thread.start()

    def stop_scan(self):
        self.scanning=False
        self.summary.config(text="Live scan stopped.")

    def loop_scan(self):
        while self.scanning:
            self.rows=scan_processes()
            self.after(0,self.refresh_table)
            time.sleep(SCAN_INTERVAL_SECONDS)

    def manual_scan(self):
        self.summary.config(text="Scanning...")
        def run():
            self.rows=scan_processes()
            self.after(0,self.refresh_table)
        threading.Thread(target=run,daemon=True).start()

    def refresh_table(self):
        q=self.search.get().lower().strip()
        for x in self.tree.get_children(): self.tree.delete(x)
        counts={"Safe":0,"Unknown":0,"Suspicious":0,"Malicious":0}
        for r in self.rows:
            counts[r.get("verdict","Unknown")] = counts.get(r.get("verdict","Unknown"),0)+1
            blob=json.dumps(r).lower()
            if q and q not in blob: continue
            vals=(r["verdict"],r["risk_score"],r["pid"],r["name"],r["path"],r["parent_name"],r["user"],r["hash"][:16])
            item=self.tree.insert("", "end", values=vals)
            if r["verdict"]=="Malicious": self.tree.item(item,tags=("bad",))
            elif r["verdict"]=="Suspicious": self.tree.item(item,tags=("warn",))
        self.tree.tag_configure("bad", background="#4c0519")
        self.tree.tag_configure("warn", background="#422006")
        self.summary.config(text=f"Safe: {counts.get('Safe',0)} | Unknown: {counts.get('Unknown',0)} | Suspicious: {counts.get('Suspicious',0)} | Malicious: {counts.get('Malicious',0)} | Total: {len(self.rows)}")

    def selected_row(self):
        sel=self.tree.selection()
        if not sel: return None
        pid=self.tree.item(sel[0])["values"][2]
        for r in self.rows:
            if str(r["pid"])==str(pid): return r
        return None

    def context_menu(self,event):
        iid=self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.menu.tk_popup(event.x_root,event.y_root)

    def show_details(self,event=None):
        r=self.selected_row()
        if r: messagebox.showinfo("Process Details", json.dumps(r,indent=2))

    def copy_text(self,text):
        if pyperclip: pyperclip.copy(text)
        else:
            self.clipboard_clear(); self.clipboard_append(text)

    def copy_row_json(self):
        r=self.selected_row()
        if r: self.copy_text(json.dumps(r,indent=2))

    def copy_field(self,f):
        r=self.selected_row()
        if r: self.copy_text(str(r.get(f,"")))

    def open_location(self):
        r=self.selected_row()
        if r and r.get("path"):
            os.startfile(os.path.dirname(r["path"]))

    def open_vt(self):
        r=self.selected_row()
        if r and r.get("hash"):
            webbrowser.open(f"https://www.virustotal.com/gui/file/{r['hash']}")

    def export_json(self):
        p=filedialog.asksaveasfilename(defaultextension=".json")
        if p: open(p,"w",encoding="utf-8").write(json.dumps(self.rows,indent=2))

    def export_csv(self):
        p=filedialog.asksaveasfilename(defaultextension=".csv")
        if not p: return
        keys=["verdict","risk_score","pid","name","path","parent_name","user","hash","cmdline","network"]
        with open(p,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
            for r in self.rows: w.writerow({k:r.get(k,"") for k in keys})

    def sort_by(self,col):
        idx={"verdict":0,"score":1,"pid":2,"name":3,"path":4,"parent":5,"user":6,"hash":7}[col]
        data=[(self.tree.set(k,col),k) for k in self.tree.get_children("")]
        data.sort(reverse=False)
        for i,(_,k) in enumerate(data): self.tree.move(k,"",i)

    def save_license_ui(self):
        key=self.license_text.get("1.0","end").strip()
        res=validate_license(key)
        if res["valid"]:
            save_license(key); self.license=res
            self.license_lbl.config(text=f"Tier: {res.get('tier','lite').upper()}")
            messagebox.showinfo("License","License activated.")
        else:
            messagebox.showerror("License",f"Invalid license: {res.get('reason')}")

    def check_updates(self):
        def run():
            try:
                info=updater.check_latest()
                if updater.update_available(info):
                    if messagebox.askyesno("Update Available",f"Version {info['latest']} is available. Download now?"):
                        path=updater.download_update(info["download_url"])
                        messagebox.showinfo("Downloaded",f"Downloaded to {path}. Launching now.")
                        updater.launch_downloaded_update(path)
                else:
                    messagebox.showinfo("Updates","You are up to date.")
            except Exception as e:
                messagebox.showerror("Update error",str(e))
        threading.Thread(target=run,daemon=True).start()
