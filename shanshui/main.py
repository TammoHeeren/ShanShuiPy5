"""
main.py - The Py5 loop, camera scrolling, and GPU-accelerated layer management
High-performance interactive reproduction of Lingdong Huang's Shan Shui for Py5,
leveraging OpenGL P2D hardware acceleration, PShape VBO caching, and real-time GLSL shaders.
"""

import math
import random
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure Java / JBR runtime is initialized before importing py5
from .utils import init_py5_runtime, set_seed
init_py5_runtime()

import py5
from PIL import Image

from .utils import PolyPrimitive
from .terrain import mountain, flat_mount, dist_mount, water, MountPlanner
from .architecture import boat01
from .fauna import bird_flock
from .atmosphere import (
    generate_paper_texture, mist_band, red_sun, calligraphy_seal
)

# -----------------------------------------------------------------------------
# Chunk Data Structure with Retained GPU PShape Caching
# -----------------------------------------------------------------------------
class LandscapeChunk:
    """
    Represents a procedural scene element (mountain, flat plateau, distant peak, boat).
    Caches its vector primitives directly inside an OpenGL PShape group (VBO) on the GPU.
    """
    __slots__ = ("tag", "x", "y", "primitives", "shape_group", "min_x", "max_x")

    def __init__(self, tag: str, x: float, y: float, primitives: List[PolyPrimitive]):
        self.tag = tag
        self.x = x
        self.y = y
        self.primitives = primitives
        self.shape_group: Optional[py5.PShape] = None

        # Compute accurate horizontal bounding box across all vector primitives
        all_x = [pt[0] for prim in primitives for pt in prim.points]
        if all_x:
            self.min_x = min(all_x)
            self.max_x = max(all_x)
        else:
            self.min_x = x
            self.max_x = x

    def build_shape(self, g):
        """Compiles thousands of polygon primitives into a single hardware-accelerated PShape group."""
        grp = g.create_shape(g.GROUP)
        for prim in self.primitives:
            if not prim.points or len(prim.points) < 2:
                continue
            sh = g.create_shape()
            sh.begin_shape()
            if prim.fill_col[3] > 0:
                sh.fill(prim.fill_col[0], prim.fill_col[1], prim.fill_col[2], prim.fill_col[3])
            else:
                sh.no_fill()
            if prim.stroke_weight > 0 and prim.stroke_col[3] > 0:
                sh.stroke(prim.stroke_col[0], prim.stroke_col[1], prim.stroke_col[2], prim.stroke_col[3])
                sh.stroke_weight(prim.stroke_weight)
            else:
                sh.no_stroke()
            for pt in prim.points:
                sh.vertex(pt[0], pt[1])
            if prim.fill_col[3] > 0:
                sh.end_shape(g.CLOSE)
            else:
                sh.end_shape()
            grp.add_child(sh)
        self.shape_group = grp

    def draw(self, g):
        """Renders the chunk via GPU VBO call."""
        if self.shape_group is None:
            self.build_shape(g)
        g.shape(self.shape_group)

# -----------------------------------------------------------------------------
# Global State
# -----------------------------------------------------------------------------
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
CHUNK_WIDTH = 512

class ShanShuiState:
    def __init__(self):
        self.seed = 1234
        self.camera_x = 0.0
        self.target_camera_x = 0.0
        self.auto_scroll = True
        self.scroll_speed = 1.2
        self.xmin = 0.0
        self.xmax = 0.0
        self.planner = MountPlanner()
        self.chunks: List[LandscapeChunk] = []
        self.show_hud = True
        self.is_dragging = False
        self.last_mouse_x = 0.0
        self.birds: List[PolyPrimitive] = []
        self.sun_prims: List[PolyPrimitive] = []
        self.seal_prims: List[PolyPrimitive] = []
        self.sun_shape: Optional[py5.PShape] = None
        self.seal_shape: Optional[py5.PShape] = None
        self.birds_shape: Optional[py5.PShape] = None
        
        # Shader management
        self.shader_mode = 1  # 1: Rice Paper, 2: Continuum CRT, 3: Raw Vector        self.paper_shader: Optional[py5.Py5Shader] = None
        self.crt_shader: Optional[py5.Py5Shader] = None

