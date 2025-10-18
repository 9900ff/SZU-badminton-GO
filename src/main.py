from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import time
import sys
import os
import random

# --- 全局变量 ---
# 将日期计算放在这里，方便全局使用
NEXT_DAY = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
TODAY = datetime.now().strftime('%Y-%m-%d')

# --- WebDriver 全局实例 ---
driver = None


def login(username, password):
    """登录模块"""
    global driver
    url = 'https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do?t_s=1709183352309#/sportVenue'
    driver.get(url)
    print("页面已打开，正在登录...")

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
    """选择场馆和时间 (最终调试版，带自动截图)"""
    print("正在选择场地...")
    try:
        # 延长等待时间以应对服务器延迟
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

        print("步骤6: 寻找一个可预约的场地...")
        group_2_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'group-2')))

        # 在这里修改你想要的优先场地名称关键字,有优先级就不要random
        # 定义你的所有目标场地
        if campus == "粤海校区":
            priority_courts = ['C5', 'C6', 'C7', 'C8', 'C4', 'C3', 'C2', 'C1',
                               'B5', 'B6', 'B7', 'B8', 'B4', 'B3', 'B2', 'B1',
                               'D5', 'D6', 'D7', 'D8', 'D4', 'D3', 'D2', 'D1',
                               'A5', 'A6', 'A7', 'A8', 'A4', 'A3', 'A2', 'A1',]
        else:
            priority_courts = ['1号', '2号', '3号', '4号', '5号', '6号', '7号', '8号', '9号', '10号', '11号', '12号']

        # --- 关键改动：打乱这个列表 ---
        random.shuffle(priority_courts)

        selected_court = False
        print(f"正在按随机顺序查找场地")

        # --- 按打乱后的 priority_courts 列表顺序来选择 ---
        # 遍历你的优先列表
        for court_name in priority_courts:
            # 遍历网页上的所有场地元素
            for group_2 in group_2_elements:
                element = group_2.find_element(By.CLASS_NAME, 'element')
                element_text = element.text

                # 检查网页元素是否包含当前优先级的场地名称，并且可预约
                if court_name in element_text and '可预约' in element_text:
                    # 找到了！
                    frame_child1 = group_2.find_element(By.CLASS_NAME, 'frame-child1')
                    frame_child1.click()
                    selected_court = True
                    print(f" -> 成功选择一个【随机优先】场地：{element_text}")
                    break  # 跳出内层循环 (遍历网页元素)

            if selected_court:
                break  # 跳出外层循环 (遍历优先级列表)

        # --- 如果一个目标场地都没找到 ---
        if not selected_court:
            print(f" -> 未找到任何在 'priority_courts' 列表中的可预约场地。")
            # 增加一个备选逻辑：选择任何一个可预约的场地
            print(" -> 正在尝试选择任何一个可预约的 'A' 场地或其它场地...")
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
        # ------------------- 随机场地优先选择逻辑结束 -------------------

        print("步骤7: 提交预约...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='提交预约']"))).click()
        print("场地选择完成，已提交预约。")

    except TimeoutException:
        print("\n!!!!!!!!!!!!!!!!!! 脚本超时 !!!!!!!!!!!!!!!!!!!")
        print(" -> 错误：在日志中**最后一条'步骤X' print语句**之后的操作上等待超时。")

        # 发生错误时自动截图，方便调试
        try:
            error_screenshot_path = f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
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
        # 点击"同行人"标签
        wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='同行人']"))).click()

        for companion_id in companions_id:
            # 点击"添加同行人"按钮
            wait.until(EC.visibility_of_element_located((By.XPATH, "//button[text()='添加同行人']"))).click()

            # 等待弹窗出现并输入学号
            search_input = wait.until(EC.visibility_of_element_located((By.ID, "searchId")))
            search_input.send_keys(companion_id)
            driver.find_element(By.XPATH, "//div[text()='查询']").click()

            # 等待并点击确定
            wait.until(EC.visibility_of_element_located((By.XPATH, "//button[text()='确定']"))).click()
            print(f"已添加同行人：{companion_id}")

        # 关闭同行人弹窗
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
        # 点击"未支付"
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


