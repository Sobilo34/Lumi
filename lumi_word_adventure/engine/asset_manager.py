"""Reusable asset loading and caching helpers."""
from __future__ import annotations

from pathlib import Path

import pygame

from config import BABY_PINK, REFERENCE_INTERFACES_DIR, SCREEN_HEIGHT, SCREEN_WIDTH, UI_CHUNKS_DIR

# Install scripts write this marker after offline PNG processing is complete.
SHIPPED_ASSETS_MARKER = ".shipped_ready"
SHIPPED_ASSETS_VERSION = "1"


def _is_flat_backdrop(r: int, g: int, b: int, a: int) -> bool:
    if a < 10:
        return True
    peak = max(r, g, b)
    if peak - min(r, g, b) < 28 and peak > 195:
        return True
    # Cream / beige letter-tile squares from exported PNGs.
    if r > 215 and g > 200 and b > 165 and r >= g >= b:
        return True
    return False


def _find_content_bbox(surface: pygame.Surface) -> tuple[int, int, int, int] | None:
    width, height = surface.get_size()
    min_x, min_y, max_x, max_y = width, height, 0, 0
    found = False
    step = 3
    for y in range(0, height, step):
        for x in range(0, width, step):
            color = surface.get_at((x, y))
            if _is_flat_backdrop(color.r, color.g, color.b, color.a):
                continue
            found = True
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if not found:
        return None
    min_x = max(0, min_x - 6)
    min_y = max(0, min_y - 6)
    max_x = min(width - 1, max_x + 6)
    max_y = min(height - 1, max_y + 6)
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            color = surface.get_at((x, y))
            if _is_flat_backdrop(color.r, color.g, color.b, color.a):
                continue
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    return min_x, min_y, max_x - min_x + 1, max_y - min_y + 1


def _is_export_padding(r: int, g: int, b: int, a: int) -> bool:
    """Checkerboard / pure-white export backdrops only — keep cream and pink card art."""
    if a < 10:
        return True
    if r > 252 and g > 252 and b > 252:
        return True
    peak = max(r, g, b)
    low = min(r, g, b)
    if peak - low <= 10 and 168 <= peak <= 238:
        return True
    return False


def _knock_out_export_padding(image: pygame.Surface) -> pygame.Surface:
    """Turn export checkerboard/white into transparency; keep card frames and art."""
    surface = image.convert_alpha()
    width, height = surface.get_size()
    step = 1 if width * height <= 250_000 else 2
    for y in range(0, height, step):
        for x in range(0, width, step):
            color = surface.get_at((x, y))
            if not _is_export_padding(color.r, color.g, color.b, color.a):
                continue
            if step == 1:
                surface.set_at((x, y), (0, 0, 0, 0))
            else:
                for dy in range(step):
                    for dx in range(step):
                        px, py = x + dx, y + dy
                        if px < width and py < height:
                            surface.set_at((px, py), (0, 0, 0, 0))
    return surface


def _trim_flat_backdrop(image: pygame.Surface) -> pygame.Surface:
    """Remove flat gray/white export padding from chunked PNGs."""
    surface = image.convert_alpha()
    bbox = _find_content_bbox(surface)
    if bbox is None:
        return surface
    min_x, min_y, bw, bh = bbox
    trimmed = pygame.Surface((bw, bh), pygame.SRCALPHA)
    for y in range(bh):
        for x in range(bw):
            color = surface.get_at((min_x + x, min_y + y))
            if _is_flat_backdrop(color.r, color.g, color.b, color.a):
                trimmed.set_at((x, y), (0, 0, 0, 0))
            else:
                trimmed.set_at((x, y), color)
    return trimmed


def _should_trim_chunk(filename: str) -> bool:
    if filename in {
        "background.png",
        "success_background.png",
        "failure_background.png",
    }:
        return False
    if filename.startswith("objects/") or filename.startswith("prompts/"):
        return False
    return True


