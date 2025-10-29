import os
import threading
import time
from flask import Flask, render_template, request

# --- 路径和全局数据设置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "information.txt")
# 这个字典将用于在模块间传递最终的配置数据
LATEST_CONFIG_DATA = {}


class ConfigServer:
    """
    一个封装了Flask网页服务的类，用于处理用户配置。
    """

    def __init__(self, completion_event):
        # 初始化Flask应用，并明确模板文件夹路径
        self.app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
        # 用于通知主程序配置已完成的事件标志
        self.completion_event = completion_event
        self.server_thread = None

        # 屏蔽Flask的启动日志
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

        # 设置网页路由
        self._setup_routes()

    def _load_config(self):
        """从 information.txt 文件读取配置"""
        if not os.path.exists(CONFIG_FILE): return {}
        config = {}
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.startswith("#"): continue
                try:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
                except ValueError:
                    pass
        return config

    def _save_config(self, data):
        """根据网页表单提交的数据保存配置"""
        global LATEST_CONFIG_DATA
        content = "# (这是由网页配置生成器自动生成的文件)\n\n"
        if data.get('login_method') == 'manual':
            data['username'], data['password'] = '', ''

        # 【修改】添加 'grabbing_mode' 到字段列表
        fields = ['username', 'password', 'campus', 'ball', 'venues', 'appointment', 'payment_password',
                  'companions_id', 'grabbing_mode']

        for field in fields:
            content += f"{field} = {data.get(field, '')}\n"
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"配置已成功保存到 {CONFIG_FILE}")
        # 重新加载配置到全局变量，供主程序使用
        LATEST_CONFIG_DATA = self._load_config()
        # 特殊处理同行人ID列表
        companions_str = LATEST_CONFIG_DATA.get("companions_id", "")
        LATEST_CONFIG_DATA["companions_id"] = [id.strip() for id in companions_str.split(",") if id.strip()]

    def _setup_routes(self):
        """定义Flask的网页路由"""

        @self.app.route('/')
        def index():
            return render_template('index.html', config=self._load_config())

        @self.app.route('/start', methods=['POST'])
        def start_process():
            form_data = request.form.to_dict()
            self._save_config(form_data)
            # 设置事件，通知主程序可以继续执行
            self.completion_event.set()
            return """
            <!DOCTYPE html><html lang="zh-CN"><head><title>配置成功</title><style>body{font-family: sans-serif; text-align: center; padding-top: 50px; background-color: #f0fdf4; color: #166534;} h1{font-size: 2em;}</style></head>
            <body><h1>✅ 配置已保存！</h1><p>浏览器将自动跳转到登录页面，请继续操作...</p></body></html>
            """

    def run_server(self):
        """运行Flask服务器的内部方法"""
        self.app.run(host='127.0.0.1', port=8088, debug=False)

    def start(self):
        """在后台线程中启动服务器"""
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()


if __name__ == '__main__':
    # --- 用于独立测试 ---
    # 这个模块允许你直接运行 web_server.py 来预览和测试网页，
    # 流程与主程序一致：自动打开浏览器，保存配置后自动关闭。
    import subprocess
    from threading import Timer


    def launch_browser(url):
        """启动项目自带的浏览器"""
        chrome_exe_path = os.path.join(BASE_DIR, 'chrome-win64', 'chrome.exe')
        if not os.path.exists(chrome_exe_path):
            print(f"错误：在测试模式下找不到项目自带的浏览器: {chrome_exe_path}")
            return
        print("正在启动项目自带的浏览器打开配置页面...")
        subprocess.Popen([chrome_exe_path, f"--app={url}"])


    print("======================================================")
    print("     正在以【独立测试模式】启动网页配置服务器...     ")
    print("======================================================")

    # 1. 创建一个虚拟的 Event，用于接收来自网页的“完成”信号
    dummy_event = threading.Event()

    # 2. 实例化服务器并启动 (在后台线程运行)
    server = ConfigServer(completion_event=dummy_event)
    server.start()

    # 3. 自动打开浏览器
    config_url = "http://127.0.0.1:8088"
    Timer(1, lambda: launch_browser(config_url)).start()
    print(f"\n请在自动打开的浏览器窗口中完成配置...")

    # 4. 等待用户点击“保存”按钮
    dummy_event.wait()

    # 5. 用户已保存，关闭服务器
    print("\n配置已保存。测试服务器将在 1 秒后自动关闭。")
    time.sleep(1)
    os._exit(0)  # 强制退出整个程序