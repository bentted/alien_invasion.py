# Alien Invasion

Alien Invasion is a Python-based arcade-style game where players control a spaceship to defend against waves of alien invaders. The game features dynamic gameplay, customizable settings, a global leaderboard, and a unique level code system.

---

## Table of Contents

1. [Game Overview](#game-overview)
2. [Features](#features)
3. [How to Play](#how-to-play)
4. [Level Codes](#level-codes)
5. [Leaderboard Server](#leaderboard-server)
6. [Installation](#installation)
7. [Repository Structure](#repository-structure)
8. [Contribution](#contribution)
9. [License](#license)

---

## Game Overview

Alien Invasion is a classic shooting game where players:
- Navigate a spaceship to shoot down waves of alien invaders.
- Progress through increasingly challenging levels.
- Customize game settings to adjust difficulty.
- Compete with others on a global leaderboard.
- Use unique level codes to skip to specific levels.

The game is built using Python and the `pygame` library, offering an engaging and interactive experience.

---

## Features

### Gameplay
- **Dynamic Alien Waves**: Aliens move faster and drop closer as levels progress.
- **Score Tracking**: Earn points by destroying aliens. Scores are displayed in real-time.
- **Game Over Conditions**: Lose a life when an alien reaches the bottom or collides with your ship.

### Title Screen
- **Start Game**: Begin a new game or resume from a level code.
- **Settings**: Adjust gameplay parameters using sliders.
- **Enter Level Code**: Input a code to start at a specific level.
- **Exit**: Quit the game.

### Customizable Settings
Adjustable parameters include:
- Ship Limit
- Bullets Allowed
- Ship Speed
- Bullet Speed
- Alien Speed
- Fleet Drop Speed
- Speedup Scale
- Score Scale
- Bullet Width and Height

### Level Codes
- Each level generates a unique code upon completion.
- Players can use these codes to start at specific levels.

### Global Leaderboard
- Submit scores to a global leaderboard.
- View the top scores on the title screen.
- Admin features for managing users and scores.

### Persistent High Scores
- High scores are saved locally in `high_scores.json`.
- Scores are loaded at the start of the game.

---

## How to Play

### Controls
- **Arrow Keys**: Move the spaceship left or right.
- **Spacebar**: Shoot bullets.
- **ESC**: Quit the game (scores are saved).
- **Q**: Quit the game immediately.

### Gameplay
1. **Start the Game**: Click "Start Game" on the title screen.
2. **Enter Username**: Input your username to track scores.
3. **Shoot Aliens**: Use the spacebar to shoot and arrow keys to move.
4. **Progress Through Levels**: Destroy all aliens to advance to the next level.
5. **Game Over**: Lose all lives or let an alien reach the bottom.

---

## Level Codes

- After completing a level, a unique code is displayed.
- Save this code to start at the same level later.
- On the title screen, click "Enter Level Code" to input a code and start at the corresponding level.

---

## Leaderboard Server

The game includes a Flask-based leaderboard server to manage global scores.

### API Endpoints

#### Public Endpoints
- **POST /api/scores**: Submit a score. Requires `username` and `score`.
- **GET /api/leaderboard**: Retrieve the top 10 scores.

#### Admin Endpoints
- **DELETE /api/admin/users/<username>**: Remove a user.
- **PUT /api/admin/users/<username>/score**: Update a user's score.
- **PUT /api/admin/users/<username>/ban**: Ban a user.
- **PUT /api/admin/users/<username>/unban**: Unban a user.

### Running the Server
1. Navigate to the project directory.
2. Run the server using:
   ```bash
   python leaderboard_server.py
   ```
3. The server will be available at `http://127.0.0.1:5000`.

---

## Installation

### Prerequisites
- Python 3.8 or higher
- `pip` package manager

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/alien_invasion.git
   cd alien_invasion.py
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the game:
   ```bash
   python alien_invasion/Alien_Invasion.py
   ```

---

## Repository Structure

```
alien_invasion.py/
├── alien_invasion/
│   ├── Alien_Invasion.py       # Main game script
│   ├── settings.py             # Game settings
│   ├── game_stats.py           # Game statistics
│   ├── scoreboard.py           # Scoreboard logic
│   ├── ship.py                 # Ship logic
│   ├── bullet.py               # Bullet logic
│   ├── alien.py                # Alien logic
│   ├── slider.py               # Slider for settings
│   ├── buttons.py              # Button logic
├── leaderboard_server.py       # Flask-based leaderboard server
├── high_scores.json            # Local high score storage
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
```

---

## Contribution

Contributions are welcome! Follow these steps to contribute:
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Make your changes and commit them:
   ```bash
   git commit -m "Add feature-name"
   ```
4. Push to your fork:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
