# maubot-llm
A Matrix AI chat bot using [Oogabooga's text-gen-webui](https://github.com/oobabooga/text-generation-webui) backend.
Based on the [ChatGPT Maubot Plugin](https://github.com/williamkray/maubot-chatgpt)

~This bot is still in early stages of development, and will probably require tinkering to run it.~

Since text-generation-webui has transitioned to OpenAI API, this project is now deprecated, and the [Original Maubot Plugin](https://github.com/williamkray/maubot-chatgpt) should be used instead.

### Character cards

This bot supports TavernAI character cards (mainly 2.0 version). Due to the nature of Matrix chats, the starting message is not used right now, so cards with lots of example messages would likely work better.

## TODO:

- Better multi-user support (some kind of unprompted (not reply or mentioning bot's name in the message) response logic?)
- Context token counting
- Add more settings (text-gen-ui URL, frequency of unprompted responses, etc)

## Completed

- (Mostly) TavernAI character card support - Characted definition, personality and example messages are added to the prompt. If the Matrix client's avatar is not set, the card is uploaded and used as the avatar (can be disabled in settings).
