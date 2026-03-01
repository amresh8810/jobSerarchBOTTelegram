"""
Telegram Job Search AI Agent
Searches the internet for jobs and returns:
  - Job Title & Description
  - Company Name
  - Location / Area
  - Salary
"""

import os
import sys
import logging
import asyncio
import json
import datetime
import tempfile
import hashlib
import threading
import PyPDF2
from flask import Flask
import google.generativeai as genai
from deep_translator import GoogleTranslator

# Fix Windows console Unicode encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode, ChatAction
from dotenv import load_dotenv
from job_searcher import JobSearcher

# ─── Load environment variables ─────────────────────────────────────────────
load_dotenv()

# Health Check Server (For Cloud Deployment)
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running! 🚀"

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Failed to configure Gemini API: {e}")

# ─── Logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Initialize Job Searcher ─────────────────────────────────────────────────
searcher = JobSearcher(api_key=RAPIDAPI_KEY)

# ─── User session state ──────────────────────────────────────────────────────
user_sessions = {}  # {user_id: {"query": str, "results": list, "page": int}}

# ─── Subscription State ──────────────────────────────────────────────────────
SUBSCRIPTIONS_FILE = "subscriptions.json"

def load_subscriptions():
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load subscriptions: {e}")
    return {}

def save_subscriptions():
    try:
        with open(SUBSCRIPTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(subscriptions, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save subscriptions: {e}")

subscriptions = load_subscriptions()

# ─── Language State ──────────────────────────────────────────────────────────
LANGUAGES_FILE = "user_langs.json"
DEFAULT_LANG = "hi"  # Default Hindi

def load_langs():
    if os.path.exists(LANGUAGES_FILE):
        try:
            with open(LANGUAGES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_langs():
    try:
        with open(LANGUAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(user_langs, f, indent=4)
    except Exception:
        pass

user_langs = load_langs()

# ─── Saved Jobs State ────────────────────────────────────────────────────────
SAVED_JOBS_FILE = "saved_jobs.json"

def load_saved_jobs():
    if os.path.exists(SAVED_JOBS_FILE):
        try:
            with open(SAVED_JOBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_saved_jobs_file():
    try:
        with open(SAVED_JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(saved_jobs, f, indent=4)
    except Exception:
        pass

saved_jobs = load_saved_jobs()

JOB_CACHE = {}

def get_job_hash(job: dict) -> str:
    s = f"{job.get('title', '')}{job.get('company', '')}{job.get('apply_url', '')}"
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:10]

# ─── Application Tracking State ──────────────────────────────────────────────
APPLICATIONS_FILE = "applications.json"

def load_applications():
    if os.path.exists(APPLICATIONS_FILE):
        try:
            with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_applications_file():
    try:
        with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(applications, f, indent=4)
    except Exception:
        pass

applications = load_applications()
# Structure: {user_id: {job_hash: {"job": job_dict, "status": str, "date": str}}}

APP_STATUSES = {
    "applied": "📝 Applied",
    "interviewing": "🤝 Interviewing",
    "selected": "🎉 Selected",
    "rejected": "❌ Rejected"
}

# ─── Translation Helper ──────────────────────────────────────────────────────
TRANSLATION_CACHE = {}

async def translate_text(text: str, target_lang: str) -> str:
    """Translate text asynchronously using deep_translator."""
    if not text or target_lang in ("en", "hinglish"): # Assume source is similar enough for hinglish fallback, or we use standard translation
        return text
    
    # We will translate Hinglish/English to exact language script.
    # To improve accuracy, we should ensure texts passed here are somewhat standard.
    
    cache_key = f"{target_lang}:{text}"
    if cache_key in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[cache_key]

    try:
        translated = await asyncio.to_thread(
            GoogleTranslator(source='auto', target=target_lang).translate, text
        )
        if translated:
            TRANSLATION_CACHE[cache_key] = translated
            return translated
        return text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

def get_user_lang(user_id):
    return user_langs.get(str(user_id), DEFAULT_LANG)


# ════════════════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ════════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    
    welcome_text = (
        f"🙏 Welcome *{user.first_name}*!\n\n"
        "I am your **Job Search AI Agent** 🤖\n\n"
        "I search the internet for jobs and tell you:\n"
        "📌 *Job Title & Description*\n"
        "🏢 *Company Name*\n"
        "📍 *Location / Area*\n"
        "💰 *Expected Salary*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔍 *How to Job Search:*\n"
        "Just write your job type, for example:\n\n"
        "  • `Python Developer Mumbai`\n"
        "  • `Data Scientist Bangalore remote`\n"
        "  • `Marketing Manager Delhi`\n"
        "  • `React Developer Pune`\n"
        "  • `Sales Executive Hyderabad`\n\n"
        "🔔 *Daily Alerts (Subscription):*\n"
        "Want morning daily messages? Subscribe:\n"
        "  • `/subscribe Python Developer Mumbai`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *Commands:*\n"
        "/start - Start Bot\n"
        "/help - See Help\n"
        "/language - Change Language (Bhasha)\n"
        "/search - Search Jobs\n"
        "/saved - View Saved Jobs\n"
        "/applications - Track Applied Jobs\n"
        "/subscribe - Activate Daily alerts\n"
        "/unsubscribe - Stop Daily alerts\n"
        "/trending - View Trending jobs\n"
        "/clear - Clear Session\n"
    )
    
    if lang != "en":
        welcome_text = await translate_text(welcome_text, lang)
        
    menu_keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔍 Search Jobs"), KeyboardButton("🔥 Trending Jobs")],
            [KeyboardButton("🔔 Subscriptions"), KeyboardButton("💾 Saved Jobs")],
            [KeyboardButton("📈 My Applications"), KeyboardButton("📄 AI Resume Matcher")],
            [KeyboardButton("🌐 Change Language"), KeyboardButton("🆘 Help")]
        ], 
        resize_keyboard=True,
        input_field_placeholder="Choose an option or type a job role..."
    )
        
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=menu_keyboard)

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language command."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"), 
         InlineKeyboardButton("Hindi (हिंदी) 🇮🇳", callback_data="lang_hi")],
        [InlineKeyboardButton("Marathi (मराठी) 🇮🇳", callback_data="lang_mr"),
         InlineKeyboardButton("Tamil (தமிழ்) 🇮🇳", callback_data="lang_ta")],
        [InlineKeyboardButton("Bengali (বাংলা) 🇮🇳", callback_data="lang_bn"),
         InlineKeyboardButton("Telugu (తెలుగు) 🇮🇳", callback_data="lang_te")]
    ])
    msg = "Please choose your preferred language / कृपया अपनी भाषा चुनें:"
    await update.message.reply_text(msg, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    
    help_text = (
        "🆘 *Help Guide — Job Search Bot*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*🔍 How to Job Search?*\n\n"
        "Simply type in the message box:\n"
        "`[Job Role] [Location] [Optional: remote/full-time/part-time]`\n\n"
        "*Examples:*\n"
        "• `Software Engineer Bangalore`\n"
        "• `Data Analyst remote India`\n"
        "• `HR Manager Mumbai full-time`\n"
        "• `Node.js Developer Pune 5 lakh`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*📊 What you will get in Results:*\n"
        "🏷️ Job Title\n"
        "🏢 Company Name + Rating\n"
        "📍 Location\n"
        "💰 Salary Range\n"
        "📝 Job Description (Summary)\n"
        "🔗 Apply Link\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*⚙️ Commands:*\n"
        "/start - Bot restart\n"
        "/language - Change Language\n"
        "/trending - Trending jobs in India\n"
        "/search `[role]` `[location]` - Direct search\n"
        "/saved - View your saved jobs\n"
        "/applications - View your job application status\n"
        "/subscribe `[query]` - Subscribe for daily jobs\n"
        "/unsubscribe - Unsubscribe from daily jobs\n"
        "/clear - Clear your search history\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📄 *AI Resume Matcher:*\n"
        "Upload your Resume (PDF file) in chat and AI \n"
        "will automatically find the best matching jobs for you!\n"
    )
    if lang != "en":
        help_text = await translate_text(help_text, lang)
        
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe command."""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please query add karein.\nUsage: `/subscribe Python Developer Mumbai`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    query = " ".join(context.args)
    user_id = str(update.effective_user.id)
    subscriptions[user_id] = query
    save_subscriptions()
    lang = get_user_lang(str(update.effective_user.id))
    
    msg = f"Aapne *'{query}'* ke liye subscribe kiya hai.\nAb roz subah bot aapko latest jobs message karega. 🌅\n\nBand karne ke liye /unsubscribe send karein."
    header = "✅ *Subscription Successful!*\n\n"
    if lang != "en":
        msg = await translate_text(msg, lang)
        header = await translate_text(header, lang)

    await update.message.reply_text(
        f"{header}\n{msg}",
        parse_mode=ParseMode.MARKDOWN
    )

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unsubscribe command."""
    user_id = str(update.effective_user.id)
    lang = get_user_lang(user_id)
    
    if user_id in subscriptions:
        del subscriptions[user_id]
        save_subscriptions()
        msg = "⛔ *Unsubscribed!*\n\nAapko ab daily alerts nahi aayengi."
        if lang != "en":
            msg = await translate_text(msg, lang)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    else:
        msg = "Aapki koi active subscription nahi hai."
        if lang != "en":
            msg = await translate_text(msg, lang)
        await update.message.reply_text(msg)


async def trending_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trending command - show trending jobs in India."""
    lang = get_user_lang(str(update.effective_user.id))
    
    status = "⏳ Searching for Trending jobs in India..."
    if lang != "en": status = await translate_text(status, lang)
    
    await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    trending_queries = ["Software Engineer India 2025", "Data Scientist India", "Product Manager India"]
    query = trending_queries[0]

    jobs = await searcher.search_jobs(query, num_results=5)

    if not jobs:
        msg = "❌ Unable to find trending jobs right now. Please try again later."
        if lang != "en": msg = await translate_text(msg, lang)
        await update.message.reply_text(msg)
        return

    header = "🔥 *Trending Jobs in India — 2025*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if lang != "en": header = await translate_text(header, lang)
    
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN)

    for i, job in enumerate(jobs[:5], 1):
        msg_card = await format_job_card(job, i, lang)
        keyboard = build_job_keyboard(job, lang)
        await update.message.reply_text(msg_card, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        await asyncio.sleep(0.3)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command."""
    lang = get_user_lang(str(update.effective_user.id))
    if not context.args:
        usage = "Usage: `/search Python Developer Mumbai`"
        if lang != "en": usage = await translate_text(usage, lang)
        await update.message.reply_text(usage, parse_mode=ParseMode.MARKDOWN)
        return
    query = " ".join(context.args)
    await perform_search(update, context, query)

async def saved_jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /saved command."""
    user_id = str(update.effective_user.id)
    lang = get_user_lang(user_id)
    
    jobs = saved_jobs.get(user_id, [])
    if not jobs:
        msg = "📂 Aapne abhi tak koi job save nahi ki hai."
        if lang != "en": msg = await translate_text(msg, lang)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    msg = f"💾 *Your Saved Jobs* ({len(jobs)})\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if lang != "en": msg = await translate_text(msg, lang)
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    for i, job in enumerate(jobs, 1):
        msg_card = await format_job_card(job, i, lang)
        keyboard = build_job_keyboard(job, lang, saved_view=True)
        await update.message.reply_text(msg_card, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        await asyncio.sleep(0.3)

async def applications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /applications command."""
    user_id = str(update.effective_user.id)
    lang = get_user_lang(user_id)
    
    user_apps = applications.get(user_id, {})
    if not user_apps:
        msg = "📈 Aapne abhi tak koi application track nahi ki hai.\nJob card par '✅ I Applied' button click karke start karein!"
        if lang != "en": msg = await translate_text(msg, lang)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    header = f"📈 *Your Job Applications* ({len(user_apps)})\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if lang != "en": header = await translate_text(header, lang)
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN)

    for i, (job_hash, app_data) in enumerate(user_apps.items(), 1):
        job = app_data["job"]
        status_key = app_data["status"]
        status_display = APP_STATUSES.get(status_key, status_key)
        date = app_data.get("date", "N/A")
        
        title = job.get("title", "N/A")
        company = job.get("company", "N/A")
        
        msg_card = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔢 *# {i}*\n"
            f"🏷️ *{title}*\n"
            f"🏢 *Company:* {company}\n"
            f"📅 *Date:* {date}\n"
            f"📍 *Status:* `{status_display}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        # Build status update keyboard
        keyboard = []
        status_row = []
        for sk, sd in APP_STATUSES.items():
            if sk != status_key:
                status_row.append(InlineKeyboardButton(sd, callback_data=f"status_{job_hash}_{sk}"))
        
        if status_row:
            keyboard.append(status_row[:2])
            keyboard.append(status_row[2:])
            
        keyboard.append([InlineKeyboardButton("🗑️ Remove Tracker", callback_data=f"remapp_{job_hash}")])
        
        await update.message.reply_text(msg_card, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
        await asyncio.sleep(0.3)

async def clear_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command."""
    user_id = update.effective_user.id
    lang = get_user_lang(str(user_id))
    if user_id in user_sessions:
        del user_sessions[user_id]
        
    msg = "✅ Your search history has been cleared!"
    if lang != "en": msg = await translate_text(msg, lang)
    
    await update.message.reply_text(msg)

# ════════════════════════════════════════════════════════════════════════════
#  MESSAGE HANDLER (Main search logic)
# ════════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages as job search queries."""
    user_id = update.effective_user.id
    lang = get_user_lang(str(user_id))
    query = update.message.text.strip()

    # Handle bottom menu button clicks
    btn_txt = query.lower()
    if "trending jobs" in btn_txt or btn_txt == "🔥 trending jobs":
        await trending_jobs(update, context)
        return
    elif "change language" in btn_txt or btn_txt == "🌐 change language":
        await language_command(update, context)
        return
    elif "help" in btn_txt or btn_txt == "🆘 help":
        await help_command(update, context)
        return
    elif "subscriptions" in btn_txt or btn_txt == "🔔 subscriptions":
        msg = "🔔 Type `/subscribe [Your Job Role & Location]` to get daily morning alerts.\nType `/unsubscribe` to stop.\nExample: `/subscribe Python Developer Bangalore`"
        if lang != "en": msg = await translate_text(msg, lang)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return
    elif "search jobs" in btn_txt or btn_txt == "🔍 search jobs":
        msg = "🔍 Which job are you looking for?\nPlease type like: `Python Developer Mumbai`"
        if lang != "en": msg = await translate_text(msg, lang)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return
    elif "saved jobs" in btn_txt or btn_txt == "💾 saved jobs":
        await saved_jobs_command(update, context)
        return
    elif "my applications" in btn_txt or btn_txt == "📈 my applications":
        await applications_command(update, context)
        return
    elif "ai resume matcher" in btn_txt or btn_txt == "📄 ai resume matcher":
        msg = "📄 Please upload your Resume (PDF format) in this chat. AI will analyze it and find the best jobs for you automatically!"
        if lang != "en": msg = await translate_text(msg, lang)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    if len(query) < 2:
        msg = "🔍 Please provide more details, like: `Python Developer Mumbai`"
        if lang != "en": msg = await translate_text(msg, lang)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    await perform_search(update, context, query)

async def handle_resume_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF document uploads for AI Resume matching."""
    user_id_str = str(update.effective_user.id)
    lang = get_user_lang(user_id_str)
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        msg = "❌ AI Resume parsing is disabled (No GEMINI_API_KEY). Contact admin."
        if lang != "en": msg = await translate_text(msg, lang)
        await update.message.reply_text(msg)
        return

    # Send a process indicator
    status_text = "📥 Downloading your Resume PDF..."
    if lang != "en": status_text = await translate_text(status_text, lang)
    
    status_msg = await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    # 1. Download document
    doc = update.message.document
    if doc.file_size > 5 * 1024 * 1024:  # 5MB limit
        await status_msg.edit_text("❌ Please 5MB se chhota PDF upload karein.")
        return

    try:
        file = await context.bot.get_file(doc.file_id)
        
        # Save it to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            pdf_path = tmp_file.name
        await file.download_to_drive(pdf_path)

        # 2. Extract text from PDF
        await status_msg.edit_text("📄 Resume se skills aur details padh raha hoon... (AI Magic ✨)", parse_mode=ParseMode.MARKDOWN)
        
        pdf_text = ""
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"
        
        # Clean up temp file
        try:
            os.remove(pdf_path)
        except Exception as e:
            logger.error(f"Failed to delete temp pdf: {e}")

        if not pdf_text.strip():
            await status_msg.edit_text("❌ Is PDF se valid text samajh nahi aaya. Kripya doosra resume bhejein.")
            return

        # 3. Use Gemini AI to extract the best matching job role and query
        prompt = (
            "You are an expert HR and Technical Recruiter. Based on the following resume text, "
            "identify the primary job role (e.g., Python Developer, Data Scientist, Marketing Manager) "
            "and suggest a 3-word or 4-word search query to find the best matching jobs (e.g., 'Senior Python Developer Bangalore'). "
            "Only focus on finding the exact 3-4 word search query string that encapsulates their best skills and probable location (if available, else 'remote' or 'India'). "
            "Return your response strictly as a real parsable JSON object with this format:\n"
            '{"role": "The Role Name", "query": "The Search Query 3 to 4 words", "explanation": "A very short 1 sentence reason in Hinglish why this matches"}\n\n'
            f"Resume Text:\n{pdf_text[:8000]}"
        )

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        ai_response = response.text

        # Try to parse JSON from response
        clean_text = ai_response.replace("```json", "").replace("```", "").strip()
        job_data = json.loads(clean_text)

        role = job_data.get("role", "Software Professional")
        query = job_data.get("query", "Software Developer")
        explanation = job_data.get("explanation", "Yeh jobs aapke resume ke hisab se best match karti hain.")

        await status_msg.edit_text(
            f"🤖 *AI Analysis Complete!*\n\n"
            f"🎯 *Best Role Match:* {role}\n"
            f"💡 *AI Says:* {explanation}\n\n"
            f"🔍 Searching best jobs for `{query}`...",
            parse_mode=ParseMode.MARKDOWN
        )

        # Wait briefly so user can read message
        await asyncio.sleep(2)
        
        # 4. Perform the job search using the new query
        await perform_search(update, context, query)

    except json.JSONDecodeError as je:
        logger.error(f"JSON Parsing Error: {je} - AI Output: {ai_response}")
        msg = "❌ AI response format error. Please try uploading your resume again."
        if lang != "en": msg = await translate_text(msg, lang)
        await status_msg.edit_text(msg)
    except Exception as e:
        logger.error(f"Error in handle_resume_pdf: {e}", exc_info=True)
        msg = "❌ Error processing your resume. Please try searching via standard text."
        if lang != "en": msg = await translate_text(msg, lang)
        await status_msg.edit_text(msg)


async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Core job search logic."""
    user_id = update.effective_user.id
    lang = get_user_lang(str(user_id))

    # Show typing indicator
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    # Show search message
    search_txt = f"🔍 Searching for jobs related to *'{query}'*...\n⏳ Please wait..."
    if lang != "en": search_txt = await translate_text(search_txt, lang)
    
    search_msg = await update.message.reply_text(search_txt, parse_mode=ParseMode.MARKDOWN)

    try:
        jobs = await searcher.search_jobs(query, num_results=8)
    except Exception as e:
        logger.error(f"Search error: {e}")
        err_txt = "❌ Problem occurred while searching. Please try again!"
        if lang != 'en': err_txt = await translate_text(err_txt, lang)
        await search_msg.edit_text(err_txt)
        return

    if not jobs:
        msg = (
            f"😔 We couldn't find jobs for *'{query}'*.\n\n"
            "Try this:\n"
            "• Add location: `Python Developer Mumbai`\n"
            "• Change keywords\n"
            "• Broader search: `Developer India`"
        )
        if lang != 'en': msg = await translate_text(msg, lang)
        await search_msg.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    # Save session
    user_sessions[user_id] = {
        "query": query,
        "results": jobs,
        "page": 0
    }

    # Delete "searching..." message
    await search_msg.delete()

    # Send header
    header = (
        f"✅ Found *{len(jobs)} jobs* for *'{query}'*!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    if lang != 'en': header = await translate_text(header, lang)
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN)

    # Send each job card
    for i, job in enumerate(jobs[:5], 1):
        msg_card = await format_job_card(job, i, lang)
        keyboard = build_job_keyboard(job, lang)
        try:
            await update.message.reply_text(msg_card, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            await asyncio.sleep(0.4)
        except Exception as e:
            logger.warning(f"Failed to send job {i}: {e}")
            # Send without markdown if parsing fails
            plain = await format_job_card_plain(job, i, lang)
            await update.message.reply_text(plain, reply_markup=keyboard)

    # Show navigation if more results
    if len(jobs) > 5:
        nav_txt = "➡️ Show More Jobs (6-8)"
        more_txt = f"📋 There are {len(jobs) - 5} more jobs:"
        if lang != 'en': 
            nav_txt = await translate_text(nav_txt, lang)
            more_txt = await translate_text(more_txt, lang)
            
        nav_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(nav_txt, callback_data=f"page_1_{user_id}")]
        ])
        await update.message.reply_text(more_txt, reply_markup=nav_keyboard)


