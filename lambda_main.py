import json
import logging
from telegram import Update, BotCommand
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram._utils.types import JSONDict

from config.loader import TELEGRAM_TOKEN, ALLOWED_GROUP_IDS, BOT_PRIVACY_MODE_ON
from core.bot_callbacks import process_image_message
from core.bot_enums import BotCommandsEnum

logger = logging.getLogger("bot")


async def post_init_set_bot_commands(application: Application) -> None:
    """Set bot commands after application initialization"""
    await application.bot.set_my_commands(
        [
            BotCommand(
                BotCommandsEnum.DESCRIVI, "Descrivi questa immagine in modo generico"
            ),
            BotCommand(
                BotCommandsEnum.DESCRIVI_EVENTO,
                "Descrivi questa immagine in modo strutturato come evento",
            ),
        ]
    )


def get_application(local_testing: bool = False):
    """Setup the application for webhook usage (singleton pattern for Lambda efficiency)"""
    # REF: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Builder-Pattern
    builder = Application.builder()
    builder.token(TELEGRAM_TOKEN)
    if not local_testing:
        builder.updater(None)
    builder.post_init(post_init_set_bot_commands)
    application = builder.build()

    # Add message handler for photos
    private_photo = filters.PHOTO & filters.ChatType.PRIVATE

    # For groups with privacy mode ON: only respond to photos when bot is mentioned
    group_photo_mentioned = (
        filters.PHOTO
        & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP)
        & filters.Chat(ALLOWED_GROUP_IDS)
    )

    # For groups with privacy mode OFF: respond to all photos (your current behavior)
    group_photo_all = (
        filters.PHOTO
        & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP)
        & filters.Chat(ALLOWED_GROUP_IDS)
    )

    # Choose one of these based on your privacy mode preference:
    if BOT_PRIVACY_MODE_ON:
        # Option A: Privacy mode ON (requires mention)
        message_filter = private_photo | group_photo_mentioned
    else:
        # Option B: Privacy mode OFF (current behavior)
        message_filter = private_photo | group_photo_all

    # Add message handler for photos
    application.add_handler(MessageHandler(message_filter, process_image_message))
    application.add_handler(
        CommandHandler(
            command=BotCommandsEnum.DESCRIVI.lstrip("/"),
            # filters=(filters.ChatType.GROUP | filters.ChatType.SUPERGROUP) & filters.Chat(ALLOWED_GROUP_IDS),
            callback=process_image_message,
        )
    )
    application.add_handler(
        CommandHandler(
            command=BotCommandsEnum.DESCRIVI_EVENTO.lstrip("/"),
            # filters=(filters.ChatType.GROUP | filters.ChatType.SUPERGROUP) & filters.Chat(ALLOWED_GROUP_IDS),
            callback=process_image_message,
        )
    )
    return application


def lambda_handler(event, context):
    """AWS Lambda handler function."""
    try:
        logger.info(f"Lambda handler called with event keys: {list(event.keys())}")
        # Extract the update data from the event
        if event.get("body"):
            update_data = json.loads(event["body"])
            logger.info(update_data)
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No update data provided"}),
            }

        # Process the update asynchronously
        import asyncio

        asyncio.run(process_webhook_update(update_data))

        return {"statusCode": 200, "body": json.dumps({"status": "OK"})}
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


async def process_webhook_update(update_data: JSONDict) -> None:
    """Process a single update from Telegram."""
    application = get_application()

    async with application:
        await application.start()

        # Create an Update object
        update = Update.de_json(update_data, application.bot)

        # Process the update
        await application.process_update(update)

        await application.stop()


# For local testing only
if __name__ == "__main__":
    logger.info("Starting bot in local testing mode with polling...")
    application = get_application(local_testing=True)
    application.run_polling(allowed_updates=Update.ALL_TYPES)
