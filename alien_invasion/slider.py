import pygame

class Slider:
    """A class to create and manage a slider widget."""

    def __init__(self, screen, name, x, y, width, height, min_val, max_val, current_val, 
                 slider_color=(200, 200, 200), handle_color=(100, 100, 100), 
                 text_color=(30, 30, 30), font_size=24, is_float=False):
        """Initialize the slider attributes."""
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.name = name
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = float(current_val) if is_float else int(current_val)
        self.is_float = is_float
        
        self.slider_color = slider_color
        self.handle_color = handle_color
        self.text_color = text_color
        self.font = pygame.font.SysFont(None, font_size)

        self.handle_width = 10
        self.handle_height = height + 10 # Make handle slightly taller
        self.handle_rect = pygame.Rect(0, 0, self.handle_width, self.handle_height)
        self.handle_rect.centery = self.rect.centery
        self._update_handle_pos()

        self.dragging = False
        self.value_text = "" # To store the formatted value string

    def _update_handle_pos(self):
        """Update the position of the handle based on the current value."""
        if self.max_val == self.min_val: # Avoid division by zero
            ratio = 0
        else:
            ratio = (self.current_val - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.centerx = self.rect.left + ratio * self.rect.width

    def _update_value_from_mouse(self, mouse_x):
        """Update the current value based on the mouse position."""
        ratio = (mouse_x - self.rect.left) / self.rect.width
        ratio = max(0, min(1, ratio)) # Clamp between 0 and 1
        
        new_val = self.min_val + ratio * (self.max_val - self.min_val)
        
        if self.is_float:
            self.current_val = round(new_val, 2) # Round to 2 decimal places for floats
        else:
            self.current_val = int(round(new_val))
        
        self._update_handle_pos()

    def handle_event(self, event):
        """Handle mouse events for the slider."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.handle_rect.collidepoint(event.pos):
                self.dragging = True
            elif event.button == 1 and self.rect.collidepoint(event.pos):
                # Allow clicking on the slider bar to jump the handle
                self.dragging = True
                self._update_value_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._update_value_from_mouse(event.pos[0])

    def draw(self):
        """Draw the slider on the screen."""
        pygame.draw.rect(self.screen, self.slider_color, self.rect)
        pygame.draw.rect(self.screen, (0,0,0), self.rect, 1) # Border for slider bar

        pygame.draw.rect(self.screen, self.handle_color, self.handle_rect)
        pygame.draw.rect(self.screen, (0,0,0), self.handle_rect, 1) # Border for handle

        name_img = self.font.render(f"{self.name}:", True, self.text_color)
        name_rect = name_img.get_rect()
        name_rect.right = self.rect.left - 10 # 10px padding to the left of slider
        name_rect.centery = self.rect.centery
        self.screen.blit(name_img, name_rect)

        if self.is_float:
            self.value_text = f"{self.current_val:.1f}" # Display floats with 1 decimal place
        else:
            self.value_text = str(self.current_val)
            
        value_img = self.font.render(self.value_text, True, self.text_color)
        value_rect = value_img.get_rect()
        value_rect.left = self.rect.right + 10 # 10px padding to the right of slider
        value_rect.centery = self.rect.centery
        self.screen.blit(value_img, value_rect)

    def get_value(self):
        """Return the current value of the slider."""
        return self.current_val