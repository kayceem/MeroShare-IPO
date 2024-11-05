#!/home/kayc/Code/Python/MeroShare-IPO/.venv/bin/python

import argparse
from sys import exit
import os
from time import sleep, perf_counter
from threading import RLock
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from cryptography.fernet import Fernet

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from pathlib import Path

from chrome_helper import setup_chrome_and_driver
# DRIVER_PATH = Path(DIR_PATH).parents[1]


DIR_PATH = Path(__file__).parent 
BINARY_PATH = DIR_PATH / "chrome/chrome"
DRIVER_PATH = DIR_PATH / "chrome/chromedriver"
key = ""
logs = []
USER = []
sorted_logs = []
DATA = []
# select_DP = {
#     '11500' : '171',
#     '17300' : '162',
#     '10400' : '164',
#     '13700' : '174',
#     '12600' : '179',
#     '11000' : '175',
# }
bank_id = {"11500": "49", "17300": "42", "10400": "37", "13700": "44", "12600": "48", "11000": "45"}


def display_logs(usr=[]):
    os.system("clear")
    temp = "--------------------------------------\n"
    filename = f"{DIR_PATH}/Results/logs.txt"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    if len(usr) == 1:
        USER.clear()
        USER.append(usr[0][0])
    # Sort logs
    for user in USER:
        for log in logs[:]:
            if not user in log:
                continue
            sorted_logs.append(log)
            logs.remove(log)
        sorted_logs.append(temp)

    # Write logs
    with open(filename, "w", encoding="utf-8") as fp:
        for log in sorted_logs:
            print()
            print(log)
            fp.write(log)
            fp.write("\n")
    return

def save_screenshot(browser, NAME, name, share_applied):
    filename = f"{DIR_PATH}/Results/{name}/{NAME}_{share_applied}.png"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    browser.get("https://meroshare.cdsc.com.np/#/asba")
    sleep(2)
    browser.save_screenshot(filename)
    return

def update_file(applied_shares, NAME="Default"):
    filename = f"{DIR_PATH}/Results/Results.txt"
    text = ""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        with open(filename, "r", encoding="utf-8") as fp:
            text = fp.read()
    except:
        pass

    # Create a file with with users name
    with open(filename, "w", encoding="utf-8") as fp:
        fp.write(text)
        # Logging date and time
        fp.write(str(datetime.now().strftime("%I:%M:%S")))
        fp.write("\n")
        fp.write(f"{NAME}")

        # If no shares to apply
        if len(applied_shares) == 0:
            fp.write(": No shares to apply")
            fp.write("\n")
            fp.write("-" * 30)
            fp.write("\n\n")
            return

        # Wrtitng the applied shares to the file
        for shares in applied_shares:
            name, _, _, ipo, share_type, button = shares
            temp = name + " | " + ipo + " | " + share_type + " | " + button + " | " + "\n"
            fp.write(f": {temp}")
        fp.write("-" * 30)
        fp.write("\n\n")
        return


