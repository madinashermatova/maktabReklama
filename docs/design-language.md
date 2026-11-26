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

## School building exterior (kit `PIECE_school_building`, `PIECE_school_grounds`)

Neutral design choices — **not** real details of the school (none provided yet; real details override these).

| Element | Spec |
|---|---|
| Massing | one 48 × 15 m teaching wing, 3 storeys, flat roof with 1.0 m parapet and graphite coping; ground floor +0.45 m on a stone plinth; floor-to-floor 3.9 m |
| Facade | warm white render `#ECE6DC` with very soft large-scale tonal variation; thin string courses at each floor line (`#DCD4C7`) |
| Windows | the interior kit module seen from outside: 2.4 × 2.0 m per 3 m module, sill 0.90 m; graphite frames recessed 0.12 m, mullion + top-hung vent transom, graphite sill flashing; some roller blinds down; room shells with lit ceiling panels behind the glass |
| Entrance | central 12 m glazed core in a teal `#2F6E73` portal frame; curtain wall with graphite mullions; double glass doors; lobby slabs with oak edges and an oak stair behind the glass; cantilevered canopy, graphite fascia, light-oak soffit with downlights; 3 steps + 1:15 ramp with steel handrails |
| Grounds | paved forecourt (600 × 300 mm slabs) with darker granite bands, lawn islands with kerbs, planter strip with clipped shrubs along the facade, oak benches, graphite bollard lights, trees (leaf clusters + leaf cards), distant tree belt |
| Never | signage, lettering, symbols or logos on the building (BRAND rules) |

## Lighting presets

| Preset | Use | Setup |
|---|---|---|
| `day_interior` | classrooms, entrance, cafeteria by day | sun 5300 K through the windows (32°), HDRI view outside, ceiling lights on at classroom level (4000 K), neutral warm ambient |
| `warm_interior` | dormitory evening, warm moments | 3000 K downlights and LED slots; neutral ambient so the ceiling stays white; sunset HDRI outside |
| `tech_dark` | IT class, CCTV room | neutral dark room, dim neutral 4300 K downlights keep wood and walls readable; blue only from LED accent channels and screens, violet only from the LED slots |
| `outdoor_day` | stadium, building exterior | sun 5600 K (52° default; per shot via `C.set_sun_direction`, then `C.sync_sky_to_sun`), procedural physical sky (no HDRI), interior fixtures off; exterior shots use the AgX "Medium High Contrast" look |

## Kit v2 review notes — apply in every scene (user approval, 2026-11-26)

Kit v2 (`renders/_kit/v2/`) is approved as the design language. These notes are binding for every scene:

1. **Exterior backdrop seen through windows:** stronger depth-of-field blur (focus stays inside the room; the outside reads as soft shapes and light). Facades get real detail — window frames, recessed openings, slight per-building colour variation — and trees have natural canopies made of leaf clusters, not smooth blobs.
2. **Classrooms always have a proper front wall:** a whiteboard or smart board, with the teacher's desk in front of it, facing the students. **No monitors on student desks** unless the scene requires it (IT class).
3. **Wood floor:** subtle lacquered gloss with soft reflections of the windows and lights (satin, never mirror-like).
4. **`tech_dark`:** exposure slightly higher plus a soft neutral fill, so the floor and desks stay readable; screens and LED strips provide the accent colour.

Every visible fixture that looks lit has a real light under it (spot / area), so walls show falloff and the floor shows soft pools. Interiors bake an irradiance volume per scene/preset for occlusion-aware bounce light.
