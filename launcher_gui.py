"""
Medicerti Vision — GUI 런처
설치 후 바탕화면에서 이 파일 실행 → 제어판 창이 열리고 서버 자동 시작
"""
import tkinter as tk
import threading
import subprocess
import webbrowser
import urllib.request
import time
import sys
import os

PORT = 8111
BASE_URL = f"http://localhost:{PORT}"
DASHBOARD_URL = f"{BASE_URL}/dashboard"


def _server_path():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "medicerti-vision.exe")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "dist", "medicerti-vision.exe")


class MedicertiLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.server_proc = None
        self._setup_window()
        self._build_ui()
        self.root.after(200, self._start_server)   # 창 표시 후 시작

    # ── 창 기본 설정 ──────────────────────────────────────
    def _setup_window(self):
        self.root.title("Medicerti Vision")
        self.root.geometry("460x400")
        self.root.configure(bg="#020817")
        self.root.resizable(False, False)
        # 화면 중앙 배치
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"460x400+{(sw-460)//2}+{(sh-400)//2}")
        # 아이콘
        try:
            base = os.path.dirname(sys.executable if getattr(sys, "frozen", False)
                                   else os.path.abspath(__file__))
            ico = os.path.join(base, "brand", "icon.ico")
            if os.path.exists(ico):
                self.root.iconbitmap(ico)
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI 구성 ───────────────────────────────────────────
    def _build_ui(self):
        # 헤더
        hdr = tk.Frame(self.root, bg="#060f22", height=88)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        badge = tk.Label(hdr, text="✚", font=("Arial", 18, "bold"),
                         fg="white", bg="#0ea5e9", width=2, height=1)
        badge.place(x=22, y=26)

        tk.Label(hdr, text="Medicerti Vision",
                 font=("Malgun Gothic", 15, "bold"),
                 fg="#22d3ee", bg="#060f22").place(x=70, y=20)
        tk.Label(hdr, text="Edge AI 환자 안전 모니터링 시스템",
                 font=("Malgun Gothic", 9),
                 fg="#445568", bg="#060f22").place(x=71, y=50)
        tk.Label(hdr, text=f"v0.1.0  ·  포트 {PORT}",
                 font=("Consolas", 8),
                 fg="#1e3050", bg="#060f22").place(x=370, y=70)

        # 상태 카드
        card = tk.Frame(self.root, bg="#0a1632", bd=0)
        card.pack(fill="x", padx=20, pady=(14, 0))

        status_row = tk.Frame(card, bg="#0a1632")
        status_row.pack(fill="x", padx=14, pady=12)

        self.dot = tk.Label(status_row, text="●", font=("Arial", 14),
                            fg="#fbbf24", bg="#0a1632")
        self.dot.pack(side="left")

        self.status = tk.Label(status_row, text="  서버 시작 중…",
                               font=("Malgun Gothic", 10), fg="#8baac9", bg="#0a1632")
        self.status.pack(side="left")

        self.pid_lbl = tk.Label(status_row, text="",
                                font=("Consolas", 8), fg="#1e3050", bg="#0a1632")
        self.pid_lbl.pack(side="right")

        # 버튼
        btn_row = tk.Frame(self.root, bg="#020817")
        btn_row.pack(fill="x", padx=20, pady=12)

        self.open_btn = tk.Button(
            btn_row, text="🌐  대시보드 열기",
            font=("Malgun Gothic", 10, "bold"),
            fg="#020817", bg="#22d3ee",
            activeforeground="#020817", activebackground="#67e8f9",
            relief="flat", bd=0, pady=11,
            cursor="hand2", state="disabled",
            command=self._open_dashboard)
        self.open_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.stop_btn = tk.Button(
            btn_row, text="⏹  서비스 중지",
            font=("Malgun Gothic", 10),
            fg="#8baac9", bg="#0a1632",
            activeforeground="#e2eeff", activebackground="#1a2645",
            relief="flat", bd=0, pady=11,
            cursor="hand2",
            command=self._stop_server)
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # 구분선
        tk.Frame(self.root, bg="#0a1428", height=1).pack(fill="x", padx=20, pady=(0, 8))

        # 로그
        tk.Label(self.root, text="시스템 로그",
                 font=("Malgun Gothic", 8), fg="#2a3e55", bg="#020817").pack(anchor="w", padx=24)

        log_wrap = tk.Frame(self.root, bg="#060f22")
        log_wrap.pack(fill="both", expand=True, padx=20, pady=(4, 0))

        sb = tk.Scrollbar(log_wrap)
        sb.pack(side="right", fill="y")

        self.log = tk.Text(
            log_wrap, font=("Consolas", 8),
            bg="#060f22", fg="#2a5070",
            insertbackground="#22d3ee",
            relief="flat", bd=0, padx=10, pady=8,
            state="disabled", wrap="word",
            yscrollcommand=sb.set)
        self.log.pack(fill="both", expand=True)
        sb.config(command=self.log.yview)

        # 푸터
        tk.Label(self.root, text="On-Premise · No Cloud · 환자 데이터 외부 전송 없음",
                 font=("Malgun Gothic", 7), fg="#0d1e35", bg="#020817").pack(pady=8)

    # ── 로그 출력 ─────────────────────────────────────────
    def _log(self, msg):
        def _do():
            self.log.config(state="normal")
            ts = time.strftime("%H:%M:%S")
            self.log.insert("end", f"[{ts}] {msg}\n")
            self.log.see("end")
            self.log.config(state="disabled")
        self.root.after(0, _do)

    def _set_status(self, text, fg, dot):
        def _do():
            self.status.config(text=f"  {text}", fg=fg)
            self.dot.config(fg=dot)
        self.root.after(0, _do)

    # ── 서버 시작 ─────────────────────────────────────────
    def _start_server(self):
        exe = _server_path()
        if not os.path.exists(exe):
            self._log(f"[오류] 서버 파일 없음: {exe}")
            self._set_status("서버 파일을 찾을 수 없습니다", "#f87171", "#f87171")
            return

        self._log(f"[시작] {os.path.basename(exe)} 실행 중…")
        try:
            self.server_proc = subprocess.Popen(
                [exe, "--no-pipeline"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._log(f"[정보] PID {self.server_proc.pid} · 포트 {PORT} 응답 대기 중…")
            self.root.after(0, lambda: self.pid_lbl.config(text=f"PID {self.server_proc.pid}"))
        except Exception as e:
            self._log(f"[오류] {e}")
            self._set_status("서버 실행 실패", "#f87171", "#f87171")
            return

        threading.Thread(target=self._wait_ready, daemon=True).start()

    def _wait_ready(self):
        for _ in range(50):   # 최대 40초 대기
            time.sleep(0.8)
            if self.server_proc and self.server_proc.poll() is not None:
                self._set_status("서버가 예기치 않게 종료됨", "#f87171", "#f87171")
                self._log("[오류] 서버 프로세스가 종료되었습니다.")
                return
            try:
                urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
                self.root.after(0, self._on_ready)
                return
            except Exception:
                pass
        self._set_status("시작 시간 초과 (40초)", "#fb923c", "#fb923c")
        self._log("[경고] 서버가 시간 내에 응답하지 않았습니다.")

    def _on_ready(self):
        self._set_status("정상 운행 중", "#4ade80", "#4ade80")
        self.open_btn.config(state="normal")
        self._log(f"[완료] 서버 준비 완료 → {DASHBOARD_URL}")
        webbrowser.open(DASHBOARD_URL)   # 자동으로 브라우저 열기

    # ── 버튼 동작 ─────────────────────────────────────────
    def _open_dashboard(self):
        webbrowser.open(DASHBOARD_URL)

    def _stop_server(self):
        if self.server_proc:
            try:
                self.server_proc.terminate()
            except Exception:
                pass
            self.server_proc = None
        self._set_status("서비스 중지됨", "#445568", "#1e3050")
        self.open_btn.config(state="disabled")
        self._log("[중지] 서비스가 중지되었습니다.")
        self.pid_lbl.config(text="")

    def _on_close(self):
        self._stop_server()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MedicertiLauncher().run()
