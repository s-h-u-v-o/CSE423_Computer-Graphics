from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import * 
import random        

ball_speed = 0.05   
ball_size = 10 
ball_arr = []   
flag = flag1 = True       
blink = False
opct = 0
mul = 1

def draw_point(x, y, size):         
    glPointSize(size)
    glBegin(GL_POINTS)       
    glVertex2f(x, y)
    glEnd()

def keyboard_listener(key, x, y):
    global flag
    if key == b' ':  
        flag = not flag
    glutPostRedisplay()

def special_key_listener(key, x, y):
    global ball_speed, flag, ball_arr
    if flag:
        if key == GLUT_KEY_UP:
            ball_speed *= 1.5
            for i in ball_arr:
                i[5] *= 1.5
                i[6] *= 1.5
        elif key == GLUT_KEY_DOWN:
            ball_speed /= 1.5
            for i in ball_arr:
                i[5] /= 1.5
                i[6] /= 1.5
    glutPostRedisplay()

def mouse_listener(button, state, x, y):
    global flag, ball_arr, flag1, blink
    if flag:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            blink = not blink     
        elif flag1 == True and button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
            r = random.choice([0.25, 0.5, 0.75, 1.0])
            g = random.choice([0.25, 0.5, 0.75, 1.0])
            b = random.choice([0.25, 0.5, 0.75, 1.0])
            vx = ball_speed * random.choice([-1, 1])
            vy = ball_speed * random.choice([-1, 1])
            ball_arr.append([x, 1000-y, r, g, b, vx, vy])
    glutPostRedisplay()

def setup_projection():
    glViewport(0, 0, 1000, 1000)    
    glMatrixMode(GL_PROJECTION)   
    glLoadIdentity()               
    glOrtho(0, 1000, 0, 1000, 0, 1)  
    glMatrixMode(GL_MODELVIEW) 

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup_projection()
    for i in ball_arr:
        glColor3f(i[2]-opct, i[3]-opct, i[4]-opct)
        draw_point(i[0], i[1], ball_size)
    glutSwapBuffers()

def animate():
    global ball_speed, flag, ball_arr, blink, opct, mul
    if flag:
        for i in ball_arr:
            i[0] += i[5]
            i[1] += i[6]
            if i[0] <= 0:
                i[0] = 0
                i[5] = -i[5]
            elif i[0] >= 1000:
                i[0] = 1000
                i[5] = -i[5]
            if i[1] <= 0:
                i[1] = 0
                i[6] = -i[6]
            elif i[1] >= 1000:
                i[1] = 1000
                i[6] = -i[6]
        if blink:
            opct += (0.001 * mul)
            if opct > 1.0:
                mul = -1
            elif opct < 0.0:
                mul = 1
    glutPostRedisplay()

def main():
    glutInit()         
    glutInitDisplayMode(GLUT_RGBA)  
    glutInitWindowSize(1000, 1000) 
    glutInitWindowPosition(0, 0)    
    glutCreateWindow(b"OpenGL 2D Point")  
    glutDisplayFunc(display)    
    glutIdleFunc(animate)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)
    glutMainLoop()        

if __name__ == "__main__":
    main()