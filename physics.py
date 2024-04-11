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

        self.MAX_SPEED_X = 3 * self.weight
        self.MAX_SPEED_Y = 2.5 * self.weight

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
        self.angle = math.degrees(math.atan(incline)) * 1.168  # shift tan of the incline
        self.angle = int(self.angle)

    #the object needs to adjust its angle
    def __ObjectOnRamps(self):

        #check if right wall
        if RIGHT_WALL - self.xPlace < DISTANCE_FROM__WALL:  # right wall
            xDiffRightWall = DISTANCE_FROM__WALL - (RIGHT_WALL - self.xPlace)
            onFloorRamp = FLOOR_HEIGHT - self.yPlace <= self.__Function(xDiffRightWall) and (self.xPlace != RIGHT_WALL or self.ySpeed > 0)
            onCeilingRamp = self.yPlace - CEILING_HEIGHT <= self.__Function(xDiffRightWall) and self.xPlace != RIGHT_WALL

            if self.xSpeed > 0 and (onCeilingRamp or onFloorRamp):  # if going up the ramp
                self.yPlace = FLOOR_HEIGHT - self.__Function(xDiffRightWall) if onFloorRamp\
                                    else CEILING_HEIGHT + self.__Function(xDiffRightWall) if onCeilingRamp\
                                    else self.yPlace
            elif (onCeilingRamp or onFloorRamp):  # if going down the ramp
                yDiff = FLOOR_HEIGHT - self.yPlace if onFloorRamp else self.yPlace - CEILING_HEIGHT if onCeilingRamp else 0
                self.xPlace = RIGHT_WALL - DISTANCE_FROM__WALL + self.__FindXValueForYValue(yDiff)
            
            if onFloorRamp or onCeilingRamp:
                self.ObjectOnGround = True
                self.__GetObjectAngleOnSides(xDiffRightWall)
        
        elif self.xPlace - LEFT_WALL < DISTANCE_FROM__WALL:  # left wall
            xDiffLeftWall = DISTANCE_FROM__WALL - (self.xPlace - LEFT_WALL)
            onFloorRamp = FLOOR_HEIGHT - self.yPlace <= self.__Function(xDiffLeftWall) and self.xPlace != LEFT_WALL
            onCeilingRamp = self.yPlace - CEILING_HEIGHT < self.__Function(xDiffLeftWall) and self.xPlace != LEFT_WALL
            
            if self.xSpeed < 0 and (onCeilingRamp or onFloorRamp):  # if going up the ramp
                self.yPlace = FLOOR_HEIGHT - self.__Function(xDiffLeftWall) if onFloorRamp\
                                    else CEILING_HEIGHT + self.__Function(xDiffLeftWall) if onCeilingRamp\
                                    else self.yPlace
            elif (onCeilingRamp or onFloorRamp):  # if going down the ramp
                yDiff = FLOOR_HEIGHT - self.yPlace if onFloorRamp else self.yPlace - CEILING_HEIGHT if onCeilingRamp else 0
                self.xPlace = LEFT_WALL + DISTANCE_FROM__WALL - self.__FindXValueForYValue(yDiff)
            
            if onFloorRamp or onCeilingRamp:
                self.ObjectOnGround = True
                self.__GetObjectAngleOnSides(xDiffLeftWall)

    # prevent the player from moving beyond walls
    def __ObjectBoundaries(self):
        self.ObjectOnGround = False  # we will assume the object is not on ground

        if self.xPlace <= LEFT_WALL:
            self.xPlace = LEFT_WALL
            self.xSpeed = 0
            self.ObjectOnGround = True
        elif self.xPlace >= RIGHT_WALL:
            self.xPlace = RIGHT_WALL
            self.xSpeed = 0
            self.ObjectOnGround = True
            self.angle = 90
        if self.yPlace >= FLOOR_HEIGHT:
            self.yPlace = FLOOR_HEIGHT
            self.ySpeed = 0
            self.angle = 0
            self.ObjectOnGround = True
        elif self.yPlace <= CEILING_HEIGHT:
            self.yPlace = CEILING_HEIGHT
            self.ySpeed = 0
            self.ObjectOnGround = True



    def __CalculateFrictionOfObject(self):
        # firstly for the object to have firction we need it to be on ground
        # we also need to check if the object is moving
        if self.ObjectOnGround and self.xSpeed != 0:
            Fk = self.yVector * FRICTION_FORCE_FK * -(self.xSpeed // abs(self.xSpeed))
                
            self.xVector += Fk  # multiply by which direction the car is facing

    # when jumping the player needs to sum the vectors in the right angle
    def __CalculateVectors(self):
        yPower = self.GRAVITY_FORCE_ACCELARATION * -50  # when jumping the force on the player needs to be big
        xPower = self.xVector

        totalVector = math.sqrt(xPower ** 2 + yPower ** 2)
        self.xVector = totalVector * math.cos(math.radians(self.angle+90))
        self.yVector = totalVector * -math.sin(math.radians(self.angle+90))

    #this function will calculate where the players need to be according to the vectors
    def CalculateObjectPlace(self, accerlerationX, IsJumping):
        self.xVector = accerlerationX * self.ACCELARATION_CAR

        if IsJumping:
            self.__CalculateVectors()
            self.ObjectOnGround = False
        else:
            self.yVector = self.GRAVITY_FORCE_ACCELARATION

        # we will use the physics function - currentPlace = placeBefore + speedBefore*timeDiff + (acceleration / 2) * timeDiff ** 2
        # we will use this function for both of the axis, one for the x axis and one for the y axis

        # before calculating we need to also calculate the Friction on the object
        self.__CalculateFrictionOfObject()

        # firstly we will need the speed which we will calculate 
        # we will use currentSpeed = prevSpeed + acceleration * timeDiff
        self.xSpeed = self.xSpeed + self.xVector * REFRESH_RATE_TIME
        self.ySpeed = self.ySpeed + self.yVector * REFRESH_RATE_TIME

        self.xSpeed = self.MAX_SPEED_X if self.xSpeed > self.MAX_SPEED_X else -self.MAX_SPEED_X if self.xSpeed < -self.MAX_SPEED_X else self.xSpeed
        self.ySpeed = self.MAX_SPEED_Y * 2 if self.ySpeed > self.MAX_SPEED_Y * 2 else -self.MAX_SPEED_Y * 2 if self.ySpeed < -self.MAX_SPEED_Y * 2 else self.ySpeed

        # if xSpeed is close to zero we will set it to be zero
        self.xSpeed = 0 if abs(self.xSpeed) - 2 <= 0 else self.xSpeed

        # now lets put it into the current place

        xDiff = self.xSpeed*REFRESH_RATE_TIME + (self.xVector / 2) * REFRESH_RATE_TIME ** 2
        yDiff = self.ySpeed*REFRESH_RATE_TIME + (self.yVector / 2) * REFRESH_RATE_TIME ** 2

        self.xPlace = self.xPlace + xDiff
        self.yPlace = self.yPlace + yDiff


        self.__ObjectBoundaries()
        self.__ObjectOnRamps()




class Ball(Object):
    pass