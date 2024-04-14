import pygame
import sys
from pygame.locals import *
import physics
import math


RIGHT_WALL_BACKGROUND = 2497
FLOOR_BACKGOURND = 1057

GREEN = (0, 255, 0)
GRAY = (128,128,128)

# Initialize Pygame
pygame.init()
infoScreen = pygame.display.Info()
width = infoScreen.current_w if infoScreen.current_w < RIGHT_WALL_BACKGROUND else RIGHT_WALL_BACKGROUND
height = infoScreen.current_h if infoScreen.current_h < FLOOR_BACKGOURND else FLOOR_BACKGOURND
SCREEN = pygame.display.set_mode((width, height))


class Server:
    pass


class Game:
    #Frames in second - cycles
    REFRESH_RATE = 60
    
    #Set Clock
    clock = pygame.time.Clock()
    
    def __init__(self, players):

        self.players = players
        self.width = self.players.width
        self.height = self.players.height
        self.screen = pygame.display.set_mode((self.width, self.height), RESIZABLE)
        pygame.display.set_caption("Rocket League")

        # Load the background image
        self.background_image = pygame.image.load("background.png").convert()
    

    def ChangePlayerPictureWithAngle(self, image):
        newAngle = self.players.PlayerObject.angle
        flipX = self.players.PlayerObject.flipObjectDraw
        
        image = pygame.transform.rotate(image, newAngle)
        return pygame.transform.flip(image, flipX, False) 
            

    def CorrectCameraView(self):
        bg_x = -self.players.player_rect.x + self.width // 2
        bg_y = -self.players.player_rect.y + self.height // 2

        bg_x = 0 if bg_x >= 0 else -(RIGHT_WALL_BACKGROUND - self.width) if -bg_x >= RIGHT_WALL_BACKGROUND - self.width else bg_x
        bg_y = 0 if bg_y >= 0 else -(FLOOR_BACKGOURND - self.height) if -bg_y >= FLOOR_BACKGOURND - self.height else bg_y
        
        return bg_x, bg_y
    
    def CorrectPlayerPlace(self, bg_x, bg_y):
        xDiff = 0
        yDiff = 0

        if bg_x == 0:
            xDiff = -((bg_x - self.players.player_rect.x) % (self.width // 2))
        elif bg_x == -(RIGHT_WALL_BACKGROUND - self.width):
            xDiff = -(-bg_x + self.width // 2 - self.players.player_rect.x)

        if bg_y == 0:
            yDiff = self.players.player_rect.y - (self.height // 2)
        elif bg_y == -(FLOOR_BACKGOURND - self.height):
            yDiff = -(-bg_y + self.height // 2 - self.players.player_rect.y)

        return xDiff, yDiff
    
    def ZoomOnPlayerImage(self):  # returned the player image after zooming on it
        zoom_level = 1.5  # Change this value to adjust zoom level
        zoomed_player_image = pygame.transform.scale(self.players.player_image, (int(self.players.player_rect.width * zoom_level),
                                                                    int(self.players.player_rect.height * zoom_level)))
        
        return zoomed_player_image

    def DrawPlayerEssntials(self, xOfPlayerOnScreen, yOfPlayerOnScreen):

        # draw boost
        amountOfBoost = (self.players.PlayerObject.boostAmount / physics.MAX_BOOST) * 100

        boostX = xOfPlayerOnScreen - 50
        boostY = yOfPlayerOnScreen - 50

        boostRect = pygame.Rect(boostX, boostY, amountOfBoost, 20)
        pygame.draw.rect(self.screen, GREEN, boostRect)

        # draw is able to jump
        jumpX = xOfPlayerOnScreen
        jumpY = yOfPlayerOnScreen - 70
        radius = 10
        color = GREEN if not self.players.IsDoubleJumping else GRAY

        pygame.draw.circle(self.screen, color, (jumpX, jumpY), radius)




    def MainLoop(self):
        running = True
        while running:
            
            
            #for player in self.players:
            self.players.PlayerMotion()
            self.width, self.height = self.players.width, self.players.height

            bg_x, bg_y = self.CorrectCameraView()  # get the camera right place
            zoomed_player_image = self.ZoomOnPlayerImage()
            zoomed_player_image = self.ChangePlayerPictureWithAngle(zoomed_player_image)
            
            xDiff, yDiff = self.CorrectPlayerPlace(bg_x, bg_y)  #  move the player to be on the right place on screen
            zoomed_player_rect = zoomed_player_image.get_rect(center=(self.width // 2 + xDiff, self.height // 2 + yDiff))

            # Draw everything
            self.screen.blit(self.background_image, (bg_x, bg_y))
            self.screen.blit(zoomed_player_image, zoomed_player_rect.topleft)

            self.DrawPlayerEssntials(self.width // 2 + xDiff, self.height // 2 + yDiff)

            # Update the display
            pygame.display.update()

            # Cap the frame rate
            self.clock.tick(self.REFRESH_RATE)



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

        self.PlayerObject = physics.Object(100, 75, 100, (self.player_rect.x, self.player_rect.y))

        self.accelrationX = 0
        self.accelrationY = 1

        self.IsJumping = False
        self.IsDoubleJumping = False

        self.PlayerTouchedControlrs = False
        self.IsBoosting = False
    
    #set players image
    def SetPlayers(self):
        self.player_image = pygame.transform.scale(pygame.image.load("player.png"), (50,25))
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
                self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
            if event.type == JOYDEVICEREMOVED:
                self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

            
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

        self.accelrationX,self.accelrationY, self.IsJumping, self.IsBoosting = 0,1,False, False
            
        


width, height = SCREEN.get_size()
player = Player(width, height)
game = Game(player)
game.MainLoop()

pygame.quit()
sys.exit()
