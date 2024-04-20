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


class Server:
    SERVER_IP = '127.0.0.1'

    def __init__(self):
        self.SERVER_PORT = 1393

        self.playerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.playerSocket.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_CONNECTING, None), (self.SERVER_IP, self.SERVER_PORT))
    
    def RecvMsg(self):
        try:
            buffer,_ = self.playerSocket.recvfrom(protocol.MAX_MESSAGE_LENGTH)
            size = int(buffer[:protocol.BUFFER_LENGTH_SIZE].decode())  # get size

            buffer = buffer[protocol.BUFFER_LENGTH_SIZE:]
            
            if size != len(buffer):
                raise Exception("Data corrupted")

            return buffer
        except socket.error as e:
            print(f"socket does not exist, disconnecting it")
            return None


    def WaitForGame(self):
        # switching to new port
        self.SERVER_PORT = int(self.RecvMsg().decode().split('~')[1])

        msg_from_server = self.RecvMsg().decode().split('~')[0]
        while not msg_from_server == protocol.STARTING_GAME:
            msg_from_server = self.RecvMsg().decode().split('~')[0]
        

    
    
    # we only need one bool to know where to place everyone
    # this bool will indicate if we are the first or the second player
    # if we are the first we will start at FIRST_PLAYER_POS and so for the second player
    # if the bool is True we are the first player
    def GetStartingPos(self) -> bool:
        isFirstPlayer = int(self.RecvMsg()[protocol.BUFFER_LENGTH_SIZE:])

        return isFirstPlayer

    def GameHandling(self, playerObject: physics.Object):
        pickleObject = pickle.dumps(playerObject)
        self.playerSocket.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, pickleObject), (self.SERVER_IP, self.SERVER_PORT))

        secondPlayler = self.RecvMsg()[protocol.BUFFER_LENGTH_SIZE:]
        ball = self.RecvMsg()[protocol.BUFFER_LENGTH_SIZE:]

        return secondPlayler, ball




