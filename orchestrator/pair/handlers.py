"""Telegram command handlers for pair programming mode."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from orchestrator.bot.formatters import chunk_message
from orchestrator.pair.manager import PairManager

logger = logging.getLogger(__name__)
pair_router = Router()

_pair_mgr: PairManager | None = None
_bot_ref: Bot | None = None


def register_pair(dp, pair_mgr: PairManager, bot: Bot) -> None:
    global _pair_mgr, _bot_ref
    _pair_mgr = pair_mgr
    _bot_ref = bot
    dp.include_router(pair_router)


def _chat_id(msg: Message) -> int:
    return msg.chat.id


def _user_id(msg: Message) -> int:
    return msg.from_user.id if msg.from_user else 0


def _username(msg: Message) -> str:
    if msg.from_user:
        return msg.from_user.username or msg.from_user.first_name or str(msg.from_user.id)
    return "unknown"


@pair_router.message(Command("pair"))
async def cmd_pair(msg: Message) -> None:
    assert _pair_mgr

    text = (msg.text or "").strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await msg.reply(
            "Usage: /pair <task-name>\n\n"
            "Starts a shared pair programming session.\n"
            "Both users talk to the same Claude, same branch.\n\n"
            "Pair commands:\n"
            "/pair <task> — start session\n"
            "/join — join the active session\n"
            "/leave — leave the session\n"
            "/driver @user — only that user talks to Claude\n"
            "/both — everyone can talk to Claude\n"
            "/handoff — swap driver to the other person\n"
            "/checkpoint [msg] — commit current state\n"
            "/endpair — push, create PR, cleanup"
        )
        return

    task_name = parts[1].strip().lower().replace(" ", "-")

    try:
        session = await _pair_mgr.start_pair(
            _chat_id(msg), task_name, _user_id(msg), _username(msg)
        )
    except (ValueError, RuntimeError) as e:
        await msg.reply(str(e))
        return

    await msg.reply(
        f"Pair session started: {session.task_name}\n"
        f"Branch: {session.branch}\n"
        f"Members: {session.member_list_str()}\n"
        f"Mode: both (everyone can send)\n\n"
        "Others: use /join to hop in."
    )


@pair_router.message(Command("join"))
async def cmd_join(msg: Message) -> None:
    assert _pair_mgr

    try:
        member = await _pair_mgr.join_pair(
            _chat_id(msg), _user_id(msg), _username(msg)
        )
    except ValueError as e:
        await msg.reply(str(e))
        return

    session = _pair_mgr.get_session(_chat_id(msg))
    await msg.reply(
        f"@{member.username} joined!\n"
        f"Members: {session.member_list_str() if session else '?'}"
    )


@pair_router.message(Command("leave"))
async def cmd_leave(msg: Message) -> None:
    assert _pair_mgr

    try:
        result = await _pair_mgr.leave_pair(_chat_id(msg), _user_id(msg))
    except ValueError as e:
        await msg.reply(str(e))
        return

    await msg.reply(result)


@pair_router.message(Command("driver"))
async def cmd_driver(msg: Message) -> None:
    assert _pair_mgr

    text = (msg.text or "").strip()
    parts = text.split()

    # If a user is mentioned, use their ID
    # Otherwise, the sender becomes driver
    target_id = _user_id(msg)
    target_name = _username(msg)

    if msg.entities:
        for entity in msg.entities:
            if entity.type == "mention" and entity.user:
                target_id = entity.user.id
                target_name = entity.user.username or entity.user.first_name or str(entity.user.id)
                break
            if entity.type == "text_mention" and entity.user:
                target_id = entity.user.id
                target_name = entity.user.username or entity.user.first_name or str(entity.user.id)
                break

    try:
        session = await _pair_mgr.set_driver(_chat_id(msg), target_id)
    except ValueError as e:
        await msg.reply(str(e))
        return

    await msg.reply(
        f"Driver mode ON. Only @{target_name} can talk to Claude.\n"
        "Others can observe. Use /both to let everyone talk again."
    )


@pair_router.message(Command("both"))
async def cmd_both(msg: Message) -> None:
    assert _pair_mgr

    try:
        session = await _pair_mgr.set_both_mode(_chat_id(msg))
    except ValueError as e:
        await msg.reply(str(e))
        return

    await msg.reply("Both mode ON. Everyone can talk to Claude.")


@pair_router.message(Command("handoff"))
async def cmd_handoff(msg: Message) -> None:
    assert _pair_mgr

    try:
        session = await _pair_mgr.handoff(_chat_id(msg), _user_id(msg))
    except ValueError as e:
        await msg.reply(str(e))
        return

    driver = session.members.get(session.driver_id)
    name = f"@{driver.username}" if driver else "?"
    await msg.reply(f"Driver handed off to {name}.")


@pair_router.message(Command("checkpoint"))
async def cmd_checkpoint(msg: Message) -> None:
    assert _pair_mgr

    text = (msg.text or "").strip()
    parts = text.split(maxsplit=1)
    commit_msg = parts[1] if len(parts) > 1 else ""

    await msg.reply("Committing...")

    try:
        result = await _pair_mgr.checkpoint(_chat_id(msg), commit_msg)
    except ValueError as e:
        await msg.reply(str(e))
        return

    for chunk in chunk_message(result):
        await msg.reply(chunk)


@pair_router.message(Command("endpair"))
async def cmd_endpair(msg: Message) -> None:
    assert _pair_mgr

    session = _pair_mgr.get_session(_chat_id(msg))
    if not session:
        await msg.reply("No pair session active.")
        return

    await msg.reply(f"Ending pair session: {session.task_name}...")

    try:
        result = await _pair_mgr.end_pair(_chat_id(msg))
    except ValueError as e:
        await msg.reply(str(e))
        return

    await msg.reply(result)


# Route non-command messages to the pair session (if active)
@pair_router.message(F.text & ~F.text.startswith("/"))
async def route_pair_message(msg: Message) -> None:
    assert _pair_mgr

    chat_id = _chat_id(msg)
    session = _pair_mgr.get_session(chat_id)
    if not session:
        return  # No pair session — let the split mode handler try

    text = (msg.text or "").strip()
    if not text:
        return

    uid = _user_id(msg)
    if uid not in session.members:
        return  # Not a member, ignore

    try:
        response = await _pair_mgr.send_message(
            chat_id, uid, _username(msg), text
        )
    except ValueError as e:
        await msg.reply(str(e))
        return

    if not response:
        await msg.reply("[No response from Claude]")
        return

    for chunk in chunk_message(f"[{session.task_name}]\n{response}"):
        await msg.reply(chunk)
