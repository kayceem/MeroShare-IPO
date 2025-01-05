from sys import exit
import os
from time import sleep, perf_counter
from threading import RLock
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from cryptography.fernet import Fernet
from os.path import dirname as up

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from pathlib import Path
import logging
from chrome_helper import setup_chrome_and_driver

logging.basicConfig(
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s - %(module)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("results.log", mode="w"), logging.StreamHandler()],
)
logging.getLogger("selenium").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

log = logging.getLogger(__name__)

DIR_PATH = Path(__file__).parent
BINARY_PATH = DIR_PATH / "chrome/chrome"
DRIVER_PATH = DIR_PATH / "chrome/chromedriver"
key = ""
USER = []
results = {}


def update_file():
    filename = f"{DIR_PATH}/Results/IPO_Results.txt"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w", encoding="utf-8") as fp:
        if not len(results):
            fp.write(": No Result")
            fp.write("\n")
            fp.write("-" * 30)
            fp.write("\n\n")
            return

        # Wrtitng the applied shares to the file
        for name, result in results.items():
            fp.write(name)
            fp.write("\n")
            fp.write("-" * 60)
            fp.write("\n")
            for res in result:
                fp.write(res[0] + "\n" + res[1] + "\n" + res[2] + "\n")
                fp.write("-" * 60)
                fp.write("\n")
            fp.write("\n\n")
            fp.write("*" * 60)
            fp.write("\n\n")
    return


def check_result(browser, info, NAME):
    for index, data in enumerate(info):
        name = data[1]
        try:
            WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, f"(//button[@type='button'])[{index+6}]"))).click()
        except:
            continue
        sleep(1)
        loop = 0
        while True:
            try:
                status = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, "(//div[@class='row'])[10]")))
                break
            except:
                if loop > 3:
                    break
                browser.refresh()
                loop += 1
        remarks = browser.find_element(By.XPATH, f"(//div[@class='row'])[11]")
        remarks = remarks.text.replace("\n", " :: ")
        status = status.text.replace("\n", " :: ")
        if name in results.keys():
            results[name].append([NAME, status, remarks])
        else:
            results[name] = [[NAME, status, remarks]]
        browser.find_element(By.XPATH,"/html/body/app-dashboard/div/main/div/app-application-report/div/div[1]/div/div[1]/div/div/div/button",).click()
    return


def get_companies(browser, lock, NAME):
    info = []
    # Navigating to ABSA
    browser.get("https://meroshare.cdsc.com.np/#/asba")
    try:
        WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div/button"))
        ).click()
        with lock:
            log.debug(f"User was unauthorized  {NAME}")
        return "not_authorized"
    except:
        pass

    track = 1
    while True:
        WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, "//main[@id='main']//li[3]//a[1]"))).click()
        if track == 4:
            with lock:
                log.debug(f"No Comapnies available/loaded  {NAME} ")
            return False
        # Getting all the companies from Apply Issue
        try:
            WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "company-list")))
            # gets lists of web element
            shares_available = browser.find_elements(By.CLASS_NAME, "company-list")
            with lock:
                log.debug(f"Got Companies for {NAME} ")
            break
        except:
            with lock:
                log.debug(f"Tried to get Companies for {NAME} ({track})")
            browser.get("https://meroshare.cdsc.com.np/#/asba")
            sleep(2 + track)
            track += 1
    # Storing all the information of comapnies from the web elements as list in a list : info
    for shares in shares_available:
        info.append(shares.text.split("\n"))
        if len(info) == 5:
            break
    return info


def login(browser, DP, USERNAME, PASSWD):
    try:
        # Dp drop down menu
        WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "selectBranch"))).click()
        # Dp feild
        dp = browser.find_element(By.XPATH, "/html/body/span/span/span[1]/input")
        dp.send_keys(f"{DP}")
        dp.send_keys(Keys.RETURN)
    except:
        return False

    # Username filed
    username = browser.find_element(By.ID, "username")
    username.send_keys(f"{USERNAME}")

    fer = Fernet(key)
    pass_word = fer.decrypt(PASSWD.encode()).decode()
    # Password feild
    passwd = browser.find_element(By.ID, "password")
    passwd.send_keys(f"{pass_word}")
    sleep(0.5)
    # Login button
    LOGIN = browser.find_element(By.XPATH,"/html/body/app-login/div/div/div/div/div/div/div[1]/div/form/div/div[4]/div/button",)
    LOGIN.click()
    sleep(0.5)
    try:
        WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div/button"))).click()
        return False
    except:
        if browser.current_url == "https://meroshare.cdsc.com.np/#/dashboard":
            return True
        return False


