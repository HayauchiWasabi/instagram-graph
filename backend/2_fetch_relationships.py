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
GRAPH_DATA_FILE = os.path.join(DATA_DIR, "graph_data.json")

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

def get_scroll_area(driver):
    """ダイアログ内のスクロール領域を確実に取得する"""
    return driver.execute_script("""
        const dialog = document.querySelector('div[role="dialog"]');
        if (!dialog) return null;
        const scrollable = dialog.querySelector('div[scrollable="true"]');
        if (scrollable) return scrollable;
        const known = dialog.querySelector('.x6nl9eh, .xyi1961, ._aano');
        if (known && known.scrollHeight > known.clientHeight) return known;
        return Array.from(dialog.querySelectorAll('div')).find(el => {
            const style = getComputedStyle(el);
            return (style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight;
        });
    """)

def scan_mutual_connections(driver, main_user, followers):
    # すでに途中までデータがあれば読み込む
    if os.path.exists(GRAPH_DATA_FILE):
        with open(GRAPH_DATA_FILE, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
        print(f"既存のデータを読み込みました: {len(graph_data['edges'])} 本の接続")
    else:
        graph_data = {
            "nodes": [{"id": main_user, "label": main_user, "group": "main"}],
            "edges": []
        }
        for f in followers:
            graph_data["nodes"].append({"id": f, "label": f, "group": "follower"})
            graph_data["edges"].append({"from": main_user, "to": f})
        print("新規グラフデータを作成しました。")

    processed_users = {node["id"] for node in graph_data["nodes"] if node.get("processed")}

    print(f"\n関係性のスキャンを開始します（計{len(followers)}名）...")
    
    for i, follower in enumerate(followers):
        if follower in processed_users:
            continue
        
        print(f"\n[{i+1}/{len(followers)}] @{follower} のプロフィールを確認中...")
        
        # 1. 共通フォロワーURLへ直行（高速化）
        driver.get(f"https://www.instagram.com/{follower}/followers/mutualFirst/")
        time.sleep(random.uniform(3, 4.5))
        
        modal_opened = False
        if driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']"):
            modal_opened = True
        else:
            # 失敗した場合はプロフィール経由で再試行
            driver.get(f"https://www.instagram.com/{follower}/")
            time.sleep(random.uniform(2, 3))
            try:
                mutual_link = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"a[href*='/{follower}/followers/mutual']"))
                )
                mutual_link.click()
                modal_opened = True
            except:
                print("  -> モーダルを開けませんでした。非公開または共通フォロワー無しの可能性があります。")

        if modal_opened:
            # 「See All Followers」の展開
            time.sleep(1.5)
            try:
                see_all = driver.find_elements(By.CSS_SELECTOR, f"a[href*='/{follower}/followers/mutualFirst']")
                if see_all:
                    driver.execute_script("arguments[0].click();", see_all[0])
                    time.sleep(2.5)
            except: pass

            # 4. スクロール抽出（JavaScript一括抽出で高速化）
            mutuals_found = set()
            found_main_user = False
            no_new_count = 0
            last_count = 0

            while not found_main_user:
                scroll_area = get_scroll_area(driver)
                if not scroll_area:
                    time.sleep(1.5)
                    if driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']"): continue
                    else: break

                # --- 高速化ポイント: JSで一括抽出 ---
                new_names = driver.execute_script("""
                    const names = [];
                    const spans = document.querySelectorAll('div[role="dialog"] a[role="link"] span');
                    for (const s of spans) {
                        const txt = s.textContent.trim();
                        if (txt && !/[\\n\\s]/.test(txt)) {
                            names.push(txt);
                        }
                    }
                    return names;
                """)

                for txt in new_names:
                    if txt == main_user:
                        print(f"  -> {main_user} (自分) を発見。停止します。")
                        found_main_user = True
                        break
                    if txt in followers and txt != follower:
                        mutuals_found.add(txt)
                
                if found_main_user: break

                if len(mutuals_found) > last_count:
                    last_count = len(mutuals_found)
                    no_new_count = 0
                else:
                    no_new_count += 1
                
                if no_new_count > 10: break

                # スクロール
                try:
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_area)
                except: pass
                time.sleep(random.uniform(1.2, 2.2))

            # エッジ追加
            for m in mutuals_found:
                edge = {"from": follower, "to": m}
                if edge not in graph_data["edges"]:
                    graph_data["edges"].append(edge)
                    print(f"    + 繋がり発見: {follower} -> {m}")

        # 進捗マークと保存
        for node in graph_data["nodes"]:
            if node["id"] == follower:
                node["processed"] = True
        
        with open(GRAPH_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=4)
        
        print(f"  完了: 現在 {len(graph_data['edges'])} 本の接続を記録。")
        time.sleep(random.uniform(3, 7)) # ユーザー間インターバルも短縮

def main():
    if not os.path.exists(FOLLOWERS_FILE):
        print(f"エラー: {FOLLOWERS_FILE} が見つかりません。まず 1_fetch_followers.py を実行してください。")
        return
    
    with open(FOLLOWERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    driver = setup_driver()
    try:
        wait_for_login(driver)
        scan_mutual_connections(driver, data["main_user"], data["followers"])
    finally:
        print("\nブラウザを終了します。")
        driver.quit()

if __name__ == "__main__": main()
