# Design language — ZIYO YOGʻDUSI

> **Status: CHOSEN — option A "Warm modern" (user decision, 2026-11-25). Fixed for the whole film.**
> There are no reference photos; every space is designed in Blender. The kit (`blender/scripts/build_kit.py`) builds only this style. Options B (clean white-and-glass) and C (bold contemporary) were rejected and removed from the kit.
> Real school details (building colour, floors, roof shape, main colours): **none provided yet** — when given, they override the values below.

Calm, comfortable and safe: warm white walls, light oak floors and doors, deep teal as the identity accent, amber as a small secondary warmth accent (links to the scene 1 amber code-liquid).

## Palette and materials

| Element | Value |
|---|---|
| Walls | warm white paint `#ECE6DC`, matte |
| Accent colours | deep teal `#2F6E73` (feature wall panels, upholstery, signage), amber `#E3A33B` (small accents only) |
| Floors | light oak planks `#CDAE88`, 1200 × 150 mm, satin lacquer (classrooms, corridors, dorm); concrete `#9A9893` only for service areas |
| Doors | light oak flush leaf, oak architraves 70 mm, brushed-steel lever handles |
| Skirting / window sills | light oak |
| Dark wood | walnut `#5B3F2C` (teacher desks, shelves, cabinets, lectern) |
| Window frames | graphite powder-coated aluminium `#2E3135`, 60 mm face, central mullion |
| Glass | clear, thin-wall |
| Ceiling | warm white `#F3F1EC` 600 × 600 mm acoustic tiles — **always reads white**; warmth comes from light colour, never from darker materials |
| Furniture frames | graphite `#2E3135` steel tube (35 mm square desks, Ø 22 mm bent tube chairs), rubber glides |
| Furniture tops / seats | light oak (desks: dark grey ABS edge band; chairs: oak plywood seat + curved back) |
| Fabric | teal `#2F6E73` |
| Metals | brushed steel (handles, trims), chrome (small fittings) |

## Architecture (kit geometry)

| Element | Spec |
|---|---|
| Module | 3.0 m grid; room height 3.2 m to the ceiling; walls 0.20 m thick, continuing 0.30 m above the ceiling to the slab |
| Windows | 2.4 × 2.0 m opening per 3 m module, sill at 0.90 m |
| Doors | 1.0 × 2.2 m |
| Ceiling fixtures | per 3 × 3 m bay: 4 round recessed downlights (Ø 190 mm trim, real spot lights) + one 2.4 m linear LED slot (real area light) |
| Accent lighting | 3 m LED channels (wall-washers, under-board strips) — coloured only in `tech_dark` |
| Exterior (seen through windows, slightly out of focus) | paved schoolyard with court lines, lawn band with trees, neighbouring 2–3 storey plaster buildings (`#E4D8C4`) at 70–90 m, HDRI sky |

## Lighting presets

| Preset | Use | Setup |
|---|---|---|
| `day_interior` | classrooms, entrance, cafeteria by day | sun 5300 K through the windows (32°), HDRI view outside, ceiling lights on at classroom level (4000 K), neutral warm ambient |
| `warm_interior` | dormitory evening, warm moments | 3000 K downlights and LED slots; neutral ambient so the ceiling stays white; sunset HDRI outside |
| `tech_dark` | IT class, CCTV room | neutral dark room, dim neutral 4300 K downlights keep wood and walls readable; blue only from LED accent channels and screens, violet only from the LED slots |
| `outdoor_day` | stadium, building exterior | high sun 5600 K (52°), HDRI sky, interior fixtures off |

Every visible fixture that looks lit has a real light under it (spot / area), so walls show falloff and the floor shows soft pools. Interiors bake an irradiance volume per scene/preset for occlusion-aware bounce light.
