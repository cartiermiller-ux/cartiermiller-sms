import tkinter as tk
from tkinter import messagebox
import threading
import time
import requests
import json

# ========== 内嵌jm_client底层接口，无需单独文件 ==========
class JmSMSClient:
    # 💡【配置修改点 1】: 如果接码平台更换了新网址，请修改下方的 base_url 默认值
    def __init__(self, secret_key: str, base_url: str = "https://www.jm111.cc"):
        self.secret_key = secret_key
        self.base_url = base_url

    def _safe_request(self, url: str, params: dict) -> dict:
        """通用安全请求解析器，确保任何返回格式都能解析，不遗漏数据"""
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                raw_text = response.text.strip()
                # 尝试解析为 JSON
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
        """获取号码接口 - 返回统一封装格式"""
        url = f"{self.base_url}/api/getnumber"
        params = {
            "country": country,
            "pid": pid,
            "secret_key": self.secret_key,
        }
        return self._safe_request(url, params)

    def get_code(self, taskid: str):
        """获取验证码接口 - 返回统一封装格式"""
        url = f"{self.base_url}/api/getcode"
        params = {"taskid": taskid, "secret_key": self.secret_key}
        return self._safe_request(url, params)

    def release_number(self, phone: str):
        """释放号码接口 - 返回统一封装格式"""
        url = f"{self.base_url}/api/releasenumber"
        clean_phone = "".join(filter(str.isdigit, str(phone)))
        params = {"phone": clean_phone, "secret_key": self.secret_key}
        return self._safe_request(url, params)

    def get_pending_orders(self):
        """查询正进行的订单 - 返回统一封装格式"""
        url = f"{self.base_url}/api/pendingorders"
        params = {"secret_key": self.secret_key}
        return self._safe_request(url, params)

    def get_successful_orders(self):
        """查询消费记录 - 返回统一封装格式"""
        url = f"{self.base_url}/api/successfulorders"
        params = {"secret_key": self.secret_key}
        return self._safe_request(url, params)


