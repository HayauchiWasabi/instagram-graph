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
GRAPH_DATA_FILE = os.path.join(DATA_DIR, "graph_data.json")

def setup_driver():
    chrome_options = Options()
    # ユーザーがログイン操作を行えるように headless=False
    chrome_options.add_argument("--start-maximized")
    # bot検知を少しでも回避するための設定
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # webdriverのプロパティを隠蔽
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def wait_for_login(driver):
    print("Instagramにアクセス中...")
    driver.get("https://www.instagram.com/")
    
    print("\n" + "="*50)
    print("【操作のお願い】")
    print("1. ブラウザでInstagramにログインしてください。")
    print("2. ログイン後、ホーム画面（タイムライン）が表示されるまで操作してください。")
    print("="*50 + "\n")
    
    while True:
        try:
            # ホーム、検索、またはメッセージアイコンが表示されたらログイン完了とみなす
            if driver.find_elements(By.CSS_SELECTOR, "svg[aria-label='ホーム'], svg[aria-label='Home'], a[href*='/direct/inbox/']"):
                print("ログインを確認しました。")
                break
        except:
            pass
        time.sleep(2)

def get_followers(driver, username):
    print(f"@{username} のプロフィールに移動します...")
    driver.get(f"https://www.instagram.com/{username}/")
    time.sleep(random.uniform(4, 6))
    
    # フォロワーボタンの特定とクリック
    print("フォロワーリストを開こうとしています...")
    try:
        # hrefを基準にするのが最も確実
        followers_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"a[href='/{username}/followers/']"))
        )
        followers_btn.click()
        print("フォロワーボタンをクリックしました。")
    except Exception as e:
        print(f"フォロワーボタンのクリックに失敗しました (セレクター再試行中...): {e}")
        try:
            # 代替案: テキスト検索
            followers_btn = driver.find_element(By.XPATH, "//a[contains(@href, '/followers')]")
            followers_btn.click()
            print("代替セレクターでクリックしました。")
        except:
            print("フォロワーリストを開けませんでした。")
            return []

    time.sleep(5)
    
    # スクロールエリアの特定 (最新UI: scrollable="true" を持つ div)
    scroll_area = None
    print("スクロール領域を特定中...")
    try:
        # 1. 属性ベース (最も安定)
        # 2. クラスベース (バックアップ)
        selectors = [
            "div[scrollable='true']:not([id='scrollview'])",
            "div.x6nl9eh.x1a5l9x9.x7vuprf.x1mg3h75.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6",
            "div[role='dialog'] div[style*='overflow-y: auto']"
        ]
        
        for sel in selectors:
            try:
                el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                # 実際にスクロール可能かJSで判定
                is_scrollable = driver.execute_script("return arguments[0].scrollHeight > arguments[0].clientHeight", el)
                if is_scrollable:
                    scroll_area = el
                    print(f"スクロール領域を特定しました: {sel}")
                    break
            except:
                continue

        if not scroll_area:
            # 汎用探索 (JS)
            print("  -> 汎用的な探索を実行中...")
            scroll_area = driver.execute_script("""
                return Array.from(document.querySelectorAll('div[role="dialog"] div'))
                    .find(el => {
                        const style = getComputedStyle(el);
                        return (style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight;
                    });
            """)

    except Exception as e:
        print(f"スクロールエリアの特定中にエラー: {e}")

    if not scroll_area:
        print("エラー: スクロール可能なエリアが見つかりませんでした。")
        return []
    
    followers = set()
    no_new_count = 0
    last_count = 0
    
    print("フォロワー一覧を収集中（スクロール中）...")
    while True:
        # ユーザー名の抽出
        # span が入れ子になっているため、より深い a > span を狙う
        elements = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'] a[role='link'] span")
        for el in elements:
            try:
                txt = el.text.strip()
                if txt and "\n" not in txt and not any(ord(c) > 127 for c in txt):
                    if txt.lower() not in ["followers", "フォロワー", "following", "フォロー中", "remove", "削除", "follow", "フォロー"]:
                        followers.add(txt)
            except:
                continue
        
        current_count = len(followers)
        if current_count > last_count:
            no_new_count = 0
            last_count = current_count
            print(f"  現在の取得数: {current_count}")
        else:
            no_new_count += 1
            
        # 終了判定 (何度かスクロールしても増えない場合)
        if no_new_count > 12:
            print("新しいフォロワーが検知されないため、収集を終了します。")
            break
            
        # スクロール実行 (最下部まで)
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_area)
        
        # 読み込み待ち (ランダムな秒数)
        time.sleep(random.uniform(2.5, 4.5))
        
        # 万が一、画面が固まっている場合のために少し上に戻して再度下げる (刺激を与える)
        if no_new_count > 5:
            driver.execute_script("arguments[0].scrollTop -= 300", scroll_area)
            time.sleep(1)
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_area)
    
    return sorted(list(followers))

