import time
import json
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
DATA_DIR = os.path.join(os.getcwd(), "data")
FOLLOWERS_FILE = os.path.join(DATA_DIR, "followers.json")

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
    print("Instagramにアクセス中...")
    driver.get("https://www.instagram.com/")
    print("\n" + "="*50)
    print("【操作のお願い】 ログインを完了させてください。")
    print("="*50 + "\n")
    while True:
        try:
            if driver.find_elements(By.CSS_SELECTOR, "svg[aria-label='ホーム'], svg[aria-label='Home'], a[href*='/direct/inbox/']"):
                print("ログインを確認しました。")
                break
        except: pass
        time.sleep(2)

def get_followers(driver, username):
    print(f"@{username} のプロフィールに移動します...")
    driver.get(f"https://www.instagram.com/{username}/")
    time.sleep(random.uniform(4, 6))
    
    try:
        followers_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"a[href='/{username}/followers/']"))
        )
        followers_btn.click()
        print("フォロワーボタンをクリックしました。")
    except Exception as e:
        print(f"フォロワーボタンが見つかりません: {e}")
        return []

    time.sleep(5)
    
    # スクロールエリアの特定
    scroll_area = None
    try:
        scroll_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog'] div[scrollable='true'], div[role='dialog'] div[style*='overflow-y: auto']"))
        )
        print("スクロール領域を特定しました。")
    except:
        scroll_area = driver.execute_script("""
            return Array.from(document.querySelectorAll('div[role="dialog"] div'))
                .find(el => {
                    const style = getComputedStyle(el);
                    return (style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight;
                });
        """)

    if not scroll_area:
        print("エラー: スクロール可能なエリアが見つかりませんでした。")
        return []
    
    followers = set()
    no_new_count = 0
    last_count = 0
    
    print("フォロワー一覧を収集中（スクロール中）...")
    while True:
        elements = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'] a[role='link'] span")
        for el in elements:
            try:
                txt = el.text.strip()
                if txt and "\n" not in txt and not any(ord(c) > 127 for c in txt):
                    if txt.lower() not in ["followers", "フォロワー", "following", "フォロー中", "remove", "削除", "follow", "フォロー"]:
                        followers.add(txt)
            except: continue
        
        current_count = len(followers)
        if current_count > last_count:
            no_new_count = 0
            last_count = current_count
            print(f"  現在の取得数: {current_count}")
        else:
            no_new_count += 1
            
        if no_new_count > 12:
            print("新しいフォロワーが検知されないため終了します。")
            break
            
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_area)
        time.sleep(random.uniform(2.5, 4.5))
        if no_new_count > 5:
            driver.execute_script("arguments[0].scrollTop -= 300", scroll_area)
            time.sleep(1)
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_area)
    
    return sorted(list(followers))

def main():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    driver = setup_driver()
    try:
        wait_for_login(driver)
        # 自分のユーザー名を取得
        profile_link = driver.find_element(By.CSS_SELECTOR, "a[href^='/'][href$='/']:has(img), a[href*='profile']")
        my_username = profile_link.get_attribute("href").strip("/").split("/")[-1]
        
        followers = get_followers(driver, my_username)
        with open(FOLLOWERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"main_user": my_username, "followers": followers}, f, ensure_ascii=False, indent=4)
        print(f"\n成功！{len(followers)}名のフォロワーを '{FOLLOWERS_FILE}' に保存しました。")
    finally:
        driver.quit()

if __name__ == "__main__": main()
