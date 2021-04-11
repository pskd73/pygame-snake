import socket
import uuid

from game import Board, BoardEventListener, BoardEventEmitter, Coordinates, Size
from game import Direction
from socket_thread import SocketThread


class ClientGame(SocketThread, BoardEventListener):
    def __init__(self, s, sid):
        super(ClientGame, self).__init__(s, sid)
        self.my_id = None
        self.board: Board = None
        self.board_event_emitter = BoardEventEmitter(self)

    def on_init(self, message):
        self.my_id = message['id']

    def on_start(self, message):
        self.board = Board(
            Size(message['board_size']['w'], message['board_size']['h']),
            Size(message['block_size']['w'], message['block_size']['h'])
        )
        self.board_event_emitter.start()
        print('initiated board')

    def on_state(self, message):
        blocks = []
        for snake in message['snakes']:
            for block in snake['blocks']:
                blocks.append(Coordinates(block['x'], block['y']))
        self.board.update(blocks, Coordinates(message['fruit']['x'], message['fruit']['y']))

    def on_board_turn(self, direction: Direction):
        self.send({'type': 'turn', 'direction': direction.name})

    def on_board_quit(self):
        self.close()


s = socket.socket()
s.connect(('127.0.0.1', 8082))
t = ClientGame(s, str(uuid.uuid4()))
t.start()


