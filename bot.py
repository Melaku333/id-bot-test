import asyncio
import requests
from aiogram import Bot, Dispatcher, Router   
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from playwright.sync_api import sync_playwright
import tempfile
from playwright.async_api import async_playwright
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery
import shutil  # make sure this import is near the top
import os
from app import bot


# Router instance
router = Router()

# Point this to your actual data_store

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:1000")
DATA_STORE_PATH = os.getenv("DATA_STORE_PATH", "/app/data_store")

# Upload command
@router.message(Command("upload"))
async def ask_file(message: Message):
    await message.answer("📂 Please send me a PDF file to upload.")

# Print command
@router.message(Command("print"))
async def print_handler(message: Message):
    await message.answer("⏳ Preparing your printable PDF...")
    try:
        response = requests.get(f"{BASE_URL}/api/print_pdf")

        print("DEBUG STATUS:", response.status_code)  # log

        if response.status_code == 200:
            pdf_path = "temp_ids.pdf"
            with open(pdf_path, "wb") as f:
                f.write(response.content)

            await message.answer_document(FSInputFile(pdf_path))
        else:
            await message.answer(f"❌ Error from server: {response.text}")
    except Exception as e:
        await message.answer(f"⚠️ Failed to fetch print PDF: {e}")





async def generate_pdf_via_browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://127.0.0.1:7000/print", wait_until="networkidle")

        await page.click("button:has-text('Save as PDF')")
        await page.wait_for_timeout(3000)

        timestamp = (datetime.datetime.now() - datetime.timedelta(hours=6)).strftime("%H_%M")
        pdf_path = f"ID_cards_{timestamp}.pdf"

        await page.pdf(
            path=pdf_path,
            width="219.91mm",
            height="301.66mm",
            margin={
                "top": "5mm",
                "right": "10mm",
                "bottom": "0mm",
                "left": "0mm"
            },
        )

        await browser.close()
        return pdf_path


@router.message(Command("download_color"))
async def download_color_handler(message: Message):
    await message.answer("⏳ Generating color PDF...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Open your color print page
            await page.goto("http://127.0.0.1:7000/print_color", wait_until="networkidle")

           # Optional: click Save as PDF button if your frontend needs it
            await page.click("button:has-text('Save as PDF')")

            # Wait for any JS rendering
            await page.wait_for_timeout(3000)

            # Save PDF with custom page size + margins
            pdf_path = "color_ids.pdf"
            await page.pdf(
                path=pdf_path,
                width="219.91mm",
                height="301.66mm",
                margin={
                    "top": "5mm",
                    "right": "10mm",
                    "bottom": "0mm",
                    "left": "0mm"
                },
               # print_background=True   # ✅ keep colors
            )

            await browser.close()

        # Send back to Telegram
        await message.answer_document(FSInputFile(pdf_path))

    except Exception as e:
        await message.answer(f"⚠️ Failed to generate color PDF: {e}")



# Delete specific ID locally by sending: /delete <person_id>
@router.message(Command("delete"))
async def delete_person_handler(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "⚠️ Please provide a person ID. Example:\n`/delete 12345`",
            parse_mode="Markdown"
        )
        return

    person_id = args[1].strip()
    person_dir = os.path.join(DATA_STORE_PATH, person_id)

    if not os.path.exists(person_dir):
        await message.answer(f"⚠️ Local folder for `{person_id}` not found, nothing to delete.", parse_mode="Markdown")
        return

    try:
        shutil.rmtree(person_dir)
        await message.answer(f"✅ Local folder for `{person_id}` deleted successfully.", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Failed to delete local folder for `{person_id}`: {e}", parse_mode="Markdown")


# Delete specific ID locally by sending: /delete <person_id>
@router.message(Command("delete"))
async def delete_person_handler(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "⚠️ Please provide a person ID. Example:\n`/delete 12345`",
            parse_mode="Markdown"
        )
        return

    person_id = args[1].strip()
    person_dir = os.path.join(DATA_STORE_PATH, person_id)

    if not os.path.exists(person_dir):
        await message.answer(f"⚠️ Local folder for `{person_id}` not found, nothing to delete.", parse_mode="Markdown")
        return

    try:
        shutil.rmtree(person_dir)
        await message.answer(f"✅ Local folder for `{person_id}` deleted successfully.", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Failed to delete local folder for `{person_id}`: {e}", parse_mode="Markdown")


@router.message(Command("list"))
async def list_records_handler(message: Message):
    await message.answer("📋 Fetching current records...")

    try:
        response = requests.get(f"{BASE_URL}/api/list")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("records"):
                records = data["records"]

                for r in records:
                    person_id = r["person_id"]   # e.g., "person_002"

                    text = f"👤 {r['english_name']}\nFAN: {r.get('fan', 'N/A')}\nID: `{person_id}`"
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="✏️ Edit Photo", callback_data=f"edit_photo:{person_id}")]
                        ]
                    )
                    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await message.answer("⚠️ No records found.")
        else:
            await message.answer(f"❌ Server error: {response.text}")
    except Exception as e:
        await message.answer(f"⚠️ Failed to fetch records: {e}")



