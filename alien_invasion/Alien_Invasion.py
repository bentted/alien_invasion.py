import sys
from time import sleep, time
import json
import requests
from stem.control import Controller  # Add Stem for Tor control
import pygame
import os
import threading

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
        self.server_url = "http://127.0.0.1:5000"  # Default server URL
        self.use_tor = False  # Flag to determine if Tor should be used
        self.tor_proxy = "socks5h://127.0.0.1:9050"  # Default Tor proxy address

        self.sse_client_running = False
        self.leaderboard_update_pending = False
        self.sse_thread = None

        self.level_codes = {}  # Store level codes
        self.high_score_mode = False  # Flag to track if high score mode is active

        self.chat_messages = []  # Store chat messages
        self.chat_input_active = False
        self.chat_user_input = ""
        self.chat_update_pending = False
        self.chat_thread = threading.Thread(target=self._listen_for_chat_updates, daemon=True)
        self.chat_thread.start()

        self._load_global_leaderboard()
        self._start_sse_listener()

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
            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self._check_play_button(mouse_pos)

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

    def _check_settings_page_buttons(self, mouse_pos):
        """Check if any settings page buttons were clicked."""
        if self.back_button.rect.collidepoint(mouse_pos):
            self._apply_slider_settings()
            self.settings_page_active = False
            self.title_screen_active = True

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
        elif event.key == pygame.K_BACKSPACE:
            self.user_input = self.user_input[:-1]
        elif len(self.user_input) < 20:
            self.user_input += event.unicode

    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play (original button)."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active and \
           not self.title_screen_active and not self.settings_page_active \
           and not self.username_input_active and self.username:
            self.settings.initialize_dynamic_settings()

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
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            self.stats.level += 1
            self.sb.prep_level()  # Update the level display

            if not self.high_score_mode:  # Only display level codes if not in high score mode
                level_code = self._generate_level_code(self.stats.level)
                print(f"Level {self.stats.level} completed! Your level code is: {level_code}")

    def _update_aliens(self):
        """Check if the fleet is at an edge, then update the positions of all aliens in the fleet."""
        self._check_fleet_edges()
        self.aliens.update()

        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        self._check_aliens_bottom()

    def _ship_hit(self):
        """Respond to the ship being hit by an alien."""
        if self.stats.ships_left > 0:
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            self.bullets.empty()
            self.aliens.empty()

            self._create_fleet()
            self.ship.center_ship()

            sleep(0.5)
        else:
            self.game_active = False
            pygame.mouse.set_visible(True)
            if self.username:
                current_high_score = self.high_scores.get(self.username, 0)
                if self.stats.score > current_high_score:
                    self.high_scores[self.username] = self.stats.score
                if self.stats.score > self.stats.high_score:
                    self.stats.high_score = self.stats.score
                    self.sb.prep_high_score()

                self._submit_score_to_global_leaderboard(self.username, self.stats.score)

            self.user_input = ""
            self.title_screen_active = True
            self.username_input_active = False
            self._load_global_leaderboard()

    def _create_fleet(self):
        """Create the fleet of aliens."""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height - 3 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x, current_y)
                current_x += 2 * alien_width

            current_x = alien_width
            current_y += 2 * alien_height

    def _create_alien(self, x_position, y_position):
        """Create an alien and place it in the fleet."""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break

    def _save_high_scores(self):
        """Save high scores to a file."""
        filename = 'high_scores.json'
        with open(filename, 'w') as f:
            json.dump(self.high_scores, f)

    def _load_high_scores(self):
        """Load high scores from a file."""
        filename = 'high_scores.json'
        try:
            with open(filename) as f:
                self.high_scores = json.load(f)
                if self.high_scores:
                    pass
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            self.high_scores = {}

    def _load_global_leaderboard(self):
        """Load global leaderboard data from the server."""
        try:
            response = requests.get(f"{self.server_url}/api/leaderboard", timeout=5)
            response.raise_for_status()  
            self.global_leaderboard_data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error loading global leaderboard: {e}")
            self.global_leaderboard_data = [] 
        except json.JSONDecodeError:
            print("Error: Could not decode JSON from leaderboard server.")
            self.global_leaderboard_data = []

        self._prepare_leaderboard_images()

    def _prepare_leaderboard_images(self):
        """Create rendered text images for the global leaderboard."""
        self.global_leaderboard_images = []
        display_data = self.global_leaderboard_data[:self.max_leaderboard_entries]
        for i, entry in enumerate(display_data):
            username = entry.get('username', 'Unknown')
            score = entry.get('score', 0)
            text = f"{i + 1}. {username}: {score:,}"
            image = self.leaderboard_font.render(text, True, self.settings.text_color, self.settings.bg_color)
            self.global_leaderboard_images.append(image)

    def _submit_score_to_global_leaderboard(self, username, score):
        """Submit score to the global leaderboard server."""
        try:
            payload = {"username": username, "score": score}
            response = requests.post(f"{self.server_url}/api/scores", json=payload, timeout=5)
            response.raise_for_status()
            print(f"Score submission response: {response.json().get('message')}")
        except requests.exceptions.RequestException as e:
            print(f"Error submitting score to global leaderboard: {e}")

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

    def _start_sse_listener(self):
        """Starts the SSE client in a separate thread."""
        if not self.sse_client_running and (self.sse_thread is None or not self.sse_thread.is_alive()): 
            self.sse_client_running = True
            self.leaderboard_update_pending = False 
            self.sse_thread = threading.Thread(target=self._listen_for_leaderboard_updates, daemon=True)
            self.sse_thread.start()
            print("SSE listener thread started.")
        elif self.sse_thread and not self.sse_thread.is_alive():
            print("SSE thread was not alive. Attempting to restart.")
            self.sse_client_running = True 
            self.leaderboard_update_pending = False
            self.sse_thread = threading.Thread(target=self._listen_for_leaderboard_updates, daemon=True)
            self.sse_thread.start()

    def _listen_for_leaderboard_updates(self):
        """Listens for SSE messages from the server."""
        stream_url = f"{self.server_url}/stream"
        print(f"SSE client: Connecting to {stream_url}...")
        
        while self.sse_client_running:
            try:
                with requests.get(stream_url, stream=True, timeout=(5.0, 15.0)) as response: 
                    response.raise_for_status() 
                    print(f"SSE client: Connected to {stream_url}. Waiting for messages...")
                    for line in response.iter_lines(): 
                        if not self.sse_client_running: 
                            print("SSE client: sse_client_running is false, breaking inner loop.")
                            break
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data:'):
                                try:
                                    message_data = decoded_line[len('data:'):].strip()
                                    if not message_data: 
                                        continue
                                    message = json.loads(message_data)
                                    print(f"SSE client: Message received: {message}")
                                    if message.get("type") == "leaderboard_update":
                                        print("SSE client: Leaderboard update message received. Setting pending flag.")
                                        self.leaderboard_update_pending = True
                                    elif message.get("type") == "connection_ack":
                                        print(f"SSE client: Connection Acknowledged: {message.get('message')}")
                                except json.JSONDecodeError:
                                    print(f"SSE client: Could not decode JSON: '{message_data}' from line '{decoded_line}'")
                                except Exception as e_json:
                                    print(f"SSE client: Error processing message data '{message_data}': {e_json}")
                    
                    if not self.sse_client_running:
                        print("SSE client: sse_client_running is false, exiting after iter_lines.")
                        break 
                    else:
                        print("SSE client: Stream ended. Will attempt to reconnect if client is still running.")

            except requests.exceptions.ConnectionError as e_conn:
                if self.sse_client_running:
                    print(f"SSE client: Connection failed: {e_conn}. Retrying in 5 seconds...")
            except requests.exceptions.Timeout as e_timeout:
                if self.sse_client_running:
                    print(f"SSE client: Connection timed out: {e_timeout}. Retrying in 5 seconds...")
            except requests.exceptions.RequestException as e_req:
                if self.sse_client_running: 
                    print(f"SSE client: Request error: {e_req}. Retrying in 5 seconds...")
            except Exception as e_generic: 
                if self.sse_client_running:
                    print(f"SSE client: Unexpected error in listener: {e_generic}. Retrying in 10 seconds...")
            
            if self.sse_client_running: 
                time.sleep(5) 
            else:
                break 

        print("SSE listener thread finished.")

    def _listen_for_chat_updates(self):
        """Listen for chat messages from the server."""
        stream_url = f"{self.server_url}/stream"
        print(f"Chat client: Connecting to {stream_url} for chat updates...")
        while True:
            try:
                with requests.get(stream_url, stream=True, timeout=(5.0, 15.0)) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data:'):
                                try:
                                    message_data = decoded_line[len('data:'):].strip()
                                    if not message_data:
                                        continue
                                    message = json.loads(message_data)
                                    if message.get("type") == "chat_message":
                                        self.chat_messages.append(f"{message['username']}: {message['message']}")
                                        if len(self.chat_messages) > 50:  # Limit chat history
                                            self.chat_messages.pop(0)
                                        self.chat_update_pending = True
                                except json.JSONDecodeError:
                                    print(f"Chat client: Could not decode JSON: '{decoded_line}'")
            except requests.exceptions.RequestException as e:
                print(f"Chat client: Connection error: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def _send_chat_message(self, message):
        """Send a chat message to the server."""
        if not self.username:
            print("Chat client: Cannot send message without a username.")
            return
        try:
            payload = {"username": self.username, "message": message}
            response = requests.post(f"{self.server_url}/api/chat", json=payload, timeout=5)
            response.raise_for_status()
            print("Chat client: Message sent successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Chat client: Error sending message: {e}")

    def _draw_chat_window(self):
        """Draw the chat window on the screen."""
        chat_window_width = 400
        chat_window_height = 300
        chat_window_rect = pygame.Rect(
            self.screen_rect.right - chat_window_width - 20,
            self.screen_rect.bottom - chat_window_height - 20,
            chat_window_width,
            chat_window_height
        )
        pygame.draw.rect(self.screen, (50, 50, 50), chat_window_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), chat_window_rect, 2)

        font = pygame.font.SysFont(None, 24)
        y_offset = chat_window_rect.top + 10
        for message in self.chat_messages[-10:]:  # Display the last 10 messages
            message_image = font.render(message, True, (255, 255, 255))
            self.screen.blit(message_image, (chat_window_rect.left + 10, y_offset))
            y_offset += font.get_height() + 5

        input_rect = pygame.Rect(
            chat_window_rect.left + 10,
            chat_window_rect.bottom - 40,
            chat_window_width - 20,
            30
        )
        pygame.draw.rect(self.screen, (255, 255, 255), input_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), input_rect, 2)

        input_text_image = font.render(self.chat_user_input, True, (0, 0, 0))
        self.screen.blit(input_text_image, (input_rect.left + 5, input_rect.top + 5))

    def _handle_chat_input(self, event):
        """Handle chat input events."""
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            if self.chat_user_input:
                self._send_chat_message(self.chat_user_input)
                self.chat_user_input = ""
        elif event.key == pygame.K_BACKSPACE:
            self.chat_user_input = self.chat_user_input[:-1]
        elif len(self.chat_user_input) < 100:
            self.chat_user_input += event.unicode

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        self.screen.fill(self.settings.bg_color)
        
        if self.title_screen_active:
            self._draw_title_screen()
        elif self.settings_page_active:
            self._draw_settings_page()
        elif self.username_input_active:
            self._draw_username_input()
        elif self.game_active:
            for bullet in self.bullets.sprites():
                bullet.draw_bullet()
            self.ship.blitme()
            self.aliens.draw(self.screen)
            self.sb.show_score()
        else: 
            if self.username: 
                self.sb.show_score() 
                self.play_button.draw_button()
            else: 
                self._draw_username_input() 

        if self.chat_update_pending:
            self.chat_update_pending = False

        self._draw_chat_window()
        pygame.display.flip()


if __name__ == '__main__':
    ai = AlienInvasion()
    ai.run_game()