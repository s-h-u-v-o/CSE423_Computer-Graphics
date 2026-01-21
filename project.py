from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
cheat_mode = False  # Toggle with C key


# ==========================================
# GLOBAL GAME STATE
# ==========================================
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
GRID_LENGTH = 1200
WALL_HEIGHT = 100
fovY = 60

# Player State
player = {
    "x": 0, "y": 0, "angle": 90, 
    "health": 100, "max_health": 100,
    "ammo": 20, "speed": 6, 
    "cooldown": 0,
}

# Global Variables
score = 0
tick = 0
airstrike_cd = 0
low_hp_flash = 0


BOSS_WAVE_INTERVAL = 5
BOSS_MAX_HEALTH = 800
BOSS_MOVE_SPEED = 0.45
BOSS_SHOOT_CD = 35
BOSS_HIT_RADIUS = 45  
BOSS_SIZE = 2.5       

AIRSTRIKE_COST = 800
AIRSTRIKE_COOLDOWN = 3600
AIRSTRIKE_BOMBS = 6


# Wave / Combo / Rapid Fire 
wave = 1
MAX_ACTIVE_ENEMIES = 5
wave_queue = 0  # remaining enemies to spawn in current wave beyond those already active

combo_multiplier = 1
combo_timer = 0
COMBO_TIMEOUT = 600  # frames before combo resets

rapid_fire_timer = 0  # frames remaining for rapid-fire powerup

camera_mode = 0 # 0 = Default, 1 = Third Person (Behind)
game_over = False 

bullets = [] 
enemies = [] 
pickups = [] 
treads = []  
explosions = [] 
obstacles = [] 

# Bombardment Variables
bomb_zones = [] 
bomb_timer = 800 

# Radar Variables
radar_state = {
    "cooldown": 0,
    "max_cooldown": 999, 
    "active": False,     # Is the pulse currently expanding?
    "radius": 0,
    "max_radius": 1000,  # How far the ping goes
    "speed": 5           # Expansion speed
}

# Constants
BULLET_SPEED = 3
ENEMY_COUNT = 6
MAX_TREAD_LIFE = 300
ENEMY_SIGHT_RANGE = 200 
MAX_OBSTACLES = 30 


#Reinforements:
def Reinforcements():
    global airstrike_cd, bomb_zones

    if airstrike_cd > 0:
        return

    # Drop bombs on enemies
    for e in enemies:
        for i in range(AIRSTRIKE_BOMBS):
            ox = random.randint(-60, 60)
            oy = random.randint(-60, 60)

            bomb_zones.append({
                "x": e['x'] + ox,
                "y": e['y'] + oy,
                "radius": 120,
                "state": "warning",
                "timer": 60,
                "bomb_z": 600,
                "source": "airstrike"  
            })


    airstrike_cd = AIRSTRIKE_COOLDOWN


# Terrain Setup
TERRAIN_ZONES = []

def generate_terrain():
    zones = []
    
    road_width = 200
    zones.append((-road_width, road_width, -GRID_LENGTH, GRID_LENGTH, 'road'))
    zones.append((-GRID_LENGTH, GRID_LENGTH, -road_width, road_width, 'road'))
    
    grid_size = 100 
    
    for x in range(-GRID_LENGTH, GRID_LENGTH, grid_size):
        for y in range(-GRID_LENGTH, GRID_LENGTH, grid_size):
            
            min_x, max_x = x, x + grid_size
            min_y, max_y = y, y + grid_size
            
            overlap_v = not (max_x <= -road_width or min_x >= road_width)
            overlap_h = not (max_y <= -road_width or min_y >= road_width)
            
            if not overlap_v and not overlap_h:
                chance = random.random()
                if chance < 0.2: 
                    zones.append((min_x, max_x, min_y, max_y, 'magma'))
                elif chance < 0.4:
                    zones.append((min_x, max_x, min_y, max_y, 'mud'))
                
    return zones

TERRAIN_ZONES = generate_terrain()

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def draw_text(x, y, text, color=(1,1,1)):
    glColor3f(color[0], color[1], color[2])
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch)) # type: ignore
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def check_terrain(x, y):
    # Returns: 'grass', 'mud', 'magma', 'road'
    for tx1, tx2, ty1, ty2, t_type in TERRAIN_ZONES:
        if tx1 <= x <= tx2 and ty1 <= y <= ty2:
            return t_type
    return 'grass'

def draw_minimap():
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    map_size = 200
    margin = 70
    start_x = WINDOW_WIDTH - map_size - margin
    start_y = WINDOW_HEIGHT - map_size - margin+20
    scale = map_size / float(GRID_LENGTH * 2)

    # Background
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex3f(start_x, start_y, 0)
    glVertex3f(start_x + map_size, start_y, 0)
    glVertex3f(start_x + map_size, start_y + map_size, 0)
    glVertex3f(start_x, start_y + map_size, 0)
    glEnd()

    # Border (4 thin quads)
    border = 3
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    # bottom
    glVertex3f(start_x, start_y, 0)
    glVertex3f(start_x + map_size, start_y, 0)
    glVertex3f(start_x + map_size, start_y + border, 0)
    glVertex3f(start_x, start_y + border, 0)
    # top
    glVertex3f(start_x, start_y + map_size - border, 0)
    glVertex3f(start_x + map_size, start_y + map_size - border, 0)
    glVertex3f(start_x + map_size, start_y + map_size, 0)
    glVertex3f(start_x, start_y + map_size, 0)
    # left
    glVertex3f(start_x, start_y, 0)
    glVertex3f(start_x + border, start_y, 0)
    glVertex3f(start_x + border, start_y + map_size, 0)
    glVertex3f(start_x, start_y + map_size, 0)
    # right
    glVertex3f(start_x + map_size - border, start_y, 0)
    glVertex3f(start_x + map_size, start_y, 0)
    glVertex3f(start_x + map_size, start_y + map_size, 0)
    glVertex3f(start_x + map_size - border, start_y + map_size, 0)
    glEnd()

    def to_map_x(wx):
        return start_x + (wx + GRID_LENGTH) * scale
    def to_map_y(wy):
        return start_y + (wy + GRID_LENGTH) * scale

    # Obstacles
    glPointSize(3)
    glColor3f(0.8, 0.7, 0.5)
    glBegin(GL_POINTS)
    for o in obstacles:
        glVertex3f(to_map_x(o['x']), to_map_y(o['y']), 0)
    glEnd()

    # Enemies (with radar gating)
    if radar_state.get('active', False):
        glPointSize(5)
        glBegin(GL_POINTS)
        glColor3f(0.6, 0.2, 0.8)
        for e in enemies:
            glVertex3f(to_map_x(e['x']), to_map_y(e['y']), 0)
        glEnd()

    # Player
    glPointSize(7)
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_POINTS)
    glVertex3f(to_map_x(player['x']), to_map_y(player['y']), 0)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def check_wall_collision(x, y, radius):
    for o in obstacles:
        half_size = o['size'] / 2 + radius
        if abs(x - o['x']) < half_size and abs(y - o['y']) < half_size:
            return True
    return False

