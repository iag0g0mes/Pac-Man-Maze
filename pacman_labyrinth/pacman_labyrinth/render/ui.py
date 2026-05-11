from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import pygame


@dataclass(slots=True)
class Button:
    rect: pygame.Rect
    text: str
    fill: tuple[int, int, int]
    hover_fill: tuple[int, int, int]
    text_color: tuple[int, int, int] = (245, 245, 245)
    radius: int = 14

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, hovered: bool) -> None:
        color = self.hover_fill if hovered else self.fill
        pygame.draw.rect(surface, color, self.rect, border_radius=self.radius)
        label = font.render(self.text, True, self.text_color)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def contains(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


@dataclass(slots=True)
class Dropdown:
    rect: pygame.Rect
    options: Sequence[str]
    selected_index: int = 0
    expanded: bool = False
    fill: tuple[int, int, int] = (52, 74, 116)
    hover_fill: tuple[int, int, int] = (74, 96, 144)
    option_fill: tuple[int, int, int] = (24, 32, 58)
    option_hover_fill: tuple[int, int, int] = (46, 60, 102)
    selected_fill: tuple[int, int, int] = (84, 74, 126)
    text_color: tuple[int, int, int] = (245, 245, 245)
    radius: int = 14
    option_gap: int = 6
    _option_rects: list[pygame.Rect] = field(default_factory=list)

    @property
    def selected_text(self) -> str:
        return self.options[self.selected_index]

    def toggle(self) -> None:
        self.expanded = not self.expanded

    def close(self) -> None:
        self.expanded = False

    def option_rects(self) -> list[pygame.Rect]:
        if not self._option_rects:
            self._option_rects = [
                pygame.Rect(
                    self.rect.x +  365,
                    self.rect.bottom - 55 + self.option_gap + idx * (self.rect.height + self.option_gap),
                    self.rect.width,
                    self.rect.height,
                )
                for idx in range(len(self.options))
            ]
        return self._option_rects

    def contains_header(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def hovered_option_index(self, pos: tuple[int, int]) -> int | None:
        if not self.expanded:
            return None
        for idx, rect in enumerate(self.option_rects()):
            if rect.collidepoint(pos):
                return idx
        return None

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        hovered_header: bool,
        hovered_option: int | None,
    ) -> None:
        header_color = self.hover_fill if hovered_header else self.fill
        pygame.draw.rect(surface, header_color, self.rect, border_radius=self.radius)
        label = font.render(f"Algorithm: {self.selected_text}", True, self.text_color)
        label_rect = label.get_rect(midleft=(self.rect.x + 16, self.rect.centery))
        surface.blit(label, label_rect)

        arrow = "◂" if self.expanded else "▸"
        arrow_label = font.render(arrow, True, self.text_color)
        arrow_rect = arrow_label.get_rect(midright=(self.rect.right - 16, self.rect.centery))
        surface.blit(arrow_label, arrow_rect)

        if not self.expanded:
            return

        for idx, option in enumerate(self.options):
            rect = self.option_rects()[idx]
            if idx == self.selected_index:
                fill = self.selected_fill
            elif hovered_option == idx:
                fill = self.option_hover_fill
            else:
                fill = self.option_fill
            pygame.draw.rect(surface, fill, rect, border_radius=self.radius)
            option_label = font.render(option, True, self.text_color)
            option_rect = option_label.get_rect(midleft=(rect.x + 16, rect.centery))
            surface.blit(option_label, option_rect)



def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    x: int,
    y: int,
    center: bool = False,
) -> pygame.Rect:
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)
    return rect
