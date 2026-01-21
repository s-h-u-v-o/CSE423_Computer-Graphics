import random
import time
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

width, height = 800, 1000
basket = width//2
basket_width = 70
diamond = [random.randint(20, width-20), 900]
r = random.choice([0.45, 0.50, 0.55, 0.65, 0.70])
g = random.choice([0.45, 0.50, 0.55, 0.65, 0.70])       
b = random.choice([0.45, 0.50, 0.55, 0.65, 0.70])
diamond_color = [r, g, b]
fallspeed = 3
score = 0
frametime = time.time()
pause_game = False
game_over = False
cheatmode = False

def buttons():
    y_top = height-30
    y_btm = y_top-40
    y_mid = (y_top + y_btm)//2
    return y_top, y_btm, y_mid

def determine_zone(x1, y1, x2, y2):
    dx = x2-x1
    dy = y2-y1
    diff_x = abs(dx)
    diff_y = abs(dy)
    if diff_x >= diff_y:
        if dx >= 0 and dy >= 0 : return 0
        if dx < 0 and dy >= 0 : return 3
        if dx < 0 and dy < 0 : return 4
        return 7
    else: 
        if dx >= 0 and dy >= 0 : return 1
        if dx < 0 and dy >= 0 : return 2
        if dx < 0 and  dy < 0 : return 5
        return 6

def map_to_z0(x, y, z):
    if z == 0 : return x, y
    if z == 1 : return y, x
    if z == 2 : return y, -x
    if z == 3 : return -x, y
    if z == 4 : return -x, -y
    if z == 5 : return -y, -x
    if z == 6 : return -y, x
    if z == 7 : return x, -y

def map_from_z0(x, y, z):
    if z == 0 : return x, y
    if z == 1 : return y, x
    if z == 2 : return -y, x
    if z == 3 : return -x, y
    if z == 4 : return -x, -y
    if z == 5 : return -y, -x
    if z == 6 : return y, -x
    if z == 7 : return x, -y

def MPL_algo(x1, y1, x2, y2):
    points = []
    dx = x2-x1
    dy = y2-y1
    d = 2*dy - dx
    d_e = 2*dy
    d_ne = 2*(dy-dx)
    x, y = x1, y1

    while x <= x2:    
        points.append((x, y))
        if d>0:
            d += d_ne
            y += 1
        else:
            d += d_e
        x += 1
    return points

def draw_line(x_start, y_start, x_end, y_end, rgb_color, size=2):
    z = determine_zone(x_start, y_start, x_end, y_end)
    z0_x1, z0_y1 = map_to_z0(x_start, y_start, z)
    z0_x2, z0_y2 = map_to_z0(x_end, y_end, z)
    
    if z0_x1 > z0_x2:
        z0_x1, z0_x2 = z0_x2, z0_x1
        z0_y1, z0_y2 = z0_y2, z0_y1
        
    z0_points = MPL_algo(z0_x1, z0_y1, z0_x2, z0_y2)
    
    final_points = []
    for px, py in z0_points:
        final_points.append(map_from_z0(px, py, z))
           
    glColor3f(*rgb_color)
    glPointSize(size)
    glBegin(GL_POINTS)

    for pt in final_points:
        glVertex2f(pt[0], pt[1])

    glEnd()
         
def draw_diamond_falling():
    global diamond, diamond_color
    bx, by = diamond[0], diamond[1]
    offset = 20
    draw_line(bx - offset, by, bx, by + offset, diamond_color)
    draw_line(bx, by + offset, bx + offset, by, diamond_color)
    draw_line(bx + offset, by, bx, by - offset, diamond_color)
    draw_line(bx, by - offset, bx - offset, by, diamond_color)

def draw_basket():
    global basket
    draw_line(basket - 70, 75, basket + 70, 75, (0.5, 0.5, 0.5))
    draw_line(basket - 50, 40, basket + 50, 40, (0.5, 0.5, 0.5))
    draw_line(basket - 70, 75, basket - 50, 40, (0.5, 0.5, 0.5))
    draw_line(basket + 50, 40, basket + 70, 75, (0.5, 0.5, 0.5))

def draw_pause_button():
    global pause_game, width
    btn_color = (1, 0.7, 0)
    mid_x = width // 2
    
    y_top, y_btm, y_mid = buttons()
    
    if not pause_game:
        draw_line(mid_x - 10, y_top, mid_x - 10, y_btm, btn_color)
        draw_line(mid_x + 10, y_top, mid_x + 10, y_btm, btn_color)
    else:
        draw_line(mid_x - 20, y_top, mid_x + 20, y_mid, btn_color)
        draw_line(mid_x + 20, y_mid, mid_x - 20, y_btm, btn_color)
        draw_line(mid_x - 20, y_top, mid_x - 20, y_btm, btn_color)

