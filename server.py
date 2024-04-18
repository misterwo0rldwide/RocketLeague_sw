#Rocket League SideSwipe Game - Omer Kfir Herzog יא'3
import socket
import threading
import physics
import time
import pickle
import protocol


IP = '0.0.0.0'
PORT = 1393


BALL_STARTING_POS = (1260, 600)
BUFFER_LIMIT = 1024

PlayersAddrDict = {}
currentGames = {}

class Match:
    
    def __init__(self, playerSocket:tuple, player2Socket:tuple):

        self.playerSocket, self.playerAddr = playerSocket
        self.player2Socket, self.player2Addr = player2Socket

        self.ballX, self.ballY = BALL_STARTING_POS[0], BALL_STARTING_POS[1]
        self.ball = physics.Ball(500, BALL_STARTING_POS, 20)

        self.timeLeft = time.time()  # get the starting game time
    

    def RecvBySize(self, sock):
        try:
            size = int(sock.recv(protocol.BUFFER_LENGTH_SIZE).decode())  # get size
            buffer = b''
            while size:
                new_bufffer = sock.recv(size)
                if not new_bufffer:
                    return b''
                buffer += new_bufffer
                size -= len(new_bufffer)
            
            return buffer
        except socket.error as e:
            print(f"socket does not exist, disconnecting it")
            return None
    
    def HandleGame(self):
        while self.timeLeft > 0:
            self.playerObject = self.RecvBySize(self.playerSocket)[protocol.BUFFER_LENGTH_SIZE:]
            self.player2Object = self.RecvBySize(self.player2Socket)[protocol.BUFFER_LENGTH_SIZE:]

            playerObject = pickle.loads(self.playerObject)
            player2Object = pickle.loads(self.player2Object)
            self.ball.CalculateBallPlace([playerObject, player2Object])

            self.playerSocket.send(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, self.player2Object))
            self.playerSocket.send(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, pickle.dumps(self.ball)))

            self.player2Socket.send(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, self.playerObject))
            self.player2Socket.send(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, pickle.dumps(self.ball)))

    def Lunching(self):
        self.playerSocket.send(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None))
        self.player2Socket.send(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None))

        self.HandleGame()


def HandlePlayers(server_socket_tcp:socket):
    global PlayersAddrDict

    prevAddr = ''

    while True:
        sock, addr = server_socket_tcp.accept()

        playerGameId = len(PlayersAddrDict) // 2
        PlayersAddrDict[addr] = playerGameId
        
        if len(PlayersAddrDict) % 2 == 0:  # new match added - 2 players exist
            game = Match((prevSock,prevAddr), (sock, addr))
            t = threading.Thread(target=game.Lunching, args=())  # start game
            t.start()

            print(f'new game started - player1-{prevAddr}, player2{addr}')

        prevAddr = addr
        prevSock = sock






def main():
    server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket_tcp.bind((IP, PORT))
    server_socket_tcp.listen()

    print('Server running')

    HandlePlayers(server_socket_tcp)
    

    server_socket_tcp.close()
        




if __name__ == '__main__':
    main()