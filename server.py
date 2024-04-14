#Rocket League SideSwipe Game - Omer Kfir Herzog יא'3
import socket
import math
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

class Match:
    
    def __init__(self, server_socket:socket, playerSocket, player2Socket):

        self.server_socket = server_socket

        self.playerSocket = playerSocket
        self.player2Socket = player2Socket

        self.playerObject = None
        self.player2Object = None

        self.playerGotData = False
        self.Player2GotData = False

        self.ballX, self.ballY = BALL_STARTING_POS[0], BALL_STARTING_POS[1]
        self.ball = physics.Ball(500, BALL_STARTING_POS, 20)

        self.timeLeft = time.time()  # get the starting game time
    

    def RecvMsgBySizeUDP(self):
        try:
            data,_ = self.playerSocket.recvfrom(BUFFER_LIMIT)
            length = int(data[:4].decode())
            if length < len(data):
                data = data[:length]
            
            return data
        except Exception:
            return None
        


    def __GetPlayerInformation(self, playerAddr, data):
        if playerAddr == self.playerSocket:
            self.playerObject = pickle.loads(data)
            self.playerGotData = True
        else:
            self.player2Object = pickle.loads(data)
            self.Player2GotData = True

    
    def HandleGame(self):
        while not (self.playerGotData and self.Player2GotData):  # if not all the players got the data
            self.__RecvMsgBySizeUDP()

        self.server_socket.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, pickle.dumps(self.player2Object)+b'~'+pickle.dumps(self.ball)), self.playerSocket)
        self.server_socket.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, pickle.dumps(self.playerObject)+b'~'+pickle.dumps(self.ball)), self.player2Socket)

        self.playerGotData = False
        self.Player2GotData = False
    

    def Lunching(self):
        self.playerSocket.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.player2Socket)
        self.player2Socket.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.playerSocket)

        self.HandleGame()


def HandlePlayers(server_socket):
    global PlayersAddrDict

    prevAddr = ''

    while True:
        msgWithLength, addr = server_socket.recvfrom(BUFFER_LIMIT)
        data = msgWithLength[4:]

        request = data.decode()[:3]

        if addr not in PlayersAddrDict and request == protocol.PLAYER_CONNECTING:  # add player to game
            playerGameId = len(PlayersAddrDict) // 2
            PlayersAddrDict[addr] = playerGameId
            
            if len(PlayersAddrDict) % 2 == 0:  # new match added - 2 players exist
                game = Match(server_socket, prevAddr, addr)
                t = threading.Thread(target=game.Lunching, args=())  # start game
                t.start()

        prevAddr = addr






def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((IP, PORT))

    HandlePlayers(server_socket)
    

    server_socket.close()
        




if __name__ == '__main__':
    main()