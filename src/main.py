import os
import sys
import random
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- 全局变量 ---
# 将日期计算放在这里，方便全局使用
NEXT_DAY = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

# --- WebDriver 全局实例 ---
driver = None


def login(username, password):
    """自动登录模块"""
    global driver
    print("检测到学号和密码，正在执行自动登录...")
    try:
        # 等待用户名输入框加载并输入
        username_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "username"))
        )
        username_input.send_keys(username)

        # 使用JavaScript输入密码，更稳定
        driver.execute_script("document.getElementById('password').value=arguments[0];", password)

        # 确保密码已填入
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element_value((By.ID, "password"), password)
        )

        # 点击登录按钮
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login_submit"))
        )
        driver.execute_script("arguments[0].click();", login_button)
        print("登录成功！")
    except TimeoutException:
        print("登录超时，请检查网页是否能正常访问或账号密码是否正确。")
        driver.quit()
        sys.exit(1)


def select_venue(campus, ball, appointment, venues):
    """选择场馆和时间 (带自动刷新和随机场地优先)"""
    # 在12:30:00准时调用此函数时，第一件事就是刷新页面
    print("12:30时间到！正在刷新页面以获取最新场次...")
    driver.refresh()
    print("页面刷新完毕，开始执行选择流程...")

    try:
        # 延长等待时间以应对服务器延迟（和刷新后的页面加载）
        wait = WebDriverWait(driver, 30)

        print("步骤1: 正在点击校区...")
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[text()='{campus}']"))).click()
        print(f" -> 已点击校区: {campus}")

        print("步骤2: 正在点击球类...")
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[text()='{ball}']"))).click()
        print(f" -> 已点击球类: {ball}")

        print("步骤3: 正在点击日期 (明天)...")
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//label[@for='{NEXT_DAY}']"))).click()
        print(f" -> 已点击日期: {NEXT_DAY}")

        print(f"步骤4: 正在点击时间段 '{appointment}'...")
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[text()='{appointment}']"))).click()
        print(f" -> 已点击时间段: {appointment}")

        print(f"步骤5: 正在寻找场馆 '{venues}'...")
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[text()='{venues}']"))).click()
        print(f" -> 已点击场馆: {venues}")

        print("步骤6: 寻找一个可预约的场地 (随机优先)...")
        group_2_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'group-2')))

        # 根据校区定义不同的场地列表
        if campus == "粤海校区":
            priority_courts = ['C5', 'C6', 'C7', 'C8', 'C4', 'C3', 'C2', 'C1',
                               'B5', 'B6', 'B7', 'B8', 'B4', 'B3', 'B2', 'B1',
                               'D5', 'D6', 'D7', 'D8', 'D4', 'D3', 'D2', 'D1',
                               'A5', 'A6', 'A7', 'A8', 'A4', 'A3', 'A2', 'A1']
        else:  # 丽湖校区
            priority_courts = ['1号', '2号', '3号', '4号', '5号', '6号', '7号', '8号', '9号', '10号', '11号', '12号']

        random.shuffle(priority_courts)
        selected_court = False
        print(f" -> 正在按随机顺序查找场地...")

        for court_name in priority_courts:
            for group_2 in group_2_elements:
                element = group_2.find_element(By.CLASS_NAME, 'element')
                element_text = element.text
                if court_name in element_text and '可预约' in element_text:
                    frame_child1 = group_2.find_element(By.CLASS_NAME, 'frame-child1')
                    frame_child1.click()
                    selected_court = True
                    print(f" -> 成功选择一个【随机优先】场地：{element_text}")
                    break
            if selected_court:
                break

        if not selected_court:
            print(f" -> 未找到任何在优先列表中的可预约场地，尝试选择任意可用场地...")
            for group_2 in group_2_elements:
                element = group_2.find_element(By.CLASS_NAME, 'element')
                element_text = element.text
                if '可预约' in element_text and '场' in element_text:
                    frame_child1 = group_2.find_element(By.CLASS_NAME, 'frame-child1')
                    frame_child1.click()
                    selected_court = True
                    print(f" -> 成功选择一个【备选】场地：{element_text}")
                    break

            if not selected_court:
                print(" -> 未找到任何可预约的场地。")
                driver.quit()
                sys.exit(1)

        print("步骤7: 提交预约...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='提交预约']"))).click()
        print("场地选择完成，已提交预约。")

    except TimeoutException:
        print("\n!!!!!!!!!!!!!!!!!! 脚本超时 !!!!!!!!!!!!!!!!!!!")
        print(" -> 错误：在日志中**最后一条'步骤X' print语句**之后的操作上等待超时。")
        try:
            error_screenshot_path = os.path.join(os.path.dirname(__file__),
                                                 f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(error_screenshot_path)
            print(f"\n -> 已保存错误截图到: {error_screenshot_path}")
            print(" -> 请打开这张图片，检查当时的网页界面。")
        except Exception as e:
            print(f" -> 截图失败: {e}")
        driver.quit()
        sys.exit(1)


def add_companions(companions_id):
    """添加同行人"""
    if not companions_id:
        return

    print("正在添加同行人...")
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='同行人']"))).click()
        for companion_id in companions_id:
            wait.until(EC.visibility_of_element_located((By.XPATH, "//button[text()='添加同行人']"))).click()
            search_input = wait.until(EC.visibility_of_element_located((By.ID, "searchId")))
            search_input.send_keys(companion_id)
            driver.find_element(By.XPATH, "//div[text()='查询']").click()
            wait.until(EC.visibility_of_element_located((By.XPATH, "//button[text()='确定']"))).click()
            print(f"已添加同行人：{companion_id}")
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "jqx-window-close-button"))).click()
        print("同行人添加完毕。")
    except TimeoutException:
        print("添加同行人失败或超时。")
    except Exception as e:
        print(f"添加同行人时发生未知错误: {e}")


