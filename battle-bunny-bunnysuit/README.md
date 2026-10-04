# Battle Bunny Bunnysuit Aurora (Rose Quartz)

`Battle-Bunny-Bunnysuit-RoseQuartz-v1_0_0.fantome` combines two mods:

- **Aurora Bunnysuit** (Abdomera): body mesh, skeleton with physics bones, texture and animations.
- **Battle Bunny Aurora (Rose Quartz) – Chroma VFX** (Sunshine Builder, v2.3.0): the rose/violet/silver
  VFX for skin 9 (66 VFX systems plus 51 particle textures, and the AuroraSpirits skin 9 bin).

**In game, pick the Battle Bunny Rose Quartz chroma.** That gives you the bunnysuit body with the Rose
Quartz Battle Bunny VFX. Base Aurora shows the plain bunnysuit.

## What changed

All files from both mods are included unchanged except `data/characters/aurora/skins/skin9.bin`. In its
`skinMeshProperties` and `skinAnimationProperties`:

| Field | Before (Battle Bunny) | After |
| --- | --- | --- |
| skeleton / simpleSkin | `Skin01/Aurora_Skin01.skl/.skn` | bunnysuit `Base/Aurora_Base.Aurora.skl/.skn` |
| texture | Rose Quartz body texture | bunnysuit texture |
| material, materialOverride | Iridescent body/hat materials, per-submesh textures | removed (they were made for the Battle Bunny UVs) |
| initialSubmeshToHide | `Critter` | `weapon` |
| animationGraphData | `Animations/Skin1` | `Animations/Skin0`, which plays the bunnysuit's re-baked animations and physics |

The VFX resolver, particles, spirits, SFX and VO are unchanged.

## Known limits

- **Body textures are still the bunnysuit's own.** The Battle Bunny / Rose Quartz outfit textures are
  only in the game's `Aurora.wad.client`. Neither mod includes them, so they can't be baked onto the
  bunnysuit UVs yet. With that file and the `Skin01` mesh, the same bake as
  `aurora-reaper-angelic/tools/merge/bake_outfit.py` would work.
- **The wand is hidden.** The bunnysuit wand needs the base game's weapon texture, and skin 9 doesn't
  reference it.
- **No Battle Bunny-specific animation events.** Effects triggered from the Battle Bunny animation graph,
  such as the dance or idle flourishes, don't play, because the body uses the base/bunnysuit graph.

## Rebuild

```
python tools/build.py aurora-bunnysuit.fantome "Battle_Bunny_Aurora_Rose_Quartz_V2_-_Chroma_VFX.fantome" out.fantome
```
Needs `pyritofile zstandard xxhash`. It reuses `../aurora-reaper-angelic/tools/wadlib.py`.
