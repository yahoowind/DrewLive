🌟 DREWLIVE PLAYLIST & EPG LINKS 🌟  
Welcome to DrewLive — your 24/7 hub for cartoons, anime, action, and nostalgic vibes. Below is everything you need to plug in, stay up to date, and never miss a beat.

━━━━━━━━━━━━━━━━━━

📺 DREWLIVE LIVE STREAM (OWNCAST)  
Your main portal for nonstop streaming — DrewLive runs day and night with curated shows and blocks.  
• [http://drewlive24.duckdns.org:8080/](http://drewlive24.duckdns.org:8080/)

━━━━━━━━━━━━━━━━━━

📂 ALL PLAYLISTS IN ONE LINK  
Simplify your setup with every playlist in one place.  
🔗 All Playlists - DrewLive URL:  
• [https://tinyurl.com/drewall8](https://tinyurl.com/drewall8)  

━━━━━━━━━━━━━━━━━━

🎮 KODI FORMAT PLAYLIST  
Built for Kodi's PVR IPTV Simple Client with full header support — plug and play.  
🔗 Kodi Playlist - DrewLive URL:  
• [https://tinyurl.com/drewallkodi8](https://tinyurl.com/drewallkodi8)  

━━━━━━━━━━━━━━━━━━

📂 DREWLIVE VOD STRM BUNDLE  
Want to take DrewLive with you? Grab our `.strm` files!  

These are simple text files with streaming URLs, named clearly like `Movie Title (Year).strm`. Just download the whole folder, then point your media app (Kodi, Jellyfin, or others) to it. Your player will list all your movies and shows by name, ready to stream instantly — no complicated setup needed.  

It’s perfect for people who want neat, playlists with clickable streams and nice titles, without messing with complicated playlists or apps.  

📥 DrewLive VOD Folder:  
• [https://tinyurl.com/drewlive-vod24](https://tinyurl.com/drewlive-vod24)  

━━━━━━━━━━━━━━━━━━

✨ CLEAN IPTV PLAYLIST  
This is the clean version of the merged IPTV playlist created by the merge script.

All channels tagged or containing keywords like NSFW, XXX, or Porn have been filtered out.

Suitable for kids and family-friendly viewing.

Organized by channel groups for easy navigation.

Updated automatically to keep your playlist fresh and safe.

• [https://tinyurl.com/MergedClean24](https://tinyurl.com/MergedClean24)  

━━━━━━━━━━━━━━━━━━

🗓️ EPG LINKS  
Stay synced with live guide data for your players. Pick the one that fits your needs:  

🔗 Merged EPG (Full Source)  
✔️ Full EPG data from all sources  
⚠️ Missing some world/regional info  
• [https://tinyurl.com/merged24-epg](https://tinyurl.com/merged24-epg)  

🔗 Merged EPG (No IPTV Crashes)  
✔️ Smooth on most players  
⚠️ May lack some local USA EPG  
• [https://tinyurl.com/merged2423-epg](https://tinyurl.com/merged2423-epg)  

🔗 All Source EPG  
✔️ Most comprehensive option available  
• [https://tinyurl.com/vizo24](https://tinyurl.com/vizo24)  

━━━━━━━━━━━━━━━━━━

📡 HOW TO USE EPG LINKS  
1. Go into your IPTV player's guide settings  
2. Paste in one of the EPG URLs above  
3. Save and refresh guide data  
4. Done — full channel listings ready to go  

⚠️ Pro tip: Some apps need a restart for EPG to fully load  

━━━━━━━━━━━━━━━━━━

[![Join DrewLive Discord](https://i.imgur.com/UPsQU4m.png)](https://discord.gg/GScZh8D3rB)  

👥 Join the DrewLive Discord!  
Get updates, ask questions, share setups, or just chill.  
Click the badge above or use this invite:  
• [https://discord.gg/GScZh8D3rB](https://discord.gg/GScZh8D3rB)  

━━━━━━━━━━━━━━━━━━

🎮 RECOMMENDED IPTV PLAYERS  
Use one of these for the cleanest DrewLive experience:  

• [Televizo](https://televizo.net/) – Lightweight and fast with advanced support  
• [Kodi](https://kodi.tv/) – Full-featured with deep customization and STRM support  
• [TiviMate](https://tivimate.com/) – Easy UI, strong playlist & EPG support  
• [IPTVNator](https://github.com/4gray/iptvnator/releases/tag/v0.16.0) – Open-source and modern  
• [UHF](https://www.uhfapp.com/) – Clean mobile player with native EPG  
• [Jellyfin](https://jellyfin.org/) – Great for library setups with built-in IPTV and VOD handling  

━━━━━━━━━━━━━━━━━━

🌐 UNLICENSED LICENSE  

This project is released under The Unlicense.  
Copy it, modify it, remix it, share it, sell it, whatever. No strings attached.

Legal TL;DR:  
• No copyright  
• No restrictions  
• No conditions  
• No warranties  

Disclaimer:  
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,  
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF  
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR  
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,  
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR  
OTHER DEALINGS IN THE SOFTWARE.  

Learn more at: [https://unlicense.org](https://unlicense.org)

## Simple Pong Game

This is a simple Pong game built with HTML, CSS, and JavaScript.

### How to Play

- Download (or clone) this repository.
- Make sure the following three files exist in the same directory:
  - `index.html`
  - `style.css`
  - `game.js`
- Open `index.html` in your browser and play!

### Files

<details>
<summary><strong>index.html</strong></summary>

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Simple Pong Game</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Simple Pong Game</h1>
    <canvas id="pong" width="700" height="400"></canvas>
    <script src="game.js"></script>
</body>
</html>
```
</details>

<details>
<summary><strong>style.css</strong></summary>

```css
body {
    background: #222;
    color: #fff;
    text-align: center;
    font-family: 'Segoe UI', Arial, sans-serif;
}

h1 {
    margin-top: 30px;
}

#pong {
    display: block;
    margin: 30px auto;
    background: #000;
    border: 2px solid #fff;
    box-shadow: 0 0 10px #333;
}
```
</details>

<details>
<summary><strong>game.js</strong></summary>

```javascript
const canvas = document.getElementById('pong');
const ctx = canvas.getContext('2d');

// Game settings
const paddleWidth = 10, paddleHeight = 80;
const ballRadius = 10;
const playerX = 20;
const aiX = canvas.width - paddleWidth - 20;
let playerY = canvas.height / 2 - paddleHeight / 2;
let aiY = canvas.height / 2 - paddleHeight / 2;
let playerScore = 0, aiScore = 0;

// Ball settings
let ball = {
    x: canvas.width / 2,
    y: canvas.height / 2,
    vx: 5 * (Math.random() > 0.5 ? 1 : -1),
    vy: 4 * (Math.random() > 0.5 ? 1 : -1),
    radius: ballRadius
};

function drawRect(x, y, w, h, color) {
    ctx.fillStyle = color;
    ctx.fillRect(x, y, w, h);
}

function drawCircle(x, y, r, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2, false);
    ctx.closePath();
    ctx.fill();
}

function drawText(text, x, y, color) {
    ctx.fillStyle = color;
    ctx.font = "36px Arial";
    ctx.fillText(text, x, y);
}

function resetBall() {
    ball.x = canvas.width / 2;
    ball.y = canvas.height / 2;
    ball.vx = 5 * (Math.random() > 0.5 ? 1 : -1);
    ball.vy = 4 * (Math.random() > 0.5 ? 1 : -1);
}

function draw() {
    // Clear
    drawRect(0, 0, canvas.width, canvas.height, "#000");
    // Center line
    for (let i = 0; i < canvas.height; i += 30) {
        drawRect(canvas.width/2 - 1, i, 2, 20, "#fff");
    }
    // Draw paddles
    drawRect(playerX, playerY, paddleWidth, paddleHeight, "#fff");
    drawRect(aiX, aiY, paddleWidth, paddleHeight, "#fff");
    // Draw ball
    drawCircle(ball.x, ball.y, ball.radius, "#fff");
    // Draw score
    drawText(playerScore, canvas.width / 4, 50, "#fff");
    drawText(aiScore, 3 * canvas.width / 4, 50, "#fff");
}

function clamp(val, min, max) {
    return Math.max(min, Math.min(max, val));
}

// Player paddle follows mouse Y
canvas.addEventListener('mousemove', function(evt) {
    const rect = canvas.getBoundingClientRect();
    let mouseY = evt.clientY - rect.top;
    playerY = clamp(mouseY - paddleHeight / 2, 0, canvas.height - paddleHeight);
});

function update() {
    // Move ball
    ball.x += ball.vx;
    ball.y += ball.vy;

    // Top/bottom wall collision
    if (ball.y - ball.radius < 0 || ball.y + ball.radius > canvas.height) {
        ball.vy = -ball.vy;
    }

    // Player paddle collision
    if (
        ball.x - ball.radius < playerX + paddleWidth &&
        ball.y > playerY &&
        ball.y < playerY + paddleHeight
    ) {
        ball.x = playerX + paddleWidth + ball.radius; // prevent sticking
        ball.vx = -ball.vx;
        // Add a bit of randomness based on hit position
        let collidePoint = ball.y - (playerY + paddleHeight / 2);
        collidePoint = collidePoint / (paddleHeight / 2);
        let angle = collidePoint * Math.PI / 4;
        let speed = Math.sqrt(ball.vx * ball.vx + ball.vy * ball.vy);
        ball.vx = speed * Math.cos(angle);
        ball.vy = speed * Math.sin(angle);
        if (ball.vx > 0) ball.vx = -ball.vx;
    }

    // AI paddle collision
    if (
        ball.x + ball.radius > aiX &&
        ball.y > aiY &&
        ball.y < aiY + paddleHeight
    ) {
        ball.x = aiX - ball.radius; // prevent sticking
        ball.vx = -ball.vx;
        let collidePoint = ball.y - (aiY + paddleHeight / 2);
        collidePoint = collidePoint / (paddleHeight / 2);
        let angle = collidePoint * Math.PI / 4;
        let speed = Math.sqrt(ball.vx * ball.vx + ball.vy * ball.vy);
        ball.vx = speed * Math.cos(angle);
        ball.vy = speed * Math.sin(angle);
        if (ball.vx < 0) ball.vx = -ball.vx;
    }

    // Score!
    if (ball.x - ball.radius < 0) {
        aiScore++;
        resetBall();
    }
    if (ball.x + ball.radius > canvas.width) {
        playerScore++;
        resetBall();
    }

    // AI paddle movement: follow the ball with some smoothing
    let target = ball.y - paddleHeight / 2;
    aiY += (target - aiY) * 0.09;
    aiY = clamp(aiY, 0, canvas.height - paddleHeight);
}

function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

// Start the game
gameLoop();
```
</details>
