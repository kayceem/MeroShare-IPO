from time import sleep
import os
from os.path import dirname as up
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DIR_PATH = os.getcwd()
DRIVER_PATH = up(up(DIR_PATH))
PATH = f"{DRIVER_PATH}\Driver\msedgedriver.exe"
WEBSITE = 'NepaliPaisa'
        
def main(start_file=True):
    data =[]
    # Opening edge driver
    ser = Service(PATH)
    option = Options()
    option.use_chromium = True
    option.add_argument('headless')
    option.add_experimental_option('excludeSwitches', ['enable-logging'])
    option.add_argument('--disable-extensions')
    browser = webdriver.Edge(service= ser,options = option)
    try:
        # browser.get('https://nepsealpha.com/investment-calandar/ipo')
        browser.get('https://www.nepalipaisa.com/ipo')
        print(f'{WEBSITE} :: Request successful!')
    except:
        print(f'{WEBSITE} :: Request failed!')
        return
    # while True:
    #     try:
    #         browser.implicitly_wait(5)
    #         # WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "selectBank")))
    #         option = Select(browser.find_element(By.XPATH, '/html/body/div[1]/div[3]/div[2]/div/div[2]/div/div/div/div/div[1]/label/select'))
    #         option.select_by_value('25')
    #         print(f'{WEBSITE} :: 25 items expanded!')
    #         break
    #     except:
    #         print(f'{WEBSITE} :: Expand failed!')
    #         pass
    # sleep(1)

    count = 1
    while True:
        try:
            # browser.implicitly_wait(5)
            WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "tblIpo")))
            table_body = (browser.find_element(By.XPATH, '/html/body/section[1]/div/div/div/div/div/div/div[3]/div/div/div[1]/table'))
            break
        except:
            browser.get(browser.current_url)
            count += 1
            print(f'{WEBSITE} :: Could not load ipo table ({count})')
            if count > 3:
                print(f'{WEBSITE} :: Exited')
                return
    rows = table_body.find_elements(By.TAG_NAME, "tr")

    for row in rows:
        if start_file:
            print(f'{WEBSITE} :: Fetching data')
        col = row.find_elements(By.TAG_NAME, "td")
        if len(col) != 8:
            continue
        if  not 'Ordinary' in col[1].text or 'Closed' in col[6].text:
            continue
        # name, quantity, opening_date, closing_date, _, status = col[0].text , col[1].text , col[2].text , col[3].text , col[4].text , col[5].text
        # data.append([name,quantity,opening_date,closing_date,status])
        name, share_type, quantity, opening_date, closing_date, _, status= col[0].text , col[1].text , col[2].text , col[3].text , col[4].text , col[5].text, col[6].text
        data.append([name,quantity,opening_date,closing_date,status])
    print(f'{WEBSITE} :: Fetch success!')

    file_path = fr"{DIR_PATH}\\Results\\Upcoming IPO.txt"
    with open(file_path, "w") as fp:
        print('PC :: Writing data')
        for item in data:
            name,quantity,opening_date,closing_date,status = item
            fp.write(f"{name} | {quantity} | {opening_date} | {closing_date} | {status}")
            fp.write('\n\n')
    print('PC :: Write success!')
    if start_file:
        os.startfile(file_path)
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted!")
        exit(1)
            
    