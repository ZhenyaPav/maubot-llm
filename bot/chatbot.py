from .textgenwebui import run
from .config import Config
from .character import get_char_data, get_char_system_prompt
from .utils import replace_tags

import asyncio
import json
import os
import re
import warnings
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

        # Load character
        character_card_path = self.config.get('character_card_path', None)
        if character_card_path and os.path.isfile(character_card_path):
            self.character = get_char_data(character_card_path)
            self.log.debug(self.character)
            self.log.debug(f"Character card \"{self.character['name']}\" loaded")
            
            avatar_url = await self.client.get_avatar_url(self.client.mxid)
            # If the matrix avatar is not set, upload the character card and use it as the avatar
            if self.config['upload_avatar']\
                and (avatar_url is None or self.config['overwrite_existing_avatar']):
                with open(character_card_path, 'rb') as char_card_file:
                    avatar_bytes = char_card_file.read()
                    url = await self.client.upload_media(avatar_bytes, 'image/png', os.path.basename(character_card_path))
                    await self.client.set_avatar_url(url)
                    self.log.debug(f"Uploaded {character_card_path} as avatar, url={url}")

        # Set the name
        try:
            self.name = self.character['name']
        except AttributeError:
            self.name = await self.client.get_displayname(self.client.mxid) or \
            self.client.parse_user_id(self.client.mxid)[0]

        self.log.debug(f"DEBUG LLM plugin started with bot name: {self.name}")

    async def should_respond(self, event: MessageEvent) -> bool:
        name = self.name
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
        if re.search("(^|\s)(@)?" + name + "([ :,.!?]|$)", event.content.body, re.IGNORECASE):
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
            prompt = context[0]
            prompt = prompt + self.name + ': '
            await event.mark_read()
            # Call the text-gen-webui API to get a response
            await self.client.set_typing(event.room_id, timeout=99999)
            user = "\n" + (await self.client.get_displayname(event.sender) or \
                        self.client.parse_user_id(event.sender)[0]) + ": "

            context[1].add(user)
            stopping_strings = context[1]
            self.log.debug(prompt)
            self.log.debug(stopping_strings)
            response = await run(prompt, list(stopping_strings))

            # Send the response back to the chat room
            await self.client.set_typing(event.room_id, timeout=0)
            await event.respond(f"{response}")#, in_thread=self.config['reply_in_thread'])
        except Exception as e:
            self.log.exception(f"Something went wrong: {e}")
            await event.respond(f"Something went wrong: {e}")
    
    async def get_event_sender_name(self, event: MessageEvent) -> str:
        return await self.client.get_displayname(event.sender) or \
                        self.client.parse_user_id(event.sender)[0]

    # Retuns a tuple with the context and the list of stopping strings
    async def get_context(self, event: MessageEvent) -> (str,set[str]):

        # timestamp = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        system_context = ''
        if hasattr(self,'character'):
            char_prompt = get_char_system_prompt(self.character, await self.get_event_sender_name(event)) or ''
            user_name = await self.get_event_sender_name(event)
            system_context += replace_tags(char_prompt, self.name, user_name)
        else:
            self.log.warning("No character is loaded")
        word_count = 0
        chat_context = ''
        events = self.generate_context_messages(event)
        stopping_strings = set()
        async for next_event in events:
            if not hasattr(next_event,'content') \
                or not hasattr(next_event.content,'msgtype') \
                or not next_event.content['msgtype'].is_text \
                or next_event.content.body.startswith('!'):
                continue

            message = next_event.content.body + '\n'
            user = f"\n{await self.get_event_sender_name(next_event)}: "
                
            #if word_count >= self.config['max_words'] or message_count >= self.config['max_context_messages']:
            #    break

            chat_context = user + message + chat_context
            stopping_strings.add(user)

        return (f"{system_context}\n***\n{chat_context}", stopping_strings)

    # Returns the list of previous messages with UserID's of the senders
    async def generate_context_messages(self, evt: MessageEvent) -> MessageEvent:
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