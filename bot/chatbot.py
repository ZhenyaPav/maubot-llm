from .textgenwebui import run
from .character import get_character
from .config import Config

import asyncio
import json
import os
import re
from datetime import datetime

from typing import Type, Deque, Dict
from mautrix.client import Client
from collections import deque, defaultdict
from maubot.handlers import command, event
from maubot import Plugin, MessageEvent
from mautrix.errors import MNotFound, MatrixRequestError
from mautrix.types import TextMessageEventContent, EventType, RoomID, UserID, MessageType, RelationType, EncryptedEvent
from mautrix.util.config import BaseProxyConfig

class LLMPlugin(Plugin):

    name: str # name of the bot

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()
        self.name = await self.client.get_displayname(self.client.mxid) or \
            self.client.parse_user_id(self.client.mxid)[0]
        self.log.debug(f"DEBUG LLM plugin started with bot name: {self.name}")

    async def should_respond(self, event: MessageEvent) -> bool:
        """ Determine if we should respond to an event """

        if (event.sender == self.client.mxid or  # Ignore ourselves
                event.content.body.startswith('!') or # Ignore commands
                event.content['msgtype'] != MessageType.TEXT or  # Don't respond to media or notices
                event.content.relates_to['rel_type'] == RelationType.REPLACE):  # Ignore edits
            return False

        if len(self.config['allowed_users']) > 0 and event.sender not in self.config['allowed_users']:
            await event.respond("sorry, you're not allowed to use this functionality.")
            return False

        # Check if the message contains the bot's ID
        if re.search("(^|\s)(@)?" + self.name + "([ :,.!?]|$)", event.content.body, re.IGNORECASE):
            return True

        # Reply to all DMs
        if len(await self.client.get_joined_members(event.room_id)) == 2:
            return True

        # Reply to threads if the thread's parent should be replied to
        if self.config['reply_in_thread'] and event.content.relates_to.rel_type == RelationType.THREAD:
            parent_event = await self.client.get_event(room_id=event.room_id, event_id=event.content.get_thread_parent())
            return await self.should_respond(parent_event)

        # Reply to messages replying to the bot
        if self.config['respond_to_replies'] and event.content.relates_to.in_reply_to:
            parent_event = await self.client.get_event(room_id=event.room_id, event_id=event.content.get_reply_to())
            if parent_event.sender == self.client.mxid:
                return True

        return False


    @event.on(EventType.ROOM_MESSAGE)
    async def on_message(self, event: MessageEvent) -> None:

        if not await self.should_respond(event):
            return

        try:
            context = await self.get_context(event)
            context = context + self.name + ': '
            await event.mark_read()
            # Call the text-gen-webui API to get a response
            await self.client.set_typing(event.room_id, timeout=99999)
            user = (await self.client.get_displayname(event.sender) or \
                        self.client.parse_user_id(event.sender)[0]) + ": "
            response = run(context, [user])

            # Send the response back to the chat room
            await self.client.set_typing(event.room_id, timeout=0)
            await event.respond(f"{response}", in_thread=self.config['reply_in_thread'])
        except Exception as e:
            self.log.exception(f"Something went wrong: {e}")
            await event.respond(f"Something went wrong: {e}")
            pass


    async def get_context(self, event: MessageEvent):

        timestamp = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        system_context = get_character() # TODO: add character prompt here

        chat_context = ''
        word_count = 0
        async for next_event in self.generate_context_messages(event):

            if not next_event.content['msgtype'].is_text:
                continue

            message = next_event['content']['body'] + '\n'
            user = (await self.client.get_displayname(next_event.sender) or \
                        self.client.parse_user_id(next_event.sender)[0]) + ": "
                
            #if word_count >= self.config['max_words'] or message_count >= self.config['max_context_messages']:
            #    break

            chat_context = user + message + chat_context

        return system_context + '\n***\n' + chat_context

    async def generate_context_messages(self, evt: MessageEvent):
        yield evt
        if self.config['reply_in_thread']:
            while evt.content.relates_to.in_reply_to:
                evt = await self.client.get_event(room_id=evt.room_id, event_id=evt.content.get_reply_to())
                yield evt
        else:
            event_context = await self.client.get_event_context(room_id=evt.room_id, event_id=evt.event_id, limit=self.config["max_context_messages"]*2)
            previous_messages = iter(event_context.events_before)
            for evt in previous_messages:
                # We already have the event, but currently, get_event_context doesn't automatically decrypt events
                if isinstance(evt, EncryptedEvent) and self.client.crypto:
                    evt = await self.client.get_event(event_id=evt.event_id, room_id=evt.room_id)
                    if not evt:
                        raise ValueError("Decryption error!")

                yield evt

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config