import pygame
import random
import time
import json
from pygame.locals import *

# Initialize pygame
pygame.init()

# Game configuration
class Config:
    SCREEN_WIDTH = 1000
    SCREEN_HEIGHT = 800
    GRID_SIZE = 20
    BG_COLOR = (40, 40, 40)
    SNAKE_COLOR = (0, 255, 0)
    FOOD_COLOR = (255, 0, 0)
    OBSTACLE_COLOR = (150, 150, 150)
    TEXT_COLOR = (255, 255, 255)
    BUTTON_COLOR = (70, 130, 180)
    BUTTON_HOVER_COLOR = (100, 160, 210)
    HISTORY_FILE = "snake_history.json"
    MAX_HISTORY_ENTRIES = 100
    INPUT_BOX_COLOR = (230, 230, 230)
    INPUT_TEXT_COLOR = (0, 0, 0)

# Directions
class Direction:
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# Button class
class Button:
    def __init__(self, x, y, width, height, text, font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont('Arial', font_size)
        self.normal_color = Config.BUTTON_COLOR
        self.hover_color = Config.BUTTON_HOVER_COLOR
        self.text_color = Config.TEXT_COLOR
        self.is_hovered = False
    
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.normal_color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=5)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def is_clicked(self, pos, event):
        return event.type == MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(pos)

