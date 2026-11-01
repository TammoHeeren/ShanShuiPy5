#ifdef GL_ES
precision mediump float;
precision mediump int;
#endif

#define PROCESSING_TEXTURE_SHADER

uniform sampler2D texture;
uniform vec2 texOffset;
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_grain_strength;

varying vec4 vertColor;
varying vec4 vertTexCoord;

// Simplex / Hash noise functions for procedural fiber simulation
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// Multi-octave fractional Brownian motion for fibrous rice paper
float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    vec2 shift = vec2(100.0);
    mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.50));
    for (int i = 0; i < 4; ++i) {
        v += a * noise(p);
        p = rot * p * 2.0 + shift;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = vertTexCoord.st;
    vec4 sceneColor = texture2D(texture, uv);

    // Procedural rice paper texture coordinate
    vec2 pCoord = uv * u_resolution * 0.08;

    // Organic fibers: stretched noise in directional strands
    float fiber1 = noise(vec2(pCoord.x * 0.4, pCoord.y * 3.0));
    float fiber2 = noise(vec2(pCoord.x * 3.5, pCoord.y * 0.5));
    float paperGrain = fbm(pCoord * 0.5) * 0.7 + (fiber1 * fiber2) * 0.3;

    // Subtle fine speckle grain
    float speckle = hash(uv * u_resolution + fract(u_time * 0.0001)) * 0.06;

    // Warm cream paper tone modulation
    float paperMod = 1.0 - (paperGrain * 0.08 + speckle) * u_grain_strength;
    vec3 paperTint = vec3(1.0, 0.985, 0.94);

    // Subtle ink bleed into surrounding paper fibers
    // Sample neighbors to detect high-contrast ink edges
    vec4 nUp = texture2D(texture, uv + vec2(0.0, texOffset.y * 1.5));
    vec4 nDn = texture2D(texture, uv - vec2(0.0, texOffset.y * 1.5));
    vec4 nLt = texture2D(texture, uv - vec2(texOffset.x * 1.5, 0.0));
    vec4 nRt = texture2D(texture, uv + vec2(texOffset.x * 1.5, 0.0));
    vec4 avgNeighbor = (nUp + nDn + nLt + nRt) * 0.25;

    // Soft ink diffusion along paper grain
    vec3 diffusedInk = mix(sceneColor.rgb, avgNeighbor.rgb, paperGrain * 0.18);

    // Blend diffused ink with the organic paper tone
    vec3 finalColor = diffusedInk * paperMod * paperTint;

    gl_FragColor = vec4(finalColor, sceneColor.a);
}
