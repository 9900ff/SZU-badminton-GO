import os
import sys
import random
import time
import threading
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# 将脚本当前所在的目录添加到 Python 的模块搜索路径中
# 这可以确保 'from web_server import ...' 始终有效
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from web_server import ConfigServer

# --- 全局变量 ---
NEXT_DAY = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
driver = None  # WebDriver 全局实例
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ======================================================================
#                        抢票逻辑部分 (Selenium)
# ======================================================================

def login(username, password):
    """自动登录模块"""
    global driver
    print("检测到学号和密码，正在执行自动登录...")
    try:
        username_input = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "username")))
        username_input.send_keys(username)
        driver.execute_script("document.getElementById('password').value=arguments[0];", password)
        WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element_value((By.ID, "password"), password))
        login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "login_submit")))
        driver.execute_script("arguments[0].click();", login_button)
        print("登录成功！")
    except TimeoutException:
        print("登录超时，请检查网页是否能正常访问或账号密码是否正确。")
        if driver: driver.quit()
        sys.exit(1)


def select_venue(campus, ball, appointment, venues):
    """选择场馆和时间 (带自动刷新和随机场地优先)"""
    print("12:30时间到！正在刷新页面以获取最新场次...")
    driver.refresh()
    print("页面刷新完毕，开始执行选择流程...")
    try:
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
        if campus == "粤海校区":
            priority_courts = ['C5', 'C6', 'C7', 'C8', 'C4', 'C3', 'C2', 'C1', 'B5', 'B6', 'B7', 'B8', 'B4', 'B3', 'B2',
                               'B1', 'D5', 'D6', 'D7', 'D8', 'D4', 'D3', 'D2', 'D1', 'A5', 'A6', 'A7', 'A8', 'A4', 'A3',
                               'A2', 'A1']
        else:
            priority_courts = ['1号', '2号', '3号', '4号', '5号', '6号', '7号', '8号', '9号', '10号', '11号', '12号']
        random.shuffle(priority_courts)
        selected_court = False
        print(f" -> 正在按随机顺序查找场地...")
        for court_name in priority_courts:
            for group_2 in group_2_elements:
                element = group_2.find_element(By.CLASS_NAME, 'element')
                element_text = element.text
                if court_name in element_text and '可预约' in element_text:
                    group_2.find_element(By.CLASS_NAME, 'frame-child1').click()
                    selected_court = True
                    print(f" -> 成功选择一个【随机优先】场地：{element_text}")
                    break
            if selected_court: break
        if not selected_court:
            print(f" -> 未找到任何在优先列表中的可预约场地，尝试选择任意可用场地...")
            for group_2 in group_2_elements:
                element = group_2.find_element(By.CLASS_NAME, 'element')
                if '可预约' in element.text and '场' in element.text:
                    group_2.find_element(By.CLASS_NAME, 'frame-child1').click()
                    selected_court = True
                    print(f" -> 成功选择一个【备选】场地：{element.text}")
                    break
            if not selected_court:
                print(" -> 未找到任何可预约的场地。")
                if driver: driver.quit()
                sys.exit(1)
        print("步骤7: 提交预约...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='提交预约']"))).click()
        print("场地选择完成，已提交预约。")
    except TimeoutException:
        print("\n!!!!!!!!!!!!!!!!!! 脚本超时 !!!!!!!!!!!!!!!!!!!")
        try:
            error_screenshot_path = os.path.join(BASE_DIR,
                                                 f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(error_screenshot_path)
            print(f"\n -> 已保存错误截图到: {error_screenshot_path}")
        except Exception as e:
            print(f" -> 截图失败: {e}")
        # 超时后不关闭浏览器，让用户查看
        # if driver: driver.quit()
        # sys.exit(1) # 不直接退出


def add_companions(companions_id):
    if not companions_id: return
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
    except Exception as e:
        print(f"添加同行人时发生错误: {e}")


def pay(payment_password):
    if not payment_password: return
    print("正在处理支付...")
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='未支付']"))).click()
        initial_window_count = len(driver.window_handles)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '支付')]"))).click()
        wait.until(EC.number_of_windows_to_be(initial_window_count + 1))
        driver.switch_to.window(driver.window_handles[-1])
        print("已切换到支付窗口。")
        wait.until(EC.visibility_of_element_located((By.ID, "btnNext"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "password"))).click()
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "key-button")))
        for digit in payment_password:
            driver.find_element(By.CLASS_NAME, f"key-button.key-{digit}").click()
        wait.until(EC.visibility_of_element_located((By.XPATH, "//button[text()='确认支付']"))).click()
        print("支付密码已输入，确认支付。")
    except Exception as e:
        print(f"支付时发生错误: {e}")


