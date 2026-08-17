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
    logging.warning('PIL not available, some features may be limited')

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8559933441:AAEqrr5YvVFGSQX0xDBdkZQb0e_attc4oRo")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "vksir6206@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "851211qw")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

# Fix ADMIN_USER_ID to handle string fallback gracefully
_admin_id_str = os.getenv("ADMIN_USER_ID", "6104320886")
try:
    ADMIN_USER_ID = int(_admin_id_str)
except ValueError:
    ADMIN_USER_ID = 6104320886

# Fix FEEDBACK_CHANNEL_ID to handle string fallback gracefully
_feedback_str = os.getenv("FEEDBACK_CHANNEL_ID", "-1002632822134")
try:
    FEEDBACK_CHANNEL_ID = int(_feedback_str)
except ValueError:
    FEEDBACK_CHANNEL_ID = -1002632822134

DB_NAME = os.getenv("DB_PATH", os.path.join(os.getcwd(), "bot.db"))

# Initialize logging
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
        for _ in range(3):
            chosen_format = random.choice(formats)
            alias = chosen_format()
            if AliasGenerator._is_unique_enough(alias):
                return alias
        return AliasGenerator._format_uuid_style()

    @staticmethod
    def _format_word_number():
        words = ['tiger', 'eagle', 'dragon', 'phoenix', 'thunder', 'lightning',
                 'rocket', 'star', 'moon', 'sun', 'cloud', 'storm', 'wave',
                 'fire', 'ice', 'wind', 'earth', 'water', 'shadow', 'crystal',
                 'diamond', 'golden', 'silver', 'bronze', 'platinum', 'titanium',
                 'ninja', 'samurai', 'warrior', 'knight', 'hero', 'legend',
                 'swift', 'quick', 'fast', 'rapid', 'instant', 'sudden',
                 'magic', 'mystic', 'ancient', 'future', 'quantum', 'cosmic']
        return f'{random.choice(words)}{random.randint(100, 9999)}'

    @staticmethod
    def _format_adjective_noun():
        adjectives = ['brave', 'clever', 'swift', 'quick', 'smart', 'wise', 'bold',
                      'calm', 'cool', 'epic', 'fast', 'free', 'fresh', 'glad',
                      'good', 'great', 'happy', 'kind', 'nice', 'proud', 'safe',
                      'strong', 'true', 'wild', 'young', 'eager', 'gentle',
                      'honest', 'lucky', 'noble', 'polite', 'quiet', 'rare',
                      'rich', 'sharp', 'silly', 'tiny', 'vast', 'warm', 'wise']
        nouns = ['tiger', 'eagle', 'dragon', 'phoenix', 'fox', 'wolf', 'bear',
                 'lion', 'hawk', 'falcon', 'owl', 'raven', 'crow', 'swan',
                 'dove', 'star', 'moon', 'sun', 'cloud', 'storm', 'wave',
                 'fire', 'ice', 'wind', 'earth', 'water', 'shadow', 'light',
                 'crystal', 'diamond', 'pearl', 'ruby', 'emerald', 'sapphire',
                 'ninja', 'samurai', 'warrior', 'knight', 'hero', 'legend']
        return f'{random.choice(adjectives)}{random.choice(nouns)}'

    @staticmethod
    def _format_mixed_chars():
        chars = string.ascii_lowercase + string.digits
        uppercase_chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
        all_chars = chars + uppercase_chars
        length = random.randint(6, 10)
        alias = ''.join(random.choices(all_chars, k=length))
        if not any(c.isdigit() for c in alias):
            alias = alias[:-1] + random.choice(string.digits)
        if not any(c.isalpha() for c in alias):
            alias = alias[:-1] + random.choice(string.ascii_lowercase)
        return alias

    @staticmethod
    def _format_uuid_style():
        chars = string.ascii_lowercase + string.digits
        parts = [''.join(random.choices(chars, k=2)) for _ in range(4)]
        return ''.join(parts)

    @staticmethod
    def _format_timestamp_style():
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        return f'{random.choice(months)}{random.randint(1, 28)}-{random.randint(100, 9999)}'

    @staticmethod
    def _format_hex_style():
        return ''.join(random.choices('0123456789abcdef', k=random.randint(6, 8)))

    @staticmethod
    def _format_pronounceable():
        consonants = 'bcdfghjklmnpqrstvwxyz'
        vowels = 'aeiou'
        length = random.randint(6, 9)
        alias = ''.join(random.choice(consonants if i % 2 == 0 else vowels) for i in range(length))
        return alias + str(random.randint(1, 99))

    @staticmethod
    def _format_leet_style():
        leet_map = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5',
                    't': '7', 'l': '1', 'g': '9', 'z': '2'}
        base_words = ['hacker', 'program', 'coder', 'developer', 'system',
                      'network', 'server', 'client', 'user', 'admin',
                      'master', 'expert', 'pro', 'elite', 'ninja', 'guru']
        word = random.choice(base_words)
        leet_word = ''.join(leet_map.get(char, char) if random.random() < 0.5 else char for char in word)
        if len(leet_word) < 6:
            leet_word += str(random.randint(10, 99))
        return leet_word

    @staticmethod
    def _format_camel_case():
        adjectives = ['swift', 'quick', 'fast', 'rapid', 'instant', 'sudden',
                      'magic', 'mystic', 'ancient', 'future', 'quantum', 'cosmic',
                      'brave', 'clever', 'smart', 'wise', 'bold', 'calm']
        nouns = ['tiger', 'eagle', 'dragon', 'phoenix', 'fox', 'wolf',
                 'hero', 'star', 'moon', 'sun', 'storm', 'wave']
        alias = random.choice(adjectives) + random.choice(nouns).capitalize()
        if random.random() < 0.3:
            alias += str(random.randint(1, 99))
        return alias

    @staticmethod
    def _format_snake_case():
        adjectives = ['swift', 'quick', 'fast', 'rapid', 'instant', 'sudden',
                      'magic', 'mystic', 'ancient', 'future', 'quantum', 'cosmic',
                      'brave', 'clever', 'smart', 'wise', 'bold', 'calm']
        nouns = ['tiger', 'eagle', 'dragon', 'phoenix', 'fox', 'wolf',
                 'hero', 'star', 'moon', 'sun', 'storm', 'wave']
        alias = f'{random.choice(adjectives)}_{random.choice(nouns)}'
        if random.random() < 0.3:
            alias += f'_{random.randint(1, 99)}'
        return alias

    @staticmethod
    def _is_unique_enough(alias):
        if len(alias) < 6:
            return False
        if len(set(alias)) < len(alias) * 0.4:
            return False
        common_patterns = [r'^[a-z]+$', r'^[0-9]+$', r'(.)\1{3,}',
                           r'123', r'abc', r'qwe', r'asd', r'zxc']
        for pattern in common_patterns:
            if re.search(pattern, alias):
                return False
        return True

