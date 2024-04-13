import pygame
import sys
from pygame.locals import *
import math
import physics

WIDTH_SCREEN_VIEW = 1500
HEIGHT_SCREEN_VIEW = 800

# Initialize Pygame
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH_SCREEN_VIEW, HEIGHT_SCREEN_VIEW))

class Server:
    pass


class Game:
    #Frames in second - cycles
    REFRESH_RATE = 60
    
    #Set Clock
    clock = pygame.time.Clock()
    
    def __init__(self, players):

        self.players = players
        self.screen = SCREEN
        pygame.display.set_caption("Rocket League")

        # Load the background image
        self.background_image = pygame.image.load("background.png").convert()
    

    def ChangePlayerPictureWithAngle(self, image):
        newAngle = self.players.PlayerObject.angle
        flipX = self.players.PlayerObject.flipObjectDraw
        
        image = pygame.transform.rotate(image, newAngle)
        return pygame.transform.flip(image, flipX, False) 
            

    def CorrectCameraView(self):  # we need to correct the camera view so it won't go out of the screen

        bg_x = WIDTH_SCREEN_VIEW // 2 - self.players.player_rect.centerx
        bg_y = HEIGHT_SCREEN_VIEW // 2 - self.players.player_rect.centery

        if bg_x >= 0:  # if the player is right to the left barrier, bg_x will be minus
            bg_x = 0  # dont let it go over the limit
        elif bg_x <= -995:  # right wall
            bg_x = -995 
        if bg_y >= 0:  # ceiling height
            bg_y = 0
        elif bg_y <= -260:  # floor height
            bg_y = -260
        
        return bg_x, bg_y
    
    def CorrectPlayerPlace(self, bg_x, bg_y):  # when the map is on the sides we need to fix the player place so it will be in the right place
        xDiff = 0
        yDiff = 0
        if bg_x == 0:
            xDiff = -((bg_x - self.players.player_rect.x) % 725)  # - because we add the xdiff
        elif bg_x == -995:
            xDiff = self.players.player_rect.x - 1725
        if bg_y == -260:
            yDiff = 200 - abs(self.players.player_rect.y - 850)  # the floor is 850 so if the player is on the floor 
        elif bg_y == 0:
            yDiff = self.players.player_rect.y - 388

        return xDiff,yDiff
    
    def ZoomOnPlayerImage(self):  # returned the player image after zooming on it
        zoom_level = 1.5  # Change this value to adjust zoom level
        zoomed_player_image = pygame.transform.scale(self.players.player_image, (int(self.players.player_rect.width * zoom_level),
                                                                    int(self.players.player_rect.height * zoom_level)))
        
        return zoomed_player_image


    def MainLoop(self):
        running = True
        while running:
            
            
            #for player in self.players:
            self.players.PlayerMotion()

            bg_x, bg_y = self.CorrectCameraView()  # get the camera right place
            zoomed_player_image = self.ZoomOnPlayerImage()
            zoomed_player_image = self.ChangePlayerPictureWithAngle(zoomed_player_image)
            
            xDiff, yDiff = self.CorrectPlayerPlace(bg_x, bg_y)  #  move the player to be on the right place on screen
            zoomed_player_rect = zoomed_player_image.get_rect(center=(WIDTH_SCREEN_VIEW // 2 + xDiff, HEIGHT_SCREEN_VIEW // 2 + yDiff))

            # Draw everything
            self.screen.blit(self.background_image, (bg_x, bg_y))
            self.screen.blit(zoomed_player_image, zoomed_player_rect.topleft)


            # Update the display
            pygame.display.update()

            # Cap the frame rate
            self.clock.tick(self.REFRESH_RATE)



class Player():
    def __init__(self):

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
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or event.type == JOYBUTTONDOWN:  # because space key cannot be held down we need it as an event
                self.JumpingAction()
            if event.type == JOYDEVICEADDED:  # if the device was diconnected
                self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
            if event.type == JOYDEVICEREMOVED:
                self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        
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

        self.PlayerObject.CalculateObjectPlace(self.accelrationX, self.accelrationY,self.IsJumping, self.PlayerTouchedControlrs)
        self.player_rect.x, self.player_rect.y = self.PlayerObject.xPlace, self.PlayerObject.yPlace

        self.accelrationX,self.accelrationY, self.IsJumping = 0,1,False
            
        


player = Player()
game = Game(player)
game.MainLoop()

pygame.quit()
sys.exit()
