from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

try:
    from PIL import Image, ImageSequence
except Exception:  # pragma: no cover
    Image = None
    ImageSequence = None


@dataclass(slots=True)
class Animation:
    frames: list[pygame.Surface]
    frame_time: float = 0.10

    def frame_at(self, elapsed: float) -> pygame.Surface:
        if not self.frames:
            raise ValueError("Animation without frames.")
        idx = int(elapsed / self.frame_time) % len(self.frames)
        return self.frames[idx]


class AssetManager:
    """
    Gerencia sprites e animações.
    """

    def __init__(self, asset_dir: str | Path):
        self.asset_dir = Path(asset_dir)
        self._surface_cache: dict[tuple[str, tuple[int, int] | None, bool], pygame.Surface] = {}
        self._animation_cache: dict[tuple[str, tuple[int, int] | None], Animation] = {}
        self._size_cache: dict[str, tuple[int, int]] = {}

    def path(self, *parts: str) -> Path:
        return self.asset_dir.joinpath(*parts)

    def exists(self, *parts: str) -> bool:
        return self.path(*parts).exists()

    def source_size(self, name: str) -> tuple[int, int]:
        """Retorna o tamanho original do asset."""
        if name in self._size_cache:
            return self._size_cache[name]
        path = self.path(name)
        if not path.exists():
            self._size_cache[name] = (64, 64)
            return (64, 64)
        if Image is not None:
            try:
                with Image.open(path) as im:
                    size = tuple(im.size)
                    self._size_cache[name] = size
                    return size
            except Exception:
                pass
        surf = pygame.image.load(str(path))
        size = surf.get_size()
        self._size_cache[name] = size
        return size

    def load_surface(
        self,
        name: str,
        size: tuple[int, int] | None = None,
        alpha: bool = True,
        trim: bool = False,
    ) -> pygame.Surface:
        """
        Carrega uma imagem estática.

        Parâmetros:
            trim: quando True, recorta margens transparentes usando Pillow.
        """
        key = (name, size, trim)
        if key in self._surface_cache:
            return self._surface_cache[key]

        path = self.path(name)
        if not path.exists():
            surf = self._placeholder(size or (64, 64), name)
            self._surface_cache[key] = surf
            return surf

        image: pygame.Surface | None = None
        if trim and Image is not None:
            try:
                with Image.open(path) as im:
                    rgba = im.convert("RGBA")
                    bbox = self._alpha_bbox(rgba, threshold=12)
                    if bbox is not None:
                        rgba = rgba.crop(bbox)
                    data = rgba.tobytes()
                    image = pygame.image.fromstring(data, rgba.size, rgba.mode).convert_alpha()
            except Exception:
                image = None

        if image is None:
            image = pygame.image.load(str(path))
            image = image.convert_alpha() if alpha else image.convert()

        if size is not None:
            image = self._scale(image, size)
        self._surface_cache[key] = image
        return image

    def load_animation(
        self,
        name: str,
        size: tuple[int, int] | None = None,
        frame_time: float = 0.10,
    ) -> Animation:
        """
        Carrega uma animação de GIF ou cria fallback estático.
        """
        key = (name, size)
        if key in self._animation_cache:
            return self._animation_cache[key]

        path = self.path(name)
        frames: list[pygame.Surface] = []

        if path.exists() and path.suffix.lower() == ".gif" and Image is not None:
            try:
                pil = Image.open(path)
                pil_frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(pil)]
                bbox = self._union_bbox(pil_frames)
                if bbox is not None:
                    pil_frames = [frame.crop(bbox) for frame in pil_frames]

                for rgba in pil_frames:
                    mode = rgba.mode
                    data = rgba.tobytes()
                    surf = pygame.image.fromstring(data, rgba.size, mode).convert_alpha()
                    if size is not None:
                        surf = self._scale(surf, size)
                    frames.append(surf)
            except Exception:
                frames = []

        if not frames:
            try:
                frames = [self.load_surface(name, size=size, trim=True)]
            except Exception:
                frames = [self._placeholder(size or (64, 64), name)]

        anim = Animation(frames=frames, frame_time=frame_time)
        self._animation_cache[key] = anim
        return anim

    def _union_bbox(self, pil_frames: list["Image.Image"]) -> tuple[int, int, int, int] | None:
        """Calcula uma bounding box comum para todos os frames."""
        boxes = [self._alpha_bbox(frame, threshold=12) for frame in pil_frames]
        boxes = [box for box in boxes if box is not None]
        if not boxes:
            return None
        left = min(box[0] for box in boxes)
        top = min(box[1] for box in boxes)
        right = max(box[2] for box in boxes)
        bottom = max(box[3] for box in boxes)
        return (left, top, right, bottom)

    def _alpha_bbox(self, image: "Image.Image", threshold: int = 1) -> tuple[int, int, int, int] | None:
        """Bounding box ignorando pixels quase transparentes."""
        alpha = image.getchannel("A")
        mask = alpha.point(lambda a: 255 if a >= threshold else 0)
        return mask.getbbox()

    def _scale(self, surface: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
        """Usa smoothscale quando possível; caso contrário, faz scale padrão."""
        try:
            if surface.get_bitsize() >= 24:
                return pygame.transform.smoothscale(surface, size)
        except Exception:
            pass
        return pygame.transform.scale(surface, size)

    def _placeholder(self, size: tuple[int, int], label: str) -> pygame.Surface:
        """Placeholder simples para asset ausente."""
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((180, 90, 90, 210))
        pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), width=2, border_radius=8)
        font = pygame.font.SysFont("arial", max(12, min(size) // 5))
        text = font.render(label[:8], True, (255, 255, 255))
        surf.blit(text, text.get_rect(center=surf.get_rect().center))
        return surf