def apply_share(browser, CRN, PIN, DP, ipo, ACCOUNT_NUMBER):
    try:
        check = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "selectBank")))
    except:
        return False
    """
    select_bank = browser.find_element(By.ID, "selectBank")
    select_bank.click()
    sleep(0.5)
    select_bank.send_keys(Keys.DOWN)
    select_bank.send_keys(Keys.DOWN)
    select_bank.send_keys(Keys.RETURN)
    """
    option = Select(browser.find_element(By.ID, "selectBank"))
    option.select_by_value(f"{bank_id[DP]}")
    sleep(0.5)
    option = Select(browser.find_element(By.ID, "accountNumber"))
    option.select_by_value(f"{ACCOUNT_NUMBER}")
    sleep(0.5)
    
    quantity = browser.find_element(By.ID, "appliedKitta")
    if ipo == "IPO" or ipo == "FPO":
        ########### Clearing the quantity if any ############
        browser.find_element(By.ID, "appliedKitta").clear()
        ############## DO NOT CHANGE THIS ###################
        QUANTITY = 10
        if QUANTITY != 10:
            QUANTITY = 10
        quantity.send_keys(f"{QUANTITY}")
        #####################################################
    text = quantity.get_attribute("value")

    # Entering CRN
    crn = browser.find_element(By.ID, "crnNumber")
    crn.clear()
    crn.send_keys(f"{CRN}")
    # Checking privacy policy and clicking on proceed button
    browser.find_element(By.ID, "disclaimer").click()
    try:
        browser.find_element(By.XPATH, "/html/body/app-dashboard/div/main/div/app-issue/div/wizard/div/wizard-step[1]/form/div[2]/div/div[5]/div[2]/div/button[1]").click()
    except:
        browser.find_element(By.XPATH, "/html/body/app-dashboard/div/main/div/app-re-apply/div/div/wizard/div/wizard-step[1]/form/div[2]/div/div[4]/div[2]/div/button[1]").click()
    sleep(1)

    fernet = Fernet(key)
    pin_number = (fernet.decrypt(PIN.encode())).decode()
    # Entering pin
    pin = WebDriverWait(browser, 2).until(EC.presence_of_element_located((By.ID, "transactionPIN")))
    pin.send_keys(f"{pin_number}")
    # breakpoint()

    # Clicking on apply button
    try:
        browser.find_element(By.XPATH, "/html/body/app-dashboard/div/main/div/app-issue/div/wizard/div/wizard-step[2]/div[2]/div/form/div[2]/div/div/div/button[1]").click()
    except:
        browser.find_element(By.XPATH, "/html/body/app-dashboard/div/main/div/app-re-apply/div/div/wizard/div/wizard-step[2]/div[2]/div/form/div[2]/div/div/div/button[1]").click()

    sleep(3)
    return int(text)


def check_to_apply(browser, user, info, lock):
    applied_shares = []
    quantities = []
    NAME, DP, _, _, CRN, PIN,ACCOUNT_NUMBER = user

    for index, data in enumerate(info):
        # Checking if there is a button
        try:
            name, _, _, ipo, share_type, button = data
        # If not continue to another share
        except:
            name = data[0]
            button = "No button"
            with lock:
                logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Already applied for {NAME} : {name} | {button} ")
                print(f"{datetime.now().strftime('%I:%M:%S')} :: Already applied for {NAME} : {name} | {button} ")

            continue
        if not share_type == "Ordinary Shares" and "Local" not in share_type:
            with lock:
                logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Not applied for {NAME} : {share_type} | {name}")
                print(f"{datetime.now().strftime('%I:%M:%S')} :: Not applied for {NAME} : {share_type} | {name}")

            continue

        if button == "Edit":
            with lock:
                logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Already applied for {NAME} : {name} : {button}")
                print(f"{datetime.now().strftime('%I:%M:%S')} :: Already applied for {NAME} : {name} : {button}")

            continue

        # Checking if the share is IPO | can be applied | and is not debenture
        if not (ipo == "IPO" or ipo == "FPO") and not ipo == "RESERVED (RIGHT SHARE)":
            continue
        if not (button == "Apply" or button == "Reapply"):
            continue

        try:
            browser.find_element(By.XPATH, f"/html/body/app-dashboard/div/main/div/app-asba/div/div[2]/app-applicable-issue/div/div/div/div/div[{index+1}]/div/div[2]/div/div[4]/button").click()
        except:
            browser.find_element(By.XPATH, f"/html/body/app-dashboard/div/main/div/app-asba/div/div[2]/app-applicable-issue/div/div/div/div/div[{index+1}]/div/div[2]/div/div[3]/button").click()
        track = 1
        #  Applying the share
        while True:
            if track == 4:
                break
            try:
                share_applied = apply_share(browser, CRN, PIN, DP, ipo, ACCOUNT_NUMBER)
                if not share_applied:
                    raise Exception

                save_screenshot(browser, NAME, name, share_applied)
                with lock:
                    logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Applied shares for {NAME} : {name} : {share_applied} shares")
                    print(f"{datetime.now().strftime('%I:%M:%S')} :: Applied shares for {NAME} : {name} : {share_applied} shares")

                quantities.append(share_applied)
                # Storing applied shares in a list
                applied_shares.append(data)
                break
            except:
                browser.get(browser.current_url)
                with lock:
                    logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Could not apply {NAME} : {name} ({track})")
                    print(f"{datetime.now().strftime('%I:%M:%S')} :: Could not apply {NAME} : {name} ({track})")
                track += 1
    # Writing the results to a file
    with lock:
        update_file(applied_shares, NAME)
    return


