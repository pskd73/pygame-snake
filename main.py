import random
from collections import deque
from enum import Enum
from time import sleep
from typing import List, Optional

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


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    def to_tuple(self):
        return self.r, self.g, self.b


class Direction(Enum):
    NORTH = 'NORTH'
    WEST = 'WEST'
    SOUTH = 'SOUTH'
    EAST = 'EAST'


class Turn:
    def __init__(self, coordinates: Coordinates, to_direction: Direction):
        self.coordinates = coordinates
        self.to_direction = to_direction


class BoardUpdateResponse:
    def __init__(
            self,
            game_over: bool
    ):
        self.game_over = game_over


class SnakeBlock:
    def __init__(self, coordinates: Coordinates):
        self.coordinates = coordinates

    def draw(self, surface, block_size: Size, color: Color):
        pygame.draw.rect(
            surface,
            color.to_tuple(),
            pygame.Rect(
                self.coordinates.x * block_size.w,
                self.coordinates.y * block_size.h,
                block_size.w,
                block_size.h
            )
        )


class Fruit:
    def __init__(self, coordinates: Coordinates, size: Size, color: Color):
        self.coordinates = coordinates
        self.size = size
        self.color = color

    def draw(self, surface, block_size: Size):
        pygame.draw.rect(
            surface,
            self.color.to_tuple(),
            pygame.Rect(
                self.coordinates.x * block_size.w,
                self.coordinates.y * block_size.h,
                self.size.w,
                self.size.h
            )
        )

    @classmethod
    def get_random_coordinates(cls, board_size: Size, block_size: Size) -> Coordinates:
        x_blocks = board_size.w // block_size.w
        y_blocks = board_size.h // block_size.h
        rand_x, rand_y = random.randint(0, x_blocks - 1), random.randint(0, y_blocks - 1)
        return Coordinates(rand_x, rand_y)


class Board:
    HEAD_COLOR = Color(255, 0, 255)
    BLOCK_COLOR = Color(255, 0, 0)
    FRUIT_COLOR = Color(192, 192, 192)

    def __init__(self, surface, size: Size, block_size: Size):
        self.surface = surface
        self.size = size
        self.block_size = block_size
        self.snake_blocks = deque([
            SnakeBlock(Coordinates(2, 0)),
            SnakeBlock(Coordinates(1, 0)),
            SnakeBlock(Coordinates(0, 0))
        ])
        self.speed = 10  # scenes per second
        self.should_add_block = False
        self.fruit = self.new_fruit()
        self.direction = Direction.EAST
        self.init()

    def init(self):
        self.clear()

    def add_snake_block(self, snake_block: SnakeBlock):
        self.snake_blocks.append(snake_block)

    def clear(self):
        self.surface.fill((0, 0, 0))

    def new_fruit(self) -> Fruit:
        coords = Fruit.get_random_coordinates(self.size, self.block_size)
        for block in self.snake_blocks:
            if block.coordinates == coords:
                return self.new_fruit()
        return Fruit(coords, self.block_size, self.FRUIT_COLOR)

    @staticmethod
    def is_opposite_direction(dir_1: Direction, dir_2: Direction) -> bool:
        opposite_dirs = [
            (Direction.EAST.value, Direction.WEST.value),
            (Direction.NORTH.value, Direction.SOUTH.value)
        ]
        if tuple(sorted([dir_1.value, dir_2.value])) in opposite_dirs:
            return True
        return False

    def turn(self, to_direction: Direction):
        if self.direction == to_direction:
            return
        if self.is_opposite_direction(self.direction, to_direction):
            return
        self.direction = to_direction

    def get_delay_secs(self):
        return 1 / self.speed

    def is_valid_block(self, snake_block: SnakeBlock):
        if snake_block.coordinates.x < 0:
            return False
        if snake_block.coordinates.y < 0:
            return False
        if snake_block.coordinates.x >= self.size.w:
            return False
        if snake_block.coordinates.y >= self.size.h:
            return False
        if len([b for b in self.snake_blocks if b.coordinates == snake_block.coordinates]) > 1:
            return False
        return True

    def get_next_head(self) -> SnakeBlock:
        head = self.snake_blocks[0]
        if self.direction == Direction.WEST:
            change = (-1, 0)
        elif self.direction == Direction.SOUTH:
            change = (0, 1)
        elif self.direction == Direction.EAST:
            change = (1, 0)
        else:
            change = (0, -1)
        return SnakeBlock(Coordinates(head.coordinates.x + change[0], head.coordinates.y + change[1]))

    def update(self) -> BoardUpdateResponse:
        self.clear()
        self.snake_blocks.appendleft(self.get_next_head())
        if not self.is_valid_block(self.snake_blocks[0]):
            return BoardUpdateResponse(True)
        if self.snake_blocks[0].coordinates == self.fruit.coordinates:
            self.fruit = self.new_fruit()
            self.speed += 2
        else:
            self.snake_blocks.pop()
        for i, snake_block in enumerate(self.snake_blocks):
            snake_block.draw(self.surface, self.block_size, self.HEAD_COLOR if i == 0 else self.BLOCK_COLOR)
        self.fruit.draw(self.surface, self.block_size)
        pygame.display.flip()
        sleep(self.get_delay_secs())
        return BoardUpdateResponse(False)


BOARD_SIZE = Size(400, 400)
BLOCK_SIZE = Size(20, 20)
pygame.init()
surface = pygame.display.set_mode((400, 400))
board = Board(surface, BOARD_SIZE, BLOCK_SIZE)
running = True
pause = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                board.turn(Direction.WEST)
            elif event.key == pygame.K_RIGHT:
                board.turn(Direction.EAST)
            elif event.key == pygame.K_UP:
                board.turn(Direction.NORTH)
            elif event.key == pygame.K_DOWN:
                board.turn(Direction.SOUTH)
            elif event.key == pygame.K_0:
                board.should_add_block = True
            elif event.key == pygame.K_SPACE:
                pause = not pause
    if not pause:
        res = board.update()
        if res.game_over:
            exit(1)
