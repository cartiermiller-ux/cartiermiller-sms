import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading
import time
import requests
import json

# ========== 内嵌 jm_client 底层接口 ==========
class JmSMSClient:
    def __init__(self, secret_key: str, base_url: str = "https://www.jm111.cc"):
        self.secret_key = secret_key
        self.base_url = base_url

    def _safe_request(self, url: str, params: dict) -> dict:
        """通用安全请求解析器，确保任何返回格式都能解析，不遗漏数据"""
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                raw_text = response.text.strip()
                try:
                    parsed_json = response.json()
                    return {"status": "success", "data": parsed_json, "raw": raw_text}
                except:
                    # 如果不是标准 JSON，返回原始纯文本
                    return {"status": "success", "data": raw_text, "raw": raw_text}
            return {"status": "error", "message": f"HTTP {response.status_code}", "raw": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e), "raw": ""}

    def get_number(self, country: str = "TH", pid: str = "2"):
        """获取号码接口"""
        url = f"{self.base_url}/api/getnumber"
        params = {
            "country": country,
            "pid": pid,
            "secret_key": self.secret_key,
        }
        return self._safe_request(url, params)

    def get_code(self, taskid: str):
        """获取验证码接口"""
        url = f"{self.base_url}/api/getcode"
        params = {"taskid": taskid, "secret_key": self.secret_key}
        return self._safe_request(url, params)

    def release_number(self, phone: str):
        """释放号码接口"""
        url = f"{self.base_url}/api/releasenumber"
        clean_phone = "".join(filter(str.isdigit, str(phone)))
        params = {"phone": clean_phone, "secret_key": self.secret_key}
        return self._safe_request(url, params)

    def get_pending_orders(self):
        """查询正进行的订单"""
        url = f"{self.base_url}/api/pendingorders"
        params = {"secret_key": self.secret_key}
        return self._safe_request(url, params)

    def get_successful_orders(self):
        """查询消费记录"""
        url = f"{self.base_url}/api/successfulorders"
        params = {"secret_key": self.secret_key}
        return self._safe_request(url, params)


