# 新北租屋新物件通知

這是一個用於爬取租屋網站並通過 LINE Notify 發送通知的 Python 爬蟲程式。

## 功能特點

- 自動爬取租屋網站的新北市最新租屋資訊
- 使用 LINE Notify 發送新房源通知
- 具有圖形使用者介面（GUI），便於操作
- 定期自動執行爬蟲，無需人工干預
- 避免重複發送相同的房源資訊

## 安裝需求

在運行此程式之前，請確保您已安裝以下 Python 套件：

```
requests
beautifulsoup4
fake_useragent
```

您可以使用以下命令安裝這些套件：

```
pip install requests beautifulsoup4 fake_useragent
```

## 使用方法

1. 克隆或下載此儲存庫到本地機器。
2. 確保您已經註冊了 LINE Notify 並獲得了 access token。
3. 運行 `main.py` 檔案來啟動 GUI。
4. 在 GUI 中輸入您的 LINE Notify token。
5. 點擊「啟動爬蟲」按鈕開始運行爬蟲。

## 配置

程式會自動創建以下檔案：

- `config.json`：儲存 LINE Notify token
- `sent_messages.json`：記錄已發送的房源資訊，避免重複發送

## 注意事項

- 本程式預設每 3 小時執行一次爬蟲操作。
- 為了避免對目標網站造成過大負擔，程式設有隨機延遲機制。
- 請遵守目標網站的使用條款和爬蟲協議。

## 免責聲明

本程式僅供學習和個人使用。使用者應自行承擔使用本程式的風險和法律責任。
