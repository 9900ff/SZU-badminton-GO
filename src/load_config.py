
import os
import subprocess
import tkinter as tk
from tkinter import messagebox

# 定义配置文件路径和主脚本路径
CONFIG_FILE = "information.txt"
MAIN_SCRIPT = "main.py"
PYTHON_EXECUTABLE = os.path.join('python-env', 'python.exe')


def load_config():
    """从配置文件加载信息"""
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config


def save_config(entries):
    """保存信息到配置文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        # 写入头部说明
        f.write("# ======================================================================\n")
        f.write("#            深圳大学场馆预约脚本 - 快速配置区\n")
        f.write("# ======================================================================\n")
        f.write("# (这是由图形化配置工具自动生成的文件)\n\n")

        # 写入配置项
        for label_text, entry_widget in entries.items():
            f.write(f"{label_text} = {entry_widget.get()}\n")

        # 写入尾部说明
        f.write("\n# ======================================================================\n")
        f.write("#                       配置说明与选项参考\n")
        f.write("# ======================================================================\n")
        f.write("# (以下为注释内容，帮助你填写上面的字段，无需修改)\n")
        f.write("# ... (此处省略详细说明) ...\n")


def start_main_script():
    """保存配置并启动主脚本"""
    # 从输入框获取当前配置
    current_entries = {
        "学号": entry_username,
        "密码": entry_password,
        "校区": entry_campus,
        "球类": entry_ball,
        "预约场馆": entry_venues,
        "预约时间": entry_appointment,
        "支付密码": entry_payment_password,
        "同行人": entry_companions_id,
    }

    # 检查必填项
    if not current_entries["学号"].get() or not current_entries["密码"].get():
        messagebox.showerror("错误", "“学号”和“密码”为必填项！")
        return

    # 保存配置
    save_config(current_entries)

    # 关闭配置窗口
    root.destroy()

    # 启动主脚本
    print("配置已保存，正在启动抢票脚本...")
    # 使用 subprocess.Popen 可以在新窗口中运行，不阻塞当前窗口
    # 注意：在Windows上，如果 start.bat 中有 chcp 65001，直接运行 bat 效果最好
    subprocess.Popen("start.bat", shell=True)


# --- 创建主窗口 ---
root = tk.Tk()
root.title("深大抢场助手 - 配置工具")
root.geometry("400x350")  # 设置窗口大小
root.resizable(False, False)  # 禁止调整窗口大小

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True, fill="both")

# --- 创建标签和输入框 ---
labels_texts = ["学号", "密码", "校区", "球类", "预约场馆", "预约时间", "支付密码", "同行人"]
entries = {}

for i, text in enumerate(labels_texts):
    label = tk.Label(frame, text=f"{text}:", anchor="w")
    label.grid(row=i, column=0, sticky="w", pady=5)

    entry = tk.Entry(frame, width=35)
    entry.grid(row=i, column=1, sticky="w", pady=5)

    # 如果是密码框，显示为 *
    if text == "密码" or text == "支付密码":
        entry.config(show="*")

    entries[text] = entry

# --- 加载现有配置并填充输入框 ---
initial_config = load_config()
entry_username = entries["学号"]
entry_password = entries["密码"]
entry_campus = entries["校区"]
entry_ball = entries["球类"]
entry_venues = entries["预约场馆"]
entry_appointment = entries["预约时间"]
entry_payment_password = entries["支付密码"]
entry_companions_id = entries["同行人"]

entry_username.insert(0, initial_config.get("学号", ""))
entry_password.insert(0, initial_config.get("密码", ""))
entry_campus.insert(0, initial_config.get("校区", "粤海校区"))
entry_ball.insert(0, initial_config.get("球类", "羽毛球"))
entry_venues.insert(0, initial_config.get("预约场馆", "全部"))
entry_appointment.insert(0, initial_config.get("预约时间", "12:00-13:00(可预约)"))
entry_payment_password.insert(0, initial_config.get("支付密码", ""))
entry_companions_id.insert(0, initial_config.get("同行人", ""))

# --- 创建按钮 ---
start_button = tk.Button(frame, text="保存并开始抢票", command=start_main_script, height=2, bg="#4CAF50", fg="white",
                         font=("Arial", 10, "bold"))
start_button.grid(row=len(labels_texts), columnspan=2, pady=20, sticky="ew")

# --- 运行窗口 ---
root.mainloop()
