import asyncio
import json
import uuid
from enum import Enum
from typing import List

import websockets


class GameStatus(Enum):
    CREATED = 'CREATED'
    IN_PROGRESS = 'IN_PROGRESS'
    FINISHED = 'FINISHED'


class Player:
    def __init__(self, player_id, socket):
        self.player_id = player_id
        self.socket = socket

    async def send(self, message):
        await self.socket.send(json.dumps(message))


class Game:
    MAX_PLAYERS = 2

    def __init__(self):
        self.players: List[Player] = []
        self.status = GameStatus.CREATED

    async def add_player(self, player: Player) -> int:
        assert self.is_waiting()
        self.players.append(player)
        if len(self.players) == self.MAX_PLAYERS:
            self.status = GameStatus.IN_PROGRESS
        return len(self.players) - 1

    def is_waiting(self):
        return self.status == GameStatus.CREATED

    async def start(self):
        while True:
            await self.clock()
            await asyncio.sleep(0.1)

    async def clock(self):
        for player in self.players:
            await player.send({'type': 'move'})

    def get_init_state(self):
        state = {'players': []}
        for i, player in enumerate(self.players):
            state['players'].append({
                'player_id': player.player_id,
                'position': (0, i * 2)
            })
        return state

    async def listen_to_player(self, player: Player):
        message = json.loads(await player.socket.recv())
        if message['type'] == 'turn':
            for _player in self.players:
                await _player.send(message)


games: List[Game] = []


async def find_game(player: Player) -> (Game, int):
    for game in games:
        try:
            player_snake_idx = await game.add_player(player)
            return game, player_snake_idx
        except AssertionError:
            continue
    g = Game()
    player_snake_idx = await g.add_player(player)
    games.append(g)
    return g, player_snake_idx


async def listen(socket, path):
    print('new player connected', socket)
    player = Player(str(uuid.uuid4()), socket)
    game, player_snake_idx = await find_game(player)
    await player.send({
        'type': 'init',
        'player_id': player.player_id,
        'player_snake_idx': player_snake_idx
    })
    if not game.is_waiting():
        for p in game.players:
            await p.send({
                'type': 'start',
                'state': game.get_init_state()
            })
        asyncio.get_event_loop().create_task(game.start())
    while True:
        t = asyncio.get_event_loop().create_task(game.listen_to_player(player))
        await asyncio.ensure_future(t)


start_server = websockets.serve(listen, "localhost", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
