import pygame
import pygame.font
import pygame.gfxdraw
import math
from typing import Tuple, List, Callable, Optional, Any
from enum import Enum

# Initialize pygame
pygame.init()

# Color constants
class Colors:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)
    LIGHT_GRAY = (200, 200, 200)
    DARK_GRAY = (64, 64, 64)
    BLUE = (70, 130, 180)
    LIGHT_BLUE = (173, 216, 230)
    GREEN = (60, 179, 113)
    RED = (220, 20, 60)
    ORANGE = (255, 140, 0)
    YELLOW = (255, 255, 0)

class GUIComponent:
    """Base class for all GUI components"""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = True
        self.enabled = True
        self.hover = False
        self.clicked = False
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events. Returns True if event was consumed."""
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.clicked = True
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.clicked:
                self.clicked = False
                if self.rect.collidepoint(event.pos):
                    self.on_click()
                    return True
                    
        return False
    
    def on_click(self):
        """Override in subclasses to handle click events"""
        pass
    
    def update(self, dt: float):
        """Update component state. Override in subclasses if needed."""
        pass
    
    def draw(self, surface: pygame.Surface):
        """Draw the component. Must be implemented by subclasses."""
        raise NotImplementedError

class TextButton(GUIComponent):
    """A clickable text button with hover effects"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 font_size: int = 16, callback: Optional[Callable] = None):
        super().__init__(x, y, width, height)
        self.text = text
        self.callback = callback
        self.font = pygame.font.Font(None, font_size)
        
        # Colors
        self.bg_color = Colors.LIGHT_GRAY
        self.hover_color = Colors.BLUE
        self.text_color = Colors.BLACK
        self.border_color = Colors.DARK_GRAY
        
    def on_click(self):
        if self.callback:
            self.callback()
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
            
        # Choose background color based on state
        bg_color = self.hover_color if self.hover else self.bg_color
        if self.clicked:
            bg_color = tuple(max(0, c - 30) for c in bg_color)
        
        # Draw button background
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

class ImageButton(GUIComponent):
    """A clickable button with an image"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 image_path: str, callback: Optional[Callable] = None):
        super().__init__(x, y, width, height)
        self.callback = callback
        
        try:
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (width - 4, height - 4))
        except pygame.error:
            # Create a placeholder if image can't be loaded
            self.image = pygame.Surface((width - 4, height - 4))
            self.image.fill(Colors.GRAY)
        
        self.border_color = Colors.DARK_GRAY
        self.hover_color = Colors.LIGHT_BLUE
    
    def on_click(self):
        if self.callback:
            self.callback()
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
            
        # Draw background with hover effect
        if self.hover:
            pygame.draw.rect(surface, self.hover_color, self.rect)
        
        # Draw border
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        # Draw image
        image_rect = self.image.get_rect(center=self.rect.center)
        surface.blit(self.image, image_rect)

class DropdownMenu(GUIComponent):
    """A dropdown menu for selecting from a list of options"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 options: List[str], font_size: int = 16, 
                 callback: Optional[Callable[[str], None]] = None):
        super().__init__(x, y, width, height)
        self.options = options
        self.selected_index = 0
        self.expanded = False
        self.callback = callback
        self.font = pygame.font.Font(None, font_size)
        
        # Calculate expanded height
        self.item_height = height
        self.expanded_height = self.item_height * len(options)
        
        # Colors
        self.bg_color = Colors.WHITE
        self.border_color = Colors.DARK_GRAY
        self.hover_color = Colors.LIGHT_BLUE
        self.text_color = Colors.BLACK
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
                return True
            elif self.expanded:
                # Check if clicking on an expanded option
                expanded_rect = pygame.Rect(self.rect.x, self.rect.y, 
                                          self.rect.width, self.expanded_height)
                if expanded_rect.collidepoint(event.pos):
                    # Calculate which option was clicked
                    relative_y = event.pos[1] - self.rect.y
                    clicked_index = relative_y // self.item_height
                    if 0 <= clicked_index < len(self.options):
                        self.selected_index = clicked_index
                        self.expanded = False
                        if self.callback:
                            self.callback(self.options[self.selected_index])
                        return True
                else:
                    self.expanded = False
        
        return False
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # Draw main button
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        # Draw selected text
        if self.options:
            text = self.options[self.selected_index]
            text_surface = self.font.render(text, True, self.text_color)
            text_rect = text_surface.get_rect(midleft=(self.rect.x + 5, self.rect.centery))
            surface.blit(text_surface, text_rect)
        
        # Draw dropdown arrow
        arrow_points = [
            (self.rect.right - 15, self.rect.centery - 3),
            (self.rect.right - 5, self.rect.centery - 3),
            (self.rect.right - 10, self.rect.centery + 3)
        ]
        pygame.draw.polygon(surface, self.text_color, arrow_points)
        
        # Draw expanded options
        if self.expanded:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + i * self.item_height,
                                        self.rect.width, self.item_height)
                
                # Highlight hovered option
                mouse_pos = pygame.mouse.get_pos()
                if option_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(surface, self.hover_color, option_rect)
                else:
                    pygame.draw.rect(surface, self.bg_color, option_rect)
                
                pygame.draw.rect(surface, self.border_color, option_rect, 1)
                
                # Draw option text
                text_surface = self.font.render(option, True, self.text_color)
                text_rect = text_surface.get_rect(midleft=(option_rect.x + 5, option_rect.centery))
                surface.blit(text_surface, text_rect)