def pay(payment_password):
    """通过体育经费支付"""
    if not payment_password:
        return

    print("正在处理支付...")
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='未支付']"))).click()
        initial_window_count = len(driver.window_handles)
        try:
            pay_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '支付')]")))
            pay_button.click()
        except TimeoutException:
            print("未找到支付按钮。")
            return
        wait.until(EC.number_of_windows_to_be(initial_window_count + 1))
        window_handles = driver.window_handles
        driver.switch_to.window(window_handles[-1])
        print("已切换到支付窗口。")
        wait.until(EC.visibility_of_element_located((By.ID, "btnNext"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "password"))).click()
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "key-button")))
        for digit in payment_password:
            driver.find_element(By.CLASS_NAME, f"key-button.key-{digit}").click()
        wait.until(EC.visibility_of_element_located((By.XPATH, "//button[text()='确认支付']"))).click()
        print("支付密码已输入，确认支付。")
    except TimeoutException:
        print("支付流程超时。")
    except Exception as e:
        print(f"支付时发生未知错误: {e}")


def load_config():
    """从 information.txt 文件读取配置"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "information.txt")

    if not os.path.exists(config_path):
        print(f"错误：找不到配置文件 {config_path}。")
        return None

    config = {}
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            try:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
            except ValueError:
                print(f"警告：配置文件中格式错误的一行将被忽略: {line}")

    companions_str = config.get("companions_id", "")
    config["companions_id"] = [id.strip() for id in companions_str.split(",") if id.strip()]

    print("\n--- 抢票配置加载成功 ---")
    for key, value in config.items():
        if 'password' in key.lower():
            print(f"{key}: {'*' * len(str(value))}")
        else:
            print(f"{key}: {value}")
    print("--------------------------\n")
    return config


def initialize_driver():
    """初始化 WebDriver (自动寻找相对路径下的驱动和浏览器)"""
    global driver
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        chromedriver_path = os.path.join(script_dir, 'chromedriver-win64', 'chromedriver.exe')
        chrome_binary_path = os.path.join(script_dir, 'chrome-win64', 'chrome.exe')

        if not os.path.exists(chromedriver_path):
            print(f"错误：在指定路径下找不到 chromedriver.exe。请检查 'chromedriver-win64' 文件夹。")
            return False
        if not os.path.exists(chrome_binary_path):
            print(f"错误：在指定路径下找不到 chrome.exe。请检查 'chrome-win64' 文件夹。")
            return False

        service = Service(executable_path=chromedriver_path)
        options = Options()
        options.binary_location = chrome_binary_path

        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)
        return True
    except Exception as e:
        print(f"初始化WebDriver失败: {e}")
        return False


def run_grabbing_process(config):
    """执行抢票的主流程，包括定时和分步执行"""
    global driver

    ACTION_TIME_STR = "12:30:00"
    ACTION_TIME = datetime.strptime(ACTION_TIME_STR, "%H:%M:%S").time()

    PRE_LOGIN_SECONDS = 90
    PRE_LOGIN_TIME = (datetime.strptime(ACTION_TIME_STR, "%H:%M:%S") - timedelta(seconds=PRE_LOGIN_SECONDS)).time()

    print(f"脚本已启动。")

    # 检查是否需要自动登录
    use_auto_login = config.get("username") and config.get("password")
    if use_auto_login:
        print(f"模式: 自动登录。将在 {PRE_LOGIN_TIME} 自动登录。")
    else:
        print(f"模式: 手动登录。将在 {PRE_LOGIN_TIME} 打开登录页面。")
    print(f"所有模式都将在 {ACTION_TIME} 准时抢票。")

    while True:
        if datetime.now().time() >= PRE_LOGIN_TIME:
            break
        time.sleep(1)

    if not initialize_driver():
        return

    try:
        url = 'https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do'
        driver.get(url)

        if use_auto_login:
            login(config["username"], config["password"])
        else:
            print("\n!!! 请在浏览器中手动登录 !!!")
            print("脚本将自动检测登录状态，登录成功后会自动继续...")
            try:
                # 等待URL从登录页面(含auth)跳转到主页(不含auth)
                # 给予5分钟的登录时间
                WebDriverWait(driver, timeout=300).until(
                    EC.url_contains("ehall.szu.edu.cn")
                )
                print("✅ 检测到登录成功！")
            except TimeoutException:
                print("❌ 手动登录超时（5分钟），程序将退出。")
                driver.quit()
                sys.exit(1)

        print(f"\n登录流程完毕，等待到达 {ACTION_TIME} 开始抢票...")
        while True:
            if datetime.now().time() >= ACTION_TIME:
                break
            time.sleep(0.01)

        select_venue(config["campus"], config["ball"], config["appointment"], config["venues"])
        add_companions(config["companions_id"])
        pay(config["payment_password"])

        print('\n🎉 预约并支付成功！请登录eHall查看确认。')
        time.sleep(10)

    except Exception as e:
        print(f"脚本运行出错: {e}")
    finally:
        if driver:
            driver.quit()
            print("浏览器已关闭。")


if __name__ == "__main__":
    config = load_config()
    if config:
        run_grabbing_process(config)

    print("\n任务执行完毕，程序退出。")
    print("github项目发布地址：https://github.com/9900ff/SZU-badminton-GO")
    # 在最后暂停，方便用户查看最终结果
    input("按 Enter 键退出...")
    sys.exit()

