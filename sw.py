import pygame
import sys
from pygame.locals import *
import math
import time

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
        newAngle = 0
        flipY = False
        flipX = False
        
        
        image = pygame.transform.rotate(image, newAngle)
        return pygame.transform.flip(image, flipX, flipY) 
            

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
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.players.ControllerMovement(event)
            
            
            
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

    # heights and x values of walls
    FLOOR_HEIGHT = 850
    CEILING_HEIGHT = 100
    RIGHT_WALL = 2150
    LEFT_WALL = 300
    DISTANCE_FROM__WALL = 110  # distance from wall of ramp

    GRAVITY_FORCE = 1000  # gravity on player

    REFRESH_RATE_TIME = 1/60  # we need the refresh rate time to calculate time differences

    MAX_SPEED = 350

    def __init__(self):
        
        self.MAX_VECTOR = 1000

        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]  # set controller movement
        self.angle = 0  # set angle of player

        # we will use for this game two vectors, xVector and yVector
        self.xVector = 0
        self.yVector = self.GRAVITY_FORCE
        
        self.SetPlayers()


        #to calculate the vectors we will need to have the previous x and y
        self.prevX = self.player_rect.x
        self.prevY = self.player_rect.y

        # and also need current speed
        self.xSpeed = 0
        self.ySpeed = 0
    
    #set players image
    def SetPlayers(self):
        self.player_image = pygame.transform.scale(pygame.image.load("player.png"), (50,25))
        self.player_image.set_colorkey((0,0,0))
        self.player_image.convert_alpha()
        self.player_rect = self.player_image.get_rect()
        self.player_rect.x = 500
        self.player_rect.y = 850

    #controls of the game - controller and keyboard
    def ControllerMovement(self, event):
        if event.type == JOYDEVICEADDED:  # if the device was diconnected
            self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
            for joystick in self.joysticks:
                print(joystick.get_name())
        if event.type == JOYDEVICEREMOVED:
            self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        if event.type == JOYBUTTONDOWN:  # if button was pressed
            if event.button == 1:  # if O button was pressed
                self.speed *= 2
            #elif event.button == 0 and not self.inJump:  #if player pressed jump and already in jump
            #    self.time = time.time()
            #    self.PlayerJump()
                
        if event.type == JOYBUTTONUP:  # if button was released
            if event.button == 1:  # if O button was released
                self.speed /= 2

        self.xVector = self.joystick.get_axis(0) * self.MAX_VECTOR
        self.yVector += self.joystick.get_axis(1) * self.GRAVITY_FORCE
       
    def KeyboardMotion(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.xVector = -self.MAX_VECTOR
        if keys[pygame.K_RIGHT]:
            self.xVector = self.MAX_VECTOR
        if keys[pygame.K_UP]:
            self.yVector = self.GRAVITY_FORCE / 2
        if keys[pygame.K_DOWN]:
            self.yVector = self.GRAVITY_FORCE * 1.5
        if keys[pygame.K_SPACE]:# and if not on a wall
            self.yVector = -self.GRAVITY_FORCE * 15

   
    def __Function(self, x):
        return (x**2) / 100

    def __DerivativeFunction(self, x):
        return 2*x / 100

    # the sides of the map require the player to change its angle
    def __GetPlayerAngleOnSides(self, xDiff):
        # we will get the angle of the player with incline of the function
        incline = self.__DerivativeFunction(xDiff)
        self.angle = math.degrees(math.atan(incline)) * 1.168  # shift tan of the incline
        self.angle = int(self.angle)
    

    #the player need to adjust its angle
    def PlayerOnRamps(self):
        xPlayer = self.player_rect.x

        #check if right wall
        if self.RIGHT_WALL - xPlayer < self.DISTANCE_FROM__WALL:  # right wall
            xDiffRightWall = self.DISTANCE_FROM__WALL - (self.RIGHT_WALL - xPlayer)
            self.player_rect.y = self.FLOOR_HEIGHT - self.__Function(xDiffRightWall) if self.FLOOR_HEIGHT - self.player_rect.y <= self.__Function(xDiffRightWall)\
                                 else self.CEILING_HEIGHT + self.__Function(xDiffRightWall) if self.player_rect.y - self.CEILING_HEIGHT < self.__Function(xDiffRightWall)\
                                 else self.player_rect.y
        elif xPlayer - self.LEFT_WALL < self.DISTANCE_FROM__WALL:  # left wall
            xDiffLeftWall = self.DISTANCE_FROM__WALL - (xPlayer - self.LEFT_WALL)
            self.player_rect.y = self.FLOOR_HEIGHT - self.__Function(xDiffLeftWall) if self.FLOOR_HEIGHT - self.player_rect.y <= self.__Function(xDiffLeftWall)\
                                 else self.CEILING_HEIGHT + self.__Function(xDiffLeftWall) if self.player_rect.y - self.CEILING_HEIGHT < self.__Function(xDiffLeftWall)\
                                 else self.player_rect.y
        
        
    # prevent the player from moving beyond walls
    def PlayerBoundaries(self):
        if self.player_rect.x < self.LEFT_WALL:
            self.player_rect.x = self.LEFT_WALL
            self.xSpeed = 0
        elif self.player_rect.x > self.RIGHT_WALL:
            self.player_rect.x = self.RIGHT_WALL
            self.xSpeed = 0

        if self.player_rect.y > self.FLOOR_HEIGHT:
            self.player_rect.y = self.FLOOR_HEIGHT
            self.ySpeed = 0
        elif self.player_rect.y < self.CEILING_HEIGHT:
            self.player_rect.y = self.CEILING_HEIGHT
            self.ySpeed = 0
    

    #this function will calculate where the players need to be according to the vectors
    def CalculatePlayerPlace(self):
        # we will use the physics function - currentPlace = placeBefore + speedBefore*timeDiff + (acceleration / 2) * timeDiff ** 2
        # we will use this function for both of the axis, one for the x axis and one for the y axis

        # firstly we will need the speed which we will calculate 
        # we will use currentSpeed = prevSpeed + acceleration * timeDiff
        self.xSpeed = self.xSpeed + self.xVector * self.REFRESH_RATE_TIME
        self.ySpeed = self.ySpeed + self.yVector * self.REFRESH_RATE_TIME

        self.xSpeed = self.MAX_SPEED if self.xSpeed > self.MAX_SPEED else -self.MAX_SPEED if self.xSpeed < -self.MAX_SPEED else self.xSpeed
        self.ySpeed = self.MAX_SPEED * 2 if self.ySpeed > self.MAX_SPEED * 2 else -self.MAX_SPEED * 2 if self.ySpeed < -self.MAX_SPEED * 2 else self.ySpeed

        # now lets put it into the current place

        xDiff = self.xSpeed*self.REFRESH_RATE_TIME + (self.xVector / 2) * self.REFRESH_RATE_TIME ** 2
        yDiff = self.ySpeed*self.REFRESH_RATE_TIME + (self.yVector / 2) * self.REFRESH_RATE_TIME ** 2

        self.player_rect.x = self.prevX + xDiff
        self.player_rect.y = self.prevY + yDiff

        # now we return the vectors to the starting phase
        self.xVector = 0
        self.yVector = self.GRAVITY_FORCE


    def PlayerMotion(self):
        # save the last place 
        self.prevX = self.player_rect.x
        self.prevY = self.player_rect.y
        
        self.KeyboardMotion()
        self.CalculatePlayerPlace()
        self.PlayerOnRamps()
        self.PlayerBoundaries()






            
        


player = Player()
game = Game(player)
game.MainLoop()

pygame.quit()
sys.exit()
