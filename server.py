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

t_id = 0

class Match:
    
    def __init__(self, server_socket_udp:socket):

        self.server_socket_udp = server_socket_udp
        self.server_socket_udp.settimeout(1)

        msg, addr = RecvMsg(self.server_socket_udp)
        while len(msg) == 0 or msg.decode()[:-1] != protocol.JOINING_GAME:
            msg, addr = RecvMsg(self.server_socket_udp)

        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.SERVER_GOT_ADDRESS, None), addr)
        log_output_data(protocol.BuildMsgProtocol(protocol.SERVER_GOT_ADDRESS, None), addr)
        self.playerAddr = addr
        
        msg, addr = RecvMsg(self.server_socket_udp)
        while len(msg) == 0 or msg.decode()[:-1] != protocol.JOINING_GAME:
            msg, addr = RecvMsg(self.server_socket_udp)

        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.SERVER_GOT_ADDRESS, None), addr)
        log_output_data(protocol.BuildMsgProtocol(protocol.SERVER_GOT_ADDRESS, None), addr)
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
        log_output_data(protocol.BuildMsgProtocol(protocol.SECOND_PLAYER_INFO, secondPlayerData), addr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, firstPlayerData), addr)
        log_output_data(protocol.BuildMsgProtocol(protocol.PLAYER_INFO, firstPlayerData), addr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.BALL_INFO, ball), addr)
        log_output_data(protocol.BuildMsgProtocol(protocol.BALL_INFO, ball), addr)
        
    
    
    def recv_game_data(self):
        msg1, addr1 = RecvMsg(self.server_socket_udp)
        msg2, addr2 = RecvMsg(self.server_socket_udp)
        ls = [(msg1, addr1), (msg2, addr2)]

        for msg, addr in ls:

            # if we got message and not socket timeout
            if msg != "" and msg != 0:
                msg_command = msg[:protocol.BUFFER_LENGTH_SIZE - 1].decode()
                msg_info = msg[protocol.BUFFER_LENGTH_SIZE:]

                # if the player sent that he is still connected to the game
                if msg_command == protocol.PLAYER_STILL_CONNECTED:
                    
                    if addr == self.playerAddr:
                        self.firstPlayerConnected = True
                    elif addr == self.player2Addr:
                        self.secondPlayerConnected = True

                    msg1, addr1 = RecvMsg(self.server_socket_udp)
                    ls.append((msg1, addr1))
                
                elif msg_command == protocol.PLAYER_INFO:
                    if addr == self.playerAddr:
                        self.firstPlayerData = msg_info
                    elif addr == self.player2Addr:
                        self.secondPlayerData = msg_info
            
            elif msg == 0:
                self.running = False


    def HandleGame(self):

        # each game is atleast two minutes
        self.running = True
        timeLeft = time.time()  # get the starting game time
        retMsg = protocol.GAME_ENDED
        ball = None

        time.sleep(5)
        while self.running:
            self.recv_game_data()
            if self.running == False:
                retMsg = protocol.GAME_STOPPED_ENTHERNET
                break

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
        log_output_data(protocol.BuildMsgProtocol(retMsg, None), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(retMsg, None), self.player2Addr)
        log_output_data(protocol.BuildMsgProtocol(retMsg, None), self.playerAddr)

        print(f'game ended - player1-{self.playerAddr}, player2{self.player2Addr}')
        self.server_socket_udp.close()


    def Lunching(self, thread_id):
        global t_id

        # sending to players that the game is about to start
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.playerAddr)
        log_output_data(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.player2Addr)
        log_output_data(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), self.player2Addr)
        
        # sending for the players which player they are
        # '0' - second player, '1' - first player
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_STARTING_POS, '1'), self.playerAddr)
        log_output_data(protocol.BuildMsgProtocol(protocol.PLAYER_STARTING_POS, '1'), self.playerAddr)
        self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.PLAYER_STARTING_POS, '0'), self.player2Addr)
        log_output_data(protocol.BuildMsgProtocol(protocol.PLAYER_STARTING_POS, '0'), self.player2Addr)


        # now we ensure both sides got data
        player1GotData = False
        player2GotData = False
        while True:
            if not player1GotData:
                msg1, addr = RecvMsg(self.server_socket_udp)
                if msg1 != "" and msg1.decode()[:-1] == protocol.MSG_NOT_RECIVED:
                    self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), addr)
                    log_output_data(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), addr)
                elif msg1 != "" and msg1.decode()[:-1] == protocol.MSG_RECIVED:
                    player1GotData = True
            
            if not player2GotData:
                msg2, addr = RecvMsg(self.server_socket_udp)
                if msg2 != "" and msg2.decode()[:-1] == protocol.MSG_NOT_RECIVED:
                    self.server_socket_udp.sendto(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), addr)
                    log_output_data(protocol.BuildMsgProtocol(protocol.STARTING_GAME, None), addr)
                elif msg2 != "" and msg2.decode()[:-1] == protocol.MSG_RECIVED:
                    player2GotData = True
            
            if player1GotData and player2GotData:
                break

        self.HandleGame()
        print(f'Thread killed - id: {thread_id}')
        print(f'Socket killed - {self.server_socket_udp}')
        self.server_socket_udp.close()
        t_id -= 1


