from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 800
ARENA_SIZE = 600      
WALL_HEIGHT = 100
        
cam_coords = [0, 500, 500]
view_angle = 0         
view_height = 500
view_mode = "TP" 

hero_coords = [0.0, 0.0, 0.0]  
hero_facing = 0
hero_hp = 5    
is_hero_alive = True
 
current_score = 0
shots_wasted = 0          
max_wasted_shots = 10
is_match_over = False        

projectiles = []        
shot_velocity = 8
      
targets = []
target_velocity = 0.1
pulse_scale = 1.0        
is_pulsing_up = True
      
cheat_mode = False
cheat_vision = False
auto_aim_ticker = 0
   
def render_text(x, y, message):
    glColor3f(1, 1, 1)      
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
             
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()      
    
    glRasterPos2f(x, y)
    for char in message:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
     
    glPopMatrix()      
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def render_floor():        
    tile_w = 60
    for row in range(-10, 10):        
        for col in range(-10, 10):
            px = row * tile_w
            py = col * tile_w
             
            if (row + col) % 2 == 0:
                glColor3f(0.9, 0.9, 0.9)  
            else:
                glColor3f(0.4, 0.4, 0.5)    
            
            glBegin(GL_QUADS)  
            glVertex3f(px, py, 0)
            glVertex3f(px + tile_w, py, 0)
            glVertex3f(px + tile_w, py + tile_w, 0)
            glVertex3f(px, py + tile_w, 0)   
            glEnd()

def render_walls():   
    coords = [
        (-ARENA_SIZE, ARENA_SIZE, 0, 1, 1), 
        (ARENA_SIZE, -ARENA_SIZE, 0, 1, 0), 
        (-ARENA_SIZE, -ARENA_SIZE, 0, 0, 1),  
    ]
          
    glBegin(GL_QUADS)     
    glColor3f(0, 1, 1)
    glVertex3f(-ARENA_SIZE, ARENA_SIZE, 0)
    glVertex3f(ARENA_SIZE, ARENA_SIZE, 0)     
    glVertex3f(ARENA_SIZE, ARENA_SIZE, WALL_HEIGHT)
    glVertex3f(-ARENA_SIZE, ARENA_SIZE, WALL_HEIGHT)
    glEnd()
   
    glBegin(GL_QUADS)
    glColor3f(0, 1, 0)
    glVertex3f(ARENA_SIZE, -ARENA_SIZE, 0)
    glVertex3f(ARENA_SIZE, ARENA_SIZE, 0)
    glVertex3f(ARENA_SIZE, ARENA_SIZE, WALL_HEIGHT)
    glVertex3f(ARENA_SIZE, -ARENA_SIZE, WALL_HEIGHT)
    glEnd()
   
    glBegin(GL_QUADS)
    glColor3f(0, 0, 1)
    glVertex3f(-ARENA_SIZE, -ARENA_SIZE, 0)
    glVertex3f(ARENA_SIZE, -ARENA_SIZE, 0)
    glVertex3f(ARENA_SIZE, -ARENA_SIZE, WALL_HEIGHT)
    glVertex3f(-ARENA_SIZE, -ARENA_SIZE, WALL_HEIGHT)
    glEnd()
   
    glBegin(GL_QUADS)
    glColor3f(0, 0, 1)
    glVertex3f(-ARENA_SIZE, -ARENA_SIZE, 0)
    glVertex3f(-ARENA_SIZE, ARENA_SIZE, 0)
    glVertex3f(-ARENA_SIZE, ARENA_SIZE, WALL_HEIGHT)
    glVertex3f(-ARENA_SIZE, -ARENA_SIZE, WALL_HEIGHT)
    glEnd()

def spawn_targets():
    global targets
    targets = []
    for _ in range(5):
        valid_pos = False  
        while not valid_pos:
            rx = random.uniform(-ARENA_SIZE + 100, ARENA_SIZE - 100)  
            ry = random.uniform(-ARENA_SIZE + 100, ARENA_SIZE - 100)
            if abs(rx) > 150 or abs(ry) > 150:
                targets.append([rx, ry, 30])        
                valid_pos = True
  
def relocate_target(idx):       
    while True:
        rx = random.uniform(-ARENA_SIZE + 100, ARENA_SIZE - 100)
        ry = random.uniform(-ARENA_SIZE + 100, ARENA_SIZE - 100)              
        hx, hy, _ = hero_coords      
        
        if math.hypot(rx - hx, ry - hy) > 200:
            targets[idx] = [rx, ry, 30]          
            break       

