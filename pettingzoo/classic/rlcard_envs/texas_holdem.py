from ast import Dict
import os
from typing import List, Optional

import numpy as np
import pygame

from pettingzoo.utils import wrappers

from .rlcard_base import RLCardBase

# Pixel art from Mariia Khmelnytska (https://www.123rf.com/photo_104453049_stock-vector-pixel-art-playing-cards-standart-deck-vector-set.html)


BG_COLOR = (7, 99, 36)
WHITE = (255, 255, 255)
RED = (217, 30, 61)

CHIPS = {
    0: {"value": 10000, "img": "ChipOrange.png", "number": 0},
    1: {"value": 5000, "img": "ChipPink.png", "number": 0},
    2: {"value": 1000, "img": "ChipYellow.png", "number": 0},
    3: {"value": 100, "img": "ChipBlack.png", "number": 0},
    4: {"value": 50, "img": "ChipBlue.png", "number": 0},
    5: {"value": 25, "img": "ChipGreen.png", "number": 0},
    6: {"value": 10, "img": "ChipLightBlue.png", "number": 0},
    7: {"value": 5, "img": "ChipRed.png", "number": 0},
    8: {"value": 1, "img": "ChipWhite.png", "number": 0},
}


def get_image(path):
    from os import path as os_path

    cwd = os_path.dirname(__file__)
    image = pygame.image.load(cwd + "/" + path)
    return image


def get_font(path, size):
    from os import path as os_path

    cwd = os_path.dirname(__file__)
    font = pygame.font.Font((cwd + "/" + path), size)
    return font


def env(**kwargs):
    env = raw_env(**kwargs)
    env = wrappers.TerminateIllegalWrapper(env, illegal_reward=-1)
    env = wrappers.AssertOutOfBoundsWrapper(env)
    env = wrappers.OrderEnforcingWrapper(env)
    return env


def calculate_offset(hand, j, tile_size):
    return int((len(hand) * (tile_size * 23 / 56)) - ((j) * (tile_size * 23 / 28)))


def calculate_height(screen_height, divisor, multiplier, tile_size, offset):
    return int(multiplier * screen_height / divisor + tile_size * offset)


