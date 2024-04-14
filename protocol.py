PLAYER_CONNECTING = 'PCN'
PLAYER_INFO = 'PNF'

STARTING_GAME = 'STG'


# length of message~ command ~ info
def BuildMsgProtocol(command, data):
    if type(command) != bytes:
        command = command.encode()
    if not data is None and type(data) != bytes:
        data = data.encode()
    else:
        data = b''
    
    prtocolMSG = command + b'~' + data
    prtocolMSG = str(len(prtocolMSG)).zfill(4).encode() + prtocolMSG
    return prtocolMSG