def render_hero():         
    glPushMatrix()
    glTranslatef(hero_coords[0], hero_coords[1], hero_coords[2])
    glRotatef(hero_facing, 0, 0, 1)
    
    if is_match_over:        
        glRotatef(90, 0, 1, 0)
    
    glPushMatrix()
    glTranslatef(-15, 0, -10)   
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.3, 0.3, 0.3)       
    glutSolidCone(10, 40, 10, 10)
    glPopMatrix()
     
    glPushMatrix()
    glTranslatef(15, 0, -10)
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.3, 0.3, 0.3)
    glutSolidCone(10, 40, 10, 10)  
    glPopMatrix()
              
    glPushMatrix()
    glTranslatef(0, 0, 10)
    glColor3f(0.6, 0.2, 0.2)    
    glScalef(1.2, 0.6, 0.8)
    glutSolidCube(40)  
    glPopMatrix()
          
    glPushMatrix()
    glTranslatef(0, 0, 35)
    glColor3f(0.8, 0.8, 0.8)     
    glScalef(1.0, 0.5, 0.6)
    glutSolidCube(35)
    glPopMatrix()
          
    glPushMatrix()
    glTranslatef(0, 0, 35)
    glRotatef(90, 0, 1, 0)
    glColor3f(1.0, 0.8, 0.0)          
    glutSolidCone(8, 50, 10, 10)    
    glPopMatrix()
     
    for offset in [-30, 30]:
        glPushMatrix()
        glTranslatef(offset, 0, 35)
        glColor3f(0.5, 0.5, 0.5)
        gluSphere(gluNewQuadric(), 12, 15, 15)
        glPopMatrix()
     
    glPushMatrix()
    glTranslatef(0, 0, 60)
    glColor3f(0.2, 0.2, 0.9)        
    gluSphere(gluNewQuadric(), 18, 20, 20)   
    glPopMatrix()
    
    glPopMatrix() 

