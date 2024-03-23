import pygame
import sys
from pygame.locals import *



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
    def __init__(self, speed):
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        self.motion = [0, 0]
        self.speed = speed
        
        self.SetPlayers()
    
    def SetPlayers(self):
        self.player_image = pygame.transform.scale(pygame.image.load("player.png"), (90,35))
        self.player_image.set_colorkey((0,0,0))
        self.player_image.convert_alpha()
        self.player_rect = self.player_image.get_rect()
    
    def ControllerMovement(self, event):
        if event.type == JOYBUTTONDOWN:  # jump
            pass
            #if event.button == 0:
            #    my_square_color = (my_square_color + 1) % len(colors)
        if event.type == JOYAXISMOTION:
            if event.axis < 2:
                self.motion[event.axis] = event.value
        if event.type == JOYDEVICEADDED:
            self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
            for joystick in self.joysticks:
                print(joystick.get_name())
        if event.type == JOYDEVICEREMOVED:
            self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
                
        
        if abs(self.motion[0]) < 0.1:
            self.motion[0] = 0
        if abs(self.motion[1]) < 0.1:
            self.motion[1] = 0
    
    def KeyboardMotion(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player_rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.player_rect.x += self.speed
        if keys[pygame.K_UP]:
            self.player_rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.player_rect.y += self.speed
    
    def PlayerMotion(self):
        self.KeyboardMotion()
        
        self.player_rect.x += self.motion[0] * 5
        self.player_rect.y += self.motion[1] * 2


game = Game(1500, 800)
player = Player(7)
game.GetPlayers(player)
game.MainLoop()

pygame.quit()
sys.exit()