def spawn_enemy():
    spawn_range = GRID_LENGTH - 100
    ex = random.randint(-spawn_range, spawn_range)
    ey = random.randint(-spawn_range, spawn_range)
    if math.sqrt((ex - player['x'])**2 + (ey - player['y'])**2) < 400 or check_wall_collision(ex, ey, 30):
        return spawn_enemy()
    
    # Assign Random Type
    ai_types = ['aggressive', 'defensive', 'sniper']
    e_type = random.choice(ai_types)
    
    # Color Code
    if e_type == 'aggressive': col = (0.9, 0.1, 0.1) # Red
    elif e_type == 'defensive': col = (0.1, 0.8, 0.1) # Green
    else: col = (0.9, 0.9, 0.1) # Yellow

    enemies.append({
        "x": ex, "y": ey, 
        "angle": random.choice([0, 90, 180, 270]),
        "health": 100, "max_health": 100,
        "cooldown": 0, 
        "color": col,
        "type": e_type,
        "state_timer": random.randint(50, 200),
        "in_danger_timer": 0 
    })



def start_wave(new_wave=None):
    global wave, wave_queue
    if new_wave is not None:
        wave = new_wave

    # Total enemies for this wave grows; keep "active at once" within 3-5 by using a queue
    total = 3 + (wave - 1) * 2
    if total < 3: total = 3

    enemies.clear()
    #  BOSS WAVE 
    if wave % BOSS_WAVE_INTERVAL == 0:
        spawn_range = GRID_LENGTH - 300
        bx = random.randint(-spawn_range, spawn_range)
        by = random.randint(-spawn_range, spawn_range)

        enemies.append({
            "x": bx, "y": by,
            "angle": 0,
            "health": BOSS_MAX_HEALTH,
            "max_health": BOSS_MAX_HEALTH,
            "cooldown": 0,
            "color": (1.0, 0.2, 0.2),
            "type": "boss",
            "state_timer": 0,
            "in_danger_timer": 0,
            "enraged": False
            
        })

        wave_queue = 0
        return

    wave_queue = total

    # Spawn initial batch up to MAX_ACTIVE_ENEMIES
    initial = MAX_ACTIVE_ENEMIES
    if wave_queue < initial: initial = wave_queue
    for _ in range(initial):
        spawn_enemy()
    wave_queue -= initial

def spawn_pickup():
    spawn_range = GRID_LENGTH - 100
    px = random.randint(-spawn_range, spawn_range)
    py = random.randint(-spawn_range, spawn_range)
    if check_wall_collision(px, py, 20):
        spawn_pickup()
        return

    r = random.random()
    if r < 0.4:
        p_type = 'health'
    elif r < 0.85:
        p_type = 'ammo'
    else:
        p_type = 'rapid'

    pickups.append({"x": px, "y": py, "type": p_type})

def spawn_explosion(x, y):
    particles = []
    for _ in range(15): 
        particles.append({
            "x": x, "y": y, "z": 15, 
            "dx": random.uniform(-8, 8),
            "dy": random.uniform(-8, 8),
            "dz": random.uniform(5, 15),
            "life": 30
        })
    
    explosions.append({
        "x": x, "y": y, 
        "life": 30,     
        "max_life": 30,
        "particles": particles
    })

def generate_obstacles():
    obstacles.clear()
    count = 20
    
    for _ in range(count):
        ox = random.randint(-GRID_LENGTH + 100, GRID_LENGTH - 100)
        oy = random.randint(-GRID_LENGTH + 100, GRID_LENGTH - 100)
        
        if math.sqrt(ox**2 + oy**2) < 300: 
            continue
            
        obstacles.append({
            'x': ox, 
            'y': oy, 
            'size': 80, 
            'health': 2 
        })

def trigger_bombardment():
    for _ in range(3):
        bx = random.randint(-GRID_LENGTH + 200, GRID_LENGTH - 200)
        by = random.randint(-GRID_LENGTH + 200, GRID_LENGTH - 200)
        
        bomb_zones.append({
            'x': bx,
            'y': by,
            'state': 'warning', 
            'timer': 120,       
            'bomb_z': 800,      
            'radius': 150       
        })

def reset_game():
    global player, score, enemies, bullets, bomb_zones, game_over
    player['health'] = 100
    player['x'] = 0
    player['y'] = 0
    player['angle'] = 90
    player['ammo'] = 20
    score = 0
    enemies.clear()
    bullets.clear()
    bomb_zones.clear()
    generate_obstacles()
    start_wave(1)
    game_over = False
    print("Game Restarted!")

