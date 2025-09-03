# 🚀 Telegram Cleaner Pro


## 🧹 Overview
**Telegram Cleaner Pro** is a **powerful and secure Telegram cleanup tool** that helps you **delete & block bots**, **leave or delete unwanted channels/groups**, and **manage private chats** safely.  
It offers **automatic cleanup mode**, **confirmation prompts**, and **beautiful table-based UI** for a seamless experience.

---

## ✨ Features
- 🤖 **Delete & Block Bots** — Remove spam/bot chats instantly  
- 📢 **Manage Channels & Groups** — Leave or delete unwanted ones easily  
- 🔒 **Private Chats Cleanup** — Delete inactive or unnecessary chats  
- 🌀 **Automatic Cleanup** — Full cleanup in one click  
- 🛡 **Safe & Secure** — Always asks for confirmation before deleting  
- 📊 **Clean Table UI** — Displays data in a neat, organized way  
- 🔄 **Auto Refresh** — Updates the lists after every action  

---

## 🛠️ Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/zcsaqueeb/telegram-cleaner-pro.git
cd telegram-cleaner-pro
````

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure API Keys

Edit **config.py** and add your Telegram API credentials:

```python
API_ID = 123456
API_HASH = "your_api_hash"
```

> You can get your API keys from [my.telegram.org](https://my.telegram.org/).

---

## ⚡ Usage

Run the tool:

```bash
python telegram_cleaner_pro.py
```

### **Main Menu**

```
1️⃣ Delete & Block Bots
2️⃣ Manage Channels & Groups
3️⃣ Automatic Full Cleanup (Safe)
4️⃣ Exit
```

* **Option 1** → Deletes & blocks selected bots
* **Option 2** → Displays all joined channels/groups → lets you leave/delete them
* **Option 3** → Cleans bots, channels, and groups automatically (with confirmation)
* **Option 4** → Exit the program safely

---

## 📦 Project Structure

```
telegram-cleaner-pro/
├── telegram_cleaner_pro.py   # Main script
├── config.py                # Stores API keys
├── requirements.txt         # Dependencies
├── README.md               # Documentation
├── LICENSE                 # License information
└── sessions/               # Auto-created Telegram sessions
```

---

## 📜 Dependencies

All required dependencies are listed in **requirements.txt**:

```txt
telethon
tabulate
prettytable
pandas
rich
qrcode
colorama
aiohttp
```

Install them:

```bash
pip install -r requirements.txt
```

---

## 🛡 License

### MIT License

```
Copyright (c) 2025 Saqueeb

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

---

## ⭐ Support

If you find this project useful, **please star the repository** to support development:
🔗 **[https://github.com/zcsaqueeb/telegram-cleaner-pro](https://github.com/zcsaqueeb/telegram-cleaner-pro)**

---

## 👨‍💻 Author

**[Saqueeb](https://github.com/zcsaqueeb)**
Creator of **Telegram Cleaner Pro** — built for **automation, privacy, and performance**.