class raw_env(RLCardBase):

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "texas_holdem_v4",
        "is_parallelizable": False,
        "render_fps": 1,
    }

    def __init__(self, num_players=2):
        super().__init__("limit-holdem", num_players, (72,))

        self.screen_height = 500
        self.screen_width = int(
            self.screen_height * (1 / 20)
            + np.ceil(len(self.possible_agents) / 2) * (self.screen_height * 1 / 2)
        )

        self.tile_size = self.screen_height * 2 / 10

        pygame.init()
        # This used to have 'if mode == human' logic, could break
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

    def calculate_width(self, i):
        return int(
            (
                self.screen_width
                / (np.ceil(len(self.possible_agents) / 2) + 1)
                * np.ceil((i + 1) / 2)
            )
            + self.tile_size * 31 / 616
        )

    def render(
        self,
        mode="human",
        most_recent_move: Optional[Dict] = None,
        win_message: Optional[str] = None,
        render_opponent_cards: bool = True,
        player_names: Optional[List[str]] = None,
        screen: Optional[pygame.Surface] = None,
    ):
        # Hack to allow injection of external screen
        if screen is not None:
            self.screen = screen
            self.screen_height = screen.get_height()
            self.screen_width = screen.get_width()

        if mode == "human":
            pygame.event.get()

        # Setup dimensions for card size and setup for colors

        self.screen.fill(BG_COLOR)

        # Load and blit all images for each card in each player's hand
        for i, player in enumerate(self.possible_agents[::-1]):
            state = self.env.game.get_state(self._name_to_int(player))
            for j, card in enumerate(state["hand"]):
                if not render_opponent_cards and player == "player_1":
                    card_img = get_image(os.path.join("img", "Card.png"))
                else:
                    card_img = get_image(os.path.join("img", card + ".png"))
                card_img = pygame.transform.scale(
                    card_img, (int(self.tile_size * (142 / 197)), int(self.tile_size))
                )
                # Players with even id go above public cards
                if i % 2 == 0:
                    self.screen.blit(
                        card_img,
                        (
                            (
                                self.calculate_width(i=i)
                                - calculate_offset(state["hand"], j, self.tile_size)
                            ),
                            calculate_height(
                                self.screen_height, 4, 1, self.tile_size, -1
                            ),
                        ),
                    )
                # Players with odd id go below public cards
                else:
                    self.screen.blit(
                        card_img,
                        (
                            (
                                self.calculate_width(i=i)
                                - calculate_offset(state["hand"], j, self.tile_size)
                            ),
                            calculate_height(
                                self.screen_height, 4, 3, self.tile_size, 0
                            ),
                        ),
                    )

            # Load and blit text for player name
            font = pygame.font.SysFont("arial", 22)

            if player_names is None:
                name = "Your player" if player == "player_0" else "Opponent"
            else:
                name = player_names[0] if player == "player_0" else player_names[1]

            move = most_recent_move[player]
            move_map = {
                None: "",
                0: "Call",
                1: "Raise",
                2: "Fold",
                3: "Check",
            }

            text = font.render(f"{name}: move = {move_map[move]}", True, WHITE)
            textRect = text.get_rect()
            if i % 2 == 0:
                textRect.center = (
                    (
                        self.screen_width
                        / (np.ceil(len(self.possible_agents) / 2) + 1)
                        * np.ceil((i + 1) / 2)
                    ),
                    calculate_height(
                        self.screen_height, 4, 1, self.tile_size, -(22 / 20)
                    ),
                )
            else:
                textRect.center = (
                    (
                        self.screen_width
                        / (np.ceil(len(self.possible_agents) / 2) + 1)
                        * np.ceil((i + 1) / 2)
                    ),
                    calculate_height(
                        self.screen_height, 4, 3, self.tile_size, (23 / 20)
                    ),
                )
            self.screen.blit(text, textRect)

            x_pos, y_pos = self.get_player_chip_position(i)

            self.draw_chips(state["my_chips"], x_pos, y_pos)

        # Load and blit public cards
        for i, card in enumerate(state["public_cards"]):
            card_img = get_image(os.path.join("img", card + ".png"))
            card_img = pygame.transform.scale(
                card_img, (int(self.tile_size * (142 / 197)), int(self.tile_size))
            )
            if len(state["public_cards"]) <= 3:
                self.screen.blit(
                    card_img,
                    (
                        (
                            (
                                ((self.screen_width / 2) + (self.tile_size * 31 / 616))
                                - calculate_offset(
                                    state["public_cards"], i, self.tile_size
                                )
                            ),
                            calculate_height(
                                self.screen_height, 2, 1, self.tile_size, -(1 / 2)
                            ),
                        )
                    ),
                )
            else:
                if i <= 2:
                    self.screen.blit(
                        card_img,
                        (
                            (
                                (
                                    (
                                        (self.screen_width / 2)
                                        + (self.tile_size * 31 / 616)
                                    )
                                    - calculate_offset(
                                        state["public_cards"][:3], i, self.tile_size
                                    )
                                ),
                                calculate_height(
                                    self.screen_height, 2, 1, self.tile_size, -21 / 20
                                ),
                            )
                        ),
                    )
                else:
                    self.screen.blit(
                        card_img,
                        (
                            (
                                (
                                    (
                                        (self.screen_width / 2)
                                        + (self.tile_size * 31 / 616)
                                    )
                                    - calculate_offset(
                                        state["public_cards"][3:], i - 3, self.tile_size
                                    )
                                ),
                                calculate_height(
                                    self.screen_height, 2, 1, self.tile_size, 1 / 20
                                ),
                            )
                        ),
                    )

        if win_message is not None:
            # Load and blit text for player name
            font = pygame.font.SysFont("arial", 22)
            text = font.render(win_message, True, RED)
            textRect = text.get_rect()
            textRect.center = (self.screen_width // 2, int(self.screen_height * 0.45))
            pygame.draw.rect(self.screen, WHITE, textRect)
            self.screen.blit(text, textRect)

            text = font.render("Click to continue", True, RED)
            textRect = text.get_rect()
            textRect.center = (
                self.screen_width // 2,
                int(self.screen_height * 0.55),
            )
            pygame.draw.rect(self.screen, WHITE, textRect)
            self.screen.blit(text, textRect)

        if mode == "human" and screen is None:
            pygame.display.update()

        observation = np.array(pygame.surfarray.pixels3d(self.screen))

        return (
            np.transpose(observation, axes=(1, 0, 2)) if mode == "rgb_array" else None
        )

    def get_player_chip_position(self, player_idx):
        if player_idx % 2 == 0:
            offset = -0.5
            multiplier = 1
        else:
            offset = 0.5
            multiplier = 3

        x_pos = self.calculate_width(player_idx) + self.tile_size * (8 / 10)
        y_pos = calculate_height(
            self.screen_height, 4, multiplier, self.tile_size, offset
        )
        return (x_pos, y_pos)

    def draw_chips(self, n_chips, x_pos, y_pos):

        font = pygame.font.SysFont("arial", 20)
        text = font.render(str(n_chips), True, WHITE)
        textRect = text.get_rect()

        # Calculate number of each chip
        height = 0

        # Draw the chips
        for key in CHIPS:
            num = n_chips / CHIPS[key]["value"]
            CHIPS[key]["number"] = int(num)
            n_chips %= CHIPS[key]["value"]

            chip_img = get_image(os.path.join("img", CHIPS[key]["img"]))
            chip_img = pygame.transform.scale(
                chip_img, (int(self.tile_size / 2), int(self.tile_size * 16 / 45))
            )

            for j in range(int(CHIPS[key]["number"])):
                height_offset = (j + height) * self.tile_size / 15
                self.screen.blit(
                    chip_img,
                    (x_pos, y_pos - height_offset),
                )
            height += CHIPS[key]["number"]

        # Blit number of chips
        textRect.center = (
            x_pos + self.tile_size // 4,
            y_pos - ((height + 1) * self.tile_size / 15),
        )
        self.screen.blit(text, textRect)