# Main game class
class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption('Snake Game')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 36)
        self.small_font = pygame.font.SysFont('Arial', 18)
        
        # Game state
        self.reset_game()
        self.create_buttons()
        self.history = self.load_history()
        self.history_scroll_offset = 0
    
    def reset_game(self):
        self.snake = [
            [Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2],
            [Config.SCREEN_WIDTH // 2 - Config.GRID_SIZE, Config.SCREEN_HEIGHT // 2],
            [Config.SCREEN_WIDTH // 2 - 2 * Config.GRID_SIZE, Config.SCREEN_HEIGHT // 2]
        ]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.score = 0
        self.food_count = 0
        self.obstacles = []
        self.food = self.generate_food()
        self.game_over = False
        self.paused = False
        self.game_started = False
        self.in_menu = True
        self.in_game_setup = False
        self.in_history = False
        self.in_speedrun = False
        self.difficulty = None
        self.start_time = None
        self.end_time = None
        self.pause_time = 0
        self.total_pause_time = 0
        self.speed_input = ""
        self.speed_input_active = False
        self.speed_error = ""
    
    def create_buttons(self):
        button_width = 200
        button_height = 50
        center_x = Config.SCREEN_WIDTH // 2 - button_width // 2
        
        # Main menu buttons
        self.start_button = Button(center_x, 200, button_width, button_height, "Start Game")
        self.speedrun_button = Button(center_x, 280, button_width, button_height, "Speedrun Mode")
        self.history_button = Button(center_x, 360, button_width, button_height, "Game History")
        self.quit_button = Button(center_x, 440, button_width, button_height, "Quit")
        
        # Game setup buttons
        self.easy_button = Button(center_x, 150, button_width, button_height, "Easy")
        self.medium_button = Button(center_x, 220, button_width, button_height, "Medium")
        self.hard_button = Button(center_x, 290, button_width, button_height, "Hard")
        
        # Speed input box
        self.speed_input_rect = pygame.Rect(center_x, 370, button_width, button_height)
        
        self.start_game_button = Button(center_x, 550, button_width, button_height, "Start Game")
        self.back_button = Button(center_x, 630, button_width, button_height, "Back")
        
        # Pause menu buttons
        self.continue_button = Button(center_x, 220, button_width, button_height, "Continue Game")
        self.resume_button = Button(center_x, 300, button_width, button_height, "Restart")
        self.restart_button = Button(center_x, 380, button_width, button_height, "New Game")
        self.menu_button = Button(center_x, 460, button_width, button_height, "Main Menu")
    
    def load_history(self):
        try:
            with open(Config.HISTORY_FILE, 'r') as f:
                history = json.load(f)
                return history[-Config.MAX_HISTORY_ENTRIES:]
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_history(self):
        with open(Config.HISTORY_FILE, 'w') as f:
            json.dump(self.history[-Config.MAX_HISTORY_ENTRIES:], f)
    
    def add_game_to_history(self):
        game_data = {
            "mode": "Speedrun" if self.in_speedrun else "Classic",
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_time)),
            "duration": round(self.end_time - self.start_time - self.total_pause_time, 2),
            "difficulty": self.difficulty if not self.in_speedrun else "N/A",
            "speed": self.speed,
            "score": self.score
        }
        self.history.append(game_data)
        self.save_history()
    
    def generate_food(self):
        while True:
            x = random.randint(0, (Config.SCREEN_WIDTH - Config.GRID_SIZE) // Config.GRID_SIZE) * Config.GRID_SIZE
            y = random.randint(0, (Config.SCREEN_HEIGHT - Config.GRID_SIZE) // Config.GRID_SIZE) * Config.GRID_SIZE
            if [x, y] not in self.snake and [x, y] not in self.obstacles:
                return [x, y]
    
    def generate_obstacles(self, count):
        self.obstacles = []
        for _ in range(count):
            while True:
                x = random.randint(3, (Config.SCREEN_WIDTH - Config.GRID_SIZE) // Config.GRID_SIZE - 3) * Config.GRID_SIZE
                y = random.randint(3, (Config.SCREEN_HEIGHT - Config.GRID_SIZE) // Config.GRID_SIZE - 3) * Config.GRID_SIZE
                
                if self.difficulty == "Hard" and random.random() < 0.3:
                    wall_length = random.randint(2, 3)
                    wall_direction = random.choice(["horizontal", "vertical"])
                    
                    valid = True
                    temp_obstacles = []
                    for i in range(wall_length):
                        if wall_direction == "horizontal":
                            new_x = x + i * Config.GRID_SIZE
                            new_y = y
                        else:
                            new_x = x
                            new_y = y + i * Config.GRID_SIZE
                        
                        if (new_x >= Config.SCREEN_WIDTH or new_y >= Config.SCREEN_HEIGHT or
                            [new_x, new_y] in self.snake or [new_x, new_y] == self.food or
                            [new_x, new_y] in self.obstacles):
                            valid = False
                            break
                        
                        temp_obstacles.append([new_x, new_y])
                    
                    if valid:
                        self.obstacles.extend(temp_obstacles)
                        break
                else:
                    if [x, y] not in self.snake and [x, y] != self.food and [x, y] not in self.obstacles:
                        self.obstacles.append([x, y])
                        break
    
    def move_snake(self):
        head = self.snake[0].copy()
        head[0] += self.direction[0] * Config.GRID_SIZE
        head[1] += self.direction[1] * Config.GRID_SIZE
        
        # Check collisions
        if (head[0] < 0 or head[0] >= Config.SCREEN_WIDTH or 
            head[1] < 0 or head[1] >= Config.SCREEN_HEIGHT or
            head in self.snake or head in self.obstacles):
            self.game_over = True
            self.end_time = time.time()
            self.add_game_to_history()
            return
        
        self.snake.insert(0, head)
        
        if head == self.food:
            self.score += 1
            self.food_count += 1
            self.food = self.generate_food()
            
            if self.in_speedrun and self.food_count % 5 == 0:
                self.speed += 1
            
            if not self.in_speedrun:
                if self.difficulty == "Medium":
                    self.generate_obstacles(3)
                elif self.difficulty == "Hard":
                    self.generate_obstacles(5)
        else:
            self.snake.pop()
    
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return False
            
            if self.in_menu:
                self.handle_menu_events(event, mouse_pos)
            elif self.in_game_setup:
                self.handle_setup_events(event, mouse_pos)
            elif self.in_history:
                self.handle_history_events(event, mouse_pos)
            elif self.paused:
                self.handle_pause_events(event, mouse_pos)
            elif not self.game_over and self.game_started:
                self.handle_game_events(event)
            elif self.game_over:
                if event.type == KEYDOWN and event.key == K_r:
                    self.reset_game()
                    if self.in_speedrun:
                        self.start_speedrun()
                    else:
                        self.in_menu = True
        
        return True
    
    def handle_menu_events(self, event, mouse_pos):
        self.start_button.check_hover(mouse_pos)
        self.speedrun_button.check_hover(mouse_pos)
        self.history_button.check_hover(mouse_pos)
        self.quit_button.check_hover(mouse_pos)
        
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.start_button.rect.collidepoint(mouse_pos):
                self.in_menu = False
                self.in_game_setup = True
            elif self.speedrun_button.rect.collidepoint(mouse_pos):
                self.start_speedrun()
            elif self.history_button.rect.collidepoint(mouse_pos):
                self.in_menu = False
                self.in_history = True
            elif self.quit_button.rect.collidepoint(mouse_pos):
                pygame.quit()
                return False
    
    def handle_setup_events(self, event, mouse_pos):
        self.easy_button.check_hover(mouse_pos)
        self.medium_button.check_hover(mouse_pos)
        self.hard_button.check_hover(mouse_pos)
        
        self.start_game_button.check_hover(mouse_pos)
        self.back_button.check_hover(mouse_pos)
        
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.easy_button.rect.collidepoint(mouse_pos):
                self.difficulty = "Easy"
            elif self.medium_button.rect.collidepoint(mouse_pos):
                self.difficulty = "Medium"
            elif self.hard_button.rect.collidepoint(mouse_pos):
                self.difficulty = "Hard"
            
            if self.speed_input_rect.collidepoint(mouse_pos):
                self.speed_input_active = True
                self.speed_error = ""
            else:
                self.speed_input_active = False
            
            if self.start_game_button.rect.collidepoint(mouse_pos) and self.difficulty:
                self.start_game()
            elif self.back_button.rect.collidepoint(mouse_pos):
                self.in_game_setup = False
                self.in_menu = True
        
        if event.type == KEYDOWN and self.speed_input_active:
            if event.key == K_BACKSPACE:
                self.speed_input = self.speed_input[:-1]
            elif event.key == K_RETURN:
                try:
                    speed = int(self.speed_input)
                    if speed >= 1:
                        self.speed = speed
                        self.speed_error = ""
                    else:
                        self.speed_error = "Speed must be at least 1"
                except ValueError:
                    self.speed_error = "Please enter a valid number"
                self.speed_input_active = False
            elif event.unicode.isdigit():
                self.speed_input += event.unicode
    
    def handle_history_events(self, event, mouse_pos):
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 4:  # Mouse wheel up
                self.history_scroll_offset = max(0, self.history_scroll_offset - 1)
            elif event.button == 5:  # Mouse wheel down
                max_offset = max(0, len(self.history) - 10)
                self.history_scroll_offset = min(max_offset, self.history_scroll_offset + 1)
            elif event.button == 1:  # Left click
                self.in_history = False
                self.in_menu = True
    
    def handle_pause_events(self, event, mouse_pos):
        self.continue_button.check_hover(mouse_pos)
        self.resume_button.check_hover(mouse_pos)
        self.restart_button.check_hover(mouse_pos)
        self.menu_button.check_hover(mouse_pos)
        
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.continue_button.rect.collidepoint(mouse_pos):
                self.unpause_game()
            elif self.resume_button.rect.collidepoint(mouse_pos):
                self.unpause_game()
            elif self.restart_button.rect.collidepoint(mouse_pos):
                self.reset_game()
                if self.in_speedrun:
                    self.start_speedrun()
                else:
                    self.start_game()
            elif self.menu_button.rect.collidepoint(mouse_pos):
                self.reset_game()
                self.in_menu = True
    
    def handle_game_events(self, event):
        if event.type == KEYDOWN:
            if event.key == K_p:
                self.pause_game()
            elif event.key == K_b:  # Back to menu
                self.reset_game()
                self.in_menu = True
            elif event.key == K_n:  # New game same mode
                self.reset_game()
                if self.in_speedrun:
                    self.start_speedrun()
                else:
                    self.start_game()
            elif not self.paused:
                if event.key in (K_UP, K_w) and self.direction != Direction.DOWN:
                    self.next_direction = Direction.UP
                elif event.key in (K_DOWN, K_s) and self.direction != Direction.UP:
                    self.next_direction = Direction.DOWN
                elif event.key in (K_LEFT, K_a) and self.direction != Direction.RIGHT:
                    self.next_direction = Direction.LEFT
                elif event.key in (K_RIGHT, K_d) and self.direction != Direction.LEFT:
                    self.next_direction = Direction.RIGHT
    
    def start_game(self):
        # Validate speed before starting
        try:
            speed = int(self.speed_input)
            if speed < 1:
                self.speed_error = "Speed must be at least 1"
                return
            self.speed = speed
        except ValueError:
            self.speed_error = "Please enter a valid number"
            return
        
        if self.difficulty == "Easy":
            self.obstacles = []
        elif self.difficulty == "Medium":
            self.generate_obstacles(5)
        elif self.difficulty == "Hard":
            self.generate_obstacles(10)
        
        self.in_game_setup = False
        self.game_started = True
        self.in_speedrun = False
        self.start_time = time.time()
        self.countdown(3)
    
    def start_speedrun(self):
        self.obstacles = []
        self.speed = 5
        self.in_menu = False
        self.game_started = True
        self.in_speedrun = True
        self.start_time = time.time()
        self.countdown(3)
    
    def pause_game(self):
        self.paused = True
        self.pause_time = time.time()
    
    def unpause_game(self):
        self.paused = False
        self.total_pause_time += time.time() - self.pause_time
    
    def countdown(self, seconds):
        for i in range(seconds, 0, -1):
            self.screen.fill(Config.BG_COLOR)
            countdown_text = self.big_font.render(str(i), True, (255, 0, 0))
            self.screen.blit(countdown_text, 
                           (Config.SCREEN_WIDTH // 2 - countdown_text.get_width() // 2, 
                            Config.SCREEN_HEIGHT // 2 - countdown_text.get_height() // 2))
            pygame.display.flip()
            pygame.time.wait(1000)
    
    def update(self):
        if not self.game_started or self.paused or self.game_over:
            return
        
        self.direction = self.next_direction
        self.move_snake()
    
    def draw(self):
        self.screen.fill(Config.BG_COLOR)
        
        if self.in_menu:
            self.draw_menu()
        elif self.in_game_setup:
            self.draw_game_setup()
        elif self.in_history:
            self.draw_history()
        elif not self.game_started:
            pass
        elif self.game_over:
            self.draw_game_over()
        elif self.paused:
            self.draw_game()
            self.draw_pause_menu()
        else:
            self.draw_game()
        
        pygame.display.flip()
    
    def draw_menu(self):
        title = self.big_font.render('Snake Game', True, Config.TEXT_COLOR)
        self.screen.blit(title, (Config.SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        
        self.start_button.draw(self.screen)
        self.speedrun_button.draw(self.screen)
        self.history_button.draw(self.screen)
        self.quit_button.draw(self.screen)
    
    def draw_game_setup(self):
        title = self.big_font.render('Game Setup', True, Config.TEXT_COLOR)
        self.screen.blit(title, (Config.SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        # Draw difficulty selection
        difficulty_text = self.font.render('Select Difficulty:', True, Config.TEXT_COLOR)
        self.screen.blit(difficulty_text, (Config.SCREEN_WIDTH // 2 - difficulty_text.get_width() // 2, 120))
        
        self.easy_button.draw(self.screen)
        self.medium_button.draw(self.screen)
        self.hard_button.draw(self.screen)
        
        # Highlight selected difficulty
        if self.difficulty:
            diff_rect = None
            if self.difficulty == "Easy":
                diff_rect = self.easy_button.rect
            elif self.difficulty == "Medium":
                diff_rect = self.medium_button.rect
            elif self.difficulty == "Hard":
                diff_rect = self.hard_button.rect
            
            if diff_rect:
                pygame.draw.rect(self.screen, (255, 255, 0), diff_rect, 3, border_radius=5)
        
        # Draw speed input
        speed_text = self.font.render('Enter Speed (1+):', True, Config.TEXT_COLOR)
        self.screen.blit(speed_text, (Config.SCREEN_WIDTH // 2 - speed_text.get_width() // 2, 340))
        
        # Draw input box
        pygame.draw.rect(self.screen, 
                        Config.INPUT_BOX_COLOR if self.speed_input_active else (200, 200, 200), 
                        self.speed_input_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0, 0, 0), self.speed_input_rect, 2, border_radius=5)
        
        # Draw input text
        input_surface = self.font.render(self.speed_input, True, Config.INPUT_TEXT_COLOR)
        self.screen.blit(input_surface, (self.speed_input_rect.x + 10, self.speed_input_rect.y + 15))
        
        # Draw current selected speed
        if hasattr(self, 'speed') and not self.speed_input_active and self.speed_input:
            speed_display = self.font.render(f"Current: {self.speed}", True, Config.TEXT_COLOR)
            self.screen.blit(speed_display, (self.speed_input_rect.x, self.speed_input_rect.y + 50))
        
        # Draw error message
        if self.speed_error:
            error_text = self.font.render(self.speed_error, True, (255, 0, 0))
            self.screen.blit(error_text, (self.speed_input_rect.x, self.speed_input_rect.y + 80))
        
        # Draw start and back buttons
        self.start_game_button.draw(self.screen)
        self.back_button.draw(self.screen)
    
    def draw_history(self):
        title = self.big_font.render('Game History', True, Config.TEXT_COLOR)
        self.screen.blit(title, (Config.SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        if not self.history:
            no_history = self.font.render('No game history yet', True, Config.TEXT_COLOR)
            self.screen.blit(no_history, (Config.SCREEN_WIDTH // 2 - no_history.get_width() // 2, 150))
        else:
            # Table parameters
            table_x = 50
            table_y = 120
            row_height = 30
            visible_rows = 15
            column_widths = [100, 180, 80, 100, 60, 60]  # Mode, Start Time, Duration, Difficulty, Speed, Score
            
            # Draw table headers with dividers
            headers = ["Mode", "Start Time", "Duration", "Difficulty", "Speed", "Score"]
            header_y = table_y
            for i, (header, width) in enumerate(zip(headers, column_widths)):
                header_surface = self.font.render(header, True, Config.TEXT_COLOR)
                header_x = table_x + sum(column_widths[:i]) + i * 10
                self.screen.blit(header_surface, (header_x + 5, header_y + 5))
                
                # Draw header divider
                pygame.draw.line(self.screen, Config.TEXT_COLOR, 
                               (header_x, header_y + row_height),
                               (header_x + width, header_y + row_height), 2)
            
            # Draw vertical dividers
            for i in range(len(column_widths) + 1):
                divider_x = table_x + sum(column_widths[:i]) + i * 10
                pygame.draw.line(self.screen, Config.TEXT_COLOR,
                               (divider_x, table_y),
                               (divider_x, table_y + visible_rows * row_height), 1)
            
            # Draw table rows with alternating colors
            visible_history = self.history[self.history_scroll_offset:self.history_scroll_offset+visible_rows]
            for row_idx, game in enumerate(visible_history):
                row_y = table_y + (row_idx + 1) * row_height
                
                # Alternate row colors
                if row_idx % 2 == 0:
                    row_color = (60, 60, 60)
                else:
                    row_color = (80, 80, 80)
                
                pygame.draw.rect(self.screen, row_color, 
                               (table_x, row_y, sum(column_widths) + (len(column_widths)-1)*10, row_height))
                
                # Draw cell content
                cells = [
                    game["mode"],
                    game["start_time"],
                    f"{game['duration']}s",
                    game["difficulty"],
                    str(game["speed"]),
                    str(game["score"])
                ]
                
                for i, (cell, width) in enumerate(zip(cells, column_widths)):
                    cell_x = table_x + sum(column_widths[:i]) + i * 10 + 5
                    cell_surface = self.small_font.render(cell, True, Config.TEXT_COLOR)
                    self.screen.blit(cell_surface, (cell_x, row_y + 5))
            
            # Draw scroll indicator if needed
            if len(self.history) > visible_rows:
                scroll_text = self.font.render(
                    f"Showing {self.history_scroll_offset+1}-{min(self.history_scroll_offset+visible_rows, len(self.history))} of {len(self.history)}", 
                    True, Config.TEXT_COLOR)
                self.screen.blit(scroll_text, (Config.SCREEN_WIDTH // 2 - scroll_text.get_width() // 2, table_y + (visible_rows + 1) * row_height))
        
        back_text = self.font.render('Click to return or use mouse wheel to scroll', True, Config.TEXT_COLOR)
        self.screen.blit(back_text, (Config.SCREEN_WIDTH // 2 - back_text.get_width() // 2, table_y + (visible_rows + 2) * row_height))
    
    def draw_game(self):
        # Draw obstacles
        for obstacle in self.obstacles:
            pygame.draw.rect(self.screen, Config.OBSTACLE_COLOR, 
                           (*obstacle, Config.GRID_SIZE, Config.GRID_SIZE))
        
        # Draw snake
        for segment in self.snake:
            pygame.draw.rect(self.screen, Config.SNAKE_COLOR, 
                           (*segment, Config.GRID_SIZE, Config.GRID_SIZE))
        
        # Draw food
        pygame.draw.rect(self.screen, Config.FOOD_COLOR, 
                        (*self.food, Config.GRID_SIZE, Config.GRID_SIZE))
        
        # Draw game info
        current_time = time.time() - self.start_time - self.total_pause_time
        time_text = self.font.render(f'Time: {current_time:.1f}s', True, Config.TEXT_COLOR)
        self.screen.blit(time_text, (10, 10))
        
        score_text = self.font.render(f'Score: {self.score}', True, Config.TEXT_COLOR)
        self.screen.blit(score_text, (10, 40))
        
        speed_text = self.font.render(f'Speed: {self.speed}', True, Config.TEXT_COLOR)
        self.screen.blit(speed_text, (10, 70))
        
        mode_text = self.font.render(f'Mode: {"Speedrun" if self.in_speedrun else self.difficulty}', True, Config.TEXT_COLOR)
        self.screen.blit(mode_text, (10, 100))
        
        if self.in_speedrun:
            food_text = self.font.render(f'Food: {self.food_count} (Next speed at {(self.food_count // 5 + 1) * 5})', 
                                       True, Config.TEXT_COLOR)
            self.screen.blit(food_text, (10, 130))
    
    def draw_pause_menu(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = self.big_font.render('GAME PAUSED', True, (255, 255, 0))
        self.screen.blit(pause_text, 
                       (Config.SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 
                        Config.SCREEN_HEIGHT // 2 - 150))
        
        # Buttons
        self.continue_button.draw(self.screen)
        self.resume_button.draw(self.screen)
        self.restart_button.draw(self.screen)
        self.menu_button.draw(self.screen)
    
    def draw_game_over(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        game_over = self.big_font.render('GAME OVER', True, (255, 0, 0))
        self.screen.blit(game_over, (Config.SCREEN_WIDTH // 2 - game_over.get_width() // 2, 150))
        
        time_played = self.end_time - self.start_time - self.total_pause_time
        stats = [
            f'Final Score: {self.score}',
            f'Time Played: {time_played:.1f}s',
            f'Mode: {"Speedrun" if self.in_speedrun else self.difficulty}',
            f'Speed: {self.speed}',
            '',
            'Press R to return to menu'
        ]
        
        y_offset = 220
        for stat in stats:
            stat_text = self.font.render(stat, True, Config.TEXT_COLOR)
            self.screen.blit(stat_text, (Config.SCREEN_WIDTH // 2 - stat_text.get_width() // 2, y_offset))
            y_offset += 40
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.speed if self.game_started and not self.paused else 60)

# Run the game
if __name__ == '__main__':
    game = SnakeGame()
    game.run()