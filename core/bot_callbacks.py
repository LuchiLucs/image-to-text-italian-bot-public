import logging
from telegram import Update, Message
from telegram.constants import MessageEntityType
from telegram.ext import ContextTypes

from core.llm_client import llm_process_image_from_url

logger = logging.getLogger("bot")


def remove_command_text(command_text: str) -> str | None:
    if command_text.startswith("/"):
        # find first space after command
        end_command = command_text.find(" ")
        if end_command == -1:  # if there is no space (only the command), return None
            return None
        return command_text[end_command + 1 :]
    return command_text


def get_bot_command(message: Message) -> str | None:
    for entity in message.entities:
        if entity.type == MessageEntityType.BOT_COMMAND:
            return message.parse_entity(entity)
    return None


async def process_image_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Process image and reply with description"""
    bot = context.bot
    message = update.message
    if message is None:
        logger.error(
            "No message found in update, don't know how to proceed or reply to user (chat_id unknown)"
        )
        return
    # Initialize processing_msg as None to avoid unbound variable error
    processing_msg: Message | None = None
    try:
        command_text = get_bot_command(message)

        if command_text is None:
            # prioritize photo in the message (assuming normal message with photo)
            photo = message.photo[-1]
            image_caption = message.caption
            image_reply_to_text = None
        else:
            # then in the replied-to message (assuming it's a command that replies to a photo)
            if (
                message.reply_to_message is None
                or message.reply_to_message.photo is None
            ):
                await bot.send_message(
                    chat_id=message.chat_id,
                    text="Per favore, i) rispondi a un messaggio che ii) contiene una foto quando usi il comando! Riprova!",  # codespell:ignore
                    reply_to_message_id=message.message_id,
                )
                return
            photo = message.reply_to_message.photo[-1]
            image_caption = message.reply_to_message.caption
            image_reply_to_text = (
                remove_command_text(message.text) if message.text else None
            )

        file = await bot.get_file(photo.file_id)
        image_url = file.file_path
        if image_url is None:
            await bot.send_message(
                chat_id=message.chat_id,
                text="Non riesco a recuperare l'URL dell'immagine dal server Telegram. Assicurati che l'immagine sia valida, e riprova.",
                reply_to_message_id=message.message_id,
            )
            return

        # Send processing message
        processing_msg = await bot.send_message(
            chat_id=message.chat_id,
            text="Sto descrivendo la tua immagine...",
            reply_to_message_id=message.message_id,
        )

        description = llm_process_image_from_url(
            image_url, image_caption, image_reply_to_text, command_text
        )

        # Reply with description
        await bot.send_message(
            chat_id=message.chat_id,
            text=description,
            reply_to_message_id=message.message_id,
        )

        # Delete processing message
        await bot.delete_message(
            chat_id=message.chat_id, message_id=processing_msg.message_id
        )

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await bot.send_message(
            chat_id=message.chat_id,
            text="Mi dispiace, ma il processo di descrizione dell'immagine è fallito per un errore interno del bot.",
            reply_to_message_id=message.message_id,
        )
        # Try to delete processing message if it exists
        # i.e. when the error happens after sending it
        if processing_msg is not None:
            await bot.delete_message(
                chat_id=message.chat_id, message_id=processing_msg.message_id
            )
