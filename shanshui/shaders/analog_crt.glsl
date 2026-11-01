#ifdef GL_ES
precision mediump float;
precision mediump int;
#endif

#define PROCESSING_TEXTURE_SHADER

uniform sampler2D texture;
uniform vec2 texOffset;
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_bloom_intensity;
uniform float u_scanline_density;

varying vec4 vertColor;
varying vec4 vertTexCoord;

float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

void main() {
    vec2 uv = vertTexCoord.st;

    // Subtle CRT barrel curvature
    vec2 crtUV = uv * 2.0 - 1.0;
    vec2 offset = crtUV.yx / vec2(32.0, 32.0);
    crtUV += crtUV * offset * offset;
    vec2 screenUV = crtUV * 0.5 + 0.5;

    // Check boundary for bezel darkening
    if (screenUV.x < 0.0 || screenUV.x > 1.0 || screenUV.y < 0.0 || screenUV.y > 1.0) {
        gl_FragColor = vec4(0.04, 0.04, 0.04, 1.0);
        return;
    }

    // Chromatic aberration on phosphor edges
    float caOffset = 0.0015;
    float r = texture2D(texture, screenUV + vec2(caOffset, 0.0)).r;
    float g = texture2D(texture, screenUV).g;
    float b = texture2D(texture, screenUV - vec2(caOffset, 0.0)).b;
    vec3 col = vec3(r, g, b);

    // Phosphor bloom: blur bright elements (sun, seal, mountain crests)
    vec3 bloom = vec3(0.0);
    float bloomRadius = 2.5;
    for (int x = -2; x <= 2; x++) {
        for (int y = -2; y <= 2; y++) {
            vec2 off = vec2(float(x), float(y)) * texOffset * bloomRadius;
            vec3 s = texture2D(texture, screenUV + off).rgb;
            bloom += s * 0.04;
        }
    }
    col = mix(col, col + bloom * u_bloom_intensity, 0.4);

    // CRT Scanlines
    float scanline = sin(screenUV.y * u_resolution.y * u_scanline_density * 3.14159) * 0.06;
    col -= scanline;

    // Aperture grille RGB phosphor mask
    float subpixel = mod(screenUV.x * u_resolution.x, 3.0);
    if (subpixel < 1.0) {
        col.gb *= 0.94;
    } else if (subpixel < 2.0) {
        col.rb *= 0.94;
    } else {
        col.rg *= 0.94;
    }

    // Analog CRT film grain
    float grain = (hash(screenUV * 100.0 + fract(u_time * 0.01)) - 0.5) * 0.035;
    col += grain;

    // Vignette falloff toward edges
    float vignette = screenUV.x * screenUV.y * (1.0 - screenUV.x) * (1.0 - screenUV.y);
    vignette = clamp(pow(16.0 * vignette, 0.25), 0.0, 1.0);
    col *= vignette;

    gl_FragColor = vec4(col, 1.0);
}
