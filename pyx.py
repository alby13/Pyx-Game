import pygame
import sys
import math
import random
from pygame.locals import *

# --------------------------- Constants & Setup ---------------------------
WIDTH, HEIGHT = 1920, 1080
FPS = 60
TARGET_FILL_PERCENTAGE = 75

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BORDER_COLOR = (100, 100, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Qix Rainbow Edition')
clock = pygame.time.Clock()

# --------------------------- Utility Functions ---------------------------

def rainbow_color(t):
    """Return a rainbow color based on angle t."""
    r = int(127 * math.sin(t) + 128)
    g = int(127 * math.sin(t + 2) + 128)
    b = int(127 * math.sin(t + 4) + 128)
    return (r, g, b)

def point_in_polygon(point, polygon):
    """Determine if point is in polygon using the ray-casting algorithm."""
    x, y = point
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def point_to_line_distance(x, y, x1, y1, x2, y2):
    """Calculate the distance from point (x,y) to line segment (x1,y1)-(x2,y2)."""
    A = x - x1
    B = y - y1
    C = x2 - x1
    D = y2 - y1

    dot = A * C + B * D
    len_sq = C * C + D * D

    if len_sq == 0:
        return math.sqrt(A * A + B * B)

    param = dot / len_sq

    if param < 0:
        xx, yy = x1, y1
    elif param > 1:
        xx, yy = x2, y2
    else:
        xx = x1 + param * C
        yy = y1 + param * D

    return math.sqrt((x - xx)**2 + (y - yy)**2)

def calculate_area_percentage(filled_areas, total_area):
    """Calculate percentage of total area covered by filled polygons."""
    filled = 0
    for polygon in filled_areas:
        if len(polygon) < 3:
            continue
        area = 0
        for i in range(len(polygon) - 1):
            area += polygon[i][0] * polygon[i+1][1] - polygon[i+1][0] * polygon[i][1]
        area = abs(area) / 2
        filled += area
    return (filled / total_area) * 100

def draw_game_boundary(surface):
    """Draw the game boundary rectangle."""
    pygame.draw.rect(surface, BORDER_COLOR, (0, 0, WIDTH, HEIGHT), 2)

# --------------------------- Classes ---------------------------

class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.speed = 4
        self.thickness = 4
        self.drawing = False
        self.temp_points = []
        self.filled_areas = []
        self.color_offset = 0
        self.current_direction = None  # 'up', 'down', 'left', 'right', or None
        self.sparks = []
        self.boundary_points = self.generate_boundary_points() # Pre-calculate boundary points

    def generate_boundary_points(self):
        """Generate a list of points that make up the game boundary."""
        boundary = []
        # Top
        for x in range(0, WIDTH):
            boundary.append((x, 0))
        # Right
        for y in range(1, HEIGHT):
            boundary.append((WIDTH - 1, y))
        # Bottom
        for x in range(WIDTH - 2, -1, -1):
            boundary.append((x, HEIGHT - 1))
        # Left
        for y in range(HEIGHT - 2, 0, -1):
            boundary.append((0, y))
        return boundary

    def is_on_boundary(self, x, y):

        for px, py in self.boundary_points:
            if (x, y) == (px, py):
                return True

        for area in self.filled_areas:
            for i in range(len(area) - 1):  # Iterate through edges, not just vertices
                if point_to_line_distance(x, y, area[i][0], area[i][1], area[i+1][0], area[i+1][1]) <= 2:
                    return True  # Consider points close to lines as on the boundary
        return False

    def is_valid_move(self, new_x, new_y):
        """Checks if a potential move is valid, considering boundaries and existing lines."""
        if not self.is_on_boundary(new_x, new_y): #boundary check is still needed to stop drawing
             # Check for collisions with the current drawing path, excluding the last few points
            # (to allow for small overlaps when turning)
            if self.drawing:
                for i in range(len(self.temp_points) - 5):  # -5:  Don't check against the very recent points
                    if self.temp_points[i] == (new_x, new_y):
                        return False
        return True

    def move(self, dx, dy):
        if self.drawing:
            # Determine new direction, but only if there's actual input
            if dx != 0 or dy != 0:
                if dx > 0:
                    new_direction = 'right'
                elif dx < 0:
                    new_direction = 'left'
                elif dy > 0:
                    new_direction = 'down'
                elif dy < 0:
                    new_direction = 'up'

                # Only change direction if it's a 90-degree turn
                if self.current_direction is not None:
                    if (self.current_direction in ('left', 'right') and new_direction in ('up', 'down')) or \
                       (self.current_direction in ('up', 'down') and new_direction in ('left', 'right')):
                        self.current_direction = new_direction
                else:
                     self.current_direction = new_direction #set initial direction

            # Apply movement based on current_direction
            if self.current_direction == 'up':
                dx, dy = 0, -1
            elif self.current_direction == 'down':
                dx, dy = 0, 1
            elif self.current_direction == 'left':
                dx, dy = -1, 0
            elif self.current_direction == 'right':
                dx, dy = 1, 0

            new_x = self.x + dx * self.speed
            new_y = self.y + dy * self.speed

            if self.is_valid_move(new_x, new_y):
                self.x = new_x
                self.y = new_y
                self.temp_points.append((self.x, self.y))

                # Create a spark
                if random.random() < 0.3:
                    self.create_spark()

            if self.is_on_boundary(new_x, new_y) and (new_x, new_y) != self.temp_points[0]: #check for the new point hitting the boundary
                 self.stop_drawing()

        else:  # Not drawing - boundary movement only
            new_x = self.x + dx * self.speed
            new_y = self.y + dy * self.speed
            if self.is_on_boundary(new_x, new_y):
                self.x = new_x
                self.y = new_y

    def create_spark(self):
        """Create a spark particle at the player's position"""
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 3)
        lifetime = random.randint(5, 15)
        color_offset = random.random() * 2 * math.pi
        self.sparks.append({
            'x': self.x,
            'y': self.y,
            'dx': math.cos(angle) * speed,
            'dy': math.sin(angle) * speed,
            'lifetime': lifetime,
            'color_offset': color_offset
        })

    def update_sparks(self):
        """Update all spark particles"""
        for spark in self.sparks:
            spark['x'] += spark['dx']
            spark['y'] += spark['dy']
            spark['lifetime'] -= 1
        # Remove dead sparks
        self.sparks = [s for s in self.sparks if s['lifetime'] > 0]

    def start_drawing(self):
        if not self.drawing and self.is_on_boundary(self.x, self.y):
            self.drawing = True
            self.temp_points = [(self.x, self.y)]
            self.current_direction = None

    def calculate_polygon_area(self, polygon):
        area = 0
        for i in range(len(polygon) - 1):
            area += polygon[i][0] * polygon[i+1][1] - polygon[i+1][0] * polygon[i][1]
        return abs(area) / 2

    def stop_drawing(self):
        if not self.drawing or len(self.temp_points) <= 2:
            return

        start_point = self.temp_points[0]
        end_point = self.temp_points[-1]

        # Determine which side of the boundary each point is on.
        def get_boundary_side(point):
            x, y = point
            tol = 2  # tolerance (in pixels)
            if abs(y - 0) < tol:
                return 'top'
            elif abs(x - (WIDTH - 1)) < tol:
                return 'right'
            elif abs(y - (HEIGHT - 1)) < tol:
                return 'bottom'
            elif abs(x - 0) < tol:
                return 'left'
            else:
                return None

        start_side = get_boundary_side(start_point)
        end_side = get_boundary_side(end_point)

        # If the two points are on different sides, determine the desired corner.
        desired_corner = None
        if start_side and end_side and start_side != end_side:
            desired_corners = {
                frozenset({'left', 'top'}): (0, 0),
                frozenset({'top', 'right'}): (WIDTH - 1, 0),
                frozenset({'right', 'bottom'}): (WIDTH - 1, HEIGHT - 1),
                frozenset({'bottom', 'left'}): (0, HEIGHT - 1)
            }
            key = frozenset({start_side, end_side})
            desired_corner = desired_corners.get(key, None)

        # Find the indices of start and end in the game boundary.
        def find_index_in_boundary(point):
            for i, bp in enumerate(self.boundary_points):
                if abs(bp[0] - point[0]) < 1 and abs(bp[1] - point[1]) < 1:
                    return i
            return None

        start_index = find_index_in_boundary(start_point)
        end_index = find_index_in_boundary(end_point)
        if start_index is None or end_index is None:
            # Fallback if indices not found.
            self.filled_areas.append(self.temp_points + [start_point])
            self.drawing = False
            self.temp_points = []
            self.current_direction = None
            return

        bp = self.boundary_points
        n = len(bp)

        # Get two candidate boundary segments (the boundary is circular).
        if start_index <= end_index:
            seg1 = bp[start_index:end_index + 1]
        else:
            seg1 = bp[start_index:] + bp[:end_index + 1]
        # The other segment is the complementary part.
        if start_index <= end_index:
            seg2 = bp[end_index:] + bp[:start_index + 1]
        else:
            seg2 = bp[end_index:start_index + 1]

        # Choose the segment that contains the desired corner.
        def contains_point(segment, point):
            for p in segment:
                if abs(p[0] - point[0]) < 1 and abs(p[1] - point[1]) < 1:
                    return True
            return False

        if desired_corner is not None:
            chosen_segment = seg1 if contains_point(seg1, desired_corner) else seg2
        else:
            # Fallback: choose the segment with fewer points.
            chosen_segment = seg1 if len(seg1) < len(seg2) else seg2

        # Build two candidate polygons:
        # Option A: drawn path in original order + chosen boundary segment reversed.
        polygon1 = self.temp_points + chosen_segment[::-1]
        # Option B: drawn path in reverse order + chosen boundary segment.
        polygon2 = self.temp_points[::-1] + chosen_segment

        # Now choose the polygon using a test point.
        # Instead of a perpendicular offset, offset toward the desired corner.
        mid_x = (start_point[0] + end_point[0]) / 2
        mid_y = (start_point[1] + end_point[1]) / 2
        if desired_corner is not None:
            vec_x = desired_corner[0] - mid_x
            vec_y = desired_corner[1] - mid_y
            length = math.hypot(vec_x, vec_y)
            if length != 0:
                offset_x = (vec_x / length) * 5  # small offset of 5 pixels
                offset_y = (vec_y / length) * 5
            else:
                offset_x, offset_y = 0, 0
            test_point = (mid_x + offset_x, mid_y + offset_y)
        else:
            # Fallback: use a perpendicular offset.
            dx = end_point[1] - start_point[1]
            dy = start_point[0] - end_point[0]
            length = math.hypot(dx, dy)
            if length == 0:
                offset_x, offset_y = 0, 0
            else:
                offset_x = (dx / length) * 5
                offset_y = (dy / length) * 5
            test_point = (mid_x + offset_x, mid_y + offset_y)

        if point_in_polygon(test_point, polygon1):
            final_polygon = polygon1
        elif point_in_polygon(test_point, polygon2):
            final_polygon = polygon2
        else:
            # As a last resort, choose the polygon with the smaller area.
            area1 = self.calculate_polygon_area(polygon1)
            area2 = self.calculate_polygon_area(polygon2)
            final_polygon = polygon1 if area1 < area2 else polygon2

        final_polygon.append(final_polygon[0])  # Close the polygon.
        self.filled_areas.append(final_polygon)
        self.drawing = False
        self.temp_points = []
        self.current_direction = None
        self.boundary_points = self.generate_boundary_points()  # Refresh boundary points.


    def draw(self, surface):
        self.update_sparks()  # Update spark positions

        # Draw sparks
        for spark in self.sparks:
            t = (spark['lifetime'] / 5 + spark['color_offset']) % (2 * math.pi)
            color = rainbow_color(t)
            size = min(4, spark['lifetime'] / 3)  # Reduce spark size
            pygame.draw.circle(surface, color, (int(spark['x']), int(spark['y'])), max(1, int(size)))

        # Draw the player
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 6)

        # Draw temporary path
        if self.drawing and len(self.temp_points) > 1:
            for i in range(len(self.temp_points) - 1):
                t = (i / 10 + self.color_offset) % (2 * math.pi)
                color = rainbow_color(t)
                pygame.draw.line(surface, color, self.temp_points[i], self.temp_points[i+1], self.thickness)

        # Draw filled areas (efficiently, with transparency)
        fill_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)  # Use SRCALPHA
        for area in self.filled_areas:
            if len(area) >= 3:
                pygame.draw.polygon(fill_surface, (*rainbow_color(self.color_offset), 100), area)

                # Draw the boundary (outline) of the filled area
                for i in range(len(area) - 1):
                    t = (i / 10 + self.color_offset) % (2 * math.pi)
                    border_color = rainbow_color(t)
                    pygame.draw.line(surface, border_color, area[i], area[i+1], self.thickness)

        surface.blit(fill_surface, (0, 0)) #blit once
        self.color_offset += 0.05  # Animate the rainbow colors

