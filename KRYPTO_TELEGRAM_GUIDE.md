# How to Create a Dedicated "Krypto" Telegram Bot

Since your existing bot is named "ISA", you need a separate bot identity for the Krypto engine to avoid confusion.

## Phase 1: Create the Bot (Using @BotFather)
1.  Open Telegram app and search for **@BotFather** (verified badge).
2.  Send the command: `/newbot`
3.  **Name**: Enter a display name, e.g., `Krypto Sentinel` or `Sovereign Krypto`.
4.  **Username**: Choose a unique username ending in `bot`, e.g., `Sovereign_Krypto_Bot`.
5.  **Copy the Token**: BotFather will give you an API Token (looks like `123456:ABC-DEF...`). **Save this.**

## Phase 2: Create the Channel/Group
1.  Create a **New Group** in Telegram.
2.  Name it `Krypto Alerts` (or your preference).
3.  **Add Members**: Search for your new bot's username and add it to the group.

## Phase 3: Get the Chat ID
1.  Send a test message (e.g., "Hello") to your new group.
2.  Visit this URL in your browser (replace `<YOUR_TOKEN>` with the token from Phase 1):
    `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3.  Look for the `"chat":{"id": -100123456789...` section in the JSON response.
4.  Copy that number (including the negative sign if present). This is your `CHAT_ID`.

## Phase 4: Update Credentials
I have updated your `.env` file to include specific slots for this new bot.
1.  Open `.env`.
2.  Paste your new token into `TELEGRAM_TOKEN_KRYPTO`.
3.  Paste your new chat ID into `TELEGRAM_CHAT_ID_KRYPTO`.
