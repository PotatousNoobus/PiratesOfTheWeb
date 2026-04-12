# 🏴‍☠️ Pirates of the Web 🌐

Ahoy, matey! Welcome to the digital high seas. This Discord bot is your trusty first mate, ready to plunder the vast ocean of the internet for all forms of digital treasure. It is a multi-talented pirate, capable of fetching movies, games, eBooks, magazines, research papers, chatting with AI and much more!

## 🎰 Sin City Hackathon 2026 Edition
This version has been specially modified for the **Sin City: Las Vegas Hackathon**. The neon lights are buzzing, the stakes are high, and the bot features a uniform **Yellow Embed** interface to match the high-roller aesthetic.

## 🌟 Features

* **🎬 Movie Downloads and Streaming**: Get direct torrent search results for movies or stream them online instantly.
* **🎮 Game Downloads**: Find direct or torrent links for your favorite games from trusted sources.
* **📚 eBook/Magazine/Comic Scouring**: Instantly download almost every printed/digital reading material on the internet.
* **👁️ Multimodal Image Recognition**: Upload a book cover or movie poster and the bot will identify it using Gemini 2.5 Flash.
* **📖 Official Book Reviews**: Fetches "trustworthy" data (ratings, authors, official summaries) directly from the **Google Books API**.
* **🤖 AI Book Recommendations**: Ask a powerful AI for book recommendations based on your favorite genre or a specific book.
* **💬 AI Chat**: Have a full conversation with an AI right within your Discord server.
* **🐳 Dockerized**: Built for easy deployment and management with Docker.

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
      <td>Headless Playwright interaction with SteamRIP for direct links.</td>
    </tr>
    <tr>
      <td><code>/game_torrent</code></td>
      <td>Scrapes trusted sources for high-quality magnet links.</td>
    </tr>
    <tr>
      <td rowspan="2" align="center"> popcorn <br><b>Cinema</b></td>
      <td><code>/movie</code></td>
      <td>Simulates physical typing/searching on torrent databases.</td>
    </tr>
    <tr>
      <td><code>/stream</code></td>
      <td>Directly constructs dynamic streaming links via Westream.</td>
    </tr>
    <tr>
      <td rowspan="3" align="center">🤖<br><b>AI Hub</b></td>
      <td><code>/ask</code></td>
      <td>General-purpose knowledge retrieval via Gemini 2.5 Flash.</td>
    </tr>
    <tr>
      <td><code>/image</code></td>
      <td>Computer Vision to identify posters or covers from uploads.</td>
    </tr>
    <tr>
      <td><code>/recommend</code></td>
      <td>Context-aware AI recommendations for books/movies.</td>
    </tr>
    <tr>
      <td rowspan="2" align="center">📚<br><b>Library</b></td>
      <td><code>/ebook</code></td>
      <td>Automated pathfinding on Anna's Archive for PDF/EPUBs.</td>
    </tr>
    <tr>
      <td><code>/review</code></td>
      <td>Google Books API integration for official critiques.</td>
    </tr>
  </tbody>
</table>

---

## 🚀 Deployment (Recommended)

This bot is designed to be deployed using Docker, which handles all the dependencies and setup for you.

### 1. Prerequisites

* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/)

### 2. Configuration

Create a file named `.env` in the root of the project directory and add your secret keys:

```env
DISCORD_TOKEN=YOUR_SECRET_BOT_TOKEN_HERE
GEMINI_API_KEY=YOUR_GOOGLE_AI_API_KEY_HERE
GOOGLE_BOOKS_API_KEY=YOUR_GOOGLE_BOOKS_API_KEY_HERE
