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

# Fix Windows console Unicode encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

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


# ════════════════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ════════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    welcome_text = (
        f"🙏 नमस्ते *{user.first_name}* जी!\n\n"
        "मैं आपका **Job Search AI Agent** हूँ 🤖\n\n"
        "मैं internet से आपके लिए jobs ढूंढता हूँ और बताता हूँ:\n"
        "📌 *Job Title & Description*\n"
        "🏢 *Company Name*\n"
        "📍 *Location / Area*\n"
        "💰 *Expected Salary*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔍 *Job Search करें:*\n"
        "बस अपनी job type लिखें, जैसे:\n\n"
        "  • `Python Developer Mumbai`\n"
        "  • `Data Scientist Bangalore remote`\n"
        "  • `Marketing Manager Delhi`\n"
        "  • `React Developer Pune`\n"
        "  • `Sales Executive Hyderabad`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *Commands:*\n"
        "/start - Bot शुरू करें\n"
        "/help - Help देखें\n"
        "/search - Job search करें\n"
        "/trending - Trending jobs देखें\n"
        "/clear - Session clear करें\n"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🆘 *Help Guide — Job Search Bot*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*🔍 Job Search कैसे करें?*\n\n"
        "Simply message box में लिखें:\n"
        "`[Job Role] [Location] [Optional: remote/full-time/part-time]`\n\n"
        "*Examples:*\n"
        "• `Software Engineer Bangalore`\n"
        "• `Data Analyst remote India`\n"
        "• `HR Manager Mumbai full-time`\n"
        "• `Node.js Developer Pune 5 lakh`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*📊 Results में मिलेगा:*\n"
        "🏷️ Job Title\n"
        "🏢 Company Name + Rating\n"
        "📍 Location\n"
        "💰 Salary Range\n"
        "📝 Job Description (Summary)\n"
        "🔗 Apply Link\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*⚙️ Commands:*\n"
        "/start - Bot restart\n"
        "/trending - Trending jobs in India\n"
        "/search `[role]` `[location]` - Direct search\n"
        "/clear - Clear your search history\n"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def trending_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trending command - show trending jobs in India."""
    await update.message.reply_text("⏳ Trending jobs India में ढूंढ रहा हूँ...", parse_mode=ParseMode.MARKDOWN)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    trending_queries = ["Software Engineer India 2025", "Data Scientist India", "Product Manager India"]
    query = trending_queries[0]

    jobs = await searcher.search_jobs(query, num_results=5)

    if not jobs:
        await update.message.reply_text("❌ अभी trending jobs नहीं मिली। बाद में try करें।")
        return

    header = "🔥 *Trending Jobs in India — 2025*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN)

    for i, job in enumerate(jobs[:5], 1):
        msg = format_job_card(job, i)
        keyboard = build_job_keyboard(job)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        await asyncio.sleep(0.3)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command."""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/search Python Developer Mumbai`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    query = " ".join(context.args)
    await perform_search(update, context, query)


async def clear_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command."""
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text("✅ आपकी search history clear हो गई!")


# ════════════════════════════════════════════════════════════════════════════
#  MESSAGE HANDLER (Main search logic)
# ════════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages as job search queries."""
    user_id = update.effective_user.id
    query = update.message.text.strip()

    if len(query) < 2:
        await update.message.reply_text("🔍 Thoda detail mein likho, jaise: `Python Developer Mumbai`", parse_mode=ParseMode.MARKDOWN)
        return

    await perform_search(update, context, query)


async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Core job search logic."""
    user_id = update.effective_user.id

    # Show typing indicator
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    # Show search message
    search_msg = await update.message.reply_text(
        f"🔍 *'{query}'* ke liye jobs search kar raha hoon...\n⏳ Please wait...",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        jobs = await searcher.search_jobs(query, num_results=8)
    except Exception as e:
        logger.error(f"Search error: {e}")
        await search_msg.edit_text("❌ Search mein kuch problem aayi. Dobara try karo!")
        return

    if not jobs:
        await search_msg.edit_text(
            f"😔 *'{query}'* ke liye jobs nahi mili.\n\n"
            "Try karo:\n"
            "• Location add karo: `Python Developer Mumbai`\n"
            "• Keywords change karo\n"
            "• Broader search: `Developer India`",
            parse_mode=ParseMode.MARKDOWN
        )
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
        f"✅ *'{query}'* ke liye *{len(jobs)} jobs* mile!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN)

    # Send each job card
    for i, job in enumerate(jobs[:5], 1):
        msg = format_job_card(job, i)
        keyboard = build_job_keyboard(job)
        try:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            await asyncio.sleep(0.4)
        except Exception as e:
            logger.warning(f"Failed to send job {i}: {e}")
            # Send without markdown if parsing fails
            plain = format_job_card_plain(job, i)
            await update.message.reply_text(plain, reply_markup=keyboard)

    # Show navigation if more results
    if len(jobs) > 5:
        nav_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Aur Jobs Dekho (6-8)", callback_data=f"page_1_{user_id}")]
        ])
        await update.message.reply_text(
            f"📋 {len(jobs) - 5} aur jobs bhi hai:",
            reply_markup=nav_keyboard
        )


# ════════════════════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER (Inline buttons)
# ════════════════════════════════════════════════════════════════════════════

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    if data.startswith("page_"):
        _, page_str, target_user = data.split("_")
        page = int(page_str)

        if user_id not in user_sessions:
            await query.message.reply_text("❌ Session expire ho gayi. Dobara search karo.")
            return

        session = user_sessions[user_id]
        jobs = session["results"]

        start_idx = page * 5
        end_idx = start_idx + 5
        page_jobs = jobs[start_idx:end_idx]

        for i, job in enumerate(page_jobs, start_idx + 1):
            msg = format_job_card(job, i)
            keyboard = build_job_keyboard(job)
            await query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            await asyncio.sleep(0.3)

    elif data == "new_search":
        await query.message.reply_text(
            "🔍 Ab naya job likh do, jaise:\n`React Developer Bangalore`",
            parse_mode=ParseMode.MARKDOWN
        )


# ════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def format_job_card(job: dict, index: int) -> str:
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

    # Clean up text for Markdown
    title = title.replace("*", "").replace("_", " ").replace("`", "")
    company = company.replace("*", "").replace("_", " ")
    location = location.replace("*", "")

    rating_str = f" ⭐ {rating}" if rating else ""
    posted_str = f" • {posted}" if posted else ""

    card = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 *Job #{index}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ *{title}*\n\n"
        f"🏢 *Company:* {company}{rating_str}\n"
        f"📍 *Location:* {location}\n"
        f"💼 *Type:* {job_type}{posted_str}\n"
        f"💰 *Salary:* {salary}\n\n"
        f"📝 *Description:*\n{description}\n"
    )
    return card


