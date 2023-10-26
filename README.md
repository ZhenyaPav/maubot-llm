# maubot-llm
A Matrix AI chat bot using [Oogabooga's text-gen-webui](https://github.com/oobabooga/text-generation-webui) backend.
Based on the [ChatGPT Maubot Plugin](https://github.com/williamkray/maubot-chatgpt)

This bot is still in early stages of development, and will probably require tinkering to run it.

### Character cards

This bot supports TavernAI character cards (mainly 2.0 version). Due to the nature of Matrix chats, the starting message is not used right now, so cards with lots of example messages would likely work better.

## TODO:

- Add proper support for multi character chats (stopping strings currently only include the author of the last message)
- Token counting

## Completed

- (Mostly) TavernAI character card support - Characted definition, personality and example messages are added to the prompt. If the Matrix client's avatar is not set, the card is uploaded and used as the avatar (can be disabled in settings).