#Rocket League SideSwipe Game - Omer Kfir Herzog יא'3
import socket
import threading
import physics
import time
import pickle
import protocol


IP = '0.0.0.0'
PORT = 1393


BALL_STARTING_POS = (1200, 600)
BUFFER_LIMIT = 1024

BALL_RADIUS = 40
BALL_WEIGHT = 70

class Match:
    
    def __init__(self, server_socket_udp:socket):

        self.server_socket_udp = server_socket_udp
        self.server_socket_udp.settimeout(1)

        msg, addr = RecvMsg(self.server_socket_udp)
        if msg.decode()[:-1] == protocol.JOINING_GAME:
            self.playerAddr = addr
        
        msg, addr = RecvMsg(self.server_socket_udp)
        if msg.decode()[:-1] == protocol.JOINING_GAME:
            self.player2Addr = addr

        self.ballX, self.ballY = BALL_STARTING_POS[0], BALL_STARTING_POS[1]
        self.ball = physics.Ball(BALL_WEIGHT, BALL_STARTING_POS, BALL_RADIUS)
    

    def HandleGame(self):

        # each game is atleast two minutes
        running = True
        timeLeft = time.time()  # get the starting game time

        time.sleep(5)
        while running:
            
            msg1, addr1 = RecvMsg(self.server_socket_udp)
            if not (msg1 == "" and addr1 == ""):
                msg1 = msg1[protocol.BUFFER_LENGTH_SIZE:]
            msg2, addr2 = RecvMsg(self.server_socket_udp)
            if not (msg2 == "" and addr2 == ""):
                msg2 = msg2[protocol.BUFFER_LENGTH_SIZE:]

            if msg1 != "" and msg2 != "":    
                playerObject = pickle.loads(msg1) if addr1 == self.playerAddr else pickle.loads(msg2)
                player2Object = pickle.loads(msg2) if addr2 == self.player2Addr else pickle.loads(msg1)
                
                self.ball.CalculateBallPlace([playerObject, player2Object])
                
                playerObject = pickle.dumps(playerObject)
                player2Object = pickle.dumps(player2Object)
                ball = pickle.dumps(self.ball)
                
                self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, player2Object), self.playerAddr)
                self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, playerObject), self.playerAddr)
                self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, ball), self.playerAddr)

                self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, playerObject), self.player2Addr)
                self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, player2Object), self.player2Addr)
                self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, ball), self.player2Addr)
            else:
                playerObject = None
                player2Object = None

            if self.ball.inGoal:
                time.sleep(5)
                timeLeft += 5  # because the players wait five seconds
                self.ball.xPlace, self.ball.ySpeed = BALL_STARTING_POS
                self.ball.xSpeed, self.ball.ySpeed = 0,0

            currentTime = time.time()
            if currentTime - timeLeft > 124:
                running = False

        
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.GAME_ENDED, None), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.GAME_ENDED, None), self.player2Addr)

        print(f'game ended - player1-{self.playerAddr}, player2{self.player2Addr}')
        self.server_socket_udp.close()


    def Lunching(self):
        # sending to players that the game is about to start
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.player2Addr)
        
        # sending for the players which player they are
        # '0' - second player, '1' - first player
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_STARTING_POS, '1'), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_STARTING_POS, '0'), self.player2Addr)


        # now we ensure both sides got data
        player1GotData = False
        player2GotData = False
        while True:
            if not player1GotData:
                msg1, addr = RecvMsg(self.server_socket_udp)
                if msg1 != "" and msg1.decode() == protocol.MSG_NOT_RECIVED:
                    self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), addr)
                elif msg1.decode()[:-1] == protocol.MSG_RECIVED:
                    player1GotData = True
            
            if not player2GotData:
                msg2, addr = RecvMsg(self.server_socket_udp)
                if msg2 != "" and msg2.decode() == protocol.MSG_NOT_RECIVED:
                    self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), addr)
                elif msg2.decode()[:-1] == protocol.MSG_RECIVED:
                    player2GotData = True
            
            if player1GotData and player2GotData:
                break

        self.HandleGame()


def RecvMsg(sock) -> tuple:
    try:
        buffer,addr = sock.recvfrom(protocol.MAX_MESSAGE_LENGTH)
        size = int(buffer[:protocol.BUFFER_LENGTH_SIZE].decode())  # get size

        buffer = buffer[protocol.BUFFER_LENGTH_SIZE:]
        
        if size != len(buffer):
            raise Exception("Data corrupted")

        return buffer, addr
    except socket.error as e:
        print(e)
        return "", ""


def HandlePlayers(server_socket_tcp : socket):
    prevClient = ''
    prevAddr = ''
    playersConnected = 0  # amount of players that have connected

    while True:
        client, addr = server_socket_tcp.accept()
        
        playersConnected += 1
        if playersConnected % 2 == 0:  # new match added - 2 players exist
            new_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_server_socket.bind((IP, 0))
            port = str(new_server_socket.getsockname()[1])

            client.send(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port))
            prevClient.send(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port))

            game = Match(new_server_socket)
            t = threading.Thread(target=game.Lunching, args=())  # start game
            t.start()

            print(f'new game started - player1-{prevAddr}, player2{addr}')

        prevClient = client
        prevAddr = addr
        


def main():
    server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket_tcp.bind((IP, PORT))
    server_socket_tcp.listen()

    print('Server running')

    HandlePlayers(server_socket_tcp)
    
    server_socket_tcp.close()



if __name__ == '__main__':
    main()