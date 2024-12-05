# ----------------------------------------
# IMPORTS AND INITIALIZATION
# ----------------------------------------
import pygame
import sys
from os import path

# ----------------------------------------
# GAME CLASS - Core game engine and asset management
# ----------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        
        # Set exact pixel dimensions
        self.MAP_WIDTH = 3955
        self.MAP_HEIGHT = 2875
        
        self.screen_width = 1900
        self.screen_height = 1000
        # Define spawn coordinates
        self.PLAYER_SPAWN_X = 450
        self.PLAYER_SPAWN_Y = 400
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('Zelda Adventure')
        self.clock = pygame.time.Clock()
        self.running = True
        self.collision_areas = []
        self.load_assets()
        self.create_collision_map()

    def load_assets(self):
        self.assets_dir = path.join(path.dirname(__file__), 'assets')
        self.sprite_sheet = pygame.image.load(path.join(self.assets_dir, 'link.png')).convert_alpha()
        
        # Load and scale terrain to exact dimensions
        self.terrain = pygame.image.load(path.join(self.assets_dir, 'terrain.png')).convert()
        self.terrain = pygame.transform.scale(self.terrain, (self.MAP_WIDTH, self.MAP_HEIGHT))
        
        # Load and scale collision map to match terrain exactly
        self.collision_map = pygame.image.load(path.join(self.assets_dir, 'collision.png')).convert()
        self.collision_map = pygame.transform.scale(self.collision_map, (self.MAP_WIDTH, self.MAP_HEIGHT))

    def create_collision_map(self):
        # Group collision areas into larger chunks for performance
        CHUNK_SIZE = 32
        for y in range(0, self.collision_map.get_height(), CHUNK_SIZE):
            for x in range(0, self.collision_map.get_width(), CHUNK_SIZE):
                has_collision = False
                for py in range(CHUNK_SIZE):
                    for px in range(CHUNK_SIZE):
                        if (x + px < self.collision_map.get_width() and
                            y + py < self.collision_map.get_height() and
                            self.collision_map.get_at((x + px, y + py)) == (0, 0, 0)):
                            has_collision = True
                            break
                    if has_collision:
                        break
                if has_collision:
                    self.collision_areas.append(pygame.Rect(x, y, CHUNK_SIZE, CHUNK_SIZE))

# ----------------------------------------
# PLAYER CLASS - Character controls, animations, and collision handling
# ----------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        # Load player collision mask
        self.collision_mask = pygame.image.load(path.join(self.game.assets_dir, 'link_collision.png')).convert()
        self.collision_points = []
        
        # Animation states
        self.animations = {
            'idle': {},
            'walk': {}
        }
        
        # Player properties
        self.frame_width = 90
        self.frame_height = 110
        self.x = x
        self.y = y
        self.speed = 4
        self.state = 'idle'
        self.direction = 'down'
        self.animation_frame = 0
        self.animation_speed = 0.1
        self.animation_timer = 0
        self.attacking = False
        
        # Load all animations
        self.load_animations()
        self.image = self.animations['idle']['down'][0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
         
        # Get collision points from the mask
        for y in range(self.collision_mask.get_height()):
            for x in range(self.collision_mask.get_width()):
                if self.collision_mask.get_at((x, y)) == (0, 0, 0):
                    self.collision_points.append((x, y))

    # ----------------------------------------
    # Player collision detection
    # ----------------------------------------
    def check_collision(self):
        player_area = pygame.Rect(self.rect.x - 32, self.rect.y - 32, self.rect.width + 64, self.rect.height + 64)
        nearby_barriers = [barrier for barrier in self.game.collision_areas if player_area.colliderect(barrier)]
        
        for point_x, point_y in self.collision_points:
            world_x = self.rect.x + point_x
            world_y = self.rect.y + point_y
            for barrier in nearby_barriers:
                if barrier.collidepoint(world_x, world_y):
                    return True
        return False

    # ----------------------------------------
    # Animation system
    # ----------------------------------------
    def load_animations(self):
        # Define animation frames for each state and direction
        animation_data = {
            'idle': {
                'down':  [(-3.5, 0), (99.5, 0), (202.5, 0)],
                'up':    [(-3.5, 225)],
                'left':  [(-3.5, 120), (99.5, 120), (202.5, 120)],
                'right': [(-3.5, 337), (95, 337), (202.5, 337)]
            },
            'walk': {
                'down':  [(-3.5, 450), (95, 450), (202.5, 450), (307.5, 450), (412.5, 450), (517.5, 450), (622.5, 450), (727.5, 450), (832.5, 450), (937.5, 450)],
                'up':    [(-3.5, 668), (95, 668), (202.5, 668), (307.5, 668), (412.5, 668), (517.5, 668), (622.5, 668), (727.5, 668), (832.5, 668), (937.5, 668)],
                'left':  [(-3.5, 555), (103, 555), (202.5, 555), (307.5, 555), (412.5, 555), (515.5, 555), (622.5, 555), (725.5, 555), (830.5, 555), (934.5, 555)],
                'right': [(-3.5, 775), (103, 775), (202.5, 775), (307.5, 775), (412.5, 775), (515.5, 775), (622.5, 775), (725.5, 775), (830.5, 775), (934.5, 775)]
            }
        }

        # Load all animation frames
        for state in animation_data:
            self.animations[state] = {}
            for direction in animation_data[state]:
                self.animations[state][direction] = []
                for x, y in animation_data[state][direction]:
                    frame = self.get_frame(x, y)
                    self.animations[state][direction].append(frame)

    def get_frame(self, x, y):
        frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
        frame.blit(self.game.sprite_sheet, (0, 0), (x, y, self.frame_width, self.frame_height))
        return frame

    def animate(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.state][self.direction]
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.image = frames[self.animation_frame]

    def update(self, dt):
        # Store previous position
        previous_x = self.rect.x
        previous_y = self.rect.y

        keys = pygame.key.get_pressed()
        moving = False

        if not self.attacking:
            # Movement controls with collision checks
            if keys[pygame.K_LEFT]:
                self.rect.x -= self.speed
                self.direction = 'left'
                moving = True
                if self.check_collision():
                    self.rect.x = previous_x

            if keys[pygame.K_RIGHT]:
                self.rect.x += self.speed
                self.direction = 'right'
                moving = True
                if self.check_collision():
                    self.rect.x = previous_x

            if keys[pygame.K_UP]:
                self.rect.y -= self.speed
                self.direction = 'up'
                moving = True
                if self.check_collision():
                    self.rect.y = previous_y

            if keys[pygame.K_DOWN]:
                self.rect.y += self.speed
                self.direction = 'down'
                moving = True
                if self.check_collision():
                    self.rect.y = previous_y

            # Map boundaries
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > 3955:
                self.rect.right = 3955
            if self.rect.top < 0:
                self.rect.top = 0
            if self.rect.bottom > 2875:
                self.rect.bottom = 2875

            # Attack handling
            if keys[pygame.K_SPACE]:
                self.state = 'attack'
                self.attacking = True
                self.animation_frame = 0
            elif moving:
                self.state = 'walk'
            else:
                self.state = 'idle'

        self.animate(dt)

        if self.attacking and self.animation_frame >= len(self.animations['attack'][self.direction]) - 1:
            self.attacking = False
            self.state = 'idle'

# ----------------------------------------
# CAMERA CLASS - Handles viewport and scrolling
# ----------------------------------------
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update_camera(self, target):
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)

        # Limit scrolling to map size
        self.offset_x = min(0, 3955)
        self.offset_y = min(0, 2875)
        
        self.camera = pygame.Rect(x, y, self.width, self.height)