def _crop_to_opaque_bbox(surface: pygame.Surface) -> pygame.Surface:
    """Trim transparent margins so object art centers in card slots."""
    image = surface.convert_alpha()
    width, height = image.get_size()
    min_x, min_y, max_x, max_y = width, height, 0, 0
    found = False
    for y in range(height):
        for x in range(width):
            if image.get_at((x, y)).a > 12:
                found = True
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if not found:
        return image
    rect = pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
    return image.subsurface(rect).copy()


def _is_word_object_border(r: int, g: int, b: int, a: int) -> bool:
    """Card frame, cream fill, and export padding around Word Garden object art."""
    if a < 12:
        return True
    if _is_export_padding(r, g, b, a):
        return True
    if _is_flat_backdrop(r, g, b, a):
        return True
    if r > 248 and g > 240 and b > 230:
        return True
    if a > 12 and r > 245 and g > 228 and b > 210 and r - b < 50:
        return True
    if r > 232 and g > 228 and b > 222 and max(r, g, b) - min(r, g, b) < 18:
        return True
    if r > 185 and g > 85 and b > 95 and r > g and r > b + 15:
        return True
    return False


def _edge_border_ratio(surface: pygame.Surface, *, edge: str) -> float:
    width, height = surface.get_size()
    if width <= 0 or height <= 0:
        return 1.0
    step = 2
    if edge == "top":
        samples = [surface.get_at((x, 0)) for x in range(0, width, step)]
    elif edge == "bottom":
        samples = [surface.get_at((x, height - 1)) for x in range(0, width, step)]
    elif edge == "left":
        samples = [surface.get_at((0, y)) for y in range(0, height, step)]
    else:
        samples = [surface.get_at((width - 1, y)) for y in range(0, height, step)]
    if not samples:
        return 1.0
    border = sum(
        1 for color in samples if _is_word_object_border(color.r, color.g, color.b, color.a)
    )
    return border / len(samples)


def _strip_word_object_borders(surface: pygame.Surface) -> pygame.Surface:
    """Peel card-frame rows/columns until only the illustration remains."""
    trimmed = surface
    for _ in range(120):
        width, height = trimmed.get_size()
        if width < 24 or height < 24:
            break
        changed = False
        if _edge_border_ratio(trimmed, edge="top") > 0.8:
            trimmed = trimmed.subsurface((0, 1, width, height - 1)).copy()
            changed = True
        if _edge_border_ratio(trimmed, edge="bottom") > 0.8:
            width, height = trimmed.get_size()
            trimmed = trimmed.subsurface((0, 0, width, height - 1)).copy()
            changed = True
        if _edge_border_ratio(trimmed, edge="left") > 0.8:
            width, height = trimmed.get_size()
            trimmed = trimmed.subsurface((1, 0, width - 1, height)).copy()
            changed = True
        if _edge_border_ratio(trimmed, edge="right") > 0.8:
            width, height = trimmed.get_size()
            trimmed = trimmed.subsurface((0, 0, width - 1, height)).copy()
            changed = True
        if not changed:
            break
    return trimmed


def _is_cream_card_face(r: int, g: int, b: int, a: int) -> bool:
    return a > 12 and r > 244 and g > 234 and b > 224 and r - b < 35


def _is_pink_card_frame(r: int, g: int, b: int, a: int) -> bool:
    return a > 12 and r > 175 and g > 70 and b > 85 and r > g + 25 and r > b + 25


def _bbox_matching(
    surface: pygame.Surface,
    predicate,
    *,
    step: int = 2,
) -> pygame.Rect | None:
    width, height = surface.get_size()
    min_x, min_y, max_x, max_y = width, height, 0, 0
    found = False
    for y in range(0, height, step):
        for x in range(0, width, step):
            color = surface.get_at((x, y))
            if not predicate(color.r, color.g, color.b, color.a):
                continue
            found = True
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if not found:
        return None
    return pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)


_OBJECT_WORK_MAX = 512


_OBJECT_PROBE_MAX = 384


