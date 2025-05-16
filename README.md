---

# Alien Invasion

This repository contains a Python-based game called **Alien Invasion**, where players defend their spaceship against waves of alien invaders. The game features a title screen, customizable settings, username input, and a persistent high score system.

---

## Repository Structure

### 1. **`.gitattributes`**
- Used to define attributes for files in the repository.
- Ensures consistent Git behavior across different environments.

### 2. **`.github/`**
- Folder reserved for GitHub-specific configurations like workflows, issue templates, or pull request templates.

### 3. **`alien_invasion/`**
- Primary directory containing the source code for the Alien Invasion game.
- Includes the game logic, assets, and related scripts.

---

## Game Overview

**Alien Invasion** is a classic arcade-style shooting game where:
- Players navigate a title screen with options to Start Game, access Settings, or Exit.
- Upon starting, players enter a username to track their scores.
- Players control a spaceship and shoot waves of alien invaders.
- Game settings (like ship speed, bullet speed, alien speed, etc.) can be adjusted on a dedicated Settings page using sliders.
- Aliens move progressively faster as the game continues.
- The goal is to score points by destroying aliens while avoiding being hit.
- High scores are saved per username and persist across game sessions.

---

## How to Play

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/bentted/alien_invasion.py.git
    cd alien_invasion.py
    ```

2.  **Install Dependencies**:
    Ensure Python is installed on your system. The game uses the `pygame` library. Install it using:
    ```bash
    pip install pygame
    ```

3.  **Run the Game**:
    Navigate to the `alien_invasion` directory and execute the main script:
    ```bash
    python alien_invasion/Alien_Invasion.py 
    ```
    *(Note: The main script is `Alien_Invasion.py`, not `main.py` as previously stated).*

4.  **Navigating the Game**:
    -   **Title Screen**: Use the mouse to click "Start Game", "Settings", or "Exit".
    -   **Username Input**: After clicking "Start Game", type your desired username and press Enter.
    -   **Settings Page**: Adjust game parameters using the sliders. Click "Back" or press ESC to return to the title screen (settings are applied automatically).
    -   **Gameplay**: Once a username is entered and "Play" is clicked (after username input), the game begins.

5.  **Controls (During Gameplay)**:
    -   Use **arrow keys** (Left/Right) to move the spaceship.
    -   Press the **spacebar** to shoot.
    -   Press **ESC** to quit the game at any time (your high score will be saved).
    -   Press **'q'** during gameplay to quit (your high score will be saved).


---

## Features
- Engaging gameplay with increasing difficulty.
- Dynamic alien movements and shooting mechanics.
- Interactive Title Screen with navigation to game, settings, and exit options.
- Username input for personalized gameplay.
- Customizable game settings via an intuitive Settings Page with sliders for:
    - Ship Limit
    - Bullets Allowed
    - Ship Speed
    - Bullet Speed
    - Alien Speed
    - Fleet Drop Speed
    - Game Speedup Scale
    - Score Scale
    - Bullet Width & Height
- Persistent high score system:
    - Scores are tracked per username.
    - High scores are saved to `high_scores.json` and loaded at game start.
- Score tracking and game-over conditions.
- Option to quit the game using the ESC key, ensuring scores are saved.

---

## Contribution
Feel free to fork the repository, make improvements, and submit a pull request. Contributions are welcome!

---


