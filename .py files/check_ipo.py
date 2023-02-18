from time import sleep
import os
from os.path import dirname as up
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

DIR_PATH = os.getcwd()
DRIVER_PATH = up(up(DIR_PATH))
PATH = f"{DRIVER_PATH}\Driver\msedgedriver.exe"

        
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
        browser.get('https://nepsealpha.com/investment-calandar/ipo')
        print('NEPSEALPHA :: Request successful!')
    except:
        print('NEPSEALPHA :: Request failed!')
        return
    while True:
        try:
            browser.implicitly_wait(5)
            option = Select(browser.find_element(By.XPATH, '/html/body/div[1]/div[3]/div[2]/div/div[2]/div/div/div/div/div[1]/label/select'))
            option.select_by_value('25')
            print('NEPSEALPHA :: 25 items expanded!')
            break
        except:
            print('NEPSEALPHA :: Expand failed!')
            pass
    sleep(1)

    table_body = (browser.find_element(By.XPATH, '/html/body/div[1]/div[3]/div[2]/div/div[2]/div/div/div/div/div[4]/table/tbody'))
        
    rows = table_body.find_elements(By.TAG_NAME, "tr")

    for row in rows:
        if start_file:
            print('NEPSEALPHA :: Fetching data')
        col = row.find_elements(By.TAG_NAME, "td")
        if 'Local' in col[0].text or 'Closed' in col[5].text:
            continue
        name, quantity, opening_date, closing_date, _, status = col[0].text , col[1].text , col[2].text , col[3].text , col[4].text , col[5].text
        data.append([name,quantity,opening_date,closing_date,status])
    print('NEPSEALPHA :: Fetch success!')

    file_path = fr"{DIR_PATH}\\Results\\Upcoming IPO.txt"
    with open(file_path, "w") as fp:
        print('PC :: Writing data')
        for item in data:
            name,quantity,opening_date,closing_date,status = item
            if name.split('(')[1] != "Public)":
                continue
            fp.write(f"{name} | {quantity} | {opening_date} | {closing_date} | {status}")
            fp.write('\n\n')
    print('PC :: Write success!')
    if start_file:
        os.startfile(file_path)
if __name__ == '__main__':
    main()
            
    