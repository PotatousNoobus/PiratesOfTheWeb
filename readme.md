# 🏴‍☠️ Pirates of the Web 🌐

Ahoy, matey! Welcome to the digital high seas. This Discord bot is your trusty first mate, ready to plunder the vast ocean of the internet for all forms of digital treasure. It is a multi-talented pirate, capable of fetching movies, games, eBooks, magazines, research papers, chatting with AI and much more!

## 🌟 Features

* **🎬 Movie Downloads and Streaming**: Get direct torrent search results for movies or stream them online instantly.
* **🎮 Game Downloads**: Find direct or torrent links for your favorite games from trusted sources.
* **📚 eBook/Magazine/Comic Scouring**: Instantly download almost every printed/digital reading material on the internet.
* **👁️ Multimodal Image Recognition**: Upload a book cover or movie poster and the bot will identify it using Gemini 2.5 Flash.
* **📖 Official Book Reviews**: Fetches trustworthy data (ratings, authors, official summaries) directly from the **Google Books API**.
* **🤖 AI Book Recommendations**: Ask a powerful AI for book recommendations based on your favorite genre or a specific book.
* **💬 AI Chat**: Have a full conversation with an AI right within your Discord server.
* **🐳 Dockerized**: Built for easy deployment and management with Docker.

## 🤖 Bot Commands

All commands are slash commands (e.g., `/movie`, not `!movie`).

<table>
  <thead>
    <tr>
      <th>Category</th>
      <th>Command</th>
      <th>The "Secret Sauce" (How it Works)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2" align="center">🎮<br><b>Gaming</b></td>
      <td><code>/game_direct</code></td>
      <td>Headless Playwright interaction for direct links.</td>
    </tr>
    <tr>
      <td><code>/game_torrent</code></td>
      <td>Scrapes trusted sources for high-quality magnet links.</td>
    </tr>
    <tr>
      <td rowspan="2" align="center"> popcorn <br><b>Cinema</b></td>
      <td><code>/movie_torrent</code></td>
      <td>Simulates physical typing/searching on torrent databases.</td>
    </tr>
    <tr>
      <td><code>/stream</code></td>
      <td>Directly constructs dynamic streaming links.</td>
    </tr>
    <tr>
      <td rowspan="3" align="center">🤖<br><b>AI Hub</b></td>
      <td><code>/chat</code></td>
      <td>General-purpose knowledge retrieval via Gemini 2.5 Flash.</td>
    </tr>
    <tr>
      <td><code>/detect</code></td>
      <td>Computer Vision to identify posters or covers from uploads.</td>
    </tr>
    <tr>
      <td><code>/book_recommend</code></td>
      <td>Context-aware AI recommendations for books/movies.</td>
    </tr>
    <tr>
      <td rowspan="2" align="center">📚<br><b>Library</b></td>
      <td><code>/ebook</code></td>
      <td>Automated pathfinding on for PDFs, EPUBs, etc.</td>
    </tr>
    <tr>
      <td><code>/book_review</code></td>
      <td>Google Books API integration for official critiques.</td>
    </tr>
  </tbody>
</table>

Enjoy your adventures on the high seas! 🌊
---

## 🚀 Deployment (Recommended)



This bot is designed to be deployed using Docker, which handles all the dependencies and setup for you.



### 1. Prerequisites



*   [Docker](https://www.docker.com/get-started)

*   [Docker Compose](https://docs.docker.com/compose/install/)



### 2. Configuration



Create a file named `.env` in the root of the project directory and add your Discord bot token and Google API Key:



```env

DISCORD_BOT_TOKEN=YOUR_SECRET_BOT_TOKEN_HERE

GOOGLE_API_KEY=YOUR_GOOGLE_AI_API_KEY_HERE

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



# Install dependencies and Playwright's browser

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



Your bot is now online and sailing the digital seas! ⛵



---



## 💻 Local Installation (For Development)



If you prefer to run the bot on your local machine for testing or development, follow these steps.



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

    ```bash

    playwright install

    ```



5.  **Configure environment variables:**

    Create a file named `.env` and add your keys:

    ```env

    DISCORD_BOT_TOKEN=YOUR_SECRET_BOT_TOKEN_HERE

    GOOGLE_API_KEY=YOUR_GOOGLE_AI_API_KEY_HERE

    ```



6.  **Running the Bot Locally:**

    ```bash

    python main.py

    ```



---
