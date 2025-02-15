from collections import defaultdict
from sys import exit
import os
from threading import RLock
from time import sleep, perf_counter
from concurrent.futures import ThreadPoolExecutor
from cryptography.fernet import Fernet

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from database.database import  get_db
from database.models import  Result, User
from utils.utils import create_browser, get_dir_path, get_logger
from dotenv import load_dotenv

load_dotenv()
log = get_logger('edis')
DIR_PATH = get_dir_path()

def check_for_edis(browser, lock, NAME):
    info = []
    # Navigating to ABSA
    browser.get("https://meroshare.cdsc.com.np/#/purchase")
    try:
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="script"]'))
        ).click()
        WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, "/html/body/app-dashboard/div/main/div/app-my-purchase/div/div[1]/div/div/ul/li[2]/a"))).click()
        with lock:
            log.debug(f"User was unauthorized  {NAME}")
        return "not_authorized"
    except:
        pass

    for attempt in range(1,5):
        pass
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

    # Password feild
    passwd = browser.find_element(By.ID, "password")
    passwd.send_keys(f"{PASSWD}")
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

def start(user, lock):
    NAME, DP, USERNAME, PASSWD, _, _, _ = user
    with create_browser() as browser:

        log.info(f"Starting for user {NAME} ")
        for attempt in range(4):
            try:
                browser.get("https://meroshare.cdsc.com.np/#/login")
                with lock:
                    log.info(f"Connection established for user {NAME} ")
                sleep(0.5)
                WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "username")))
                break
            except Exception as e:
                with lock:
                    log.info(f"Connection attempt {attempt + 1} failed for user {NAME}: {e}")
                if attempt == 3:
                    with lock:
                        log.info(f"Connection could not be established for user {NAME} after 4 attempts")
                    return False

        for attempt in range(4):
            try:
                logged_in = login(browser, DP, USERNAME, PASSWD)
                if not logged_in:
                    raise Exception
                with lock:
                    log.info(f"Logged in for {NAME} ")
                break
            except:
                browser.get_screenshot_as_file(f"Errors/{NAME.lower()}_{login_failed}.png")
                browser.get("https://meroshare.cdsc.com.np/#/login")
                login_failed += 1
                with lock:
                    log.info(f"Problem Logging in {NAME}")

        if not logged_in:
            return False
        is_edis_available = check_for_edis(browser, lock, NAME)

        with lock:
            log.info(f"Completed for user {NAME} ")
        return True


def main():
    lock = RLock()

    key = os.getenv("KEY")
    if not key:
        print("Key not found")
        return
    fernet = Fernet(key)
    with get_db() as db:
        name = input("Enter user: ")
        user = db.query(User).filter(User.name == name).first()
        if not user:
            print("User not found")
            return

        
    start_time = perf_counter()
    executor = ThreadPoolExecutor()
    executor.submit(start, user, lock)
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