def check_for_companies(browser, lock, NAME):
    info = []
    track = 1

    # Navigating to ABSA
    browser.get("https://meroshare.cdsc.com.np/#/asba")
    try:
        WebDriverWait(browser, 2).until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div/button"))).click()
        with lock:
            logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: User was unauthorized  {NAME} ")
            print(f"{datetime.now().strftime('%I:%M:%S')} :: User was unauthorized  {NAME} ")

        return "not_authorized"
    except:
        pass

    while True:
        if track == 4:
            with lock:
                logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: No Comapnies available/loaded  {NAME} ")
                print(f"{datetime.now().strftime('%I:%M:%S')} :: No Comapnies available/loaded  {NAME} ")
            return False
        # Getting all the companies from Apply Issue
        try:
            WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "company-list")))
            # gets lists of web element
            shares_available = browser.find_elements(By.CLASS_NAME, "company-list")
            with lock:
                logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Got Companies for {NAME} ")
                print(f"{datetime.now().strftime('%I:%M:%S')} :: Got Companies for {NAME} ")
            break
        except:
            with lock:
                logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Tried to get Companies for {NAME} ({track})")
                print(f"{datetime.now().strftime('%I:%M:%S')} :: Tried to get Companies for {NAME} ({track})")
            browser.get("https://meroshare.cdsc.com.np/#/asba")
            sleep(2 + track)
            track += 1
    # Storing all the information of comapnies from the web elements as list in a list : info
    for shares in shares_available:
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

    fer = Fernet(key)
    pass_word = fer.decrypt(PASSWD.encode()).decode()
    # Password feild
    passwd = browser.find_element(By.ID, "password")
    passwd.send_keys(f"{pass_word}")
    sleep(0.5)
    # Login button
    LOGIN = browser.find_element(By.XPATH, "/html/body/app-login/div/div/div/div/div/div/div[1]/div/form/div/div[4]/div/button")
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
    # fernet = Fernet(key)
    # pin_number = (fernet.decrypt(PIN.encode())).decode()
    # breakpoint()
    # Opening edge driver
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
        logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Starting for user {NAME} ")
        print(f"{datetime.now().strftime('%I:%M:%S')} :: Starting for user {NAME} ")

    while True:
        try:
            browser.get("https://meroshare.cdsc.com.np/#/login")
            with lock:
                logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Connection established for user {NAME} ")
                print(f"{datetime.now().strftime('%I:%M:%S')} :: Connection established for user {NAME} ")
            sleep(0.5)
        except:
            with lock:
                logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Connection failed for user {NAME} ")
                print(f"{datetime.now().strftime('%I:%M:%S')} :: Connection failed for user {NAME} ")
            continue
        try:
            check = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "username")))
            break
        except:
            with lock:
                logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Site didnot load {NAME} !!!  ")
                print(f"{datetime.now().strftime('%I:%M:%S')} :: Site didnot load {NAME} !!!")

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
                    logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Logged in for {NAME} ")
                    print(f"{datetime.now().strftime('%I:%M:%S')} :: Logged in for {NAME} ")

                login_failed = False
                break
            except:
                browser.get_screenshot_as_file(f"Errors/{NAME.lower()}_{login_failed}.png")
                browser.get("https://meroshare.cdsc.com.np/#/login")
                login_failed += 1
                with lock:
                    logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Problem Logging in {NAME}")
                    print(f"{datetime.now().strftime('%I:%M:%S')} :: Problem Logging in {NAME}")

        if login_failed:
            companies_available = False
            break
        #  Checks if comapnies are available
        companies_available = check_for_companies(browser, lock, NAME)
        if companies_available == "not_authorized":
            browser.get("https://meroshare.cdsc.com.np/#/login")
            continue
        break

    if not companies_available:
        with lock:
            logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Exited for user {NAME}")
            print(f"{datetime.now().strftime('%I:%M:%S')} :: Exited for user {NAME}")

        return False

    #  Tries to apply available companies
    check_to_apply(browser, user, companies_available, lock)

    # Quiting the browser
    with lock:
        logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Completed for user {NAME} ")
        print(f"{datetime.now().strftime('%I:%M:%S')} :: Completed for user {NAME} ")
    browser.quit()
    return True