def render_villain(x, y, z):       
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.9, 0.1, 0.1)                 
    gluSphere(gluNewQuadric(), 25 * pulse_scale, 15, 15)
           
    glPushMatrix()
    glTranslatef(0, 0, 20 * pulse_scale)
    glColor3f(0.1, 0.1, 0.1)
    gluSphere(gluNewQuadric(), 15 * pulse_scale, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def render_shot(x, y, z):    
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(1, 1, 0)  
    glutSolidCube(8)
    glPopMatrix()

def shoot_projectile():      
    if not is_match_over:
        rads = math.radians(hero_facing)        
        bx = hero_coords[0] + 60 * math.cos(rads)
        by = hero_coords[1] + 60 * math.sin(rads)
        bz = hero_coords[2]    
        projectiles.append([bx, by, bz, hero_facing])

def move_shots():
    global shots_wasted, current_score, is_match_over, projectiles
    
    surviving_bullets = []
    
    for shot in projectiles:      
        rads = math.radians(shot[3])
        shot[0] += shot_velocity * math.cos(rads)  
        shot[1] += shot_velocity * math.sin(rads)
        
        hit_target = False
        out_of_bounds = False
         
        if abs(shot[0]) > ARENA_SIZE or abs(shot[1]) > ARENA_SIZE:
            out_of_bounds = True
            if not cheat_mode:
                shots_wasted += 1
                if shots_wasted >= max_wasted_shots:
                    is_match_over = True      
        
        if not out_of_bounds: 
            for idx, villain in enumerate(targets):   
                dist = math.hypot(shot[0] - villain[0], shot[1] - villain[1])
                if dist < 35:
                    current_score += 1
                    relocate_target(idx)
                    hit_target = True     
                    break
                  
        if not hit_target and not out_of_bounds:
            surviving_bullets.append(shot)
            
    projectiles = surviving_bullets       

def move_villains():     
    global hero_hp, is_match_over, pulse_scale, is_pulsing_up
    
    if is_match_over: return
         
    if is_pulsing_up:
        pulse_scale += 0.01      
        if pulse_scale >= 1.2: is_pulsing_up = False
    else:      
        pulse_scale -= 0.01
        if pulse_scale <= 0.8: is_pulsing_up = True
          
    for villain in targets:
        dx = hero_coords[0] - villain[0]
        dy = hero_coords[1] - villain[1]      
        dist = math.hypot(dx, dy)
        
        if dist > 0:     
            villain[0] += (dx / dist) * target_velocity
            villain[1] += (dy / dist) * target_velocity
                    
        if dist < 40:
            hero_hp -= 1
            if hero_hp <= 0:
                is_match_over = True        
            relocate_target(targets.index(villain))

def auto_pilot_logic():   
    global hero_facing, auto_aim_ticker
       
    if cheat_mode and not is_match_over:
        auto_aim_ticker += 1
        
        if targets:       
            closest = min(targets, key=lambda t: math.hypot(t[0] - hero_coords[0], t[1] - hero_coords[1]))
            
            dx = closest[0] - hero_coords[0]    
            dy = closest[1] - hero_coords[1]
            
            if dx == 0:    
                hero_facing = 90 if dy > 0 else 270
            else: 
                rads = math.atan(dy / dx)
                hero_facing = math.degrees(rads)
                if dx < 0: hero_facing += 180
                
            if int(auto_aim_ticker) % 30 == 0:
                shoot_projectile()

def handle_keys(key, x, y):
    global hero_coords, hero_facing, cheat_mode, cheat_vision, is_match_over, hero_hp, current_score, shots_wasted
    
    step = 10
    rads = math.radians(hero_facing)
     
    if not is_match_over:
        if key == b'w':
            nx = hero_coords[0] + step * math.cos(rads)
            ny = hero_coords[1] + step * math.sin(rads)
            if abs(nx) < ARENA_SIZE - 50 and abs(ny) < ARENA_SIZE - 50:
                hero_coords[0], hero_coords[1] = nx, ny
                  
        elif key == b's':
            nx = hero_coords[0] - step * math.cos(rads)
            ny = hero_coords[1] - step * math.sin(rads)
            if abs(nx) < ARENA_SIZE - 50 and abs(ny) < ARENA_SIZE - 50:
                hero_coords[0], hero_coords[1] = nx, ny
            
        if not cheat_mode:
            if key == b'a': hero_facing += 5
            elif key == b'd': hero_facing -= 5
              
        if key == b'c': cheat_mode = not cheat_mode
        if key == b'v' and cheat_mode: cheat_vision = not cheat_vision
   
    if key == b'r':
        is_match_over = False
        hero_hp = 5
        current_score = 0
        shots_wasted = 0
        hero_coords = [0.0, 0.0, 0.0]
        hero_facing = 0      
        projectiles.clear()
        spawn_targets()
        cheat_mode = False
        cheat_vision = False   

def handle_special_keys(key, x, y):
    global view_angle, view_height      
    
    if key == GLUT_KEY_UP:  
        view_height = min(view_height + 10, 800)
    elif key == GLUT_KEY_DOWN:
        view_height = max(view_height - 10, 100)
    elif key == GLUT_KEY_LEFT: 
        view_angle += 5  
    elif key == GLUT_KEY_RIGHT:  
        view_angle -= 5 

def handle_mouse(btn, state, x, y):  
    global view_mode     
    
    if btn == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if not is_match_over and not cheat_mode:
            shoot_projectile()       
              
    if btn == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        view_mode = "FP" if view_mode == "TP" else "TP"
   
def configure_view(): 
    glMatrixMode(GL_PROJECTION)     
    glLoadIdentity()
    gluPerspective(120, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if view_mode == "FP" or (cheat_mode and cheat_vision):
        rads = math.radians(hero_facing)
           
        cx = hero_coords[0] - 20 * math.cos(rads)
        cy = hero_coords[1] - 20 * math.sin(rads)
        cz = hero_coords[2] + 150
         
        lx = hero_coords[0] + 300 * math.cos(rads)
        ly = hero_coords[1] + 300 * math.sin(rads)
        lz = hero_coords[2]
        
        gluLookAt(cx, cy, cz, lx, ly, lz, 0, 0, 1)
    else:           
        rads = math.radians(view_angle)
        orbit_radius = 700   
        cx = orbit_radius * math.cos(rads)   
        cy = orbit_radius * math.sin(rads)
        
        gluLookAt(cx, cy, view_height, 0, 0, 0, 0, 0, 1)    

def game_loop():   
    move_shots()
    move_villains()   
    auto_pilot_logic()   
    glutPostRedisplay() 
    
def render_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)    
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)   

    configure_view()   
      
    render_floor()
    render_walls()
    render_hero()      
    
    for t in targets:
        render_villain(t[0], t[1], t[2])     
        
    for p in projectiles:  
        render_shot(p[0], p[1], p[2])
     
    render_text(10, 770, f"HP: {hero_hp}")
    render_text(10, 740, f"Score: {current_score}")
    render_text(10, 710, f"Misses: {shots_wasted} / {max_wasted_shots}")
    
    if is_match_over:   
        render_text(360, 500, "GAME OVER! Press 'R' to Restart")
    if cheat_mode:
        render_text(10, 680, "[Cheat Mode ON]")   
           
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)   
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Bullet Frenzy")    

    glEnable(GL_DEPTH_TEST)
    spawn_targets()
    
    glutDisplayFunc(render_scene)
    glutKeyboardFunc(handle_keys)   
    glutSpecialFunc(handle_special_keys)
    glutMouseFunc(handle_mouse)
    glutIdleFunc(game_loop)
   
    glutMainLoop()   
   
if __name__ == "__main__":     
    main()     