class Qix:
    def __init__(self, x=None, y=None):
        # Start near center if no position is given
        self.x = x if x is not None else WIDTH // 2
        self.y = y if y is not None else HEIGHT // 2
        self.dx = random.choice([-3, -2, 2, 3])
        self.dy = random.choice([-3, -2, 2, 3])
        self.size = 30
        self.rotation = 0
        self.rotation_speed = random.choice([-0.05, -0.03, 0.03, 0.05])
        self.points = self.generate_points()
        self.color_offset = random.random() * 10

    def generate_points(self):
        """Generate points for a spiky (non-uniform) circular shape."""
        points = []
        num_points = 10
        for i in range(num_points):
            angle = self.rotation + 2 * math.pi * i / num_points
            # Vary radius for a spikey effect
            r = self.size * (0.5 + 0.5 * math.sin(i * 1.5))
            x = self.x + r * math.cos(angle)
            y = self.y + r * math.sin(angle)
            points.append((x, y))
        return points

    def update(self, filled_areas):
        # Update position and handle wall bounces
        self.x += self.dx
        self.y += self.dy

        if self.x - self.size < 0 or self.x + self.size > WIDTH:
            self.dx *= -1
        if self.y - self.size < 0 or self.y + self.size > HEIGHT:
            self.dy *= -1

        # Update rotation for a shimmering effect
        self.rotation += self.rotation_speed

        # Check collision with filled areas using a simple check:
        for area in filled_areas:
            if point_in_polygon((self.x, self.y), area):
                # Bounce in a new random direction upon collision with a filled area
                self.dx = random.choice([-3, -2, 2, 3])
                self.dy = random.choice([-3, -2, 2, 3])
                break

        self.points = self.generate_points()
        self.color_offset += 0.1

    def draw(self, surface):
        # Draw the Qix shape with a rainbow outline
        for i in range(len(self.points) - 1):
            t = (i / 5 + self.color_offset) % (2 * math.pi)
            color = rainbow_color(t)
            pygame.draw.line(surface, color, self.points[i], self.points[i+1], 3)
        pygame.draw.line(surface,
                         rainbow_color((len(self.points) / 5 + self.color_offset) % (2 * math.pi)),
                         self.points[-1], self.points[0], 3)

        # Draw inner glow (using semi-transparent circles)
        for r in range(10, 0, -2):
            t = (r / 5 + self.color_offset * 2) % (2 * math.pi)
            color = (*rainbow_color(t), 20)
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r)

