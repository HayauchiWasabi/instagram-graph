import json
import time
import os
import random
from curl_cffi import requests

# --- 設定 ---
DATA_DIR = os.path.join(os.getcwd(), "data")
COOKIES_FILE = os.path.join(DATA_DIR, "cookies.json")
FOLLOWERS_FILE = os.path.join(DATA_DIR, "followers.json")

# API設定
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.instagram.com/",
}

def load_cookies():
    if not os.path.exists(COOKIES_FILE):
        print(f"エラー: {COOKIES_FILE} が見つかりません。step2_dump_cookies.py を実行してください。")
        return None
    
    with open(COOKIES_FILE, "r") as f:
        selenium_cookies = json.load(f)
    
    cookie_dict = {}
    for c in selenium_cookies:
        cookie_dict[c["name"]] = c["value"]
    return cookie_dict

def get_user_info(user_id, cookies):
    url = f"https://www.instagram.com/api/v1/users/{user_id}/info/"
    try:
        res = requests.get(url, cookies=cookies, headers=HEADERS, impersonate="chrome124")
        if res.status_code == 200:
            return res.json().get("user", {})
    except Exception as e:
        print(f"User Info Error: {e}")
    return {}

def fetch_all_followers(user_id, cookies):
    followers = []
    next_max_id = ""
    base_url = f"https://www.instagram.com/api/v1/friendships/{user_id}/followers/"
    
    print("フォロワーリストの取得を開始します...")

    try:
        request_count = 0
        while True:
            # 安全運転モード: 一度に取得する数を減らす (200 -> 50)
            params = {"count": 50, "search_surface": "follow_list_page"}
            if next_max_id:
                params["max_id"] = next_max_id

            response = requests.get(
                base_url, 
                params=params,
                cookies=cookies, 
                headers=HEADERS,
                impersonate="chrome124",
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                for u in users:
                    followers.append({
                        "username": u["username"],
                        "id": u["pk"]
                    })
                
                print(f"  -> {len(users)} 名取得 (計: {len(followers)} 名)")
                
                next_max_id = data.get("next_max_id")
                
                if not next_max_id:
                    break
                
                # 安全運転モード: 待機時間を大幅に増やす (10〜20秒)
                request_count += 1
                sleep_time = random.uniform(10.0, 20.0)
                
                # 5回に1回、さらに長く休む (30〜60秒)
                if request_count % 5 == 0:
                    print("  ☕ 休憩中 (45秒)...")
                    sleep_time = random.uniform(30.0, 60.0)

                time.sleep(sleep_time)
            
            elif response.status_code == 429:
                print("⚠️ レート制限 (429)。10分待機します...")
                time.sleep(600)
            else:
                print(f"⚠️ APIエラー: {response.status_code}")
                break

    except Exception as e:
        print(f"❌ 通信エラー: {e}")
        return None

    return followers

def main():
    cookies = load_cookies()
    if not cookies: return

    # Cookieから自分のIDを取得
    ds_user_id = cookies.get("ds_user_id")
    if not ds_user_id:
        print("エラー: Cookieに ds_user_id が含まれていません。")
        return

    print(f"ログインユーザーID: {ds_user_id}")

    # 自分のユーザー名を取得
    user_info = get_user_info(ds_user_id, cookies)
    MyUsername = user_info.get("username")
    if not MyUsername:
        print("ユーザー情報の取得に失敗しました。")
        return
    
    print(f"ユーザー名: {MyUsername}")

    # フォロワー取得
    followers_list = fetch_all_followers(ds_user_id, cookies)
    
    if followers_list:
        print(f"\n✅ 合計 {len(followers_list)} 名のフォロワーを取得しました。")
        
        save_data = {
            "main_user": MyUsername,
            "followers": followers_list
        }
        
        with open(FOLLOWERS_FILE, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4)
        print(f"結果を {FOLLOWERS_FILE} に保存しました。")

if __name__ == "__main__":
    main()
