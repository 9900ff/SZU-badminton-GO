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
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException

# 将脚本当前所在的目录添加到 Python 的模块搜索路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from web_server import ConfigServer

# --- 全局变量 ---
NEXT_DAY = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
driver = None
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PAGE_URL = 'https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do#/sportVenue'


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
        # 登录后等待页面跳转到主页
        WebDriverWait(driver, 15).until(EC.url_contains("sportVenue"))
    except TimeoutException:
        print("登录超时或失败，请检查网页是否能正常访问或账号密码是否正确。")
        if driver: driver.quit()
        sys.exit(1)


def find_and_click_available_court(config, preferred_court=None):
    """在当前页面寻找并点击一个可预约的场地，返回场地信息字符串或None"""
    try:
        # 等待场地状态（无论是哪种）加载出来
        wait = WebDriverWait(driver, 10)  # 延长等待时间
        wait.until(EC.presence_of_element_located(
            (By.XPATH,
             "//div[@class='group-2']//div[contains(text(), '可预约') or contains(text(), '已满员') or contains(text(), '体育课占用')]")
        ))

        # 确认可预约场地已加载后，再获取所有场地元素
        group_2_elements = driver.find_elements(By.CLASS_NAME, 'group-2')

        # --- 第一优先级，尝试粘性场地 ---
        if preferred_court:
            print(f" -> 优先尝试粘性场地: {preferred_court}")
            for group_2 in group_2_elements:
                element = group_2.find_element(By.CLASS_NAME, 'element')
                element_text = element.text
                if preferred_court in element_text and '可预约' in element_text:
                    group_2.find_element(By.CLASS_NAME, 'frame-child1').click()
                    print(f" -> 成功锁定【粘性】场地：{element_text}")
                    return element_text
            print(f" -> 粘性场地 {preferred_court} 不可用，开始随机查找...")

        # --- 第二优先级，随机查找热门场地 ---
        if config["campus"] == "粤海校区":
            priority_courts = ['C5', 'C6', 'C7', 'C8', 'C4', 'C3', 'C2', 'C1', 'B5', 'B6', 'B7', 'B8', 'B4', 'B3', 'B2',
                               'B1', 'D5', 'D6', 'D7', 'D8', 'D4', 'D3', 'D2', 'D1', 'A5', 'A6', 'A7', 'A8', 'A4', 'A3',
                               'A2', 'A1']
        else:
            priority_courts = ['1号', '2号', '3号', '4号', '5号', '6号', '7号', '8号', '9号', '10号', '11号', '12号']
        random.shuffle(priority_courts)

        for court_name in priority_courts:
            for group_2 in group_2_elements:
                element = group_2.find_element(By.CLASS_NAME, 'element')
                element_text = element.text
                if court_name in element_text and '可预约' in element_text:
                    group_2.find_element(By.CLASS_NAME, 'frame-child1').click()
                    print(f" -> 成功选择一个【随机优先】场地：{element_text}")
                    return element_text

        # --- 第三优先级，选择任意备选场地 ---
        for group_2 in group_2_elements:
            element = group_2.find_element(By.CLASS_NAME, 'element')
            element_text = element.text
            if '可预约' in element_text and '场' in element_text:
                group_2.find_element(By.CLASS_NAME, 'frame-child1').click()
                print(f" -> 成功选择一个【备选】场地：{element_text}")
                return element_text

        return None
    except TimeoutException:
        # 如果10秒内都找不到任何一个场地状态，才返回None
        return None


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
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except Exception as e:
        print(f"支付时发生错误: {e}")
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])


