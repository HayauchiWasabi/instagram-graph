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
TEST_TARGET = "02_0631"  # テストする対象のユーザーID
MY_USERNAME = "kai.ikeda.52"  # あなたのユーザーID

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
        
        // 1. scrollable="true" 属性を持つ div を優先（これが一番確実）
        const scrollable = dialog.querySelector('div[scrollable="true"]');
        if (scrollable) return scrollable;
        
        // 2. クラス名で検索
        const known = dialog.querySelector('.x6nl9eh, .xyi1961, ._aano');
        if (known && known.scrollHeight > known.clientHeight) return known;
        
        // 3. 全 div から計算スタイルで検索
        return Array.from(dialog.querySelectorAll('div')).find(el => {
            const style = getComputedStyle(el);
            return (style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight;
        });
    """)

def test_mutual_fetch(driver, target_user, main_user):
    # 1. プロフィールに移動
    profile_url = f"https://www.instagram.com/{target_user}/"
    print(f"\nターゲット: @{target_user}")
    print(f"プロフィールに移動中: {profile_url}")
    driver.get(profile_url)
    time.sleep(random.uniform(4, 6))

    # 2. 共通フォロワーのモーダルを開く
    print("共通フォロワーのモーダルを開こうとしています...")
    modal_opened = False
    
    try:
        # 手法1: URL直行
        driver.get(f"https://www.instagram.com/{target_user}/followers/mutualFirst/")
        time.sleep(5)
        if driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']"):
            modal_opened = True
            print("  -> 直接URLでモーダルを確認しました。")
    except: pass

    if not modal_opened:
        try:
            # 手法2: 「Followed by...」リンクをクリック
            mutual_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f"a[href*='/{target_user}/followers/mutual']"))
            )
            mutual_link.click()
            print("  -> 共通フォロワーリンクをクリックしました。")
            modal_opened = True
        except:
            print("エラー: モーダルを開けませんでした。")
            return

    # 3. 「See All Followers (すべて見る)」のクリック（必要に応じて）
    # 共通フォロワーが数名しかいない場合、これをクリックして展開する必要がある
    time.sleep(3)
    try:
        see_all_links = driver.find_elements(By.CSS_SELECTOR, f"a[href*='/{target_user}/followers/mutualFirst']")
        if see_all_links:
            print("  -> 'See All Followers' をクリックして全展開します...")
            driver.execute_script("arguments[0].click();", see_all_links[0])
            time.sleep(4)
    except: pass

    # 4. スクロール抽出
    mutuals = set()
    found_self = False
    no_new_count = 0
    last_count = 0

    print(f"抽出開始: @{main_user} が見つかるまでスクロールします...")
    
    while not found_self:
        # スクロール領域をループ内で毎回取得（StaleElementReferenceException 対策）
        scroll_area = get_scroll_area(driver)
        if not scroll_area:
            print("警告: スクロール領域を特定できません。再試行中...", end="\r")
            time.sleep(2)
            continue

        # ユーザー名の抽出 (aタグ内のspan。これが最も安定)
        elements = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'] a[role='link'] span")
        for el in elements:
            try:
                txt = el.text.strip()
                if not txt: continue
                
                # 自分を見つけたら即終了
                if txt == main_user:
                    print(f"\n  >>> 自分 (@{main_user}) を発見！スキャンを終了します。")
                    found_self = True
                    break
                
                # UIテキスト以外の英数字/ドット/アンダースコアの文字列をユーザー名とみなす
                if txt.lower() not in ["followers", "following", "remove", "follow", "フォロー", "common", "see all", "すべて見る", "すべて表示"]:
                    if txt not in mutuals:
                        mutuals.add(txt)
            except: continue
        
        if found_self: break

        # 進捗表示
        if len(mutuals) > last_count:
            print(f"  抽出済み: {len(mutuals)} 名 (直近: {list(mutuals)[-1]})", end="\r")
            last_count = len(mutuals)
            no_new_count = 0
        else:
            no_new_count += 1
        
        if no_new_count > 15:
            print("\nこれ以上増えないため終了します。")
            break

        # スクロール実行 (最下部まで)
        try:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_area)
        except Exception as e:
            print(f"\nスクロール失敗: {e}")
            time.sleep(2)
        
        time.sleep(random.uniform(2.5, 3.5))

    print(f"\n\n【最終結果】")
    print(f"対象: @{target_user}")
    print(f"見つかった共通フォロワー: {len(mutuals)} 名")
    print(f"リスト: {list(mutuals)}")
    print(f"自分の発見: {'成功 ✅' if found_self else '失敗 ❌'}")

def main():
    # followers.json からランダムにターゲットを選択
    followers_file = os.path.join(os.path.dirname(__file__), "..", "data", "followers.json")
    if not os.path.exists(followers_file):
        print(f"エラー: {followers_file} が見つかりません。先に 1_fetch_followers.py を実行してください。")
        return

    with open(followers_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    followers = data.get("followers", [])
    main_user = data.get("main_user", MY_USERNAME)

    if not followers:
        print("エラー: フォロワーリストが空です。")
        return

    target_user = random.choice(followers)
    print(f"【ランダム選択】次回のターゲット: @{target_user}")

    driver = setup_driver()
    try:
        wait_for_login(driver)
        test_mutual_fetch(driver, target_user, main_user)
    finally:
        print("\n30秒後にブラウザを閉じます...")
        time.sleep(30)
        driver.quit()

if __name__ == "__main__":
    main()
