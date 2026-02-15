import json
import time
import os
import random
from curl_cffi import requests

# --- 設定 ---
DATA_DIR = os.path.join(os.getcwd(), "data")
COOKIES_FILE = os.path.join(DATA_DIR, "cookies.json")
FOLLOWERS_FILE = os.path.join(DATA_DIR, "followers.json")
GRAPH_DATA_FILE = os.path.join(DATA_DIR, "graph_data.json")

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

def load_json(filepath, default=None):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def fetch_mutual_followers(target_id, cookies):
    """
    指定ユーザーIDの共通フォロワーをAPI経由で取得する (ページネーション対応)
    """
    mutuals = []
    next_max_id = ""
    page_count = 0
    base_url = f"https://www.instagram.com/api/v1/friendships/{target_id}/mutual_followers/"

    try:
        while True:
            params = {}
            if next_max_id:
                params["max_id"] = next_max_id

            # print(f"  [DEBUG] Requesting API: {base_url} (max_id={next_max_id})")
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
                # print(f"  [DEBUG] Response: Found {len(users)} users. Next Max ID: {data.get('next_max_id')}")
                
                mutuals.extend(users)
                
                next_max_id = data.get("next_max_id")
                page_count += 1
                
                if not next_max_id:
                    break
                
                time.sleep(random.uniform(1.0, 2.0))
            
            elif response.status_code == 429:
                print("⚠️ レート制限 (429) を検知しました。5分間待機します...")
                time.sleep(300)
            elif response.status_code == 401:
                print("❌ 認証エラー (401)。Cookieが無効です。再取得してください。")
                return None
            else:
                print(f"⚠️ APIエラー: Status {response.status_code}")
                print(response.text[:200])
                break

    except Exception as e:
        print(f"❌ 通信エラー: {e}")
        return None

    return mutuals

def main():
    print("🚀 高速スクレイパー (API版) を起動します...")
    
    # データ読み込み
    followers_data = load_json(FOLLOWERS_FILE)
    if not followers_data:
        print("エラー: data/followers.json がありません。")
        return

    main_user = followers_data.get("main_user")
    followers = followers_data.get("followers", [])
    cookies = load_cookies()

    if not cookies:
        return

    # グラフデータ初期化
    graph_data = load_json(GRAPH_DATA_FILE, {
        "nodes": [{"id": main_user, "label": main_user, "group": "main"}],
        "edges": []
    })
    
    # ノード情報の整備
    existing_nodes = {node["id"] for node in graph_data["nodes"]}
    for f in followers:
        if f not in existing_nodes:
            graph_data["nodes"].append({"id": f, "label": f, "group": "follower"})

    # ユーザーIDのマッピング（APIにはIDが必要なため）
    # followers.json にIDがあれば良いが、なければAPIから引く必要がある
    # 今はIDがわからないので、search等はせず、ひとまずIDがわかるユーザー (mutual_followers APIはID必須)
    # -> 実は step1 で取得した cookies には自分のIDが含まれているが、
    #    他人のIDを知るには username -> id 変換が必要。
    #    しかし `followers.json` は username のリスト。
    #    APIで `web_profile_info` を叩くか、検索APIを使う必要がある。
    
    # ★ ここで問題: username から user_id への変換が必要。
    # API: https://www.instagram.com/web/search/topsearch/?context=blended&query={username}
    # または https://www.instagram.com/{username}/?__a=1&__d=dis
    
    print(f"対象人数: {len(followers)} 名")
    processed_count = 0
    
    # 既存データのprocessedフラグを確認
    processed_users = {node["id"] for node in graph_data["nodes"] if node.get("processed")}

    for i, follower_data in enumerate(followers):
        username = follower_data.get("username")
        user_id = follower_data.get("id")

        if not username or not user_id:
            print(f"Warning: Invalid data for index {i}. Skipping.")
            continue

        if username in processed_users:
            continue
            
        print(f"\n[{i+1}/{len(followers)}] @{username} の処理中...")

        # 1. User ID は既に持っているので取得不要！
        
        # 2. 共通フォロワー取得
        mutual_users = fetch_mutual_followers(user_id, cookies)
        
        if mutual_users is not None:
            count = 0
            for m_user in mutual_users:
                m_username = m_user.get("username")
                # 自分自身は除外
                if m_username == main_user: continue
                
                # エッジ追加
                edge = {"from": username, "to": m_username}
                # 重複チェックは簡易的に行う（リスト内検索は遅いが今は許容）
                if edge not in graph_data["edges"]:
                    graph_data["edges"].append(edge)
                    count += 1
            
            print(f"  -> {count} 件の繋がりを発見")
            
            # 完了マーク
            for node in graph_data["nodes"]:
                if node["id"] == username:
                    node["processed"] = True
            
            save_json(GRAPH_DATA_FILE, graph_data)
        
        processed_count += 1
        
        # 安全運転モード: 待機時間を大幅に増やす (15〜25秒)
        sleep_time = random.uniform(15.0, 25.0)
        
        # 10人に1回、休憩 (60秒)
        if processed_count % 10 == 0:
            print("  ☕ 休憩中 (60秒)...")
            sleep_time = 60
            
        # 50人に1回、長めの休憩 (5分)
        if processed_count % 50 == 0:
            print("  ☕ 長めの休憩 (5分)...")
            sleep_time = 300
            
        time.sleep(sleep_time)

    print("\n✅ 全処理が完了しました！")

if __name__ == "__main__":
    main()