# ════════════════════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER (Inline buttons)
# ════════════════════════════════════════════════════════════════════════════

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = str(update.effective_user.id)
    lang = get_user_lang(user_id)

    # Handle Language Change
    if data.startswith("lang_"):
        selected_lang = data.split("_")[1]
        user_langs[user_id] = selected_lang
        save_langs()
        
        msg = f"Language changed successfully to {selected_lang.upper()} ✅"
        if selected_lang != "en":
            msg = await translate_text(msg, selected_lang)
            
        await query.message.edit_text(msg)
        return

    if data.startswith("save_"):
        job_hash = data.split("_")[1]
        job = JOB_CACHE.get(job_hash)
        if job:
            if user_id not in saved_jobs:
                saved_jobs[user_id] = []
            
            # Check if already saved
            already_saved = any(get_job_hash(sj) == job_hash for sj in saved_jobs[user_id])
            if not already_saved:
                saved_jobs[user_id].append(job)
                save_saved_jobs_file()
                msg = "✅ Job saved successfully!"
            else:
                msg = "⚠️ This job is already saved."
            
            if lang != "en": msg = await translate_text(msg, lang)
            await query.answer(msg, show_alert=True)
        else:
            await query.answer("❌ Job expired. Please search again.", show_alert=True)
        return

    if data.startswith("unsave_"):
        job_hash = data.split("_")[1]
        if user_id in saved_jobs:
            original_len = len(saved_jobs[user_id])
            saved_jobs[user_id] = [j for j in saved_jobs[user_id] if get_job_hash(j) != job_hash]
            if len(saved_jobs[user_id]) < original_len:
                save_saved_jobs_file()
                msg = "❌ Job removed from saved list."
                if lang != "en": msg = await translate_text(msg, lang)
                await query.answer(msg, show_alert=True)
                await query.message.delete()
            else:
                await query.answer("⚠️ Job not found in saved list.", show_alert=True)
        return

    if data.startswith("applied_"):
        job_hash = data.split("_")[1]
        job = JOB_CACHE.get(job_hash)
        if job:
            if user_id not in applications:
                applications[user_id] = {}
            
            if job_hash not in applications[user_id]:
                applications[user_id][job_hash] = {
                    "job": job,
                    "status": "applied",
                    "date": datetime.datetime.now().strftime("%d %b %Y")
                }
                save_applications_file()
                msg = "✅ Added to Tracked Applications!"
            else:
                msg = "⚠️ Already tracking this application."
                
            if lang != "en": msg = await translate_text(msg, lang)
            await query.answer(msg, show_alert=True)
        else:
            await query.answer("❌ Job expired. Please search again.", show_alert=True)
        return

    if data.startswith("status_"):
        _, job_hash, new_status = data.split("_")
        if user_id in applications and job_hash in applications[user_id]:
            applications[user_id][job_hash]["status"] = new_status
            save_applications_file()
            msg = f"✅ Status updated to {APP_STATUSES.get(new_status, new_status)}"
            if lang != "en": msg = await translate_text(msg, lang)
            await query.answer(msg, show_alert=True)
            # Update the message to show new status
            await query.message.edit_text(
                query.message.text.split("Status:")[0] + f"Status: `{APP_STATUSES.get(new_status, new_status)}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=query.message.reply_markup # Keep keyboard
            )
        return

    if data.startswith("remapp_"):
        job_hash = data.split("_")[1]
        if user_id in applications and job_hash in applications[user_id]:
            del applications[user_id][job_hash]
            save_applications_file()
            msg = "🗑️ Application tracker removed."
            if lang != "en": msg = await translate_text(msg, lang)
            await query.answer(msg, show_alert=True)
            await query.message.delete()
        return

    if data.startswith("page_"):
        _, page_str, target_user = data.split("_")
        page = int(page_str)
        target_uid = int(target_user)

        if target_uid not in user_sessions:
            msg = "❌ Session has expired. Please search again."
            if lang != "en": msg = await translate_text(msg, lang)
            await query.message.reply_text(msg)
            return

        session = user_sessions[target_uid]
        jobs = session["results"]

        start_idx = page * 5
        end_idx = start_idx + 5
        page_jobs = jobs[start_idx:end_idx]

        for i, job in enumerate(page_jobs, start_idx + 1):
            msg_card = await format_job_card(job, i, lang)
            keyboard = build_job_keyboard(job, lang)
            await query.message.reply_text(msg_card, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            await asyncio.sleep(0.3)

    elif data == "new_search":
        msg = "🔍 Try a new job search, for example:\n`React Developer Bangalore`"
        if lang != "en": msg = await translate_text(msg, lang)
        await query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


# ════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

async def format_job_card(job: dict, index: int, lang: str = "en") -> str:
    """Format a job dict into a beautiful Telegram message."""
    title = job.get("title", "Job Title N/A")
    company = job.get("company", "Company N/A")
    location = job.get("location", "Location N/A")
    salary = job.get("salary", "Salary not mentioned")
    description = job.get("description", "Description N/A")
    job_type = job.get("job_type", "Full-time")
    posted = job.get("posted", "")
    rating = job.get("rating", "")

    # Truncate description
    if len(description) > 300:
        description = description[:300] + "..."

    # Extract strings for translation
    labels = {
        "company_lbl": "Company:", "location_lbl": "Location:", 
        "type_lbl": "Type:", "salary_lbl": "Salary:", "desc_lbl": "Description:"
    }
    
    # Translate dynamic strings if needed
    if lang != "en":
        title = await translate_text(title, lang)
        description = await translate_text(description, lang)
        location = await translate_text(location, lang)
        salary = await translate_text(salary, lang)
        labels["company_lbl"] = await translate_text(labels["company_lbl"], lang)
        labels["location_lbl"] = await translate_text(labels["location_lbl"], lang)
        labels["type_lbl"] = await translate_text(labels["type_lbl"], lang)
        labels["salary_lbl"] = await translate_text(labels["salary_lbl"], lang)
        labels["desc_lbl"] = await translate_text(labels["desc_lbl"], lang)

    # Clean up text for Markdown
    title = str(title).replace("*", "").replace("_", " ").replace("`", "")
    company = str(company).replace("*", "").replace("_", " ")
    location = str(location).replace("*", "")

    rating_str = f" ⭐ {rating}" if rating else ""
    posted_str = f" • {posted}" if posted else ""

    card = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 *# {index}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ *{title}*\n\n"
        f"🏢 *{labels['company_lbl']}* {company}{rating_str}\n"
        f"📍 *{labels['location_lbl']}* {location}\n"
        f"💼 *{labels['type_lbl']}* {job_type}{posted_str}\n"
        f"💰 *{labels['salary_lbl']}* {salary}\n\n"
        f"📝 *{labels['desc_lbl']}*\n{description}\n"
    )
    return card


