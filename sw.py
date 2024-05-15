#Rocket League SideSwipe Game - Omer Kfir Herzog יא'3
import pygame
import sys
from pygame.locals import *
import physics
import math
from random import randint
import time
import socket
import pickle
import protocol
import threading


RIGHT_WALL_BACKGROUND = 2497
FLOOR_BACKGOURND = 1057
RIGHT_WALL_BG_X = 4647


GREEN = (0, 255, 0)
GRAY = (128,128,128)

PLAYER_WIDTH = 75
PLAYER_HEIGHT = 38

BOOST_WIDTH = 8

BUFFER_LIMIT = 1024

BALL_RADIUS = 40
BALL_WEIGHT = 70

FIRST_PLAYER_POS = (500, 850)
SECOND_PLAYER_POS = (1800,850)
BALL_STARTING_POS = (1200, 600)


# Initialize Pygame
pygame.init()
infoScreen = pygame.display.Info()
width = infoScreen.current_w if infoScreen.current_w < RIGHT_WALL_BACKGROUND else RIGHT_WALL_BACKGROUND
height = infoScreen.current_h if infoScreen.current_h < FLOOR_BACKGOURND else FLOOR_BACKGOURND
SCREEN = pygame.display.set_mode((width, height))

RUN = True
DEBUG = False


