import random
import threading
from abc import abstractmethod
from collections import deque
from enum import Enum
from time import sleep
from typing import List, Optional, Dict

import pygame


class Coordinates:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Size:
    def __init__(self, w: int, h: int):
        self.w = w
        self.h = h

    def to_tuple(self):
        return self.w, self.h


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    def to_tuple(self):
        return self.r, self.g, self.b


class Direction(Enum):
    NORTH = (0, -1)
    WEST = (-1, 0)
    SOUTH = (0, 1)
    EAST = (1, 0)


class Board:
    HEAD_COLOR = Color(255, 0, 255)
    BLOCK_COLOR = Color(255, 0, 0)
    FRUIT_COLOR = Color(192, 192, 192)

    def __init__(self, size: Size, block_size: Size):
        self.surface = pygame.display.set_mode((size.w, size.h + 103))
        self.size = size
        self.block_size = block_size
        self.x_blocks = self.size.w // self.block_size.w
        self.y_blocks = self.size.h // self.block_size.h
        self.init()

    def init(self):
        pygame.init()
        pygame.display.set_caption('pskd\'s snake game')
        self.clear()

    def clear(self):
        self.surface.fill((0, 0, 0))

    def draw_score_card(self, scores: Dict[str, int], game_over: bool):
        start_coords = Coordinates(0, self.size.h + 3 + 5)
        pygame.draw.line(self.surface, (122, 122, 122), (0, self.size.h), self.size.to_tuple(), width=3)
        for i, pid in enumerate(scores.keys()):
            font = pygame.font.Font(pygame.font.get_default_font(), 14)
            text = font.render('{}: {}'.format(pid, scores[pid]), True, (255, 255, 255))
            self.surface.blit(text, (start_coords.x + 5, start_coords.y + i * 18))
        if game_over:
            font = pygame.font.Font(pygame.font.get_default_font(), 14)
            text = font.render('GAME OVER', True, (255, 255, 255))
            self.surface.blit(text, (self.size.w / 2 - text.get_size()[0] / 2, self.size.h + 103 - 18))

    def update(self, blocks: List[Coordinates], fruit: Coordinates, scores: Dict[str, int], game_over: bool):
        self.clear()
        self.draw_score_card(scores, game_over)
        for i, block in enumerate(blocks):
            pygame.draw.rect(
                self.surface,
                self.BLOCK_COLOR.to_tuple(),
                pygame.Rect(
                    block.x * self.block_size.w,
                    block.y * self.block_size.h,
                    self.block_size.w,
                    self.block_size.h
                )
            )
        pygame.draw.rect(
            self.surface,
            self.FRUIT_COLOR.to_tuple(),
            pygame.Rect(
                fruit.x * self.block_size.w,
                fruit.y * self.block_size.h,
                self.block_size.w,
                self.block_size.h
            )
        )
        pygame.display.flip()


class BoardEventListener:
    @abstractmethod
    def on_board_turn(self, direction: Direction):
        pass

    @abstractmethod
    def on_board_quit(self):
        pass


class BoardEventEmitter:
    def __init__(self, listener: BoardEventListener):
        self.listener = listener
        self.thread = None
        self.running = False
        self.muted = False
        self.delay = 0.1

    def start(self, delay: float):
        self.running = True
        self.thread = threading.Thread(target=self.listen)
        self.delay = delay
        self.thread.start()

    def mute(self):
        self.muted = True

    def close(self):
        self.running = False

    def listen(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.listener.on_board_quit()
                if not self.muted and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.listener.on_board_turn(Direction.WEST)
                    elif event.key == pygame.K_RIGHT:
                        self.listener.on_board_turn(Direction.EAST)
                    elif event.key == pygame.K_UP:
                        self.listener.on_board_turn(Direction.NORTH)
                    elif event.key == pygame.K_DOWN:
                        self.listener.on_board_turn(Direction.SOUTH)
            sleep(self.delay)
