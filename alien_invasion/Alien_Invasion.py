import sys
from time import sleep
import json # Added for saving/loading high scores (optional future step)

import pygame
import os # Import os

# Get the absolute path of the directory containing this script
# __file__ is the path to the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the current working directory to the script's directory
os.chdir(script_dir)

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from buttons import Button
from ship import Ship
from bullet import Bullet
from alien import Alien
from slider import Slider # Import the Slider class


class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        self.screen_rect = self.screen.get_rect() # Moved and corrected
        pygame.display.set_caption("Alien Invasion")

        # Username and high score attributes (moved earlier)
        self.username = "" 
        self.user_input = ""
        self.high_scores = {} # Stores {username: score}
        self._load_high_scores() # Load scores from a file

        # Create an instance to store game statistics,
        #   and create a scoreboard.
        self.stats = GameStats(self)
        self.sb = Scoreboard(self) # Now username exists when Scoreboard is initialized

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        # Game states (username attributes were here before)
        self.title_screen_active = True
        self.settings_page_active = False
        self.username_input_active = False # Will be True after clicking Start on title screen
        self.game_active = False

        # Make the Play button (for after username input).
        self.play_button = Button(self, "Play")
        
        # Title screen buttons
        self.start_button = Button(self, "Start Game")
        self.settings_button = Button(self, "Settings")
        self.exit_button = Button(self, "Exit")
        
        # Settings page button
        self.back_button = Button(self, "Back")

        # Font for username input and title
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 72)

        # Load alien image for title screen
        try:
            self.alien_title_image = pygame.image.load('images/alien.bmp')
            # Scale it if it's too small or too large for title screen decoration
            self.alien_title_image = pygame.transform.scale(self.alien_title_image, (100, 80)) 
        except pygame.error:
            self.alien_title_image = None # Handle missing image gracefully
        
        self._initialize_settings_sliders()

    def _initialize_settings_sliders(self):
        """Create sliders for the settings page."""
        self.settings_sliders = []
        slider_width = 250
        slider_height = 20
        slider_x = self.screen_rect.centerx - (slider_width / 2) # Centered
        start_y = 150
        y_increment = 50 # Increased spacing for labels

        # Ship Limit Slider
        self.settings_sliders.append(Slider(self.screen, "Ship Limit", slider_x, start_y, slider_width, slider_height, 1, 10, self.settings.ship_limit))
        # Bullets Allowed Slider
        self.settings_sliders.append(Slider(self.screen, "Bullets Allowed", slider_x, start_y + y_increment, slider_width, slider_height, 1, 10, self.settings.bullets_allowed))
        # Ship Speed Slider
        self.settings_sliders.append(Slider(self.screen, "Ship Speed", slider_x, start_y + 2 * y_increment, slider_width, slider_height, 0.5, 5.0, self.settings.ship_speed, is_float=True))
        # Bullet Speed Slider
        self.settings_sliders.append(Slider(self.screen, "Bullet Speed", slider_x, start_y + 3 * y_increment, slider_width, slider_height, 1.0, 10.0, self.settings.bullet_speed, is_float=True))
        # Alien Speed Slider
        self.settings_sliders.append(Slider(self.screen, "Alien Speed", slider_x, start_y + 4 * y_increment, slider_width, slider_height, 0.1, 3.0, self.settings.alien_speed, is_float=True))
        # Fleet Drop Speed Slider
        self.settings_sliders.append(Slider(self.screen, "Fleet Drop Speed", slider_x, start_y + 5 * y_increment, slider_width, slider_height, 5, 50, self.settings.fleet_drop_speed))
        # Speedup Scale Slider
        self.settings_sliders.append(Slider(self.screen, "Speedup Scale", slider_x, start_y + 6 * y_increment, slider_width, slider_height, 1.0, 2.0, self.settings.speedup_scale, is_float=True))
        # Score Scale Slider
        self.settings_sliders.append(Slider(self.screen, "Score Scale", slider_x, start_y + 7 * y_increment, slider_width, slider_height, 1.0, 3.0, self.settings.score_scale, is_float=True))
        # Bullet Width Slider
        self.settings_sliders.append(Slider(self.screen, "Bullet Width", slider_x, start_y + 8 * y_increment, slider_width, slider_height, 1, 10, self.settings.bullet_width))
        # Bullet Height Slider
        self.settings_sliders.append(Slider(self.screen, "Bullet Height", slider_x, start_y + 9 * y_increment, slider_width, slider_height, 5, 30, self.settings.bullet_height))

    def run_game(self):
        """Start the main loop for the game."""
        while True:
            self._check_events()

            # No updates needed if on title or settings screen, only drawing
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
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.settings_page_active:
                        # On settings page, ESC goes back to title screen
                        self._apply_slider_settings()
                        self.settings_page_active = False
                        self.title_screen_active = True
                        continue  # Skip general ESC quit handling
                    else:
                        # For all other states, ESC quits the game
                        self._save_high_scores()
                        sys.exit()
            
            # State-specific event handling
            if self.title_screen_active:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self._check_title_screen_buttons(mouse_pos)
            elif self.settings_page_active:
                # Handle events for sliders first
                for slider in self.settings_sliders:
                    slider.handle_event(event)
                # Then check for button clicks on settings page
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self._check_settings_page_buttons(mouse_pos)
                # ESC for settings page is handled in the KEYDOWN block above
            elif self.username_input_active:
                if event.type == pygame.KEYDOWN:
                    # ESC to quit is handled above, _handle_username_input processes other keys
                    self._handle_username_input(event)
            elif self.game_active:
                if event.type == pygame.KEYDOWN:
                    # ESC to quit is handled above, _check_keydown_events handles 'q' and game keys
                    self._check_keydown_events(event)
                elif event.type == pygame.KEYUP:
                    self._check_keyup_events(event)
            else:  # This is the screen after username input, before Play (original) is clicked
                   # (i.e., not title, not settings, not username_input, not game_active)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self._check_play_button(mouse_pos)

    def _check_title_screen_buttons(self, mouse_pos):
        """Check if any title screen buttons were clicked."""
        if self.start_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self.username_input_active = True
            pygame.mouse.set_visible(True) # Show cursor for username input
        elif self.settings_button.rect.collidepoint(mouse_pos):
            self.title_screen_active = False
            self.settings_page_active = True
        elif self.exit_button.rect.collidepoint(mouse_pos):
            self._save_high_scores()
            sys.exit()

    def _check_settings_page_buttons(self, mouse_pos):
        """Check if any settings page buttons were clicked."""
        if self.back_button.rect.collidepoint(mouse_pos):
            self._apply_slider_settings() # Apply settings before going back
            self.settings_page_active = False
            self.title_screen_active = True
            # Add logic to save settings if they were changed

    def _handle_username_input(self, event):
        """Handle keypresses during username input."""
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            if self.user_input: # Ensure username is not empty
                self.username = self.user_input
                self.username_input_active = False
                self.user_input = "" # Clear input field for next time
                # After username is entered, scoreboard might need to be updated if it shows username
                self.sb.prep_score() # Refresh score display, potentially with username
                self.sb.prep_high_score() # Refresh high score display
        elif event.key == pygame.K_BACKSPACE:
            self.user_input = self.user_input[:-1]
        elif len(self.user_input) < 20: # Limit username length
            self.user_input += event.unicode

    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play (original button)."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        # This button is only active if no other screen is active and game is not active
        if button_clicked and not self.game_active and \
           not self.title_screen_active and not self.settings_page_active \
           and not self.username_input_active and self.username: # Ensure username is entered
            # Reset the game settings.
            self.settings.initialize_dynamic_settings()

            # Reset the game statistics.
            self.stats.reset_stats()
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()
            self.game_active = True

            # Get rid of any remaining bullets and aliens.
            self.bullets.empty()
            self.aliens.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # Hide the mouse cursor.
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Respond to keypresses."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            self._save_high_scores() # Ensure scores are saved before exiting
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
        # Update bullet positions.
        self.bullets.update()

        # Get rid of bullets that have disappeared.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # Remove any bullets and aliens that have collided.
        collisions = pygame.sprite.groupcollide(
                self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            # Destroy existing bullets and create new fleet.
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # Increase level.
            self.stats.level += 1
            self.sb.prep_level()

    def _update_aliens(self):
        """
        Check if the fleet is at an edge,
          then update the positions of all aliens in the fleet.
        """
        self._check_fleet_edges()
        self.aliens.update()

        # Look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # Look for aliens hitting the bottom of the screen.
        self._check_aliens_bottom()

    def _ship_hit(self):
        """Respond to the ship being hit by an alien."""
        if self.stats.ships_left > 0:
            # Decrement ships_left, and update scoreboard.
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            # Get rid of any remaining bullets and aliens.
            self.bullets.empty()
            self.aliens.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # Pause.
            sleep(0.5)
        else:
            self.game_active = False
            pygame.mouse.set_visible(True)
            # Save score
            if self.username: # Ensure there's a username
                current_high_score = self.high_scores.get(self.username, 0)
                if self.stats.score > current_high_score:
                    self.high_scores[self.username] = self.stats.score
                # Update overall high score for display if necessary
                if self.stats.score > self.stats.high_score:
                    self.stats.high_score = self.stats.score # This updates the general high score
                    self.sb.prep_high_score() # Update display
                # self._save_high_scores() # Optional: save to file immediately
            
            # Reset for next username input
            self.username_input_active = True
            # self.username = "" # Keep username or clear? For now, keep for convenience if playing again.
            self.user_input = ""
            # After game over, return to title screen instead of username input directly
            self.title_screen_active = True
            self.game_active = False # Ensure game_active is false
            self.username_input_active = False # Ensure this is false too


    def _create_fleet(self):
        """Create the fleet of aliens."""
        # Create an alien and keep adding aliens until there's no room left.
        # Spacing between aliens is one alien width and one alien height.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height - 3 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x, current_y)
                current_x += 2 * alien_width

            # Finished a row; reset x value, and increment y value.
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
                # Treat this the same as if the ship got hit.
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
                # Ensure stats.high_score is updated with the loaded global high score
                if self.high_scores:
                    # Find the overall highest score from the loaded dictionary
                    # This assumes self.stats.high_score should reflect the highest score ever,
                    # not just the current user's. If it's per user, this logic changes.
                    # For now, let's assume it's the global highest.
                    # This might be better handled when sb.prep_high_score() is called.
                    # Let's ensure GameStats initializes high_score from loaded data if needed.
                    # For simplicity, we can update stats.high_score when a new high score is made
                    # or when loading. Scoreboard will use stats.high_score.
                    # Let's find the max score from the loaded dictionary to set the initial overall high score.
                    # This is a bit simplistic as GameStats also tries to load 'high_score.txt'
                    # We should consolidate high score loading.
                    # For now, we'll leave GameStats to manage its own high_score.txt loading.
                    # and self.high_scores is for {user: score}.
                    # The scoreboard will show self.stats.high_score.
                    # When a user gets a new score, we update self.high_scores[user]
                    # AND self.stats.high_score if it's a new global high.
                    pass # GameStats handles its own high_score.txt loading.
        except FileNotFoundError:
            pass
        except json.JSONDecodeError: # Handle empty or corrupted file
            self.high_scores = {}


    def _draw_title_screen(self):
        """Draw the title screen elements."""
        self.screen.fill(self.settings.bg_color)
        
        # Title
        title_text = "Alien Invasion"
        title_image = self.title_font.render(title_text, True, self.settings.text_color, self.settings.bg_color)
        title_rect = title_image.get_rect()
        title_rect.centerx = self.screen_rect.centerx
        title_rect.top = 100
        self.screen.blit(title_image, title_rect)

        # Alien Image
        if self.alien_title_image:
            alien_rect = self.alien_title_image.get_rect()
            alien_rect.centerx = self.screen_rect.centerx
            alien_rect.top = title_rect.bottom + 20 # Position alien below title
            self.screen.blit(self.alien_title_image, alien_rect)
            current_top = alien_rect.bottom + 50 # Start buttons below alien image
        else:
            current_top = title_rect.bottom + 50 # Start buttons below title if no image

        # Buttons - Vertically stacked and centered
        button_spacing = 20 # Vertical space between buttons

        # Start Game Button (already labeled "Start Game")
        self.start_button.rect.centerx = self.screen_rect.centerx
        self.start_button.rect.top = current_top
        self.start_button.draw_button()

        # Settings Button (already labeled "Settings")
        current_top += self.start_button.rect.height + button_spacing
        self.settings_button.rect.centerx = self.screen_rect.centerx
        self.settings_button.rect.top = current_top
        self.settings_button.draw_button()
        
        # Exit Button (already labeled "Exit")
        current_top += self.settings_button.rect.height + button_spacing
        self.exit_button.rect.centerx = self.screen_rect.centerx
        self.exit_button.rect.top = current_top
        self.exit_button.draw_button()
        
        pygame.mouse.set_visible(True)


    def _draw_settings_page(self):
        """Draw the settings page with sliders."""
        self.screen.fill(self.settings.bg_color)
        
        # Settings Title
        settings_title_img = self.title_font.render("Settings", True, self.settings.text_color, self.settings.bg_color)
        settings_title_rect = settings_title_img.get_rect()
        settings_title_rect.centerx = self.screen_rect.centerx
        settings_title_rect.top = 50
        self.screen.blit(settings_title_img, settings_title_rect)

        # Draw all sliders
        for slider in self.settings_sliders:
            slider.draw()
        
        # Position Back button at the bottom
        self.back_button.rect.centerx = self.screen_rect.centerx
        self.back_button.rect.bottom = self.screen_rect.bottom - 30
        self.back_button.draw_button()
        
        pygame.mouse.set_visible(True)


    def _draw_username_input(self):
        """Draw the username input field on the screen."""
        self.screen.fill(self.settings.bg_color) # Clear screen for this state
        prompt_text = "Enter Username (Press Enter to Confirm):"
        prompt_image = self.font.render(prompt_text, True, self.settings.text_color, self.settings.bg_color)
        prompt_rect = prompt_image.get_rect()
        prompt_rect.centerx = self.screen_rect.centerx
        prompt_rect.centery = self.screen_rect.centery - 80 # Move prompt up

        # Define the visual input field box
        input_field_width = 300 # Wider to accommodate text, user asked for 100px visual
        input_field_height = 50
        self.input_field_rect = pygame.Rect(0, 0, input_field_width, input_field_height) # Store as attribute
        self.input_field_rect.centerx = self.screen_rect.centerx
        self.input_field_rect.centery = self.screen_rect.centery - 25 # Position below prompt
        
        # Draw the visual box for the input field
        pygame.draw.rect(self.screen, (230, 230, 230), self.input_field_rect) # Light gray box
        pygame.draw.rect(self.screen, (0,0,0), self.input_field_rect, 2) # Black border

        # Render and position the actual user input text
        input_text_image = self.font.render(self.user_input, True, (0,0,0), (230,230,230)) # Black text on light gray
        input_text_rect = input_text_image.get_rect()
        # Position text slightly inside the left of the input_field_rect
        input_text_rect.left = self.input_field_rect.left + 10 
        input_text_rect.centery = self.input_field_rect.centery
        
        self.screen.blit(prompt_image, prompt_rect)
        self.screen.blit(input_text_image, input_text_rect)
        
        pygame.mouse.set_visible(True)


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
            # Draw game elements only if username input is done and game is active
            for bullet in self.bullets.sprites():
                bullet.draw_bullet()
            self.ship.blitme()
            self.aliens.draw(self.screen)
            self.sb.show_score()
            # Mouse should be hidden during gameplay (set in _check_play_button)
        else: # Not game_active, not title, not settings, not username input
              # This is the state after username is entered, before Play is clicked
            if self.username: # Only show Play button if a username has been entered
                self.sb.show_score() # Show score/high score even on this screen
                self.play_button.draw_button()
            else: # Should not happen if flow is correct, but as a fallback:
                # This could be a state where username was cleared or not entered
                # Re-direct to username input or title screen might be an option
                self._draw_username_input() # Or self.title_screen_active = True

        pygame.display.flip()


if __name__ == '__main__':
    # Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()