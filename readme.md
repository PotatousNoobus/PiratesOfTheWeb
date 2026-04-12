# 🏴‍☠️ Pirates of the Web 🦜

Ahoy, matey! Welcome to the digital high seas. This Discord bot is your trusty first mate, ready to plunder the vast ocean of the internet for entertainment. What started as a movie bot has grown into a multi-talented pirate, capable of fetching movies, eBooks, and more!

## 🌟 Features

*   **🎬 Movie Streaming**: Get direct stream links for any movie.
*   **📚 eBook Scouring**: Find links to download eBooks from Anna's Archive.
*   **🤖 AI Book Recommendations**: Ask the AI for book recommendations based on your favorite genre.
*   **💬 AI Chat**: Have a conversation with a powerful AI right within your Discord server.
*   **🐳 Dockerized**: Easy to deploy and manage with Docker.

---

## 🚀 Deployment (Recommended)

This bot is designed to be deployed using Docker, which handles all the dependencies and setup for you.

### 1. Prerequisites

*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### 2. Configuration

Create a file named `.env` in the root of the project directory and add your Discord bot token:

```env
DISCORD_BOT_TOKEN=YOUR_SECRET_BOT_TOKEN_HERE
```

### 3. Create Docker Files

Create a `Dockerfile` and a `docker-compose.yml` in your project's root directory.

#### `Dockerfile`

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# and install playwright dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

# Copy the rest of the application's code into the container
COPY . .

# Run the bot when the container launches
CMD ["python", "main.py"]
```

#### `docker-compose.yml`

```yaml
version: '3.8'
services:
  pirates-of-the-web:
    build: .
    container_name: pirates_of_the_web_bot
    restart: unless-stopped
    env_file:
      - .env
```

### 4. Run with Docker Compose

Open your terminal in the project's root directory and run:

```bash
docker-compose up --build -d
```

Your bot is now online!  sailing the digital seas.

---

## 💻 Local Installation (For Development)

If you prefer to run the bot on your local machine for testing or development, follow these steps.

### 1. Prerequisites

*   Python 3.8+

### 2. Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/PotatousNoobus/PiratesOfTheWeb.git
    cd PiratesOfTheWeb
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    Create a `requirements.txt` file with the following content:
    ```txt
    discord.py
    playwright
    google-generativeai
    python-dotenv
    ```
    Then, run the installer:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright browsers:**
    This command downloads the necessary browser binaries for Playwright.
    ```bash
    playwright install
    ```

5.  **Configure your bot token:**
    Create a file named `.env` in the root project directory. Add your Discord bot token like so:
    ```env
    DISCORD_BOT_TOKEN=YOUR_SECRET_BOT_TOKEN_HERE
    ```

### 3. Running the Bot Locally

Once you've completed the setup, you can start the bot with:

```bash
python main.py
```

---

## 🤖 Bot Commands

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `!stream` | `<movie_name>` | 🎬 Provides a direct stream link for the specified movie. |
| `!ebook` | `<book_name>` | 📚 Searches Anna's Archive and returns the link for the first result. |
| `!chat` | `<message>` | 💬 Starts a conversation with the Gemini AI. |
| `!recommend`| `<genre>` | 🌟 Asks the AI to recommend 5 books from a specific genre. |

Enjoy your adventures on the high seas! 🌊