# Radar Trigger
def trigger_radar():
    if radar_state['cooldown'] <= 0:
        radar_state['active'] = True
        radar_state['radius'] = 0
        radar_state['cooldown'] = radar_state['max_cooldown']


# DRAWING FUNCTIONS

def draw_single_bullet():
    glPushMatrix()
    gluCylinder(gluNewQuadric(), 3, 3, 12, 10, 2)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 12)
    glScalef(1, 1, 1.5)
    gluSphere(gluNewQuadric(), 3, 10, 10)
    glPopMatrix()

def draw_bullet_icon():
    glColor3f(1.0, 0.8, 0.0) 
    glPushMatrix()
    glTranslatef(-4, 0, 0)
    draw_single_bullet()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(4, 0, 0)
    draw_single_bullet()
    glPopMatrix()

def draw_heart_icon():
    glPushMatrix()
    glColor3f(1.0, 0.0, 0.2) 
    glScalef(1.5, 1.5, 1.5)  
    glPushMatrix()
    glTranslatef(-3, 0, 5)
    gluSphere(gluNewQuadric(), 4, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(3, 0, 5)
    gluSphere(gluNewQuadric(), 4, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, -5) 
    gluCylinder(gluNewQuadric(), 0, 5.5, 10, 10, 2) 
    glPopMatrix()
    glPopMatrix()

def draw_pickups():
    global tick
    for p in pickups:
        glPushMatrix()
        glTranslatef(p['x'], p['y'], 15)
        glRotatef(player['angle'] * 2, 0, 0, 1) 
        bob_height = math.sin(tick * 0.05) * 5
        glTranslatef(0, 0, bob_height)
        if p['type'] == 'ammo':
            draw_bullet_icon()
        elif p['type'] == 'health':
            draw_heart_icon()
        elif p['type'] == 'rapid':
            # Rapid-fire pickup: cyan sphere
            glColor3f(0.2, 1.0, 1.0)
            gluSphere(gluNewQuadric(), 10, 10, 10)
        glPopMatrix()

def draw_health_bar(x, y, z, health, max_health):
    bar_width = 50
    bar_height = 6
    health_pct = max(0, min(1, health / max_health))

    # ==============================
    # FIRST PERSON MODE (HUD)
    # ==============================
    if camera_mode == 1:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # PLAYER HUD 
        if x == player['x'] and y == player['y']:
            sx = 20
            sy = WINDOW_HEIGHT - 70
            bw = 160
            bh = 12

        # ENEMY LIST (right side under minimap)
        else:
            idx = enemies.index(next(e for e in enemies if e['x']==x and e['y']==y))
            sx = WINDOW_WIDTH - 240
            sy = WINDOW_HEIGHT - 260 - idx * 15
            bw = 140
            bh = 8

        # Background
        glColor3f(0,0,0)
        glBegin(GL_QUADS)
        glVertex3f(sx, sy, 0)
        glVertex3f(sx+bw, sy, 0)
        glVertex3f(sx+bw, sy+bh, 0)
        glVertex3f(sx, sy+bh, 0)
        glEnd()

        # Fill
        if x == player['x']:
            glColor3f(0,1,0)
        else:
            glColor3f(1,0,0)

        fw = bw * health_pct
        glBegin(GL_QUADS)
        glVertex3f(sx, sy, 0)
        glVertex3f(sx+fw, sy, 0)
        glVertex3f(sx+fw, sy+bh, 0)
        glVertex3f(sx, sy+bh, 0)
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        return

    # ==============================
    # THIRD PERSON (world-space bars)
    # ==============================
    glPushMatrix()
    glTranslatef(x, y, z + 80)

    glBegin(GL_QUADS)

    # Background
    glColor3f(0, 0, 0)
    glVertex3f(-bar_width/2, -2, 0)
    glVertex3f(bar_width/2, -2, 0)
    glVertex3f(bar_width/2, bar_height+2, 0)
    glVertex3f(-bar_width/2, bar_height+2, 0)

    # Health
    glColor3f(0, 1, 0)
    current = bar_width * health_pct
    glVertex3f(-bar_width/2, 0, 0)
    glVertex3f(-bar_width/2 + current, 0, 0)
    glVertex3f(-bar_width/2 + current, bar_height, 0)
    glVertex3f(-bar_width/2, bar_height, 0)

    glEnd()
    glPopMatrix()



def draw_tank(x, y, angle, color, is_player=False):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glRotatef(angle, 0, 0, 1) 
    glPushMatrix()
    glColor3f(color[0], color[1], color[2])
    glScalef(1.5, 1, 0.5) 
    glTranslatef(0, 0, 15) 
    glutSolidCube(30)
    glPopMatrix()
    glPushMatrix()
    glColor3f(color[0]*0.8, color[1]*0.8, color[2]*0.8) 
    glTranslatef(0, 0, 25)
    gluSphere(gluNewQuadric(), 12, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.2)
    glTranslatef(5, 0, 25) 
    glRotatef(90, 0, 1, 0) 
    gluCylinder(gluNewQuadric(), 3, 3, 35, 8, 8)
    glPopMatrix()
    glPopMatrix()

def draw_treads():
    glPointSize(4)
    glBegin(GL_POINTS)
    for t in treads:
        alpha = t['life'] / MAX_TREAD_LIFE
        glColor3f(0.1 * alpha, 0.1 * alpha, 0.1 * alpha)
        glVertex3f(t['x'], t['y'], 1)
    glEnd()

def draw_bullets():
    glColor3f(1, 1, 0)
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], 25)
        gluSphere(gluNewQuadric(), 3, 5, 5)
        glPopMatrix()

