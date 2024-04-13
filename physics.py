import math


# heights and x values of walls
FLOOR_HEIGHT = 850
CEILING_HEIGHT = 100
RIGHT_WALL = 2150
LEFT_WALL = 300
DISTANCE_FROM__WALL = 110  # distance from wall of ramp

REFRESH_RATE_TIME = 1/60  # we need the refresh rate time to calculate time differences

FRICTION_FORCE_FK = 0.4

# a class for rectangle objects
class Object:
    def __init__(self, width: int, height: int, weight: int,statringPlace:tuple):
        self.width = width
        self.height = height
        self.weight = weight

        self.xPlace, self.yPlace = statringPlace

        self.yVector = self.GRAVITY_FORCE_ACCELARATION = 10 * self.weight
        self.xVector = 0

        self.xSpeed, self.ySpeed = 0, 0

        self.angle = 0
        self.ObjectOnGround = True

        self.ACCELARATION_CAR = 10 * self.weight

        # because we cant draw the object to all of his sides due to many of his angles we will need to rotate it
        # from time to time, so for the main code we will have this variable which indicate if we need to flip the object
        self.flipObjectDraw = False

        self.spinning = False
        self.startingAngle = 0

        self.boostAmount = 100

    def __Function(self, x):
        return (x**2) / 100
    
    def __FindXValueForYValue(self, y):
        return math.sqrt(y * 100)

    def __DerivativeFunction(self, x):
        return 2*x / 100

    # the sides of the map require the player to change its angle
    def __GetObjectAngleOnSides(self, xDiff):
        # we will get the angle of the player with incline of the function
        incline = self.__DerivativeFunction(xDiff)
        angle = math.degrees(math.atan(incline)) * 1.168  # shift tan of the incline
        return int(angle)
    
    # when the player is in the air he needs to rotate
    def __GetObjectAngleInAir(self, accelrationX, accelrationY):
        #we will calculate the angle of the car with the acceleration which the player is doing
        # basically we will do pythagoras to get the totla vector
        # then we will get the angle between the totla vector and x axis
        self.angle = math.degrees(math.acos(accelrationX / math.sqrt(accelrationX ** 2 + accelrationY ** 2))) * -(accelrationY / abs(accelrationY))

        # now if the player is going backwards we will flip his drawing
        if self.xSpeed < 0:
            self.flipObjectDraw = True
            self.angle = self.angle * -1 + 180
        else:
            self.flipObjectDraw = False


    def __CalculateAnglesWallRamps(self, rightWall:bool ,xDiff:int, onFloorRamp:bool):
        normalWallAngle = self.__GetObjectAngleOnSides(xDiff)
        if rightWall:  # if on right wall ramps
            if self.ySpeed <= 0 and onFloorRamp:
                self.angle = normalWallAngle
                self.flipObjectDraw = False
            elif self.ySpeed > 0 and onFloorRamp:
                self.angle = -normalWallAngle
                self.flipObjectDraw = True
            elif self.ySpeed < 0:  # on ceiling ramp
                self.angle = 180 - normalWallAngle
                self.flipObjectDraw = False
            else:
                self.angle = 180 + normalWallAngle
                self.flipObjectDraw = True
        else:         
            if self.ySpeed <= 0 and onFloorRamp:
                self.angle = normalWallAngle
                self.flipObjectDraw = True
            elif self.ySpeed > 0 and onFloorRamp:
                self.angle = 360 - normalWallAngle
                self.flipObjectDraw = False
            elif self.ySpeed < 0:  # on ceiling ramp
                self.angle = 180 - normalWallAngle
                self.flipObjectDraw = True
            else:
                self.angle = 180 + normalWallAngle
                self.flipObjectDraw = False

    #the object needs to adjust its angle
    def __ObjectOnRamps(self):

        self.__ObjectBoundaries()  # firstly we will check the state of the object


        #check if right wall
        if RIGHT_WALL - self.xPlace < DISTANCE_FROM__WALL:  # right wall
            xDiffRightWall = DISTANCE_FROM__WALL - (RIGHT_WALL - self.xPlace)
            onFloorRamp = FLOOR_HEIGHT - self.yPlace <= self.__Function(xDiffRightWall) and (self.xPlace != RIGHT_WALL or self.ySpeed > 0)
            onCeilingRamp = self.yPlace - CEILING_HEIGHT <= self.__Function(xDiffRightWall) and (self.xPlace != RIGHT_WALL or self.ySpeed < 0)

            if self.xSpeed > 0 and (onCeilingRamp or onFloorRamp):  # if going up the ramp
                self.yPlace = FLOOR_HEIGHT - self.__Function(xDiffRightWall) if onFloorRamp\
                                    else CEILING_HEIGHT + self.__Function(xDiffRightWall) if onCeilingRamp\
                                    else self.yPlace
            elif (onCeilingRamp or onFloorRamp):  # if going down the ramp
                yDiff = FLOOR_HEIGHT - self.yPlace if onFloorRamp else self.yPlace - CEILING_HEIGHT if onCeilingRamp else 0
                self.xPlace = RIGHT_WALL - DISTANCE_FROM__WALL + self.__FindXValueForYValue(yDiff)
            
            if onFloorRamp or onCeilingRamp:
                self.ObjectOnGround = True
                self.__CalculateAnglesWallRamps(True ,xDiffRightWall, onFloorRamp)
        
        elif self.xPlace - LEFT_WALL < DISTANCE_FROM__WALL:  # left wall
            xDiffLeftWall = DISTANCE_FROM__WALL - (self.xPlace - LEFT_WALL)
            onFloorRamp = FLOOR_HEIGHT - self.yPlace <= self.__Function(xDiffLeftWall) and (self.xPlace != LEFT_WALL or self.ySpeed > 0)
            onCeilingRamp = self.yPlace - CEILING_HEIGHT < self.__Function(xDiffLeftWall) and (self.xPlace != LEFT_WALL or self.ySpeed < 0)
            
            if self.xSpeed < 0 and (onCeilingRamp or onFloorRamp):  # if going up the ramp
                self.yPlace = FLOOR_HEIGHT - self.__Function(xDiffLeftWall) if onFloorRamp\
                                    else CEILING_HEIGHT + self.__Function(xDiffLeftWall) if onCeilingRamp\
                                    else self.yPlace
            elif (onCeilingRamp or onFloorRamp):  # if going down the ramp
                yDiff = FLOOR_HEIGHT - self.yPlace if onFloorRamp else self.yPlace - CEILING_HEIGHT if onCeilingRamp else 0
                self.xPlace = LEFT_WALL + DISTANCE_FROM__WALL - self.__FindXValueForYValue(yDiff)
            
            if onFloorRamp or onCeilingRamp:
                self.ObjectOnGround = True
                self.__CalculateAnglesWallRamps(False ,xDiffLeftWall, onFloorRamp)

    # prevent the player from moving beyond walls
    def __ObjectBoundaries(self):
        self.ObjectOnGround = False  # we will assume the object is not on ground

        if self.xPlace <= LEFT_WALL:
            self.xPlace = LEFT_WALL
            self.xSpeed = 0
            self.ObjectOnGround = True
            self.spinning = False
            if self.ySpeed <= 0:
                self.angle = 90
                self.flipObjectDraw = True
            else:
                self.angle = 270
                self.flipObjectDraw = False
        elif self.xPlace >= RIGHT_WALL:
            self.xPlace = RIGHT_WALL
            self.xSpeed = 0
            self.ObjectOnGround = True
            self.spinning = False
            if self.ySpeed <= 0:
                self.angle = 90
                self.flipObjectDraw = False
            else:
                self.angle = 270
                self.flipObjectDraw = True
        if self.yPlace >= FLOOR_HEIGHT:
            self.yPlace = FLOOR_HEIGHT
            self.ySpeed = 0
            self.angle = 0
            self.ObjectOnGround = True
            self.flipObjectDraw = False if self.xSpeed >= 0 else True
            self.spinning = False
        elif self.yPlace <= CEILING_HEIGHT:
            self.yPlace = CEILING_HEIGHT
            self.ySpeed = 0
            self.ObjectOnGround = True
            self.angle = 180
            self.flipObjectDraw = True if self.xSpeed >= 0 else False
            self.spinning = False



    def __CalculateFrictionOfObject(self):
        # firstly for the object to have firction we need it to be on ground
        # we also need to check if the object is moving
        if self.ObjectOnGround and self.xSpeed != 0:
            Fk = self.yVector * FRICTION_FORCE_FK * -(self.xSpeed // abs(self.xSpeed))
                
            self.xVector += Fk  # multiply by which direction the car is facing

    def __CalculateMaxSpeed(self, IsBoosting):

        MAX_SPEED_X = 3 * self.weight
        MAX_SPEED_Y = 2.5 * self.weight

        if not self.ObjectOnGround or IsBoosting:
            MAX_SPEED_X *= 1.4
            MAX_SPEED_Y *= 1.2

        self.xSpeed = MAX_SPEED_X if self.xSpeed > MAX_SPEED_X else -MAX_SPEED_X if self.xSpeed < -MAX_SPEED_X else self.xSpeed
        self.ySpeed = MAX_SPEED_Y * 2 if self.ySpeed > MAX_SPEED_Y * 2 else -MAX_SPEED_Y * 2 if self.ySpeed < -MAX_SPEED_Y * 2 else self.ySpeed

    # when jumping the player needs to sum the vectors in the right angle
    def __CalculateVectorsJump(self, PlayerTouchedControls):
        yPower = self.GRAVITY_FORCE_ACCELARATION * -20  # when jumping the force on the player needs to be big
        xPower = self.xVector

        mul = 1

        angle = self.angle
        if self.ObjectOnGround or not PlayerTouchedControls:
            angle = angle + 90 if not self.flipObjectDraw else 90 - angle
        else:
            mul = -1 if self.flipObjectDraw else mul
            self.spinning = True
            self.startingAngle = angle
        
        totalVector = math.sqrt(xPower ** 2 + yPower ** 2)
        self.xVector = totalVector * math.cos(math.radians(angle)) * mul
        self.yVector = totalVector * -math.sin(math.radians(angle))

    # when the player is in the air he can be either moving itself the angle or in spinning mid air
    def __AdjustAngle(self, PlayerTouchedControls, acelerationX, accelerationY):
        if not self.ObjectOnGround and PlayerTouchedControls and not self.spinning:
            self.__GetObjectAngleInAir(acelerationX, accelerationY)
        elif self.spinning:
            self.angle = (self.angle - 15) % 360  # jumps of 15 angles
            if abs(self.startingAngle - self.angle) < 10:
                self.spinning = False
                self.angle = self.startingAngle


    def __PlayerBoosting(self):
        if self.boostAmount > 0:
            # firstly we will calculate the totalVector of the boost

            totalVector = math.sqrt(self.xVector ** 2 + self.yVector ** 2) * 0.8

            angle = self.angle
            if self.flipObjectDraw:
                angle = 180 - angle

            # now we will add the right proportion to each axis
            self.xVector += totalVector * math.cos(math.radians(angle)) * self.weight / 45
            self.yVector -= totalVector * math.sin(math.radians(angle)) * self.weight / 60

            self.boostAmount -= 1


    #this function will calculate where the players need to be according to the vectors
    def CalculateObjectPlace(self, accelerationX: int, accelerationY: int ,IsJumping: bool, PlayerTouchedControls: bool, IsBoosting: bool):

        saveAccelerationX, saveAccelerationY = accelerationX, accelerationY
        self.xVector = accelerationX * self.ACCELARATION_CAR

        if IsJumping:
            self.__CalculateVectorsJump(PlayerTouchedControls)
            self.ObjectOnGround = False
        else:
            if not self.ObjectOnGround:
                accelerationY = 1
                accelerationX = 0
            elif not (self.xPlace == RIGHT_WALL or self.xPlace == LEFT_WALL):  # not on walls
                accelerationY = 1
            
            self.xVector = accelerationX * self.ACCELARATION_CAR
            self.yVector = accelerationY * self.GRAVITY_FORCE_ACCELARATION

        if IsBoosting:
            self.__PlayerBoosting()
        else:
            self.boostAmount = self.boostAmount + 1 if self.ObjectOnGround and self.boostAmount < 100 else self.boostAmount

        # we will use the physics function - currentPlace = placeBefore + speedBefore*timeDiff + (acceleration / 2) * timeDiff ** 2
        # we will use this function for both of the axis, one for the x axis and one for the y axis

        # before calculating we need to also calculate the Friction on the object
        self.__CalculateFrictionOfObject()

        # firstly we will need the speed which we will calculate 
        # we will use currentSpeed = prevSpeed + acceleration * timeDiff
        self.xSpeed = self.xSpeed + self.xVector * REFRESH_RATE_TIME
        self.ySpeed = self.ySpeed + self.yVector * REFRESH_RATE_TIME


        self.__CalculateMaxSpeed(IsBoosting)

        # if xSpeed is close to zero we will set it to be zero
        self.xSpeed = 0 if abs(self.xSpeed) - 5 <= 0 else self.xSpeed

        # now lets put it into the current place

        xDiff = self.xSpeed*REFRESH_RATE_TIME + (self.xVector / 2) * REFRESH_RATE_TIME ** 2
        yDiff = self.ySpeed*REFRESH_RATE_TIME + (self.yVector / 2) * REFRESH_RATE_TIME ** 2

        # before moving we will save the current place so that after moving we will have the correct speed
        yplace = self.yPlace
        xplace = self.xPlace

        self.xPlace = self.xPlace + xDiff
        self.yPlace = self.yPlace + yDiff

        self.__ObjectOnRamps()

        # calculating the real speed of the object
        self.ySpeed = (self.yPlace - yplace) / REFRESH_RATE_TIME
        self.xSpeed = (self.xPlace - xplace) / REFRESH_RATE_TIME

        self.__AdjustAngle(PlayerTouchedControls, saveAccelerationX, saveAccelerationY)




class Ball(Object):
    pass