class Server:
    SERVER_IP = '10.100.102.103'

    def __init__(self):
        self.SERVER_PORT = 1393

        try:
            self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f'New socket: {self.tcpSocket}')
            self.tcpSocket.connect((self.SERVER_IP, self.SERVER_PORT))
            print(f'Socket connected succusfully: {self.tcpSocket}')
        
        except Exception as e:
            print("server is not running...")
            print(e)
            self.nullObject = True
            print(f'Socket connected unsuccusfully: {self.tcpSocket}')
            print(f'Closing socket: {self.tcpSocket}')
            self.tcpSocket.close()
            return

        self.buffer = ""

        t = threading.Thread(target=self.recv_by_size, args=())
        t.start()
        print(f'New Thread: {t}')
        while self.buffer == "":
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.nullObject = True
                        print(f'Closing socket: {self.tcpSocket}')
                        self.tcpSocket.close()
                        return
            
            if self.buffer == 0:
                self.nullObject = True
                return

        self.SERVER_PORT = int(self.buffer[protocol.BUFFER_LENGTH_SIZE:])

        self.playerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f'New socket: {self.playerSocket}')
        self.log_output_data(protocol.BuildMsgProtocol(protocol.JOINING_GAME, None), (self.SERVER_IP, self.SERVER_PORT))
        self.playerSocket.sendto(protocol.BuildMsgProtocol(protocol.JOINING_GAME, None), (self.SERVER_IP, self.SERVER_PORT))
        msg = self.recv_msg()
        while len(msg) == 0 or msg.decode()[:-1] != protocol.SERVER_GOT_ADDRESS:
            self.log_output_data(protocol.BuildMsgProtocol(protocol.JOINING_GAME, None), (self.SERVER_IP, self.SERVER_PORT))
            self.playerSocket.sendto(protocol.BuildMsgProtocol(protocol.JOINING_GAME, None), (self.SERVER_IP, self.SERVER_PORT))
            msg = self.recv_msg()
        
        self.playerSocket.settimeout(0.1)

        self.gameEnded = False
        self.gameEndedEnt = False

        # we will send the server every few seconds that the client is still connected
        self.clientConnected = time.time()

        # the object did manage to connect to the server
        self.nullObject = False

        self.first_player = False

        self.player_object = None
        self.second_player_object = None
        self.ball_object = None

        self.time_out_cnt = 0
        self.running = True
    

    def recv_msg(self):
        try:
            buffer,addr = self.playerSocket.recvfrom(protocol.MAX_MESSAGE_LENGTH)
            size = int(buffer[:protocol.BUFFER_LENGTH_SIZE].decode())  # get size

            if DEBUG:
                print(f'---\nRECIVED MESSAGE\nAddress: {addr}\nContent: {buffer[:protocol.MAX_PROTOCOL_LOG_LENGTH]}...\n---')

            buffer = buffer[protocol.BUFFER_LENGTH_SIZE:]
            
            if size != len(buffer):
                raise Exception("Data corrupted")
            
            if buffer[:protocol.BUFFER_LENGTH_SIZE - 1].decode() == protocol.GAME_ENDED:
                self.gameEnded = True
            
            if buffer[:protocol.BUFFER_LENGTH_SIZE - 1].decode() == protocol.GAME_STOPPED_ENTHERNET:
                self.gameEndedEnt = True

            self.time_out_cnt = 0
            return buffer
        except ConnectionResetError as e:
            self.gameEndedEnt = True
            print(e)
            return b""
        except socket.timeout as e:
            self.time_out_cnt += 1
            if self.time_out_cnt > 10:
                self.gameEndedEnt = True
            print(e)
            return b""
        except Exception as e:
            print(e)
            return b""
        

    # for using tcp
    def recv_by_size(self):
        try:
            dataLength = int(self.tcpSocket.recv(4).decode())
            buffer = self.tcpSocket.recv(dataLength)

            if DEBUG:
                print(f'---\nRECIVED MESSAGE\nAddress: {(self.SERVER_IP, self.SERVER_PORT)}\nContent: {buffer[:protocol.MAX_PROTOCOL_LOG_LENGTH]}...\n---')
            
            lengthMsg = len(buffer)
            while lengthMsg != dataLength:
                buffer += self.tcpSocket.recv(dataLength - lengthMsg)
                lengthMsg = len(buffer)
            
            self.buffer = buffer

        except Exception as e:
            print(e)
            self.buffer = 0
            print(f'Closing socket: {self.tcpSocket}')
            self.tcpSocket.close()
        
        finally:
            print(f'Thread ended')
    
    # we only need one bool to know where to place everyone
    # this bool will indicate if we are the first or the second player
    # if we are the first we will start at FIRST_PLAYER_POS and so for the second player
    # if the bool is True we are the first player
    def get_starting_pos(self):
        self.recv_msg()

        while True:
            try:
                msg = self.recv_msg()[protocol.BUFFER_LENGTH_SIZE:]
                msg = int(msg)
                self.log_output_data(protocol.BuildMsgProtocol(protocol.MSG_RECIVED, None), (self.SERVER_IP, self.SERVER_PORT))
                self.playerSocket.sendto(protocol.BuildMsgProtocol(protocol.MSG_RECIVED, None), (self.SERVER_IP, self.SERVER_PORT))
                break
            except Exception as e:
                if self.gameEndedEnt:
                    return
                print(e)
                self.log_output_data(protocol.BuildMsgProtocol(protocol.MSG_NOT_RECIVED, None), (self.SERVER_IP, self.SERVER_PORT))
                self.playerSocket.sendto(protocol.BuildMsgProtocol(protocol.MSG_NOT_RECIVED, None), (self.SERVER_IP, self.SERVER_PORT))
        
        
        self.first_player = msg


    def game_handle(self):

        while not (self.gameEnded or self.gameEndedEnt or not self.running) and RUN:
            if self.ball_object != None and self.ball_object.inGoal:
                time.sleep(5)
            if time.time() - self.clientConnected > 5:
                self.clientConnected = time.time()
                self.log_output_data(protocol.BuildMsgProtocol(protocol.PLAYER_STILL_CONNECTED, None), (self.SERVER_IP, self.SERVER_PORT))
                self.playerSocket.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_STILL_CONNECTED, None), (self.SERVER_IP, self.SERVER_PORT))

            msg = self.recv_msg()
            msg_command = msg[:protocol.BUFFER_LENGTH_SIZE - 1].decode()
            msg_info = msg[protocol.BUFFER_LENGTH_SIZE:]

            if msg_info != b"":

                if msg_command == protocol.GAME_STOPPED_ENTHERNET:
                    self.gameEndedEnt = True
                elif msg_command == protocol.GAME_ENDED:
                    self.gameEnded = True
                
                elif msg_command == protocol.PLAYER_INFO:
                    self.player_object = pickle.loads(msg_info)
                elif msg_command == protocol.SECOND_PLAYER_INFO:
                    self.second_player_object = pickle.loads(msg_info)
                elif msg_command == protocol.BALL_INFO:
                    self.ball_object = pickle.loads(msg_info)
        
        print('Thread ended')
        
    
    def send_player(self, player_object : physics.Object):
        player = pickle.dumps(player_object)
        self.log_output_data(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, player), (self.SERVER_IP, self.SERVER_PORT))
        self.playerSocket.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, player), (self.SERVER_IP, self.SERVER_PORT))
    
    def close_game(self):
        print(f'Closing socket {self.playerSocket}')
        self.playerSocket.close()
    
    def log_output_data(self, msg_info, addr):
        if DEBUG:
            print(f"---SENDING MESSAGE\nAddress: {addr}\nContent: {msg_info[:protocol.MAX_PROTOCOL_LOG_LENGTH]}...\n---")