class Game:
    #Frames in second - cycles
    REFRESH_RATE = 60
    
    #Set Clock
    clock = pygame.time.Clock()
    
    def __init__(self, player):

        self.player = player
        self.width = self.player.width
        self.height = self.player.height

        self.screen = pygame.display.set_mode((self.width, self.height), RESIZABLE)
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
    

    def ChangePlayerPictureWithAngle(self, image, angle, flipObjectDraw, car: physics.Object):
        image = pygame.transform.rotate(image, angle)
        image = pygame.transform.flip(image, flipObjectDraw, False) 
        rect = image.get_rect(center=(car.xPlace + PLAYER_WIDTH / 2, car.yPlace + PLAYER_HEIGHT / 2))
        return image, rect
            

    def CorrectCameraView(self):
        self.bg_x = -self.player.player_rect.x + self.width // 2
        self.bg_y = -self.player.player_rect.y + self.height // 2

        self.bg_x = 0 if self.bg_x >= 0 else -(RIGHT_WALL_BACKGROUND - self.width) if -self.bg_x >= RIGHT_WALL_BACKGROUND - self.width else self.bg_x
        self.bg_y = 0 if self.bg_y >= 0 else -(FLOOR_BACKGOURND - self.height) if -self.bg_y >= FLOOR_BACKGOURND - self.height else self.bg_y
        

    def DrawPlayerEssntials(self, xOfPlayerOnScreen : int, yOfPlayerOnScreen : int, secondPlayer :physics.Object):

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
        color = GREEN if not self.player.IsDoubleJumping else GRAY

        pygame.draw.circle(self.screen, color, (jumpX, jumpY), radius)

        self.DrawBoost(secondPlayer)
    
    
    # when player is boosting we will print his boost
    def DrawBoost(self, secondPlayer:physics.Object):
        # we will add to the list number of rects
        if self.player.PlayerObject.IsBoosting and self.player.PlayerObject.boostAmount:
            amountOfBoostBlocks = randint(10, PLAYER_HEIGHT-5)  # min of 10 blocks

            angle = self.player.PlayerObject.angle if not self.player.PlayerObject.flipObjectDraw else 180 - self.player.PlayerObject.angle

            rectX, rectY = self.player.player_rect.x, self.player.player_rect.y - randint(0,10) # we will start drawing the blocks from the middle of the object and down
            rectX = rectX - 40 * math.cos(math.radians(angle)) + 20
            rectY = rectY + 40 * math.sin(math.radians(angle)) + 20

            self.boostSprites.append([time.time()])  # the first index of each row will be the time of when the player started it
            self.boostSprites[-1].append((rectX, rectY, amountOfBoostBlocks))
        
        if secondPlayer != None and secondPlayer.IsBoosting and secondPlayer.boostAmount:
            amountOfBoostBlocks = randint(10, PLAYER_HEIGHT-5)  # min of 10 blocks

            angle = secondPlayer.angle if not secondPlayer.flipObjectDraw else 180 - secondPlayer.angle

            rectX, rectY = secondPlayer.xPlace, secondPlayer.yPlace - randint(0,10) # we will start drawing the blocks from the middle of the object and down
            rectX = rectX - 40 * math.cos(math.radians(angle)) + 20
            rectY = rectY + 40 * math.sin(math.radians(angle)) + 20

            self.secondplayerboostSprites.append([time.time()])  # the first index of each row will be the time of when the player started it
            self.secondplayerboostSprites[-1].append((rectX, rectY, amountOfBoostBlocks))
        
        # now we will draw the boost
        if len(self.boostSprites) > 0:
            for index, boostRow in enumerate(self.boostSprites):
                boostTime = time.time() - boostRow[0]
                if boostTime > 0.5:  # kill the boost row
                    del self.boostSprites[index]
                else:
                    rectX, rectY = boostRow[1][0], boostRow[1][1]
                    if -self.bg_x + self.width > rectX > -self.bg_x and -self.bg_y + self.height > rectY > -self.bg_y:  # if on screen
                        maxTimeR = 255/0.7
                        maxTimeG = 165/0.7

                        boost = pygame.Rect(rectX + self.bg_x, rectY + self.bg_y, BOOST_WIDTH, boostRow[1][2])
                        pygame.draw.rect(self.screen, (255 - boostTime * maxTimeR,165 - boostTime * maxTimeG,0), boost)
            
        if len(self.secondplayerboostSprites) > 0 and secondPlayer != None:
            for index, boostRow in enumerate(self.secondplayerboostSprites):
                boostTime = time.time() - boostRow[0]
                if boostTime > 0.5:  # kill the boost row
                    del self.secondplayerboostSprites[index]
                else:
                    rectX, rectY = boostRow[1][0], boostRow[1][1]
                    if -self.bg_x + self.width > rectX > -self.bg_x and -self.bg_y + self.height > rectY > -self.bg_y:  # if on screen
                        maxTimeR = 255/0.7
                        maxTimeG = 165/0.7

                        boost = pygame.Rect(rectX + self.bg_x, rectY + self.bg_y, BOOST_WIDTH, boostRow[1][2])
                        pygame.draw.rect(self.screen, (255 - boostTime * maxTimeR,165 - boostTime * maxTimeG,0), boost)
        

    def DrawBallAndSecondPlayer(self, secondPlayer:physics.Object, ball:physics.Ball):
        
        secondPlayerX,secondPlayerY = 0,0
        if secondPlayer != None:
            secondPlayerX, secondPlayerY = secondPlayer.xPlace, secondPlayer.yPlace
        if ball != None:
            ballX, ballY = ball.xPlace, ball.yPlace

        if secondPlayer != None and (-self.bg_x + self.width > secondPlayerX > -self.bg_x or -self.bg_x + self.width > secondPlayerX + PLAYER_WIDTH > -self.bg_x)\
              and (-self.bg_y + self.height > secondPlayerY > -self.bg_y or -self.bg_y + self.height > secondPlayerY + PLAYER_HEIGHT > -self.bg_y):  # if on screen
            secondPlayerImage = self.player.player_image
            secondPlayerImage, rect = self.ChangePlayerPictureWithAngle(secondPlayerImage, secondPlayer.angle, secondPlayer.flipObjectDraw, secondPlayer)
            self.screen.blit(secondPlayerImage, (rect.x + self.bg_x, rect.y + self.bg_y))
        
        if (-self.bg_x + self.width > ballX > -self.bg_x or -self.bg_x + self.width > ballX + BALL_RADIUS > -self.bg_x)\
              and (-self.bg_y + self.height > ballY > -self.bg_y or -self.bg_y + self.height > ballY + BALL_RADIUS > -self.bg_y):
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


    def GameLoop(self):
        colorOfTimer = (255,215,0)
        font = pygame.font.Font(None, 50)


        waitingScreen = pygame.image.load('waitingScreen.png').convert()
        waitingScreen = pygame.transform.scale(waitingScreen, (self.width, self.height))

        self.screen.blit(waitingScreen, (0,0))

        pygame.display.flip()

        self.gameNetwork = Server()
        self.gameNetwork.WaitForGame()
        isFirstPlayer = self.gameNetwork.GetStartingPos()
        self.PutObjectInPlace(isFirstPlayer)

        self.screen.blit(self.background_image, (0,0))
        self.WaitFiveSeconds()

        secondPlayer, ball = None, None
        firstPlayerGoals = 0
        secondPlayerGoals = 0

        running = True
        endGameTime = time.time() + 120  # two minutes from now
        while running: 
            #for player in self.players:
            self.player.PlayerMotion()
            self.width, self.height = self.player.width, self.player.height

            secondPlayer, ball = self.gameNetwork.GameHandling(self.player.PlayerObject)
            secondPlayer, ball = pickle.loads(secondPlayer), pickle.loads(ball)
            ball.BallBouncesPlayer(self.player.PlayerObject)

            self.CorrectCameraView()  # get the camera right place
            player_image = self.player.player_image
            player_image, rect = self.ChangePlayerPictureWithAngle(player_image, self.player.PlayerObject.angle, self.player.PlayerObject.flipObjectDraw, self.player.PlayerObject)

            # Draw everything
            self.screen.blit(self.background_image, (self.bg_x, self.bg_y))
            self.DrawPlayerEssntials(self.player.player_rect.x + self.bg_x, self.player.player_rect.y + self.bg_y, secondPlayer)

            self.screen.blit(player_image, (rect.x + self.bg_x, rect.y + self.bg_y))
            self.DrawBallAndSecondPlayer(secondPlayer, ball)

            # print block so that player will see the stats
            statsRect = pygame.Rect(self.width // 2 - 60, 0, 205, 60)
            pygame.draw.rect(self.screen, (0,0,0), statsRect)

            timeLeft = int(endGameTime - time.time())
            minutes, seconds = divmod(timeLeft, 60)
            timeInStr = f'{minutes:02d}:{seconds:02d}'  # format for minutes and seconds

            #print time
            text_surface, text_rect = self.render_text(timeInStr, font, colorOfTimer)
            self.screen.blit(text_surface, (self.width //2, 20))

            # print goals
            text_surface, text_rect = self.render_text(str(firstPlayerGoals), font, (255,255,255))
            self.screen.blit(text_surface, (self.width //2 - 50, 20))

            text_surface, text_rect = self.render_text(str(secondPlayerGoals), font, (255,255,255))
            self.screen.blit(text_surface, (self.width //2 + 120, 20))

            # Update the display
            pygame.display.update()

            # Cap the frame rate
            self.clock.tick(self.REFRESH_RATE)

            if ball.inGoal:
                self.WaitFiveSeconds()

                if isFirstPlayer:
                    self.player.PlayerObject.xPlace, self.player.PlayerObject.yPlace = FIRST_PLAYER_POS
                    self.player.PlayerObject.flipObjectDraw = False
                else:
                    self.player.PlayerObject.xPlace, self.player.PlayerObject.yPlace = SECOND_PLAYER_POS
                    self.player.PlayerObject.flipObjectDraw = False

                if ball.xPlace > 1000:  # right goal
                    firstPlayerGoals += 1
                else:
                    secondPlayerGoals += 1
                
                self.player.PlayerObject.xSpeed, self.player.PlayerObject.ySpeed = 0, 0
                endGameTime += 5  # the player waited five seconds so we add to the end time




    def FreePlayLoop(self):
        running = True
        while running: 
            #for player in self.players:
            self.player.PlayerMotion()
            self.width, self.height = self.player.width, self.player.height

            self.ball.CalculateBallPlace([self.player.PlayerObject])
            self.ball.BallBouncesPlayer(self.player.PlayerObject)

            self.CorrectCameraView()  # get the camera right place
            player_image = self.player.player_image
            player_image, rect = self.ChangePlayerPictureWithAngle(player_image, self.player.PlayerObject.angle, self.player.PlayerObject.flipObjectDraw, self.player.PlayerObject)

            # Draw everything
            self.screen.blit(self.background_image, (self.bg_x, self.bg_y))
            self.DrawPlayerEssntials(self.player.player_rect.x + self.bg_x, self.player.player_rect.y + self.bg_y, None)

            self.screen.blit(player_image, (rect.x + self.bg_x, rect.y + self.bg_y))
            self.DrawBallAndSecondPlayer(None, self.ball)

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
                self.ball.xPlace, self.ball.yPlace = BALL_STARTING_POS



    def MainLoop(self):
        self.startScreen()
        isFreePlay = self.menuScreen()

        if not isFreePlay:
            self.GameLoop()
        else:
            self.FreePlayLoop()



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

        self.IsJumping = False
        self.IsDoubleJumping = False

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

        self.PlayerTouchedControlrs = False

        if self.PlayerObject.ObjectOnGround:
            self.IsDoubleJumping = False

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
                pygame.quit()
                sys.exit()


        # because the player usually presses the boost and not tapping it will not be as an event so we need to check it manually
        if self.joystick != 0 and self.joystick.get_button(1):
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
        
        if keys[pygame.K_LEFT]:
            self.accelrationX = -1
            self.PlayerTouchedControlrs = True
        if keys[pygame.K_RIGHT]:
            self.accelrationX = 1
            self.PlayerTouchedControlrs = True
        if keys[pygame.K_UP]:
            self.accelrationY = -1
            self.PlayerTouchedControlrs = True
        # because going down is just as only gravity working we dont need to check if player going down
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            self.IsBoosting = True

    def JumpingAction(self):
        if self.PlayerObject.ObjectOnGround:
            self.IsJumping = True
        elif not self.PlayerObject.ObjectOnGround and not self.IsDoubleJumping:
            self.IsJumping = True
            self.IsDoubleJumping = True

    def PlayerMotion(self):
        
        self.HandleEvents()
        if not self.PlayerTouchedControlrs:
            self.KeyboardMotion()

        #print(self.accelrationX, self.accelrationY)

        self.PlayerObject.CalculateObjectPlace(self.accelrationX, self.accelrationY,self.IsJumping, self.PlayerTouchedControlrs, self.IsBoosting)
        self.player_rect.x, self.player_rect.y = self.PlayerObject.xPlace, self.PlayerObject.yPlace

        isPlayerBoosting = self.IsBoosting
        self.accelrationX,self.accelrationY, self.IsJumping, self.IsBoosting = 0,1,False, False
        

width, height = SCREEN.get_size()
player = Player(width, height)
game = Game(player)
game.MainLoop()



pygame.quit()
sys.exit()
