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
log = get_logger('ipo-result')
DIR_PATH = get_dir_path()


def update_file(results):
    if len(results) == 0:
        return
    with get_db() as db:
        for name, result in results.items():
            entry = {"script": name}
            for res in result:
                entry[res[0]] = res[1].split('::')[1].strip() + " - " + res[2].split('::')[1].strip()
            existing_entry = db.query(Result).filter(Result.script == name).first()
            if existing_entry:
                for key, value in entry.items():
                    setattr(existing_entry, key, value)
            else:
                db.add(Result(**entry))
        db.commit()
    return


def check_result(browser, info, NAME, lock):
    results = defaultdict(list)
    for index, data in enumerate(info):
        name = data[1]
        try:
            WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, f"(//button[@type='button'])[{index+6}]"))).click()
        except:
            continue
        sleep(1)
        for _ in range(3):
            try:
                status = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, "(//div[@class='row'])[10]")))
                break
            except:
                browser.refresh()
        remarks = browser.find_element(By.XPATH, f"(//div[@class='row'])[11]")
        remarks = remarks.text.replace("\n", " :: ")
        status = status.text.replace("\n", " :: ")
        with lock:
            results[name].append([NAME, status, remarks])
        browser.find_element(By.XPATH,"/html/body/app-dashboard/div/main/div/app-application-report/div/div[1]/div/div[1]/div/div/div/button",).click()
    return results


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

    for attempt in range(1,5):
        WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, "//main[@id='main']//li[3]//a[1]"))).click()
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
                log.debug(f"Tried to get Companies for {NAME} ({attempt})")
            browser.get("https://meroshare.cdsc.com.np/#/asba")
            sleep(2 + attempt)
            if attempt == 4:
                log.debug(f"No Comapnies available/loaded  {NAME} ")
                return False
    # Storing all the information of comapnies from the web elements as list in a list : info
    for shares in shares_available[:5]:
        info.append(shares.text.split("\n"))
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

                # Checks for companies available
        if logged_in:
            companies_to_check = get_companies(browser, lock, NAME)
            if companies_to_check == "not_authorized":
                with lock:
                    log.info(f"User unauthorized {NAME}")
                return False

        if not companies_to_check:
            with lock:
                log.info(f"Exited for user {NAME}")
            return False

        #  Check result available companies
        with lock:
            log.debug(f"Checking results for {NAME}")

        results = check_result(browser, companies_to_check, NAME, lock)

        with lock:
            update_file(results)

        # Quiting the browser
        with lock:
            log.info(f"Completed for user {NAME} ")
        return True


def main():
    user_data = []
    lock = RLock()
    WAIT_TIME = 3

    key = os.getenv("KEY")
    if not key:
        print("Key not found")
        return
    fernet = Fernet(key)
    with get_db() as db:
        users = db.query(User).all()
        for user in users:
            if user.name != "m" and user.name != "p":
                continue
            user_data.append((user.name, user.dp, user.boid, (fernet.decrypt(user.passsword.encode())).decode(), user.crn, (fernet.decrypt(user.pin.encode())).decode(), user.account))

        
    start_time = perf_counter()
    executor = ThreadPoolExecutor()
    for user in user_data:
        executor.submit(start, user, lock)
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