def scan_mutual_connections(driver, main_user, followers):
    """
    各フォロワーのプロフィールを訪れ、「共通のフォロワー」情報を取得してエッジを作成する。
    """
    graph_data = {
        "nodes": [{"id": main_user, "label": main_user, "group": "main"}],
        "edges": []
    }
    
    # フォロワーをノードとして追加し、自分とのエッジを作成
    for f in followers:
        graph_data["nodes"].append({"id": f, "label": f, "group": "follower"})
        graph_data["edges"].append({"from": main_user, "to": f})
    
    print(f"\n関係性のスキャンを開始します（計{len(followers)}名）...")
    print("※ BAN対策のため、非常にゆっくり進めます。")
    
    for i, follower in enumerate(followers):
        print(f"[{i+1}/{len(followers)}] @{follower} のプロフィールを確認中...")
        driver.get(f"https://www.instagram.com/{follower}/")
        time.sleep(random.uniform(4, 7))
        
        try:
            # 「共通のフォロワー」リンク（a[href*='/mutualOnly']）を直接探す
            # これがある＝自分との共通の繋がりが存在する
            mutual_link = driver.find_elements(By.CSS_SELECTOR, "a[href*='/mutualOnly'], a[href$='/followers/mutualOnly/']")
            
            if mutual_link:
                print(f"  -> 共通のフォロワーを検知しました。詳細を解析中...")
                # リンクのテキストから「〇〇さんと他〇名」という情報を解析
                text = mutual_link[0].text
                
                # 既存のフォロワーリスト内の名前が含まれているかチェック
                for potential_mutual in followers:
                    if potential_mutual != follower and potential_mutual in text:
                        edge = {"from": follower, "to": potential_mutual}
                        if edge not in graph_data["edges"]:
                            graph_data["edges"].append(edge)
                            print(f"    + 繋がりを保存: {follower} -> {potential_mutual}")
            else:
                # リンクがない場合、テキストベースでも一応探す
                mutual_text_areas = driver.find_elements(By.XPATH, "//span[contains(text(), 'フォロー中') or contains(text(), 'Followed by')]")
                for area in mutual_text_areas:
                    text = area.text
                    for potential_mutual in followers:
                        if potential_mutual != follower and potential_mutual in text:
                            edge = {"from": follower, "to": potential_mutual}
                            if edge not in graph_data["edges"]:
                                graph_data["edges"].append(edge)
                                print(f"    + 繋がりを保存 (テキストより): {follower} -> {potential_mutual}")
        except Exception as e:
            print(f"  エラー (スキップ): {e}")

        # 進捗を都度保存
        with open(GRAPH_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=4)
        
        # 安全のための長い休憩
        sleep_time = random.uniform(5, 12)
        if (i+1) % 10 == 0:
            sleep_time += 30
            print("  [Safety Check] 10名ごとに長めの休憩を入れます（30秒追加）...")
        time.sleep(sleep_time)

    return graph_data

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    driver = setup_driver()
    try:
        wait_for_login(driver)
        
        # 自分のユーザー名を取得
        # (ホーム画面で自分のプロフィールのリンクから取得)
        profile_link = driver.find_element(By.CSS_SELECTOR, "a[href^='/'][href$='/']:has(img), a[href*='profile']")
        my_username = profile_link.get_attribute("href").strip("/").split("/")[-1]
        print(f"対象アカウント: @{my_username}")
        
        # Step 1: 全フォロワーリストの取得
        followers = get_followers(driver, my_username)
        print(f"\n合計 {len(followers)} 名のフォロワーを特定しました。")
        
        # Step 2: 関係性のスキャン
        graph_data = scan_mutual_connections(driver, my_username, followers)
        
        print(f"\n完了！ グラフデータを '{GRAPH_DATA_FILE}' に保存しました。")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