state = ShanShuiState()

# -----------------------------------------------------------------------------
# Chunk Generation & Painter's Sorting
# -----------------------------------------------------------------------------
def load_chunk_plan(plan_items: List[Dict[str, Any]]):
    """Instantiates procedural geometry for planned items and inserts in ascending Y order."""
    for item in plan_items:
        tag = item["tag"]
        ix = item["x"]
        iy = item["y"]
        prims: List[PolyPrimitive] = []

        if tag == "mount":
            prims.extend(mountain(ix, iy, seed=random.random() * 100.0))
            # Companion water rippling below mountain foot
            water_chunk = LandscapeChunk(
                "water", ix, iy - 10000.0,
                water(ix, iy, seed=random.random() * 100.0)
            )
            _insert_chunk(water_chunk)
        elif tag == "flatmount":
            prims.extend(flat_mount(
                ix, iy, seed=random.random() * math.pi * 2.0,
                wid=600.0 + random.random() * 400.0, hei=100.0,
                cho=0.5 + random.random() * 0.2
            ))
        elif tag == "distmount":
            prims.extend(dist_mount(
                ix, iy, seed=random.random() * 100.0,
                hei=150.0, len_=random.choice([500.0, 1000.0, 1500.0])
            ))
        elif tag == "boat":
            sca = iy / 800.0
            prims.extend(boat01(
                ix, iy, seed=random.random(),
                sca=sca, fli=random.choice([True, False])
            ))

        chunk = LandscapeChunk(tag, ix, iy, prims)
        _insert_chunk(chunk)

def _insert_chunk(nch: LandscapeChunk):
    """Inserts chunk sorted by Y-coordinate (Painter's algorithm: background first)."""
    if not state.chunks:
        state.chunks.append(nch)
        return

    if nch.y <= state.chunks[0].y:
        state.chunks.insert(0, nch)
        return
    if nch.y >= state.chunks[-1].y:
        state.chunks.append(nch)
        return

    for j in range(len(state.chunks) - 1):
        if state.chunks[j].y <= nch.y <= state.chunks[j + 1].y:
            state.chunks.insert(j + 1, nch)
            return

    state.chunks.append(nch)

def update_chunks(left_x: float, right_x: float):
    """Dynamically loads procedural chunks as the camera pans horizontally."""
    while right_x > state.xmax - CHUNK_WIDTH:
        plan = state.planner.plan_chunk(state.xmax, state.xmax + CHUNK_WIDTH)
        state.xmax += CHUNK_WIDTH
        load_chunk_plan(plan)

    while left_x < state.xmin + CHUNK_WIDTH:
        plan = state.planner.plan_chunk(state.xmin - CHUNK_WIDTH, state.xmin)
        state.xmin -= CHUNK_WIDTH
        load_chunk_plan(plan)

    # Garbage-collect chunks situated far off-screen to preserve memory
    margin = 3500.0
    state.chunks = [c for c in state.chunks if c.max_x >= (left_x - margin) and c.min_x <= (right_x + margin)]

# -----------------------------------------------------------------------------
# Py5 Lifecycle (Hardware Accelerated with py5.P2D)
# -----------------------------------------------------------------------------
def settings():
    # Activate hardware-accelerated OpenGL 4.6 pipeline on the RTX 4070
    py5.size(WINDOW_WIDTH, WINDOW_HEIGHT, py5.P2D)
    py5.smooth(8)  # 8x MSAA hardware anti-aliasing