def _downscale_for_probe(surface: pygame.Surface, max_dim: int = _OBJECT_PROBE_MAX) -> tuple[pygame.Surface, float]:
    width, height = surface.get_size()
    if max(width, height) <= max_dim:
        return surface, 1.0
    scale = max_dim / max(width, height)
    probe = pygame.transform.smoothscale(
        surface,
        (max(1, int(width * scale)), max(1, int(height * scale))),
    )
    return probe, scale


def _scale_probe_rect(rect: pygame.Rect, scale: float, bounds: pygame.Rect) -> pygame.Rect:
    if scale >= 1.0:
        return rect.clip(bounds)
    inv = 1.0 / scale
    scaled = pygame.Rect(
        int(rect.x * inv),
        int(rect.y * inv),
        max(1, int(rect.width * inv)),
        max(1, int(rect.height * inv)),
    )
    return scaled.clip(bounds)


def _knock_out_word_card_pixels(surface: pygame.Surface) -> pygame.Surface:
    """Make card frame / cream fill transparent so only the illustration remains."""
    result = surface.convert_alpha()
    width, height = result.get_size()
    step = 1 if width * height <= 180_000 else 2
    for y in range(0, height, step):
        for x in range(0, width, step):
            color = result.get_at((x, y))
            if not _is_word_object_border(color.r, color.g, color.b, color.a):
                continue
            if step == 1:
                result.set_at((x, y), (0, 0, 0, 0))
            else:
                for dy in range(step):
                    for dx in range(step):
                        px, py = x + dx, y + dy
                        if px < width and py < height:
                            result.set_at((px, py), (0, 0, 0, 0))
    return result


def _process_word_garden_object(image: pygame.Surface) -> pygame.Surface:
    """Strip export padding and baked-in card art from object PNGs."""
    source = image.convert_alpha()
    width, height = source.get_size()
    work_scale = min(1.0, _OBJECT_WORK_MAX / max(width, height))
    if work_scale < 1.0:
        work = pygame.transform.smoothscale(
            source,
            (max(1, int(width * work_scale)), max(1, int(height * work_scale))),
        )
    else:
        work = source
    work = _crop_to_opaque_bbox(_knock_out_export_padding(work))
    work = _strip_word_object_borders(work)
    work = _knock_out_word_card_pixels(work)
    illustration = _bbox_matching(
        work,
        lambda r, g, b, a: a > 12 and not _is_word_object_border(r, g, b, a),
        step=1,
    )
    if illustration is not None and illustration.width >= 20 and illustration.height >= 20:
        work = work.subsurface(illustration).copy()
    return _crop_to_opaque_bbox(work)


def _extract_word_object_illustration(image: pygame.Surface) -> pygame.Surface:
    """Keep only the painted object; drop baked-in card frame and export padding."""
    return _process_word_garden_object(image)


def _knock_out_light_backdrop(image: pygame.Surface) -> pygame.Surface:
    """Remove near-white export backdrops from prompt PNGs."""
    surface = image.convert_alpha()
    width, height = surface.get_size()
    for y in range(height):
        for x in range(width):
            color = surface.get_at((x, y))
            if color.a < 12:
                continue
            r, g, b = color.r, color.g, color.b
            if r > 235 and g > 230 and b > 230:
                surface.set_at((x, y), (0, 0, 0, 0))
    return surface


def _process_word_garden_chunk(image: pygame.Surface, *, crop: bool = False) -> pygame.Surface:
    """Remove export padding from Word Garden object/prompt PNGs."""
    if crop:
        return _extract_word_object_illustration(image)
    surface = _knock_out_export_padding(_knock_out_light_backdrop(image))
    return _crop_to_opaque_bbox(surface)


WORD_GARDEN_TRIM_CACHE_VERSION = "v8"


def write_shipped_assets_marker(chunks_dir: Path, screen_id: str, *, version: str = SHIPPED_ASSETS_VERSION) -> None:
    """Mark a chunk folder as install-processed so runtime skips pixel surgery."""
    marker = chunks_dir / screen_id / SHIPPED_ASSETS_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(f"{version}\n", encoding="utf-8")


