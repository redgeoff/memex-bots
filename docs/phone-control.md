# Controlling a bot from your phone (Slack)

Some agent platforms have no mobile app. A private Slack channel per bot works as a
remote control: you post a request from the Slack mobile app, and a routine on the bot
wakes up, does the work and replies in the thread. A free Slack workspace is enough.

## Setup (one bot)

1. **Connect Slack to the bot** (a Slack plugin or connector on your agent platform), so
   it can read the channel and post replies.
2. **Create one private channel per bot**, e.g. `#my-bot`, so routing stays clear.
3. **Create a routine triggered by any message in that channel.** Its prompt must:
   - treat your posts as requests;
   - reply **in the message's thread**, briefly;
   - give choices as **numbered text**, since interactive widgets may not render;
   - never message anyone else;
   - **ignore its own messages.** If the connector posts as you, the bot's replies
     re-trigger the routine, so it must recognize and skip them to avoid a loop.
4. **Invite the platform's Slack app to the channel** if it needs one.
5. **Test** by posting `hi`. The bot should reply in the thread.

## Limits

- Routines may not be able to listen to DMs; use a channel.
- Approvals, sign-ins and file uploads usually still need the desktop app.
- Anything that would go to another person stays a **draft** for your approval.

## Copy-paste routine prompt

> A message was posted in #<bot-name>. If it is your own message (a reply you posted),
> do nothing and stop. Otherwise treat my post as a request to you. Do the work, then
> reply in that message's thread. Keep the reply short, and give any choices as a
> numbered list in plain text. Never message any other person or channel. Anything
> addressed to someone else stays a draft for my approval. If something needs approval,
> a sign-in or a file upload, say so and tell me to use the desktop app.
