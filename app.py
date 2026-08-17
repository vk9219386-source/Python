import os
import re
import sqlite3
import threading
import time
import random
import string
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError
from telegram import ChatMemberAdministrator, ChatMemberOwner, ChatMemberMember, ChatMemberRestricted
import requests
import json
import asyncio
import io
from queue import Queue

# Try to import PIL, make it optional
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available, some features may be limited")

# Configuration - Use environment variables for Plesk
BOT_TOKEN = os.getenv("BOT_TOKEN", "8559933441:AAEqrr5YvVFGSQX0xDBdkZQb0e_attc4oRo")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "vksir6206@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "851211qw")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "Enter_your_admin_id_here"))
FEEDBACK_CHANNEL_ID = int(os.getenv("FEEDBACK_CHANNEL_ID", "-1002632822134"))

# Database setup - Use absolute path for Plesk
DB_NAME = os.getenv("DB_PATH", os.path.join(os.getcwd(), "bot.db"))

# Initialize logging for Plesk
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.getcwd(), 'bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AliasGenerator:
    """Generate unique and varied Gmail aliases"""
    
    @staticmethod
    def generate_random_alias():
        """Generate a random alias using various formats"""
        formats = [
            AliasGenerator._format_word_number,
            AliasGenerator._format_adjective_noun,
            AliasGenerator._format_mixed_chars,
            AliasGenerator._format_uuid_style,
            AliasGenerator._format_timestamp_style,
            AliasGenerator._format_hex_style,
            AliasGenerator._format_pronounceable,
            AliasGenerator._format_leet_style,
            AliasGenerator._format_camel_case,
            AliasGenerator._format_snake_case
        ]
        
        # Try a few formats to ensure uniqueness
        for _ in range(3):
            chosen_format = random.choice(formats)
            alias = chosen_format()
            
            # Check if alias looks unique enough
            if AliasGenerator._is_unique_enough(alias):
                return alias
        
        # Fallback to UUID style if all else fails
        return AliasGenerator._format_uuid_style()
    
    @staticmethod
    def _format_word_number():
        """Format: word + number (e.g., 'tiger123', 'rocket456')"""
        words = [
            'tiger', 'eagle', 'dragon', 'phoenix', 'thunder', 'lightning',
            'rocket', 'star', 'moon', 'sun', 'cloud', 'storm', 'wave',
            'fire', 'ice', 'wind', 'earth', 'water', 'shadow', 'crystal',
            'diamond', 'golden', 'silver', 'bronze', 'platinum', 'titanium',
            'ninja', 'samurai', 'warrior', 'knight', 'hero', 'legend',
            'swift', 'quick', 'fast', 'rapid', 'instant', 'sudden',
            'magic', 'mystic', 'ancient', 'future', 'quantum', 'cosmic'
        ]
        word = random.choice(words)
        number = random.randint(100, 9999)
        return f"{word}{number}"
    
    @staticmethod
    def _format_adjective_noun():
        """Format: adjective + noun (e.g., 'bravetiger', 'cleverfox')"""
        adjectives = [
            'brave', 'clever', 'swift', 'quick', 'smart', 'wise', 'bold',
            'calm', 'cool', 'epic', 'fast', 'free', 'fresh', 'glad',
            'good', 'great', 'happy', 'kind', 'nice', 'proud', 'safe',
            'strong', 'true', 'wild', 'young', 'eager', 'gentle',
            'honest', 'lucky', 'noble', 'polite', 'quiet', 'rare',
            'rich', 'sharp', 'silly', 'tiny', 'vast', 'warm', 'wise'
        ]
        nouns = [
            'tiger', 'eagle', 'dragon', 'phoenix', 'fox', 'wolf', 'bear',
            'lion', 'hawk', 'falcon', 'owl', 'raven', 'crow', 'swan',
            'dove', 'star', 'moon', 'sun', 'cloud', 'storm', 'wave',
            'fire', 'ice', 'wind', 'earth', 'water', 'shadow', 'light',
            'crystal', 'diamond', 'pearl', 'ruby', 'emerald', 'sapphire',
            'ninja', 'samurai', 'warrior', 'knight', 'hero', 'legend'
        ]
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        return f"{adjective}{noun}"
    
    @staticmethod
    def _format_mixed_chars():
        """Format: mix of letters, numbers, and some uppercase (e.g., 'aX7bK9p')"""
        chars = string.ascii_lowercase + string.digits
        # Add some uppercase letters for variety
        uppercase_chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # Exclude confusing letters
        all_chars = chars + uppercase_chars
        
        length = random.randint(6, 10)
        alias = ''.join(random.choices(all_chars, k=length))
        
        # Ensure at least one number and one letter
        if not any(c.isdigit() for c in alias):
            alias = alias[:-1] + random.choice(string.digits)
        if not any(c.isalpha() for c in alias):
            alias = alias[:-1] + random.choice(string.ascii_lowercase)
        
        return alias
    
    @staticmethod
    def _format_uuid_style():
        """Format: UUID-like (e.g., 'a1b2c3d4')"""
        chars = string.ascii_lowercase + string.digits
        parts = []
        for _ in range(4):
            part = ''.join(random.choices(chars, k=2))
            parts.append(part)
        return ''.join(parts)
    
    @staticmethod
    def _format_timestamp_style():
        """Format: timestamp-based (e.g., 'dec31-2345')"""
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        month = random.choice(months)
        day = random.randint(1, 28)
        number = random.randint(100, 9999)
        return f"{month}{day}-{number}"
    
    @staticmethod
    def _format_hex_style():
        """Format: hexadecimal style (e.g., 'a1f4b8')"""
        hex_chars = '0123456789abcdef'
        length = random.randint(6, 8)
        return ''.join(random.choices(hex_chars, k=length))
    
    @staticmethod
    def _format_pronounceable():
        """Format: pronounceable random strings (e.g., 'zokita', 'mavexi')"""
        consonants = 'bcdfghjklmnpqrstvwxyz'
        vowels = 'aeiou'
        length = random.randint(6, 9)
        alias = ''
        
        for i in range(length):
            if i % 2 == 0:
                alias += random.choice(consonants)
            else:
                alias += random.choice(vowels)
        
        # Add a number at the end
        alias += str(random.randint(1, 99))
        return alias
    
    @staticmethod
    def _format_leet_style():
        """Format: leet speak style (e.g., 'h4ck3r', 'pr0gr4m')"""
        leet_map = {
            'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5',
            't': '7', 'l': '1', 'g': '9', 'z': '2'
        }
        
        base_words = [
            'hacker', 'program', 'coder', 'developer', 'system',
            'network', 'server', 'client', 'user', 'admin',
            'master', 'expert', 'pro', 'elite', 'ninja', 'guru'
        ]
        
        word = random.choice(base_words)
        # Convert some letters to leet
        leet_word = ''
        for char in word:
            if char in leet_map and random.random() < 0.5:  # 50% chance to convert
                leet_word += leet_map[char]
            else:
                leet_word += char
        
        # Add number if too short
        if len(leet_word) < 6:
            leet_word += str(random.randint(10, 99))
        
        return leet_word
    
    @staticmethod
    def _format_camel_case():
        """Format: camelCase style (e.g., 'swiftTiger', 'quickFox')"""
        adjectives = [
            'swift', 'quick', 'fast', 'rapid', 'instant', 'sudden',
            'magic', 'mystic', 'ancient', 'future', 'quantum', 'cosmic',
            'brave', 'clever', 'smart', 'wise', 'bold', 'calm'
        ]
        nouns = [
            'tiger', 'eagle', 'dragon', 'phoenix', 'fox', 'wolf',
            'hero', 'star', 'moon', 'sun', 'storm', 'wave'
        ]
        
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        
        # Capitalize first letter of noun
        noun = noun.capitalize()
        
        alias = adjective + noun
        
        # Add number if needed
        if random.random() < 0.3:  # 30% chance to add number
            alias += str(random.randint(1, 99))
        
        return alias
    
    @staticmethod
    def _format_snake_case():
        """Format: snake_case style (e.g., 'swift_tiger', 'quick_fox')"""
        adjectives = [
            'swift', 'quick', 'fast', 'rapid', 'instant', 'sudden',
            'magic', 'mystic', 'ancient', 'future', 'quantum', 'cosmic',
            'brave', 'clever', 'smart', 'wise', 'bold', 'calm'
        ]
        nouns = [
            'tiger', 'eagle', 'dragon', 'phoenix', 'fox', 'wolf',
            'hero', 'star', 'moon', 'sun', 'storm', 'wave'
        ]
        
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        
        alias = f"{adjective}_{noun}"
        
        # Add number if needed
        if random.random() < 0.3:  # 30% chance to add number
            alias += f"_{random.randint(1, 99)}"
        
        return alias
    
    @staticmethod
    def _is_unique_enough(alias):
        """Check if alias is unique enough (not too simple or repetitive)"""
        # Check minimum length
        if len(alias) < 6:
            return False
        
        # Check for too many repeating characters
        if len(set(alias)) < len(alias) * 0.4:  # Less than 40% unique chars
            return False
        
        # Check for common patterns
        common_patterns = [
            r'^[a-z]+$',  # All lowercase only
            r'^[0-9]+$',  # All numbers only
            r'(.)\1{3,}',  # 4 or more repeating chars
            r'123', r'abc', r'qwe', r'asd', r'zxc'  # Common sequences
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, alias):
                return False
        
        return True