def draw_explosions():
    for exp in explosions:
        if exp['life'] > 0:
            glPushMatrix()
            glTranslatef(exp['x'], exp['y'], 20)
            
            age_ratio = 1.0 - (exp['life'] / exp['max_life'])
            scale = 0.5 + (age_ratio * 2.0) 
            
            red = 1.0
            green = 0.8 * (1.0 - age_ratio) 
            blue = 0.0
            
            glColor3f(red, green, blue)
            glScalef(scale, scale, scale)
            gluSphere(gluNewQuadric(), 15, 10, 10)
            glPopMatrix()

        for p in exp['particles']:
            glPushMatrix()
            glTranslatef(p['x'], p['y'], p['z'])
            life_ratio = p['life'] / 30.0
            glColor3f(1.0, 0.5 * life_ratio, 0.0) 
            glScalef(life_ratio, life_ratio, life_ratio)
            gluSphere(gluNewQuadric(), 4, 6, 6)
            glPopMatrix()

def draw_obstacles():
    for o in obstacles:
        if o['health'] == 2:
            glColor3f(0.8, 0.7, 0.5) 
        else:
            glColor3f(0.6, 0.5, 0.4) 
            
        glPushMatrix()
        glTranslatef(o['x'], o['y'], 25) 
        glScalef(o['size'], o['size'], 50)
        glutSolidCube(1)
        glPopMatrix()

def draw_terrain():
    glBegin(GL_QUADS)
    glColor3f(0.1, 0.6, 0.1) 
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, -1)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, -1)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, -1)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, -1)
    glEnd()

    glBegin(GL_QUADS)
    for tx1, tx2, ty1, ty2, t_type in TERRAIN_ZONES:
        if t_type == 'magma': glColor3f(0.8, 0.2, 0.0) 
        elif t_type == 'mud': glColor3f(0.4, 0.2, 0.1) 
        elif t_type == 'road': glColor3f(0.5, 0.5, 0.5) 
        
        glVertex3f(tx1, ty2, 1) 
        glVertex3f(tx2, ty2, 1)
        glVertex3f(tx2, ty1, 1)
        glVertex3f(tx1, ty1, 1)
    glEnd()

def draw_walls():
    wall_thickness = 50
    glColor3f(0.3, 0.3, 0.3) 
    glPushMatrix()
    glTranslatef(0, GRID_LENGTH + wall_thickness/2, WALL_HEIGHT/2)
    glScalef(GRID_LENGTH * 2 + wall_thickness * 2, wall_thickness, WALL_HEIGHT)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, -GRID_LENGTH - wall_thickness/2, WALL_HEIGHT/2)
    glScalef(GRID_LENGTH * 2 + wall_thickness * 2, wall_thickness, WALL_HEIGHT)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-GRID_LENGTH - wall_thickness/2, 0, WALL_HEIGHT/2)
    glScalef(wall_thickness, GRID_LENGTH * 2, WALL_HEIGHT)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(GRID_LENGTH + wall_thickness/2, 0, WALL_HEIGHT/2)
    glScalef(wall_thickness, GRID_LENGTH * 2, WALL_HEIGHT)
    glutSolidCube(1)
    glPopMatrix()

