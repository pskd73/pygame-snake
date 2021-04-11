import asyncio
import json

import pygame
import websockets

from main import Size, Board, Direction, Coordinates

BOARD_SIZE = Size(400, 400)
BLOCK_SIZE = Size(10, 10)


class Player:
    def __init__(self, socket, loop):
        self.player_id = None
        self.socket = socket
        self.loop = loop
        self.snake_idx = None
        self.board: Board = None

    async def listen_to_server(self):
        message = json.loads(await self.socket.recv())
        print('message', message)
        if message['type'] == 'init':
            self.player_id = message['player_id']
            self.snake_idx = message['player_snake_idx']
        elif message['type'] == 'start':
            self.board = Board()
            for player in message['state']['players']:
                self.board.add_snake(player['player_id'], Coordinates(player['position'][0], player['position'][1]))
            self.loop.create_task(self.listen_to_board())
        elif message['type'] == 'turn':
            self.board.turn(message['player_id'], Direction[message['direction']])
        elif message['type'] == 'move':
            self.board.move()
            self.board.update()

    async def send(self, message):
        await self.socket.send(json.dumps(message))

    async def listen_to_board(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.loop.stop()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        await self.send({'type': 'turn', 'direction': Direction.WEST.name, 'player_id': self.player_id})
                    elif event.key == pygame.K_RIGHT:
                        await self.send({'type': 'turn', 'direction': Direction.EAST.name, 'player_id': self.player_id})
                    elif event.key == pygame.K_UP:
                        await self.send({'type': 'turn', 'direction': Direction.NORTH.name, 'player_id': self.player_id})
                    elif event.key == pygame.K_DOWN:
                        await self.send({'type': 'turn', 'direction': Direction.SOUTH.name, 'player_id': self.player_id})
            await asyncio.sleep(0.001)


async def main(loop):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        p = Player(websocket, loop)
        while True:
            await p.listen_to_server()


loop = asyncio.get_event_loop()
asyncio.get_event_loop().run_until_complete(main(loop))