def setup():
    try:
        py5.window_title("Shan Shui (山水) - GPU Accelerated (OpenGL P2D / RTX 4070)")
    except Exception:
        pass
    set_seed(state.seed)

    # 1. Compile and link GLSL shaders
    shader_dir = Path(__file__).parent / "shaders"
    paper_path = shader_dir / "paper_texture.glsl"
    crt_path = shader_dir / "analog_crt.glsl"

    if paper_path.exists():
        try:
            state.paper_shader = py5.load_shader(str(paper_path))
            print("[ShanShui GPU] Compiled paper_texture.glsl successfully.")
        except Exception as e:
            print(f"[ShanShui GPU] Paper shader compile error: {e}")

    if crt_path.exists():
        try:
            state.crt_shader = py5.load_shader(str(crt_path))
            print("[ShanShui GPU] Compiled analog_crt.glsl successfully.")
        except Exception as e:
            print(f"[ShanShui GPU] CRT shader compile error: {e}")

    # 2. Celestial & Calligraphy Stamp Atmosphere
    state.sun_prims = red_sun(220, 180, radius=55.0)
    state.seal_prims = calligraphy_seal(WINDOW_WIDTH - 90, 80, size=52.0, style="yin")
    state.birds = bird_flock(500, 140, count=8, scale=0.9)

    # 3. Initial chunks around camera origin
    print("[ShanShui GPU] Planning initial landscape chunks...")
    state.xmin = -CHUNK_WIDTH
    state.xmax = CHUNK_WIDTH * 3
    initial_plan = state.planner.plan_chunk(state.xmin, state.xmax)
    load_chunk_plan(initial_plan)
    print(f"[ShanShui GPU] Loaded {len(state.chunks)} landscape features.")

def draw():
    # Smooth camera interpolation
    if state.auto_scroll and not state.is_dragging:
        state.target_camera_x += state.scroll_speed

    state.camera_x += (state.target_camera_x - state.camera_x) * 0.1

    # Update active chunks covering viewport
    update_chunks(state.camera_x - 500, state.camera_x + WINDOW_WIDTH + 500)

    # 1. Base parchment background
    py5.background(246, 243, 234)

    # 2. Fixed celestial elements
    for p in state.sun_prims:
        p.draw(py5)

    # 3. Drifting bird flock with subtle parallax
    py5.push_matrix()
    py5.translate(-state.camera_x * 0.35, 0)
    for p in state.birds:
        p.draw(py5)
    py5.pop_matrix()

    # 4. Landscape Chunks (Painter's algorithm: Y-sorted)
    py5.push_matrix()
    py5.translate(-state.camera_x, 0)

    # Viewport culling boundaries (robust against wide mountain spans)
    view_left = state.camera_x - 400
    view_right = state.camera_x + WINDOW_WIDTH + 400

    for chunk in state.chunks:
        if chunk.max_x >= view_left and chunk.min_x <= view_right:
            chunk.draw(py5)

    # Soft ink wash valley mist bands
    mist_prims = mist_band(state.camera_x - 200, 480, width=WINDOW_WIDTH + 400, height=110, seed=state.seed)
    for p in mist_prims:
        p.draw(py5)

    py5.pop_matrix()

    # 5. Calligraphy Seal (stamped on top of finished landscape artwork)
    for p in state.seal_prims:
        p.draw(py5)

    # 5. Apply Real-Time GLSL Shaders on the GPU
    if state.shader_mode == 1 and state.paper_shader:
        state.paper_shader.set("u_resolution", float(WINDOW_WIDTH), float(WINDOW_HEIGHT))
        state.paper_shader.set("u_time", float(py5.frame_count))
        state.paper_shader.set("u_grain_strength", 1.0)
        py5.apply_filter(state.paper_shader)
    elif state.shader_mode == 2 and state.crt_shader:
        state.crt_shader.set("u_resolution", float(WINDOW_WIDTH), float(WINDOW_HEIGHT))
        state.crt_shader.set("u_time", float(py5.frame_count))
        state.crt_shader.set("u_bloom_intensity", 0.6)
        state.crt_shader.set("u_scanline_density", 0.45)
        py5.apply_filter(state.crt_shader)

    # 6. On-Screen HUD & Telemetry (Rendered crisp on top of shader)
    if state.show_hud:
        draw_hud()

