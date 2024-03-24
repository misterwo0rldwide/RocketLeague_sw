import pygame
import sys
from pygame.locals import *
import math
import time



# Initialize Pygame
pygame.init()

class Server:
    pass


class Game:
    #Frames in second - cycles
    REFRESH_RATE = 60
    
    
    #Set Clock
    clock = pygame.time.Clock()
    
    def __init__(self, width, height):
        
        self.width = width
        self.height = height
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Rocket League")

        # Load the background image
        self.background_image = pygame.image.load("background.png").convert()
    
    def GetPlayers(self, players):
        self.players = players
    
    def ChangePlayerPictureWithAngle(self, image):
        if 0 <= self.players.angle <= 90:  # turning right on the ground
            image = pygame.transform.rotate(image, self.angle)
            return pygame.transform.flip(image, False, False)
        elif 90 <= self.players.angle <= 180:  # turning left on the ground
            image = pygame.transform.rotate(image, 180 - self.angle)
            return pygame.transform.flip(image, True, False)
        elif 180 <= self.players.angle <= 270:  # turning left on the ceiling
            image = pygame.transform.rotate(image, self.angle - 180)
            return pygame.transform.flip(image, True, True)
        elif 270 <= self.players.angle <= 360:  # turning right on the ceiling
            image = pygame.transform.rotate(image, 180 - self.angle)
            return pygame.transform.flip(image, True, False)


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
            # Update background position based on player movement
            bg_x = self.width // 2 - self.players.player_rect.centerx
            bg_y = self.height // 2 - self.players.player_rect.centery

            # Zoom in on the player
            zoom_level = 1.5  # Change this value to adjust zoom level
            zoomed_player_image = pygame.transform.scale(self.players.player_image, (int(self.players.player_rect.width * zoom_level),
                                                                       int(self.players.player_rect.height * zoom_level)))
            zoomed_player_rect = zoomed_player_image.get_rect(center=(self.width // 2, self.height // 2))

            self.ChangePlayerPictureWithAngle(zoomed_player_image)

            zoomed_player_image = self.ChangePlayerPictureWithAngle(zoomed_player_image)

            # Draw everything
            self.screen.blit(self.background_image, (bg_x, bg_y))
            self.screen.blit(zoomed_player_image, zoomed_player_rect.topleft)

            # Update the display
            pygame.display.update()

            # Cap the frame rate
            self.clock.tick(self.REFRESH_RATE)


class Player(Game):
    
    FLOOR_HEIGHT = 850
    CEILING_HEIGHT = 100
    RIGHT_WALL = 2150
    LEFT_WALL = 300
    DISTANCE_FROM__WALL = 110

    GRAVITY_FORCE = 10

    def __init__(self, speed):
        super().__init__(1500, 800)
    
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        self.motion = [0, 0]
        self.speed = speed
        self.inJump = False
        self.angle = 0
        
        self.SetPlayers()
    
    def SetPlayers(self):
        self.player_image = pygame.transform.scale(pygame.image.load("player.png"), (70,35))
        self.player_image.set_colorkey((0,0,0))
        self.player_image.convert_alpha()
        self.player_rect = self.player_image.get_rect()
        self.player_rect.x = 500
        self.player_rect.y = 850

    
    def __Function(self, x):
        return (x**2) / 80

    def __DerivativeFunction(self, x):
        return 2*x / 80

    # the sides of the map require the player to change its angle
    def __GetPlayerAngleOnSides(self, xDiff):
        # we will get the angle of the player with incline of the function
        incline = self.__DerivativeFunction(xDiff)
        angle = math.degrees(math.atan(incline)) * 1.168  # shift tan of the incline
        angle = int(angle)
        if angle < 0:
            angle = abs(angle)
            angle += 180 + (180 - angle)

        return angle


    def ChangePlayerHeightOnSides(self):
        
        # we will check on which side the player is and the build the right equation according to the side
        xDiffRight = self.RIGHT_WALL - self.player_rect.x
        xDiffLeft = self.player_rect.x - self.LEFT_WALL
        if xDiffRight < self.DISTANCE_FROM__WALL:  # right wall
            xDiff = abs(xDiffRight - self.DISTANCE_FROM__WALL)
            if self.player_rect.y > self.FLOOR_HEIGHT - self.__Function(xDiff): # right bottom ramp
                self.player_rect.y = self.FLOOR_HEIGHT - self.__Function(xDiff)
                self.angle = self.__GetPlayerAngleOnSides(xDiff)
            elif self.player_rect.y < self.CEILING_HEIGHT + self.__Function(xDiff):  # right upper ramp
                self.player_rect.y = self.CEILING_HEIGHT + self.__Function(xDiff)
                self.angle = 360 - self.__GetPlayerAngleOnSides(xDiff)
        elif xDiffLeft < self.DISTANCE_FROM__WALL:  # left wall
            xDiff = abs(xDiffLeft - self.DISTANCE_FROM__WALL)
            if self.player_rect.y > self.FLOOR_HEIGHT - self.__Function(xDiff):  # left bottom  ramp
                self.player_rect.y = self.FLOOR_HEIGHT - self.__Function(xDiff)
                self.angle = 180 - self.__GetPlayerAngleOnSides(xDiff)
            elif self.player_rect.y < self.CEILING_HEIGHT + self.__Function(xDiff):  # left upper ramp
                self.player_rect.y = self.CEILING_HEIGHT + self.__Function(xDiff)
                self.angle = 180 + self.__GetPlayerAngleOnSides(xDiff)

    
    def PlayerJump(self):
        # we will use one physics equation
        # y = y0 + v0*t - 5*t**2
        # x = x0 + v0(t1 - t0)
        
        # we will use F=ma to calculate the v0
        

        if not self.inJump:  # if first time in this function (right after the player pressed jump)
            self.inJump = True
            timeDiff = time.time() - self.time

            if timeDiff == 0:
                timeDiff = 0.1
            self.Fy = (-(self.player_rect.y - self.yBefore) / timeDiff)*1.3
            self.Fx = ((self.player_rect.x - self.xBefore) / timeDiff)*1.3

            if self.angle != 0:
                vectorSpeed = math.sqrt(self.Fy**2 + self.Fx**2)
                angle = self.angle
                if 360 >= angle >= 180:
                    angle = -(angle % 180)
                self.Fy = vectorSpeed * math.sin(math.radians(self.angle))
                self.Fx = vectorSpeed * math.cos(math.radians(self.angle))

            if self.Fy == 0:
                self.Fy = 100
        
        timeDiff = (time.time() - self.time) * self.speed + 0.01 # if timeDiff is zero it won't count it so we will add a little bit
        self.player_rect.y = self.yBefore - self.Fy * timeDiff + (self.GRAVITY_FORCE*2) * timeDiff ** 2
        self.player_rect.x = self.xBefore + self.Fx * timeDiff
        
        self.CheckBoundariesDurringJump()  # check boundaries
        
    
    def CheckBoundariesDurringJump(self):
        if self.player_rect.y <= self.CEILING_HEIGHT:
            self.player_rect.y = self.CEILING_HEIGHT
            self.inJump = False
        if self.player_rect.y >= self.FLOOR_HEIGHT:
            self.player_rect.y = self.FLOOR_HEIGHT
            self.inJump = False
        if self.player_rect.x <= self.LEFT_WALL:
            self.player_rect.x = self.LEFT_WALL
            self.inJump = False
        if self.player_rect.x >= self.RIGHT_WALL:
            self.player_rect.x = self.RIGHT_WALL
            self.inJump = False
    
    def ControllerMovement(self, event):
        if event.type == JOYAXISMOTION:  # axis motion
            if event.axis < 2:
                self.motion[event.axis] = event.value
        if event.type == JOYDEVICEADDED:  # if the device was diconnected
            self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
            for joystick in self.joysticks:
                print(joystick.get_name())
        if event.type == JOYDEVICEREMOVED:
            self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        if event.type == JOYBUTTONDOWN:  # if button was pressed
            if event.button == 1:  # if O button was pressed
                self.speed *= 2
            elif event.button == 0 and not self.inJump:  #if player pressed jump and already in jump
                self.time = time.time()
                self.PlayerJump()
                
        if event.type == JOYBUTTONUP:  # if button was released
            if event.button == 1:  # if O button was released
                self.speed /= 2
        
        if event.type == pygame.KEYUP:  # the only way to check if the keyboard was released is in event type
            if event.key == pygame.K_RCTRL:
                self.speed /= 2
                
        
        if abs(self.motion[0]) < 0.1:
            self.motion[0] = 0
        if abs(self.motion[1]) < 0.1:
            self.motion[1] = 0
    
    def KeyboardMotion(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RCTRL] and self.speed < 20:
            self.speed *= 2
        if keys[pygame.K_LEFT] and self.player_rect.x > self.LEFT_WALL:
            self.player_rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.player_rect.x < self.RIGHT_WALL:
            self.player_rect.x += self.speed
        if keys[pygame.K_UP] and self.player_rect.y > self.CEILING_HEIGHT:
            self.player_rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.player_rect.y < self.FLOOR_HEIGHT:
            self.player_rect.y += self.speed
        if keys[pygame.K_SPACE] and not self.inJump:
            self.time = time.time()
            self.PlayerJump()
    
    def PlayerMotion(self):
        if not self.inJump:  # if not in jump motion we need to get the x and y
                             # in case we will jump we need to know the difference between the last place and current place so we will know the speed
            self.xBefore = self.player_rect.x
            self.yBefore = self.player_rect.y

        self.KeyboardMotion()
        
        if self.inJump:
            self.PlayerJump()
        
        else:
            self.player_rect.x += self.motion[0] * self.speed
            if self.player_rect.x > self.RIGHT_WALL or self.player_rect.x < self.LEFT_WALL:
                self.player_rect.x -= self.motion[0] * self.speed
            self.player_rect.y += self.motion[1] * 2
            if self.player_rect.y > self.FLOOR_HEIGHT or self.player_rect.y < self.CEILING_HEIGHT:
                self.player_rect.y -= self.motion[1] * 2
        
        """if self.xBefore < self.player_rect.x and 270 > self.angle > 90:  # if turned right from left
            self.angle -= 180
        elif self.xBefore > self.player_rect.x and (self.angle < 90 or self.angle > 270):  # if turned left from right
            self.angle += 180"""


        self.ChangePlayerHeightOnSides()
        print(self.angle)
            
        


player = Player(7)
player.GetPlayers(player)
player.MainLoop()

pygame.quit()
sys.exit()
