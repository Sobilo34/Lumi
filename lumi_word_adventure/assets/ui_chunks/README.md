# UI chunk packs (PNG layers)

Place divided reference art here — one folder per screen.

## Folder layout

```
assets/ui_chunks/
  splash_loading/
    background.png
    logo.png
    mascot.png
    letter_a.png
    letter_b.png
    letter_c.png
    card_apple.png
    card_cat.png
    card_boat.png
    loading_bar.png
  letter_island_game/
    background.png      # beach/sky (no letters on board)
    board.png           # white stitched board frame (empty center)
    hud.png             # optional top bar chrome
    footer_actions.png  # optional Repeat/Hint/Speak buttons
    card_frame.png      # optional empty card template (repeated x4)
  how_to_play/
    background.png
    panel_frame.png
    title_how_to_play.png
    step_listen.png
    step_tap.png
    step_speak.png
    step_stars.png
    mascot.png
    btn_lets_go.png
    btn_speaker.png
  main_menu/
    background.png
    logo.png
    mascot.png
    btn_play.png
    btn_practice.png
    btn_report.png
    btn_settings.png
    btn_speaker.png
    btn_star.png
    abc_blocks.png
    letter_a/b/c.png   # optional; reuse splash pack
    card_apple/cat/boat.png
  profile_selection/
    background.png
    title_banner.png
    btn_back.png
    btn_settings.png
    profile_card_frame.png
    avatar_player1.png
    avatar_player2.png
    avatar_new.png
    mascot_decor.png
    letter_a/b/c.png   # optional; can reuse splash pack
  welcome/
    background.png
    logo.png
    mascot.png
    speech_bubble.png
    start_button.png
    btn_speaker.png
    btn_star.png
    btn_abc.png
    card_apple.png
    card_cat.png
    card_boat.png      # optional; can reuse splash pack
    letter_a/b/c.png   # optional; can reuse splash pack
  ...
```

## Rules

1. **Target canvas:** 1280×720 (same as `reference_interfaces/`).
2. **Same designs** as `reference_interfaces/01_…` through `28_…`, split into layers.
3. **Leave dynamic areas empty** on static layers (letter cards, “Find B”, word labels, progress text).
4. **PNG with transparency** where elements float over the background.
5. Layer positions are defined in `data/ui_chunk_manifest.json` — tell us if your export uses different coordinates.

## Until chunks arrive

The app uses the **full reference PNG** from `reference_interfaces/` and draws **dynamic text** on top for gameplay screens (letters, words, prompts).

When you add chunk files for a screen, those layers replace the full PNG automatically.

## Naming

Match `screen_id` from `engine/screen_registry.py` (e.g. `letter_island_game`, not `07_letter_island`).

Reference mapping:

| screen_id | reference_interfaces file |
|-----------|---------------------------|
| splash_loading | 01_splash_loading.png |
| welcome | 02_welcome_start.png |
| profile_selection | 03_profile_selection.png |
| main_menu | 04_main_menu.png |
| how_to_play | 05_instruction_how_to_play.png |
| world_map | 06_world_map.png |
| letter_island_game | 07_letter_island_gameplay.png |
| … | … |

Send chunks screen-by-screen; we wire each pack in the manifest as you provide them.

## Performance

Chunk PNGs exported on white/gray canvases are trimmed once on first load and cached under
`assets/ui_chunks/.trim_cache/`. After the first run (or after `python tools/preprocess_chunks.py`),
startup loads in under one second.

Static screen layers are baked into memory; only dynamic overlays (loading stars, speech text,
profile names) redraw each frame.
