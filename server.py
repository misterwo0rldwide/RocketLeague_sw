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
    
    def __init__(self, server_socket_udp:socket,playerAddr:tuple, player2Addr:tuple):

        self.server_socket_udp = server_socket_udp
        self.playerAddr = playerAddr
        self.player2Addr = player2Addr

        self.ballX, self.ballY = BALL_STARTING_POS[0], BALL_STARTING_POS[1]
        self.ball = physics.Ball(BALL_WEIGHT, BALL_STARTING_POS, BALL_RADIUS)

        self.timeLeft = time.time()  # get the starting game time
    

    def HandleGame(self):

        # each game is atlest two minutes
        while time.time() - self.timeLeft < 120:
            
            msg1, addr1 = RecvMsg(self.server_socket_udp)
            msg1 = msg1[protocol.BUFFER_LENGTH_SIZE:]
            msg2, addr2 = RecvMsg(self.server_socket_udp)
            msg2 = msg2[protocol.BUFFER_LENGTH_SIZE:]

            playerObject = pickle.loads(msg1) if addr1 == self.playerAddr else pickle.loads(msg2)
            player2Object = pickle.loads(msg2) if addr2 == self.player2Addr else pickle.loads(msg1)
            
            self.ball.CalculateBallPlace([playerObject, player2Object])

            playerObject = pickle.dumps(playerObject)
            player2Object = pickle.dumps(player2Object)
            ball = pickle.dumps(self.ball)

            self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, player2Object), self.playerAddr)
            self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, ball), self.playerAddr)

            self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, playerObject), self.player2Addr)
            self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, ball), self.player2Addr)
        
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.GAME_ENDED, None), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.GAME_ENDED, None), self.player2Addr)


    def Lunching(self):
        # sending to players that the game is about to start
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.player2Addr)
        
        # sending for the players which player they are
        # '0' - second player, '1' - first player
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_STARTING_POS, '1'), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_STARTING_POS, '0'), self.player2Addr)

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
        print(f"socket does not exist, disconnecting it")
        return None


def HandlePlayers(server_socket_udp : socket):
    prevAddr = ''
    playersConnected = 0  # amount of players that have connected

    while True:
        data, addr = RecvMsg(server_socket_udp)

        msg = data[:protocol.BUFFER_LENGTH_SIZE - 1].decode()


        if msg == protocol.PLAYER_CONNECTING:
            playersConnected += 1
            if playersConnected % 2 == 0:  # new match added - 2 players exist
                new_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                new_server_socket.bind((IP, 0))
                port = str(new_server_socket.getsockname()[1])

                server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port), prevAddr)
                server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port), addr)

                game = Match(new_server_socket, prevAddr, addr)
                t = threading.Thread(target=game.Lunching, args=())  # start game
                t.start()

                print(f'new game started - player1-{prevAddr}, player2{addr}')

            prevAddr = addr
        


def main():
    server_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket_udp.bind((IP, PORT))

    print('Server running')

    HandlePlayers(server_socket_udp)
    
    server_socket_udp.close()



if __name__ == '__main__':
    main()