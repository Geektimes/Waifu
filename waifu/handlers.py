from telethon import events

def register_handlers(client):

    @client.on(events.NewMessage(pattern="/ping"))
    async def ping(event):
        await event.reply("pong")