class Slider(GUIComponent):
    """A slider for selecting numeric values"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 min_value: float = 0.0, max_value: float = 1.0, 
                 initial_value: float = 0.5, callback: Optional[Callable[[float], None]] = None):
        super().__init__(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.callback = callback
        self.dragging = False
        
        # Colors
        self.track_color = Colors.LIGHT_GRAY
        self.handle_color = Colors.BLUE
        self.handle_hover_color = Colors.LIGHT_BLUE
        
        # Handle dimensions
        self.handle_width = 20
        self.handle_height = height
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_x = self._get_handle_x()
            handle_rect = pygame.Rect(handle_x, self.rect.y, 
                                    self.handle_width, self.handle_height)
            if handle_rect.collidepoint(event.pos):
                self.dragging = True
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Update value based on mouse position
            relative_x = event.pos[0] - self.rect.x - self.handle_width // 2
            track_width = self.rect.width - self.handle_width
            relative_x = max(0, min(track_width, relative_x))
            
            self.value = self.min_value + (relative_x / track_width) * (self.max_value - self.min_value)
            
            if self.callback:
                self.callback(self.value)
            return True
        
        elif event.type == pygame.MOUSEMOTION:
            handle_x = self._get_handle_x()
            handle_rect = pygame.Rect(handle_x, self.rect.y, 
                                    self.handle_width, self.handle_height)
            self.hover = handle_rect.collidepoint(event.pos)
        
        return False
    
    def _get_handle_x(self) -> int:
        """Get the x position of the handle based on current value"""
        track_width = self.rect.width - self.handle_width
        relative_value = (self.value - self.min_value) / (self.max_value - self.min_value)
        return self.rect.x + int(relative_value * track_width)
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # Draw track
        track_rect = pygame.Rect(self.rect.x, self.rect.centery - 2, 
                               self.rect.width, 4)
        pygame.draw.rect(surface, self.track_color, track_rect)
        pygame.draw.rect(surface, Colors.DARK_GRAY, track_rect, 1)
        
        # Draw handle
        handle_x = self._get_handle_x()
        handle_rect = pygame.Rect(handle_x, self.rect.y, 
                                self.handle_width, self.handle_height)
        
        handle_color = self.handle_hover_color if (self.hover or self.dragging) else self.handle_color
        pygame.draw.rect(surface, handle_color, handle_rect)
        pygame.draw.rect(surface, Colors.DARK_GRAY, handle_rect, 2)

class ToggleButton(GUIComponent):
    """A toggle button that can be in on/off state"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str = "", initial_state: bool = False, 
                 font_size: int = 16, callback: Optional[Callable[[bool], None]] = None):
        super().__init__(x, y, width, height)
        self.text = text
        self.state = initial_state
        self.callback = callback
        self.font = pygame.font.Font(None, font_size)
        
        # Colors
        self.on_color = Colors.GREEN
        self.off_color = Colors.LIGHT_GRAY
        self.text_color = Colors.BLACK
        self.border_color = Colors.DARK_GRAY
    
    def on_click(self):
        self.state = not self.state
        if self.callback:
            self.callback(self.state)
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # Choose colors based on state
        bg_color = self.on_color if self.state else self.off_color
        if self.hover:
            bg_color = tuple(min(255, c + 20) for c in bg_color)
        if self.clicked:
            bg_color = tuple(max(0, c - 30) for c in bg_color)
        
        # Draw button
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        # Draw text
        if self.text:
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)
        
        # Draw state indicator
        indicator_size = min(self.rect.width // 4, self.rect.height // 4)
        indicator_x = self.rect.right - indicator_size - 5
        indicator_y = self.rect.y + 5
        
        indicator_color = Colors.WHITE if self.state else Colors.DARK_GRAY
        pygame.draw.circle(surface, indicator_color, 
                         (indicator_x + indicator_size // 2, indicator_y + indicator_size // 2), 
                         indicator_size // 2)

class Panel(GUIComponent):
    """A container for organizing GUI elements"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 title: str = "", collapsible: bool = False):
        super().__init__(x, y, width, height)
        self.title = title
        self.collapsible = collapsible
        self.collapsed = False
        self.components: List[GUIComponent] = []
        self.font = pygame.font.Font(None, 16)
        
        # Colors
        self.bg_color = Colors.WHITE
        self.border_color = Colors.DARK_GRAY
        self.title_bg_color = Colors.LIGHT_GRAY
        self.title_text_color = Colors.BLACK
        
        # Title bar height
        self.title_height = 25 if title else 0
        self.content_rect = pygame.Rect(x, y + self.title_height, width, height - self.title_height)
    
    def add_component(self, component: GUIComponent):
        """Add a component to this panel"""
        self.components.append(component)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        
        # Handle title bar click for collapsible panels
        if self.collapsible and self.title and event.type == pygame.MOUSEBUTTONDOWN:
            title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.title_height)
            if title_rect.collidepoint(event.pos):
                self.collapsed = not self.collapsed
                return True
        
        # Handle component events if not collapsed
        if not self.collapsed:
            for component in self.components:
                if component.handle_event(event):
                    return True
        
        return False
    
    def update(self, dt: float):
        if not self.collapsed:
            for component in self.components:
                component.update(dt)
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # Draw panel background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        # Draw title bar
        if self.title:
            title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.title_height)
            pygame.draw.rect(surface, self.title_bg_color, title_rect)
            pygame.draw.rect(surface, self.border_color, title_rect, 1)
            
            # Draw title text
            title_surface = self.font.render(self.title, True, self.title_text_color)
            title_text_rect = title_surface.get_rect(midleft=(title_rect.x + 5, title_rect.centery))
            surface.blit(title_surface, title_text_rect)
            
            # Draw collapse indicator
            if self.collapsible:
                arrow_x = title_rect.right - 15
                arrow_y = title_rect.centery
                if self.collapsed:
                    # Right arrow
                    arrow_points = [(arrow_x - 3, arrow_y - 5), (arrow_x + 3, arrow_y), (arrow_x - 3, arrow_y + 5)]
                else:
                    # Down arrow
                    arrow_points = [(arrow_x - 5, arrow_y - 3), (arrow_x + 5, arrow_y - 3), (arrow_x, arrow_y + 3)]
                pygame.draw.polygon(surface, self.title_text_color, arrow_points)
        
        # Draw components if not collapsed
        if not self.collapsed:
            # Create a clipping rect for the content area
            content_clip = surface.get_clip()
            surface.set_clip(self.content_rect)
            
            for component in self.components:
                component.draw(surface)
            
            surface.set_clip(content_clip)

class MainApplication:
    """Main application class that demonstrates all GUI components"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("3D Architecture GUI")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize GUI components
        self.init_gui()
    
    def init_gui(self):
        """Initialize all GUI components"""
        self.components: List[GUIComponent] = []
        
        # Top toolbar buttons
        button_width = 60
        button_height = 50
        button_spacing = 5
        start_x = 50
        
        # Create toolbar buttons using the asset images
        toolbar_buttons = [
            ("Move", "assets/button_move.png", self.on_move_click),
            ("Copy", "assets/button_copy.png", self.on_copy_click),
            ("Cut", "assets/button_cut.png", self.on_cut_click),
            ("Paste", "assets/button_paste.png", self.on_paste_click),
            ("Delete", "assets/button_delete.png", self.on_delete_click),
            ("Measure", "assets/button_measure.png", self.on_measure_click),
        ]
        
        for i, (name, image_path, callback) in enumerate(toolbar_buttons):
            x = start_x + i * (button_width + button_spacing)
            button = ImageButton(x, 10, button_width, button_height, image_path, callback)
            self.components.append(button)
        
        # Left panel - Library
        library_panel = Panel(10, 80, 180, 500, "LIBRARY", collapsible=True)
        
        # Sound/Material toggle
        sound_toggle = ToggleButton(20, 110, 80, 25, "SOUND", True, callback=self.on_sound_toggle)
        material_toggle = ToggleButton(105, 110, 80, 25, "MATERIAL", False, callback=self.on_material_toggle)
        library_panel.add_component(sound_toggle)
        library_panel.add_component(material_toggle)
        
        # Voice dropdown
        voices_dropdown = DropdownMenu(20, 140, 160, 25, ["Voices", "Adult Male", "Adult Female", "Young boy"], 
                                     callback=self.on_voice_select)
        library_panel.add_component(voices_dropdown)
        
        # Add some placeholder buttons for library items
        for i in range(4):
            item_button = TextButton(20, 180 + i * 35, 75, 30, f"Item {i+1}", callback=lambda: print(f"Item clicked"))
            library_panel.add_component(item_button)
        
        # Categories
        categories = ["HVAC", "Electronics", "Custom"]
        for i, category in enumerate(categories):
            category_button = TextButton(20, 320 + i * 30, 160, 25, f"+ {category}", 14, 
                                       callback=lambda c=category: print(f"{c} clicked"))
            library_panel.add_component(category_button)
        
        self.components.append(library_panel)
        
        # Right panel - Properties
        props_panel = Panel(self.width - 200, 80, 190, 500, "PROPERTY", collapsible=True)
        
        # Slider
        slider_label = TextButton(self.width - 190, 110, 60, 20, "Slider", 14)
        slider = Slider(self.width - 190, 135, 120, 20, 0.0, 2.0, 1.2, self.on_slider_change)
        props_panel.add_component(slider_label)
        props_panel.add_component(slider)
        
        # Single options
        single_options = ["Option 1", "Option 2", "Option 3"]
        for i, option in enumerate(single_options):
            toggle = ToggleButton(self.width - 190, 170 + i * 30, 170, 25, option, 
                                i == 0, callback=lambda state, opt=option: print(f"{opt}: {state}"))
            props_panel.add_component(toggle)
        
        # Dropdown
        dropdown_label = TextButton(self.width - 190, 260, 80, 20, "Drop-down", 14)
        dropdown = DropdownMenu(self.width - 190, 285, 170, 25, ["Text", "Option A", "Option B"], 
                              callback=self.on_dropdown_select)
        props_panel.add_component(dropdown_label)
        props_panel.add_component(dropdown)
        
        # Toggle section
        toggle_label = TextButton(self.width - 190, 320, 80, 20, "Toggle (OFF)", 14)
        toggle_options = ["Option 1"]
        for i, option in enumerate(toggle_options):
            toggle = ToggleButton(self.width - 190, 345 + i * 30, 170, 25, option, 
                                True, callback=lambda state, opt=option: print(f"{opt}: {state}"))
            props_panel.add_component(toggle)
        
        props_panel.add_component(toggle_label)
        self.components.append(props_panel)
        
        # Bottom panel - Assets
        assets_panel = Panel(200, self.height - 120, self.width - 400, 110, "ASSETS", collapsible=True)
        
        # Room button
        room_button = TextButton(210, self.height - 85, 100, 30, "+ Room 1", callback=self.on_add_room)
        assets_panel.add_component(room_button)
        
        self.components.append(assets_panel)
        
        # Bottom toolbar
        bottom_buttons = [
            ("Import Room", self.on_import_room),
            ("Place Sound", self.on_place_sound),
            ("Place Listener", self.on_place_listener),
            ("Render", self.on_render)
        ]
        
        button_width = 100
        total_width = len(bottom_buttons) * button_width + (len(bottom_buttons) - 1) * 10
        start_x = (self.width - total_width) // 2
        
        for i, (text, callback) in enumerate(bottom_buttons):
            x = start_x + i * (button_width + 10)
            button = TextButton(x, self.height - 40, button_width, 30, text, callback=callback)
            self.components.append(button)
    
    # Callback methods
    def on_move_click(self): print("Move tool selected")
    def on_copy_click(self): print("Copy tool selected")
    def on_cut_click(self): print("Cut tool selected") 
    def on_paste_click(self): print("Paste tool selected")
    def on_delete_click(self): print("Delete tool selected")
    def on_measure_click(self): print("Measure tool selected")
    
    def on_sound_toggle(self, state): print(f"Sound: {state}")
    def on_material_toggle(self, state): print(f"Material: {state}")
    def on_voice_select(self, voice): print(f"Voice selected: {voice}")
    
    def on_slider_change(self, value): print(f"Slider value: {value:.2f}")
    def on_dropdown_select(self, option): print(f"Dropdown selected: {option}")
    
    def on_add_room(self): print("Adding room")
    def on_import_room(self): print("Import room")
    def on_place_sound(self): print("Place sound")
    def on_place_listener(self): print("Place listener")
    def on_render(self): print("Render")
    
    def handle_events(self):
        """Handle all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Let GUI components handle events
            for component in self.components:
                if component.handle_event(event):
                    break  # Stop processing if event was consumed
    
    def update(self, dt: float):
        """Update all components"""
        for component in self.components:
            component.update(dt)
    
    def draw(self):
        """Draw everything"""
        self.screen.fill(Colors.WHITE)
        
        # Draw main 3D viewport area
        viewport_rect = pygame.Rect(200, 80, self.width - 400, self.height - 220)
        pygame.draw.rect(self.screen, Colors.LIGHT_GRAY, viewport_rect)
        pygame.draw.rect(self.screen, Colors.DARK_GRAY, viewport_rect, 2)
        
        # Draw a simple 3D-looking cube in the center
        center_x = viewport_rect.centerx
        center_y = viewport_rect.centery
        cube_size = 100
        
        # Back face
        back_points = [
            (center_x - cube_size//2 + 20, center_y - cube_size//2 + 20),
            (center_x + cube_size//2 + 20, center_y - cube_size//2 + 20),
            (center_x + cube_size//2 + 20, center_y + cube_size//2 + 20),
            (center_x - cube_size//2 + 20, center_y + cube_size//2 + 20)
        ]
        
        # Front face
        front_points = [
            (center_x - cube_size//2, center_y - cube_size//2),
            (center_x + cube_size//2, center_y - cube_size//2),
            (center_x + cube_size//2, center_y + cube_size//2),
            (center_x - cube_size//2, center_y + cube_size//2)
        ]
        
        # Draw faces
        pygame.draw.polygon(self.screen, Colors.GRAY, back_points)
        pygame.draw.polygon(self.screen, Colors.WHITE, front_points)
        
        # Draw connecting lines
        for i in range(4):
            pygame.draw.line(self.screen, Colors.DARK_GRAY, front_points[i], back_points[i], 2)
        
        # Draw outlines
        pygame.draw.polygon(self.screen, Colors.DARK_GRAY, back_points, 2)
        pygame.draw.polygon(self.screen, Colors.DARK_GRAY, front_points, 2)
        
        # Draw all GUI components
        for component in self.components:
            component.draw(self.screen)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    app = MainApplication()
    app.run()
