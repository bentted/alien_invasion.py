# Alien Invasion Game

Alien Invasion is a feature-rich 2D space shooter game built using Python and Pygame. Players control a spaceship to defend against waves of aliens, earn points, and unlock upgrades. The game includes multiplayer functionality, a marketplace, achievements, and more.

---

## Features

### 1. **Core Gameplay**
- **Spaceship Control**: Move the spaceship left or right and shoot bullets to destroy aliens.
- **Alien Waves**: Aliens move in a fleet and drop down as they approach the player.
- **Levels**: Progress through increasingly difficult levels as you destroy all aliens in a wave.
- **Score System**: Earn points for destroying aliens and completing levels.

### 2. **Multiplayer Mode**

Alien Invasion now supports a multiplayer mode where players can compete against each other. Features include:

- **Random Matchmaking**: Join a queue to be matched with another player.
- **Host or Join**: Players can choose to host a game or join an existing one.
- **Opponent Aliens**: Send aliens to your opponent to increase the challenge.

### How to Start Multiplayer
1. From the title screen, click the "Multiplayer" button.
2. Choose to host a game or join a random match.
3. Play against your opponent and try to win!

### 3. **Voice Chat**

The game also includes a voice chat feature for multiplayer mode. Players can communicate with each other during the game.

### How to Use Voice Chat
- Voice chat starts automatically when a multiplayer game begins.
- Ensure your microphone and speakers are properly configured.

### Restrictions
- Voice chat may be disabled for users who have been reported or kicked for inappropriate behavior.

### 4. **Marketplace**
- **Purchase Items**: Spend in-game currency to buy ships, alien skins, and upgrades.
- **Available Items**:
  - New Ship: Unlock a new spaceship design.
  - Alien Skin: Customize the appearance of aliens.
  - Speed Upgrade: Increase ship speed.
  - Fire Rate Upgrade: Increase bullet speed.
  - Extra Life: Gain an additional life.

### 5. **Achievements**
- **Track Progress**: Unlock achievements based on your performance.
- **Achievements List**:
  - **First Blood**: Destroy your first alien.
  - **Sharp Shooter**: Destroy 50 aliens.
  - **Survivor**: Survive 5 levels.
  - **Chest Collector**: Collect 5 chests.
  - **High Scorer**: Score 10,000 points.
- **Achievements Screen**: View all achievements and their unlock status.

### 6. **Chest Drops**
- **Earn Rewards**: For every 1,000 points, a chest drops with a random upgrade.
- **Temporary Upgrades**: Upgrades last until the player loses a life.
- **Possible Upgrades**:
  - Double Speed: Doubles the ship's speed.
  - Double Fire Rate: Doubles the bullet speed.
  - Double Score: Doubles the score multiplier.

### 7. **Global Leaderboard**
- **High Scores**: Compete with other players by submitting your high scores.
- **Leaderboard Display**: View the top scores on the title screen.

### 8. **Settings**
- **Customizable Gameplay**: Adjust game settings using sliders.
- **Available Settings**:
  - Ship Limit: Set the number of lives.
  - Bullets Allowed: Limit the number of bullets on screen.
  - Ship Speed: Adjust the speed of the spaceship.
  - Bullet Speed: Adjust the speed of bullets.
  - Alien Speed: Adjust the speed of aliens.
  - Fleet Drop Speed: Adjust how quickly aliens drop down.
  - Speedup Scale: Adjust how quickly the game speeds up.
  - Score Scale: Adjust the score multiplier.
  - Bullet Dimensions: Customize bullet width and height.

### 9. **Login and Registration**
- **User Profiles**: Create and log in to user profiles.
- **High Score Tracking**: Track high scores for individual users.
- **Penalty and Bonus**: Load user-specific penalties and bonuses from the server.

### 10. **Reports and Moderation**
- **Report Users**: Report players for inappropriate behavior in multiplayer chat.
- **Report Reasons**: Choose from predefined topics like "Hate Speech" or "Harassment."
- **Moderation**: Reports are sent to the server for review.

---

## Installation

### Prerequisites
- Python 3.8 or higher
- Pygame library
- Additional dependencies:
  - `pyaudio` for voice chat
  - `requests` for server communication
  - `stem` for Tor proxy support (optional)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/alien_invasion.py.git
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

## Controls

- **Arrow Keys**: Move the spaceship left or right.
- **Spacebar**: Shoot bullets.
- **Escape**: Pause or exit the game.

---

## Screens

### 1. **Title Screen**
- Start the game, access settings, view the leaderboard, or enter multiplayer mode.

### 2. **Settings Screen**
- Adjust gameplay settings using sliders.

### 3. **Marketplace**
- Spend in-game currency to purchase items and upgrades.

### 4. **Achievements Screen**
- View all achievements and their unlock status.

### 5. **Gameplay Screen**
- Control your spaceship, destroy aliens, and progress through levels.

---

## Future Enhancements

- **Additional Achievements**: Add more achievements for advanced players.
- **New Game Modes**: Introduce time attack or survival modes.
- **Cosmetic Upgrades**: Expand the marketplace with more customization options.

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.