def main(default):
    if not BINARY_PATH.exists() or not DRIVER_PATH.exists():
        setup_chrome_and_driver()
        sleep(5)
        if not BINARY_PATH.exists() or not DRIVER_PATH.exists():
            return

    user_data = []
    temp = []
    thread_list = []
    lock = RLock()
    check = False
    path = DIR_PATH / "Results"
    # os.system("clear")
    try:
        os.remove(f"{path}/Results.txt")
        os.remove(f"{path}/logs.txt")
    except:
        pass
    SINGLE_USER = ""
    WAIT_TIME = 3
    if not default:
        #  Asks user for wait time
        try:
            WAIT_TIME = int(input("Enter wait time between each user: "))
            if WAIT_TIME < 3:
                WAIT_TIME = 3
            if WAIT_TIME > 10:
                WAIT_TIME = 10
        except:
            WAIT_TIME = 3

        # Asks is user wants to use only for single user
        SINGLE_USER = (input("Enter the user you want to apply: ")).upper()
        print()

    # Checks for key in key.key
    try:
        with open(f"{DIR_PATH}/Source Files/key.key", "r", encoding="utf-8") as fp:
            global key
            key = fp.read()
            key = key.encode()
    except:
        logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: No key Found! ")
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
        logs.append(f"{datetime.now().strftime('%I:%M:%S')} :: Data Base not found! ")
        return
    # Checks for single user
    for index, user in enumerate(user_data):
        if not user[0].upper() == SINGLE_USER:
            continue
        temp.append(user_data.pop(index))
        check = True
        break

    if check:
        user_data = temp
    DATA.append(user_data)

    start_time = perf_counter()
    executor = ThreadPoolExecutor()
    # print(executor._max_workers)
    # print(os.cpu_count())
    for user in user_data:
        executor.submit(create_browser, user, lock)
        # thread_list.append(executor.submit(create_browser, user, lock))
        sleep(WAIT_TIME)

    executor.shutdown()
    end_time = perf_counter()

    time_delta = end_time - start_time
    minutes, seconds = divmod(time_delta, 60)
    with lock:
        display_logs(user_data)
        print()
        print(f"Completed :: {minutes:.0f} minutes | {seconds:.1f} seconds")
        print()
        # if not default:
        #     input("Press Enter to Exit")
        #     os.startfile(f"{DIR_PATH}/Results/logs.txt")
        # if default:
        #     os.startfile(f"{DIR_PATH}/Results/Results.txt")

    return


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
        "--default",
        type=bool,
        default=False,
        help="Whether to use default values or not",
        )
        args = parser.parse_args()
        main(args.default)
    except KeyboardInterrupt:
        display_logs(DATA[0])
        input("Interrupted!!!")
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