@router.callback_query(lambda c: c.data.startswith("edit_photo:"))
async def callback_edit_photo(query: CallbackQuery):
    person_id = query.data.split(":")[1]  # e.g., "person_002"
    photo_path = os.path.join(DATA_STORE_PATH, person_id, "photo_original.png")

    if not os.path.exists(photo_path):
        await query.message.answer(
            f"⚠️ No photo.png found for {person_id}.\nExpected at:\n`{photo_path}`",
            
        )
        await query.answer()
        return

    try:
        await query.message.answer_document(FSInputFile(photo_path))
        await query.message.answer(
            f"📤 Sent photo for {person_id}. Edit it and send it back with:\n"
            f"`/replace {person_id}` (attach your edited image)",
            
        )
    except Exception as e:
        await query.message.answer(f"⚠️ Failed to send photo for {person_id}: {e}")

    await query.answer()


# --- add these imports near the top ---
import logging, io, datetime
from typing import Optional
from PIL import Image 

try:
    from PIL import Image  # Pillow for PNG conversion if needed
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

logging.basicConfig(level=logging.INFO)  # or DEBUG if you want more noise


def _fmt_dt(ts: float) -> str:
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)

# Keep track of which user is replacing which person
pending_replace = {}  # user_id -> person_id

# Step 1: command sets pending replace