async def format_job_card_plain(job: dict, index: int, lang: str = "en") -> str:
    """Plain text job card (no markdown)."""
    title = job.get("title", "N/A")
    company = job.get("company", "N/A")
    location = job.get("location", "N/A")
    salary = job.get("salary", "Not mentioned")
    description = job.get("description", "N/A")[:250]

    if lang != "en":
        title = await translate_text(title, lang)
        description = await translate_text(description, lang)

    return (
        f"─────────────────────────\n"
        f"Job #{index}: {title}\n"
        f"Company: {company}\n"
        f"Location: {location}\n"
        f"Salary: {salary}\n"
        f"Description: {description}...\n"
        f"─────────────────────────"
    )

def build_job_keyboard(job: dict, lang: str = "en", saved_view: bool = False) -> InlineKeyboardMarkup:
    """Build inline keyboard for a job card."""
    buttons = []
    apply_url = job.get("apply_url", "")
    company_url = job.get("company_url", "")
    
    job_hash = get_job_hash(job)
    JOB_CACHE[job_hash] = job

    row1 = []
    if apply_url:
        row1.append(InlineKeyboardButton("✅ Apply Now", url=apply_url))
    if company_url:
        row1.append(InlineKeyboardButton("🏢 Company", url=company_url))

    if row1:
        buttons.append(row1)

    row2 = []
    if saved_view:
        row2.append(InlineKeyboardButton("❌ Remove Saved Job", callback_data=f"unsave_{job_hash}"))
    else:
        row2.append(InlineKeyboardButton("💾 Save Job", callback_data=f"save_{job_hash}"))
    
    row2.append(InlineKeyboardButton("✅ I Applied", callback_data=f"applied_{job_hash}"))
    buttons.append(row2)

    buttons.append([
        InlineKeyboardButton("🔍 New Search", callback_data="new_search")
    ])
    return InlineKeyboardMarkup(buttons)

