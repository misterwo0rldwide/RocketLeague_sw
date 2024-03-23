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

            # Draw everything
            self.screen.blit(self.background_image, (bg_x, bg_y))
            self.screen.blit(zoomed_player_image, zoomed_player_rect.topleft)

            # Update the display
            pygame.display.update()

            # Cap the frame rate
            self.clock.tick(self.REFRESH_RATE)


class Player(Game):
    
    GRAVITY_FORCE = 9.81

    def __init__(self, speed):
        super().__init__(1500, 800)
    
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        self.motion = [0, 0]
        self.speed = speed
        self.inJump = False
        
        self.SetPlayers()
    
    def SetPlayers(self):
        self.player_image = pygame.transform.scale(pygame.image.load("player.png"), (70,35))
        self.player_image.set_colorkey((0,0,0))
        self.player_image.convert_alpha()
        self.player_rect = self.player_image.get_rect()
        self.player_rect.x = 500
        self.player_rect.y = 850
    
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

            if self.Fy == 0 and self.Fx == 0:
                self.inJump = False
                return

        timeDiff = (time.time() - self.time) * self.speed
        if self.Fy != 0:
            self.player_rect.y = self.yBefore - self.Fy * timeDiff + (self.GRAVITY_FORCE / 2) * timeDiff ** 2
        if self.Fx != 0:
            self.player_rect.x = self.xBefore + self.Fx * timeDiff

        
    
    
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
            elif event.button == 0:
                self.time = time.time()
                self.PlayerJump()
                
        if event.type == JOYBUTTONUP:  # if button was released
            if event.button == 1:  # if O button was released
                self.speed /= 2
        
        if event.type == pygame.KEYUP:  # the only way to check if the keyboard was released is in event type
            if event.key == pygame.K_SPACE:
                self.speed /= 2
                
        
        if abs(self.motion[0]) < 0.1:
            self.motion[0] = 0
        if abs(self.motion[1]) < 0.1:
            self.motion[1] = 0
    
    def KeyboardMotion(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.speed < 20:
            self.speed *= 2
        if keys[pygame.K_LEFT] and self.player_rect.x > 300:
            self.player_rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.player_rect.x < 2100:
            self.player_rect.x += self.speed
        if keys[pygame.K_UP] and self.player_rect.y > 100:
            self.player_rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.player_rect.y < 850:
            self.player_rect.y += self.speed
    
    def PlayerMotion(self):
        if not self.inJump:
            self.xBefore = self.player_rect.x
            self.yBefore = self.player_rect.y

        self.KeyboardMotion()
        
        if self.player_rect.y >= 850 and self.inJump:
            self.inJump = False
            self.player_rect.y = 850
        elif self.inJump:
            self.PlayerJump()
        
        if not self.inJump:
            self.player_rect.x += self.motion[0] * self.speed
            if self.player_rect.x > 2100 or self.player_rect.x < 300:
                self.player_rect.x -= self.motion[0] * self.speed
            self.player_rect.y += self.motion[1] * 2
            if self.player_rect.y > 850 or self.player_rect.y < 100:
                self.player_rect.y -= self.motion[1] * 2
            
        


player = Player(7)
player.GetPlayers(player)
player.MainLoop()

pygame.quit()
sys.exit()