def initialize_driver():
    """初始化 WebDriver"""
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
    """接管浏览器，执行抢票的主流程 (时间优先，粘性场地)"""
    global driver
    ACTION_TIME_STR = "12:30:00"
    ACTION_TIME = datetime.strptime(ACTION_TIME_STR, "%H:%M:%S").time()

    appointments_to_try = [t.strip() for t in config.get('appointment', '').split(',') if t.strip()]
    venues_to_try = [v.strip() for v in config.get('venues', '').split(',') if v.strip()]

    if not appointments_to_try or not venues_to_try:
        print("错误：未选择任何预约时间或场馆，程序退出。")
        return

    try:
        # 登录流程
        url = 'https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do'
        print(f"\n配置完成，正在导航到深大登录页: {url}")
        driver.get(url)
        if config.get("username") and config.get("password"):
            login(config["username"], config["password"])
        else:
            print("\n!!! 请在当前浏览器中手动登录 !!!")
            try:
                WebDriverWait(driver, timeout=300).until(EC.url_contains("sportVenue"))
                print("✅ 检测到登录成功！")
            except TimeoutException:
                print("❌ 手动登录超时（5分钟），程序将退出。")
                return

        # 等待抢票时间
        print(f"\n登录流程完毕，等待到达 {ACTION_TIME} 开始抢票...")
        while True:
            now_time = datetime.now().time()
            if now_time >= ACTION_TIME:
                sys.stdout.write("\r" + " " * 80 + "\r")
                break
            if (datetime.combine(datetime.min, ACTION_TIME) - datetime.combine(datetime.min,
                                                                               now_time)).total_seconds() <= 10:
                sys.stdout.write(f"\r进入最后 10 秒倒计时，高频检查中...")
                time.sleep(0.01)
            else:
                sys.stdout.write(f"\r当前时间: {now_time.strftime('%H:%M:%S')}, 等待中...")
                time.sleep(1)

        # 时间优先，粘性场地循环
        driver.get(MAIN_PAGE_URL)
        print("页面刷新完毕，开始按时间优先，粘性场地策略抢票...")

        successful_bookings = {}
        failed_bookings = []
        preferred_court = None  # 粘性场地

        # 外层循环是时间
        for appointment in appointments_to_try:
            print(f"\n=========== 开始任务: [时间] {appointment.replace('(可预约)', '')} ===========")
            task_successful = False

            # 内层循环是场馆
            for venue in venues_to_try:
                print(f"--- 正在尝试场馆: {venue} ---")

                # 为每个场馆尝试增加重试循环
                for attempt in range(3):  # 最多重试3次
                    try:
                        if attempt > 0:
                            print(f" -> 正在进行第 {attempt + 1}/3 次重试...")
                            driver.get("about:blank")
                            driver.get(MAIN_PAGE_URL)


                        wait = WebDriverWait(driver, 20)  # 延长整体等待时间
                        wait.until(
                            EC.element_to_be_clickable((By.XPATH, f"//div[text()='{config['campus']}']"))).click()
                        time.sleep(0.1)
                        wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[text()='{config['ball']}']"))).click()
                        time.sleep(0.1)
                        wait.until(EC.element_to_be_clickable((By.XPATH, f"//label[@for='{NEXT_DAY}']"))).click()
                        time.sleep(0.1)
                        wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[text()='{appointment}']"))).click()
                        time.sleep(0.1)
                        wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[text()='{venue}']"))).click()
                        time.sleep(0.1)

                        court_info = find_and_click_available_court(config, preferred_court)
                        if court_info:
                            WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[text()='提交预约']"))).click()

                            print(" -> 正在等待预约确认页面...")
                            WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.XPATH, "//a[text()='同行人']")))
                            print("✅ 成功提交预约！")

                            successful_bookings[appointment] = (venue, court_info)
                            preferred_court = court_info.split('(')[0].strip()
                            task_successful = True

                            add_companions(config.get("companions_id", []))
                            pay(config["payment_password"])
                        else:
                            print("  -> 该场馆下无可用场地。")

                        break

                    except (StaleElementReferenceException, TimeoutException) as e:
                        print(f" -> 点击操作失败或超时: {type(e).__name__}")
                        if attempt == 2:
                            print(" -> 重试3次后仍然失败，放弃该场馆。")

                if task_successful:
                    break

            if not task_successful:
                failed_bookings.append(appointment)

            print("...当前时间段任务结束，返回主页...")

            driver.get("about:blank")
            driver.get(MAIN_PAGE_URL)
            time.sleep(1)

        # 打印最终总结
        print("\n" + "=" * 25 + " 抢票总结 " + "=" * 25)
        if successful_bookings:
            driver.get("https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do#/myBooking")
            print("✅ 成功预约的时间段和场地:")
            for appointment in appointments_to_try:
                if appointment in successful_bookings:
                    venue, court = successful_bookings[appointment]
                    print(f"   - {appointment.replace('(可预约)', '')} @ {venue} ({court.split('(')[0].strip()})")
        else:
            print("...本次未能成功预约任何场地...")

        if failed_bookings:
            print("\n❌ 未能成功预约的时间段:")
            for item in failed_bookings:
                print(f"   - {item.replace('(可预约)', '')}")
        print("=" * 60)


    except KeyError as e:
        print(f"\n!!!!!!!!!! 配置错误 !!!!!!!!!!\n脚本在配置中找不到必要的信息: {e}\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
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
    return config


if __name__ == "__main__":
    print("=" * 60 + "\n" + " " * 20 + "深大抢场助手 - 安全提示" + "\n" + "=" * 60)
    print(" > 本项目完全开源，源程序全部公开可查，不保存任何用户数据。")
    print(" > 为防止在传播过程被恶意修改，【推荐选择手动登录】。")
    print(" > 请保护好自己的密码！！")
    print("\n > 请从唯一github发布地址下载本程序：")
    print(" > https://github.com/9900ff/SZU-badminton-GO" + "\n" + "=" * 60 + "\n")
    time.sleep(3)

    config_complete_event = threading.Event()
    config_server = ConfigServer(completion_event=config_complete_event)
    config_server.start()
    time.sleep(1)

    if not initialize_driver():
        sys.exit(1)

    try:
        config_url = "http://127.0.0.1:8088"
        print(f"请在打开的浏览器窗口中完成配置: {config_url}")
        driver.get(config_url)
        config_complete_event.wait()

        latest_config = load_config_from_file()
        if not latest_config:
            raise Exception("无法加载配置，程序终止。")

        run_grabbing_process(latest_config)

        print("\n----------------------------------------------------")
        print("所有任务已执行完毕！浏览器将保持打开状态以便你查看结果。")
        input(">>> 按 Enter 键关闭浏览器并退出... <<<")

    except WebDriverException:
        print("浏览器窗口被手动关闭，程序退出。")
    except Exception as e:
        print(f"主程序发生未知错误: {e}")
    finally:
        if driver:
            driver.quit()
            print("浏览器已关闭。")

    print("\n程序已退出。")
    os._exit(0)