def RecvMsg(sock) -> tuple:
    try:
        buffer,addr = sock.recvfrom(protocol.MAX_MESSAGE_LENGTH)
        size = int(buffer[:protocol.BUFFER_LENGTH_SIZE].decode())  # get size

        print(f'---\nRECIVED MESSAGE\nAddress: {addr}\nContent: {buffer}\n---')

        buffer = buffer[protocol.BUFFER_LENGTH_SIZE:]
        
        if size != len(buffer):
            raise Exception("Data corrupted")

        return buffer, addr
    except socket.timeout as e:
        print(e)
        return "", ""
    
    except ConnectionResetError as e:
        print(e)
        return 0,0


def log_output_data(msg_info, addr):
    print(f"---SENDING MESSAGE\nAddress: {addr}\nContent: {msg_info}\n---")

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
            sock.close()
            print(f'Closed socket - {sock}')
        except socket.timeout as e:
            pass


def HandlePlayers(server_socket_tcp : socket):
    global t_id
    
    prevClient = ''
    prevAddr = ''
    currentClient = []
    threads = []

    while True:
        client, addr = server_socket_tcp.accept()
        print(f'New client accepted - {addr}')
        
        currentClient.append(client)
        check_client_connected(currentClient)

        if len(currentClient) % 2 == 0:  # new match added - 2 players exist
            new_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_server_socket.bind((IP, 0))
            port = str(new_server_socket.getsockname()[1])

            print(f'New socket: {new_server_socket}')

            client.send(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port))
            log_output_data(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port), client)
            prevClient.send(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port))
            log_output_data(protocol.BuildMsgProtocol(protocol.NEW_GAME_PORT, port), prevClient)

            game = Match(new_server_socket)
            t = threading.Thread(target=game.Lunching, args=(t_id,))  # start game
            t.start()

            print(f'New thread - id: {t_id}')
            threads.append(t)
            t_id += 1

            currentClient.remove(prevClient)
            currentClient.remove(client)

            print(f'new game started - player1-{prevAddr}, player2{addr}')

        prevClient = client
        prevAddr = addr

    for t in threads:
        t.join()
        


def main():
    server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket_tcp.bind((IP, PORT))
    server_socket_tcp.listen()

    print('Server running')
    print(f'New socket: {server_socket_tcp}')

    HandlePlayers(server_socket_tcp)
    
    print(f'Closing socket: {server_socket_tcp}')
    server_socket_tcp.close()



if __name__ == '__main__':
    main()