def draw_restart_button():
    btn_color = (0, 0.7, 0.7) 
    y_top, y_btm, y_mid = buttons()
    
    draw_line(50, y_mid, 100, y_mid, btn_color)     
    draw_line(75, y_top, 50, y_mid, btn_color)
    draw_line(75, y_btm, 50, y_mid, btn_color)

def draw_quit_button():
    global width 
    btn_color = (1, 0, 0)
    center_x = width - 50 
    y_top, y_btm, y_mid = buttons()    
  
    draw_line(center_x - 15, y_top, center_x + 15, y_btm, btn_color)
    draw_line(center_x - 15, y_btm, center_x + 15, y_top, btn_color)

def game_physics():
    global diamond, basket, game_over, fallspeed, diamond_color, score, frametime, pause_game, cheatmode, width, height

    current_time = time.time()
    del_time = current_time - frametime       
    frametime = current_time    
    fallspeed += del_time * 0.25

    if game_over:
        return

    if not pause_game:        
        ball_x, ball_y = diamond[0], diamond[1]
        
        if 20 < ball_y < 95:
            hit_left = basket - 70
            hit_right = basket + 70
            ball_width_offset = 20
               
            if (ball_x - ball_width_offset < hit_right) and (ball_x + ball_width_offset > hit_left):
                diamond = [random.randint(20, width-20), 900]    
                r = random.choice([0.45, 0.50, 0.55, 0.65, 0.70])
                g = random.choice([0.45, 0.50, 0.55, 0.65, 0.70])       
                b = random.choice([0.45, 0.50, 0.55, 0.65, 0.70])
                diamond_color = [r, g, b]
                score += 1
                print(f"Current score: {score}")
            else:
                diamond[1] -= fallspeed

        elif ball_y < -40:
            game_over = True
            print(f"GAME OVER. Total score: {score}")

        else:
            diamond[1] -= fallspeed       

        if cheatmode:
            target_y = 75
            dy = ball_y - target_y
            if dy < height + 20:
                dx = basket - ball_x  
                predict = 1 - (dy / (height + 20))
                move = dx * predict * 0.25
                          
                new_basket_pos = basket - move
                if 60 < new_basket_pos < width - 60:
                    basket = new_basket_pos

    glutPostRedisplay()

def handle_mouse_input(btn, state, mouse_x, mouse_y):
    global pause_game, game_over, score, diamond, fallspeed, diamond_color, width, height, cheatmode
    
    click_y = height - mouse_y
    mid_x = width // 2    
    y_top, y_btm, _ = buttons()
         
    if btn == GLUT_LEFT_BUTTON and state == GLUT_DOWN:   
        if (mid_x - 30) < mouse_x < (mid_x + 30) and y_btm < click_y < y_top:
            pause_game = not pause_game                
        elif 50 < mouse_x < 100 and y_btm < click_y < y_top:
            game_over = False
            cheatmode = False
            score = 0
            diamond = [random.randint(20, width - 20), height + 50]
            fallspeed = 3
            r = random.choice([0.45, 0.50, 0.55, 0.65, 0.70])
            g = random.choice([0.45, 0.50, 0.55, 0.65, 0.70])       
            b = random.choice([0.45, 0.50, 0.55, 0.65, 0.70])
            diamond_color = [r, g, b]
            print("Starting Over...")                  
        elif (width - 80) < mouse_x < width - 30 and y_btm < click_y < y_top:
            print("Goodbye! Total score:", score)
            glutLeaveMainLoop()  
            
    glutPostRedisplay()
   
def handle_keyboard_input(key_code, x, y):
    global basket, cheatmode, diamond, width
    
    step_size = (fallspeed + 5) * 5

    if game_over or pause_game: 
        return

    if key_code == b'c':  
        if not cheatmode:
            cheatmode = True
            print("Cheat Mode [ON]")                
        else:
            cheatmode = False
            print("Cheat Mode [OFF]")  

    glutPostRedisplay()

def handle_special_keys(key, x, y): 
    global basket, width    
    step_size = (fallspeed + 5) * 5 
    
    if not game_over and not pause_game and not cheatmode:              
        if key == GLUT_KEY_LEFT:
            if basket - 70 - step_size > 0:
                basket -= step_size                    
        elif key == GLUT_KEY_RIGHT:
            if basket + 70 + step_size < width:
                basket += step_size
                
    glutPostRedisplay()

def setup_projection():      
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, width, 0.0, height, 0, 1.0)
    glMatrixMode(GL_MODELVIEW)

def draw_display():  
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup_projection()
    
    draw_basket()
    draw_diamond_falling()
    draw_pause_button()
    draw_restart_button()
    draw_quit_button()
    
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Catch the Diamond!")    
    glClearColor(0.0, 0.0, 0.0, 1.0)           
    glutDisplayFunc(draw_display)
    glutIdleFunc(game_physics)
    glutKeyboardFunc(handle_keyboard_input) 
    glutMouseFunc(handle_mouse_input)
    glutSpecialFunc(handle_special_keys)
            
    glutMainLoop()

if __name__ == "__main__":  
    main() 