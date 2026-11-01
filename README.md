# Shan Shui (山水) - Python / Py5 Procedural Landscape Art Engine

A modern, GPU-accelerated Python port of **Lingdong Huang's** acclaimed procedural Chinese landscape generation system, implemented in **py5** (Processing for Python) with OpenGL P2D hardware acceleration, retained `PShape` VBO caching, and custom GLSL post-processing shaders.

---

## 1. Provenance & Original Repository Reference

* **Original Work**: [*Shan, Shui* (山水)](https://github.com/Lingdong-/shanshui) by **Lingdong Huang** (黄凌东)
* **Original Repository**: [https://github.com/Lingdong-/shanshui](https://github.com/Lingdong-/shanshui)
* **Original Live Demonstration**: [https://lingdong-.github.io/shanshui/](https://lingdong-.github.io/shanshui/)
* **Original Technology**: Single-file HTML5/JavaScript application (`shanshui/index.html`) generating dynamic SVG vector polylines via procedural Perlin noise, polyline subdivision, and ear-clipping polygon triangulation.
* **Original License**: MIT License (Copyright (c) 2018 Lingdong Huang).

---

## 2. Project Architecture & Modularization

The original 4,360+ line monolithic JavaScript file (`index.html`) has been systematically decoupled and refactored into a high-cohesion, clean Python package consisting of 7 distinct domain modules:

```
ShanShuiPy5/
├── .idea/                      # PyCharm project workspace metadata
├── shanshui/                   # Core Python package
│   ├── __init__.py             # Package exports and public API
│   ├── main.py                 # Py5 loop, camera scrolling, GPU layer orchestration & HUD
│   ├── utils.py                # PRNG, 3D Perlin noise, PolyTools, brush stroke ribbon generator
│   ├── terrain.py              # Mountain ridge synthesis, cunfa hatching, plateaus, water ripples, planner
│   ├── flora.py                # 8 tree archetypes (recursive pines, weeping willows, deciduous trees)
│   ├── architecture.py         # Multi-tiered pagodas, pavilions, arched bridges, fences, huts, sampans
│   ├── fauna.py                # Articulated human travelers, fishermen, and soaring bird flocks
│   ├── atmosphere.py           # Rice paper texture, misty ink wash bands, crimson sun, calligraphy seal
│   ├── index.html              # Original reference engine benchmark
│   └── shaders/
│       ├── paper_texture.glsl  # Real-time GPU rice paper fiber diffusion & ink bleed
│       └── analog_crt.glsl     # Continuum Transmissions phosphor CRT scanlines & bloom
├── requirements.txt            # Python dependencies (py5, Pillow, numpy)
├── run.py                      # Standalone launcher script
└── README.md                   # Project overview & documentation
```

### Module Breakdown

1. **`shanshui/main.py`**
   - Implements the py5 lifecycle (`settings`, `setup`, `draw`, keyboard & mouse event handlers).
   - Infinite horizontal scrolling with dynamic chunk streaming and camera interpolation.
   - Retained GPU caching via `PShape` VBOs (compiles thousands of procedural vector primitives into grouped GPU vertex buffers).
   - Real-time GLSL shader filter passes (`paper_texture.glsl` and `analog_crt.glsl`).
   - Retro-futuristic classified HUD matching the Continuum Transmissions aesthetic with live FPS, telemetry, and seed indicators.

2. **`shanshui/utils.py`**
   - **PRNG & 3D Perlin Noise**: Custom permutation-table Perlin noise matching the JavaScript `Noise.noise()` algorithm identically.
   - **PolyTools**: Jordan curve ray-casting point-in-polygon tests (`pt_in_poly`), polyline intersection, ear-clipping triangulation with area constraints (`triangulate`), polygon shattering, and midpoint smoothing.
   - **`stroke()` Brush Stroke Generator**: Calligraphic brush simulation modulating width with noise to replicate dry-brush split bristles (*feibai* 飞白) and normal displacement.
   - **`blob()`**: Organic droplet/leaf cluster generator with loop noise perimeter.
   - **Java/JBR Runtime Auto-configuration**: Automatic detection and configuration of JetBrains Runtime (`JBR` Java 17/25) for seamless py5 execution without manual `JAVA_HOME` configuration.

3. **`shanshui/terrain.py`**
   - **`mountain()`**: Layered mountain ridges using sinusoidal profile modulation, Perlin perturbation, white backing occlusion hulls, rim foliage, and foot mist contours.
   - **`texture()`**: Traditional Chinese brushwork *Cunfa* (皴法 - texture strokes) generated along elevation gradients.
   - **`flat_mount()`**: Terraced table mountains and cliff plateaus with boundary validation.
   - **`dist_mount()`**: Atmospheric distant mountain silhouettes with seamless contour-sharing ear-clipped triangulation.
   - **`water()`**: Horizontal calligraphic wave strokes clustering beneath mountain bases.
   - **`MountPlanner`**: Procedural spatial planner distributing terrain features and architectural landmarks.

4. **`shanshui/flora.py`**
   - **`tree01`**: Mountain conifer / spruce with stepped triangular needle tiers.
   - **`tree02`**: Foliage cluster droplets along ridge lines and cliff plateaus.
   - **`tree03`**: Curved mountain leaning pine tree with foliage clusters.
   - **`tree04`**: Majestic fractal pine tree with bark cross-hatchings and radial pine needle bundles.
   - **`tree05`**: Bare winter deciduous tree with organic branching.
   - **`tree06`**: Heavy leafy willow / broadleaf tree.
   - **`tree07`**: Clustered bamboo groves.
   - **`tree08`**: Gnarled ancient cliff pine.

5. **`shanshui/architecture.py`**
   - **`arch01`**: Classic Chinese arched stone bridge with balustrades and water reflections.
   - **`arch02`**: Multi-story pavilion / cliffside gazebo with curved swept-eave roofs.
   - **`arch03`**: Towering 5- to 7-story Buddhist pagoda with decorative corbel brackets.
   - **`arch04`**: Tiered lakeside observation tower.
   - **`boat01`**: Traditional sampan / fishing boat with canopy and steering oar.
   - **`transmission_tower01`**: Futuristic Continuum Transmissions high-voltage lattice power tower easter egg.
   - Building blocks: `hut`, `box`, `deco`, `rail`, `roof`, `pagroof`.

6. **`shanshui/fauna.py`**
   - **`man()`**: Articulated human figure with kinematic limbs, robes, and walking stick.
   - **`traveler()`**: Wanderer with conical bamboo hat (`hat01`/`hat02`) and walking staff.
   - **`fisherman()`**: Angler seated on a boat holding a slender fishing rod with hanging line.
   - **`bird_flock()`**: Flying cranes / geese soaring across the sky with subtle parallax.

7. **`shanshui/atmosphere.py`**
   - **`red_sun()`**: Soft cinnabar sun rendered with concentric gradient wash rings.
   - **`calligraphy_seal()`**: Traditional red cinnabar artist seal (*Yinzhang* 印章) in both Yin (carved character) and Yang (embossed character) styles.
   - **`mist_band()`**: Atmospheric ink wash mist rolling across mountain valleys.
   - **`generate_paper_texture()`**: Procedural rice paper texture with visible mulberry fibers and ink absorption bleeding.

---

## 3. GPU Hardware Acceleration & Shaders

To overcome the performance limits of interpreting thousands of procedural polylines per frame:

1. **Retained GPU PShape Grouping**:
   Vector primitives are assembled once upon chunk generation into hardware-accelerated OpenGL Vertex Buffer Objects (`PShape.GROUP`). Drawing a mountain requires a single GPU `shape()` call rather than thousands of individual CPU draw calls.

2. **Real-Time GLSL Post-Processing**:
   - **Mode 1 (`paper_texture.glsl`)**: Simulates traditional Xuan rice paper (宣纸) with procedural fiber grain, uneven fiber clumps, and pigment absorption diffusion.
   - **Mode 2 (`analog_crt.glsl`)**: Continuum Transmissions surveillance aesthetic with phosphor bloom, subtle scanlines, RGB chromatic aberration, and vignette.
   - **Mode 3**: Raw high-precision vector rendering without post-processing.

---

## 4. Key Engineering Fixes & Algorithmic Refinements

During the Python/py5 reproduction, three subtle visual bugs present in early iterations were analyzed and resolved:

1. **Distant Mountain Popping / Premature Culling**:
   - *Problem*: Viewport culling checked only `chunk.x`. Distant mountain ranges span up to 2000px horizontally; when `chunk.x` crossed the camera margin, the entire 2000px range vanished abruptly.
   - *Fix*: Added dynamic horizontal bounding box calculation (`min_x`, `max_x`) across all primitives in `LandscapeChunk`. Both viewport culling and chunk garbage collection now evaluate whether `[min_x, max_x]` overlaps the view boundaries.

2. **Regular Triangular Cuts in Distant Mountains**:
   - *Problem*: In `dist_mount`, integer division `seg // 2 + 1` caused the bottom contour to terminate before the section boundary, leaving a 10px triangular hole showing the background at the bottom of every segment.
   - *Fix*: Restructured section generation so the top contour advances from `k_start` to `k_end` and the bottom contour reverses from `k_end` to `k_start`. Adjacent sections now share the exact seam `(top(k_end) <-> bot(k_end))`.

3. **Floating Trees & Droplets**:
   - *Problem*: Standard Box-Muller Gaussian ($\sigma=1.0$, unbounded) was used instead of Lingdong Huang's bounded rejection-sampled Gaussian ($[-1, 1]$, $\sigma \approx 0.288$), blowing foliage droplets 40–80px into the air above ridges. Unconstrained plateau foliage also drifted off cliff edges.
   - *Fix*: Implemented the exact bounded rejection-sampled Gaussian, enforced `PolyTools.pt_in_poly` boundaries on plateaus, and removed forced shape closure on open stroke polylines.

---

## 5. Getting Started & Controls

### Prerequisites
- **Python 3.14** (Required: `jpype1` provides pre-built binary wheels up to Python 3.14; Python 3.15+ lacks wheels on PyPI and fails building wheels without MSVC C++ Build Tools)
- Java 17+ or JetBrains Runtime (`JBR`)
- Modern GPU supporting OpenGL 3.3+ (e.g. NVIDIA RTX series)

### Installation

Use the Python 3.14 launcher to create the virtual environment:

```bash
# Ensure Python 3.14 is used to avoid JPype1 C++ wheel compilation errors
py -3.14 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Running
```bash
python run.py
```
*(or run `python -m shanshui.main`)*

### Interactive Controls
| Key / Input | Action |
|---|---|
| **SPACE** | Toggle automatic camera scrolling |
| **Mouse Drag** / **Arrows** | Pan camera left / right manually |
| **Mouse Wheel** | Quick scroll through landscape |
| **1** | Switch to **Rice Paper & Ink Bleed** shader mode |
| **2** | Switch to **Analog CRT & Bloom** shader mode |
| **3** | Switch to **Raw High-Precision Vector** mode |
| **R** | Re-seed and generate a brand new procedural universe |
| **S** | Save high-resolution PNG screenshot to disk |
| **H** | Toggle telemetry HUD display |