def load_config(config_path="information.txt"):
    """从 information.txt 文件读取配置"""
    if not os.path.exists(config_path):
        print(f"错误：找不到配置文件 {config_path}。请确保它和脚本在同一目录下。")
        return None

    config = {}
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
            except ValueError:
                print(f"警告：配置文件中格式错误的一行将被忽略: {line}")

    # 特殊处理同行人ID列表
    companions_str = config.get("companions_id", "")
    config["companions_id"] = [id.strip() for id in companions_str.split(",") if id.strip()]

    print("--- 配置加载成功 ---")
    for key, value in config.items():
        if 'password' in key.lower():
            print(f"{key}: {'*' * len(str(value))}")
        else:
            print(f"{key}: {value}")
    print("--------------------")

    return config


def initialize_driver():
    """初始化 WebDriver (自动寻找相对路径下的驱动和浏览器)"""
    global driver
    try:
        # 1. 获取脚本所在的目录
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 2. 拼接出 chromedriver 和 chrome 的相对路径
        chromedriver_path = os.path.join(script_dir, 'chromedriver-win64', 'chromedriver.exe')
        chrome_binary_path = os.path.join(script_dir, 'chrome-win64', 'chrome.exe')

        print(f"正在使用驱动: {chromedriver_path}")
        print(f"正在使用浏览器: {chrome_binary_path}")

        # 3. 检查文件是否存在
        if not os.path.exists(chromedriver_path):
            print(f"错误：在指定路径下找不到 chromedriver.exe。请检查 'chromedriver-win64' 文件夹。")
            return False
        if not os.path.exists(chrome_binary_path):
            print(f"错误：在指定路径下找不到 chrome.exe。请检查 'chrome-win64' 文件夹。")
            return False

        service = Service(executable_path=chromedriver_path)
        options = Options()

        # 4. 明确告诉 Selenium 浏览器本体的位置
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

    # 1. 设置时间
    ACTION_TIME_STR = "12:30:00"
    ACTION_TIME = datetime.strptime(ACTION_TIME_STR, "%H:%M:%S").time()

    # 你可自行调整提前的秒数，这里设置为提前90秒
    PRE_LOGIN_SECONDS = 11190
    PRE_LOGIN_TIME = (datetime.strptime(ACTION_TIME_STR, "%H:%M:%S") - timedelta(seconds=PRE_LOGIN_SECONDS)).time()

    print(f"脚本已启动。")
    print(f"将在 {PRE_LOGIN_TIME} 自动登录。")
    print(f"将在 {ACTION_TIME} 自动抢票。")

    # 2. 阶段一：等待"预登录时间"
    while True:
        now_time = datetime.now().time()
        if now_time >= PRE_LOGIN_TIME:
            print(f"时间到达 {PRE_LOGIN_TIME}，开始预登录...")
            break
        time.sleep(1)  # 每秒检查一次

    # 3. 阶段二：执行登录
    if not initialize_driver():
        return  # WebDriver启动失败，退出

    try:
        login(config["学号"], config["登录密码"])

        # 4. 阶段三：等待"抢票执行时间"
        print(f"登录成功，等待到达 {ACTION_TIME} 开始抢票...")
        while True:
            now_time = datetime.now().time()
            if now_time >= ACTION_TIME:
                print(f"时间到达 {ACTION_TIME}！开始执行抢票流程...")
                break
            time.sleep(0.5)  # 高精度等待

        # 5. 阶段四：执行抢票
        select_venue(config["校区"], config["球类"], config["预约时间"], config["预约场馆"])
        add_companions(config["同行人"])
        pay(config["支付密码"])

        print('预约并支付成功！请登录eHall查看确认。')
        time.sleep(10)  # 留出时间查看结果

    except Exception as e:
        print(f"脚本运行出错: {e}")
    finally:
        if driver:
            driver.quit()
            print("浏览器已关闭。")


if __name__ == "__main__":
    # 加载配置
    config = load_config("information.txt")

    # 仅在配置加载成功时运行主程序
    if config:
        run_grabbing_process(config)

    print("任务执行完毕，程序退出。")
    print("github项目发布地址：https://github.com/9900ff/SZU-badminton-GO")

    sys.exit()