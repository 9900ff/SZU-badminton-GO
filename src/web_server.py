import os
import sys
import subprocess
from threading import Timer
from flask import Flask, render_template, request

# 获取当前脚本所在的绝对目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 定义所有路径都相对于脚本所在的目录，确保路径的准确性
CONFIG_FILE = os.path.join(BASE_DIR, "information.txt")
CHROME_EXE_PATH = os.path.join(BASE_DIR, 'chrome-win64', 'chrome.exe')

# --- Flask App 设置 ---
# 同样，明确告诉 Flask 模板文件夹在哪里
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))

# 关闭 Flask 的启动日志，保持界面干净
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def load_config():
    """从配置文件加载信息"""
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line: continue
                try:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
                except ValueError:
                    pass
    return config


def save_config(data):
    """根据网页表单提交的数据保存配置"""
    content = """# ======================================================================
#            深圳大学场馆预约脚本 - 快速配置区
# ======================================================================
# (这是由网页配置生成器自动生成的文件)

"""
    # 如果是手动登录，则清空学号和密码
    if data.get('login_method') == 'manual':
        data['username'] = ''
        data['password'] = ''

    # 保证字段顺序
    fields = ['username', 'password', 'campus', 'ball', 'venues', 'appointment', 'payment_password', 'companions_id']
    for field in fields:
        content += f"{field} = {data.get(field, '')}\n"

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"配置已成功保存到 {CONFIG_FILE}")


# --- 网页路由 ---
@app.route('/')
def index():
    """主配置页面"""
    config = load_config()
    # 将加载的配置传给HTML模板
    return render_template('index.html', config=config)


@app.route('/start', methods=['POST'])
def start_process():
    """处理表单提交，保存配置，并关闭服务器"""
    form_data = request.form.to_dict()
    save_config(form_data)

    # 定义一个函数来关闭服务器进程
    def shutdown_server():
        print("配置服务器正在关闭...")
        # os._exit(0) 是一个可靠的硬退出，可以确保进程终止
        os._exit(0)

    # 延迟0.5秒执行关闭，确保HTTP响应能成功发回浏览器
    Timer(0.5, shutdown_server).start()

    # 返回给用户的成功页面
    return """
    <!DOCTYPE html><html lang="zh-CN"><head><title>配置成功</title><style>body{font-family: sans-serif; text-align: center; padding-top: 50px; background-color: #f0fdf4; color: #166534;} h1{font-size: 2em;}</style></head>
    <body><h1>✅ 配置已保存！</h1><p>抢票脚本即将启动，请查看原来的命令行窗口...</p><p>本页面可以关闭了。</p></body></html>
    """


def launch_browser(url):
    """启动项目自带的浏览器"""
    if not os.path.exists(CHROME_EXE_PATH):
        print(f"错误：找不到项目自带的浏览器，请确认路径是否正确: {CHROME_EXE_PATH}")
        return

    print("正在启动项目自带的浏览器打开配置页面...")
    # 使用 subprocess 精确启动自带的 chrome.exe
    # --app 模式可以创建一个干净的、无边框的窗口，体验更好
    subprocess.Popen([CHROME_EXE_PATH, f"--app={url}"])


def run_server():
    """启动服务器的函数"""
    url = "http://127.0.0.1:8088"
    # 使用 Timer 在服务器启动后延迟1秒打开浏览器
    Timer(1, lambda: launch_browser(url)).start()
    print("----------------------------------------------------")
    print("  欢迎使用深大抢场助手！")
    print("----------------------------------------------------")
    print("\n步骤 1: 正在启动网页配置工具...")
    print(f"如果浏览器未自动弹出，请手动打开 {url} 进行配置。")
    print("(请在打开的浏览器窗口中完成配置，然后点击“保存并启动”按钮)")

    # host='127.0.0.1' 仅本机访问
    app.run(host='127.0.0.1', port=8088, debug=False)


if __name__ == '__main__':
    run_server()

