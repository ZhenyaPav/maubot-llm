# maubot-llm
A Matrix AI chat bot using [Oogabooga's text-gen-webui](https://github.com/oobabooga/text-generation-webui) backend.
Based on the [ChatGPT Maubot Plugin](https://github.com/williamkray/maubot-chatgpt)

This bot is still in early stages of development, and will probably require tinkering to run it.

## TODO:

- Add proper support for multi character chats (stopping strings currently only include the author of the last message)
- Token counting

## Completed

- (Mostly) TavernAI character card support - Characted definition, personality and example messages are added to the prompt. If the Matrix client's avatar is not set, the card is uploaded and used as the avatar (can be disabled in settings).