def initialize_driver():
    """初始化 WebDriver (自动寻找相对路径下的驱动和浏览器)"""
    global driver
    try:
        chromedriver_path = os.path.join(BASE_DIR, 'chromedriver-win64', 'chromedriver.exe')
        chrome_binary_path = os.path.join(BASE_DIR, 'chrome-win64', 'chrome.exe')
        if not os.path.exists(chromedriver_path) or not os.path.exists(chrome_binary_path):
            print("错误：找不到 'chromedriver-win64' 或 'chrome-win64' 文件夹。")
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
    """接管浏览器，执行抢票的主流程"""
    global driver
    ACTION_TIME_STR = "12:30:00"
    ACTION_TIME = datetime.strptime(ACTION_TIME_STR, "%H:%M:%S").time()

    try:
        url = 'https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do'
        print(f"\n配置完成，正在导航到深大登录页: {url}")
        driver.get(url)

        use_auto_login = config.get("username") and config.get("password")
        if use_auto_login:
            login(config["username"], config["password"])
        else:
            print("\n!!! 请在当前浏览器中手动登录 !!!")
            print("脚本将自动检测登录状态，登录成功后会自动继续...")
            try:
                WebDriverWait(driver, timeout=300).until(EC.url_contains("ehall.szu.edu.cn"))
                print("✅ 检测到登录成功！")
            except TimeoutException:
                print("❌ 手动登录超时（5分钟），程序将退出。")
                return

        print(f"\n登录流程完毕，等待到达 {ACTION_TIME} 开始抢票...")
        while True:
            if datetime.now().time() >= ACTION_TIME: break
            time.sleep(0.01)

        select_venue(config["campus"], config["ball"], config["appointment"], config["venues"])
        add_companions(config.get("companions_id", []))
        pay(config["payment_password"])

        print('\n🎉 预约并支付成功！请登录eHall查看确认。')
        # time.sleep(10) # 任务完成后不再需要固定等待

    except KeyError as e:
        print(f"\n!!!!!!!!!! 配置错误 !!!!!!!!!!")
        print(f"脚本在配置中找不到必要的信息: {e}")
        print("请检查 information.txt 文件是否已正确生成。")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    except Exception as e:
        print(f"脚本运行出错: {e}")


def load_config_from_file():
    """从 information.txt 文件加载配置。"""
    config_file_path = os.path.join(BASE_DIR, "information.txt")
    if not os.path.exists(config_file_path):
        print(f"错误：找不到配置文件 {config_file_path}")
        return None

    config = {}
    with open(config_file_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.startswith("#"): continue
            try:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
            except ValueError:
                pass

    # 特殊处理同行人
    companions_str = config.get("companions_id", "")
    config["companions_id"] = [id.strip() for id in companions_str.split(",") if id.strip()]
    return config


# ======================================================================
#                            主程序入口
# ======================================================================

if __name__ == "__main__":
    # 1. 创建一个用于线程通信的事件
    config_complete_event = threading.Event()

    # 2. 实例化配置服务器类，并启动它
    config_server = ConfigServer(completion_event=config_complete_event)
    config_server.start()
    time.sleep(1)  # 等待服务器启动

    # 3. 初始化Selenium浏览器
    if not initialize_driver():
        sys.exit(1)

    try:
        # 4. 打开配置页面
        config_url = "http://127.0.0.1:8088"
        print(f"请在打开的浏览器窗口中完成配置: {config_url}")
        driver.get(config_url)

        # 5. 等待用户在网页上提交配置
        config_complete_event.wait()

        # 6. 【关键修复】用户已提交配置，我们在这里主动重新读取配置文件
        latest_config = load_config_from_file()
        if not latest_config:
            raise Exception("无法加载配置，程序终止。")

        # 7. 现在接管浏览器执行抢票
        run_grabbing_process(latest_config)

        # 8. 【新逻辑】任务完成后，保持浏览器打开
        print("\n----------------------------------------------------")
        print("所有任务已执行完毕！")
        print("github项目发布地址：https://github.com/9900ff/SZU-badminton-GO")
        input(">>> 按 Enter 键关闭浏览器并退出... <<<")


    except WebDriverException:
        print("浏览器窗口被手动关闭，程序退出。")
    except Exception as e:
        print(f"主程序发生未知错误: {e}")
    finally:
        # 无论成功或失败，最终都会在这里关闭浏览器
        if driver:
            driver.quit()
            print("浏览器已关闭。")

    print("\n程序已退出。")
    # 使用 os._exit(0) 确保所有线程（包括Flask的）都被终止
    os._exit(0)