class NotificationQueue:
    """Queue for handling notifications from Gmail thread to bot thread"""
    def __init__(self):
        self.queue = Queue()
        self.bot = None
        self.application = None
    
    def set_bot(self, application):
        """Set the bot application for sending notifications"""
        self.application = application
    
    def add_notification(self, user_id, notification_type, data):
        """Add a notification to the queue"""
        self.queue.put({
            'user_id': user_id,
            'type': notification_type,
            'data': data,
            'timestamp': time.time()
        })
    
    async def process_notifications(self):
        """Process all pending notifications"""
        while not self.queue.empty():
            try:
                notification = self.queue.get_nowait()
                await self._send_notification(notification)
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
    
    async def _send_notification(self, notification):
        """Send a single notification"""
        if not self.application:
            logger.warning("Bot application not set, cannot send notification")
            return
        
        try:
            user_id = notification['user_id']
            notification_type = notification['type']
            data = notification['data']
            
            if notification_type == 'otp':
                await self._send_otp_notification(user_id, data)
            elif notification_type == 'message':
                await self._send_message_notification(user_id, data)
                
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def _send_otp_notification(self, user_id, data):
        """Send OTP notification to user"""
        try:
            alias_name = data.get('alias_name')
            otp_code = data.get('otp_code')
            verification_links = data.get('verification_links', [])
            subject = data.get('subject', 'No Subject')
            
            # Create notification message
            notification = f"🔔 **New OTP/Verification Received!**\n\n"
            notification += f"📧 **Alias:** `{alias_name}`\n"
            notification += f"📨 **Subject:** {subject}\n\n"
            
            if otp_code:
                notification += f"🔑 **OTP Code:** `{otp_code}`\n\n"
            
            if verification_links:
                notification += "🔗 **Verification Links:**\n"
                for i, link in enumerate(verification_links[:3]):  # Show max 3 links
                    notification += f"• [Link {i+1}]({link})\n"
                notification += "\n"
            
            notification += "💡 *Use /otp to view all codes*\n"
            notification += "⏰ *Auto-expires in 1 hour*"
            
            # Create inline keyboard
            keyboard = []
            row = []
            
            if otp_code:
                row.append(InlineKeyboardButton("📋 Copy OTP", callback_data=f"quick_copy_otp_{otp_code}"))
            
            if verification_links:
                row.append(InlineKeyboardButton("🔗 Copy Link", callback_data=f"quick_copy_link_{verification_links[0][:30]}"))
            
            if row:
                keyboard.append(row)
            
            keyboard.append([
                InlineKeyboardButton("👀 View Messages", callback_data=f"view_{alias_name}"),
                InlineKeyboardButton("🔑 All OTPs", callback_data="view_otp")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send notification
            await self.application.bot.send_message(
                chat_id=user_id,
                text=notification,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            logger.info(f"Sent OTP notification to user {user_id} for alias {alias_name}")
            
        except Exception as e:
            logger.error(f"Failed to send OTP notification: {e}")
    
    async def _send_message_notification(self, user_id, data):
        """Send regular message notification"""
        try:
            alias_name = data.get('alias_name')
            subject = data.get('subject', 'No Subject')
            
            notification = f"📧 **New Email Received**\n\n"
            notification += f"📧 **Alias:** `{alias_name}`\n"
            notification += f"📨 **Subject:** {subject}\n\n"
            notification += "💡 *Use /view to read the message*"
            
            await self.application.bot.send_message(
                chat_id=user_id,
                text=notification,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Failed to send message notification: {e}")

# Global notification queue
notification_queue = NotificationQueue()

class DatabaseManager:
    def __init__(self):
        self.db_path = DB_NAME
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to database with retry logic"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
                logger.info(f"Connected to database at {self.db_path}")
                return True
            except Exception as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e
        return False
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                banned BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Aliases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aliases (
                alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                alias_name TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Add active column if it doesn't exist
        cursor.execute('PRAGMA table_info(aliases)')
        columns = [col[1] for col in cursor.fetchall()]
        if 'active' not in columns:
            cursor.execute('ALTER TABLE aliases ADD COLUMN active BOOLEAN DEFAULT TRUE')
            logger.info("Added 'active' column to aliases table")
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                alias_id INTEGER,
                email_subject TEXT,
                email_body TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                seen BOOLEAN DEFAULT FALSE,
                otp_code TEXT,
                verification_links TEXT,
                FOREIGN KEY (alias_id) REFERENCES aliases (alias_id)
            )
        ''')
        
        # Add otp_code and verification_links columns if they don't exist
        cursor.execute('PRAGMA table_info(messages)')
        message_columns = [col[1] for col in cursor.fetchall()]
        if 'otp_code' not in message_columns:
            cursor.execute('ALTER TABLE messages ADD COLUMN otp_code TEXT')
            logger.info("Added 'otp_code' column to messages table")
        if 'verification_links' not in message_columns:
            cursor.execute('ALTER TABLE messages ADD COLUMN verification_links TEXT')
            logger.info("Added 'verification_links' column to messages table")
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Check and add feedback_photo_id column if it doesn't exist
        cursor.execute('PRAGMA table_info(feedback)')
        feedback_columns = [col[1] for col in cursor.fetchall()]
        if 'feedback_photo_id' not in feedback_columns:
            cursor.execute('ALTER TABLE feedback ADD COLUMN feedback_photo_id TEXT')
            logger.info("Added 'feedback_photo_id' column to feedback table")
        
        self.conn.commit()
    
    def add_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        self.conn.commit()
    
    def is_user_banned(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT banned FROM users WH