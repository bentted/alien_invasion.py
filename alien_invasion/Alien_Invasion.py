import sys
from time import sleep, time
import json
import requests
from stem.control import Controller  
import pygame
import os
import threading
import random  
import socket
import queue
import pyaudio
from datetime import datetime, timedelta

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from buttons import Button
from ship import Ship
from bullet import Bullet
from alien import Alien
from slider import Slider


class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        self.screen_rect = self.screen.get_rect()
        pygame.display.set_caption("Alien Invasion")

        self.username = ""
        self.user_input = ""
        self.high_scores = {}
        self._load_high_scores()

        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.opponent_aliens = pygame.sprite.Group()

        self._create_fleet()

        self.title_screen_active = True
        self.settings_page_active = False
        self.username_input_active = False
        self.game_active = False
        self.level_code_input_active = False

        self.play_button = Button(self, "Play")
        self.start_button = Button(self, "Start Game")
        self.settings_button = Button(self, "Settings")
        self.exit_button = Button(self, "Exit")
        self.level_code_button = Button(self, "Enter Level Code")
        self.high_score_mode_button = Button(self, "High Score Mode")
        self.back_button = Button(self, "Back")
        self.multiplayer_button = Button(self, "Multiplayer")  # Add Multiplayer button
        self.marketplace_button = Button(self, "Marketplace")  # Add Marketplace button
        self.achievements_button = Button(self, "Achievements")  # Add Achievements button
        self.about_us_button = Button(self, "About Us")  # Add "About Us" button
        self.contact_us_button = Button(self, "Contact Us")  # Add "Contact Us" button

        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 72)

        self.leaderboard_font = pygame.font.SysFont(None, 36)
        self.global_leaderboard_data = []
        self.global_leaderboard_images = []
        self.max_leaderboard_entries = 5

        try:
            self.alien_title_image = pygame.image.load('images/alien_title.bmp')
        except pygame.error as e:
            print(f"Error loading title alien image: {e}")
            self.alien_title_image = None

        self._initialize_settings_sliders()
        self.server_url = "http://192.168.254.14:5555"  # Updated to connect to the leaderboard server
        self.use_tor = False  
        self.tor_proxy = "socks5h://127.0.0.1:9050"  

        self.sse_client_running = False
        self.leaderboard_update_pending = False
        self.sse_thread = None

        self.level_codes = {} 
        self.high_score_mode = False 

        self.chat_messages = [] 
        self.chat_input_active = False
        self.chat_user_input = ""
        self.chat_update_pending = False
        self.chat_thread = threading.Thread(target=self._listen_for_chat_updates, daemon=True)
        self.chat_thread.start()

        self._load_global_leaderboard()
        self._start_sse_listener()

        self.penalty_per_alien = 0 
        self.bonus_per_alien = 0  
        self.login_screen_active = True
        self.registration_screen_active = False
        self.login_username = ""
        self.login_password = ""
        self.registration_username = ""
        self.registration_password = ""
        self.registration_confirm_password = ""
        self.dropdown_active = False
        self.dropdown_rect = None
        self.selected_username = None
        self.user_profile_data = None 
        self.report_window_active = False
        self.report_topics = ["Hate Speech", "Harassment", "CP", "Gore", "Rude", "Hateful"]
        self.selected_report_topic = None
        self.report_details_input = ""  
        self.report_details_active = False  
        self.upgrade_active = None 
        self.upgrade_timer = 0  

        self.social_score = 0  

        self.is_multiplayer = False
        self.network_thread = None
        self.server_socket = None
        self.client_socket = None
        self.is_host = False

        self.multiplayer_stats = {"wins": 0, "losses": 0}  # Track multiplayer wins and losses

        self.matchmaking_queue = queue.Queue()  # Queue for random matchmaking
        self.matchmaking_thread = None

        self.voice_chat_enabled = False
        self.voice_chat_thread = None
        self.voice_chat_socket = None
        self.audio_stream = None

        self.kick_list = {}  # Track kicked users and their ban expiration

        self.marketplace_active = False
        self.marketplace_items = [
            {"name": "New Ship", "cost": 500, "type": "ship"},
            {"name": "Alien Skin", "cost": 300, "type": "alien"},
            {"name": "Speed Upgrade", "cost": 200, "type": "upgrade", "effect": "speed"},
            {"name": "Fire Rate Upgrade", "cost": 200, "type": "upgrade", "effect": "fire_rate"},
            {"name": "Extra Life", "cost": 1000, "type": "upgrade", "effect": "life"}
        ]
        self.player_currency = 1000  # Starting currency for the player

        self.chest_drop_threshold = 1000  # Points required for a chest drop
        self.last_chest_drop_score = 0  # Track the score at the last chest drop
        self.active_chest_upgrade = None  # Track the active chest upgrade

        self.achievements_active = False
        self.achievements = [
            {"name": "First Blood", "description": "Destroy your first alien.", "unlocked": False},
            {"name": "Sharp Shooter", "description": "Destroy 50 aliens.", "unlocked": False},
            {"name": "Survivor", "description": "Survive 5 levels.", "unlocked": False},
            {"name": "Chest Collector", "description": "Collect 5 chests.", "unlocked": False},
            {"name": "High Scorer", "description": "Score 10,000 points.", "unlocked": False},
        ]
        self.chests_collected = 0  # Track the number of chests collected

        self.available_ship_skins = [
            {"name": "Default Skin", "image": "images/ship.bmp", "cost": 0, "unlocked": True},
            {"name": "Red Ship", "image": "images/ship_red.bmp", "cost": 300, "unlocked": False},
            {"name": "Blue Ship", "image": "images/ship_blue.bmp", "cost": 300, "unlocked": False},
            {"name": "Green Ship", "image": "images/ship_green.bmp", "cost": 300, "unlocked": False},
        ]
        self.current_ship_skin = self.available_ship_skins[0]  # Default skin

        self.available_alien_skins = [
            {"name": "Default Alien", "image": "images/alien.bmp", "cost": 0, "unlocked": True},
            {"name": "Red Alien", "image": "images/alien_red.bmp", "cost": 300, "unlocked": False},
            {"name": "Blue Alien", "image": "images/alien_blue.bmp", "cost": 300, "unlocked": False},
            {"name": "Green Alien", "image": "images/alien_green.bmp", "cost": 300, "unlocked": False},
        ]
        self.current_alien_skin = self.available_alien_skins[0]  # Default alien skin

        self.available_backgrounds = [
            {"name": "Default Background", "image": "images/background_default.bmp", "cost": 0, "unlocked": True},
            {"name": "Space Background", "image": "images/background_space.bmp", "cost": 500, "unlocked": False},
            {"name": "Galaxy Background", "image": "images/background_galaxy.bmp", "cost": 500, "unlocked": False},
            {"name": "Nebula Background", "image": "images/background_nebula.bmp", "cost": 500, "unlocked": False},
        ]
        self.current_background = self.available_backgrounds[0]  # Default background
        self.background_image = pygame.image.load(self.current_background["image"])

        self.win_music = "sounds/upbeat_music.mp3"
        self.lose_music = "sounds/dramatic_music.mp3"
        self.background_music = "sounds/default_background_music.mp3"
        self.is_admin = False  # Flag to determine if the user is an admin
        pygame.mixer.init()  # Initialize the mixer for playing sounds
        self._start_background_music()

        pygame.joystick.init()  # Initialize joystick support
        self.joystick = None
        self._initialize_joystick()

        self.difficulty = "Easy"  # Default difficulty
        self.difficulty_button = Button(self, f"Difficulty: {self.difficulty}")

    def _initialize_joystick(self):
        """Initialize the first connected joystick."""
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Joystick initialized: {self.joystick.get_name()}")
        else:
            print("No joystick detected.")

    def _initialize_settings_sliders(self):
        """Create sliders for the settings page."""
        self.settings_sliders = []
        slider_width = 250
        slider_height = 20
        slider_x = self.screen_rect.centerx - (slider_width / 2)
        start_y = 150
        y_increment = 50

        self.settings_sliders.append(Slider(self.screen, "Ship Limit", slider_x, start_y, slider_width, slider_height, 1, 10, self.settings.ship_limit))
        self.settings_sliders.append(Slider(self.screen, "Bullets Allowed", slider_x, start_y + y_increment, slider_width, slider_height, 1, 10, self.settings.bullets_allowed))
        self.settings_sliders.append(Slider(self.screen, "Ship Speed", slider_x, start_y + 2 * y_increment, slider_width, slider_height, 0.5, 5.0, self.settings.ship_speed, is_float=True))
        self.settings_sliders.append(Slider(self.screen, "Bullet Speed", slider_x, start_y + 3 * y_increment, slider_width, slider_height, 1.0, 10.0, self.settings.bullet_speed, is_float=True))
        self.settings_sliders.append(Slider(self.screen, "Alien Speed", slider_x, start_y + 4 * y_increment, slider_width, slider_height, 0.1, 3.0, self.settings.alien_speed, is_float=True))
        self.settings_sliders.append(Slider(self.screen, "Fleet Drop Speed", slider_x, start_y + 5 * y_increment, slider_width, slider_height, 5, 50, self.settings.fleet_drop_speed))
        self.settings_sliders.append(Slider(self.screen, "Speedup Scale", slider_x, start_y + 6 * y_increment, slider_width, slider_height, 1.0, 2.0, self.settings.speedup_scale, is_float=True))
        self.settings_sliders.append(Slider(self.screen, "Score Scale", slider_x, start_y + 7 * y_increment, slider_width, slider_height, 1.0, 3.0, self.settings.score_scale, is_float=True))
        self.settings_sliders.append(Slider(self.screen, "Bullet Width", slider_x, start_y + 8 * y_increment, slider_width, slider_height, 1, 10, self.settings.bullet_width))
        self.settings_sliders.append(Slider(self.screen, "Bullet Height", slider_x, start_y + 9 * y_increment, slider_width, slider_height, 5, 30, self.settings.bullet_height))

        self.control_mode = "Keyboard/Mouse"  # Default control mode
        self.control_mode_button = Button(self, f"Control Mode: {self.control_mode}")

    def _start_background_music(self):
        """Start playing the background music."""
        pygame.mixer.music.load(self.background_music)
        pygame.mixer.music.play(-1)  # Loop the music indefinitely

    def _change_background_music(self, new_music_path):
        """Change the background music (admin only)."""
        if self.is_admin:
            try:
                pygame.mixer.music.load(new_music_path)
                pygame.mixer.music.play(-1)
                self.background_music = new_music_path
                print(f"Background music changed to: {new_music_path}")
            except pygame.error as e:
                print(f"Error loading music file: {e}")
        else:
            print("Only admins can change the background music.")

    def _handle_server_commands(self, command):
        """Handle commands sent by the server."""
        if command.startswith("CHANGE_MUSIC:"):
            new_music_path = command.split(":", 1)[1]
            self._change_background_music(new_music_path)
        # ...existing code for handling other commands...

    def run_game(self):
        """Start the main loop for the game."""
        while True:
            self._check_events()

            if self.leaderboard_update_pending:
                print("Leaderboard update detected by main loop, refreshing...")
                self._load_global_leaderboard()
                self.leaderboard_update_pending = False

            if self.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()
            self.clock.tick(60)

    def _check_events(self):
        """Respond to keypresses and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._save_high_scores()
                self.sse_client_running = False
                if self.sse_thread and self.sse_thread.is_alive():
                    try:
                        self.sse_thread.join(timeout=1.0)
                    except RuntimeError:
                        pass
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.settings_page_active:
                        self._apply_slider_settings()
                        self.settings_page_active = False
                        self.title_screen_active = True
                        continue
                    else:
                        self._save_high_scores()
                        self.sse_client_running = False
                        if self.sse_thread and self.sse_thread.is_alive():
                            try:
                                self.sse_thread.join(timeout=1.0)
                            except RuntimeError:
                                pass
                        sys.exit()

            if self.title_screen_active:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self._check_title_screen_buttons(mouse_pos)
            elif self.settings_page_active:
                for slider in self.settings_sliders:
                    slider.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self._check_settings_page_buttons(mouse_pos)
            elif self.username_input_active:
                if event.type == pygame.KEYDOWN:
                    self._handle_username_input(event)
            elif self.game_active:
                if event.type == pygame.KEYDOWN:
                    self._check_keydown_events(event)
                elif event.type == pygame.KEYUP:
                    self._check_keyup_events(event)
                elif event.type == pygame.JOYAXISMOTION or event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                    self._handle_joystick_input(event)
            elif self.login_screen_active:
                self._handle_login_input(event)
            elif self.registration_screen_active:
                self._handle_registration_input(event)
            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self._check_play_button(mouse_pos)

    def _handle_joystick_input(self, event):
        """Handle joystick input for movement and actions."""
        if self.control_mode == "Controller":
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:  # Left stick horizontal
                    if event.value > 0.5:
                        self.ship.moving_right = True
                        self.ship.moving_left = False
                    elif event.value < -0.5:
                        self.ship.moving_left = True
                        self.ship.moving_right = False
                    else:
                        self.ship.moving_right = False
                        self.ship.moving_left = False
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # "A" on Xbox or "Cross" on PlayStation
                    self._fire_bullet()
                elif event.button == 7:  # "Start" button
                    self.game_active = not self.game_active
            elif event.type == pygame.JOYBUTTON_UP:
                if event.button == 0:  # Stop firing when "A" or "Cross" is released
                    pass

    def _check_title_screen_buttons(self, mouse_pos):
        """Check if any title screen buttons were clicked."""
        if self.start_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self.username_input_active = True
            pygame.mouse.set_visible(True)
        elif self.settings_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self.settings_page_active = True
        elif self.exit_button.rect.collidepoint(mouse_pos):
            self._save_high_scores()
            sys.exit()
        elif self.level_code_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self.level_code_input_active = True
        elif self.high_score_mode_button.rect.collidepoint(mouse_pos):
            self.high_score_mode = True
            self.title_screen_active = False
            self.username_input_active = True
        elif self.multiplayer_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self._start_random_match()  # Start random multiplayer match
        elif self.marketplace_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self.marketplace_active = True
        elif self.achievements_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self.achievements_active = True
        elif self.about_us_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self.about_us_active = True
        elif self.contact_us_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self.contact_us_active = True

        # Check if the GitHub link was clicked
        if self.github_link_rect.collidepoint(mouse_pos):
            import webbrowser
            webbrowser.open("https://www.github.com/bentted")

    def _check_settings_page_buttons(self, mouse_pos):
        """Check if any settings page buttons were clicked."""
        if self.back_button.rect.collidepoint(mouse_pos):
            self._apply_slider_settings()
            self.settings_page_active = False
            self.title_screen_active = True
        elif self.control_mode_button.rect.collidepoint(mouse_pos):
            self._toggle_control_mode()
        elif self.difficulty_button.rect.collidepoint(mouse_pos):
            self._toggle_difficulty()

    def _toggle_control_mode(self):
        """Toggle between controller and keyboard/mouse controls."""
        if self.control_mode == "Keyboard/Mouse":
            self.control_mode = "Controller"
        else:
            self.control_mode = "Keyboard/Mouse"
        self.control_mode_button.msg = f"Control Mode: {self.control_mode}"
        self.control_mode_button._prep_msg()

    def _toggle_difficulty(self):
        """Toggle between difficulty levels."""
        if self.difficulty == "Easy":
            self.difficulty = "Hard"
        elif self.difficulty == "Hard":
            self.difficulty = "Impossible"
        else:
            self.difficulty = "Easy"
        self.difficulty_button.msg = f"Difficulty: {self.difficulty}"
        self.difficulty_button._prep_msg()

    def _apply_slider_settings(self):
        """Apply the settings from the sliders."""
        for slider in self.settings_sliders:
            slider.apply_settings()

    def _apply_difficulty_settings(self):
        """Apply settings based on the selected difficulty."""
        if self.difficulty == "Easy":
            self.settings.initialize_dynamic_settings()
        elif self.difficulty == "Hard":
            self.settings.ship_speed *= 10
            self.settings.bullet_speed *= 10
            self.settings.alien_speed *= 10
            self.settings.fleet_drop_speed *= 10
            self.settings.speedup_scale *= 10
            self.settings.score_scale *= 10
        elif self.difficulty == "Impossible":
            self.settings.ship_speed *= 30
            self.settings.bullet_speed *= 30
            self.settings.alien_speed *= 30
            self.settings.fleet_drop_speed *= 30
            self.settings.speedup_scale *= 30
            self.settings.score_scale *= 30

    def _load_user_penalty(self):
        """Load the penalty score for the current user."""
        if not self.username:
            return
        try:
            response = requests.get(f"{self.server_url}/api/penalty", params={"username": self.username}, timeout=5)
            response.raise_for_status()
            self.penalty_per_alien = response.json().get('penalty', 0)
            print(f"Penalty for {self.username}: {self.penalty_per_alien} points per alien.")
        except requests.exceptions.RequestException as e:
            print(f"Error loading penalty for {self.username}: {e}")
            self.penalty_per_alien = 0

    def _load_user_bonus(self):
        """Load the bonus score for the current user."""
        if not self.username:
            return
        try:
            response = requests.get(f"{self.server_url}/api/bonus", params={"username": self.username}, timeout=5)
            response.raise_for_status()
            self.bonus_per_alien = response.json().get('bonus', 0)
            print(f"Bonus for {self.username}: {self.bonus_per_alien} points per alien.")
        except requests.exceptions.RequestException as e:
            print(f"Error loading bonus for {self.username}: {e}")
            self.bonus_per_alien = 0

    def _handle_username_input(self, event):
        """Handle keypresses during username input."""
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            if self.user_input:
                self.username = self.user_input
                self.username_input_active = False
                self.user_input = ""
                self.sb.prep_score()
                self.sb.prep_high_score()
                self.title_screen_active = False
                self.settings_page_active = False
                self.game_active = False
                self._load_user_penalty() 
                self._load_user_bonus()  
        elif event.key == pygame.K_BACKSPACE:
            self.user_input = self.user_input[:-1]
        elif len(self.user_input) < 20:
            self.user_input += event.unicode

    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active and \
           not self.title_screen_active and not self.settings_page_active \
           and not self.username_input_active and self.username and not self.high_score_mode:
            self.settings.initialize_dynamic_settings()
            self._apply_difficulty_settings()  # Apply difficulty settings

            self.stats.reset_stats()
            self.sb.prep_score()
            self.sb.prep_high_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            self.title_screen_active = True
            self.game_active = False
            self.username_input_active = False
            self.bullets.empty()
            self.aliens.empty()

            self._create_fleet()
            self.ship.center_ship()

            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Respond to keypresses."""
        if self.control_mode == "Keyboard/Mouse":
            if event.key == pygame.K_RIGHT:
                self.ship.moving_right = True
            elif event.key == pygame.K_LEFT:
                self.ship.moving_left = True
            elif event.key == pygame.K_q:
                self._save_high_scores()
                sys.exit()
            elif event.key == pygame.K_SPACE:
                self._fire_bullet()

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if self.control_mode == "Keyboard/Mouse":
            if event.key == pygame.K_RIGHT:
                self.ship.moving_right = False
            elif event.key == pygame.K_LEFT:
                self.ship.moving_left = False

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        self.bullets.update()

        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                for alien in aliens:
                    if self.is_multiplayer:
                        self._send_alien_to_opponent(alien)
                base_points = self.settings.alien_points * len(aliens)
                penalty_points = self.penalty_per_alien * len(aliens)
                bonus_points = self.bonus_per_alien * len(aliens)
                self.stats.score += base_points - penalty_points + bonus_points
            self.sb.prep_score()
            self.sb.check_high_score()
            self._check_for_chest_drop()

        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            self.stats.level += 1
            self.sb.prep_level()

    def _check_for_upgrade(self):
        """Randomly grant an upgrade when an alien is killed."""
        drop_rate = 0.1  #
        if self.social_score >= 1000:
            drop_rate = 0.5 

        if random.random() < drop_rate:
            upgrade_type = random.choice(["double_speed", "double_fire_rate", "double_score", "+1_life"])
            print(f"Upgrade granted: {upgrade_type}")
            self._apply_upgrade(upgrade_type)

    def _apply_upgrade(self, upgrade_type):
        """Apply the given upgrade."""
        self.upgrade_active = upgrade_type
        duration = 10000  
        if self.social_score >= 300:
            duration = 60000 

        self.upgrade_timer = pygame.time.get_ticks() + duration 

        if upgrade_type == "double_speed":
            self.settings.ship_speed *= 2
        elif upgrade_type == "double_fire_rate":
            self.settings.bullet_speed *= 2
        elif upgrade_type == "double_score":
            self.settings.score_scale *= 2
        elif upgrade_type == "+1_life":
            self.stats.ships_left += 1
            self.sb.prep_ships()

    def _update_upgrades(self):
        """Update and deactivate upgrades after their duration expires."""
        if self.upgrade_active and pygame.time.get_ticks() > self.upgrade_timer:
            print(f"Upgrade expired: {self.upgrade_active}")
            if self.upgrade_active == "double_speed":
                self.settings.ship_speed /= 2
            elif self.upgrade_active == "double_fire_rate":
                self.settings.bullet_speed /= 2
            elif self.upgrade_active == "double_score":
                self.settings.score_scale /= 2
            self.upgrade_active = None

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        self.screen.blit(self.background_image, (0, 0))  # Draw the current background

        if self.title_screen_active:
            self._draw_title_screen()
        elif self.settings_page_active:
            self._draw_settings_page()
        elif self.username_input_active:
            self._draw_username_input()
        elif self.login_screen_active:
            self._draw_login_screen()
        elif self.registration_screen_active:
            self._draw_registration_screen()
        elif self.report_window_active:
            self._draw_report_window()
        elif self.marketplace_active:
            self._draw_marketplace()
        elif self.achievements_active:
            self._draw_achievements_screen()
        elif self.about_us_active:
            self._draw_about_us_page()
        elif self.contact_us_active:
            self._draw_contact_us_page()
        else:
            self.screen.fill(self.settings.bg_color)

        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)
        self.opponent_aliens.draw(self.screen)

        self.sb.show_score()

        pygame.display.flip()

        self._update_upgrades() 

    def _draw_title_screen(self):
        """Draw the title screen elements."""
        self.screen.fill(self.settings.bg_color)
        
        title_text = "Alien Invasion"
        title_image = self.title_font.render(title_text, True, self.settings.text_color, self.settings.bg_color)
        title_rect = title_image.get_rect()
        title_rect.centerx = self.screen_rect.centerx
        title_rect.top = 100
        self.screen.blit(title_image, title_rect)

        if self.alien_title_image:
            alien_rect = self.alien_title_image.get_rect()
            alien_rect.centerx = self.screen_rect.centerx
            alien_rect.top = title_rect.bottom + 20 
            self.screen.blit(self.alien_title_image, alien_rect)
            current_top = alien_rect.bottom + 50 
        else:
            current_top = title_rect.bottom + 50 

        button_spacing = 20 

        self.start_button.rect.centerx = self.screen_rect.centerx
        self.start_button.rect.top = current_top
        self.start_button.draw_button()

        current_top += self.start_button.rect.height + button_spacing
        self.settings_button.rect.centerx = self.screen_rect.centerx
        self.settings_button.rect.top = current_top
        self.settings_button.draw_button()
        
        current_top += self.settings_button.rect.height + button_spacing
        self.exit_button.rect.centerx = self.screen_rect.centerx
        self.exit_button.rect.top = current_top
        self.exit_button.draw_button()

        current_top += self.exit_button.rect.height + button_spacing
        self.level_code_button.rect.centerx = self.screen_rect.centerx
        self.level_code_button.rect.top = current_top
        self.level_code_button.draw_button()

        current_top += self.level_code_button.rect.height + button_spacing
        self.high_score_mode_button.rect.centerx = self.screen_rect.centerx
        self.high_score_mode_button.rect.top = current_top
        self.high_score_mode_button.draw_button()

        current_top += self.high_score_mode_button.rect.height + button_spacing
        self.multiplayer_button.rect.centerx = self.screen_rect.centerx
        self.multiplayer_button.rect.top = current_top
        self.multiplayer_button.draw_button()

        current_top += self.multiplayer_button.rect.height + button_spacing
        self.marketplace_button.rect.centerx = self.screen_rect.centerx
        self.marketplace_button.rect.top = current_top
        self.marketplace_button.draw_button()

        current_top += self.marketplace_button.rect.height + button_spacing
        self.achievements_button.rect.centerx = self.screen_rect.centerx
        self.achievements_button.rect.top = current_top
        self.achievements_button.draw_button()

        current_top += self.achievements_button.rect.height + button_spacing
        self.about_us_button.rect.centerx = self.screen_rect.centerx
        self.about_us_button.rect.top = current_top
        self.about_us_button.draw_button()

        current_top += self.about_us_button.rect.height + button_spacing
        self.contact_us_button.rect.centerx = self.screen_rect.centerx
        self.contact_us_button.rect.top = current_top
        self.contact_us_button.draw_button()

        leaderboard_title_text = "Global Leaderboard"
        leaderboard_title_image = self.font.render(leaderboard_title_text, True, self.settings.text_color, self.settings.bg_color)
        leaderboard_title_rect = leaderboard_title_image.get_rect()
        leaderboard_title_rect.centerx = self.screen_rect.centerx
        leaderboard_title_rect.top = self.exit_button.rect.bottom + 40
        self.screen.blit(leaderboard_title_image, leaderboard_title_rect)

        leaderboard_y_start = leaderboard_title_rect.bottom + 15
        for i, image in enumerate(self.global_leaderboard_images):
            image_rect = image.get_rect()
            image_rect.centerx = self.screen_rect.centerx
            image_rect.top = leaderboard_y_start + (i * (self.leaderboard_font.get_height() + 5))
            self.screen.blit(image, image_rect)

        # Draw the GitHub link at the bottom of the screen
        link_text = "Visit www.github.com/bentted"
        link_image = self.font.render(link_text, True, (0, 0, 255))  # Blue color for the link
        link_rect = link_image.get_rect()
        link_rect.centerx = self.screen_rect.centerx
        link_rect.bottom = self.screen_rect.bottom - 10
        self.screen.blit(link_image, link_rect)
        self.github_link_rect = link_rect  # Save the rect for click detection

        pygame.mouse.set_visible(True)

    def _draw_settings_page(self):
        """Draw the settings page with sliders."""
        self.screen.fill(self.settings.bg_color)
        
        settings_title_img = self.title_font.render("Settings", True, self.settings.text_color, self.settings.bg_color)
        settings_title_rect = settings_title_img.get_rect()
        settings_title_rect.centerx = self.screen_rect.centerx
        settings_title_rect.top = 50
        self.screen.blit(settings_title_img, settings_title_rect)

        for slider in self.settings_sliders:
            slider.draw()
        
        self.back_button.rect.centerx = self.screen_rect.centerx
        self.back_button.rect.bottom = self.screen_rect.bottom - 30
        self.back_button.draw_button()

        self.control_mode_button.rect.centerx = self.screen_rect.centerx
        self.control_mode_button.rect.top = self.back_button.rect.top - 50
        self.control_mode_button.draw_button()

        self.difficulty_button.rect.centerx = self.screen_rect.centerx
        self.difficulty_button.rect.top = self.control_mode_button.rect.top - 50
        self.difficulty_button.draw_button()
        
        pygame.mouse.set_visible(True)

    def _draw_username_input(self):
        """Draw the username input field on the screen."""
        self.screen.fill(self.settings.bg_color) 
        prompt_text = "Enter Username (Press Enter to Confirm):"
        prompt_image = self.font.render(prompt_text, True, self.settings.text_color, self.settings.bg_color)
        prompt_rect = prompt_image.get_rect()
        prompt_rect.centerx = self.screen_rect.centerx
        prompt_rect.centery = self.screen_rect.centery - 80 

        input_field_width = 300 
        input_field_height = 50
        self.input_field_rect = pygame.Rect(0, 0, input_field_width, input_field_height) 
        self.input_field_rect.centerx = self.screen_rect.centerx
        self.input_field_rect.centery = self.screen_rect.centery - 25 
        
        pygame.draw.rect(self.screen, (230, 230, 230), self.input_field_rect) 
        pygame.draw.rect(self.screen, (0,0,0), self.input_field_rect, 2) 

        input_text_image = self.font.render(self.user_input, True, (0,0,0), (230,230,230)) 
        input_text_rect = input_text_image.get_rect()
        input_text_rect.left = self.input_field_rect.left + 10 
        input_text_rect.centery = self.input_field_rect.centery
        
        self.screen.blit(prompt_image, prompt_rect)
        self.screen.blit(input_text_image, input_text_rect)
        
        pygame.mouse.set_visible(True)

    def _draw_login_screen(self):
        """Draw the login screen."""
        self.screen.fill(self.settings.bg_color)
        font = pygame.font.SysFont(None, 36)

        username_label = font.render("Username:", True, self.settings.text_color)
        username_label_rect = username_label.get_rect()
        username_label_rect.topleft = (100, 150)
        self.screen.blit(username_label, username_label_rect)

        username_input_rect = pygame.Rect(250, 150, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), username_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), username_input_rect, 2)
        username_text = font.render(self.login_username, True, (0, 0, 0))
        self.screen.blit(username_text, (username_input_rect.x + 5, username_input_rect.y + 5))

        password_label = font.render("Password:", True, self.settings.text_color)
        password_label_rect = password_label.get_rect()
        password_label_rect.topleft = (100, 200)
        self.screen.blit(password_label, password_label_rect)

        password_input_rect = pygame.Rect(250, 200, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), password_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), password_input_rect, 2)
        password_text = font.render("*" * len(self.login_password), True, (0, 0, 0))
        self.screen.blit(password_text, (password_input_rect.x + 5, password_input_rect.y + 5))

        login_button = Button(self, "Login")
        login_button.rect.topleft = (250, 250)
        login_button.draw_button()

        register_button = Button(self, "Register")
        register_button.rect.topleft = (250, 300)
        register_button.draw_button()

        pygame.mouse.set_visible(True)

    def _handle_login_input(self, event):
        """Handle input on the login screen."""
        if event.key == pygame.K_TAB:
            pass
        elif event.key == pygame.K_RETURN:
            self._attempt_login()
        elif event.key == pygame.K_BACKSPACE:
            if self.login_password:
                self.login_password = self.login_password[:-1]
            elif self.login_username:
                self.login_username = self.login_username[:-1]
        else:
            if len(self.login_username) < 20:
                self.login_username += event.unicode
            elif len(self.login_password) < 20:
                self.login_password += event.unicode

    def _attempt_login(self):
        """Attempt to log in the user."""
        try:
            payload = {"username": self.login_username, "password": self.login_password}
            response = requests.post(f"{self.server_url}/api/login", json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                print("Login successful!")
                self.username = self.login_username  
                self.login_screen_active = False
                self.title_screen_active = True
            else:
                print("Login failed:", data.get("message"))
        except requests.exceptions.RequestException as e:
            print(f"Error during login: {e}")

    def _draw_registration_screen(self):
        """Draw the registration screen."""
        self.screen.fill(self.settings.bg_color)
        font = pygame.font.SysFont(None, 36)

        username_label = font.render("Username:", True, self.settings.text_color)
        username_label_rect = username_label.get_rect()
        username_label_rect.topleft = (100, 150)
        self.screen.blit(username_label, username_label_rect)

        username_input_rect = pygame.Rect(250, 150, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), username_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), username_input_rect, 2)
        username_text = font.render(self.registration_username, True, (0, 0, 0))
        self.screen.blit(username_text, (username_input_rect.x + 5, username_input_rect.y + 5))

        password_label = font.render("Password:", True, self.settings.text_color)
        password_label_rect = password_label.get_rect()
        password_label_rect.topleft = (100, 200)
        self.screen.blit(password_label, password_label_rect)

        password_input_rect = pygame.Rect(250, 200, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), password_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), password_input_rect, 2)
        password_text = font.render("*" * len(self.registration_password), True, (0, 0, 0))
        self.screen.blit(password_text, (password_input_rect.x + 5, password_input_rect.y + 5))

        confirm_password_label = font.render("Confirm Password:", True, self.settings.text_color)
        confirm_password_label_rect = confirm_password_label.get_rect()
        confirm_password_label_rect.topleft = (100, 250)
        self.screen.blit(confirm_password_label, confirm_password_label_rect)

        confirm_password_input_rect = pygame.Rect(250, 250, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), confirm_password_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), confirm_password_input_rect, 2)
        confirm_password_text = font.render("*" * len(self.registration_confirm_password), True, (0, 0, 0))
        self.screen.blit(confirm_password_text, (confirm_password_input_rect.x + 5, confirm_password_input_rect.y + 5))

        register_button = Button(self, "Register")
        register_button.rect.topleft = (250, 300)
        register_button.draw_button()

        back_button = Button(self, "Back")
        back_button.rect.topleft = (250, 350)
        back_button.draw_button()

        pygame.mouse.set_visible(True)

    def _handle_registration_input(self, event):
        """Handle input on the registration screen."""
        if event.key == pygame.K_TAB:
            pass
        elif event.key == pygame.K_RETURN:
            self._attempt_registration()
        elif event.key == pygame.K_BACKSPACE:
            if self.registration_confirm_password:
                self.registration_confirm_password = self.registration_confirm_password[:-1]
            elif self.registration_password:
                self.registration_password = self.registration_password[:-1]
            elif self.registration_username:
                self.registration_username = self.registration_username[:-1]
        else:
            if len(self.registration_username) < 20:
                self.registration_username += event.unicode
            elif len(self.registration_password) < 20:
                self.registration_password += event.unicode
            elif len(self.registration_confirm_password) < 20:
                self.registration_confirm_password += event.unicode

    def _attempt_registration(self):
        """Attempt to register a new user."""
        if self.registration_password != self.registration_confirm_password:
            print("Passwords do not match!")
            return

        try:
            payload = {"username": self.registration_username, "password": self.registration_password}
            response = requests.post(f"{self.server_url}/api/register", json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                print("Registration successful! You can now log in.")
                self.registration_screen_active = False
                self.login_screen_active = True
            else:
                print("Registration failed:", data.get("message"))
        except requests.exceptions.RequestException as e:
            print(f"Error during registration: {e}")

    def _draw_report_window(self):
        """Draw the report window."""
        if self.report_window_active:
            self.screen.fill(self.settings.bg_color)
            font = pygame.font.SysFont(None, 36)

            title_text = f"Report User: {self.selected_username}"
            title_image = font.render(title_text, True, self.settings.text_color)
            title_rect = title_image.get_rect()
            title_rect.centerx = self.screen_rect.centerx
            title_rect.top = 50
            self.screen.blit(title_image, title_rect)

            topic_font = pygame.font.SysFont(None, 30)
            y_offset = 150
            self.report_topic_rects = []
            for topic in self.report_topics:
                topic_image = topic_font.render(topic, True, self.settings.text_color)
                topic_rect = topic_image.get_rect()
                topic_rect.centerx = self.screen_rect.centerx
                topic_rect.top = y_offset
                self.report_topic_rects.append((topic, topic_rect))
                self.screen.blit(topic_image, topic_rect)
                y_offset += 40

            if self.selected_report_topic:
                details_label = font.render("Details (optional):", True, self.settings.text_color)
                details_label_rect = details_label.get_rect()
                details_label_rect.topleft = (50, y_offset + 20)
                self.screen.blit(details_label, details_label_rect)

                input_box_rect = pygame.Rect(50, y_offset + 60, 500, 30)
                pygame.draw.rect(self.screen, (255, 255, 255), input_box_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), input_box_rect, 2)

                input_text_image = font.render(self.report_details_input, True, (0, 0, 0))
                self.screen.blit(input_text_image, (input_box_rect.left + 5, input_box_rect.top + 5))

                submit_button = Button(self, "Submit")
                submit_button.rect.centerx = self.screen_rect.centerx
                submit_button.rect.top = y_offset + 120
                submit_button.draw_button()

            back_button = Button(self, "Back")
            back_button.rect.centerx = self.screen_rect.centerx
            back_button.rect.top = y_offset + 180
            back_button.draw_button()

    def _handle_report_window_click(self, mouse_pos):
        """Handle clicks in the report window."""
        for topic, rect in self.report_topic_rects:
            if rect.collidepoint(mouse_pos):
                self.selected_report_topic = topic
                self.report_details_active = True  
                return

        if self.selected_report_topic:
            submit_button_rect = pygame.Rect(
                self.screen_rect.centerx - 50, self.report_topic_rects[-1][1].bottom + 120, 100, 30
            )
            if submit_button_rect.collidepoint(mouse_pos):
                self._submit_report()
                self.report_window_active = False
                return
        back_button_rect = pygame.Rect(
            self.screen_rect.centerx - 50, self.report_topic_rects[-1][1].bottom + 180, 100, 30
        )
        if back_button_rect.collidepoint(mouse_pos):
            self.report_window_active = False

    def _handle_report_window_input(self, event):
        """Handle text input for the report details."""
        if self.report_details_active:
            if event.key == pygame.K_RETURN:
                self.report_details_active = False 
            elif event.key == pygame.K_BACKSPACE:
                self.report_details_input = self.report_details_input[:-1]
            elif len(self.report_details_input) < 200:  
                self.report_details_input += event.unicode

    def _submit_report(self):
        """Submit the report for the selected user."""
        try:
            payload = {
                "username": self.selected_username,
                "type": "negative",
                "reporter": self.username,
                "reason": self.selected_report_topic,
                "details": self.report_details_input, 
            }
            response = requests.post(f"{self.server_url}/api/chat/report", json=payload, timeout=5)
            response.raise_for_status()
            print(f"Reported user {self.selected_username}: {response.json().get('message')}")
        except requests.exceptions.RequestException as e:
            print(f"Error reporting user {self.selected_username}: {e}")

    def _start_multiplayer(self, is_host):
        """Start multiplayer mode."""
        self.is_multiplayer = True
        self.is_host = is_host
        if is_host:
            self._start_server()
        else:
            self._connect_to_server()

    def _start_random_match(self):
        """Start the matchmaking process for a random multiplayer match."""
        self.is_multiplayer = True
        self.matchmaking_thread = threading.Thread(target=self._matchmaking_process, daemon=True)
        self.matchmaking_thread.start()

    def _matchmaking_process(self):
        """Handle matchmaking for random multiplayer matches."""
        try:
            self.matchmaking_queue.put(self.username)
            print(f"{self.username} added to matchmaking queue. Waiting for an opponent...")

            while True:
                if self.matchmaking_queue.qsize() >= 2:
                    player1 = self.matchmaking_queue.get()
                    player2 = self.matchmaking_queue.get()

                    if player1 == self.username:
                        self._connect_to_server()
                        print(f"Matched with {player2}. Starting game as client.")
                        break
                    elif player2 == self.username:
                        self._start_server()
                        print(f"Matched with {player1}. Starting game as host.")
                        break
        except Exception as e:
            print(f"Error during matchmaking: {e}")

    def _start_server(self):
        """Start the server for multiplayer."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("192.168.254.14", 5555))  # Host on specified IP and port
        self.server_socket.listen(1)
        print("Waiting for opponent to connect...")
        self.client_socket, _ = self.server_socket.accept()
        print("Opponent connected!")
        self.network_thread = threading.Thread(target=self._handle_network_communication, daemon=True)
        self.network_thread.start()

    def _connect_to_server(self):
        """Connect to the server for multiplayer."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("192.168.254.14", 5555))  # Connect to specified IP and port
        print("Connected to the host!")
        self.network_thread = threading.Thread(target=self._handle_network_communication, daemon=True)
        self.network_thread.start()

    def _handle_network_communication(self):
        """Handle communication between players."""
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if data.startswith("COMMAND:"):
                    command = data.split(":", 1)[1]
                    self._handle_server_commands(command)
                elif data == "GAME_OVER":
                    self._end_multiplayer_game(winner="self")
                elif data.startswith("ALIEN:"):
                    alien_data = json.loads(data[6:])
                    self._add_opponent_alien(alien_data)
            except (ConnectionResetError, ConnectionAbortedError):
                print("Connection lost.")
                self._end_multiplayer_game(winner="self")
                break

    def _send_alien_to_opponent(self, alien):
        """Send alien data to the opponent."""
        if self.client_socket:
            alien_data = {
                "x": alien.rect.x,
                "y": alien.rect.y,
                "speed": alien.speed
            }
            self.client_socket.sendall(f"ALIEN:{json.dumps(alien_data)}".encode())

    def _add_opponent_alien(self, alien_data):
        """Add an alien sent by the opponent."""
        alien = Alien(self)
        alien.rect.x = alien_data["x"]
        alien.rect.y = alien_data["y"]
        alien.speed = alien_data["speed"]
        self.opponent_aliens.add(alien)

    def _update_aliens(self):
        """Update the positions of all aliens."""
        self.aliens.update()
        self.opponent_aliens.update()

        if pygame.sprite.spritecollideany(self.ship, self.aliens) or pygame.sprite.spritecollideany(self.ship, self.opponent_aliens):
            self._ship_hit()

        self._check_aliens_bottom()

    def _check_multiplayer_game_over(self):
        """Check if the multiplayer game is over."""
        if self.stats.ships_left <= 0:
            self._send_game_over_to_opponent()
            self._end_multiplayer_game(winner="opponent")
        elif self.is_host and self._opponent_disconnected():
            self._end_multiplayer_game(winner="self")

    def _send_game_over_to_opponent(self):
        """Notify the opponent that the game is over."""
        if self.client_socket:
            self.client_socket.sendall("GAME_OVER".encode())

    def _opponent_disconnected(self):
        """Check if the opponent has disconnected."""
        try:
            self.client_socket.sendall("PING".encode())
            return False
        except (ConnectionResetError, ConnectionAbortedError):
            return True

    def _end_multiplayer_game(self, winner):
        """Handle the end of a multiplayer game."""
        if winner == "self":
            self.multiplayer_stats["wins"] += 1
            print("You won the multiplayer game!")
            pygame.mixer.music.load(self.win_music)
            pygame.mixer.music.play()
        elif winner == "opponent":
            self.multiplayer_stats["losses"] += 1
            print("You lost the multiplayer game!")
            pygame.mixer.music.load(self.lose_music)
            pygame.mixer.music.play()

        self.is_multiplayer = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()

    def _start_voice_chat(self, is_host):
        """Start the voice chat feature."""
        if not self._is_voice_chat_allowed(self.username):
            print("Voice chat is currently disabled for you.")
            return

        self.voice_chat_enabled = True
        self.voice_chat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.audio_stream = pyaudio.PyAudio().open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            output=True,
            frames_per_buffer=1024
        )

        if is_host:
            self.voice_chat_socket.bind(("0.0.0.0", 6000))
            print("Voice chat server started. Waiting for connection...")
        else:
            self.voice_chat_socket.connect(("127.0.0.1", 6000))
            print("Connected to voice chat server.")

        self.voice_chat_thread = threading.Thread(target=self._handle_voice_chat, daemon=True)
        self.voice_chat_thread.start()

    def _handle_voice_chat(self):
        """Handle sending and receiving audio data."""
        try:
            while self.voice_chat_enabled:
                # Send audio
                audio_data = self.audio_stream.read(1024, exception_on_overflow=False)
                self.voice_chat_socket.sendto(audio_data, ("127.0.0.1", 6000))

                # Receive audio
                data, _ = self.voice_chat_socket.recvfrom(1024)
                self.audio_stream.write(data)
        except Exception as e:
            print(f"Voice chat error: {e}")
        finally:
            self._stop_voice_chat()

    def _stop_voice_chat(self):
        """Stop the voice chat feature."""
        self.voice_chat_enabled = False
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.voice_chat_socket:
            self.voice_chat_socket.close()
        print("Voice chat stopped.")

    def _handle_kick(self, username):
        """Handle a user being kicked from chat."""
        ban_duration_days = 3  # Number of days to disable voice chat
        self.kick_list[username] = datetime.now() + timedelta(days=ban_duration_days)
        print(f"User {username} has been kicked. Voice chat disabled until {self.kick_list[username]}.")

    def _is_voice_chat_allowed(self, username):
        """Check if the user is allowed to use voice chat."""
        if username in self.kick_list and self.kick_list[username] > datetime.now():
            print(f"Voice chat is disabled for {username} until {self.kick_list[username]}.")
            return False
        return True

    def _draw_about_us_page(self):
        """Draw the 'About Us' page."""
        self.screen.fill(self.settings.bg_color)

        title_text = "About Us"
        title_image = self.title_font.render(title_text, True, self.settings.text_color)
        title_rect = title_image.get_rect()
        title_rect.centerx = self.screen_rect.centerx
        title_rect.top = 50
        self.screen.blit(title_image, title_rect)

        about_text = (
            "Wasser Development is a self-taught software engineer.\n"
            "This project has taken about 2 years to reach this point.\n"
            "We are open and willing to accept contributions to this project\n"
            "and any of our other projects at:\n"
            "github.com/bentted"
        )
        lines = about_text.split("\n")
        y_offset = title_rect.bottom + 30
        for line in lines:
            line_image = self.font.render(line, True, self.settings.text_color)
            line_rect = line_image.get_rect()
            line_rect.centerx = self.screen_rect.centerx
            line_rect.top = y_offset
            self.screen.blit(line_image, line_rect)
            y_offset += 40

        back_button = Button(self, "Back")
        back_button.rect.centerx = self.screen_rect.centerx
        back_button.rect.top = y_offset + 50
        back_button.draw_button()
        self.about_us_back_button = back_button

        pygame.mouse.set_visible(True)

    def _draw_contact_us_page(self):
        """Draw the 'Contact Us' page."""
        self.screen.fill(self.settings.bg_color)

        title_text = "Contact Us"
        title_image = self.title_font.render(title_text, True, self.settings.text_color)
        title_rect = title_image.get_rect()
        title_rect.centerx = self.screen_rect.centerx
        title_rect.top = 50
        self.screen.blit(title_image, title_rect)

        github_text = "GitHub: github.com/bentted"
        github_image = self.font.render(github_text, True, (0, 0, 255))  # Blue color for the link
        github_rect = github_image.get_rect()
        github_rect.centerx = self.screen_rect.centerx
        github_rect.top = title_rect.bottom + 30
        self.screen.blit(github_image, github_rect)
        self.github_link_rect = github_rect  # Save the rect for click detection

        tor_text = "Tor Site: http://blkhatjxlrvc5aevqzz5t6kxldayog6jlx5h7glnu44euzongl4fh5ad.onion/index.php-FeuerWasser"
        tor_image = self.font.render(tor_text, True, (0, 0, 255))  # Blue color for the link
        tor_rect = tor_image.get_rect()
        tor_rect.centerx = self.screen_rect.centerx
        tor_rect.top = github_rect.bottom + 20
        self.screen.blit(tor_image, tor_rect)
        self.tor_link_rect = tor_rect  # Save the rect for click detection

        back_button = Button(self, "Back")
        back_button.rect.centerx = self.screen_rect.centerx
        back_button.rect.top = tor_rect.bottom + 50
        back_button.draw_button()
        self.contact_us_back_button = back_button

        pygame.mouse.set_visible(True)

    def _check_contact_us_buttons(self, mouse_pos):
        """Check if any 'Contact Us' page buttons were clicked."""
        if self.github_link_rect.collidepoint(mouse_pos):
            import webbrowser
            webbrowser.open("https://www.github.com/bentted")
        elif self.tor_link_rect.collidepoint(mouse_pos):
            import webbrowser
            webbrowser.open("http://blkhatjxlrvc5aevqzz5t6kxldayog6jlx5h7glnu44euzongl4fh5ad.onion/index.php-FeuerWasser")
        elif self.contact_us_back_button.rect.collidepoint(mouse_pos):
            self.contact_us_active = False
            self.title_screen_active = True

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        self.screen.blit(self.background_image, (0, 0))  # Draw the current background

        if self.title_screen_active:
            self._draw_title_screen()
        elif self.settings_page_active:
            self._draw_settings_page()
        elif self.username_input_active:
            self._draw_username_input()
        elif self.login_screen_active:
            self._draw_login_screen()
        elif self.registration_screen_active:
            self._draw_registration_screen()
        elif self.report_window_active:
            self._draw_report_window()
        elif self.marketplace_active:
            self._draw_marketplace()
        elif self.achievements_active:
            self._draw_achievements_screen()
        elif self.about_us_active:
            self._draw_about_us_page()
        elif self.contact_us_active:
            self._draw_contact_us_page()
        else:
            self.screen.fill(self.settings.bg_color)

        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)
        self.opponent_aliens.draw(self.screen)

        self.sb.show_score()

        pygame.display.flip()

        self._update_upgrades() 

    def _draw_title_screen(self):
        """Draw the title screen elements."""
        self.screen.fill(self.settings.bg_color)
        
        title_text = "Alien Invasion"
        title_image = self.title_font.render(title_text, True, self.settings.text_color, self.settings.bg_color)
        title_rect = title_image.get_rect()
        title_rect.centerx = self.screen_rect.centerx
        title_rect.top = 100
        self.screen.blit(title_image, title_rect)

        if self.alien_title_image:
            alien_rect = self.alien_title_image.get_rect()
            alien_rect.centerx = self.screen_rect.centerx
            alien_rect.top = title_rect.bottom + 20 
            self.screen.blit(self.alien_title_image, alien_rect)
            current_top = alien_rect.bottom + 50 
        else:
            current_top = title_rect.bottom + 50 

        button_spacing = 20 

        self.start_button.rect.centerx = self.screen_rect.centerx
        self.start_button.rect.top = current_top
        self.start_button.draw_button()

        current_top += self.start_button.rect.height + button_spacing
        self.settings_button.rect.centerx = self.screen_rect.centerx
        self.settings_button.rect.top = current_top
        self.settings_button.draw_button()
        
        current_top += self.settings_button.rect.height + button_spacing
        self.exit_button.rect.centerx = self.screen_rect.centerx
        self.exit_button.rect.top = current_top
        self.exit_button.draw_button()

        current_top += self.exit_button.rect.height + button_spacing
        self.level_code_button.rect.centerx = self.screen_rect.centerx
        self.level_code_button.rect.top = current_top
        self.level_code_button.draw_button()

        current_top += self.level_code_button.rect.height + button_spacing
        self.high_score_mode_button.rect.centerx = self.screen_rect.centerx
        self.high_score_mode_button.rect.top = current_top
        self.high_score_mode_button.draw_button()

        current_top += self.high_score_mode_button.rect.height + button_spacing
        self.multiplayer_button.rect.centerx = self.screen_rect.centerx
        self.multiplayer_button.rect.top = current_top
        self.multiplayer_button.draw_button()

        current_top += self.multiplayer_button.rect.height + button_spacing
        self.marketplace_button.rect.centerx = self.screen_rect.centerx
        self.marketplace_button.rect.top = current_top
        self.marketplace_button.draw_button()

        current_top += self.marketplace_button.rect.height + button_spacing
        self.achievements_button.rect.centerx = self.screen_rect.centerx
        self.achievements_button.rect.top = current_top
        self.achievements_button.draw_button()

        current_top += self.achievements_button.rect.height + button_spacing
        self.about_us_button.rect.centerx = self.screen_rect.centerx
        self.about_us_button.rect.top = current_top
        self.about_us_button.draw_button()

        current_top += self.about_us_button.rect.height + button_spacing
        self.contact_us_button.rect.centerx = self.screen_rect.centerx
        self.contact_us_button.rect.top = current_top
        self.contact_us_button.draw_button()

        leaderboard_title_text = "Global Leaderboard"
        leaderboard_title_image = self.font.render(leaderboard_title_text, True, self.settings.text_color, self.settings.bg_color)
        leaderboard_title_rect = leaderboard_title_image.get_rect()
        leaderboard_title_rect.centerx = self.screen_rect.centerx
        leaderboard_title_rect.top = self.exit_button.rect.bottom + 40
        self.screen.blit(leaderboard_title_image, leaderboard_title_rect)

        leaderboard_y_start = leaderboard_title_rect.bottom + 15
        for i, image in enumerate(self.global_leaderboard_images):
            image_rect = image.get_rect()
            image_rect.centerx = self.screen_rect.centerx
            image_rect.top = leaderboard_y_start + (i * (self.leaderboard_font.get_height() + 5))
            self.screen.blit(image, image_rect)

        # Draw the GitHub link at the bottom of the screen
        link_text = "Visit www.github.com/bentted"
        link_image = self.font.render(link_text, True, (0, 0, 255))  # Blue color for the link
        link_rect = link_image.get_rect()
        link_rect.centerx = self.screen_rect.centerx
        link_rect.bottom = self.screen_rect.bottom - 10
        self.screen.blit(link_image, link_rect)
        self.github_link_rect = link_rect  # Save the rect for click detection

        pygame.mouse.set_visible(True)

    def _draw_settings_page(self):
        """Draw the settings page with sliders."""
        self.screen.fill(self.settings.bg_color)
        
        settings_title_img = self.title_font.render("Settings", True, self.settings.text_color, self.settings.bg_color)
        settings_title_rect = settings_title_img.get_rect()
        settings_title_rect.centerx = self.screen_rect.centerx
        settings_title_rect.top = 50
        self.screen.blit(settings_title_img, settings_title_rect)

        for slider in self.settings_sliders:
            slider.draw()
        
        self.back_button.rect.centerx = self.screen_rect.centerx
        self.back_button.rect.bottom = self.screen_rect.bottom - 30
        self.back_button.draw_button()

        self.control_mode_button.rect.centerx = self.screen_rect.centerx
        self.control_mode_button.rect.top = self.back_button.rect.top - 50
        self.control_mode_button.draw_button()

        self.difficulty_button.rect.centerx = self.screen_rect.centerx
        self.difficulty_button.rect.top = self.control_mode_button.rect.top - 50
        self.difficulty_button.draw_button()
        
        pygame.mouse.set_visible(True)

    def _draw_username_input(self):
        """Draw the username input field on the screen."""
        self.screen.fill(self.settings.bg_color) 
        prompt_text = "Enter Username (Press Enter to Confirm):"
        prompt_image = self.font.render(prompt_text, True, self.settings.text_color, self.settings.bg_color)
        prompt_rect = prompt_image.get_rect()
        prompt_rect.centerx = self.screen_rect.centerx
        prompt_rect.centery = self.screen_rect.centery - 80 

        input_field_width = 300 
        input_field_height = 50
        self.input_field_rect = pygame.Rect(0, 0, input_field_width, input_field_height) 
        self.input_field_rect.centerx = self.screen_rect.centerx
        self.input_field_rect.centery = self.screen_rect.centery - 25 
        
        pygame.draw.rect(self.screen, (230, 230, 230), self.input_field_rect) 
        pygame.draw.rect(self.screen, (0,0,0), self.input_field_rect, 2) 

        input_text_image = self.font.render(self.user_input, True, (0,0,0), (230,230,230)) 
        input_text_rect = input_text_image.get_rect()
        input_text_rect.left = self.input_field_rect.left + 10 
        input_text_rect.centery = self.input_field_rect.centery
        
        self.screen.blit(prompt_image, prompt_rect)
        self.screen.blit(input_text_image, input_text_rect)
        
        pygame.mouse.set_visible(True)

    def _draw_login_screen(self):
        """Draw the login screen."""
        self.screen.fill(self.settings.bg_color)
        font = pygame.font.SysFont(None, 36)

        username_label = font.render("Username:", True, self.settings.text_color)
        username_label_rect = username_label.get_rect()
        username_label_rect.topleft = (100, 150)
        self.screen.blit(username_label, username_label_rect)

        username_input_rect = pygame.Rect(250, 150, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), username_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), username_input_rect, 2)
        username_text = font.render(self.login_username, True, (0, 0, 0))
        self.screen.blit(username_text, (username_input_rect.x + 5, username_input_rect.y + 5))

        password_label = font.render("Password:", True, self.settings.text_color)
        password_label_rect = password_label.get_rect()
        password_label_rect.topleft = (100, 200)
        self.screen.blit(password_label, password_label_rect)

        password_input_rect = pygame.Rect(250, 200, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), password_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), password_input_rect, 2)
        password_text = font.render("*" * len(self.login_password), True, (0, 0, 0))
        self.screen.blit(password_text, (password_input_rect.x + 5, password_input_rect.y + 5))

        login_button = Button(self, "Login")
        login_button.rect.topleft = (250, 250)
        login_button.draw_button()

        register_button = Button(self, "Register")
        register_button.rect.topleft = (250, 300)
        register_button.draw_button()

        pygame.mouse.set_visible(True)

    def _handle_login_input(self, event):
        """Handle input on the login screen."""
        if event.key == pygame.K_TAB:
            pass
        elif event.key == pygame.K_RETURN:
            self._attempt_login()
        elif event.key == pygame.K_BACKSPACE:
            if self.login_password:
                self.login_password = self.login_password[:-1]
            elif self.login_username:
                self.login_username = self.login_username[:-1]
        else:
            if len(self.login_username) < 20:
                self.login_username += event.unicode
            elif len(self.login_password) < 20:
                self.login_password += event.unicode

    def _attempt_login(self):
        """Attempt to log in the user."""
        try:
            payload = {"username": self.login_username, "password": self.login_password}
            response = requests.post(f"{self.server_url}/api/login", json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                print("Login successful!")
                self.username = self.login_username  
                self.login_screen_active = False
                self.title_screen_active = True
            else:
                print("Login failed:", data.get("message"))
        except requests.exceptions.RequestException as e:
            print(f"Error during login: {e}")

    def _draw_registration_screen(self):
        """Draw the registration screen."""
        self.screen.fill(self.settings.bg_color)
        font = pygame.font.SysFont(None, 36)

        username_label = font.render("Username:", True, self.settings.text_color)
        username_label_rect = username_label.get_rect()
        username_label_rect.topleft = (100, 150)
        self.screen.blit(username_label, username_label_rect)

        username_input_rect = pygame.Rect(250, 150, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), username_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), username_input_rect, 2)
        username_text = font.render(self.registration_username, True, (0, 0, 0))
        self.screen.blit(username_text, (username_input_rect.x + 5, username_input_rect.y + 5))

        password_label = font.render("Password:", True, self.settings.text_color)
        password_label_rect = password_label.get_rect()
        password_label_rect.topleft = (100, 200)
        self.screen.blit(password_label, password_label_rect)

        password_input_rect = pygame.Rect(250, 200, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), password_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), password_input_rect, 2)
        password_text = font.render("*" * len(self.registration_password), True, (0, 0, 0))
        self.screen.blit(password_text, (password_input_rect.x + 5, password_input_rect.y + 5))

        confirm_password_label = font.render("Confirm Password:", True, self.settings.text_color)
        confirm_password_label_rect = confirm_password_label.get_rect()
        confirm_password_label_rect.topleft = (100, 250)
        self.screen.blit(confirm_password_label, confirm_password_label_rect)

        confirm_password_input_rect = pygame.Rect(250, 250, 200, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), confirm_password_input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), confirm_password_input_rect, 2)
        confirm_password_text = font.render("*" * len(self.registration_confirm_password), True, (0, 0, 0))
        self.screen.blit(confirm_password_text, (confirm_password_input_rect.x + 5, confirm_password_input_rect.y + 5))

        register_button = Button(self, "Register")
        register_button.rect.topleft = (250, 300)
        register_button.draw_button()

        back_button = Button(self, "Back")
        back_button.rect.topleft = (250, 350)
        back_button.draw_button()

        pygame.mouse.set_visible(True)

    def _handle_registration_input(self, event):
        """Handle input on the registration screen."""
        if event.key == pygame.K_TAB:
            pass
        elif event.key == pygame.K_RETURN:
            self._attempt_registration()
        elif event.key == pygame.K_BACKSPACE:
            if self.registration_confirm_password:
                self.registration_confirm_password = self.registration_confirm_password[:-1]
            elif self.registration_password:
                self.registration_password = self.registration_password[:-1]
            elif self.registration_username:
                self.registration_username = self.registration_username[:-1]
        else:
            if len(self.registration_username) < 20:
                self.registration_username += event.unicode
            elif len(self.registration_password) < 20:
                self.registration_password += event.unicode
            elif len(self.registration_confirm_password) < 20:
                self.registration_confirm_password += event.unicode

    def _attempt_registration(self):
        """Attempt to register a new user."""
        if self.registration_password != self.registration_confirm_password:
            print("Passwords do not match!")
            return

        try:
            payload = {"username": self.registration_username, "password": self.registration_password}
            response = requests.post(f"{self.server_url}/api/register", json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                print("Registration successful! You can now log in.")
                self.registration_screen_active = False
                self.login_screen_active = True
            else:
                print("Registration failed:", data.get("message"))
        except requests.exceptions.RequestException as e:
                       print(f"Error during registration: {e}")

    def _draw_report_window(self):
        """Draw the report window."""
        if self.report_window_active:
            self.screen.fill(self.settings.bg_color)
            font = pygame.font.SysFont(None, 36)

            title_text = f"Report User: {self.selected_username}"
            title_image = font.render(title_text, True, self.settings.text_color)
            title_rect = title_image.get_rect()
            title_rect.centerx = self.screen_rect.centerx
            title_rect.top = 50
            self.screen.blit(title_image, title_rect)

            topic_font = pygame.font.SysFont(None, 30)
            y_offset = 150
            self.report_topic_rects = []
            for topic in self.report_topics:
                topic_image = topic_font.render(topic, True, self.settings.text_color)
                topic_rect = topic_image.get_rect()
                topic_rect.centerx = self.screen_rect.centerx
                topic_rect.top = y_offset
                self.report_topic_rects.append((topic, topic_rect))
                self.screen.blit(topic_image, topic_rect)
                y_offset += 40

            if self.selected_report_topic:
                details_label = font.render("Details (optional):", True, self.settings.text_color)
                details_label_rect = details_label.get_rect()
                details_label_rect.topleft = (50, y_offset + 20)
                self.screen.blit(details_label, details_label_rect)

                input_box_rect = pygame.Rect(50, y_offset + 60, 500, 30)
                pygame.draw.rect(self.screen, (255, 255, 255), input_box_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), input_box_rect, 2)

                input_text_image = font.render(self.report_details_input, True, (0, 0, 0))
                self.screen.blit(input_text_image, (input_box_rect.left + 5, input_box_rect.top + 5))

                submit_button = Button(self, "Submit")
                submit_button.rect.centerx = self.screen_rect.centerx
                submit_button.rect.top = y_offset + 120
                submit_button.draw_button()

            back_button = Button(self, "Back")
            back_button.rect.centerx = self.screen_rect.centerx
            back_button.rect.top = y_offset + 180
            back_button.draw_button()

    def _handle_report_window_click(self, mouse_pos):
        """Handle clicks in the report window."""
        for topic, rect in self.report_topic_rects:
            if rect.collidepoint(mouse_pos):
                self.selected_report_topic = topic
                self.report_details_active = True  
                return

        if self.selected_report_topic:
            submit_button_rect = pygame.Rect(
                self.screen_rect.centerx - 50, self.report_topic_rects[-1][1].bottom + 120, 100, 30
            )
            if submit_button_rect.collidepoint(mouse_pos):
                self._submit_report()
                self.report_window_active = False
                return
        back_button_rect = pygame.Rect(
            self.screen_rect.centerx - 50, self.report_topic_rects[-1][1].bottom + 180, 100, 30
        )
        if back_button_rect.collidepoint(mouse_pos):
            self.report_window_active = False

    def _handle_report_window_input(self, event):
        """Handle text input for the report details."""
        if self.report_details_active:
            if event.key == pygame.K_RETURN:
                self.report_details_active = False 
            elif event.key == pygame.K_BACKSPACE:
                self.report_details_input = self.report_details_input[:-1]
            elif len(self.report_details_input) < 200:  
                self.report_details_input += event.unicode

    def _submit_report(self):
        """Submit the report for the selected user."""
        try:
            payload = {
                "username": self.selected_username,
                "type": "negative",
                "reporter": self.username,
                "reason": self.selected_report_topic,
                "details": self.report_details_input, 
            }
            response = requests.post(f"{self.server_url}/api/chat/report", json=payload, timeout=5)
            response.raise_for_status()
            print(f"Reported user {self.selected_username}: {response.json().get('message')}")
        except requests.exceptions.RequestException as e:
            print(f"Error reporting user {self.selected_username}: {e}")

    def _start_multiplayer(self, is_host):
        """Start multiplayer mode."""
        self.is_multiplayer = True
        self.is_host = is_host
        if is_host:
            self._start_server()
        else:
            self._connect_to_server()

    def _start_random_match(self):
        """Start the matchmaking process for a random multiplayer match."""
        self.is_multiplayer = True
        self.matchmaking_thread = threading.Thread(target=self._matchmaking_process, daemon=True)
        self.matchmaking_thread.start()

    def _matchmaking_process(self):
        """Handle matchmaking for random multiplayer matches."""
        try:
            self.matchmaking_queue.put(self.username)
            print(f"{self.username} added to matchmaking queue. Waiting for an opponent...")

            while True:
                if self.matchmaking_queue.qsize() >= 2:
                    player1 = self.matchmaking_queue.get()
                    player2 = self.matchmaking_queue.get()

                    if player1 == self.username:
                        self._connect_to_server()
                        print(f"Matched with {player2}. Starting game as client.")
                        break
                    elif player2 == self.username:
                        self._start_server()
                        print(f"Matched with {player1}. Starting game as host.")
                        break
        except Exception as e:
            print(f"Error during matchmaking: {e}")

    def _start_server(self):
        """Start the server for multiplayer."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("192.168.254.14", 5555))  # Host on specified IP and port
        self.server_socket.listen(1)
        print("Waiting for opponent to connect...")
        self.client_socket, _ = self.server_socket.accept()
        print("Opponent connected!")
        self.network_thread = threading.Thread(target=self._handle_network_communication, daemon=True)
        self.network_thread.start()

    def _connect_to_server(self):
        """Connect to the server for multiplayer."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("192.168.254.14", 5555))  # Connect to specified IP and port
        print("Connected to the host!")
        self.network_thread = threading.Thread(target=self._handle_network_communication, daemon=True)
        self.network_thread.start()

    def _handle_network_communication(self):
        """Handle communication between players."""
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if data.startswith("COMMAND:"):
                    command = data.split(":", 1)[1]
                    self._handle_server_commands(command)
                elif data == "GAME_OVER":
                    self._end_multiplayer_game(winner="self")
                elif data.startswith("ALIEN:"):
                    alien_data = json.loads(data[6:])
                    self._add_opponent_alien(alien_data)
            except (ConnectionResetError, ConnectionAbortedError):
                print("Connection lost.")
                self._end_multiplayer_game(winner="self")
                break

    def _send_alien_to_opponent(self, alien):
        """Send alien data to the opponent."""
        if self.client_socket:
            alien_data = {
                "x": alien.rect.x,
                "y": alien.rect.y,
                "speed": alien.speed
            }
            self.client_socket.sendall(f"ALIEN:{json.dumps(alien_data)}".encode())

    def _add_opponent_alien(self, alien_data):
        """Add an alien sent by the opponent."""
        alien = Alien(self)
        alien.rect.x = alien_data["x"]
        alien.rect.y = alien_data["y"]
        alien.speed = alien_data["speed"]
        self.opponent_aliens.add(alien)

    def _update_aliens(self):
        """Update the positions of all aliens."""
        self.aliens.update()
        self.opponent_aliens.update()

        if pygame.sprite.spritecollideany(self.ship, self.aliens) or pygame.sprite.spritecollideany(self.ship, self.opponent_aliens):
            self._ship_hit()

        self._check_aliens_bottom()

    def _check_multiplayer_game_over(self):
        """Check if the multiplayer game is over."""
        if self.stats.ships_left <= 0:
            self._send_game_over_to_opponent()
            self._end_multiplayer_game(winner="opponent")
        elif self.is_host and self._opponent_disconnected():
            self._end_multiplayer_game(winner="self")

    def _send_game_over_to_opponent(self):
        """Notify the opponent that the game is over."""
        if self.client_socket:
            self.client_socket.sendall("GAME_OVER".encode())

    def _opponent_disconnected(self):
        """Check if the opponent has disconnected."""
        try:
            self.client_socket.sendall("PING".encode())
            return False
        except (ConnectionResetError, ConnectionAbortedError):
            return True

    def _end_multiplayer_game(self, winner):
        """Handle the end of a multiplayer game."""
        if winner == "self":
            self.multiplayer_stats["wins"] += 1
            print("You won the multiplayer game!")
            pygame.mixer.music.load(self.win_music)
            pygame.mixer.music.play()
        elif winner == "opponent":
            self.multiplayer_stats["losses"] += 1
            print("You lost the multiplayer game!")
            pygame.mixer.music.load(self.lose_music)
            pygame.mixer.music.play()

        self.is_multiplayer = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()

    def _start_voice_chat(self, is_host):
        """Start the voice chat feature."""
        if not self._is_voice_chat_allowed(self.username):
            print("Voice chat is currently disabled for you.")
            return

        self.voice_chat_enabled = True
        self.voice_chat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.audio_stream = pyaudio.PyAudio().open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            output=True,
            frames_per_buffer=1024
        )

        if is_host:
            self.voice_chat_socket.bind(("0.0.0.0", 6000))
            print("Voice chat server started. Waiting for connection...")
        else:
            self.voice_chat_socket.connect(("127.0.0.1", 6000))
            print("Connected to voice chat server.")

        self.voice_chat_thread = threading.Thread(target=self._handle_voice_chat, daemon=True)
        self.voice_chat_thread.start()

    def _handle_voice_chat(self):
        """Handle sending and receiving audio data."""
        try:
            while self.voice_chat_enabled:
                # Send audio
                audio_data = self.audio_stream.read(1024, exception_on_overflow=False)
                self.voice_chat_socket.sendto(audio_data, ("127.0.0.1", 6000))

                # Receive audio
                data, _ = self.voice_chat_socket.recvfrom(1024)
                self.audio_stream.write(data)
        except Exception as e:
            print(f"Voice chat error: {e}")
        finally:
            self._stop_voice_chat()

    def _stop_voice_chat(self):
        """Stop the voice chat feature."""
        self.voice_chat_enabled = False
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.voice_chat_socket:
            self.voice_chat_socket.close()
        print("Voice chat stopped.")

    def _handle_kick(self, username):
        """Handle a user being kicked from chat."""
        ban_duration_days = 3  # Number of days to disable voice chat
        self.kick_list[username] = datetime.now() + timedelta(days=ban_duration_days)
        print(f"User {username} has been kicked. Voice chat disabled until {self.kick_list[username]}.")

    def _is_voice_chat_allowed(self, username):
        """Check if the user is allowed to use voice chat."""
        if username in self.kick_list and self.kick_list[username] > datetime.now():
            print(f"Voice chat is disabled for {username} until {self.kick_list[username]}.")
            return False
        return True