# ----------------------------------------
# MENU SYSTEM - Main menu interface
# ----------------------------------------
def main_menu(screen):
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # Menu options
    menu_items = ['Start Game', 'Options', 'Exit']
    selected_item = 0
    
    # Menu styling
    font = pygame.font.Font(None, 48)
    title_font = pygame.font.Font(None, 74)
    
    while True:
        screen.fill((0, 0, 0))
        
        # Draw title
        title = title_font.render('Zelda Adventure', True, (34, 139, 34))
        title_rect = title.get_rect(center=(screen_width // 2, 100))
        screen.blit(title, title_rect)
        
        # Draw menu items
        for i, item in enumerate(menu_items):
            color = (255, 255, 255) if i != selected_item else (34, 139, 34)
            text = font.render(item, True, color)
            text_rect = text.get_rect(center=(screen_width // 2, 250 + i * 60))
            screen.blit(text, text_rect)
        
        pygame.display.flip()
        
        # Handle menu navigation
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_item = (selected_item - 1) % len(menu_items)
                elif event.key == pygame.K_DOWN:
                    selected_item = (selected_item + 1) % len(menu_items)
                elif event.key == pygame.K_RETURN:
                    if selected_item == 0:  # Start Game
                        return True
                    elif selected_item == 1:  # Options
                        pass  # Add options menu later
                    elif selected_item == 2:  # Exit
                        pygame.quit()
                        sys.exit()

# ----------------------------------------
# LOADING SCREEN - Progress indicator
# ----------------------------------------
def show_loading_screen(screen):
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # Loading bar dimensions
    bar_width = 400
    bar_height = 40
    bar_x = (screen_width - bar_width) // 2
    bar_y = (screen_height - bar_height) // 2
    
    # Loading text
    font = pygame.font.Font(None, 36)
    text = font.render("Loading...", True, (34, 139, 34))
    text_rect = text.get_rect(center=(screen_width // 2, bar_y - 50))
    
    for progress in range(101):
        screen.fill((0, 0, 0))
        
        # Draw border
        pygame.draw.rect(screen, (34, 139, 34), (bar_x - 3, bar_y - 3, bar_width + 6, bar_height + 6))
        
        # Draw background
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Draw progress
        progress_width = int(bar_width * (progress / 100))
        pygame.draw.rect(screen, (34, 139, 34), (bar_x, bar_y, progress_width, bar_height))
        
        screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.delay(50)  # Control loading speed

# ----------------------------------------
# MAIN GAME LOOP - Core game execution
# ----------------------------------------
def main():
    game = Game()
    if main_menu(game.screen):
        show_loading_screen(game.screen)
    all_sprites = pygame.sprite.Group()
    player = Player(game, game.PLAYER_SPAWN_X, game.PLAYER_SPAWN_Y)
    camera = Camera(game.screen_width, game.screen_height)
    all_sprites.add(player)

    while game.running:
        dt = game.clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False

        all_sprites.update(dt)
        camera.update_camera(player)

        game.screen.fill((0,0,0))
        game.screen.blit(game.terrain, camera.camera.topleft)
        
        for sprite in all_sprites:
            game.screen.blit(sprite.image, camera.apply(sprite))
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

# ----------------------------------------
# ENTRY POINT
# ----------------------------------------
if __name__ == '__main__':
    main()