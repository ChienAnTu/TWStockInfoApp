"""
@File: stock_crawler
@Date: 13/02/2025
@Author: Chris Tu
@Version: 1.0
@Description: 
"""
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime

# Initialize logging
logging.basicConfig(filename='crawler.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_stock_data(url):
    options = Options()
    # options.headless = True
    # options.add_argument("--headless")  # 啟用無頭模式
    options.add_argument("--headless=new")  # 啟用無頭模式 for Chrome >= 109
    # options.add_argument("--disable-gpu")  # 在某些系統上需要禁用 GPU 來避免錯誤
    # options.add_argument("--window-size=1920x1080")  # 設定視窗大小（避免某些網站元素載入問題）
    # options.add_argument("--no-sandbox")  # 避免在某些環境中發生權限錯誤
    # options.add_argument("--disable-dev-shm-usage")  # 避免 /dev/shm 空間不足的錯誤
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        logging.info(f"訪問 {url}")
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.ID, 'Details')))
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        table = soup.find('table', {'id': 'Details'})
        if not table:
            logging.warning("未找到表格，請確認股票代碼是否輸入正確")
            return None

        rows = table.find_all('tr')
        data = [
            [cell.text.strip() for cell in row.find_all('td')]
            for row in rows if len(row.find_all('td')) >= 16
        ]

        # Assume the first row is headers
        columns = data.pop(0)
        dataframe = pd.DataFrame(data, columns=columns)
        # Remove empty columns if any
        dataframe = dataframe.loc[:, dataframe.columns.str.strip() != '']

        logging.info("數據提取並清理成功")
        return dataframe

    except Exception as e:
        logging.error(f"錯誤: {e}")
        return None
    finally:
        driver.quit()


def update_master_file(code, today_filename):
    """ 讀取今天的 CSV，再合併到 master file，並刪除重複資料 """

    # Create master directory(if not exists)
    master_dir = "master"
    os.makedirs(master_dir, exist_ok=True)

    # 定義 master file
    master_file = os.path.join(master_dir, code + ".csv")

    # 確保 today_filename 存在
    if not os.path.exists(today_filename):
        print(f"錯誤: {today_filename} 不存在，無法更新 master file")
        return

    # 讀取今天的數據
    df = pd.read_csv(today_filename, encoding='utf-8-sig')

    # 讀取 master_file，如果不存在則建立空的 DataFrame
    if os.path.exists(master_file):
        master_df = pd.read_csv(master_file, encoding='utf-8-sig')
    else:
        master_df = pd.DataFrame()

    # 合併數據
    combined_df = pd.concat([master_df, df], ignore_index=True)

    # 確保第一列沒有 NaN
    first_col = combined_df.columns[0]

    # 移除重複資料
    combined_df.drop_duplicates(subset=[first_col], keep='first', inplace=True)

    # Sorting based on 資料日期
    combined_df = combined_df.sort_values(by=first_col, ascending=False)

    # 儲存合併後的 master file
    combined_df.to_csv(master_file, index=False, encoding='utf-8-sig')
    print(f"Updated master file {master_file}")


# 主程式
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python stock_crawler.py <stock code>")
        sys.exit(1)

    code = sys.argv[1]
    url = f"https://norway.twsthr.info/StockHolders.aspx?stock={code}"
    date_str = datetime.today().strftime('%Y%m%d')

    # Create log_file directory(if not exists)
    log_dir = "log_file"
    os.makedirs(log_dir, exist_ok=True)

    # 取得股票數據
    df = fetch_stock_data(url)

    if df is not None:
        # 儲存當日資料
        today_filename = os.path.join(log_dir, f"{code}_{date_str}.csv")
        df.to_csv(today_filename, index=False, encoding='utf-8-sig')
        print(f"Saved today's data to {today_filename}")

        # 使用 CSV 檔案來更新 master file
        update_master_file(code, today_filename)
    else:
        print("未提取數據，請確認股票代碼是否輸入正確")