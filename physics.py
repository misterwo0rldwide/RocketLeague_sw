#Rocket League SideSwipe Game - Omer Kfir Herzog יא'3
import math


# heights and x values of walls
FLOOR_HEIGHT = 850
CEILING_HEIGHT = 100
RIGHT_WALL = 2150
LEFT_WALL = 300
DISTANCE_FROM__WALL = 110  # distance from wall of ramp

REFRESH_RATE_TIME = 1/60  # we need the refresh rate time to calculate time differences

FRICTION_FORCE_PLAYER_FK = 0.4
FRICTION_FORCE_BALL_FK = 0.6

MAX_BOOST = 100
ENERGY_LOSS = 0.6

BOUNCE_POWER = 2.5

# a class for rectangle objects
class Object:
    def __init__(self,width:int,height:int,weight: int,statringPlace:tuple):
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

        self.framesOnCeiling = 0

        self.IsBoosting = False

        self.IsJumping = False
        self.IsDoubleJumping = False

    def Function(self, x):
        return (x**2) / 100
    
    def FindXValueForYValue(self, y):
        return math.sqrt(y * 100)

    def __DerivativeFunction(self, x):
        return 2*x / 100

    # the sides of the map require the player to change its angle
    def GetObjectAngleOnSides(self, xDiff):
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
        normalWallAngle = self.GetObjectAngleOnSides(xDiff)
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
    def ObjectOnRamps(self):

        #check if right wall
        if RIGHT_WALL - self.xPlace < DISTANCE_FROM__WALL:  # right wall
            xDiffRightWall = DISTANCE_FROM__WALL - (RIGHT_WALL - self.xPlace)
            onFloorRamp = FLOOR_HEIGHT - self.yPlace <= self.Function(xDiffRightWall) and (self.xPlace != RIGHT_WALL or self.ySpeed > 0)
            onCeilingRamp = self.yPlace - CEILING_HEIGHT <= self.Function(xDiffRightWall) and (self.xPlace != RIGHT_WALL or self.ySpeed < 0)

            if self.xSpeed > 0 and (onCeilingRamp or onFloorRamp):  # if going up the ramp
                self.yPlace = FLOOR_HEIGHT - self.Function(xDiffRightWall) if onFloorRamp\
                                    else CEILING_HEIGHT + self.Function(xDiffRightWall) if onCeilingRamp\
                                    else self.yPlace
            elif (onCeilingRamp or onFloorRamp):  # if going down the ramp
                yDiff = FLOOR_HEIGHT - self.yPlace if onFloorRamp else self.yPlace - CEILING_HEIGHT if onCeilingRamp else 0
                self.xPlace = RIGHT_WALL - DISTANCE_FROM__WALL + self.FindXValueForYValue(yDiff)
            
            if onFloorRamp or onCeilingRamp:
                self.ObjectOnGround = True
                self.__CalculateAnglesWallRamps(True ,xDiffRightWall, onFloorRamp)
        
        elif self.xPlace - LEFT_WALL < DISTANCE_FROM__WALL:  # left wall
            xDiffLeftWall = DISTANCE_FROM__WALL - (self.xPlace - LEFT_WALL)
            onFloorRamp = FLOOR_HEIGHT - self.yPlace <= self.Function(xDiffLeftWall) and (self.xPlace != LEFT_WALL or self.ySpeed > 0)
            onCeilingRamp = self.yPlace - CEILING_HEIGHT < self.Function(xDiffLeftWall) and (self.xPlace != LEFT_WALL or self.ySpeed < 0)
            
            if self.xSpeed < 0 and (onCeilingRamp or onFloorRamp):  # if going up the ramp
                self.yPlace = FLOOR_HEIGHT - self.Function(xDiffLeftWall) if onFloorRamp\
                                    else CEILING_HEIGHT + self.Function(xDiffLeftWall) if onCeilingRamp\
                                    else self.yPlace
            elif (onCeilingRamp or onFloorRamp):  # if going down the ramp
                yDiff = FLOOR_HEIGHT - self.yPlace if onFloorRamp else self.yPlace - CEILING_HEIGHT if onCeilingRamp else 0
                self.xPlace = LEFT_WALL + DISTANCE_FROM__WALL - self.FindXValueForYValue(yDiff)
            
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
            if self.xSpeed > 0:
                self.flipObjectDraw = False
            elif self.xSpeed < 0:
                self.flipObjectDraw = True
            self.spinning = False
        elif self.yPlace <= CEILING_HEIGHT:
            self.yPlace = CEILING_HEIGHT
            self.ObjectOnGround = True
            self.angle = 180
            self.flipObjectDraw = True if self.xSpeed >= 0 else False
            self.spinning = False
            

    def CalculateFrictionOfObject(self, firction_force):
        # firstly for the object to have firction we need it to be on ground
        # we also need to check if the object is moving
        if self.ObjectOnGround and self.xSpeed != 0:
            Fk = self.yVector * firction_force * -(self.xSpeed // abs(self.xSpeed))
                
            self.xVector += Fk  # multiply by which direction the car is facing

            return Fk
        
        return 0


    def CalculateMaxSpeed(self, xMax, yMax):

        MAX_SPEED_X = xMax * self.weight
        MAX_SPEED_Y = yMax * self.weight

        if not self.ObjectOnGround or self.IsBoosting:
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
    
    # calculating the vectors using the accelrations
    def __CalculateVectors(self,accelerationX: int, accelerationY: int ,IsJumping: bool, PlayerTouchedControls: bool):
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
    
    # calculate the ceiling acceleration - the player needs to stay a couple of seconds on ceiling
    def __HandleCeiling(self):
        if self.yPlace == CEILING_HEIGHT:
            self.framesOnCeiling += 1
            self.yVector = -self.GRAVITY_FORCE_ACCELARATION + (self.GRAVITY_FORCE_ACCELARATION / 10) * self.framesOnCeiling
        else:
            self.framesOnCeiling = 0

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
        if self.boostAmount > 1:
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

        self.__CalculateVectors(accelerationX, accelerationY,IsJumping, PlayerTouchedControls)
        self.IsBoosting = IsBoosting

        if self.IsBoosting:
            self.__PlayerBoosting()
        else:
            if self.ObjectOnGround and self.boostAmount < 100:
                self.boostAmount += 1
            #self.boostAmount = self.boostAmount + 1 if self.ObjectOnGround and self.boostAmount < 100 else self.boostAmount

        self.__HandleCeiling()

        # we will use the physics function - currentPlace = placeBefore + speedBefore*timeDiff + (acceleration / 2) * timeDiff ** 2
        # we will use this function for both of the axis, one for the x axis and one for the y axis

        # before calculating we need to also calculate the Friction on the object
        self.CalculateFrictionOfObject(FRICTION_FORCE_PLAYER_FK)

        # firstly we will need the speed which we will calculate 
        # we will use currentSpeed = prevSpeed + acceleration * timeDiff
        self.xSpeed = self.xSpeed + self.xVector * REFRESH_RATE_TIME
        self.ySpeed = self.ySpeed + self.yVector * REFRESH_RATE_TIME


        self.CalculateMaxSpeed(3, 2.5)

        # if xSpeed is close to zero we will set it to be zero because of friction
        self.xSpeed = 0 if abs(self.xSpeed) - 5 <= 0 else self.xSpeed

        # now lets put it into the current place

        xDiff = self.xSpeed*REFRESH_RATE_TIME + (self.xVector / 2) * REFRESH_RATE_TIME ** 2
        yDiff = self.ySpeed*REFRESH_RATE_TIME + (self.yVector / 2) * REFRESH_RATE_TIME ** 2

        # before moving we will save the current place so that after moving we will have the correct speed
        yplace = self.yPlace
        xplace = self.xPlace

        self.xPlace = self.xPlace + xDiff
        self.yPlace = self.yPlace + yDiff

        self.__ObjectBoundaries()  # firstly we will check the state of the object
        self.ObjectOnRamps()

        # calculating the real speed of the object
        self.ySpeed = (self.yPlace - yplace) / REFRESH_RATE_TIME
        self.xSpeed = (self.xPlace - xplace) / REFRESH_RATE_TIME

        self.__AdjustAngle(PlayerTouchedControls, saveAccelerationX, saveAccelerationY)




# we will also have ball physics, similar to object physics but with a few changes
class Ball(Object):
    
    def __init__(self, weight: int, startingPlace: tuple, radius:int):
        Object.__init__(self, 0, 0, weight, startingPlace)
        self.radius = radius
        self.ObjectOnGround = False # ball starts from air

        self.angleSub = 0  # we need to know for printing the ball how much the ball need to spin
        self.inGoal = False
    

    def BallBoundaries(self):
        self.ObjectOnGround = False
        self.inGoal = False

        if self.xPlace <= LEFT_WALL:
            if self.yPlace >= 375 and self.yPlace + self.radius * 2 <= 750:
                if self.xPlace <= LEFT_WALL - self.radius:
                    self.inGoal = True
            else:
                self.xPlace = LEFT_WALL
                self.xSpeed *= -1
                self.ObjectOnGround = True

        elif self.xPlace >= RIGHT_WALL:
            if self.yPlace >= 375 and self.yPlace + self.radius * 2 <= 750:
                if self.xPlace >= RIGHT_WALL + self.radius:
                    self.inGoal = True
            else:
                self.xPlace = RIGHT_WALL
                self.xSpeed *= -1
                self.ObjectOnGround = True
        
        if self.yPlace + self.radius >= FLOOR_HEIGHT:
            self.yPlace = FLOOR_HEIGHT - self.radius
            self.ySpeed *= -1
            self.ObjectOnGround = True

        elif self.yPlace <= CEILING_HEIGHT:
            self.yPlace = CEILING_HEIGHT
            self.ySpeed *= -1
            self.ObjectOnGround = True
    

    def BallOnRamps(self):
        #check if right wall
        if RIGHT_WALL - self.xPlace - self.radius < DISTANCE_FROM__WALL:  # right wall
            xDiffRightWall = DISTANCE_FROM__WALL - (RIGHT_WALL - self.xPlace)
            onFloorRamp = FLOOR_HEIGHT - self.yPlace - self.radius <= self.Function(xDiffRightWall)
            onCeilingRamp = self.yPlace - CEILING_HEIGHT + self.radius <= self.Function(xDiffRightWall)

            if (onFloorRamp or onCeilingRamp) and xDiffRightWall > 20:
                if xDiffRightWall > DISTANCE_FROM__WALL + self.radius / 3:
                    self.inGoal = True
                else:
                    self.yPlace = FLOOR_HEIGHT - self.radius - self.Function(xDiffRightWall) if onFloorRamp else CEILING_HEIGHT - self.radius + self.Function(xDiffRightWall)
                    angle = self.GetObjectAngleOnSides(xDiffRightWall)
                    angle = 180 - angle if onFloorRamp else 180 + angle

                    totalSpeed = math.sqrt(self.xSpeed ** 2 + self.ySpeed ** 2) / 2
                    self.xSpeed += (totalSpeed) / math.cos(math.radians(angle))
                    self.ySpeed -= (totalSpeed) / math.sin(math.radians(angle))

                    return angle
                

        
        elif (self.xPlace + self.radius) - LEFT_WALL < DISTANCE_FROM__WALL:  # left wall
            xDiffLeftWall = DISTANCE_FROM__WALL - (self.xPlace - LEFT_WALL)
            onFloorRamp = FLOOR_HEIGHT - self.yPlace - self.radius <= self.Function(xDiffLeftWall)
            onCeilingRamp = self.yPlace - CEILING_HEIGHT + self.radius <= self.Function(xDiffLeftWall)
            
            if onFloorRamp or onCeilingRamp and xDiffLeftWall > 20:
                if xDiffLeftWall > DISTANCE_FROM__WALL + self.radius / 3:
                    self.inGoal = True
                else:
                    self.yPlace = FLOOR_HEIGHT - self.radius - self.Function(xDiffLeftWall) if onFloorRamp else CEILING_HEIGHT - self.radius + self.Function(xDiffLeftWall)
                    angle = self.GetObjectAngleOnSides(xDiffLeftWall)
                    angle = angle if onFloorRamp else 360 - angle

                    totalSpeed = math.sqrt(self.xSpeed ** 2 + self.ySpeed ** 2) / 2
                    self.xSpeed += (totalSpeed) / math.cos(math.radians(angle))
                    self.ySpeed -= (totalSpeed) / math.sin(math.radians(angle))

                    return angle



    def __GetRotatedRectCoordinate(self, angle: float, currentX : float, centerX : float, currentY : float, centerY : float, rectFlipped) -> tuple[float, float]:

        # Convert rotation angle from degrees to radians
        angle = angle if not rectFlipped else 360 - angle
        theta = math.radians(angle)
        
        # Calculate the distance from the center of rotation to the top left corner
        dx = currentX - centerX
        dy = currentY - centerY
        
        # Calculate the new angle after rotation
        x1 = centerX + dx * math.cos(theta) + dy * math.sin(theta)
        y1 = centerY - dx * math.sin(theta) + dy * math.cos(theta)

        return x1, y1
    
    # distance from the middle of the ball to the coordiante
    def __BallCoordianteDistance(self, coordinate:tuple) -> float:
        # we will do simple pythagoras

        centerBallX = self.xPlace + self.radius
        xDiff = centerBallX - coordinate[0]

        centerBallY = self.yPlace + self.radius
        yDiff = centerBallY - coordinate[1]

        return math.sqrt(xDiff ** 2 + yDiff ** 2)


    def BallRectCollision(self, rect : Object) -> tuple[bool, float, float]:
        rectCenterX = rect.xPlace + rect.width / 2
        rectCenterY = rect.yPlace + rect.height / 2

        if abs((self.yPlace + self.radius) - rectCenterY) > self.radius + rect.height / 2:
            return False, (0,0), 0
        if abs((self.xPlace + self.radius) - rectCenterX) > self.radius + rect.width / 2:
            return False, (0,0), 0

        # we will check each of its corners
        topLeftCornerCoordinate = self.__GetRotatedRectCoordinate(rect.angle, rect.xPlace, rectCenterX, rect.yPlace, rectCenterY, rect.flipObjectDraw)
        distance = self.__BallCoordianteDistance(topLeftCornerCoordinate)
        if distance <= self.radius:
            return True, topLeftCornerCoordinate, distance
        
        topRightCornerCoordinate = self.__GetRotatedRectCoordinate(rect.angle, rect.xPlace + rect.width, rectCenterX, rect.yPlace + 5, rectCenterY, rect.flipObjectDraw)
        distance = self.__BallCoordianteDistance(topRightCornerCoordinate)
        if distance <= self.radius:
            return True, topRightCornerCoordinate, distance
        
        bottomLeftCornerCoordinate = self.__GetRotatedRectCoordinate(rect.angle, rect.xPlace, rectCenterX, rect.yPlace + rect.height, rectCenterY, rect.flipObjectDraw)
        distance = self.__BallCoordianteDistance(bottomLeftCornerCoordinate)
        if distance <= self.radius:
            return True, bottomLeftCornerCoordinate, distance
        
        bottomRightCornerCoordiante = self.__GetRotatedRectCoordinate(rect.angle, rect.xPlace + rect.width, rectCenterX, rect.yPlace + rect.height, rectCenterY, rect.flipObjectDraw)
        distance = self.__BallCoordianteDistance(bottomRightCornerCoordiante)
        if distance <= self.radius:
            return True, bottomRightCornerCoordiante, distance
        
        middleUpperCornerCoordinate = self.__GetRotatedRectCoordinate(rect.angle, rect.xPlace + rect.width / 2, rectCenterX, rect.yPlace, rectCenterY, rect.flipObjectDraw)
        distance = self.__BallCoordianteDistance(middleUpperCornerCoordinate)
        if distance <= self.radius:
            return True, middleUpperCornerCoordinate, distance
    
        middleDownCornerCoordinate = self.__GetRotatedRectCoordinate(rect.angle, rect.xPlace + rect.width / 2, rectCenterX, rect.yPlace + self.height, rectCenterY, rect.flipObjectDraw)
        distance = self.__BallCoordianteDistance(middleDownCornerCoordinate)
        if distance <= self.radius:
            return True, middleDownCornerCoordinate, distance
        
        return False, (0,0), 0


    # when ball and player overlapp we need to seperate them they dont go into one another
    def PreventOverLappingBallRect(self, alpha : float, xDiff, yDiff):

        xAdd = self.radius * math.cos(math.radians(alpha)) - xDiff
        yAdd = self.radius * math.sin(math.radians(alpha)) + yDiff

        self.xPlace += xAdd
        self.yPlace -= yAdd


    # we will need collision with objects for this one
    # because more than one object can hit the balls we will get a list of all the objects
    # and we will check which one is hitting the ball then we will calculate the balls vectors
    def CollisionWithObject(self, rects: list[Object]):
        # we will use attack and momentuem equation which is m1 * v1 + m2 * v2 = m1 * u1 + m2 * u2 * cos(a)
        # where v is the speed before and u is the speed after

        for rect in rects:
            
            if type(rect) == Object:
                colDetection, coordiante, distance = self.BallRectCollision(rect)
                if colDetection:  # if indeed a collision
                    if self.ObjectOnGround and not rect.ObjectOnGround:
                        rect.ySpeed = self.ySpeed * BOUNCE_POWER
                        rect.IsJumping = False
                        rect.IsDoubleJumping = False

                    yDiff = (self.yPlace + self.radius) - coordiante[1]
                    xDiff = (self.xPlace + self.radius) - coordiante[0]

                    # all axis speed
                    m1 = rect.weight
                    v1 = math.sqrt(rect.xSpeed ** 2 + rect.ySpeed ** 2)

                    m2 = self.weight
                    v2 = math.sqrt(self.xSpeed ** 2 + self.ySpeed ** 2)

                    u1 = v1 * ENERGY_LOSS

                    totalSpeed = ((m1*v1 + m2*v2 - m1 * u1) / m2) 

                    alpha = 0
                    alpha = math.degrees(math.asin(-yDiff / distance))

                    if alpha == 0:
                        alpha = math.degrees(math.acos(xDiff / distance))

                    alpha = 360 + alpha if alpha < 0 else alpha
                    if xDiff < 0 and alpha != 180:
                        alpha = 180 - alpha
                    
                    self.xSpeed += totalSpeed * math.cos(math.radians(alpha))
                    self.ySpeed -= totalSpeed * math.sin(math.radians(alpha))

                    self.PreventOverLappingBallRect(alpha, xDiff, yDiff)
                    self.BallBouncesPlayer(rect)


    def BallBouncesPlayer(self, rect : Object):
        angle = self.BallOnRamps()
        # if the object is not on ramps it will return None
        if angle is not None:
            boostSpeed = 20 * rect.weight
            rect.xSpeed = boostSpeed * math.cos(math.radians(angle))
            rect.ySpeed = -boostSpeed * math.sin(math.radians(angle))
            rect.IsJumping = False
            rect.IsDoubleJumping = False
            rect.boostAmount += 20
                


    def CalculateBallPlace(self, rect: list[Object]):
        #this function will be close to the object one, but because ball is not controlled by anyone, it will be slightly different
        #we will also use similar function such as x = x0 + v0(t - t0) + a/2(t - t0)^2

        angleSub = self.CalculateFrictionOfObject(FRICTION_FORCE_BALL_FK)
        self.angleSub = angleSub if angleSub != 0 else self.angleSub
        self.BallOnRamps()
        self.CollisionWithObject(rect)
        
        self.xSpeed = self.xSpeed + self.xVector * REFRESH_RATE_TIME
        self.ySpeed = self.ySpeed + self.yVector * REFRESH_RATE_TIME

        self.xSpeed = 0 if abs(self.xSpeed) < 5 else self.xSpeed
        self.CalculateMaxSpeed(5, 3.5)

        xDiff = self.xSpeed*REFRESH_RATE_TIME + (self.xVector / 2) * REFRESH_RATE_TIME ** 2
        yDiff = self.ySpeed*REFRESH_RATE_TIME + (self.yVector / 2) * REFRESH_RATE_TIME ** 2

        self.xPlace = self.xPlace + xDiff
        self.yPlace = self.yPlace + yDiff

        self.xSpeed = xDiff / REFRESH_RATE_TIME
        self.ySpeed = yDiff / REFRESH_RATE_TIME if self.yPlace != FLOOR_HEIGHT - self.radius else self.ySpeed

        self.BallBoundaries()

        # different from other objects, with balls (an object that no one controls) we need to zero out the vectors
        self.xVector = 0
        self.yVector = self.GRAVITY_FORCE_ACCELARATION

        self.angle = (self.angle - self.xSpeed / self.radius)  % 360

        