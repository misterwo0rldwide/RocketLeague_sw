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
        angle = self.players.angle
        turningRight = self.players.PlayerGoingRight
        x = self.players.player_rect.x
        y = self.players.player_rect.y
        newAngle = 0
        flipY = False
        flipX = False
        if not turningRight:  # if the player going left
            # the angle needs to be changed so pygame will draw it correctly
            flipX = True
            if 270 >= angle > 180:  #רביע שלישי
                self.players.PlayerUpsideDown = True
                if angle == 270:
                    flipX = False
                    newAngle = 270
                elif x + self.players.DISTANCE_FROM__WALL > self.players.RIGHT_WALL:  # right bottom wall
                    self.players.PlayerUpsideDown = False
                    flipY = False
                    newAngle = -(angle % 90)
                else:
                    flipY = True
                    newAngle = angle % 90
            else: #רביע שני
                self.players.PlayerUpsideDown = False
                if self.players.player_rect.y == self.players.CEILING_HEIGHT or self.players.jumpedFromCeiling:  # if on ceiling or jumped from ceiling
                    flipY = True
                elif x + self.players.DISTANCE_FROM__WALL > self.players.RIGHT_WALL:  # right upper wall
                    self.players.PlayerUpsideDown = True
                    flipX, flipY = False, False
                    newAngle = angle
                else:  
                    newAngle = 180-angle
        else: # if the player going right
            if 360 >= angle >= 270: # רביע רביעי
                self.players.PlayerUpsideDown = True
                if x - self.players.DISTANCE_FROM__WALL < self.players.LEFT_WALL:  # if on left bottom wall
                    flipY = False
                    newAngle = - (360 - angle)
                else:
                    flipY = True
                    if angle == 360: 
                        newAngle = 0
                    else:
                        newAngle = 90-angle%90
            else:# רביע ראשון
                if x - self.players.DISTANCE_FROM__WALL < self.players.LEFT_WALL:  # if on the left upper wall
                    flipY = True
                    self.players.PlayerUpsideDown = True
                    newAngle = -angle
                else:
                    self.players.PlayerUpsideDown = False
                    newAngle = angle
        
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

    FLOOR_HEIGHT = 850
    CEILING_HEIGHT = 100
    RIGHT_WALL = 2150
    LEFT_WALL = 300
    DISTANCE_FROM__WALL = 110

    GRAVITY_FORCE = 10

    def __init__(self, speed):
    
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        self.motion = [0, 0]
        self.speed = speed
        self.inJump = False
        self.angle = 0

        self.PlayerGoingRight = True
        self.onWall = False
        self.PlayerUpsideDown = False
        
        self.SetPlayers()
    
    def SetPlayers(self):
        self.player_image = pygame.transform.scale(pygame.image.load("player.png"), (50,25))
        self.player_image.set_colorkey((0,0,0))
        self.player_image.convert_alpha()
        self.player_rect = self.player_image.get_rect()
        self.player_rect.x = 500
        self.player_rect.y = 850

    
    def __Function(self, x):
        return (x**2) / 100

    def __DerivativeFunction(self, x):
        return 2*x / 100

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

    def MatchAngleOfplayerToWall(self):  # checks if the player is on the wall, if so correct its angle
        if self.CheckIfOnWall():
            if 180 >= self.angle >= 0:
                if self.yBefore < self.player_rect.y:  # if player going down
                    self.angle = 270
                else:
                    self.angle = 90
            else:
                if self.yBefore > self.player_rect.y:  # if player going up
                    self.angle = 90
                else:
                    self.angle = 270
        else:
            return False


    def ChangePlayerHeightOnRamps(self):
        
        # we will check on which side the player is and the build the right equation according to the side
        xDiffRight = self.RIGHT_WALL - self.player_rect.x
        xDiffLeft = self.player_rect.x - self.LEFT_WALL
        if xDiffRight < self.DISTANCE_FROM__WALL:  # right wall
            xDiff = abs(xDiffRight - self.DISTANCE_FROM__WALL)
            if self.player_rect.y > self.FLOOR_HEIGHT - self.__Function(xDiff): # right bottom ramp
                if 270 >= self.angle >= 180:   # going down the ramp
                    self.PlayerGoingRight = False
                    xDiff -= 2 + self.speed * 0.5
                    self.player_rect.x -= 2 + self.speed * 0.5
                self.player_rect.y = self.FLOOR_HEIGHT - self.__Function(xDiff)
                
                self.angle = self.__GetPlayerAngleOnSides(xDiff)
                if not self.PlayerGoingRight:
                    self.angle += 180
            elif self.player_rect.y < self.CEILING_HEIGHT + self.__Function(xDiff):  # right upper ramp
                if 180 >= self.angle >= 90:  # going up the ramp
                    self.PlayerGoingRight = False
                    xDiff -= 2 + self.speed * 0.5
                    self.player_rect.x -= 2 + self.speed * 0.5

                self.player_rect.y = self.CEILING_HEIGHT + self.__Function(xDiff)
                self.angle = 360 - self.__GetPlayerAngleOnSides(xDiff)
                if not self.PlayerGoingRight:
                    self.angle -= 180
        elif xDiffLeft < self.DISTANCE_FROM__WALL:  # left wall
            xDiff = abs(xDiffLeft - self.DISTANCE_FROM__WALL)
            if self.player_rect.y > self.FLOOR_HEIGHT - self.__Function(xDiff):  # left bottom  ramp
                if 360 > self.angle >= 270:  # going down the ramp
                    self.PlayerGoingRight = True
                    xDiff -= 2 + self.speed * 0.5
                    self.player_rect.y += 2 + self.speed * 0.5
                    self.player_rect.x += 2 + self.speed * 0.5


                self.player_rect.y = self.FLOOR_HEIGHT - self.__Function(xDiff)
                self.angle = 180 - self.__GetPlayerAngleOnSides(xDiff)
                if self.PlayerGoingRight:
                    self.angle = 270 + self.angle % 90
            elif self.player_rect.y < self.CEILING_HEIGHT + self.__Function(xDiff):  # left upper ramp
                if 90 >= self.angle > 0:  # if going up the ramp
                    self.PlayerGoingRight = True
                    xDiff -= 2 + self.speed * 0.5
                    self.player_rect.y -= 2 + self.speed * 0.5
                    self.player_rect.x += 2 + self.speed * 0.5


                self.player_rect.y = self.CEILING_HEIGHT + self.__Function(xDiff)
                self.angle = 180 + self.__GetPlayerAngleOnSides(xDiff)
                if self.PlayerGoingRight:
                    self.angle = self.angle % 90
 
        self.CheckBoundariesDurringJump()

    
    def PlayerJump(self):
        # we will use one physics equation
        # y = y0 + v0*t - 5*t**2
        # x = x0 + v0(t1 - t0)
        
        # we will use F=ma to calculate the v0
        

        if not self.inJump:  # if first time in this function (right after the player pressed jump)
            if self.player_rect.y == self.CEILING_HEIGHT:
                self.jumpedFromCeiling = True
            self.inJump = True
            timeDiff = time.time() - self.time

            if timeDiff == 0:
                timeDiff = 0.1
            yPower = (-(self.player_rect.y - self.yBefore) / timeDiff)
            xPower = ((self.player_rect.x - self.xBefore) / timeDiff)
            
            vectorSpeed = math.sqrt(yPower**2 + xPower**2) + 50
            angle = self.angle

            if angle == 90:  # those angles can show twice - or right or left
                if not self.PlayerGoingRight:
                    angle -= 90
                else:
                    angle += 90
                    xPower = -30
            elif angle == 270:
                if not self.PlayerGoingRight:
                    angle += 90
                else:
                    angle -= 90
                    xPower = -30
            elif 180 >= angle > 90 or 360 >= angle > 270:
                if (self.angle == 180 and self.player_rect.y == self.CEILING_HEIGHT) or (self.PlayerUpsideDown and self.player_rect.x - self.DISTANCE_FROM__WALL <= self.LEFT_WALL) or (not self.PlayerGoingRight and self.player_rect.x + self.DISTANCE_FROM__WALL >= self.RIGHT_WALL):  # because the player is upside down and the angle is intended to be upright
                    angle += 90
                else:
                    angle -= 90
            else:
                if (self.PlayerUpsideDown and self.PlayerGoingRight) or (not self.PlayerUpsideDown and not self.PlayerGoingRight):
                    angle -= 90
                else:
                    angle += 90

            self.Fy = vectorSpeed * math.sin(math.radians(angle))
            self.Fx = vectorSpeed * math.cos(math.radians(angle)) + xPower
        
        timeDiff = (time.time() - self.time) * self.speed + 0.01 # if timeDiff is zero it won't count it so we will add a little bit
        self.player_rect.y = self.yBefore - self.Fy * timeDiff + (self.GRAVITY_FORCE*2) * timeDiff ** 2
        self.player_rect.x = self.xBefore + self.Fx * timeDiff
        
        self.CheckBoundariesDurringJump()  # check boundaries
        
    
    def CheckBoundariesDurringJump(self):
        if self.player_rect.y <= self.CEILING_HEIGHT:
            self.player_rect.y = self.CEILING_HEIGHT
            self.inJump = False
            self.jumpedFromCeiling = False
        if self.player_rect.y >= self.FLOOR_HEIGHT:
            self.player_rect.y = self.FLOOR_HEIGHT
            self.inJump = False
            self.jumpedFromCeiling = False
        if self.player_rect.x <= self.LEFT_WALL:
            self.player_rect.x = self.LEFT_WALL
            self.inJump = False
            self.jumpedFromCeiling = False
        if self.player_rect.x >= self.RIGHT_WALL:
            self.player_rect.x = self.RIGHT_WALL
            self.inJump = False
            self.jumpedFromCeiling = False
    
    def CheckIfOnWall(self):  # checks if the player is on one if the walls
        if self.player_rect.x - 5 <= self.LEFT_WALL or self.player_rect.x + 5 >= self.RIGHT_WALL:
            self.onWall = True
        else:
            self.onWall = False
        return self.onWall
    
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
    
    def ControllerMovmentHandling(self):
        self.player_rect.x += self.motion[0] * self.speed
        if self.player_rect.x > self.RIGHT_WALL or self.player_rect.x < self.LEFT_WALL:
            self.player_rect.x -= self.motion[0] * self.speed
        self.player_rect.y += self.motion[1] * 2
        if self.player_rect.y > self.FLOOR_HEIGHT or self.player_rect.y < self.CEILING_HEIGHT:
            self.player_rect.y -= self.motion[1] * 2
    
    def ChangAngleInTurn(self):
        if 360 >= self.angle >= 270:
            self.angle = 180 + 360 - self.angle
        elif 270 > self.angle > 180:
            self.angle = 360 - self.angle % 90
        else:
            self.angle = 180 - self.angle

    def CorrectAngleOnGround(self):

        if self.player_rect.y - 15 <= self.CEILING_HEIGHT:
            if self.PlayerGoingRight:
                self.angle = 360
            else:
                self.angle = 180
        elif self.player_rect.y + 5 >= self.FLOOR_HEIGHT:
            if self.PlayerGoingRight:
                self.angle = 0
            else:
                self.angle = 180

    def PlayerMotion(self):
        if not self.inJump:  # if not in jump motion we need to get the x and y
                             # in case we will jump we need to know the difference between the last place and current place so we will know the speed
            self.xBefore = self.player_rect.x
            self.yBefore = self.player_rect.y

        
        if self.inJump:
            self.PlayerJump()
        else:
            self.CorrectAngleOnGround()
            self.ControllerMovmentHandling()
            self.KeyboardMotion()
        
        self.ChangePlayerHeightOnRamps()
        self.MatchAngleOfplayerToWall()
            

        if self.xBefore < self.player_rect.x and not self.PlayerGoingRight and not self.inJump:  # if turned right from left
            self.PlayerGoingRight = True

            if not self.onWall:
                self.ChangAngleInTurn()
            else:
                self.onWall = False

        elif self.xBefore > self.player_rect.x and self.PlayerGoingRight and not self.inJump:  # if turned left from right
            self.PlayerGoingRight = False
            
            if not self.onWall:
                self.ChangAngleInTurn()
            else:
                self.onWall = False
            
        print(self.angle)
            
        


player = Player(7)
game = Game(player)
game.MainLoop()

pygame.quit()
sys.exit()