def format_job_card_plain(job: dict, index: int) -> str:
    """Plain text job card (no markdown)."""
    title = job.get("title", "N/A")
    company = job.get("company", "N/A")
    location = job.get("location", "N/A")
    salary = job.get("salary", "Not mentioned")
    description = job.get("description", "N/A")[:250]

    return (
        f"─────────────────────────\n"
        f"Job #{index}: {title}\n"
        f"Company: {company}\n"
        f"Location: {location}\n"
        f"Salary: {salary}\n"
        f"Description: {description}...\n"
        f"─────────────────────────"
    )


def build_job_keyboard(job: dict) -> InlineKeyboardMarkup:
    """Build inline keyboard for a job card."""
    buttons = []
    apply_url = job.get("apply_url", "")
    company_url = job.get("company_url", "")

    row1 = []
    if apply_url:
        row1.append(InlineKeyboardButton("✅ Apply Now", url=apply_url))
    if company_url:
        row1.append(InlineKeyboardButton("🏢 Company", url=company_url))

    if row1:
        buttons.append(row1)

    buttons.append([
        InlineKeyboardButton("🔍 Naya Search", callback_data="new_search")
    ])
    return InlineKeyboardMarkup(buttons)


# ════════════════════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ════════════════════════════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Exception: {context.error}", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ Kuch error aayi. Please /start karke dobara try karo."
        )


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN .env file mein set nahi hai!")
    if not RAPIDAPI_KEY:
        raise ValueError("RAPIDAPI_KEY .env file mein set nahi hai!")

    print("[BOT] Telegram Job Search Bot starting...")
    print("[OK]  Press Ctrl+C to stop")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("trending", trending_jobs))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("clear", clear_session))

    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback query handler
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Error handler
    app.add_error_handler(error_handler)

    print("[LIVE] Bot is running! Telegram pe /start karo")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
