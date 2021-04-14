import random
import socket
import uuid
from collections import deque
from enum import Enum
from time import sleep
from typing import List, Dict

from game import Coordinates, Direction, Size
from socket_thread import SocketThread

s = socket.socket()
s.bind(('', 8082))
s.listen(5)


class GameState(Enum):
    WAITING = 'WAITING'
    IN_PROGRESS = 'IN_PROGRESS'
    GAME_OVER = 'GAME_OVER'


class Snake:
    def __init__(self, blocks: List[Coordinates], st: SocketThread):
        self.blocks = deque(blocks)
        self.direction = Direction.EAST
        self.st = st

    def turn(self, to_direction: Direction):
        if self.direction == to_direction:
            return
        if self.direction.value[0] + to_direction.value[0] == 0 or self.direction.value[1] + to_direction.value[1] == 0:
            return
        self.direction = to_direction

    def get_next_head(self) -> Coordinates:
        head = self.blocks[0]
        return Coordinates(
            head.x + self.direction.value[0],
            head.y + self.direction.value[1]
        )

    def are_coordinates_inside(self, coordinates: Coordinates):
        for block in self.blocks:
            if block == coordinates:
                return True
        return False

    def move(self, fruit, x_blocks: int, y_blocks: int):
        next_head = self.get_next_head()
        if next_head.x < 0 or \
            next_head.y < 0 or \
            next_head.y > y_blocks or \
            next_head.x > x_blocks or \
            self.are_coordinates_inside(next_head):
            raise ValueError('Invalid move')
        self.blocks.appendleft(next_head)
        if self.blocks[0] == fruit:
            return True
        else:
            self.blocks.pop()

    def get_state(self) -> dict:
        return {
            'blocks': [b.__dict__ for b in self.blocks],
            'direction': self.direction.name
        }


class Game:
    MAX_PLAYERS = 2

    def __init__(self):
        self.snakes: Dict[str, Snake] = {}
        self.fruit: Coordinates = None
        self.size = Size(400, 400)
        self.block_size = Size(8, 8)
        self.x_blocks = self.size.w // self.block_size.w
        self.y_blocks = self.size.h // self.block_size.h
        self.state: GameState = GameState.WAITING

    def new_fruit(self) -> Coordinates:
        coords = Coordinates(random.randint(0, self.x_blocks - 1), random.randint(0, self.y_blocks - 1))
        for snake in self.snakes.values():
            if snake.are_coordinates_inside(coords):
                return self.new_fruit()
        return coords

    def is_vacant(self):
        return len(self.snakes) < self.MAX_PLAYERS

    def add_player(self, st: SocketThread):
        assert self.is_vacant()
        self.snakes[st.sid] = Snake([Coordinates(0, 0)], st)
        st.send({'type': 'init', 'id': st.sid})
        if not self.is_vacant():
            for snake in self.snakes.values():
                self.state = GameState.IN_PROGRESS
                snake.st.send({
                    'type': 'start',
                    'players': [s.st.sid for s in self.snakes.values()],
                    'board_size': self.size.__dict__,
                    'block_size': self.block_size.__dict__
                })
            self.start()

    def get_state(self) -> dict:
        return {
            'snakes': [snake.get_state() for snake in self.snakes.values()],
            'fruit': self.fruit.__dict__,
            'state': self.state.value
        }

    def start(self):
        self.fruit = self.new_fruit()
        while self.state == GameState.IN_PROGRESS:
            for snake in self.snakes.values():
                try:
                    eaten = snake.move(self.fruit, self.x_blocks, self.y_blocks)
                except ValueError as e:
                    self.state = GameState.GAME_OVER
                    eaten = False
                if eaten:
                    self.fruit = self.new_fruit()
            for snake in self.snakes.values():
                try:
                    snake.st.send({
                        'type': 'state',
                        **self.get_state()
                    })
                except BrokenPipeError:
                    self.state = GameState.GAME_OVER
            sleep(0.2)

    def turn(self, player_id: str, direction):
        self.snakes[player_id].turn(Direction[direction])


class Player(SocketThread):
    def __init__(self, s, sid, game: Game):
        super(Player, self).__init__(s, sid)
        self.game = game

    def on_turn(self, message):
        self.game.turn(self.sid, message['direction'])


games: List[Game] = []


def find_game() -> Game:
    for game in games:
        if game.is_vacant():
            return game
    g = Game()
    games.append(g)
    return g


while True:
    print('listening for connections..')
    c, address = s.accept()
    print('new connection', address)
    game = find_game()
    player = Player(c, str(uuid.uuid4()), game)
    player.start()
    game.add_player(player)
