import os
import sys
import asyncio
import qrcode
from datetime import datetime

from telethon import TelegramClient, functions
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import User, ChannelParticipantAdmin, ChannelParticipantCreator
from telethon.tl.functions.channels import LeaveChannelRequest, GetParticipantRequest

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from config import *  # API_ID, API_HASH

# ---------- Globals ----------
SESSIONS_DIR = "sessions"
console = Console()

# Windows asyncio fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# ---------- Logging ----------
def log(msg, file="leave_channels.log"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    console.print(line)
    with open(file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------- FS helpers ----------
def ensure_sessions_folder():
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)
        log(f"📂 Created sessions folder: {SESSIONS_DIR}")


# ---------- UI helpers ----------
def banner():
    console.print(Panel.fit("[bold cyan]Telegram Cleanup Tool[/bold cyan]", border_style="cyan"))


def show_table(rows, headers, title):
    """
    rows: list of lists (strings)
    headers: list of header strings
    """
    if not rows:
        console.print(Panel.fit("No items found.", title=title, border_style="yellow"))
        return False
    table = Table(title=title, show_lines=True, header_style="bold magenta")
    for h in headers:
        table.add_column(h)
    for r in rows:
        table.add_row(*[str(x) for x in r])
    console.print(table)
    return True


# ---------- Login ----------
async def login_with_qr(index=0):
    ensure_sessions_folder()
    session_file = f"{SESSIONS_DIR}/user{index}.session"
    client = TelegramClient(session_file, API_ID, API_HASH)
    await client.connect()
    if await client.is_user_authorized():
        log(f"✅ [user{index}] Already logged in.")
        return client

    img_path = f"qr_user{index}.png"
    try:
        qr = await client.qr_login()
        qrcode.make(qr.url).save(img_path)
        console.print(Panel.fit(f"[green]Scan the QR code image:[/green] [bold]{img_path}[/bold]\n"
                                f"Open Telegram → Settings → Devices → Link Desktop Device",
                                title="QR Login", border_style="green"))
        await qr.wait()
        log(f"🎉 [user{index}] QR login successful!")
    except Exception as e:
        log(f"❌ [user{index}] QR login failed: {e}")
        return None
    finally:
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception:
                pass
    return client


async def login_with_mobile(index=0):
    ensure_sessions_folder()
    session_file = f"{SESSIONS_DIR}/user{index}.session"
    client = TelegramClient(session_file, API_ID, API_HASH)
    await client.connect()
    if await client.is_user_authorized():
        log(f"✅ [user{index}] Already logged in.")
        return client

    try:
        phone = input(f"[user{index}] Enter your mobile number (+123...): ").strip()
        await client.send_code_request(phone)
        code = input("Enter the code you received: ").strip()
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("Two-step verification password: ").strip()
            await client.sign_in(password=password)
        log(f"🎉 [user{index}] Mobile login successful!")
    except Exception as e:
        log(f"❌ [user{index}] Mobile login failed: {e}")
        return None
    return client


async def login_user(index=0):
    ensure_sessions_folder()
    session_file = f"{SESSIONS_DIR}/user{index}.session"

    # If session exists and authorized, use it
    if os.path.exists(session_file):
        client = TelegramClient(session_file, API_ID, API_HASH)
        await client.connect()
        if await client.is_user_authorized():
            log(f"✅ [user{index}] Using existing session.")
            return client
        else:
            log(f"⚠️ [user{index}] Old session invalid. Starting fresh login...")

    console.print(Panel.fit("Choose login method:\n1) QR Login\n2) Mobile Login", title="Login", border_style="magenta"))
    choice = input("Enter 1 or 2: ").strip()
    client = await (login_with_mobile(index) if choice == "2" else login_with_qr(index))

    if client:
        log(f"✅ [user{index}] Session saved successfully.")
        return client
    else:
        log(f"❌ [user{index}] Login failed.")
        return None


# ---------- Fetchers ----------
async def get_bots(client):
    bots = []
    async for dialog in client.iter_dialogs():
        if isinstance(dialog.entity, User) and getattr(dialog.entity, "bot", False):
            bots.append(dialog)
    return bots


async def get_channels_and_groups(client, exclude_admin_owner=True):
    me = await client.get_me()
    items = []
    async for dialog in client.iter_dialogs():
        e = dialog.entity
        if getattr(e, "broadcast", False) or getattr(e, "megagroup", False):
            if exclude_admin_owner:
                try:
                    part = await client(GetParticipantRequest(e, me.id))
                    if isinstance(part.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
                        continue
                except Exception:
                    # If participant info fails, show item (safer to show than hide)
                    pass
            items.append(dialog)
    return items


async def get_private_chats(client, exclude_bots=True):
    """
    Returns dialogs where entity is a User and not a bot (unless exclude_bots=False)
    We'll attempt to get last message date for display.
    """
    privs = []
    async for dialog in client.iter_dialogs():
        e = dialog.entity
        if isinstance(e, User):
            if exclude_bots and getattr(e, "bot", False):
                continue
            # gather last message date if available
            last_date = None
            try:
                last_date = getattr(dialog, "message", None)
                # dialog.message may be None; try dialog.date
                if last_date:
                    last_date = getattr(last_date, "date", None)
            except Exception:
                last_date = None
            # fallback to dialog.date
            if not last_date:
                try:
                    last_date = getattr(dialog, "date", None)
                except Exception:
                    last_date = None
            # format
            last_date_str = last_date.strftime("%Y-%m-%d") if last_date else "—"
            privs.append((dialog, last_date_str))
    return privs


# ---------- Actions ----------
async def delete_and_block_bots(client):
    bots = await get_bots(client)
    rows = [[i+1, d.name, f"@{d.entity.username}" if d.entity.username else "—"] for i, d in enumerate(bots)]
    if not show_table(rows, ["#", "Bot Name", "Username"], "Bots"):
        return

    sel = input("Enter bot numbers to delete & block (e.g., 1,3,5) or press Enter to stop: ").strip()
    if not sel:
        log("➡️ Skipped bot deletion.")
        return

    try:
        idxs = sorted({int(x.strip()) for x in sel.split(",") if x.strip().isdigit()})
    except Exception:
        log("❌ Invalid selection.")
        return

    chosen = []
    for i in idxs:
        if 1 <= i <= len(bots):
            d = bots[i-1]
            chosen.append([i, d.name, f"@{d.entity.username}" if d.entity.username else "—"])
    if not chosen:
        log("❌ No valid bots selected.")
        return

    show_table(chosen, ["#", "Bot Name", "Username"], "Confirm Bots to Delete & Block")
    if not Confirm.ask("⚠️ Confirm delete & block the selected bots?", default=False):
        log("❌ Cancelled.")
        return
    if not Confirm.ask("⚠️ Are you absolutely sure?", default=False):
        log("❌ Aborted for safety.")
        return

    for i in idxs:
        try:
            dialog = bots[i-1]
            await client.delete_dialog(dialog.id)
            await client(functions.contacts.BlockRequest(dialog.id))
            log(f"✅ Deleted chat & blocked bot: {dialog.name} ({'@'+dialog.entity.username if dialog.entity.username else '—'})")
        except Exception as e:
            log(f"❌ Failed for bot #{i}: {e}")

    # Auto-refresh
    await show_bots_list(client, title="🔄 Updated Bots")


async def leave_channels_groups(client):
    items = await get_channels_and_groups(client, exclude_admin_owner=True)
    rows = [[i+1, d.name, f"@{getattr(d.entity,'username', None) or '—'}",
             "Group" if getattr(d.entity, 'megagroup', False) else "Channel"]
            for i, d in enumerate(items)]
    if not show_table(rows, ["#", "Name", "Username", "Type"], "Joined Channels & Groups (excluding your admin/owner)"):
        return

    sel = input("Enter numbers to leave (e.g., 1,3,5) or press Enter to stop: ").strip()
    if not sel:
        log("➡️ Skipped leaving channels/groups.")
        return

    try:
        idxs = sorted({int(x.strip()) for x in sel.split(",") if x.strip().isdigit()})
    except Exception:
        log("❌ Invalid selection.")
        return

    chosen = []
    for i in idxs:
        if 1 <= i <= len(items):
            d = items[i-1]
            chosen.append([i, d.name, f"@{getattr(d.entity,'username', None) or '—'}",
                           "Group" if getattr(d.entity, 'megagroup', False) else "Channel"])
    if not chosen:
        log("❌ No valid targets selected.")
        return

    show_table(chosen, ["#", "Name", "Username", "Type"], "Confirm Leave")
    if not Confirm.ask("⚠️ Confirm leaving the selected channels/groups?", default=False):
        log("❌ Cancelled.")
        return
    if not Confirm.ask("⚠️ Are you absolutely sure?", default=False):
        log("❌ Aborted for safety.")
        return

    for i in idxs:
        try:
            dialog = items[i-1]
            await client(LeaveChannelRequest(dialog.entity))
            log(f"✅ Left {dialog.name} ({'@'+getattr(dialog.entity,'username','') if getattr(dialog.entity,'username',None) else '—'})")
        except Exception as e:
            log(f"❌ Failed leaving #{i} {getattr(dialog,'name','Unknown')}: {e}")

    # Auto-refresh
    await show_channels_groups_list(client, title="🔄 Updated Channels/Groups (excluding your admin/owner)")


async def manage_private_chats(client):
    """
    Show private chats (users), allow delete-only or block+delete.
    """
    while True:
        privs = await get_private_chats(client, exclude_bots=True)
        rows = []
        for i, (dialog, last_date) in enumerate(privs):
            username = dialog.entity.username or "—"
            display_name = dialog.name or (dialog.entity.first_name or "Unknown")
            rows.append([i+1, display_name, f"@{username}" if username != "—" else "—", last_date])
        if not show_table(rows, ["#", "Name", "Username", "Last Msg Date"], "Private Chats"):
            return

        sel = input("Enter private chat numbers to act on (e.g., 1,3,5) or press Enter to stop: ").strip()
        if not sel:
            log("➡️ Skipped private chat management.")
            return

        try:
            idxs = sorted({int(x.strip()) for x in sel.split(",") if x.strip().isdigit()})
        except Exception:
            log("❌ Invalid selection.")
            return

        chosen = []
        for i in idxs:
            if 1 <= i <= len(privs):
                d, last = privs[i-1]
                chosen.append([i, d.name or (d.entity.first_name or "Unknown"), f"@{d.entity.username}" if d.entity.username else "—", last])
        if not chosen:
            log("❌ No valid private chats selected.")
            return

        show_table(chosen, ["#", "Name", "Username", "Last Msg Date"], "Confirm Private Chats to Act On")

        console.print("\nWhat do you want to do with selected private chats?")
        console.print("1) Delete chat only")
        console.print("2) Block user & delete chat")
        console.print("3) Cancel")
        act = input("Enter 1/2/3: ").strip()
        if act not in ("1", "2"):
            log("❌ Cancelled private chat operation.")
            continue

        # Confirmation
        if not Confirm.ask("⚠️ Confirm selection?", default=False):
            log("❌ Cancelled.")
            continue
        if not Confirm.ask("⚠️ Are you absolutely sure?", default=False):
            log("❌ Aborted for safety.")
            continue

        for i in idxs:
            try:
                dialog, _ = privs[i-1]
                if act == "2":
                    # block + delete
                    await client.delete_dialog(dialog.id)
                    await client(functions.contacts.BlockRequest(dialog.id))
                    log(f"🛑 Blocked & deleted chat: {dialog.name} ({'@'+dialog.entity.username if dialog.entity.username else '—'})")
                else:
                    # delete only
                    await client.delete_dialog(dialog.id)
                    log(f"✅ Deleted chat: {dialog.name} ({'@'+dialog.entity.username if dialog.entity.username else '—'})")
            except Exception as e:
                log(f"❌ Failed on private chat #{i}: {e}")

        # auto-refresh preview after action and loop continues unless user stops
        await show_bots_list(client, title="🔄 Bots (unchanged preview after private chat ops)")
        await show_channels_groups_list(client, title="🔄 Channels/Groups (unchanged preview after private chat ops)")


# ---------- List previews ----------
async def show_bots_list(client, title="Bots"):
    bots = await get_bots(client)
    rows = [[i+1, d.name, f"@{d.entity.username}" if d.entity.username else "—"] for i, d in enumerate(bots)]
    show_table(rows, ["#", "Bot Name", "Username"], title)


async def show_channels_groups_list(client, title="Channels & Groups"):
    items = await get_channels_and_groups(client, exclude_admin_owner=True)
    rows = [[i+1, d.name, f"@{getattr(d.entity,'username', None) or '—'}",
             "Group" if getattr(d.entity, 'megagroup', False) else "Channel"]
            for i, d in enumerate(items)]
    show_table(rows, ["#", "Name", "Username", "Type"], title)


# ---------- Automatic Cleanup ----------
async def automatic_cleanup(client):
    console.print(Panel.fit("This will:\n• Delete chats & block ALL bots\n• Leave ALL channels & groups (excluding ones you admin/own)\n• Optionally include private chats if you allow it",
                            title="⚠️ Automatic Full Cleanup WARNING", border_style="red"))
    if not Confirm.ask("Proceed with automatic cleanup?", default=False):
        # fallback micro-menu
        console.print(Panel.fit("Choose one:", border_style="yellow"))
        console.print("1) Delete & Block Bots Only")
        console.print("2) Leave Channels & Groups Only")
        console.print("3) Manage Private Chats Only")
        console.print("4) Cancel")
        choice = input("Enter 1/2/3/4: ").strip()
        if choice == "1":
            await delete_and_block_bots(client)
        elif choice == "2":
            await leave_channels_groups(client)
        elif choice == "3":
            await manage_private_chats(client)
        else:
            log("❌ Automatic cleanup cancelled.")
        return

    # Delete/Block ALL bots
    bots = await get_bots(client)
    if bots:
        show_table([[i+1, d.name, f"@{d.entity.username}" if d.entity.username else "—"] for i, d in enumerate(bots)],
                   ["#", "Bot Name", "Username"], "Bots to Remove")
        if Confirm.ask("Proceed to remove ALL bots listed above?", default=True):
            for d in bots:
                try:
                    await client.delete_dialog(d.id)
                    await client(functions.contacts.BlockRequest(d.id))
                    log(f"✅ Deleted chat & blocked bot: {d.name}")
                except Exception as e:
                    log(f"❌ Failed for bot {d.name}: {e}")
    else:
        log("✅ No bots found.")

    # Leave all non-admin channels/groups
    items = await get_channels_and_groups(client, exclude_admin_owner=True)
    if items:
        show_table([[i+1, d.name, f"@{getattr(d.entity,'username', None) or '—'}",
                     "Group" if getattr(d.entity, 'megagroup', False) else "Channel"]
                    for i, d in enumerate(items)],
                   ["#", "Name", "Username", "Type"], "Channels/Groups to Leave")
        if Confirm.ask("Proceed to leave ALL listed channels/groups?", default=True):
            for d in items:
                try:
                    await client(LeaveChannelRequest(d.entity))
                    log(f"✅ Left {d.name}")
                except Exception as e:
                    log(f"❌ Failed leaving {d.name}: {e}")
    else:
        log("✅ No channels/groups to leave (or you're admin/owner).")

    # Private chats: ask user if they want to include private chats
    if Confirm.ask("Include private chats cleanup? (delete all shown private chats) ", default=False):
        privs = await get_private_chats(client, exclude_bots=True)
        if privs:
            show_table([[i+1, d.name or (d.entity.first_name or "Unknown"), f"@{d.entity.username}" if d.entity.username else "—", last] for i, (d, last) in enumerate(privs)],
                       ["#", "Name", "Username", "Last Msg Date"], "Private Chats to Delete")
            if Confirm.ask("Proceed to delete ALL listed private chats?", default=False):
                for d, _ in privs:
                    try:
                        await client.delete_dialog(d.id)
                        log(f"✅ Deleted private chat: {d.name} ({'@'+d.entity.username if d.entity.username else '—'})")
                    except Exception as e:
                        log(f"❌ Failed to delete private chat {d.name}: {e}")
        else:
            log("✅ No private chats found (excluding bots).")

    # Final refresh
    await show_bots_list(client, title="🔄 Final Bots")
    await show_channels_groups_list(client, title="🔄 Final Channels/Groups (excluding your admin/owner)")


# ---------- Main Menu ----------
async def main_menu(client):
    while True:
        banner()
        console.print("[bold]1)[/bold] Delete & Block Bots")
        console.print("[bold]2)[/bold] Show & Leave/Delete Channels & Groups")
        console.print("[bold]3)[/bold] Automatic Full Cleanup (⚠️ WARNING)")
        console.print("[bold]4)[/bold] Manage Private Chats (NEW)")
        console.print("[bold]5)[/bold] Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            await delete_and_block_bots(client)
        elif choice == "2":
            await leave_channels_groups(client)
        elif choice == "3":
            await automatic_cleanup(client)
        elif choice == "4":
            await manage_private_chats(client)
        elif choice == "5":
            log("👋 Exiting...")
            break
        else:
            console.print("[red]Invalid choice. Try again.[/red]")


# ---------- Entrypoint ----------
async def main():
    client = await login_user(0)
    if not client:
        log("❌ Could not log in. Exiting.")
        return
    async with client:
        await main_menu(client)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("🛑 Exited by user.")
