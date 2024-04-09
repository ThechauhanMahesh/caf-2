import re 
import logging 
import constants
from pyrogram.types import Message
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.WARN)

app = Client(
    "userbot", 
    api_id=constants.API_ID,
    api_hash=constants.API_HASH,
    session_string=constants.SESSSION_STRING
)
db = AsyncIOMotorClient(constants.DATABASE_URL)["forwarder"]


@app.on_message(filters=filters.chat(constants.SOURCE_CHANNEL))
async def forward_message(_, message: Message):
    
    for fillers in ["VOL", "MC", "LIQ"]:

        match = re.search(rf"{fillers}: \$(\S+)", str(message.text))
        if not match: 
            return # either VOL, MC or LIQ not found

        amount = match.group(1).lower() # so that we can remove m or k without 
        value = float(amount.replace("k", "").replace("m", "")) # remove k and m
        if "k" in amount: value *= 1000
        elif "m" in amount: value *= 1000000

        doc = await db.limits.find_one({"type": fillers.lower(), "limit": {"$lte": value}})
        if not doc: 
            return # limit exceedes for VOL, MC or LIQ        

    await message.copy(constants.TARGET_CHANNEL) # to copy message
    # await message.forward(constants.TARGET_CHANNEL) # to forward message


@app.on_message(filters=filters.command("set"))
async def set_limit(_, message: Message):
    try:
        _, limit_type, number = message.text.split(" ")
        parsed_number = float(number.replace("k", "")) * 1000
        if limit_type not in ["vol", "mc", "liq"]:
            raise ValueError
    except ValueError:
        await message.reply_text("Invalid command!\n\nExample: /set (vol|mc|liq) 5k")
        return
    await db.limits.update_one({"type": limit_type}, {"$set": {"limit": parsed_number}}, upsert=True)
    await message.reply_text(f"Limit for {limit_type.upper()} set to {number}k")


if __name__ == "__main__":
    app.run()