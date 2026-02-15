import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
COOKIES_FILE = "data/cookies.json"

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def wait_for_login(driver):
    driver.get("https://www.instagram.com/")
    print("\n" + "="*50)
    print("【操作のお願い】 ログインしてホーム画面を表示してください。")
    print("="*50 + "\n")
    while True:
        try:
            if driver.find_elements(By.CSS_SELECTOR, "svg[aria-label='ホーム'], svg[aria-label='Home']"):
                print("ログインを確認しました。")
                break
        except: pass
        time.sleep(2)

def main():
    driver = setup_driver()
    try:
        wait_for_login(driver)
        
        # Cookieを取得
        cookies = driver.get_cookies()
        
        # 重要なCookieがあるか確認
        session_id = next((c for c in cookies if c["name"] == "sessionid"), None)
        if session_id:
            with open(COOKIES_FILE, "w") as f:
                json.dump(cookies, f, indent=4)
            print(f"\n成功！Cookieを '{COOKIES_FILE}' に保存しました。")
            print(f"Session ID prefix: {session_id['value'][:10]}...")
        else:
            print("警告: 'sessionid' が見つかりませんでした。ログインが不完全な可能性があります。")

    finally:
        print("ブラウザを終了します。")
        driver.quit()

if __name__ == "__main__":
    main()
