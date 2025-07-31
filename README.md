# 🛡️ LSPD Discord Bot

The **LSPD Discord Bot** is a fully-featured roleplay assistant tailored for police department roleplay servers on Discord (e.g., MTA RP servers). Built with `discord.py`, this bot helps law enforcement teams stay organized, communicate efficiently, and manage role-specific tasks in an immersive and automated way.

## 🚓 Key Features

- **Duty Management System**
  - Slash commands: `/onduty`, `/offduty`
  - Auto-updates a duty status message per server
  - Creates and manages roles like `On Duty`, `Off Duty`

- **Command Access Control**
  - Restricts commands to roles like `Full access to commands`
  - Supports multiple role-based permissions

- **Structured Slash Commands**
  - `/announce [message]`: Broadcast department-wide messages
  - `/bolo [description]`: Issue "Be On the Lookout" alerts
  - `/store`, `/broadcast`, and more coming soon

- **Ticket Panel System** 🎫
  - React-based ticket creation with predefined categories
  - Auto-channel creation per request (e.g., refund, question)
  - Collects structured application information (e.g., name, age, experience)

- **Bot Logs**
  - Auto-creates a `#bot-logs` channel if it doesn’t exist
  - Logs command usage, ticket creation, and errors in clean embed format

- **Replit Hosting with Flask Keep-Alive**
  - Keeps the bot running 24/7 using a lightweight web server
  - Supports UptimeRobot or similar monitoring tools

## 🛠️ Tech Stack

- Python 3.x
- `discord.py` (API wrapper)
- Flask (for keep-alive on Replit)
- JSON for config and persistent storage

## 🌐 Hosting

This bot is designed to run on **Replit**. Flask is used to keep the process alive. You can connect it to **UptimeRobot** or another ping service to keep it running 24/7.

## 📂 Project Structure (Example)