def create_browser(user, lock):
    NAME, DP, USERNAME, PASSWD, _, _, _ = user
    try:
        ser = Service(str(DRIVER_PATH))
        option = Options()
        option.binary_location = str(BINARY_PATH)
        option.use_chromium = True
        option.add_argument("headless")
        option.add_experimental_option("excludeSwitches", ["enable-logging"])
        option.add_argument("--disable-extensions")
        option.add_argument("--disable-gpu")
        option.add_argument("start-maximized")
        option.add_argument("--disable-inforbars")
        option.add_argument("--no-sandbox")
        option.add_argument("dom.disable_beforeunload=true")
        option.add_argument("--log-level=3")
        browser = webdriver.Chrome(service=ser, options=option)
    except Exception as e:
        print(e)
        return False

    with lock:
        log.debug(f"Starting for user {NAME} ")

    while True:
        try:
            browser.get("https://meroshare.cdsc.com.np/#/login")
            with lock:
                log.debug(f"Connection established for user {NAME} ")
            sleep(0.5)
        except:
            with lock:
                log.debug(f"Connection failed for user {NAME} ")
            continue
        try:
            check = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "username")))
            break
        except:
            with lock:
                log.debug(f"Site didnot load {NAME} !!!  ")

    login_failed = 1
    while True:
        while True:
            if login_failed > 4:
                login_failed = True
                break
            try:
                #  Calling the login function
                logged_in = login(browser, DP, USERNAME, PASSWD)

                if not logged_in:
                    raise Exception

                with lock:
                    log.debug(f"Logged in for {NAME} ")
                login_failed = False
                break
            except:
                browser.get_screenshot_as_file(f"Errors/{NAME.lower()}_{login_failed}.png")
                browser.get("https://meroshare.cdsc.com.np/#/login")
                login_failed += 1
                with lock:
                    log.debug(f"Problem Logging in {NAME}")

        if login_failed:
            companies_available = False
            break
        #  Checks if comapnies data are available
        companies_available = get_companies(browser, lock, NAME)
        if companies_available == "not_authorized":
            browser.get("https://meroshare.cdsc.com.np/#/login")
            continue
        break

    if not companies_available:
        with lock:
            log.debug(f"Exited for user {NAME}")

        browser.quit()
        return False

    #  Check result available companies
    with lock:
        log.debug(f"Checking results for {NAME}")
    check_result(browser, companies_available, NAME)
    with lock:
        update_file()

    # Quiting the browser
    with lock:
        log.debug(f"Completed for user {NAME} ")
        print(f"Completed for user {NAME} ")
    browser.quit()
    return True


def main():
    user_data = []
    thread_list = []
    lock = RLock()
    path = f"{DIR_PATH}/Results"
    try:
        os.remove(f"{path}/IPO_Results.txt")
        os.remove(f"{path}/logs.txt")
    except:
        pass
    WAIT_TIME = 3

    # Checks for key in key.key
    try:
        with open(f"{DIR_PATH}/Source Files/key.key", "r", encoding="utf-8") as fp:
            global key
            key = fp.read()
            key = key.encode()
    except:
        log.debug(f"No key Found! ")
        return
    # Checks for database
    try:
        with open(f"{DIR_PATH}/Source Files/dataBase.txt", "r", encoding="utf-8") as fp:
            lines = fp.read().splitlines()
            for line in lines:
                data = line.split(",")
                if len(data) != 7:
                    continue
                user_data.append(data)
                USER.append(data[0])
    except:
        log.debug(f"Data Base not found! ")
        return

    start_time = perf_counter()
    executor = ThreadPoolExecutor()
    for user in user_data:
        executor.submit(create_browser, user, lock)
        sleep(WAIT_TIME)

    executor.shutdown()
    end_time = perf_counter()

    time_delta = end_time - start_time
    minutes, seconds = divmod(time_delta, 60)
    with lock:
        log.debug(f"Completed :: {minutes:.0f} minutes | {seconds:.1f} seconds")

    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        input("Interrupted!!!")
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
