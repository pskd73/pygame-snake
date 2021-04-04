import random
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
    def __init__(
            self,
            coordinates: Coordinates,
            size: Size,
            color: Color,
            direction: Direction
    ):
        self.coordinates = coordinates
        self.size = size
        self.color = color
        self.direction = direction
        self.border_width = 2
        self.border_color = Color(255, 255, 0)

    def move(self):
        if self.direction == Direction.WEST:
            self.coordinates = Coordinates(self.coordinates.x - self.size.w, self.coordinates.y)
        elif self.direction == Direction.SOUTH:
            self.coordinates = Coordinates(self.coordinates.x, self.coordinates.y + self.size.h)
        elif self.direction == Direction.EAST:
            self.coordinates = Coordinates(self.coordinates.x + self.size.w, self.coordinates.y)
        else:
            self.coordinates = Coordinates(self.coordinates.x, self.coordinates.y - self.size.h)

    def draw(self, surface):
        pygame.draw.rect(
            surface,
            self.color.to_tuple(),
            pygame.Rect(
                self.coordinates.x + self.border_width,
                self.coordinates.y + self.border_width,
                self.size.w - self.border_width,
                self.size.h - self.border_width
            ),
            0
        )
        pygame.draw.rect(
            surface,
            self.border_color.to_tuple(),
            pygame.Rect(
                self.coordinates.x,
                self.coordinates.y,
                self.size.w,
                self.size.h
            ),
            self.border_width
        )


class Fruit:
    def __init__(self, coordinates: Coordinates, size: Size, color: Color):
        self.coordinates = coordinates
        self.size = size
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(
            surface,
            self.color.to_tuple(),
            pygame.Rect(
                self.coordinates.x,
                self.coordinates.y,
                self.size.w,
                self.size.h
            )
        )

    @classmethod
    def get_random_coordinates(cls, board_size: Size, block_size: Size) -> Coordinates:
        x_blocks = board_size.w // block_size.w
        y_blocks = board_size.h // block_size.h
        rand_x, rand_y = random.randint(0, x_blocks - 1), random.randint(0, y_blocks - 1)
        return Coordinates(rand_x * block_size.w, rand_y * block_size.h)


class Board:
    def __init__(self, surface, size: Size, block_size: Size):
        self.surface = surface
        self.size = size
        self.block_size = block_size
        self.snake_blocks: List[SnakeBlock] = [
            SnakeBlock(
                Coordinates(self.block_size.w * 2, 0),
                self.block_size,
                Color(255, 0, 255),
                Direction.EAST
            ),
            SnakeBlock(
                Coordinates(self.block_size.w, 0),
                self.block_size,
                Color(255, 0, 0),
                Direction.EAST
            ),
            SnakeBlock(
                Coordinates(0, 0),
                self.block_size,
                Color(255, 0, 0),
                Direction.EAST
            )
        ]
        self.speed = 8  # scenes per second
        self.turns = set()
        self.should_add_block = False
        self.fruit = self.new_fruit()
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
        return Fruit(coords, self.block_size, Color(192, 192, 192))

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
        head_block = self.snake_blocks[0]
        if head_block.direction == to_direction:
            return
        if self.is_opposite_direction(head_block.direction, to_direction):
            return
        self.turns.add(Turn(head_block.coordinates, to_direction))

    def get_delay_secs(self):
        return 1 / self.speed

    def apply_turns(self, idx: int, snake_block: SnakeBlock):
        # TODO: this logic breaks if there are two turns at a same coordinate
        finished_turn = None
        for turn in self.turns:
            if snake_block.coordinates == turn.coordinates:
                snake_block.direction = turn.to_direction
                if idx == len(self.snake_blocks) - 1:
                    finished_turn = turn
        if finished_turn:
            self.turns.remove(finished_turn)

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

    def try_get_new_block(self, idx: int, snake_block: SnakeBlock) -> Optional[SnakeBlock]:
        if idx == len(self.snake_blocks) - 1 and self.should_add_block:
            self.should_add_block = False
            return SnakeBlock(
                snake_block.coordinates,
                snake_block.size,
                snake_block.color,
                snake_block.direction
            )

    def update(self) -> BoardUpdateResponse:
        self.clear()
        new_block = None
        for i, snake_block in enumerate(self.snake_blocks):
            self.apply_turns(i, snake_block)
            new_block = self.try_get_new_block(i, snake_block)
            snake_block.move()
            if not self.is_valid_block(snake_block):
                return BoardUpdateResponse(True)
            if snake_block.coordinates == self.fruit.coordinates:
                self.should_add_block = True
                self.fruit = self.new_fruit()
                self.speed += 2
        if new_block is not None:
            self.snake_blocks.append(new_block)
        for snake_block in self.snake_blocks:
            snake_block.draw(self.surface)
        self.fruit.draw(self.surface)
        pygame.display.flip()
        sleep(self.get_delay_secs())
        return BoardUpdateResponse(False)


BOARD_SIZE = Size(800, 800)
BLOCK_SIZE = Size(20, 20)
pygame.init()
surface = pygame.display.set_mode((800, 800))
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
