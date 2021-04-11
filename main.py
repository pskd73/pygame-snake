import random
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


class Snake:
    def __init__(self, blocks: List[SnakeBlock]):
        self.blocks = deque(blocks)
        self.direction = Direction.EAST

    def turn(self, to_direction: Direction):
        if self.direction == to_direction:
            return
        if self.direction.value[0] + to_direction.value[0] == 0 or self.direction.value[1] + to_direction.value[1] == 0:
            return
        self.direction = to_direction

    def get_next_head(self) -> SnakeBlock:
        head = self.blocks[0]
        return SnakeBlock(
            Coordinates(
                head.coordinates.x + self.direction.value[0],
                head.coordinates.y + self.direction.value[1]
            )
        )

    def are_coordinates_inside(self, coordinates: Coordinates):
        for block in self.blocks:
            if block.coordinates == coordinates:
                return True
        return False


class Board:
    HEAD_COLOR = Color(255, 0, 255)
    BLOCK_COLOR = Color(255, 0, 0)
    FRUIT_COLOR = Color(192, 192, 192)

    BOARD_SIZE = Size(400, 400)
    BLOCK_SIZE = Size(8, 8)

    def __init__(self, size: Size=BOARD_SIZE, block_size: Size=BLOCK_SIZE):
        self.surface = pygame.display.set_mode(size.to_tuple())
        self.size = size
        self.block_size = block_size
        self.snakes: Dict[str, Snake] = {}
        self.speed = 10  # scenes per second
        self.should_add_block = False
        self.x_blocks = self.size.w // self.block_size.w
        self.y_blocks = self.size.h // self.block_size.h
        self.fruit = self.new_fruit()
        self.init()

    def init(self):
        pygame.init()
        self.clear()

    def clear(self):
        self.surface.fill((0, 0, 0))

    def add_snake(self, snake_id: str, head_coordinates: Coordinates):
        self.snakes[snake_id] = Snake([
            SnakeBlock(head_coordinates)
        ])

    def new_fruit(self) -> Fruit:
        coords = Coordinates(random.randint(0, self.x_blocks - 1), random.randint(0, self.y_blocks - 1))
        for snake in self.snakes.values():
            if snake.are_coordinates_inside(coords):
                return self.new_fruit()
        return Fruit(coords, self.block_size, self.FRUIT_COLOR)

    def get_delay_secs(self):
        return 1 / self.speed

    def is_valid_block(self, snake_block: SnakeBlock):
        if snake_block.coordinates.x < 0:
            return False
        if snake_block.coordinates.y < 0:
            return False
        if snake_block.coordinates.x >= self.x_blocks:
            return False
        if snake_block.coordinates.y >= self.y_blocks:
            return False
        for snake in self.snakes.values():
            if snake.are_coordinates_inside(snake_block.coordinates):
                return False
        return True

    def turn(self, snake_id: str, direction: Direction):
        self.snakes[snake_id].turn(direction)

    def move(self):
        for snake in self.snakes.values():
            next_head = snake.get_next_head()
            if not self.is_valid_block(next_head):
                return BoardUpdateResponse(True)
            snake.blocks.appendleft(next_head)
            if snake.blocks[0].coordinates == self.fruit.coordinates:
                self.fruit = self.new_fruit()
                # self.speed += 2
            else:
                snake.blocks.pop()

    def update(self) -> BoardUpdateResponse:
        self.clear()
        for snake in self.snakes.values():
            for i, block in enumerate(snake.blocks):
                block.draw(self.surface, self.block_size, self.HEAD_COLOR if i == 0 else self.BLOCK_COLOR)
        self.fruit.draw(self.surface, self.block_size)
        pygame.display.flip()
        sleep(self.get_delay_secs())
        return BoardUpdateResponse(False)


if __name__ == '__main__':
    board = Board()
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
                if event.key == pygame.K_a:
                    board.turn2(Direction.WEST)
                elif event.key == pygame.K_d:
                    board.turn2(Direction.EAST)
                elif event.key == pygame.K_w:
                    board.turn2(Direction.NORTH)
                elif event.key == pygame.K_s:
                    board.turn2(Direction.SOUTH)
                elif event.key == pygame.K_SPACE:
                    pause = not pause
        if not pause:
            res = board.update()
            if res.game_over:
                exit(1)