def _shipped_assets_version(chunks_dir: Path, screen_id: str) -> str | None:
    marker = chunks_dir / screen_id / SHIPPED_ASSETS_MARKER
    if not marker.is_file():
        return None
    return marker.read_text(encoding="utf-8").strip() or None


def _word_garden_trim_cache_stale(filename: str, surface: pygame.Surface, source: pygame.Surface) -> bool:
    """Ignore old caches from previous processing pipelines."""
    if filename.startswith("objects/"):
        return (
            surface.get_width() >= min(450, source.get_width() - 80)
            and surface.get_height() >= min(450, source.get_height() - 80)
        )
    if filename.startswith("prompts/"):
        return surface.get_width() >= min(850, source.get_width() - 40)
    return False


class AssetManager:
    def __init__(
        self,
        reference_dir: Path | None = None,
        chunks_dir: Path | None = None,
    ) -> None:
        self.reference_dir = Path(reference_dir) if reference_dir is not None else REFERENCE_INTERFACES_DIR
        self.chunks_dir = Path(chunks_dir) if chunks_dir is not None else UI_CHUNKS_DIR
        self._image_cache: dict[str, pygame.Surface] = {}
        self._chunk_cache: dict[str, pygame.Surface | None] = {}
        self._scaled_cache: dict[str, pygame.Surface] = {}
        self._missing_images: set[str] = set()
        self._shipped_ready: dict[str, bool] = {}

    def assets_shipped_ready(self, screen_id: str) -> bool:
        cached = self._shipped_ready.get(screen_id)
        if cached is not None:
            return cached
        ready = _shipped_assets_version(self.chunks_dir, screen_id) == SHIPPED_ASSETS_VERSION
        self._shipped_ready[screen_id] = ready
        return ready

    def _load_chunk_file(self, image_path: Path) -> pygame.Surface:
        image = pygame.image.load(str(image_path))
        if image.get_alpha() is not None:
            image = image.convert_alpha()
        else:
            image = image.convert()
        return self._prepare_surface(image)

    def _load_chunk_legacy(self, screen_id: str, filename: str, image_path: Path) -> pygame.Surface:
        trimmed_path = (
            self.chunks_dir
            / ".trim_cache"
            / WORD_GARDEN_TRIM_CACHE_VERSION
            / screen_id
            / filename
        )
        use_trim_cache = _should_trim_chunk(filename) or filename.startswith(("objects/", "prompts/"))
        if (
            use_trim_cache
            and trimmed_path.is_file()
            and trimmed_path.stat().st_mtime >= image_path.stat().st_mtime
        ):
            cached_trim = pygame.image.load(str(trimmed_path))
            if not _word_garden_trim_cache_stale(filename, cached_trim, pygame.image.load(str(image_path))):
                return self._prepare_surface(cached_trim)
        image = pygame.image.load(str(image_path))
        image = self._prepare_surface(image)
        if filename.startswith("objects/"):
            image = _process_word_garden_object(image)
        elif filename.startswith("prompts/"):
            image = _process_word_garden_chunk(image, crop=False)
        elif use_trim_cache:
            image = _trim_flat_backdrop(image)
        if use_trim_cache or filename.startswith(("objects/", "prompts/")):
            trimmed_path.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(image, str(trimmed_path))
        return image

    def _placeholder_surface(self, filename: str) -> pygame.Surface:
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.fill(pygame.Color(BABY_PINK))
        if filename not in self._missing_images:
            self._missing_images.add(filename)
            print(
                f"[Lumi Assets] Missing reference image '{filename}' "
                f"in {self.reference_dir}. Using baby-pink placeholder."
            )
        return surface

    def _prepare_surface(self, image: pygame.Surface) -> pygame.Surface:
        if pygame.display.get_surface() is not None:
            if image.get_alpha() is not None:
                return image.convert_alpha()
            return image.convert()
        return image

    def scaled_chunk(
        self,
        screen_id: str,
        filename: str,
        width: int,
        height: int,
        *,
        fit: str = "contain",
    ) -> pygame.Surface | None:
        if width <= 0 or height <= 0:
            return None
        cache_key = f"{screen_id}/{filename}@{width}x{height}:{fit}"
        if cache_key in self._scaled_cache:
            return self._scaled_cache[cache_key]
        image = self.load_chunk(screen_id, filename)
        if image is None:
            return None
        prepared = self._fit_surface(image, width, height, fit=fit)
        self._scaled_cache[cache_key] = prepared
        return prepared

    def _fit_surface(self, image: pygame.Surface, width: int, height: int, *, fit: str) -> pygame.Surface:
        source_w, source_h = image.get_size()
        if source_w <= 0 or source_h <= 0:
            return image
        if fit == "fill":
            if source_w == width and source_h == height:
                return image
            scaler = pygame.transform.scale
            if max(width, height) > 320:
                scaler = pygame.transform.smoothscale
            return scaler(image, (width, height))
        scale = min(width / source_w, height / source_h)
        target_w = max(1, int(source_w * scale))
        target_h = max(1, int(source_h * scale))
        if target_w == source_w and target_h == source_h:
            return image
        scaler = pygame.transform.scale
        if max(target_w, target_h) > 320:
            scaler = pygame.transform.smoothscale
        return scaler(image, (target_w, target_h))

    def load_image(self, filename: str) -> pygame.Surface:
        if filename not in self._image_cache:
            image_path = self.reference_dir / filename
            if not image_path.is_file():
                self._image_cache[filename] = self._placeholder_surface(filename)
                return self._image_cache[filename]

            try:
                image = pygame.image.load(str(image_path))
            except (pygame.error, FileNotFoundError, OSError) as error:
                print(f"[Lumi Assets] Failed to load '{filename}': {error}")
                self._image_cache[filename] = self._placeholder_surface(filename)
                return self._image_cache[filename]

            image = self._prepare_surface(image)
            self._image_cache[filename] = pygame.transform.smoothscale(
                image,
                (SCREEN_WIDTH, SCREEN_HEIGHT),
            )
        return self._image_cache[filename]

    def load_chunk(self, screen_id: str, filename: str) -> pygame.Surface | None:
        """Load a PNG chunk from assets/ui_chunks/<screen_id>/<filename>."""
        if not filename:
            return None
        cache_key = f"{screen_id}/{filename}"
        if cache_key in self._chunk_cache:
            return self._chunk_cache[cache_key]
        image_path = self.chunks_dir / screen_id / filename
        if not image_path.is_file():
            self._chunk_cache[cache_key] = None
            return None
        try:
            if self.assets_shipped_ready(screen_id):
                image = self._load_chunk_file(image_path)
            else:
                image = self._load_chunk_legacy(screen_id, filename, image_path)
            self._chunk_cache[cache_key] = image
        except (pygame.error, FileNotFoundError, OSError) as error:
            print(f"[Lumi Assets] Failed to load chunk '{cache_key}': {error}")
            self._chunk_cache[cache_key] = None
        return self._chunk_cache[cache_key]

    def invalidate_letter_tiles(self, asset_root: str = "letter_island_game") -> None:
        """Drop cached letter PNGs so updated assets in letters/ are reloaded."""
        needle = f"{asset_root}/letters/"
        for cache in (self._chunk_cache, self._scaled_cache):
            for key in list(cache.keys()):
                if needle in key:
                    del cache[key]

    def invalidate_word_garden_assets(self, asset_root: str = "word_garden_game") -> None:
        """Drop in-memory Word Garden caches (keeps shipped PNGs on disk)."""
        needle = f"{asset_root}/"
        for cache in (self._chunk_cache, self._scaled_cache):
            for key in list(cache.keys()):
                if key.startswith(needle):
                    del cache[key]
        self._shipped_ready.pop(asset_root, None)

    def prewarm_gameplay_assets(
        self,
        *,
        word_garden_root: str = "word_garden_game",
        letter_root: str = "letter_island_game",
        word_object_w: int = 182,
        word_object_h: int = 227,
        word_prompt_w: int = 109,
        word_prompt_h: int = 26,
        letter_tile_w: int = 140,
        letter_tile_h: int = 158,
        find_w: int = 435,
        find_h: int = 72,
    ) -> None:
        """Load shipped gameplay PNGs and common draw sizes once at startup."""
        from string import ascii_uppercase

        from engine.word_garden import WORD_GARDEN_WORDS

        for filename in ("background.png", "success_background.png", "failure_background.png"):
            self.load_chunk(word_garden_root, filename)
        for word in WORD_GARDEN_WORDS:
            key = word.lower()
            self.load_chunk(word_garden_root, f"objects/{key}.png")
            self.load_chunk(word_garden_root, f"prompts/{key}.png")
            self.scaled_word_prompt(word_garden_root, key, word_prompt_w, word_prompt_h, fit="contain")
            self.scaled_word_object(word_garden_root, key, word_object_w, word_object_h, fit="contain")
        for filename in ("07_letter_island_gameplay.png", "08_letter_correct_feedback.png", "11_word_garden_gameplay.png"):
            self.load_image(filename)
        for letter in ascii_uppercase:
            key = letter.lower()
            self.load_chunk(letter_root, f"find/{key}.png")
            self.load_chunk(letter_root, f"letters/{key}.png")
            self.load_chunk(letter_root, f"letters/{key}_selected.png")
            self.scaled_find_prompt(letter_root, letter, find_w, find_h)
            self.scaled_letter_tile(letter_root, letter, letter_tile_w, letter_tile_h, selected=False)
            self.scaled_letter_tile(
                letter_root,
                letter,
                letter_tile_w,
                letter_tile_h,
                selected=True,
                selected_scale=1.22,
            )

    def warm_word_garden_round(
        self,
        words: tuple[str, ...],
        *,
        asset_root: str = "word_garden_game",
        prompt_w: int = 109,
        prompt_h: int = 26,
        object_w: int = 182,
        object_h: int = 227,
    ) -> None:
        """Pre-scale assets for the active Word Garden round."""
        for word in words:
            key = str(word or "").strip().lower()
            if not key:
                continue
            self.scaled_word_prompt(asset_root, key, prompt_w, prompt_h, fit="contain")
            self.scaled_word_object(
                asset_root,
                key,
                object_w,
                object_h,
                fit="contain",
            )

    def chunk_exists(self, screen_id: str, filename: str) -> bool:
        return (self.chunks_dir / screen_id / filename).is_file()

    def load_letter_tile(self, asset_root: str, letter: str, *, selected: bool = False) -> pygame.Surface | None:
        key = str(letter or "A").lower()
        suffix = "_selected" if selected else ""
        return self.load_chunk(asset_root, f"letters/{key}{suffix}.png")

    def scaled_letter_tile(
        self,
        asset_root: str,
        letter: str,
        width: int,
        height: int,
        *,
        selected: bool = False,
        selected_scale: float = 1.22,
    ) -> pygame.Surface | None:
        if width <= 0 or height <= 0:
            return None
        key = str(letter or "A").lower()
        suffix = "_selected" if selected else ""
        filename = f"letters/{key}{suffix}.png"
        scale = selected_scale if selected else 1.0
        fit_w = max(1, int(width * scale))
        fit_h = max(1, int(height * scale))
        cache_key = f"{asset_root}/{filename}@{width}x{height}@s{scale}"
        if cache_key in self._scaled_cache:
            return self._scaled_cache[cache_key]
        image = self.load_letter_tile(asset_root, letter, selected=selected)
        if image is None and selected:
            image = self.load_letter_tile(asset_root, letter, selected=False)
        if image is None:
            return None
        prepared = self._fit_surface(image, fit_w, fit_h, fit="contain")
        self._scaled_cache[cache_key] = prepared
        return prepared

    def load_find_prompt(self, asset_root: str, letter: str) -> pygame.Surface | None:
        key = str(letter or "A").upper()
        if not key.isalpha() or len(key) != 1:
            return None
        return self.load_chunk(asset_root, f"find/{key.lower()}.png")

    def scaled_find_prompt(
        self,
        asset_root: str,
        letter: str,
        width: int,
        height: int,
    ) -> pygame.Surface | None:
        if width <= 0 or height <= 0:
            return None
        key = str(letter or "A").lower()
        cache_key = f"{asset_root}/find/{key}@{width}x{height}"
        if cache_key in self._scaled_cache:
            return self._scaled_cache[cache_key]
        image = self.load_find_prompt(asset_root, letter)
        if image is None:
            return None
        prepared = self._fit_surface(image, width, height, fit="contain")
        self._scaled_cache[cache_key] = prepared
        return prepared

    def load_word_prompt(self, asset_root: str, word: str) -> pygame.Surface | None:
        key = str(word or "").strip().lower()
        if not key:
            return None
        return self.load_chunk(asset_root, f"prompts/{key}.png")

    def scaled_word_prompt(
        self,
        asset_root: str,
        word: str,
        width: int,
        height: int,
        *,
        fit: str = "contain",
    ) -> pygame.Surface | None:
        if width <= 0 or height <= 0:
            return None
        key = str(word or "cat").strip().lower()
        cache_key = f"{asset_root}/prompts/{key}@{width}x{height}@{fit}"
        if cache_key in self._scaled_cache:
            return self._scaled_cache[cache_key]
        image = self.load_word_prompt(asset_root, word)
        if image is None:
            return None
        prepared = self._fit_surface(image, width, height, fit=fit)
        self._scaled_cache[cache_key] = prepared
        return prepared

    def load_word_object(self, asset_root: str, word: str) -> pygame.Surface | None:
        key = str(word or "").strip().lower()
        if not key:
            return None
        return self.load_chunk(asset_root, f"objects/{key}.png")

    def scaled_word_object(
        self,
        asset_root: str,
        word: str,
        width: int,
        height: int,
        *,
        selected: bool = False,
        selected_scale: float = 1.08,
        fit: str = "contain",
    ) -> pygame.Surface | None:
        if width <= 0 or height <= 0:
            return None
        key = str(word or "cat").strip().lower()
        scale = selected_scale if selected else 1.0
        fit_w = max(1, int(width * scale))
        fit_h = max(1, int(height * scale))
        cache_key = f"{asset_root}/objects/{key}@{width}x{height}@s{scale}@{fit}"
        if cache_key in self._scaled_cache:
            return self._scaled_cache[cache_key]
        image = self.load_word_object(asset_root, word)
        if image is None:
            return None
        prepared = self._fit_surface(image, fit_w, fit_h, fit=fit)
        self._scaled_cache[cache_key] = prepared
        return prepared

    def preload_screen(self, screen_id: str, filenames: tuple[str, ...]) -> None:
        for filename in filenames:
            self.load_chunk(screen_id, filename)

    def preload_letter_island(
        self,
        asset_root: str = "letter_island_game",
        *,
        tile_w: int = 140,
        tile_h: int = 158,
        find_w: int = 435,
        find_h: int = 72,
    ) -> None:
        """Warm scaled letter/find caches for the active round sizes."""
        from string import ascii_uppercase

        for filename in ("07_letter_island_gameplay.png", "08_letter_correct_feedback.png"):
            self.load_image(filename)
        for letter in ascii_uppercase:
            self.scaled_find_prompt(asset_root, letter, find_w, find_h)
            self.scaled_letter_tile(asset_root, letter, tile_w, tile_h, selected=False)
            self.scaled_letter_tile(
                asset_root,
                letter,
                tile_w,
                tile_h,
                selected=True,
                selected_scale=1.22,
            )