def draw_bombardment():
    global tick
    for b in bomb_zones:
        if b['state'] == 'warning':
            # Warning ring drawn as blinking points 
            if (tick // 10) % 2 == 0:
                glColor3f(1, 0, 0)
            else:
                glColor3f(0.5, 0, 0)

            glPushMatrix()
            glTranslatef(b['x'], b['y'], 5)

            glPointSize(3)
            glBegin(GL_POINTS)
            steps = 90
            r = b['radius']
            for i in range(steps):
                ang = 2 * math.pi * i / steps
                glVertex3f(math.cos(ang) * r, math.sin(ang) * r, 0)

            # Crosshair (as points along axes)
            for k in range(-20, 21):
                t = (k / 20.0) * r
                glVertex3f(t, 0, 0)
                glVertex3f(0, t, 0)
            glEnd()

            glPopMatrix()

        elif b['state'] == 'falling':
            glPushMatrix()
            glTranslatef(b['x'], b['y'], b['bomb_z'])
            glColor3f(0, 0, 0)
            gluSphere(gluNewQuadric(), 15, 10, 10)
            glPopMatrix()

            # Ground shadow as a small sphere squash 
            glPushMatrix()
            glTranslatef(b['x'], b['y'], 2)
            glColor3f(0.2, 0.2, 0.2)
            scale = 1.0 - (b['bomb_z'] / 800.0)
            glScalef(scale, scale, 0.1)
            gluSphere(gluNewQuadric(), 15, 10, 10)
            glPopMatrix()

        elif b['state'] == 'burning':
            glPushMatrix()
            glTranslatef(b['x'], b['y'], 2)

            if tick % 5 == 0:
                glColor3f(1.0, 0.6, 0.0)
            else:
                glColor3f(1.0, 0.2, 0.0)

            glPointSize(4)
            glBegin(GL_POINTS)
            for _ in range(120):
                rx = random.uniform(-b['radius'], b['radius'])
                ry = random.uniform(-b['radius'], b['radius'])
                if rx*rx + ry*ry <= b['radius']*b['radius']:
                    glVertex3f(rx, ry, 0)
            glEnd()

            glPopMatrix()

# Draw Radar Pulse

def draw_radar_effect():
    if radar_state['active']:
        glPushMatrix()
        glTranslatef(player['x'], player['y'], 5)

        alpha = 1.0 - (radar_state['radius'] / radar_state['max_radius'])
        glColor3f(0, 1 * alpha, 1 * alpha)

        glPointSize(3)
        glBegin(GL_POINTS)
        steps = 80
        r = radar_state['radius']
        for i in range(steps):
            ang = 2 * math.pi * i / steps
            glVertex3f(math.cos(ang) * r, math.sin(ang) * r, 0)
        glEnd()

        glPopMatrix()

# ==========================================
# LOGIC & INPUT
# ==========================================

def update_game():
    global player, tick, score, bomb_timer, bomb_zones, game_over, cheat_mode
    global airstrike_cd
    global low_hp_flash
    
    if game_over: return
    
    tick += 1
    # CHEAT MODE
    if cheat_mode:

        if player['health'] < 1:
            player['health'] = 1
        #player['ammo'] = 10000

    if cheat_mode and len(enemies) > 0:
        target = enemies[0]

        dx = target['x'] - player['x']
        dy = target['y'] - player['y']
        dist = math.sqrt(dx*dx + dy*dy)

        target_angle = math.degrees(math.atan2(dy, dx))
        player['angle'] = target_angle


        DESIRED_RANGE = 350 # stops to shoot 

        if dist > DESIRED_RANGE:
            rad = math.radians(player['angle'])
            nx = player['x'] + math.cos(rad) * 0.8
            ny = player['y'] + math.sin(rad) * 0.8

            hit_wall = False
            for o in obstacles[:]:
                if abs(o['x'] - nx) < o['size']/2 + 25 and abs(o['y'] - ny) < o['size']/2 + 25:
                    spawn_explosion(o['x'], o['y'])
                    obstacles.remove(o)
                    hit_wall = True
                    break

            # Always move forward after smashing
            player['x'] = nx
            player['y'] = ny



        # Fire only when in range
        if dist < DESIRED_RANGE + 50 and player['cooldown'] <= 0:
            rad = math.radians(player['angle'])
            bullets.append({
                "x": player['x'], "y": player['y'],
                "dx": math.cos(rad) * BULLET_SPEED,
                "dy": math.sin(rad) * BULLET_SPEED,
                "owner": "player"
            })
            player['cooldown'] = 100

    # -----------------------------

    #  COMBO / RAPID TIMERS 
    global combo_timer, combo_multiplier, rapid_fire_timer, wave, wave_queue
    if combo_timer > 0:
        combo_timer -= 1
    else:
        combo_multiplier = 0
    if rapid_fire_timer > 0:
        rapid_fire_timer -= 1

    # RADAR LOGIC 
    if radar_state['active']:
        radar_state['radius'] += radar_state['speed']
        if radar_state['radius'] >= radar_state['max_radius']:
            radar_state['active'] = False
    
    if radar_state['cooldown'] > 0:
        radar_state['cooldown'] -= 1
    # 

    # Bombardment
    bomb_timer -= 1
    if bomb_timer <= 0:
        trigger_bombardment()
        bomb_timer = 800 + random.randint(0, 400) 

    for b in bomb_zones:
        if b['state'] == 'warning':
            b['timer'] -= 1
            if b['timer'] <= 0:
                b['state'] = 'falling'
        
        elif b['state'] == 'falling':
            b['bomb_z'] -= 25 
            if b['bomb_z'] <= 0:
                b['state'] = 'burning'
                b['timer'] = 250 
                spawn_explosion(b['x'], b['y']) 
                if b.get('source') == 'airstrike':
                    for e in enemies[:]:
                        d = math.sqrt((e['x'] - b['x'])**2 + (e['y'] - b['y'])**2)
                        if d < b['radius']:
                            e['health'] -= 80  
                            if e['health'] <= 0:
                                spawn_explosion(e['x'], e['y'])
                                enemies.remove(e)

                                # wave system restore
                                global wave_queue
                                if wave_queue > 0 and len(enemies) < MAX_ACTIVE_ENEMIES:
                                    spawn_enemy()
                                    wave_queue -= 1

        
        elif b['state'] == 'burning':
            b['timer'] -= 1
            dist = math.sqrt((player['x'] - b['x'])**2 + (player['y'] - b['y'])**2)
            if dist < b['radius'] and not cheat_mode:
                player['health'] -= 0.01 
            
    bomb_zones = [b for b in bomb_zones if not (b['state'] == 'burning' and b['timer'] <= 0)]

    for b in bullets[:]:
        b['x'] += b['dx']
        b['y'] += b['dy']
        
        if abs(b['x']) >= GRID_LENGTH or abs(b['y']) >= GRID_LENGTH:
            bullets.remove(b)
            continue
        
        hit_wall = False
        for o in obstacles:
            collision_dist = o['size']/2 + 5 
            if abs(b['x'] - o['x']) < collision_dist and abs(b['y'] - o['y']) < collision_dist:
                hit_wall = True
                dmg = 2 if b['owner'] == 'player' else 1
                o['health'] -= dmg
                if o['health'] <= 0:
                    spawn_explosion(o['x'], o['y'])
                    obstacles.remove(o)
                    if b['owner'] == 'player': score += 10 
                break
        
        if hit_wall:
            bullets.remove(b)
            continue

        if b['owner'] == 'enemy':
            dist = math.sqrt((b['x'] - player['x'])**2 + (b['y'] - player['y'])**2)
            if dist < 25:
                if not cheat_mode:
                    player['health'] -= 10

                if b in bullets:
                    bullets.remove(b)
                continue


        if b['owner'] == 'player':
            for e in enemies[:]:
                hit_r = BOSS_HIT_RADIUS if e['type'] == 'boss' else 25
                dist = math.sqrt((b['x'] - e['x'])**2 + (b['y'] - e['y'])**2)
                if dist < hit_r:
                    e['health'] -= 50
                    if b in bullets: bullets.remove(b)
                    if e['health'] <= 0:
                        spawn_explosion(e['x'], e['y'])

                        if e['type'] == 'boss':
                            score += 1500
                            for _ in range(5):
                                spawn_pickup()
                        else:
                            # Combo multiplier
                            if combo_timer > 0:
                                combo_multiplier += 1
                            else:
                                combo_multiplier = 1
                            combo_timer = COMBO_TIMEOUT
                            score += 100 * combo_multiplier

                            # Small drop chance
                            r_drop = random.random()
                            if r_drop < 0.20:
                                pickups.append({'x': e['x'], 'y': e['y'], 'type': 'rapid'})
                            elif r_drop < 0.30:
                                pickups.append({'x': e['x'], 'y': e['y'], 'type': 'ammo'})
                            elif r_drop < 0.36:
                                pickups.append({'x': e['x'], 'y': e['y'], 'type': 'health'})

                        enemies.remove(e)

                        if wave_queue > 0 and len(enemies) < MAX_ACTIVE_ENEMIES:
                            spawn_enemy()
                            wave_queue -= 1

                    break

    t_type = check_terrain(player['x'], player['y'])
    if t_type == 'magma' and not cheat_mode: player['health'] -= 0.01 

    for e in enemies:
        # ===== BOSS AI =====
        if e['type'] == 'boss':
            dx = player['x'] - e['x']
            dy = player['y'] - e['y']
            dist = math.sqrt(dx*dx + dy*dy) + 0.0001

            # Rotate toward player
            target_angle = math.degrees(math.atan2(dy, dx))
            diff = (target_angle - e['angle'] + 180) % 360 - 180
            e['angle'] += max(-3, min(3, diff))

            rad = math.radians(e['angle'])
            # ENRAGE CHECK
            if not e['enraged'] and e['health'] < e['max_health'] * 0.5:
                e['enraged'] = True
                e['color'] = (0.7, 0.1, 0.8)   # purple

            if e['enraged']:
                DESIRED_RANGE = 350
            else:
                DESIRED_RANGE = 450


            if dist > DESIRED_RANGE:
                if dist > DESIRED_RANGE:
                    next_x = e['x'] + math.cos(rad) * BOSS_MOVE_SPEED
                    next_y = e['y'] + math.sin(rad) * BOSS_MOVE_SPEED

                    limit = GRID_LENGTH - 60
                    hit_border = abs(next_x) > limit or abs(next_y) > limit

                    hit_obstacle = None
                    for o in obstacles:
                        if abs(next_x - o['x']) < (o['size']/2 + 55) and abs(next_y - o['y']) < (o['size']/2 + 55):
                            hit_obstacle = o
                            break

                    if not hit_border and not hit_obstacle:
                        e['x'], e['y'] = next_x, next_y

                    elif hit_obstacle:
                        # Boss smashes walls
                        hit_obstacle['health'] -= 5
                        if hit_obstacle['health'] <= 0:
                            spawn_explosion(hit_obstacle['x'], hit_obstacle['y'])
                            obstacles.remove(hit_obstacle)

                    else:
                        # Slide along border
                        e['angle'] += 90


            # BOSS SHOOTING 
            e['cooldown'] -= 1
            if dist < DESIRED_RANGE + 50 and abs(diff) < 8 and e['cooldown'] <= 0:
                bullets.append({
                    "x": e['x'], "y": e['y'],
                    "dx": math.cos(rad) * BULLET_SPEED,
                    "dy": math.sin(rad) * BULLET_SPEED,
                    "owner": "enemy"
                })
                if e['enraged']:
                    e['cooldown'] = 80 
                else:
                    e['cooldown'] = 90
                # slower, heavy-tank fire rate

            continue


        in_danger = False
        if check_terrain(e['x'], e['y']) == 'magma':
            in_danger = True
        
        if not in_danger:
            for b in bomb_zones:
                if b['state'] == 'burning':
                    if math.sqrt((e['x'] - b['x'])**2 + (e['y'] - b['y'])**2) < b['radius']:
                        in_danger = True
                        break
        
        if in_danger and not cheat_mode:
            e['health'] -= 0.01
            e['in_danger_timer'] += 1
        else:
            e['in_danger_timer'] = 0

        dx = player['x'] - e['x']
        dy = player['y'] - e['y']
        dist = math.sqrt(dx*dx + dy*dy)
        
        panicking = e['in_danger_timer'] >= 100
        
        if panicking:
            e['state_timer'] -= 1
            if e['state_timer'] <= 0:
                e['angle'] = random.choice([0, 90, 180, 270])
                e['state_timer'] = 50
                e['in_danger_timer'] = 90 
            
            rad = math.radians(e['angle'])
            move_speed = 0.3
            next_x = e['x'] + math.cos(rad) * move_speed
            next_y = e['y'] + math.sin(rad) * move_speed
            
            limit = GRID_LENGTH - 40
            hit_border = abs(next_x) > limit or abs(next_y) > limit
            hit_obstacle = check_wall_collision(next_x, next_y, 30) 
            
            if hit_border or hit_obstacle:
                e['angle'] = random.choice([0, 90, 180, 270])
            else:
                e['x'], e['y'] = next_x, next_y
            
            continue 

        shoot_target = False
        move_speed = 0.2
        
        if e['type'] == 'aggressive':
            if abs(dx) > abs(dy): e['angle'] = 0 if dx > 0 else 180
            else: e['angle'] = 90 if dy > 0 else 270
            
            rad = math.radians(e['angle'])
            next_x = e['x'] + math.cos(rad) * move_speed
            next_y = e['y'] + math.sin(rad) * move_speed
            
            if dist < 300: shoot_target = True
            
        elif e['type'] == 'sniper':
            if abs(dx) > abs(dy): angle_to_player = 0 if dx > 0 else 180
            else: angle_to_player = 90 if dy > 0 else 270
            e['angle'] = angle_to_player
            
            rad = math.radians(e['angle'])
            move_dir = 0 
            
            if dist < 400: move_dir = -1 
            elif dist > 600: move_dir = 1 
            
            next_x = e['x'] + (math.cos(rad) * move_speed * move_dir)
            next_y = e['y'] + (math.sin(rad) * move_speed * move_dir)
            
            if dist < 700: shoot_target = True

        elif e['type'] == 'defensive':
            nearest_wall = None
            min_w_dist = 9999
            for o in obstacles:
                w_dist = math.sqrt((e['x'] - o['x'])**2 + (e['y'] - o['y'])**2)
                if w_dist < min_w_dist:
                    min_w_dist = w_dist
                    nearest_wall = o
            
            if nearest_wall:
                if min_w_dist > 100:
                    wx = nearest_wall['x'] - e['x']
                    wy = nearest_wall['y'] - e['y']
                    if abs(wx) > abs(wy): e['angle'] = 0 if wx > 0 else 180
                    else: e['angle'] = 90 if wy > 0 else 270
                    
                    rad = math.radians(e['angle'])
                    next_x = e['x'] + math.cos(rad) * move_speed
                    next_y = e['y'] + math.sin(rad) * move_speed
                else:
                    if abs(dx) > abs(dy): e['angle'] = 0 if dx > 0 else 180
                    else: e['angle'] = 90 if dy > 0 else 270
                    next_x, next_y = e['x'], e['y'] 
                    
                    if dist < 300: shoot_target = True
            else:
                next_x, next_y = e['x'], e['y']

        limit = GRID_LENGTH - 40
        hit_border = abs(next_x) > limit or abs(next_y) > limit
        hit_obstacle = check_wall_collision(next_x, next_y, 30) 

        if not hit_border and not hit_obstacle:
            e['x'] = next_x
            e['y'] = next_y
        
        e['cooldown'] -= 1
        if shoot_target and e['cooldown'] <= 0:
            rad = math.radians(e['angle'])
            bullets.append({
                "x": e['x'], "y": e['y'],
                "dx": math.cos(rad) * BULLET_SPEED,
                "dy": math.sin(rad) * BULLET_SPEED,
                "owner": "enemy"
            })
            e['cooldown'] = 200 

    for t in treads[:]:
        t['life'] -= 1
        if t['life'] <= 0:
            treads.remove(t)
            
    for exp in explosions[:]:
        exp['life'] -= 1 
        dead_particles = True
        for p in exp['particles']:
            if p['life'] > 0:
                p['x'] += p['dx']
                p['y'] += p['dy']
                p['z'] += p['dz']
                p['dz'] -= 0.5 
                p['life'] -= 1
                dead_particles = False
        if dead_particles and exp['life'] <= 0:
            explosions.remove(exp)

    for p in pickups[:]:
        dist = math.sqrt((player['x'] - p['x'])**2 + (player['y'] - p['y'])**2)
        if dist < 40:
            if p['type'] == 'ammo':
                player['ammo'] += 10
            elif p['type'] == 'health':
                player['health'] = min(player['max_health'], player['health'] + 30)
            elif p['type'] == 'rapid':
                rapid_fire_timer = 1200
            pickups.remove(p)
            spawn_pickup() 

    if player['cooldown'] > 0: player['cooldown'] -= 1
    # --- WAVE PROGRESSION ---
    if len(enemies) == 0 and wave_queue == 0:
        wave += 1
        # Start next wave (spawns initial batch and sets queue)
        start_wave(wave)


    
    if (not cheat_mode) and player['health'] <= 0:
        print("Game Over!")
        spawn_explosion(player['x'], player['y']) 
        game_over = True

    
    if airstrike_cd > 0:
        airstrike_cd -= 1  



    if player['health'] < player['max_health'] * 0.3:
        low_hp_flash += 1
    else:
        low_hp_flash = 0
      

def keyboardListener(key, x, y):
    global cheat_mode
    if key == b'c' or key == b'C':
        cheat_mode = not cheat_mode
        return
    global player, camera_mode, game_over
    
    if game_over:
        if key == b'r' or key == b'R':
            reset_game()
        return 

    # Trigger Radar
    if key == b'e' or key == b'E':
        trigger_radar()

    if key == b'v' or key == b'V':
        camera_mode = (camera_mode + 1) % 2
        return 
        
    t_type = check_terrain(player['x'], player['y'])
    speed = player['speed']
    if t_type == 'mud': speed *= 0.5
    if t_type == 'road': speed *= 1.5

    moved = False
    next_x, next_y = player['x'], player['y']
    
    if camera_mode == 0: 
        new_angle = player['angle']
        if key == b'w' or key == b'W':
            new_angle = 90
            next_y += speed
            moved = True
        elif key == b's' or key == b'S':
            new_angle = 270
            next_y -= speed
            moved = True
        elif key == b'a' or key == b'A':
            new_angle = 180
            next_x -= speed
            moved = True
        elif key == b'd' or key == b'D':
            new_angle = 0
            next_x += speed
            moved = True
        
        player['angle'] = new_angle 

    else: 
        turn_speed = 5 
        
        if key == b'a' or key == b'A':
            player['angle'] += turn_speed
        elif key == b'd' or key == b'D':
            player['angle'] -= turn_speed
        
        rad = math.radians(player['angle'])
        
        if key == b'w' or key == b'W':
            next_x += math.cos(rad) * speed
            next_y += math.sin(rad) * speed
            moved = True
        elif key == b's' or key == b'S':
            next_x -= math.cos(rad) * speed
            next_y -= math.sin(rad) * speed
            moved = True

    limit = GRID_LENGTH - 40 
    
    hit_border = abs(next_x) > limit or abs(next_y) > limit
    hit_obstacle = check_wall_collision(next_x, next_y, 25) 

    if not hit_border and not hit_obstacle:
        player['x'] = next_x
        player['y'] = next_y
    else:
        pass

    if moved and not hit_border and not hit_obstacle:
        rad = math.radians(player['angle'])
        offset_dist = 12 
        dx = -math.sin(rad) * offset_dist
        dy = math.cos(rad) * offset_dist
        
        treads.append({"x": player['x'] + dx, "y": player['y'] + dy, "life": MAX_TREAD_LIFE})
        treads.append({"x": player['x'] - dx, "y": player['y'] - dy, "life": MAX_TREAD_LIFE})
        
    if key == b'n':  
        global score
        if score >= AIRSTRIKE_COST and airstrike_cd <= 0:
            Reinforcements()
            score -= AIRSTRIKE_COST    

def mouseListener(button, state, x, y):
    global player, game_over
    if game_over: return 

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if player['ammo'] > 0 and player['cooldown'] <= 0:
            rad = math.radians(player['angle'])
            bullets.append({
                "x": player['x'], "y": player['y'],
                "dx": math.cos(rad) * BULLET_SPEED,
                "dy": math.sin(rad) * BULLET_SPEED,
                "owner": "player"
            })
            # Rapid fire doesn't consume ammo
            if rapid_fire_timer <= 0:
                player['ammo'] -= 1
            player['cooldown'] = 4 if rapid_fire_timer > 0 else 20
    
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if len(obstacles) < MAX_OBSTACLES: 
            rad = math.radians(player['angle'])
            dist = 100 
            new_x = player['x'] + math.cos(rad) * dist
            new_y = player['y'] + math.sin(rad) * dist
            
            if abs(new_x) < GRID_LENGTH - 50 and abs(new_y) < GRID_LENGTH - 50:
                if not check_wall_collision(new_x, new_y, 40):
                    clear_shot = True
                    for e in enemies:
                        if math.sqrt((new_x - e['x'])**2 + (new_y - e['y'])**2) < 60:
                            clear_shot = False
                            break
                    
                    if clear_shot:
                        obstacles.append({
                            'x': new_x, 
                            'y': new_y, 
                            'size': 80, 
                            'health': 2 
                        })

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 3000) 
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if camera_mode == 0:
        gluLookAt(player['x'], player['y'] - 400, 500,  
                  player['x'], player['y'], 0,          
                  0, 0, 1)
    else:
        rad = math.radians(player['angle'])
        dist = 300
        height = 150
        
        cx = player['x'] - dist * math.cos(rad)
        cy = player['y'] - dist * math.sin(rad)
        cz = height
        
        gluLookAt(cx, cy, cz,
                  player['x'], player['y'], 20,
                  0, 0, 1)

