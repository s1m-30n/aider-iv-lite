import os
import json
import asyncio
import threading
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv

from telegram.constants import ParseMode

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = "subscribers.json"

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.subscribers = self._load_subscribers()
        self.app = None
        self.loop = None
        self.thread = None
        self.running = False

        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not found in environment variables. Bot will not start.")

    def _load_subscribers(self):
        if os.path.exists(SUBSCRIBERS_FILE):
            try:
                with open(SUBSCRIBERS_FILE, "r") as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Failed to load subscribers: {e}")
                return set()
        return set()

    def _save_subscribers(self):
        try:
            with open(SUBSCRIBERS_FILE, "w") as f:
                json.dump(list(self.subscribers), f)
        except Exception as e:
            logger.error(f"Failed to save subscribers: {e}")

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id not in self.subscribers:
            self.subscribers.add(chat_id)
            self._save_subscribers()
            await context.bot.send_message(chat_id=chat_id, text="✅ <b>You are now subscribed to trading signals!</b>", parse_mode=ParseMode.HTML)
            logger.info(f"New subscriber: {chat_id}")
        else:
            await context.bot.send_message(chat_id=chat_id, text="ℹ️ <i>You are already subscribed.</i>", parse_mode=ParseMode.HTML)

    async def _broadcast(self, message: str):
        if not self.app:
            return
            
        # We need to copy subscribers to avoid runtime modification issues if we were to change it
        # though here we are just reading.
        for chat_id in self.subscribers:
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Failed to send message to {chat_id}: {e}")

    def start(self):
        if not self.token:
            return

        if self.running:
            return

        self.running = True
        
        # Create a new event loop for the thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_bot, args=(self.loop,), daemon=True)
        self.thread.start()
        logger.info("Telegram Bot started in background thread.")

    def _run_bot(self, loop):
        asyncio.set_event_loop(loop)
        
        self.app = ApplicationBuilder().token(self.token).build()
        
        start_handler = CommandHandler('start', self._start_command)
        self.app.add_handler(start_handler)
        
        # Run polling
        logger.info("Bot polling started...")
        self.app.run_polling()

    def send_signal(self, message: str):
        """
        Thread-safe method to send a signal to all subscribers.
        """
        if not self.running or not self.app:
            logger.warning("Bot is not running, cannot send signal.")
            return

        # Since run_polling blocks and manages the loop, we need to be careful.
        # However, python-telegram-bot's Application is designed to be async.
        # If we are calling this from a sync thread (main loop), we need to schedule 
        # the coroutine in the bot's loop.
        
        # Note: self.app.run_polling() creates its own loop if not provided, 
        # or uses the current one. In _run_bot we set the loop.
        
        # But run_polling() is blocking. We can't easily inject tasks into it from outside 
        # unless we have access to the loop it's using.
        
        # A safer approach for simple broadcasting from another thread is to use 
        # asyncio.run_coroutine_threadsafe
        
        # Wait, self.app.run_polling() might close the loop when done? 
        # Actually, we can just use the loop we created.
        
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._broadcast(message), self.loop)
        else:
            logger.error("Bot loop is not running.")

    def stop(self):
        self.running = False
        # Stopping run_polling from another thread is tricky. 
        # Usually we just let it die with the daemon thread or use app.stop() if accessible.
        if self.app:
            # This might need to be awaited or scheduled
            pass

    def format_status_message(self, market_data: dict) -> str:
        """
        Format market status into a beautiful HTML message.
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%H:%M')
        message = f"📊 <b>Market Update</b> ({timestamp})\n\n"
        message += "<pre>"
        # Header: Sym | Price | Bias | Sig | Risk
        message += f"{'Sym':<5} | {'Bias':<4} | {'Sig':<4} | {'Risk':<4}\n"
        message += "-" * 28 + "\n"
        
        for symbol, data in market_data.items():
            # Shorten symbol name (e.g., "Boom 1000 Index" -> "B1000")
            short_symbol = symbol.replace("Boom ", "B").replace("Crash ", "C").replace(" Index", "")
            
            # price = f"{data.get('price', 0):.1f}" # Removing price to save space if needed, or keeping it?
            # User asked for "full table section plus signal and bias".
            # Let's try to fit: Sym | Price | Bias | Sig | Risk
            # B1000 | 12345 | BUY  | BUY  | 🔴85%
            # 6 + 7 + 5 + 5 + 5 = 28 chars. Fits easily.
            
            price = f"{data.get('price', 0):.0f}" # Int price to save space? Or .1f
            if len(price) > 6:
                price = f"{data.get('price', 0):.0f}"
            
            bias = data.get('bias', 'N/A')[:3].upper() # Limit to 3 chars (NEU, BUY, SEL)
            if bias == "NEU": bias = "-"
            
            signal = data.get('signal', 'None')
            if signal == 'None':
                sig_str = "-"
            else:
                sig_str = signal[:3].upper() # BUY/SEL
            
            spike_prob = data.get('spike_prob', 0)
            
            # Add risk indicator
            risk_icon = ""
            if spike_prob >= 70:
                risk_icon = "🔴"
            elif spike_prob >= 30:
                risk_icon = "🟠"
            else:
                risk_icon = "🟢"
                
            # Format row
            # B1000 | 12345 | BUY | BUY | 🔴85%
            row = f"{short_symbol:<5} | {price:<5} | {bias:<3} | {sig_str:<3} | {risk_icon}{int(spike_prob)}%\n"
            message += row
            
        message += "</pre>"
        return message