# Step 2: handle next photo/document from user
@router.message(lambda m: m.photo)
async def replace_photo_file(message: Message):
    user_id = message.from_user.id
    if user_id not in pending_replace:
        return  # not expecting a replace from this user

    person_id = pending_replace.pop(user_id)  # remove pending state
    target_dir = os.path.join(DATA_STORE_PATH, person_id)
    target_path = os.path.join(target_dir, "photo.png")

    # Pick file_id
    if message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_id = message.document.file_id

    try:
        # Download from Telegram
        tg_file = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{tg_file.file_path}"
        r = requests.get(file_url, timeout=60)
        if r.status_code != 200:
            await message.answer(f"❌ Failed to download file (HTTP {r.status_code})")
            return

        # Save file
        os.makedirs(target_dir, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(r.content)

        await message.answer_document(
            FSInputFile(target_path),
            caption=f"✅ Replaced photo for `{person_id}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Replace failed: {e}")


# Delete all processed files
@router.message(Command("delete_all"))
async def delete_all_handler(message: Message):
    await message.answer("🗑️ Deleting all records...")
    try:
        response = requests.post(f"{BASE_URL}/delete_all")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                await message.answer("✅ All records deleted successfully.")
            else:
                await message.answer(f"⚠️ Failed: {data.get('error', 'Unknown error')}")
        else:
            await message.answer(f"❌ Server error: {response.text}")
    except Exception as e:
        await message.answer(f"⚠️ Failed to delete all: {e}")

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@router.message(Command("list_photo"))
async def list_photo_handler(message: Message):
    """
    Sends all photos from data_store/<person_id>/photo.png
    with an inline 'Edit Photo' button.
    """
    try:
        if not os.path.exists(DATA_STORE_PATH):
            await message.answer("⚠️ DATA_STORE_PATH does not exist.")
            return

        sent_any = False
        for person_id in os.listdir(DATA_STORE_PATH):
            person_dir = os.path.join(DATA_STORE_PATH, person_id)
            photo_path = os.path.join(person_dir, "photo.png")

            if os.path.isfile(photo_path):
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="✏️ Edit Photo", callback_data=f"edit_photo:{person_id}")]
                    ]
                )
                try:
                    await message.answer_document(
                        FSInputFile(photo_path),
                        caption=f"👤 `{person_id}`",
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    sent_any = True
                except Exception as e:
                    await message.answer(f"⚠️ Failed to send photo for `{person_id}`: {e}")

        if not sent_any:
            await message.answer("⚠️ No photos found in data_store.")

    except Exception as e:
        await message.answer(f"❌ Error while listing photos: {e}")


@router.callback_query(lambda c: c.data.startswith("edit_photo:"))
async def callback_edit_photo(query: CallbackQuery):
    person_id = query.data.split(":")[1]
    original_path = os.path.join(DATA_STORE_PATH, person_id, "photo_original.png")

    if not os.path.exists(original_path):
        await query.message.answer(
            f"⚠️ No `photo_original.png` found for `{person_id}`.\n"
            f"Expected at:\n`{original_path}`",
            parse_mode="Markdown"
        )
        await query.answer()
        return

    try:
        await query.message.answer_document(FSInputFile(original_path))
        await query.message.answer(
            f"📤 Sent *original photo* for `{person_id}`.\n\n"
            f"➡️ Edit it manually and send back with:\n"
            f"`/replace {person_id}` (attach the new image).",
            parse_mode="Markdown"
        )
    except Exception as e:
        await query.message.answer(f"⚠️ Failed to send original photo for `{person_id}`: {e}")

    await query.answer()



# Delete specific ID by sending: /delete <person_id>
@router.message(Command("delete"))
async def delete_person_handler(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Please provide a person ID. Example:\n`/delete 12345`", parse_mode="Markdown")
        return

    person_id = args[1]
    await message.answer(f"🗑️ Deleting record for ID: {person_id} ...")

    try:
        response = requests.post(f"{BASE_URL}/delete/{person_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                await message.answer(f"✅ Record for ID `{person_id}` deleted.", parse_mode="Markdown")
            else:
                await message.answer(f"⚠️ Failed: {data.get('error', 'Unknown error')}")
        else:
            await message.answer(f"❌ Server error: {response.text}")
    except Exception as e:
        await message.answer(f"⚠️ Failed to delete ID {person_id}: {e}")


@router.message(Command("download"))
async def download_handler(message: Message):
    await message.answer("⏳ Generating PDF...")
    try:
        pdf_path = await generate_pdf_via_browser()
        await message.answer_document(FSInputFile(pdf_path))
    except Exception as e:
        await message.answer(f"⚠️ Failed to generate PDF: {e}")



@router.message(Command("gray_all"))
async def gray_all_handler(message: Message):
    await message.answer("⏳ Applying grayscale to all IDs...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:7000/print", wait_until="networkidle")

        # Click the "gray all" button (adjust selector!)
        await page.click("#grayAllButton")

        # Now trigger the save-as-pdf button
        await page.click("#savePdfButton")

        # Wait for the PDF download (catch via browser context)
        # -- OR use page.pdf() if HTML supports it
        pdf_bytes = await page.pdf(format="A4")

        await browser.close()

    # Save and send to Telegram
    pdf_path = "gray_ids.pdf"
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    await message.answer_document(FSInputFile(pdf_path))



@router.message(Command("replace"))
async def replace_command(message: Message):
    args = message.text.split() if message.text else []
    if len(args) < 2:
        await message.answer("⚠️ Usage: `/replace <person_id>`", parse_mode="Markdown")
        return

    person_id = args[1].strip()
    pending_replace[message.from_user.id] = person_id
    await message.answer(
        f"📤 Ready to replace photo for `{person_id}`.\n"
        f"Please send the new image now.",
        parse_mode="Markdown"
    )
@router.message(lambda m: m.document or m.photo)
async def handle_file_or_photo(message: Message):
    user_id = message.from_user.id

    if user_id in pending_replace:
        person_id = pending_replace.pop(user_id)
        target_dir = os.path.join(DATA_STORE_PATH, person_id)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, "photo.png")

        file_id = message.photo[-1].file_id if message.photo else message.document.file_id

        tg_file = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{tg_file.file_path}"
        r = requests.get(file_url)
        with open(target_path, "wb") as f:
            f.write(r.content)

        await message.answer_document(
            FSInputFile(target_path),
            caption=f"✅ Replaced photo for `{person_id}`",
            parse_mode="Markdown"
        )
    else:
        # Normal upload → send to API
        file_id = message.document.file_id if message.document else message.photo[-1].file_id
        file_name = message.document.file_name if message.document else "photo.png"

        tg_file = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{tg_file.file_path}"
        r = requests.get(file_url)

        files = {"file": (file_name, r.content)}
        api_response = requests.post(f"{BASE_URL}/api/upload", files=files)
        await message.answer("✅ File uploaded and processed successfully.")


