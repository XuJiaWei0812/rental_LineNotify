import os
import json
import time
import random
import re
from datetime import datetime, timedelta
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# 常量定義
SENT_MESSAGES_FILE = 'sent_messages.json'  # 儲存已發送訊息的檔案
CONFIG_FILE = 'config.json'  # 儲存配置資訊的檔案
BASE_URL = 'https://rent.591.com.tw/list'  # 爬蟲目標網站的基礎URL
LINE_NOTIFY_URL = "https://notify-api.line.me/api/notify"  # LINE Notify API的URL

class CrawlerGUI:
    def __init__(self, master):
        self.master = master  # 主視窗
        master.title("新北租屋新物件通知")  # 設定視窗標題
        master.geometry("400x300")  # 設定視窗大小

        self.token = tk.StringVar()  # 用於儲存LINE Notify token的變數
        self.load_config()  # 載入配置檔案

        # 創建並放置GUI組件
        tk.Label(master, text="LINE Notify Token:").pack(pady=5)
        self.token_entry = tk.Entry(master, textvariable=self.token, width=50)
        self.token_entry.pack(pady=5)

        self.start_button = tk.Button(master, text="啟動爬蟲", command=self.start_crawler)
        self.start_button.pack(pady=10)

        self.status_text = scrolledtext.ScrolledText(master, height=10, width=50)
        self.status_text.pack(pady=10)

        self.crawler_thread = None  # 爬蟲執行緒
        self.is_running = False  # 爬蟲執行狀態標誌

    def load_config(self):
        """從配置檔案中載入LINE Notify token"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.token.set(config.get('token', ''))

    def save_config(self):
        """儲存LINE Notify token到配置檔案"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'token': self.token.get()}, f)

    def start_crawler(self):
        """啟動爬蟲"""
        if not self.token.get():
            messagebox.showerror("錯誤", "請輸入有效的LINE Notify Token")
            return

        if self.is_running:
            messagebox.showinfo("提示", "爬蟲已在執行中")
            return

        self.save_config()  # 儲存token
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)  # 禁用啟動按鈕
        self.crawler_thread = threading.Thread(target=self.run_crawler)
        self.crawler_thread.start()  # 在新執行緒中啟動爬蟲

    def run_crawler(self):
        """爬蟲主迴圈"""
        self.update_status("爬蟲開始執行...")
        while self.is_running:
            try:
                self.crawl_and_notify()  # 執行爬取和通知
                self.update_status("等待3小時後重新爬取...")
                for i in range(180, 0, -1):  # 3小時倒數計時
                    if not self.is_running:
                        break
                    self.update_status(f"下次爬取倒數計時: {i} 分鐘")
                    time.sleep(60)  # 每分鐘更新一次狀態
            except Exception as e:
                self.update_status(f"發生錯誤: {str(e)}")
                time.sleep(60)  # 發生錯誤時，暫停1分鐘後繼續

        self.update_status("爬蟲已停止")
        self.start_button.config(state=tk.NORMAL)  # 重新啟用啟動按鈕

    def update_status(self, message):
        """更新狀態顯示"""
        self.status_text.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        self.status_text.see(tk.END)  # 捲動到最新訊息

    def crawl_and_notify(self):
        """執行爬取和通知操作"""
        ua = UserAgent()
        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "User-Agent": ua.random,
            "Host": "rent.591.com.tw", 
        }
        session = requests.Session()
        sent_messages = self.load_sent_messages()

        for page in range(1, 999):  # 只爬取第一頁
            url = f'{BASE_URL}?section=37&region=3&sort=updatetime_desc&page={page}'
            sent_messages, uptime_count = self.crawl_591(session, headers, url, sent_messages)
            if uptime_count == 0:
                self.update_status('沒有需要提醒的新刊登')
                break
            time.sleep(random.uniform(3, 6))  # 隨機延遲，避免被封IP
        
        self.save_sent_messages(sent_messages)

    def load_sent_messages(self):
        """載入已發送的訊息列表"""
        if os.path.exists(SENT_MESSAGES_FILE):
            with open(SENT_MESSAGES_FILE, 'r') as f:
                return set(json.load(f))
        return set()

    def save_sent_messages(self, sent_messages):
        """儲存已發送的訊息列表"""
        with open(SENT_MESSAGES_FILE, 'w') as f:
            json.dump(list(sent_messages), f)

    def line_notify_message(self, msg):
        """發送LINE Notify訊息"""
        headers = {
            "Authorization": f"Bearer {self.token.get()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {'message': msg}
        response = requests.post(LINE_NOTIFY_URL, headers=headers, data=payload)
        return response.status_code

    def parse_uptime(self, uptime):
        """解析更新時間"""
        if '小時內更新' in uptime:
            return int(re.search(r'(\d+)(?=小時)', uptime).group(1))
        elif '分鐘內更新' in uptime:
            return 0
        return 24  # 假設超過24小時的更新時間

    def crawl_591(self, session, headers, url, sent_messages):
        """爬取591租屋網站並處理資料"""
        max_retries = 3
        uptime_count = 0

        for retry in range(max_retries):
            response = session.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all("div", class_="item")
            
            if items:
                break
            
            self.update_status(f'該頁面沒有任何房屋資訊，正在進行第 {retry + 1} 次重試')
            time.sleep(random.uniform(10, 15))
            ua = UserAgent()
            headers = {
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "User-Agent": ua.random,
                "Host": "rent.591.com.tw", 
            }
        else:
            self.update_status('重試 3 次後仍沒有任何房屋資訊')
            return sent_messages, uptime_count

        for item in items:
            # 解析每個房源的資訊
            title = item.find("div", class_="item-info-title").find('a').get('title')
            detail_url = item.find("div", class_="item-info-title").find('a').get('href')
            price = item.find("div", class_="item-info-price").get_text(strip=True)
            details = item.find_all("div", class_="item-info-txt")
            
            word_detail = ' | '.join(span.getText().strip() for span in details[0].find_all('span'))
            
            uptime = details[-1].find_all('span')[1].getText().strip()
            hours = self.parse_uptime(uptime)
            
            if hours <= 1:  # 只處理3小時內更新的房源
                uptime_count += 1
                msg = f'''租屋網更新資訊啦!
                        標題: {title}
                        價格: {price}
                        詳情: {word_detail}
                        更新時間: {uptime}
                        看更詳細點↓網址
                        {detail_url}
                        '''
                msg = '\n'.join([line.strip() for line in msg.splitlines()])        
                
                if detail_url not in sent_messages:
                    status_code = self.line_notify_message(msg)
                    if status_code == 200:
                        self.update_status(f"已經將 '{title}' 發送至Line")
                        sent_messages.add(detail_url)

        return sent_messages, uptime_count

def main():
    """主函數，創建並執行GUI"""
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()