# ========== GUI 主程序 ==========
class CartierMillerSmsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CartierandMiller 云接码 - 豪华优化版 v3.0")
        self.root.geometry("620x680")
        self.root.configure(bg="#f8f9fa")
        self.root.resizable(False, False)

        # 默认配置
        self.default_key = "ae96221a960ae51fcd91e23d1e906781"
        self.client = JmSMSClient(self.default_key)

        # 项目映射 (项目名 -> PID)
        self.PROJECTS = {
            "陌陌 (1.5 USDT)": "2",
            "Soul (1.8 USDT)": "3",
            "自定义项目 (手动输入 ID)": "custom"
        }

        # 运行状态
        self.current_taskid = ""
        self.current_phone = ""
        self.is_looping = False

        # 配色规范 (Sleek UI Palette)
        self.COLOR_PRIMARY = "#1a252f"     # 深邃蓝
        self.COLOR_SECONDARY = "#34495e"   # 蓝灰
        self.COLOR_ACCENT = "#3498db"      # 天空蓝
        self.COLOR_SUCCESS = "#2ecc71"     # 翡翠绿
        self.COLOR_RED = "#e74c3c"         # 番茄红
        self.COLOR_BG = "#f8f9fa"          # 浅灰底
        self.COLOR_CARD_BG = "#ffffff"     # 白色卡片
        self.COLOR_BORDER = "#e2e8f0"      # 边框灰

        self._init_styles()
        self._build_ui()

    def _init_styles(self):
        # 优化 ttk 控件外观
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # 统一下拉菜单样式
        self.style.configure("TCombobox", 
                             fieldbackground="white", 
                             background="#f1f5f9", 
                             foreground="#334155", 
                             bordercolor=self.COLOR_BORDER,
                             darkcolor=self.COLOR_BORDER, 
                             lightcolor=self.COLOR_BORDER)
        self.style.map("TCombobox", fieldbackground=[("readonly", "white")])

    def _safe_ui_update(self, widget, **kwargs):
        """线程安全的 UI 更新机制"""
        if widget.winfo_exists():
            self.root.after(0, lambda: widget.config(**kwargs))

    def _build_ui(self):
        # 1. 顶部艺术渐变栏
        header_frame = tk.Frame(self.root, bg=self.COLOR_PRIMARY, height=70)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="CartierandMiller", font=("Segoe UI", 16, "bold"), fg="#ffffff", bg=self.COLOR_PRIMARY)
        title_label.pack(side="left", padx=25, pady=10)
        
        subtitle_label = tk.Label(header_frame, text="云接码高级终端 v3.0", font=("Microsoft YaHei", 10), fg="#94a3b8", bg=self.COLOR_PRIMARY)
        subtitle_label.pack(side="left", pady=16)

        # 2. 状态信号灯
        self.signal_light = tk.Label(header_frame, text="● 系统就绪", font=("Microsoft YaHei", 9, "bold"), fg=self.COLOR_SUCCESS, bg=self.COLOR_PRIMARY, padx=15)
        self.signal_light.pack(side="right", padx=25)

        # 主滚动容器
        main_container = tk.Frame(self.root, bg=self.COLOR_BG)
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # ====== 卡片一：API 密钥配置 ======
        key_card = tk.LabelFrame(main_container, text="  API 授权配置  ", bg=self.COLOR_CARD_BG, fg=self.COLOR_SECONDARY, font=("Microsoft YaHei", 10, "bold"), bd=1, relief="solid")
        key_card.pack(fill="x", pady=8, ipady=5)
        
        self.key_input = tk.Entry(key_card, font=("Consolas", 11), bg="#f8fafc", fg="#1e293b", bd=1, relief="solid", highlightthickness=0)
        self.key_input.insert(0, self.default_key)
        self.key_input.pack(fill="x", padx=15, pady=10, ipady=6)

        # ====== 卡片二：任务控制中心 ======
        control_card = tk.LabelFrame(main_container, text="  控制台参数  ", bg=self.COLOR_CARD_BG, fg=self.COLOR_SECONDARY, font=("Microsoft YaHei", 10, "bold"), bd=1, relief="solid")
        control_card.pack(fill="x", pady=8)

        # 左侧核心输入区
        inputs_frame = tk.Frame(control_card, bg=self.COLOR_CARD_BG)
        inputs_frame.pack(side="left", fill="y", padx=15, pady=12)

        # 国家代码
        tk.Label(inputs_frame, text="国家代码:", font=("Microsoft YaHei", 9, "bold"), fg="#475569", bg=self.COLOR_CARD_BG).grid(row=0, column=0, sticky="w", pady=6)
        self.country_in = tk.Entry(inputs_frame, width=16, font=("Segoe UI", 10), bd=1, relief="solid")
        self.country_in.insert(0, "TH")
        self.country_in.grid(row=0, column=1, padx=10, sticky="w")

        # 项目选择
        tk.Label(inputs_frame, text="业务项目:", font=("Microsoft YaHei", 9, "bold"), fg="#475569", bg=self.COLOR_CARD_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.project_combo = ttk.Combobox(inputs_frame, values=list(self.PROJECTS.keys()), width=16, state="readonly")
        self.project_combo.current(0)
        self.project_combo.grid(row=1, column=1, padx=10, sticky="w")
        self.project_combo.bind("<<ComboboxSelected>>", self._on_project_changed)

        # 自定义 PID 输入（默认隐藏或禁用，当选择自定义时激活）
        tk.Label(inputs_frame, text="项目 PID:", font=("Microsoft YaHei", 9, "bold"), fg="#475569", bg=self.COLOR_CARD_BG).grid(row=2, column=0, sticky="w", pady=6)
        self.pid_in = tk.Entry(inputs_frame, width=16, font=("Segoe UI", 10), bd=1, relief="solid", state="disabled", bg="#f1f5f9")
        self.pid_in.insert(0, "2")
        self.pid_in.grid(row=2, column=1, padx=10, sticky="w")

        # 右侧快捷动作与申请按钮
        actions_frame = tk.Frame(control_card, bg=self.COLOR_CARD_BG)
        actions_frame.pack(side="right", fill="both", expand=True, padx=15, pady=12)

        # 两个小查询按钮
        query_grid = tk.Frame(actions_frame, bg=self.COLOR_CARD_BG)
        query_grid.pack(fill="x", pady=2)
        
        btn_active_order = tk.Button(query_grid, text="未完成订单", font=("Microsoft YaHei", 9), bg="#f1f5f9", fg="#334155", bd=1, relief="groove", cursor="hand2", command=self.check_order)
        btn_active_order.pack(side="left", fill="x", expand=True, padx=(0, 4), ipady=3)
        
        btn_history = tk.Button(query_grid, text="消费记录", font=("Microsoft YaHei", 9), bg="#f1f5f9", fg="#334155", bd=1, relief="groove", cursor="hand2", command=self.check_success_orders)
        btn_history.pack(side="right", fill="x", expand=True, padx=(4, 0), ipady=3)

        # 核心：申请新号码按钮
        self.btn_request_num = tk.Button(actions_frame, text="⚡ 申请新号码", font=("Microsoft YaHei", 10, "bold"), bg=self.COLOR_ACCENT, fg="#ffffff", activebackground="#2980b9", activeforeground="#ffffff", bd=0, cursor="hand2", command=self.get_num)
        self.btn_request_num.pack(fill="x", pady=6, ipady=8)

        # ====== 卡片三：号码看板 ======
        phone_card = tk.Frame(main_container, bg=self.COLOR_CARD_BG, bd=1, relief="solid")
        phone_card.pack(fill="x", pady=8, ipady=6)

        tk.Label(phone_card, text="当前手机号:", font=("Microsoft YaHei", 10, "bold"), fg=self.COLOR_SECONDARY, bg=self.COLOR_CARD_BG).pack(side="left", padx=15, pady=10)
        
        self.phone_show = tk.Entry(phone_card, font=("Consolas", 15, "bold"), fg=self.COLOR_ACCENT, bg="#f8fafc", bd=1, relief="solid", justify="center", width=16)
        self.phone_show.pack(side="left", padx=5)

        # 复制手机号按钮
        btn_copy_phone = tk.Button(phone_card, text="复制", font=("Microsoft YaHei", 9), bg="#f1f5f9", fg="#475569", bd=1, relief="groove", cursor="hand2", command=self.copy_phone)
        btn_copy_phone.pack(side="left", padx=5)

        # 释放按钮
        btn_release = tk.Button(phone_card, text="释放号码", font=("Microsoft YaHei", 9, "bold"), bg=self.COLOR_RED, fg="#ffffff", activebackground="#c0392b", activeforeground="#ffffff", bd=0, cursor="hand2", command=self.release_num)
        btn_release.pack(side="right", padx=15, ipady=3, ipadx=10)

        # ====== 卡片四：验证码大面板 ======
        code_card = tk.LabelFrame(main_container, text="  验证码监控中心  ", bg=self.COLOR_CARD_BG, fg=self.COLOR_SECONDARY, font=("Microsoft YaHei", 10, "bold"), bd=1, relief="solid")
        code_card.pack(fill="both", expand=True, pady=8)

        # 状态小字提示
        self.status_text = tk.Label(code_card, text="[系统就绪] 等待您申请号码...", font=("Microsoft YaHei", 9), fg="#64748b", bg=self.COLOR_CARD_BG, anchor="w", padx=15)
        self.status_text.pack(fill="x", pady=6)

        # 验证码巨幅大显示屏
        display_frame = tk.Frame(code_card, bg="#f1f5f9", bd=1, relief="solid")
        display_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.code_display = tk.Label(display_frame, text="--- WAIT ---", font=("Consolas", 32, "bold"), fg="#94a3b8", bg="#f1f5f9")
        self.code_display.pack(fill="both", expand=True, pady=15)

        # 底部控制：一键复制验证码
        self.btn_copy_code = tk.Button(display_frame, text="📋 一键复制验证码", font=("Microsoft YaHei", 9, "bold"), bg="#e2e8f0", fg="#334155", bd=0, cursor="hand2", command=self.copy_code, state="disabled")
        self.btn_copy_code.pack(fill="x", side="bottom")

    def _on_project_changed(self, event):
        """联动选择框，决定是否开放手动输入 PID"""
        selected = self.project_combo.get()
        if self.PROJECTS[selected] == "custom":
            self.pid_in.config(state="normal", bg="white")
            self.status_text.config(text="[提示] 已切换到自定义模式，请在下方手动输入所需项目 PID")
        else:
            self.pid_in.config(state="disabled", bg="#f1f5f9")
            self.pid_in.delete(0, tk.END)
            self.pid_in.insert(0, self.PROJECTS[selected])

    # 复制号码到剪贴板
    def copy_phone(self):
        num = self.phone_show.get().strip()
        if not num:
            self.status_text.config(text="⚠️ 复制失败：当前没有手机号", fg=self.COLOR_RED)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(num)
        self.status_text.config(text=f"📋 手机号 {num} 已成功复制到剪贴板！", fg="green")

    # 复制验证码到剪贴板
    def copy_code(self):
        code = self.code_display.cget("text").strip()
        if not code or code == "--- WAIT ---" or code == "TIMEOUT":
            self.status_text.config(text="⚠️ 复制失败：当前无可用验证码", fg=self.COLOR_RED)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.status_text.config(text=f"🎉 验证码 {code} 已成功复制到剪贴板！", fg="green")

    # 申请号码
    def get_num(self):
        key = self.key_input.get().strip()
        country = self.country_in.get().strip()
        
        # 获取最终使用的 PID
        selected_project = self.project_combo.get()
        if self.PROJECTS[selected_project] == "custom":
            pid = self.pid_in.get().strip()
        else:
            pid = self.PROJECTS[selected_project]

        if not key:
            messagebox.showwarning("密钥缺失", "API 密钥不能为空，请配置后再试！")
            return
        if not pid:
            messagebox.showwarning("参数不全", "项目 ID 不能为空，请输入对应的 PID！")
            return

        self.client = JmSMSClient(key)
        self._safe_ui_update(self.status_text, text="正在向云端提交号码申请...", fg=self.COLOR_ACCENT)
        self._safe_ui_update(self.signal_light, text="● 正在申请", fg=self.COLOR_ACCENT)
        self.btn_request_num.config(state="disabled")

        def task():
            res = self.client.get_number(country, pid)
            self.root.after(0, lambda: self._handle_getnum(res))
        threading.Thread(target=task, daemon=True).start()

    def _handle_getnum(self, res):
        self.btn_request_num.config(state="normal")
        if res.get("status") == "error":
            self._safe_ui_update(self.status_text, text=f"❌ 申请失败: {res.get('message')}", fg=self.COLOR_RED)
            self._safe_ui_update(self.signal_light, text="● 错误异常", fg=self.COLOR_RED)
            return

        data = res.get("data")
        raw = res.get("raw", "")

        # 格式解析
        if isinstance(data, dict):
            self.current_phone = str(data.get("phone", ""))
            self.current_taskid = str(data.get("taskid", ""))
        else:
            if "|" in raw:
                parts = raw.split("|")
                if len(parts) >= 3:
                    self.current_phone = parts[1]
                    self.current_taskid = parts[2]
                elif len(parts) == 2:
                    self.current_phone = parts[0]
                    self.current_taskid = parts[1]
            else:
                self.current_phone = raw
                self.current_taskid = "未知"

        # 检验合法性
        if not self.current_phone or "ERROR" in self.current_phone.upper() or self.current_phone == "None" or self.current_phone == "":
            err_msg = raw if raw else "无库存可用，或您的密钥余额不足。"
            self._safe_ui_update(self.status_text, text=f"❌ 平台反馈: {err_msg}", fg=self.COLOR_RED)
            self._safe_ui_update(self.signal_light, text="● 申请被拒", fg=self.COLOR_RED)
            messagebox.showwarning("分配号码失败", f"云端接码平台提示:\n{err_msg}")
            return

        # 更新界面
        self.phone_show.delete(0, tk.END)
        self.phone_show.insert(0, self.current_phone)
        self._safe_ui_update(self.status_text, text=f"✅ 获取号码成功! 订单号: {self.current_taskid}", fg=self.COLOR_SUCCESS)
        self._safe_ui_update(self.signal_light, text="● 监听短信中", fg="#f39c12")
        self._safe_ui_update(self.code_display, text="WAITING", fg="#e67e22", bg="#fef9e7")
        self.btn_copy_code.config(state="disabled")

        # 启动高频多线程轮询监听
        self.is_looping = True
        threading.Thread(target=self.poll_code, daemon=True).start()

    # 轮询验证码 (带安全的中断保护)
    def poll_code(self):
        max_duration = 120  # 最大监听时长（120秒）
        interval = 3       # 监听频率 3秒/次
        total_steps = max_duration // interval

        for step in range(total_steps):
            if not self.is_looping:
                break
            
            remaining = max_duration - (step * interval)
            self._safe_ui_update(self.status_text, text=f"⏳ 正高频监听短信中... (剩余 {remaining} 秒)", fg="#e67e22")
            
            ret = self.client.get_code(self.current_taskid)
            if ret.get("status") == "success":
                data = ret.get("data")
                raw = ret.get("raw", "")

                code_content = ""
                if isinstance(data, dict):
                    code_content = str(data.get("code", ""))
                else:
                    code_content = str(raw)

                content_upper = code_content.upper()
                # 判空及等待标志剔除
                if code_content and "WAIT" not in content_upper and "PENDING" not in content_upper and "SUCCESS" not in content_upper:
                    self._safe_ui_update(self.code_display, text=code_content, bg="#e8f8f5", fg=self.COLOR_SUCCESS)
                    self._safe_ui_update(self.status_text, text="🎉 验证码成功收到并解密！请迅速点击复制！", fg=self.COLOR_SUCCESS)
                    self._safe_ui_update(self.signal_light, text="● 接收成功", fg=self.COLOR_SUCCESS)
                    self._safe_ui_update(self.btn_copy_code, state="normal")
                    return
            
            time.sleep(interval)

        if self.is_looping:
            self._safe_ui_update(self.status_text, text="❌ 接收超时。请释放并重新申请号码。", fg=self.COLOR_RED)
            self._safe_ui_update(self.code_display, text="TIMEOUT", fg=self.COLOR_RED, bg="#fce4d6")
            self._safe_ui_update(self.signal_light, text="● 监听超时", fg=self.COLOR_RED)

    # 释放号码
    def release_num(self):
        self.is_looping = False
        phone = self.phone_show.get().strip()
        if not phone:
            self._safe_ui_update(self.status_text, text="⚠️ 释放失败：当前未分配号码", fg=self.COLOR_RED)
            return

        self._safe_ui_update(self.status_text, text="正在向云端提交释放指令...", fg=self.COLOR_ACCENT)

        def release_task():
            ret = self.client.release_number(phone)
            self.root.after(0, lambda: self._after_release(ret))
        threading.Thread(target=release_task, daemon=True).start()

    def _after_release(self, ret):
        message = ""
        if ret.get("status") == "success":
            data = ret.get("data")
            raw = ret.get("raw", "")
            if isinstance(data, dict):
                message = str(data.get("message", "号码释放已处理"))
            else:
                message = raw
        else:
            message = ret.get("message", "通讯故障")

        self.phone_show.delete(0, tk.END)
        self._safe_ui_update(self.code_display, text="--- WAIT ---", bg="#f1f5f9", fg="#94a3b8")
        self.current_phone = ""
        self.current_taskid = ""
        self.btn_copy_code.config(state="disabled")
        self._safe_ui_update(self.status_text, text=f"ℹ️ {message}", fg=self.COLOR_SECONDARY)
        self._safe_ui_update(self.signal_light, text="● 系统就绪", fg=self.COLOR_SUCCESS)

    # 独立开发的现代化、自适应美化信息展示面板（解决 Messagebox 文本超长或排版崩溃的问题）
    def _format_pop_data_optimized(self, title: str, ret: dict):
        if ret.get("status") == "error":
            messagebox.showerror(title, f"请求发生系统故障：\n{ret.get('message')}")
            return

        data = ret.get("data")
        raw = ret.get("raw", "")

        formatted_msg = ""
        try:
            if isinstance(data, (dict, list)):
                formatted_msg = json.dumps(data, ensure_ascii=False, indent=4)
            else:
                formatted_msg = str(raw)
        except:
            formatted_msg = str(raw)

        if not formatted_msg.strip() or formatted_msg == "[]" or formatted_msg == "{}":
            formatted_msg = "📭 暂无相关历史/未完成数据记录 (返回为空)"

        # 弹出优雅的自定义展示子窗口
        detail_win = tk.Toplevel(self.root)
        detail_win.title(title)
        detail_win.geometry("520x400")
        detail_win.configure(bg="#f8f9fa")
        detail_win.transient(self.root)
        detail_win.grab_set()

        lbl = tk.Label(detail_win, text=f"📋 {title} 明细:", font=("Microsoft YaHei", 10, "bold"), fg=self.COLOR_PRIMARY, bg="#f8f9fa")
        lbl.pack(anchor="w", padx=15, pady=10)

        txt_frame = tk.Frame(detail_win, bd=1, relief="solid")
        txt_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        scrollbar = tk.Scrollbar(txt_frame)
        scrollbar.pack(side="right", fill="y")

        text_area = tk.Text(txt_frame, font=("Consolas", 10), bg="#1e293b", fg="#f8fafc", insertbackground="white", yscrollcommand=scrollbar.set, wrap="word")
        text_area.insert("1.0", formatted_msg)
        text_area.config(state="disabled")
        text_area.pack(fill="both", expand=True)
        scrollbar.config(command=text_area.yview)

    # 查询挂单
    def check_order(self):
        key = self.key_input.get().strip()
        if not key:
            messagebox.showwarning("密钥缺失", "API 密钥不能为空，请配置密钥后再试！")
            return
        self.client = JmSMSClient(key)
        def query():
            ret = self.client.get_pending_orders()
            self.root.after(0, lambda: self._format_pop_data_optimized("当前未完成订单", ret))
        threading.Thread(target=query, daemon=True).start()

    # 查询消费记录 (已修复 Bug)
    def check_success_orders(self):
        key = self.key_input.get().strip()
        if not key:
            messagebox.showwarning("密钥缺失", "API 密钥不能为空，请配置密钥后再试！")
            return
        self.client = JmSMSClient(key)
        def query():
            ret = self.client.get_successful_orders()
            # 💡 这里已完美修复：修正为调用优雅的通用展示函数，而不是之前的 _after_release 释放函数！
            self.root.after(0, lambda: self._format_pop_data_optimized("消费历史记录", ret))
        threading.Thread(target=query, daemon=True).start()


if __name__ == "__main__":
    # 高 DPI 清晰度完美适配
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    app = CartierMillerSmsApp(root)
    
    def close_event():
        app.is_looping = False
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", close_event)
    root.mainloop()