# --------------------------- Game Object Creation / Utility Functions (Moved outside Qix class)---------------------------
def create_enemies(level):
    """Create a list of Qix enemies based on the current level."""
    num_enemies = level + 1  # e.g., Level 1 = 2 enemies, Level 2 = 3 enemies, etc.
    enemies = []
    for i in range(num_enemies):
        # Distribute enemies around the center
        angle = 2 * math.pi * i / num_enemies
        x = WIDTH // 2 + int((WIDTH // 4) * math.cos(angle))
        y = HEIGHT // 2 + int((HEIGHT // 4) * math.sin(angle))
        qix = Qix(x, y)
        qix.size = 25 + random.randint(-5, 5)
        enemies.append(qix)
    return enemies

def check_collision(player, enemies):
    """Check if the player's circle or its drawing path collides with any enemy."""
    for qix in enemies:
        # Check collision with player circle (simple circle-to-circle collision)
        if math.hypot(player.x - qix.x, player.y - qix.y) < qix.size + 6:  # 6 is the player radius
            return True

        # When drawing, check if any segment is close enough to an enemy's center
        if player.drawing and len(player.temp_points) > 1:
            for i in range(len(player.temp_points) - 1):
                p1 = player.temp_points[i]
                p2 = player.temp_points[i + 1]
                dist = point_to_line_distance(qix.x, qix.y, p1[0], p1[1], p2[0], p2[1])
                if dist < qix.size:
                    return True
    return False

