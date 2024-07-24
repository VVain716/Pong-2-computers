import socket
import pygame
import threading
import math
import struct
import time
import helpers

# Configuration
WIDTH, HEIGHT = 1200, 600
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 100
BUFF = 20
BALL_RADIUS = 10
STARTING_SPEED = 10
PIXEL_BUFF = 10

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont('ariel', 75)

# Socket setup with SO_REUSEADDR
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 12345))
server_socket.listen(1)
print("Server listening on port 12345")

clientsocket, addr = server_socket.accept()
print("Connected to:", addr)

# Game classes
class Paddle:
    def __init__(self, center: list):
        self.center = center
        self.rect = None

    def get_rect(self):
        self.rect = pygame.rect.Rect(self.center[0] - PADDLE_WIDTH / 2, self.center[1] - PADDLE_HEIGHT / 2, PADDLE_WIDTH, PADDLE_HEIGHT)

class Ball:
    def __init__(self):
        self.center = [WIDTH / 2, HEIGHT / 2]
        self.angle = 15
        self.speed = STARTING_SPEED
        self.movement = [-1 * STARTING_SPEED * math.cos(self.angle * math.pi / 180), -1 * STARTING_SPEED * math.sin(self.angle * math.pi / 180)]

    def update(self):
        self.center[0] += self.movement[0]
        self.center[1] += self.movement[1]

    def check_collision(self, paddle1: Paddle, paddle2: Paddle):
        if self.center[1] - BALL_RADIUS <= 20 or self.center[1] + BALL_RADIUS >= 580:
            self.movement[1] *= -1
        if self.center[0] - BALL_RADIUS <= paddle1.center[0] + PADDLE_WIDTH / 2 and self.center[0] - BALL_RADIUS >= paddle1.center[0] + PADDLE_WIDTH / 2 - PIXEL_BUFF:
            if paddle1.center[1] - PADDLE_HEIGHT / 2 <= self.center[1] <= paddle1.center[1] + PADDLE_HEIGHT / 2:
                self.movement[0] *= -1
        if self.center[0] + BALL_RADIUS >= paddle2.center[0] - PADDLE_WIDTH / 2 and self.center[0] + BALL_RADIUS <= paddle2.center[0] + PADDLE_WIDTH / 2 + PIXEL_BUFF:
            if paddle2.center[1] - PADDLE_HEIGHT / 2 <= self.center[1] <= paddle2.center[1] + PADDLE_HEIGHT / 2:
                self.movement[0] *= -1

def draw_paddle(paddle: Paddle):
    paddle.get_rect()
    pygame.draw.rect(screen, 'white', paddle.rect)

def draw_ball(ball: Ball):
    pygame.draw.circle(screen, 'white', (int(ball.center[0]), int(ball.center[1])), BALL_RADIUS)

def draw_screen():
    screen.fill('black')
    pygame.draw.rect(screen, 'white', pygame.rect.Rect(0, 0, WIDTH, 20))
    pygame.draw.rect(screen, 'white', pygame.rect.Rect(0, 580, WIDTH, 20))
    middle = WIDTH / 2
    length = 5
    for i in range(15):
        rect = pygame.rect.Rect(0, 0, length, length)
        rect.center = (middle, 40 + HEIGHT * i / 15)
        pygame.draw.rect(screen, 'white', rect)

def draw_score(score1: int, score2: int):
    font1 = font.render(str(score1), True, 'white')
    font1_rect = font1.get_rect(center=(WIDTH / 2 - 50, 80))
    screen.blit(font1, font1_rect)
    font2 = font.render(str(score2), True, 'white')
    font2_rect = font2.get_rect(center=(WIDTH / 2 + 50, 80))
    screen.blit(font2, font2_rect)

player1 = Paddle([BUFF + PADDLE_WIDTH / 2, HEIGHT / 2])
player2 = Paddle([WIDTH - BUFF - PADDLE_WIDTH / 2, HEIGHT / 2])
ball = Ball()
start = False
score1, score2 = 0, 0

# Data handling functions
def get_data(clientsocket, stop_event):
    while not stop_event.is_set():
        try:
            data = clientsocket.recv(8)
            if data:
                unpacked_data = struct.unpack('!ff', data)
                print("Received:", unpacked_data)
            else:
                break
        except socket.error:
            break
    clientsocket.close()

def send_data(clientsocket, int1, int2):
    data = struct.pack('!ff', int1, int2)
    clientsocket.sendall(data)

# Main function
def main():
    global score1, score2, player1, player2, ball, start
    stop_event = threading.Event()
    data_thread = threading.Thread(target=get_data, args=(clientsocket, stop_event))
    data_thread.start()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                stop_event.set()
                break 

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and player1.center[1] > 20 + PADDLE_HEIGHT / 1.7:
            player1.center[1] -= 7
        if keys[pygame.K_s] and player1.center[1] < 580 - PADDLE_HEIGHT / 1.7:
            player1.center[1] += 7
        if keys[pygame.K_UP] and player2.center[1] > 20 + PADDLE_HEIGHT / 1.7:
            player2.center[1] -= 7
        if keys[pygame.K_DOWN] and player2.center[1] < 580 - PADDLE_HEIGHT / 1.7:
            player2.center[1] += 7
        if keys[pygame.K_SPACE]:
            start = True

        draw_screen()
        draw_score(score1, score2)
        draw_ball(ball)
        draw_paddle(player1)
        draw_paddle(player2)
        print(type(player1.center[1]))
        send_data(clientsocket, player1.center[1], player2.center[1])
        if ball.center[0] <= 0:
            score2 += 1
            ball = Ball()
            start = False
        if ball.center[0] >= WIDTH:
            score1 += 1
            ball = Ball()
            start = False

        ball.check_collision(player1, player2)
        if start:
            ball.update()

        pygame.display.update()
        clock.tick(60)

    # Clean up
    pygame.quit()
    stop_event.set()  # Ensure the data thread stops
    try:
        data_thread.join(timeout=1)  # Wait for the data thread to finish with a timeout
    except RuntimeError:
        print("Data thread did not exit cleanly.")
    server_socket.close()  # Close the server socket

if __name__ == '__main__':
    main()