class Game:
    #Frames in second - cycles
    REFRESH_RATE = 60
    
    #Set Clock
    clock = pygame.time.Clock()
    
    def __init__(self, player):

        self.player = player
        self.width = self.player.width
        self.height = self.player.height

        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        pygame.display.set_caption("Rocket League")

        # Load the background image
        self.background_image = pygame.image.load("background.png").convert()
        self.ballImage = pygame.transform.scale(pygame.image.load("soccer.png"), (BALL_RADIUS*2,BALL_RADIUS*2))
        self.ballImage.set_colorkey((255,255,255))
        self.ballImage.convert_alpha()

        self.boostSprites = []
        self.secondplayerboostSprites = []

        self.bg_x = 0
        self.bg_y = 0

        self.ball = physics.Ball(BALL_WEIGHT, BALL_STARTING_POS, BALL_RADIUS)
    

    def change_player_picture_with_angle(self, image, angle, flipObjectDraw, car: physics.Object):
        image = pygame.transform.rotate(image, angle)
        image = pygame.transform.flip(image, flipObjectDraw, False)
        rect = image.get_rect(center=(car.xPlace + PLAYER_WIDTH / 2, car.yPlace + PLAYER_HEIGHT / 2))
        return image, rect


    def correct_camera_view(self):
        self.bg_x = -self.player.player_rect.x + self.width // 2
        self.bg_y = -self.player.player_rect.y + self.height // 2

        self.bg_x = 0 if self.bg_x >= 0 else -(RIGHT_WALL_BACKGROUND - self.width) if -self.bg_x >= RIGHT_WALL_BACKGROUND - self.width else self.bg_x
        self.bg_y = 0 if self.bg_y >= 0 else -(FLOOR_BACKGOURND - self.height) if -self.bg_y >= FLOOR_BACKGOURND - self.height else self.bg_y
        

    def draw_player_essentials(self, xOfPlayerOnScreen : int, yOfPlayerOnScreen : int, secondPlayer :physics.Object):

        # draw boost amount
        amountOfBoost = (self.player.PlayerObject.boostAmount / physics.MAX_BOOST) * 100

        boostX = xOfPlayerOnScreen - 10
        boostY = yOfPlayerOnScreen - 20

        boostRect = pygame.Rect(boostX, boostY, amountOfBoost, 20)
        pygame.draw.rect(self.screen, GREEN, boostRect)

        # draw is able to jump
        jumpX = xOfPlayerOnScreen + PLAYER_WIDTH / 2 + 5
        jumpY = yOfPlayerOnScreen - 45
        radius = 10
        color = GREEN if not self.player.PlayerObject.IsDoubleJumping else GRAY

        pygame.draw.circle(self.screen, color, (jumpX, jumpY), radius)

        self.draw_boost(secondPlayer)
    

    def add_boost_particle(self, object : physics.Object, particles_lst: list):
        amountOfBoostBlocks = randint(10, PLAYER_HEIGHT-5)  # min of 10 blocks

        angle = object.angle if not object.flipObjectDraw else 180 - object.angle

        rectX, rectY = object.xPlace, object.yPlace - randint(0,10) # we will start drawing the blocks from the middle of the object and down
        rectX = rectX - 40 * math.cos(math.radians(angle)) + 20
        rectY = rectY + 40 * math.sin(math.radians(angle)) + 20

        particles_lst.append([time.time()])  # the first index of each row will be the time of when the player started it
        particles_lst[-1].append((rectX, rectY, amountOfBoostBlocks))


    def draw_boost_particles(self, particles_lst: list):
        # now we will draw the boost
        if len(particles_lst) > 0:
            for index, boostRow in enumerate(particles_lst):
                boostTime = time.time() - boostRow[0]
                if boostTime > 0.5:  # kill the boost row
                    del particles_lst[index]
                else:
                    rectX, rectY = boostRow[1][0], boostRow[1][1]
                    if -self.bg_x + self.width > rectX > -self.bg_x and -self.bg_y + self.height > rectY > -self.bg_y:  # if on screen
                        maxTimeR = 255/0.7
                        maxTimeG = 165/0.7

                        boost = pygame.Rect(rectX + self.bg_x, rectY + self.bg_y, BOOST_WIDTH, boostRow[1][2])
                        pygame.draw.rect(self.screen, (255 - boostTime * maxTimeR,165 - boostTime * maxTimeG,0), boost)

    
    # when player is boosting we will print his boost
    def draw_boost(self, secondPlayer : physics.Object):
        # we will add to the list number of rects
        if self.player.PlayerObject.IsBoosting and self.player.PlayerObject.boostAmount:
            self.add_boost_particle(self.player.PlayerObject, self.boostSprites)
        
        if type(secondPlayer) == physics.Object and secondPlayer.IsBoosting and secondPlayer.boostAmount:
            self.add_boost_particle(secondPlayer, self.secondplayerboostSprites)
        
        # now we will draw the boost
        self.draw_boost_particles(self.boostSprites)

        # seoncd player
            
        if type(secondPlayer) == physics.Object:
            self.draw_boost_particles(self.secondplayerboostSprites)
    
    def object_in_player_view(self, x, y, width, height):
        return (-self.bg_x + self.width > x > -self.bg_x or -self.bg_x + self.width > x + width > -self.bg_x)\
              and (-self.bg_y + self.height > y > -self.bg_y or -self.bg_y + self.height > y + height > -self.bg_y)

    def DrawBallAndSecondPlayer(self, secondPlayer:physics.Object, ball:physics.Ball):
        
        secondPlayerX,secondPlayerY = 0,0
        secondPlayerObject = type(secondPlayer) == physics.Object
        ballObject = type(ball) == physics.Ball
        if secondPlayerObject:
            secondPlayerX, secondPlayerY = secondPlayer.xPlace, secondPlayer.yPlace
        if ballObject:
            ballX, ballY = ball.xPlace, ball.yPlace

        if secondPlayerObject and self.object_in_player_view(secondPlayerX, secondPlayerY, PLAYER_WIDTH, PLAYER_HEIGHT):  # if on screen
            secondPlayerImage = self.player.player_image
            secondPlayerImage, rect = self.change_player_picture_with_angle(secondPlayerImage, secondPlayer.angle, secondPlayer.flipObjectDraw, secondPlayer)
            self.screen.blit(secondPlayerImage, (rect.x + self.bg_x, rect.y + self.bg_y))
        
        if ballObject and self.object_in_player_view(ballX, ballY, BALL_RADIUS, BALL_RADIUS):
            ballImage = pygame.transform.rotate(self.ballImage, ball.angle)
            rect = ballImage.get_rect(center=(ballX + BALL_RADIUS, ballY + BALL_RADIUS))
            self.screen.blit(ballImage, (rect.x + self.bg_x, rect.y + self.bg_y))


    def PutObjectInPlace(self, firstPlayer : bool) -> None:
        if firstPlayer:
            self.player.PlayerObject.xPlace = FIRST_PLAYER_POS[0]
            self.player.PlayerObject.yPlace = FIRST_PLAYER_POS[1]
        else:
            self.player.PlayerObject.xPlace = SECOND_PLAYER_POS[0]
            self.player.PlayerObject.yPlace = SECOND_PLAYER_POS[1]
            self.player.PlayerObject.flipObjectDraw = True


    def render_text(self, text, font, color):
        text_surface = font.render(text, True, color)
        return text_surface, text_surface.get_rect()
    
    
    def WaitFiveSeconds(self):
        font = pygame.font.Font(None, 100)
        t = time.time()
        wantedTime = t + 5  # wait for five seconds
        
        while wantedTime - t > 0:
            text_surface, text_rect = self.render_text(str(int(wantedTime - t)), font, (255, 215, 0))
            self.screen.blit(self.background_image, (self.bg_x, self.bg_y))
            self.screen.blit(text_surface, (self.width // 2, self.height // 2))

            pygame.display.flip()

            t = time.time()
    

    def startScreen(self):
        startScreen = pygame.image.load("startScreen.png").convert()
        startScreen = pygame.transform.scale(startScreen, (self.width, self.height))
        self.screen.blit(startScreen, (0,0))

        pygame.display.flip()

        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    run = False
            

    def menuScreen(self):
        menuScreen = pygame.image.load('menu.png').convert()
        menuScreen = pygame.transform.scale(menuScreen, (self.width, self.height))
        self.screen.blit(menuScreen, (0,0))

        pygame.display.flip()

        originalMenuSize = (3840,2160)
        originalGameRect = (1440, 480, 2350 - 1440, 1035 - 480)  # x, y, width, height
        originalFreePlayRect = (1440, 1190, 2350 - 1440, 1680 - 1090)  # x, y, width, height
        
        # game rect sizes
        x = self.width / (originalMenuSize[0] / originalGameRect[0])
        y = self.height / (originalMenuSize[1] / originalGameRect[1])
        width = self.width / (originalMenuSize[0] / originalGameRect[2])
        height = self.height / (originalMenuSize[1] / originalGameRect[3])
        gameRect = pygame.Rect(x, y, width, height)

        # free play rect sizes
        x = self.width / (originalMenuSize[0] / originalFreePlayRect[0])
        y = self.height / (originalMenuSize[1] / originalFreePlayRect[1])
        width = self.width / (originalMenuSize[0] / originalFreePlayRect[2])
        height = self.height / (originalMenuSize[1] / originalFreePlayRect[3])
        freePlayRect = pygame.Rect(x, y, width, height)

        run = True
        freePlay = False

        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()

                    if gameRect.collidepoint(pos):
                        run = False
                    elif freePlayRect.collidepoint(pos):
                        freePlay = True
                        run = False
        
        return freePlay


    def endGame(self, timeLeft, firstPlayerGoals, secondPlayerGoals, isFirstPlayer):
                # if game ended properly
        if self.gameNetwork.gameEnded or timeLeft <= 0:
            if isFirstPlayer and firstPlayerGoals >= secondPlayerGoals:
                winScreen = pygame.image.load('win.jpg').convert()
                winScreen = pygame.transform.scale(winScreen, (self.width, self.height))
                self.screen.blit(winScreen, (0,0))
            
            elif (not isFirstPlayer) and secondPlayerGoals >= firstPlayerGoals:
                winScreen = pygame.image.load('win.jpg').convert()
                winScreen = pygame.transform.scale(winScreen, (self.width, self.height))
                self.screen.blit(winScreen, (0,0))
            
            else:
                lostScreen = pygame.image.load('lost.jpg').convert()
                lostScreen = pygame.transform.scale(lostScreen, (self.width, self.height))
                self.screen.blit(lostScreen, (0,0))
            
            pygame.display.flip()

            time.sleep(5)
        
        # if game ended due to internter issues
        if self.gameNetwork.gameEndedEnt:
            internetScreen = pygame.image.load('error.jpg').convert()
            internetScreen = pygame.transform.scale(internetScreen, (self.width, self.height))
            self.screen.blit(internetScreen, (0,0))

            pygame.display.flip()

            time.sleep(5)


    def set_game(self):
        waitingScreen = pygame.image.load('waitingScreen.png').convert()
        waitingScreen = pygame.transform.scale(waitingScreen, (self.width, self.height))

        self.screen.blit(waitingScreen, (0,0))

        pygame.display.flip()
        music = pygame.mixer.music.load('menuMusic.mp3')

        pygame.mixer.music.play(loops=-1)
        self.gameNetwork = Server()

        if self.gameNetwork.nullObject or self.gameNetwork.gameEndedEnt:
            pygame.mixer.music.stop()
            return

        self.gameNetwork.get_starting_pos()
        if self.gameNetwork.gameEndedEnt:
            pygame.mixer.music.stop()
            return
        
        pygame.mixer.music.stop()

        self.PutObjectInPlace(self.gameNetwork.first_player)

        self.screen.blit(self.background_image, (0,0))
        self.WaitFiveSeconds()

        music = pygame.mixer.music.load('gameMusic.mp3')
        pygame.mixer.music.play(-1)


    def print_elements_screen(self, second_player : physics.Object, ball : physics.Ball, end_game_time, first_player_goals : int, second_player_goals : int):
        colorOfTimer = (255,215,0)
        font = pygame.font.Font(None, 50)

        self.correct_camera_view()  # get the camera right place
        player_image = self.player.player_image
        player_image, rect = self.change_player_picture_with_angle(player_image, self.player.PlayerObject.angle, self.player.PlayerObject.flipObjectDraw, self.player.PlayerObject)

        # Draw everything
        self.screen.blit(self.background_image, (self.bg_x, self.bg_y))
        self.draw_player_essentials(self.player.PlayerObject.xPlace + self.bg_x, self.player.PlayerObject.yPlace + self.bg_y, second_player)

        self.screen.blit(player_image, (rect.x + self.bg_x, rect.y + self.bg_y))
        self.DrawBallAndSecondPlayer(second_player, ball)

        # print block so that player will see the stats
        statsRect = pygame.Rect(self.width // 2 - 60, 0, 205, 60)
        pygame.draw.rect(self.screen, (0,0,0), statsRect)

        timeLeft = int(end_game_time - time.time())
        minutes, seconds = divmod(timeLeft, 60)
        timeInStr = f'{minutes:02d}:{seconds:02d}'  # format for minutes and seconds

        #print time
        text_surface, text_rect = self.render_text(timeInStr, font, colorOfTimer)
        self.screen.blit(text_surface, (self.width //2, 20))

        # print goals
        text_surface, text_rect = self.render_text(str(first_player_goals), font, (255,255,255))
        self.screen.blit(text_surface, (self.width //2 - 50, 20))

        text_surface, text_rect = self.render_text(str(second_player_goals), font, (255,255,255))
        self.screen.blit(text_surface, (self.width //2 + 120, 20))

        return timeLeft


    def GameLoop(self):
        self.set_game()

        if self.gameNetwork.nullObject:
            del self.gameNetwork
            return

        self.screen = pygame.display.set_mode((self.width, self.height), RESIZABLE)
        firstPlayerGoals = 0
        secondPlayerGoals = 0
        end_game_time = time.time() + 120  # two minutes from now
        th = threading.Thread(target=self.gameNetwork.game_handle, args=())
        th.start()
        print(f'New thread: {th}')
        while self.gameNetwork.running:

            self.player.PlayerObject = self.gameNetwork.player_object if self.gameNetwork.player_object != None and self.gameNetwork.player_object != "" else self.player.PlayerObject
            second_player = self.gameNetwork.second_player_object
            ball = self.gameNetwork.ball_object

            self.player.PlayerMotion()
            self.gameNetwork.send_player(self.player.PlayerObject)
            self.width, self.height = self.player.width, self.player.height

            time_left = self.print_elements_screen(second_player, ball, end_game_time, firstPlayerGoals, secondPlayerGoals)

            # Update the display
            pygame.display.update()

            # Cap the frame rate
            self.clock.tick(self.REFRESH_RATE)

            if type(ball) == physics.Ball and ball.inGoal:
                if self.gameNetwork.first_player:
                    self.player.PlayerObject.xPlace, self.player.PlayerObject.yPlace = FIRST_PLAYER_POS
                    self.player.PlayerObject.flipObjectDraw = False
                else:
                    self.player.PlayerObject.xPlace, self.player.PlayerObject.yPlace = SECOND_PLAYER_POS
                    self.player.PlayerObject.flipObjectDraw = True

                if ball.xPlace > 1000:  # right goal
                    firstPlayerGoals += 1
                else:
                    secondPlayerGoals += 1
                
                self.player.PlayerObject.xSpeed, self.player.PlayerObject.ySpeed = 0, 0
                end_game_time += 5  # the player waited five seconds so we add to the end time
                self.player.PlayerObject.boostAmount = 100
                self.gameNetwork.ball_object.inGoal = False

                self.gameNetwork.send_player(self.player.PlayerObject)
                self.WaitFiveSeconds()

            keys=pygame.key.get_pressed()
            # if player wants to get out in the middle of the game
            if keys[K_ESCAPE]:
                self.gameNetwork.running = False
            
            if time_left <= 0 or self.gameNetwork.gameEnded or self.gameNetwork.gameEndedEnt:
                self.gameNetwork.running = False
        
        th.join()
        pygame.mixer.music.stop()
        
        self.gameNetwork.close_game()
        self.endGame(int(end_game_time - time.time()), firstPlayerGoals, secondPlayerGoals, self.gameNetwork.first_player)


    def FreePlayLoop(self):
        self.screen = pygame.display.set_mode((self.width, self.height), RESIZABLE)
        running = True
        music = pygame.mixer.music.load('gameMusic.mp3')
        pygame.mixer.music.play(-1)

        goals = 0

        while running: 
            #for player in self.players:
            self.player.PlayerMotion()
            self.width, self.height = self.player.width, self.player.height

            keys=pygame.key.get_pressed()
            if keys[K_ESCAPE]:
                running = False

            self.ball.CalculateBallPlace([self.player.PlayerObject])

            self.print_elements_screen(None, self.ball, time.time(), goals, 0)

            # Update the display
            pygame.display.update()

            # Cap the frame rate
            self.clock.tick(self.REFRESH_RATE)

            # if there is a goal
            if self.ball.inGoal:
                self.WaitFiveSeconds()
                self.player.PlayerObject.xPlace, self.player.PlayerObject.yPlace = FIRST_PLAYER_POS
                self.player.PlayerObject.xSpeed, self.player.PlayerObject.ySpeed = 0, 0
                self.ball.xSpeed, self.ball.ySpeed = 0,0
                self.player.PlayerObject.flipObjectDraw = False
                self.ball.xPlace, self.ball.yPlace = BALL_STARTING_POS
                goals += 1
        
        pygame.mixer.music.stop()



    def MainLoop(self):
        self.startScreen()

        while True:
            isFreePlay = self.menuScreen()

            if not isFreePlay:
                self.GameLoop()
            else:
                self.FreePlayLoop()
            
            self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)            
            width, height = SCREEN.get_size()
            self.player = Player(width, height)
            self.ball.xPlace, self.ball.yPlace = BALL_STARTING_POS
            self.player.PlayerObject.xSpeed, self.player.PlayerObject.ySpeed = 0,0




class Player():
    def __init__(self, width, height):

        self.width = width
        self.height = height

        pygame.joystick.init()
        self.joystick = 0
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)


        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]  # set controller movement
        
        self.SetPlayers()

        self.PlayerObject = physics.Object(PLAYER_WIDTH, PLAYER_HEIGHT, 100, (self.player_rect.x, self.player_rect.y))

        self.accelrationX = 0
        self.accelrationY = 1

        self.PlayerTouchedControlrs = False
        self.IsBoosting = False
    
    #set players image
    def SetPlayers(self):
        self.player_image = pygame.transform.scale(pygame.image.load("player.png"), (PLAYER_WIDTH,PLAYER_HEIGHT))
        self.player_image.set_colorkey((0,0,0))
        self.player_image.convert_alpha()
        self.player_rect = self.player_image.get_rect()
        self.player_rect.x = 500
        self.player_rect.y = 850

    def HandleEvents(self):
        global RUN

        self.PlayerTouchedControlrs = False

        if self.PlayerObject.ObjectOnGround:
            self.PlayerObject.IsDoubleJumping = False

        # Handle events
        for event in pygame.event.get():
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or (event.type == JOYBUTTONDOWN and event.button == 0):  # because space key cannot be held down we need it as an event
                self.JumpingAction()
            if event.type == JOYDEVICEADDED:  # if the device was diconnected
                self.joystick = pygame.joystick.Joystick(0)
            if event.type == JOYDEVICEREMOVED:
                self.joystick = 0
            
            # if game was resized
            if event.type == pygame.WINDOWRESIZED:
                self.width, self.height = pygame.display.get_surface().get_size()
            # if game is closed
            if event.type == pygame.QUIT:
                RUN = False
                pygame.quit()
                sys.exit()


        # because the player usually presses the boost and not tapping it will not be as an event so we need to check it manually
        if self.joystick != 0 and self.joystick.get_button(1) and self.PlayerObject.boostAmount != 0:
            self.IsBoosting = True

        
        if self.joystick != 0:  # if joystick exist
            self.accelrationX = self.joystick.get_axis(0) # right and left
            self.accelrationY = self.joystick.get_axis(1) # up and down
            self.accelrationX = 0 if abs(self.accelrationX) < 0.1 else self.accelrationX
            self.accelrationY = 1 if abs(self.accelrationY) < 0.1 else self.accelrationY
            self.PlayerTouchedControlrs = False if self.accelrationX == 0 and self.accelrationY == 1 else True
       
    def KeyboardMotion(self):

        self.PlayerTouchedControlrs = False

        keys = pygame.key.get_pressed()  # get the keys which are pressed
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.accelrationX = -1
            self.PlayerTouchedControlrs = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.accelrationX = 1
            self.PlayerTouchedControlrs = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.accelrationY = -1
            self.PlayerTouchedControlrs = True
        # because going down is just as only gravity working we dont need to check if player going down
        if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and self.PlayerObject.boostAmount != 0:
            self.IsBoosting = True

    def JumpingAction(self):
        if self.PlayerObject.ObjectOnGround:
            self.PlayerObject.IsJumping = True
        elif not self.PlayerObject.ObjectOnGround and not self.PlayerObject.IsDoubleJumping:
            self.PlayerObject.IsJumping = True
            self.PlayerObject.IsDoubleJumping = True

    def PlayerMotion(self):
        
        self.HandleEvents()
        if not self.PlayerTouchedControlrs:
            self.KeyboardMotion()

        #print(self.accelrationX, self.accelrationY)

        self.PlayerObject.CalculateObjectPlace(self.accelrationX, self.accelrationY,self.PlayerObject.IsJumping, self.PlayerTouchedControlrs, self.IsBoosting)
        self.player_rect.x, self.player_rect.y = self.PlayerObject.xPlace, self.PlayerObject.yPlace

        isPlayerBoosting = self.IsBoosting
        self.accelrationX,self.accelrationY, self.PlayerObject.IsJumping, self.IsBoosting = 0,1,False, False
        


def main():
    width, height = SCREEN.get_size()
    player = Player(width, height)
    game = Game(player)
    game.MainLoop()



    pygame.quit()
    sys.exit()



if __name__ == '__main__':
    main()