# ════════════════════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ════════════════════════════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Exception: {context.error}", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        user_id = update.effective_user.id
        lang = get_user_lang(user_id) if user_id else "en"
        msg = "⚠️ An error occurred. Please type /start and try again."
        if lang != "en":
            try:
                # synchronous fallback translation if possible
                pass
            except:
                pass
        await update.message.reply_text(msg)

# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

async def send_daily_jobs(context: ContextTypes.DEFAULT_TYPE):
    """Job queue callback to send daily jobs to subscribed users."""
    logger.info("Running daily job alerts...")
    for user_id_str, query in subscriptions.items():
        try:
            lang = get_user_lang(user_id_str)
            jobs = await searcher.search_jobs(query, num_results=3) # Top 3 jobs daily
            if not jobs:
                continue

            user_id = int(user_id_str)
            header = (
                f"🌅 *Good Morning!* ☕\n\n"
                f"For your *'{query}'* subscription, here are today's top jobs:\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            if lang != "en": header = await translate_text(header, lang)
            
            await context.bot.send_message(chat_id=user_id, text=header, parse_mode=ParseMode.MARKDOWN)

            for i, job in enumerate(jobs[:3], 1):
                msg_card = await format_job_card(job, i, lang)
                keyboard = build_job_keyboard(job, lang)
                try:
                    await context.bot.send_message(chat_id=user_id, text=msg_card, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
                    await asyncio.sleep(0.4)
                except Exception as e:
                    logger.warning(f"Failed to send daily job to {user_id}: {e}")
                    plain = await format_job_card_plain(job, i, lang)
                    await context.bot.send_message(chat_id=user_id, text=plain, reply_markup=keyboard)
            
            # Small delay between users to avoid hitting Telegram API limits
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error processing daily job for user {user_id_str}: {e}")

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN .env file mein set nahi hai!")
    if not RAPIDAPI_KEY:
        raise ValueError("RAPIDAPI_KEY .env file mein set nahi hai!")

    print("[BOT] Telegram Job Search Bot starting...")
    
    # Start Health Check Server in background
    print("[WEB] Starting Health Check Server...")
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    print("[OK]  Press Ctrl+C to stop")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Schedule daily job at 9:00 AM IST
    ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    job_time = datetime.time(hour=9, minute=0, tzinfo=ist_tz)
    
    app.job_queue.run_daily(send_daily_jobs, time=job_time)

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("trending", trending_jobs))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("saved", saved_jobs_command))
    app.add_handler(CommandHandler("applications", applications_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    app.add_handler(CommandHandler("clear", clear_session))

    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback query handler
    app.add_handler(CallbackQueryHandler(callback_handler))

    # PDF Document handler for AI Resume Parsing
    app.add_handler(MessageHandler(filters.Document.PDF, handle_resume_pdf))

    # Error handler
    app.add_error_handler(error_handler)

    print("[LIVE] Bot is running! Telegram pe /start karo")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