def showScreen():
    update_game()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setupCamera()
    
    draw_terrain()
    draw_walls() 
    draw_obstacles() 
    draw_treads()
    draw_pickups()
    draw_bullets()
    draw_bombardment() 
    draw_radar_effect() 
    draw_explosions() 

    draw_tank(player['x'], player['y'], player['angle'], (0.2, 0.6, 1.0), is_player=True)
    draw_health_bar(player['x'], player['y'], 30, player['health'], player['max_health'])


    for e in enemies:
        if e['type'] == 'boss':
            glPushMatrix()
            glTranslatef(e['x'], e['y'], 0)
            glScalef(BOSS_SIZE, BOSS_SIZE, BOSS_SIZE)
            draw_tank(0, 0, e['angle'], e['color'])
            glPopMatrix()
            draw_health_bar(e['x'], e['y'], 30 * BOSS_SIZE, e['health'], e['max_health'])
        else:
            draw_tank(e['x'], e['y'], e['angle'], e['color'])
            draw_health_bar(e['x'], e['y'], 30, e['health'], e['max_health'])

    #draw_text(10, 870, f"Health: {int(player['health'])}")
    draw_text(10, 810, f"Ammo: {player['ammo']}")
    combo_display = f"Combo: x{combo_multiplier}" if combo_multiplier > 0 else ""
    rapid_display = f"Rapid: {int(rapid_fire_timer/60)}s" if rapid_fire_timer > 0 else "Rapid: READY"
    parts = [f"Wave: {wave}"]
    if combo_display: parts.append(combo_display)
    parts.append(rapid_display)
    draw_text(10, 720, "   ".join(parts))
    
    #Radar Status
    if radar_state['cooldown'] > 0:
        msg = f"RADAR: {int(radar_state['cooldown']/60)}s"
        col = (0.5, 0.5, 0.5)
    else:
        msg = "RADAR: READY (E)"
        col = (0, 1, 1)
    draw_text(10, 680, msg, col)

    terrain_name = check_terrain(player['x'], player['y']).upper()
    draw_text(10, 780, f"Terrain: {terrain_name}")
    
    draw_text(10, 750, f"Walls: {len(obstacles)}/30")

    draw_text(int(WINDOW_WIDTH/2) - 40, WINDOW_HEIGHT - 70, f"SCORE: {score}")
    draw_text(10, 610, f"AIRSTRIKE: {max(0, airstrike_cd)}")
    draw_text(10, 580, f"COST: {AIRSTRIKE_COST}")

    if cheat_mode:
        draw_text(10, 640, "CHEAT MODE ON")

    if player['health'] < player['max_health'] * 0.3:
        if (low_hp_flash // 20) % 2 == 0:   # blinking
            draw_text(int(WINDOW_WIDTH/2) - 80, int(WINDOW_HEIGHT/2) + 100, "!!! WARNING !!!")
    

    for b in bomb_zones:
        if b['state'] == 'warning':
            if (tick // 20) % 2 == 0:
                draw_text(int(WINDOW_WIDTH/2) - 100, 700, "WARNING: AERIAL ATTACK!", (1, 0, 0))
            break

    if game_over:
        draw_text(int(WINDOW_WIDTH/2) - 50, int(WINDOW_HEIGHT/2), "GAME OVER", (1, 0, 0))
        draw_text(int(WINDOW_WIDTH/2) - 75, int(WINDOW_HEIGHT/2) - 25, "Press 'R' to Restart")
    else:
        controls = "W/S: Move   |   A/D: Move/Turn   |   LMB: Shoot   |   RMB: Build   |   E: Radar   |   V: View"
        draw_text(10, 10, controls)

    draw_minimap()

    glutSwapBuffers()

def idle():
    glutPostRedisplay()

def main():
    generate_obstacles() 
    start_wave(1)
    for _ in range(5): spawn_pickup()
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"3D Tank Battle")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()