# ========== GUI主程序 Cartiermiller云接码正式版 ==========
class CartierMillerSmsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CartierandMiller云接码 - 正式版 v2.0")
        
        self.root.geometry("580x590") # 稍微拉高高度
        self.root.configure(bg="#f5f7f6")
        self.root.resizable(False, False)

        # 💡【配置修改点 2】: 在下方双引号内填入您默认想要自动加载的 API 密钥
        self.default_key = "ae96221a960ae51fcd91e23d1e906781"
        self.client = JmSMSClient(self.default_key)

        # 运行状态
        self.current_taskid = ""
        self.current_phone = ""
        self.is_looping = False

        # 配色
        self.PRIMARY = "#2c3e50"
        self.SECONDARY = "#3498db"
        self.SUCCESS_COLOR = "#2ecc71"
        self.RED = "#e74c3c"
        self.BG = "#f5f7f6"
        self.WHITE = "#ffffff"

        self._build_ui()

    def _safe_ui_update(self, widget, **kwargs):
        # 线程安全更新UI，杜绝黑屏
        if widget.winfo_exists():
            self.root.after(0, lambda: widget.config(**kwargs))

    def _build_ui(self):
        # 顶部标题栏
        top_frame = tk.Frame(self.root, bg=self.PRIMARY, height=60)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)
        tk.Label(top_frame, text="CartierandMiller 云接码平台", font=("微软雅黑", 14, "bold"), fg=self.WHITE, bg=self.PRIMARY).pack(side="left", padx=20, pady=15)
        tk.Label(top_frame, text="正式版 v2.0", font=("微软雅黑", 10), fg="#bdc3c7", bg=self.PRIMARY).pack(side="right", padx=20, pady=15)

        main_box = tk.Frame(self.root, bg=self.BG)
        main_box.pack(fill="both", expand=True, padx=15, pady=15)

        # API密钥区域
        key_group = tk.LabelFrame(main_box, text="API密钥配置", bg=self.BG, font=("微软雅黑", 10, "bold"))
        key_group.pack(fill="x", pady=6)
        self.key_input = tk.Entry(key_group, font=("Consolas", 11))
        self.key_input.insert(0, self.default_key)
        self.key_input.pack(fill="x", ipady=5, padx=5, pady=5)

        # 参数控制区
        param_group = tk.LabelFrame(main_box, text="任务控制中心", bg=self.BG, font=("微软雅黑", 10, "bold"))
        param_group.pack(fill="x", pady=6)
        
        left = tk.Frame(param_group, bg=self.BG)
        left.pack(side="left", padx=5)
        tk.Label(left, text="国家代码：", bg=self.BG).grid(row=0, column=0, sticky="w", pady=4)
        self.country_in = tk.Entry(left, width=10)
        self.country_in.insert(0, "TH")
        self.country_in.grid(row=0, column=1, padx=6)
        tk.Label(left, text="项目ID：", bg=self.BG).grid(row=1, column=0, sticky="w", pady=4)
        self.pid_in = tk.Entry(left, width=10)
        self.pid_in.insert(0, "2")
        self.pid_in.grid(row=1, column=1, padx=6)

        # 右侧按钮组
        right_btn = tk.Frame(param_group, bg=self.BG)
        right_btn.pack(side="right", fill="both", expand=True, padx=8)
        
        # 快捷水平并排两个小查询按钮
        query_sub_frame = tk.Frame(right_btn, bg=self.BG)
        query_sub_frame.pack(fill="x", pady=2)
        tk.Button(query_sub_frame, text="未完成订单", command=self.check_order, bg="#ecf0f1", cursor="hand2", width=12).pack(side="left", expand=True, fill="x", padx=(0,2))
        tk.Button(query_sub_frame, text="消费记录", command=self.check_success_orders, bg="#ecf0f1", cursor="hand2", width=12).pack(side="right", expand=True, fill="x", padx=(2,0))
        
        tk.Button(right_btn, text="申请新号码", command=self.get_num, bg=self.SECONDARY, fg=self.WHITE, font=("微软雅黑", 10, "bold"), cursor="hand2").pack(fill="x", pady=2, ipady=4)

        # 号码展示
        phone_box = tk.Frame(main_box, bg=self.BG, bd=1, relief="solid")
        phone_box.pack(fill="x", pady=6)
        tk.Label(phone_box, text="当前手机号：", bg=self.BG, font=("微软雅黑", 10)).pack(side="left", padx=10, pady=10)
        self.phone_show = tk.Entry(phone_box, font=("微软雅黑", 14, "bold"), fg=self.SECONDARY, width=18, justify="center")
        self.phone_show.pack(side="left")
        tk.Button(phone_box, text="释放号码", command=self.release_num, bg=self.RED, fg=self.WHITE, cursor="hand2").pack(side="right", padx=10, pady=5)

        # 验证码看板
        code_group = tk.LabelFrame(main_box, text="验证码接收看板", bg=self.BG, font=("微软雅黑", 10, "bold"))
        code_group.pack(fill="both", expand=True, pady=6)
        self.status_text = tk.Label(code_group, text="[系统就绪] 等待操作", fg="#666", bg=self.BG, anchor="w")
        self.status_text.pack(fill="x", pady=3)
        self.code_display = tk.Label(code_group, text="---等待验证码---", font=("Consolas", 28, "bold"), bg="#ecf0f1", width=22, height=2)
        self.code_display.pack(fill="both", expand=True, pady=8)

    # 申请号码
    def get_num(self):
        key = self.key_input.get().strip()
        country = self.country_in.get().strip()
        pid = self.pid_in.get().strip()
        if not key:
            messagebox.showwarning("提示", "API 密钥不能为空，请先在上方配置密钥！")
            return
        self.client = JmSMSClient(key)
        self._safe_ui_update(self.status_text, text="正在申请号码...", fg=self.SECONDARY)

        def task():
            res = self.client.get_number(country, pid)
            self.root.after(0, lambda: self._handle_getnum(res))
        threading.Thread(target=task, daemon=True).start()

    def _handle_getnum(self, res):
        # 1. 检查请求是否通顺
        if res.get("status") == "error":
            self._safe_ui_update(self.status_text, text=f"❌ 请求失败: {res.get('message')}", fg=self.RED)
            return

        data = res.get("data")
        raw = res.get("raw", "")

        # 2. 解析返回结果
        if isinstance(data, dict):
            # 获取号码成功的 JSON 返回包含 phone 和 taskid 字段
            self.current_phone = str(data.get("phone", ""))
            self.current_taskid = str(data.get("taskid", ""))
        else:
            # 文本兼容解析 (如: SUCCESS|手机号|任务ID)
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

        # 3. 校验数据有效性
        if not self.current_phone or "ERROR" in self.current_phone.upper() or self.current_phone == "None" or self.current_phone == "":
            err_msg = raw if raw else "没有分配到可用号码，请检查余额或项目库存"
            self._safe_ui_update(self.status_text, text=f"❌ 申请失败: {err_msg}", fg=self.RED)
            messagebox.showwarning("申请号码失败", f"平台返回信息:\n{err_msg}")
            return
            
        # 4. 更新界面
        self.phone_show.delete(0, tk.END)
        self.phone_show.insert(0, self.current_phone)
        self._safe_ui_update(self.status_text, text=f"✅ 获取成功 订单号(TaskID): {self.current_taskid}", fg="green")
        
        # 5. 启动轮询
        self.is_looping = True
        threading.Thread(target=self.poll_code, daemon=True).start()

    # 轮询验证码
    def poll_code(self):
        for i in range(30):
            if not self.is_looping:
                break
            self._safe_ui_update(self.status_text, text=f"⏳ 短信监听中 {i+1}/30秒...", fg=self.SECONDARY)
            ret = self.client.get_code(self.current_taskid)
            
            if ret.get("status") == "success":
                data = ret.get("data")
                raw = ret.get("raw", "")

                code_content = ""
                # 解析验证码字段
                if isinstance(data, dict):
                    code_content = str(data.get("code", ""))
                else:
                    code_content = str(raw)
                
                content_upper = code_content.upper()
                # 检查验证码内容不为空，且不属于等待、挂起、排队状态
                if code_content and "WAIT" not in content_upper and "PENDING" not in content_upper and "SUCCESS" not in content_upper:
                    self._safe_ui_update(self.code_display, text=code_content, bg="#27ae60", fg=self.WHITE)
                    self._safe_ui_update(self.status_text, text="🎉 验证码已成功接收！", fg="green")
                    return
            time.sleep(4)
            
        if self.is_looping:
            self._safe_ui_update(self.status_text, text="❌ 接收超时，请点击释放号码", fg=self.RED)
            self._safe_ui_update(self.code_display, text="TIMEOUT", fg=self.RED, bg="#ecf0f1")

    # 释放号码
    def release_num(self):
        self.is_looping = False
        phone = self.phone_show.get().strip()
        if not phone:
            self._safe_ui_update(self.status_text, text="无号码可释放", fg="#666")
            return
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
                message = str(data.get("message", "号码释放指令已送达"))
            else:
                message = raw
        else:
            message = ret.get("message", "网络连接异常")

        self.phone_show.delete(0, tk.END)
        self._safe_ui_update(self.code_display, text="---等待验证码---", bg="#ecf0f1", fg=self.PRIMARY)
        self.current_phone = ""
        self.current_taskid = ""
        self._safe_ui_update(self.status_text, text=f"ℹ️ {message}", fg="#333")

    def _format_pop_data(self, title: str, ret: dict):
        """通用美化弹出窗口，确保能优雅地展示列表或字典数据"""
        if ret.get("status") == "error":
            messagebox.showerror(title, f"请求失败：\n{ret.get('message')}")
            return

        data = ret.get("data")
        raw = ret.get("raw", "")

        # 格式化展示
        formatted_msg = ""
        try:
            if isinstance(data, (dict, list)):
                formatted_msg = json.dumps(data, ensure_ascii=False, indent=4)
            else:
                formatted_msg = str(raw)
        except:
            formatted_msg = str(raw)

        if not formatted_msg.strip() or formatted_msg == "[]" or formatted_msg == "{}":
            formatted_msg = "📭 暂无相关订单/交易数据（数据为空）"

        messagebox.showinfo(title, formatted_msg)

    # 查询挂单
    def check_order(self):
        key = self.key_input.get().strip()
        if not key:
            messagebox.showwarning("提示", "API 密钥不能为空，请先在上方配置密钥！")
            return
        self.client = JmSMSClient(key)
        def query():
            ret = self.client.get_pending_orders()
            self.root.after(0, lambda: self._format_pop_data("未完成订单列表", ret))
        threading.Thread(target=query, daemon=True).start()

    # 查询消费记录
    def check_success_orders(self):
        key = self.key_input.get().strip()
        if not key:
            messagebox.showwarning("提示", "API 密钥不能为空，请先在上方配置密钥！")
            return
        self.client = JmSMSClient(key)
        def query():
            ret = self.client.get_successful_orders()
            self.root.after(0, lambda: self._format_pop_data("消费历史记录", ret))
        threading.Thread(target=query, daemon=True).start()


# 启动程序
if __name__ == "__main__":
    # 高 DPI 适配
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