def draw_hud():
    """Renders retro-futuristic classified HUD matching Continuum Transmissions theme."""
    py5.no_stroke()
    py5.fill(15, 15, 15, 190)
    py5.rect(15, WINDOW_HEIGHT - 75, 540, 60, 4)

    # Phosphor green accent
    py5.fill(57, 255, 20)
    py5.text_size(12)

    shader_names = {1: "RICE PAPER & INK BLEED", 2: "ANALOG CRT & BLOOM", 3: "RAW VECTOR (NO SHADER)"}
    mode_name = shader_names.get(state.shader_mode, "CUSTOM")
    fps = int(py5.get_frame_rate())

    status_str = f"GPU: P2D (RTX 4070) | FPS: {fps} | MODE: {mode_name}"
    py5.text(status_str, 25, WINDOW_HEIGHT - 53)

    py5.fill(220, 220, 220)
    info_str = f"CAM X: {int(state.camera_x)}  |  FEATURES: {len(state.chunks)}  |  AUTO-SCROLL: {'ON' if state.auto_scroll else 'OFF'}"
    py5.text(info_str, 25, WINDOW_HEIGHT - 36)

    py5.fill(160, 160, 160)
    py5.text("1-3: Shader Mode | DRAG: Pan | SPACE: Auto-Scroll | R: Re-seed | S: Save | H: HUD", 25, WINDOW_HEIGHT - 20)

# -----------------------------------------------------------------------------
# User Input & Interaction Handlers
# -----------------------------------------------------------------------------
def mouse_pressed():
    state.is_dragging = True
    state.last_mouse_x = py5.mouse_x

def mouse_dragged():
    if state.is_dragging:
        dx = py5.mouse_x - state.last_mouse_x
        state.target_camera_x -= dx * 1.5
        state.last_mouse_x = py5.mouse_x

def mouse_released():
    state.is_dragging = False

def mouse_wheel(e):
    state.target_camera_x += e.get_count() * 40.0

def key_pressed():
    if py5.key == ' ':
        state.auto_scroll = not state.auto_scroll
    elif py5.key == '1':
        state.shader_mode = 1
        print("[ShanShui GPU] Switched to Mode 1: Rice Paper & Ink Bleed Shader")
    elif py5.key == '2':
        state.shader_mode = 2
        print("[ShanShui GPU] Switched to Mode 2: Continuum Transmissions Analog CRT & Bloom")
    elif py5.key == '3':
        state.shader_mode = 3
        print("[ShanShui GPU] Switched to Mode 3: Raw High-Precision Vector")
    elif py5.key in ('r', 'R'):
        state.seed = random.randint(1000, 999999)
        set_seed(state.seed)
        state.planner = MountPlanner()
        state.chunks.clear()
        state.camera_x = 0.0
        state.target_camera_x = 0.0
        state.xmin = -CHUNK_WIDTH
        state.xmax = CHUNK_WIDTH * 3
        state.seal_prims = calligraphy_seal(WINDOW_WIDTH - 90, 80, size=52.0, style="yin")
        plan = state.planner.plan_chunk(state.xmin, state.xmax)
        load_chunk_plan(plan)
    elif py5.key in ('s', 'S'):
        filename = f"shanshui_gpu_seed_{state.seed}_x_{int(state.camera_x)}.png"
        py5.save_frame(filename)
        print(f"[ShanShui GPU] Saved high-resolution artwork to {filename}")
    elif py5.key in ('h', 'H'):
        state.show_hud = not state.show_hud
    elif py5.key == py5.CODED:
        if py5.key_code == py5.LEFT:
            state.target_camera_x -= 100.0
        elif py5.key_code == py5.RIGHT:
            state.target_camera_x += 100.0

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def run(block: Optional[bool] = None):
    """Runs the Py5 Shan Shui sketch."""
    sketch_funcs = {
        "settings": settings,
        "setup": setup,
        "draw": draw,
        "mouse_pressed": mouse_pressed,
        "mouse_dragged": mouse_dragged,
        "mouse_released": mouse_released,
        "mouse_wheel": mouse_wheel,
        "key_pressed": key_pressed,
    }
    py5.run_sketch(block=block, sketch_functions=sketch_funcs)

if __name__ == "__main__":
    run()
