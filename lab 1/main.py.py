
import tkinter as tk
from tkinter import messagebox, colorchooser
import colorsys
def rgb_to_cmyk(r, g, b):
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    k = 1 - max(r_, g_, b_)
    if k == 1:
        return 0.0, 0.0, 0.0, 1.0
    c = (1 - r_ - k) / (1 - k)
    m = (1 - g_ - k) / (1 - k)
    y = (1 - b_ - k) / (1 - k)
    return c, m, y, k

def cmyk_to_rgb(c, m, y, k):
    r = int(255 * (1 - c) * (1 - k))
    g = int(255 * (1 - m) * (1 - k))
    b = int(255 * (1 - y) * (1 - k))
    return r, g, b
def rgb_to_hsv(r, g, b):
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

def hsv_to_rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)
def apply_color(r, g, b):
    c, m, y, k = rgb_to_cmyk(r, g, b)
    c_scale.set(c); m_scale.set(m); y_scale.set(y); k_scale.set(k)
    cmyk_label.config(text=f"CMYK: {c:.2f}, {m:.2f}, {y:.2f}, {k:.2f}")
    h, s, v = rgb_to_hsv(r, g, b)
    h_deg = h * 360
    h_scale.set(h_deg); s_scale.set(s); v_scale.set(v)
    hsv_label.config(text=f"HSV: {h_deg:.0f}, {s:.2f}, {v:.2f}")
    r_scale.set(r); g_scale.set(g); b_scale.set(b)
    rgb_label.config(text=f"RGB: {r}, {g}, {b}")
    color_display.config(bg=f'#{r:02x}{g:02x}{b:02x}')
def update_from_rgb(_=None):
    r, g, b = r_scale.get(), g_scale.get(), b_scale.get()
    apply_color(r, g, b)

def update_from_cmyk(_=None):
    c, m, y_, k = c_scale.get(), m_scale.get(), y_scale.get(), k_scale.get()
    r, g, b = cmyk_to_rgb(c, m, y_, k)
    apply_color(r, g, b)

def update_from_hsv(_=None):
    h_deg, s, v = h_scale.get(), s_scale.get(), v_scale.get()
    r, g, b = hsv_to_rgb(h_deg / 360.0, s, v)
    apply_color(r, g, b)

def choose_color():
    col = colorchooser.askcolor(title="Choose color")[0]
    if col:
        r, g, b = map(int, col)
        apply_color(r, g, b)

root = tk.Tk()
root.title("Color Model Converter")
rgb_label = tk.Label(root, text="RGB: 0, 0, 0")
rgb_label.pack(pady=(10, 0))

r_scale = tk.Scale(
    root, from_=0, to=255, orient="horizontal",
    label="R", command=update_from_rgb
)
g_scale = tk.Scale(
    root, from_=0, to=255, orient="horizontal",
    label="G", command=update_from_rgb
)
b_scale = tk.Scale(
    root, from_=0, to=255, orient="horizontal",
    label="B", command=update_from_rgb
)
r_scale.pack(fill="x", padx=10)
g_scale.pack(fill="x", padx=10)
b_scale.pack(fill="x", padx=10)

cmyk_label = tk.Label(root, text="CMYK: 0.00, 0.00, 0.00, 1.00")
cmyk_label.pack(pady=(10, 0))
c_scale = tk.Scale(
    root, from_=0, to=1, resolution=0.01, orient="horizontal",
    label="C", command=update_from_cmyk
)
m_scale = tk.Scale(
    root, from_=0, to=1, resolution=0.01, orient="horizontal",
    label="M", command=update_from_cmyk
)
y_scale = tk.Scale(
    root, from_=0, to=1, resolution=0.01, orient="horizontal",
    label="Y", command=update_from_cmyk
)
k_scale = tk.Scale(
    root, from_=0, to=1, resolution=0.01, orient="horizontal",
    label="K", command=update_from_cmyk
)
c_scale.pack(fill="x", padx=10)
m_scale.pack(fill="x", padx=10)
y_scale.pack(fill="x", padx=10)
k_scale.pack(fill="x", padx=10)
hsv_label = tk.Label(root, text="HSV: 0, 0.00, 0.00")
hsv_label.pack(pady=(10, 0))
h_scale = tk.Scale(
    root, from_=0, to=360, resolution=1, orient="horizontal",
    label="H\u00B0", command=update_from_hsv
)
s_scale = tk.Scale(
    root, from_=0, to=1, resolution=0.01, orient="horizontal",
    label="S", command=update_from_hsv
)
v_scale = tk.Scale(
    root, from_=0, to=1, resolution=0.01, orient="horizontal",
    label="V", command=update_from_hsv
)
h_scale.pack(fill="x", padx=10)
s_scale.pack(fill="x", padx=10)
v_scale.pack(fill="x", padx=10)
choose_btn = tk.Button(root, text="Choose Color", command=choose_color)
choose_btn.pack(pady=(10, 0))
color_display = tk.Label(
    root, text="Color Display", width=20, height=5, bg="#000000"
)
color_display.pack(pady=(10, 20))
apply_color(0, 0, 0)

root.mainloop()