class NotificationQueue:
    def __init__(self):
        self.queue = Queue()
        self.application = None

    def set_bot(self, application):
        self.application = application

    def add_notification(self, user_id, notification_type, data):
        self.queue.put({
            'user_id': user_id,
            'type': notification_type,
            'data': data,
            'timestamp': time.time()
        })

    async def process_notifications(self):
        while not self.queue.empty():
            try:
                notification = self.queue.get_nowait()
                await self._send_notification(notification)
            except Exception as e:
                logger.error(f'Error processing notification: {e}')

    async def _send_notification(self, notification):
        if not self.application:
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
            logger.error(f'Failed to send notification: {e}')

    async def _send_otp_notification(self, user_id, data):
        try:
            alias_name = data.get('alias_name')
            otp_code = data.get('otp_code')
            verification_links = data.get('verification_links', [])
            subject = data.get('subject', 'No Subject')

            notification = f'🔔 **New OTP/Verification Received!**\n\n'
            notification += f'📧 **Alias:** `{alias_name}`\n'
            notification += f'📨 **Subject:** {subject}\n\n'
            if otp_code:
                notification += f'🔑 **OTP Code:** `{otp_code}`\n\n'
            if verification_links:
                notification += '🔗 **Verification Links:**\n'
                for i, link in enumerate(verification_links[:3]):
                    notification += f'• [Link {i+1}]({link})\n'
                notification += '\n'
            notification += '💡 *Use /otp to view all codes*\n'
            notification += '⏰ *Auto-expires in 1 hour*'

            keyboard = []
            row = []
            if otp_code:
                row.append(InlineKeyboardButton('📋 Copy OTP', callback_data=f'quick_copy_otp_{otp_code}'))
            if verification_links:
                row.append(InlineKeyboardButton('🔗 Copy Link', callback_data=f'quick_copy_link_{verification_links[0][:30]}'))
            if row:
                keyboard.append(row)
            keyboard.append([
                InlineKeyboardButton('👀 View Messages', callback_data=f'view_{alias_name}'),
                InlineKeyboardButton('🔑 All OTPs', callback_data='view_otp')
            ])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await self.application.bot.send_message(
                chat_id=user_id,
                text=notification,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            logger.info(f'Sent OTP notification to user {user_id} for alias {alias_name}')
        except Exception as e:
            logger.error(f'Failed to send OTP notification: {e}')

    async def _send_message_notification(self, user_id, data):
        try:
            alias_name = data.get('alias_name')
            subject = data.get('subject', 'No Subject')
            notification = f'📧 **New Email Received**\n\n'
            notification += f'📧 **Alias:** `{alias_name}`\n'
            notification += f'📨 **Subject:** {subject}\n\n'
            notification += '💡 *Use /view to read the message*'
            await self.application.bot.send_message(
                chat_id=user_id,
                text=notification,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f'Failed to send message notification: {e}')

notification_queue = NotificationQueue()

class DatabaseManager:
    def __init__(self):
        self.db_path = DB_NAME
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
                logger.info(f'Connected to database at {self.db_path}')
                return True
            except Exception as e:
                logger.error(f'Database connection attempt {attempt + 1} failed: {e}')
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise e
        return False

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                banned BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aliases (
                alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                alias_name TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback_text TEXT,
                feedback_photo_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        self.conn.commit()

    def add_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        self.conn.commit()

    def is_user_banned(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else False

    def ban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET banned = TRUE WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def unban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET banned = FALSE WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def add_alias(self, user_id, alias_name):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO aliases (user_id, alias_name) VALUES (?, ?)', (user_id, alias_name))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_aliases(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT alias_name, active, created_at FROM aliases WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        return cursor.fetchall()

    def get_alias_by_name(self, alias_name):
        cursor = self.conn.cursor()
        cursor.execute('SELECT alias_id, user_id, alias_name FROM aliases WHERE alias_name = ?', (alias_name,))
        return cursor.fetchone()

    def delete_alias(self, alias_name):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM aliases WHERE alias_name = ?', (alias_name,))
        self.conn.commit()

    def add_message(self, alias_id, subject, body, otp_code=None, verification_links=None):
        cursor = self.conn.cursor()
        links_str = json.dumps(verification_links) if verification_links else None
        cursor.execute(
            'INSERT INTO messages (alias_id, email_subject, email_body, otp_code, verification_links) VALUES (?, ?, ?, ?, ?)',
            (alias_id, subject, body, otp_code, links_str)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_messages_for_alias(self, alias_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT m.email_subject, m.email_body, m.received_at, m.seen, m.otp_code, m.verification_links
            FROM messages m
            JOIN aliases a ON m.alias_id = a.alias_id
            WHERE a.alias_name = ?
            ORDER BY m.received_at DESC
        ''', (alias_name,))
        return cursor.fetchall()

    def get_otps_for_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT m.otp_code, m.email_subject, a.alias_name, m.received_at
            FROM messages m
            JOIN aliases a ON m.alias_id = a.alias_id
            WHERE a.user_id = ? AND m.otp_code IS NOT NULL
            ORDER BY m.received_at DESC
            LIMIT 20
        ''', (user_id,))
        return cursor.fetchall()

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, banned, created_at FROM users ORDER BY created_at DESC')
        return cursor.fetchall()

    def add_feedback(self, user_id, feedback_text, photo_id=None):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO feedback (user_id, feedback_text, feedback_photo_id) VALUES (?, ?, ?)',
                       (user_id, feedback_text, photo_id))
        self.conn.commit()

    def get_stats(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM aliases')
        total_aliases = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM messages')
        total_messages = cursor.fetchone()[0]
        return total_users, total_aliases, total_messages

db = DatabaseManager()

def extract_otp(text):
    """Extract OTP codes from email text"""
    if not text:
        return None

    otp_patterns = [
        r'(?:otp|verification|confirm|auth|security|access|login|signin)[^\d]{0,20}(?:code|pin|number|token|key|pass|password)[^\d]{0,10}[:\s#]*(\d{4,8})',
        r'(?:code|pin|token|key)[^\d]{0,10}[:\s#]*(\d{4,8})',
        r'(?:is|\:)[\s]*(\d{4,8})(?![\d])',
        r'\b(\d{4,8})\b[^\d]{0,30}(?:otp|verification|code|token)',
        r'(?:your|the)[\s]+(?:otp|code|pin|token)[\s]+(?:is|\:)[\s]*(\d{4,8})',
    ]

    for pattern in otp_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    codes = re.findall(r'\b(\d{4,8})\b', text)
    for code in codes:
        if code in ['2024', '2025', '2026', '2027', '1234', '0000', '1111', '9999']:
            continue
        if len(code) >= 4:
            return code

    return None

def extract_links(text):
    """Extract verification links from email text"""
    if not text:
        return []

    url_pattern = r'https?://[^\s<>"\']{10,500}'
    urls = re.findall(url_pattern, text)

    verification_keywords = ['verify', 'confirm', 'activate', 'validate', 'auth', 'token', 'otp', 'code', 'login', 'signin', 'reset']
    verification_links = []

    for url in urls:
        url_lower = url.lower()
        if any(kw in url_lower for kw in verification_keywords):
            verification_links.append(url)

    if not verification_links and urls:
        return urls[:3]

    return verification_links[:5]

def check_gmail():
    """Check Gmail inbox for new emails to aliases"""
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        mail.select('inbox')

        status, messages = mail.search(None, 'UNSEEN')

        if status != 'OK' or not messages[0]:
            mail.logout()
            return

        email_ids = messages[0].split()

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            to_header = msg.get('To', '')

            alias_match = re.search(r'([^+@]+)\+([^@]+)@', to_header)
            if not alias_match:
                continue

            alias_name = alias_match.group(2)
            alias_data = db.get_alias_by_name(alias_name)
            if not alias_data:
                continue

            alias_id, user_id, _ = alias_data

            subject = ''
            subject_header = msg.get('Subject', '')
            if subject_header:
                decoded = decode_header(subject_header)
                for part, charset in decoded:
                    if isinstance(part, bytes):
                        subject += part.decode(charset or 'utf-8', errors='replace')
                    else:
                        subject += part

            body = ''
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain' or content_type == 'text/html':
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or 'utf-8'
                                body += payload.decode(charset, errors='replace')
                        except:
                            pass
            else:
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        charset = msg.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                except:
                    pass

            otp_code = extract_otp(body) or extract_otp(subject)
            verification_links = extract_links(body)

            db.add_message(alias_id, subject, body, otp_code, verification_links)

            notification_data = {
                'alias_name': alias_name,
                'otp_code': otp_code,
                'verification_links': verification_links,
                'subject': subject
            }

            if otp_code:
                notification_queue.add_notification(user_id, 'otp', notification_data)
            else:
                notification_queue.add_notification(user_id, 'message', notification_data)

            logger.info(f'Processed email for alias {alias_name}, OTP: {otp_code}')

        mail.logout()
    except Exception as e:
        logger.error(f'Error checking Gmail: {e}')

def gmail_checker_thread():
    """Background thread to check Gmail periodically"""
    while True:
        try:
            check_gmail()
        except Exception as e:
            logger.error(f'Gmail checker error: {e}')
        time.sleep(30)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if db.is_user_banned(user_id):
        await update.message.reply_text('❌ You are banned from using this bot.')
        return
    db.add_user(user_id)

    welcome_text = (
        '👋 **Welcome to the Gmail Alias Bot!**\n\n'
        '📧 Generate unlimited Gmail aliases\n'
        '🔑 Receive OTPs and verification codes\n'
        '📨 Read emails sent to your aliases\n\n'
        '**Commands:**\n'
        '/newalias - Generate a new alias\n'
        '/myaliases - List your aliases\n'
        '/otp - View recent OTPs\n'
        '/view <alias> - View messages for an alias\n'
        '/delalias <alias> - Delete an alias\n'
        '/feedback - Send feedback\n'
        '/help - Show help\n\n'
        '💡 All aliases are in format:\n'
        f'`{GMAIL_EMAIL.split("@")[0]}+alias@gmail.com`'
    )

    keyboard = [
        [InlineKeyboardButton('➕ New Alias', callback_data='new_alias'),
         InlineKeyboardButton('📋 My Aliases', callback_data='my_aliases')],
        [InlineKeyboardButton('🔑 OTPs', callback_data='view_otp'),
         InlineKeyboardButton('❓ Help', callback_data='help')]
    ]

    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def newalias_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if db.is_user_banned(user_id):
        await update.message.reply_text('❌ You are banned.')
        return
    db.add_user(user_id)

    max_attempts = 10
    alias_name = None
    for _ in range(max_attempts):
        candidate = AliasGenerator.generate_random_alias()
        if db.add_alias(user_id, candidate):
            alias_name = candidate
            break

    if not alias_name:
        await update.message.reply_text('❌ Failed to generate unique alias. Please try again.')
        return

    full_email = f'{GMAIL_EMAIL.split("@")[0]}+{alias_name}@gmail.com'

    text = (
        f'✅ **New Alias Generated!**\n\n'
        f'📧 **Alias:** `{alias_name}`\n'
        f'📨 **Email:** `{full_email}`\n\n'
        f'💡 Use this email to receive OTPs and messages.\n'
        f'⏰ Messages auto-delete after 1 hour.'
    )

    keyboard = [
        [InlineKeyboardButton('📋 Copy Email', callback_data=f'copy_email_{alias_name}')],
        [InlineKeyboardButton('📋 Copy Alias', callback_data=f'copy_alias_{alias_name}')],
        [InlineKeyboardButton('👀 View Messages', callback_data=f'view_{alias_name}')]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def myaliases_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    aliases = db.get_aliases(user_id)

    if not aliases:
        await update.message.reply_text('📭 You have no aliases yet. Use /newalias to create one.')
        return

    text = '📧 **Your Aliases:**\n\n'
    keyboard = []

    for alias_name, active, created_at in aliases:
        status = '🟢' if active else '🔴'
        text += f'{status} `{alias_name}`\n'
        keyboard.append([InlineKeyboardButton(f'👀 {alias_name}', callback_data=f'view_{alias_name}')])

    keyboard.append([InlineKeyboardButton('➕ New Alias', callback_data='new_alias')])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def otp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    otps = db.get_otps_for_user(user_id)

    if not otps:
        await update.message.reply_text('🔑 No OTPs found. Use /newalias to create an alias and wait for emails.')
        return

    text = '🔑 **Recent OTPs:**\n\n'

    for otp_code, subject, alias_name, received_at in otps[:10]:
        text += f'📧 `{alias_name}`\n'
        text += f'🔑 **Code:** `{otp_code}`\n'
        text += f'📨 {subject}\n'
        text += f'🕐 {received_at}\n\n'

    await update.message.reply_text(text, parse_mode='Markdown')

async def view_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text('📧 Usage: /view <alias_name>\nExample: /view tiger123')
        return

    alias_name = context.args[0].strip()
    alias_data = db.get_alias_by_name(alias_name)

    if not alias_data or alias_data[1] != user_id:
        await update.message.reply_text('❌ Alias not found or does not belong to you.')
        return

    messages = db.get_messages_for_alias(alias_name)

    if not messages:
        await update.message.reply_text(f'📭 No messages found for `{alias_name}`.', parse_mode='Markdown')
        return

    text = f'📨 **Messages for `{alias_name}`:**\n\n'

    for subject, body, received_at, seen, otp_code, links_json in messages[:5]:
        text += f'📧 **Subject:** {subject}\n'
        if otp_code:
            text += f'🔑 **OTP:** `{otp_code}`\n'
        text += f'🕐 {received_at}\n'
        text += '━' * 20 + '\n\n'

    keyboard = [[InlineKeyboardButton('🔄 Refresh', callback_data=f'view_{alias_name}')]]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def delalias_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text('🗑 Usage: /delalias <alias_name>')
        return

    alias_name = context.args[0].strip()
    alias_data = db.get_alias_by_name(alias_name)

    if not alias_data or alias_data[1] != user_id:
        await update.message.reply_text('❌ Alias not found or does not belong to you.')
        return

    db.delete_alias(alias_name)
    await update.message.reply_text(f'🗑 Alias `{alias_name}` deleted.', parse_mode='Markdown')

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('📝 Please send your feedback as a message or photo.')
    context.user_data['awaiting_feedback'] = True

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        '📖 **Bot Commands**\n\n'
        '/start - Start the bot\n'
        '/newalias - Generate new Gmail alias\n'
        '/myaliases - List your aliases\n'
        '/otp - View recent OTP codes\n'
        '/view <alias> - View messages for alias\n'
        '/delalias <alias> - Delete an alias\n'
        '/feedback - Send feedback\n'
        '/help - Show this help\n\n'
        '💡 Aliases work with Gmail\'s + trick:\n'
        f'`{GMAIL_EMAIL.split("@")[0]}+alias@gmail.com`'
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if db.is_user_banned(user_id):
        await query.edit_message_text('❌ You are banned.')
        return

    if data == 'new_alias':
        max_attempts = 10
        alias_name = None
        for _ in range(max_attempts):
            candidate = AliasGenerator.generate_random_alias()
            if db.add_alias(user_id, candidate):
                alias_name = candidate
                break

        if not alias_name:
            await query.edit_message_text('❌ Failed to generate alias. Try again.')
            return

        full_email = f'{GMAIL_EMAIL.split("@")[0]}+{alias_name}@gmail.com'

        text = (
            f'✅ **New Alias Generated!**\n\n'
            f'📧 **Alias:** `{alias_name}`\n'
            f'📨 **Email:** `{full_email}`\n\n'
            f'💡 Use this email to receive OTPs and messages.'
        )

        keyboard = [
            [InlineKeyboardButton('📋 Copy Email', callback_data=f'copy_email_{alias_name}')],
            [InlineKeyboardButton('👀 View Messages', callback_data=f'view_{alias_name}')],
            [InlineKeyboardButton('➕ Another Alias', callback_data='new_alias')]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif data == 'my_aliases':
        aliases = db.get_aliases(user_id)

        if not aliases:
            await query.edit_message_text(
                '📭 No aliases yet. Use /newalias or click below.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('➕ New Alias', callback_data='new_alias')]])
            )
            return

        text = '📧 **Your Aliases:**\n\n'
        keyboard = []

        for alias_name, active, created_at in aliases:
            status = '🟢' if active else '🔴'
            text += f'{status} `{alias_name}`\n'
            keyboard.append([InlineKeyboardButton(f'👀 {alias_name}', callback_data=f'view_{alias_name}')])

        keyboard.append([InlineKeyboardButton('➕ New Alias', callback_data='new_alias')])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif data == 'view_otp':
        otps = db.get_otps_for_user(user_id)

        if not otps:
            await query.edit_message_text('🔑 No OTPs found yet.')
            return

        text = '🔑 **Recent OTPs:**\n\n'

        for otp_code, subject, alias_name, received_at in otps[:10]:
            text += f'📧 `{alias_name}`\n'
            text += f'🔑 **Code:** `{otp_code}`\n'
            text += f'📨 {subject}\n\n'

        await query.edit_message_text(text, parse_mode='Markdown')

    elif data == 'help':
        help_text = (
            '📖 **Bot Commands**\n\n'
            '/start - Start the bot\n'
            '/newalias - Generate new Gmail alias\n'
            '/myaliases - List your aliases\n'
            '/otp - View recent OTP codes\n'
            '/view <alias> - View messages for alias\n'
            '/delalias <alias> - Delete an alias\n'
            '/feedback - Send feedback\n'
            '/help - Show this help'
        )
        await query.edit_message_text(help_text, parse_mode='Markdown')

    elif data.startswith('view_'):
        alias_name = data[5:]
        alias_data = db.get_alias_by_name(alias_name)

        if not alias_data or alias_data[1] != user_id:
            await query.edit_message_text('❌ Alias not found.')
            return

        messages = db.get_messages_for_alias(alias_name)

        if not messages:
            await query.edit_message_text(
                f'📭 No messages for `{alias_name}` yet.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔄 Refresh', callback_data=f'view_{alias_name}')]]),
                parse_mode='Markdown'
            )
            return

        text = f'📨 **Messages for `{alias_name}`:**\n\n'

        for subject, body, received_at, seen, otp_code, links_json in messages[:5]:
            text += f'📧 **Subject:** {subject}\n'
            if otp_code:
                text += f'🔑 **OTP:** `{otp_code}`\n'
            text += f'🕐 {received_at}\n'
            text += '━' * 20 + '\n\n'

        keyboard = [
            [InlineKeyboardButton('🔄 Refresh', callback_data=f'view_{alias_name}')],
            [InlineKeyboardButton('📋 My Aliases', callback_data='my_aliases')]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif data.startswith('copy_email_'):
        alias_name = data[11:]
        full_email = f'{GMAIL_EMAIL.split("@")[0]}+{alias_name}@gmail.com'
        await query.edit_message_text(
            f'📨 **Email:** `{full_email}`',
            parse_mode='Markdown'
        )

    elif data.startswith('copy_alias_'):
        alias_name = data[11:]
        await query.edit_message_text(
            f'📧 **Alias:** `{alias_name}`',
            parse_mode='Markdown'
        )

    elif data.startswith('quick_copy_otp_'):
        otp_code = data[15:]
        await query.edit_message_text(
            f'🔑 **OTP Code:** `{otp_code}`',
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if context.user_data.get('awaiting_feedback'):
        feedback_text = update.message.text or 'Photo feedback'
        photo_id = None

        if update.message.photo:
            photo_id = update.message.photo[-1].file_id
            feedback_text = update.message.caption or 'Photo feedback'

        db.add_feedback(user_id, feedback_text, photo_id)

        try:
            if FEEDBACK_CHANNEL_ID:
                user = update.effective_user
                feedback_msg = f'📝 **New Feedback**\n\n'
                feedback_msg += f'👤 User: [{user.first_name}](tg://user?id={user_id})\n'
                feedback_msg += f'🆔 ID: `{user_id}`\n'
                feedback_msg += f'💬 {feedback_text}'

                if photo_id:
                    await context.bot.send_photo(
                        chat_id=FEEDBACK_CHANNEL_ID,
                        photo=photo_id,
                        caption=feedback_msg,
                        parse_mode='Markdown'
                    )
                else:
                    await context.bot.send_message(
                        chat_id=FEEDBACK_CHANNEL_ID,
                        text=feedback_msg,
                        parse_mode='Markdown'
                    )
        except Exception as e:
            logger.error(f'Failed to send feedback to channel: {e}')

        await update.message.reply_text('✅ Feedback sent! Thank you.')
        context.user_data['awaiting_feedback'] = False

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text('❌ Admin only.')
        return

    total_users, total_aliases, total_messages = db.get_stats()

    text = (
        '📊 **Bot Statistics**\n\n'
        f'👤 Total Users: {total_users}\n'
        f'📧 Total Aliases: {total_aliases}\n'
        f'📨 Total Messages: {total_messages}'
    )

    await update.message.reply_text(text, parse_mode='Markdown')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text('❌ Admin only.')
        return

    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text('📢 Usage: /broadcast <message> or reply to a message.')
        return

    if update.message.reply_to_message:
        message_text = update.message.reply_to_message.text
    else:
        message_text = ' '.join(context.args)

    users = db.get_all_users()
    sent = 0
    failed = 0

    for user_data in users:
        try:
            await context.bot.send_message(chat_id=user_data[0], text=message_text)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f'📢 Broadcast sent: {sent} successful, {failed} failed.')

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text('❌ Admin only.')
        return

    if not context.args:
        await update.message.reply_text('🚫 Usage: /ban <user_id>')
        return

    try:
        target_id = int(context.args[0])
        db.ban_user(target_id)
        await update.message.reply_text(f'🚫 User `{target_id}` banned.', parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text('❌ Invalid user ID.')

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text('❌ Admin only.')
        return

    if not context.args:
        await update.message.reply_text('✅ Usage: /unban <user_id>')
        return

    try:
        target_id = int(context.args[0])
        db.unban_user(target_id)
        await update.message.reply_text(f'✅ User `{target_id}` unbanned.', parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text('❌ Invalid user ID.')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f'Update {update} caused error {context.error}')

async def main():
    """Main function to start the bot"""
    gmail_thread = threading.Thread(target=gmail_checker_thread, daemon=True)
    gmail_thread.start()
    logger.info('Gmail checker thread started')

    application = Application.builder().token(BOT_TOKEN).build()
    notification_queue.set_bot(application)

    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('newalias', newalias_command))
    application.add_handler(CommandHandler('myaliases', myaliases_command))
    application.add_handler(CommandHandler('otp', otp_command))
    application.add_handler(CommandHandler('view', view_command))
    application.add_handler(CommandHandler('delalias', delalias_command))
    application.add_handler(CommandHandler('feedback', feedback_command))
    application.add_handler(CommandHandler('help', help_command))

    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('broadcast', broadcast_command))
    application.add_handler(CommandHandler('ban', ban_command))
    application.add_handler(CommandHandler('unban', unban_command))

    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    application.add_error_handler(error_handler)

    logger.info('Starting bot...')

    async def notification_loop():
        while True:
            try:
                await notification_queue.process_notifications()
            except Exception as e:
                logger.error(f'Notification loop error: {e}')
            await asyncio.sleep(5)

    await asyncio.gather(
        application.run_polling(allowed_updates=Update.ALL_TYPES),
        notification_loop()
    )

if __name__ == '__main__':
    asyncio.run(main())