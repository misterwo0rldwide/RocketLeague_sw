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

        self.firstPlayerConnected = False
        self.secondPlayerConnected = False

        self.firstPlayerTimeConnected = time.time()
        self.secondPlayerTimeConnected = time.time()

        self.firstPlayerData = None
        self.secondPlayerData = None

    def send_game_data(self, addr, secondPlayerData, firstPlayerData, ball):
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.SECOND_PLAYER_INFO, secondPlayerData), addr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, firstPlayerData), addr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.BALL_INFO, ball), addr)
    
    
    def recv_game_data(self):
        msg1, addr1 = RecvMsg(self.server_socket_udp)
        msg2, addr2 = RecvMsg(self.server_socket_udp)
        ls = [(msg1, addr1), (msg2, addr2)]

        for msg, addr in ls:

            # if we got message and not socket timeout
            if msg != "":
                msg_command = msg[:protocol.BUFFER_LENGTH_SIZE - 1].decode()
                msg_info = msg[protocol.BUFFER_LENGTH_SIZE:]

                # if the player sent that he is still connected to the game
                if msg_command == protocol.PLAYER_STILL_CONNECTED:
                    
                    if addr == self.playerAddr:
                        self.firstPlayerConnected = True
                    else:
                        self.secondPlayerConnected = True

                    msg1, addr1 = RecvMsg(self.server_socket_udp)
                    ls.append((msg1, addr1))
                
                elif msg_command == protocol.PLAYER_INFO:
                    if addr == self.playerAddr:
                        self.firstPlayerData = msg_info
                    elif addr == self.player2Addr:
                        self.secondPlayerData = msg_info




    def HandleGame(self):

        # each game is atleast two minutes
        self.running = True
        timeLeft = time.time()  # get the starting game time
        retMsg = protocol.GAME_ENDED
        ball = None

        time.sleep(5)
        while self.running:
            self.recv_game_data()

            first_player = pickle.loads(self.firstPlayerData) if self.firstPlayerData != None else self.firstPlayerData
            second_player = pickle.loads(self.secondPlayerData) if self.secondPlayerData != None else self.secondPlayerData
            
            self.ball.CalculateBallPlace([first_player, second_player])

            first_player = pickle.dumps(first_player)
            second_player = pickle.dumps(second_player)
            ball = pickle.dumps(self.ball)

            self.send_game_data(self.playerAddr, second_player, first_player, ball)
            self.send_game_data(self.player2Addr, first_player, second_player, ball)


            if self.ball.inGoal:
                timeLeft += 5  # because the players wait five seconds
                self.firstPlayerTimeConnected += 5
                self.secondPlayerTimeConnected += 5
                self.ball.xPlace, self.ball.ySpeed = BALL_STARTING_POS
                self.ball.xSpeed, self.ball.ySpeed = 0,0
                self.recv_game_data()
                time.sleep(5)
            
            if self.firstPlayerConnected:
                self.firstPlayerTimeConnected = time.time()
            else:
                if time.time() - self.firstPlayerTimeConnected > 6:  # if one of the players is not connected
                    self.running = False
                    retMsg = protocol.GAME_STOPPED_ENTHERNET
            
            if self.secondPlayerConnected:
                self.secondPlayerTimeConnected = time.time()
            else:
                if time.time() - self.secondPlayerTimeConnected > 6:
                    self.running = False
                    retMsg = protocol.GAME_STOPPED_ENTHERNET
            
            self.firstPlayerConnected = False
            self.secondPlayerConnected = False

            currentTime = time.time()
            if currentTime - timeLeft > 124:
                self.running = False
                
        
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(retMsg, None), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(retMsg, None), self.player2Addr)

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
        return "", ""


# gets a list of clients
# check if each of the client is connected
# if not removes it
def check_client_connected(clients: list[socket.socket]):

    for sock in clients:
        
        sock.settimeout(0.1)
        try:
            sock.recv(1)
        except ConnectionError as e:
            # if got to here it means the socket does not longer exists
            clients.remove(sock)
        except socket.timeout as e:
            pass


def HandlePlayers(server_socket_tcp : socket):
    prevClient = ''
    prevAddr = ''
    currentClient = []


    while True:
        client, addr = server_socket_tcp.accept()
        
        currentClient.append(client)
        check_client_connected(currentClient)

        if len(currentClient) % 2 == 0:  # new match added - 2 players exist
            new_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_server_socket.bind((IP, 0))
            port = str(new_server_socket.getsockname()[1])

            client.send(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port))
            prevClient.send(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port))

            game = Match(new_server_socket)
            t = threading.Thread(target=game.Lunching, args=())  # start game
            t.start()

            currentClient.remove(prevClient)
            currentClient.remove(client)

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