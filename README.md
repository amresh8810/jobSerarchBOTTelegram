# 🤖 Telegram Job Search AI Agent

Internet se jobs search karo — directly Telegram chat mein!

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🔍 Smart Job Search | Job role + location se internet pe search |
| 🏢 Company Details | Company name + rating |
| 📍 Location | City, State, Country ya Remote |
| 💰 Salary | Exact range ya estimated |
| 📝 Description | Job summary |
| ✅ Apply Button | Direct apply link |
| 🔥 Trending Jobs | India ke trending jobs |

---

## ⚙️ Setup Guide (Step by Step)

### Step 1: Telegram Bot Token lo

1. Telegram pe [@BotFather](https://t.me/BotFather) open karo
2. `/newbot` command bhejo
3. Bot ka naam do (e.g., `My Job Search Bot`)
4. Username do (e.g., `myjobsearch_bot`)
5. **Token copy karo** — ye aapka `TELEGRAM_BOT_TOKEN` hai

---

### Step 2: RapidAPI Key lo (JSearch API — Free)

1. [rapidapi.com](https://rapidapi.com) pe account banao
2. Search karo: **"JSearch"**
3. **"Subscribe to Test"** karo (Free plan: 200 req/month)
4. **API Key copy karo** — ye aapka `RAPIDAPI_KEY` hai

🔗 Direct link: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

---

### Step 3: Project Setup

```bash
# 1. Folder mein jao
cd "C:\Users\Amresh kumar\Downloads\AI"

# 2. Virtual environment banao (recommended)
python -m venv venv

# 3. Activate karo
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Dependencies install karo
pip install -r requirements.txt
```

---

### Step 4: .env file banao

`.env.example` ko copy karo aur `.env` naam do:

```bash
copy .env.example .env
```

Phir `.env` file open karo aur apni keys daalo:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
RAPIDAPI_KEY=abc123def456ghi789
```

---

### Step 5: Bot Run karo

```bash
python bot.py
```

Output dikhega:
```
🤖 Telegram Job Search Bot starting...
✅ Press Ctrl+C to stop
🟢 Bot is live! Telegram pe /start karo
```

---

## 📱 Bot Commands

| Command | Kya karta hai |
|---|---|
| `/start` | Bot start karo |
| `/help` | Help guide dekho |
| `/search Python Developer Mumbai` | Direct job search |
| `/trending` | India ke trending jobs |
| `/clear` | Search history clear karo |

---

## 💬 Usage Examples

Bot pe ye messages bhejo:

```
Python Developer Mumbai
Data Scientist Bangalore remote  
Marketing Manager Delhi
React Developer Pune 5 lakh salary
Sales Executive Hyderabad full-time
Java Backend Engineer Noida
UI/UX Designer Chennai
Product Manager remote India
```

---

## 📊 Response Format

Bot har job ke liye ye batayega:

```
━━━━━━━━━━━━━━━━━━━━━━━━━
🔢 Job #1
━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️ Senior Python Developer

🏢 Company: TCS (Tata Consultancy Services)
📍 Location: Mumbai, Maharashtra, India
💼 Type: Full-time • 2 din pehle
💰 Salary: ₹12L - ₹18L/year

📝 Description:
We are looking for an experienced Python Developer
to join our growing team. You will be responsible
for developing scalable applications...

[✅ Apply Now]  [🏢 Company]
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Bot Framework | python-telegram-bot 21.x |
| Job Search API | JSearch (RapidAPI) |
| HTTP Client | httpx (async) |
| Runtime | Python 3.10+ |

---

## ❓ FAQ

**Q: Free mein kitne searches hoti hain?**  
A: JSearch free plan mein 200 requests/month milte hain.

**Q: Kya Hindi mein search kar sakte hain?**  
A: Abhi English mein search karo (results Indian jobs ke aate hain).

**Q: Bot slow hai?**  
A: Internet speed pe depend karta hai. Usually 2-5 seconds.

**Q: Koi error aa rahi?**  
A: Check karo ki `.env` file mein sahi tokens hain.

---

## 📞 Common Errors & Solutions

| Error | Solution |
|---|---|
| `TELEGRAM_BOT_TOKEN not set` | `.env` file mein token daalo |
| `RAPIDAPI_KEY not set` | RapidAPI key daalo |
| `No jobs found` | Query change karo, location add karo |
| `HTTP 429 Too Many Requests` | RapidAPI free plan limit khatam — upgrade karo |
| `Timeout error` | Internet check karo, dobara try karo |
