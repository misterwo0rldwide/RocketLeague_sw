PLAYER_CONNECTING = 'PCN'
PLAYER_INFO = 'PNF'
SECOND_PLAYER_INFO = 'SNF'
BALL_INFO = 'BIO'
PLAYER_STARTING_POS = 'PSP'
SERVER_GOT_ADDRESS = 'SGA'

STARTING_GAME = 'STG'

MSG_CORRUPTED = 'MSC'

GAME_STOPPED_ENTHERNET = 'GSE'
GAME_ENDED = 'GEN'

NEW_GAME_PORT = 'NGP'

MSG_NOT_RECIVED = 'MNR'
MSG_RECIVED = 'MSR'
JOINING_GAME = 'JGA'

PLAYER_STILL_CONNECTED = 'PSC'

BUFFER_LENGTH_SIZE = 4
MAX_MESSAGE_LENGTH = 1024

# length of message~ command ~ info
def BuildMsgProtocol(command, data):
    if type(command) != bytes:
        command = command.encode()
    if (not data is None) and type(data) != bytes:
        data = data.encode()
    elif data is None:
        data = b''
    
    prtocolMSG = command + b'~' + data
    prtocolMSG = str(len(prtocolMSG)).zfill(4).encode() + prtocolMSG
    return prtocolMSG