# --------------------------- End-of-Game Screens ---------------------------
def display_message(surface, message):
    """Display a centered message on the screen."""
    font = pygame.font.SysFont(None, 96)
    text_surface = font.render(message, True, WHITE)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surface.blit(text_surface, text_rect)
    pygame.display.flip()
    # Pause for a few seconds
    pygame.time.wait(3000)

# --------------------------- Main Game Loop ---------------------------
def main():  # Moved main function outside of the Qix Class
    # Initialize game state variables
    level = 1
    total_area = WIDTH * HEIGHT
    player = Player()
    enemies = create_enemies(level)
    game_over = False
    game_win = False

    while True:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            # Start drawing with spacebar
            if event.type == KEYDOWN:
                if event.key == K_SPACE and not player.drawing:
                    player.start_drawing()
                # Press R to restart after game over/win
                if event.key == K_r and (game_over or game_win):
                    return  # Restart by returning from main()

        # --- Get Key States for Movement ---
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        if keys[K_LEFT]:
            dx = -1
        if keys[K_RIGHT]:
            dx = 1
        if keys[K_UP]:
            dy = -1
        if keys[K_DOWN]:
            dy = 1

        # Only update game state if not game over or win
        if not (game_over or game_win):
            player.move(dx, dy)

            # Update each enemy
            for qix in enemies:
                qix.update(player.filled_areas)

            # Check for collision events (player or drawing hit an enemy)
            if check_collision(player, enemies):
                game_over = True
                player.stop_drawing()  # Stop drawing if collision happens

            # Check win condition by the percentage of fill area
            fill_percentage = calculate_area_percentage(player.filled_areas, total_area)
            if fill_percentage >= TARGET_FILL_PERCENTAGE:
                game_win = True

        # --- Drawing Section ---
        screen.fill(BLACK)
        draw_game_boundary(screen)

        for qix in enemies:
            qix.draw(screen)
        player.draw(screen)

        # Display score/fill percentage on top-left
        font = pygame.font.SysFont(None, 36)
        info = font.render(f"Fill: {fill_percentage:0.1f}%   Level: {level}", True, WHITE)
        screen.blit(info, (10, 10))

        # Display controls
        controls = font.render("SPACE to start drawing | Arrow keys to move | R to restart", True, WHITE)
        screen.blit(controls, (10, HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)

        # --- End-of-Game Checks ---
        if game_over:
            display_message(screen, "Game Over! Press R to Restart")
            #wait for input to prevent the game from immediately resetting
            waiting_for_input = True
            while waiting_for_input:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == KEYDOWN:
                        if event.key == K_r:
                            waiting_for_input = False

        if game_win:
            display_message(screen, "You Win! Press R to Restart")
            #wait for input to prevent the game from immediately resetting
            waiting_for_input = True
            while waiting_for_input:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == KEYDOWN:
                        if event.key == K_r:
                            waiting_for_input = False
if __name__ == '__main__':
    main()
