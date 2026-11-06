"""Matplotlib font setup: use a Korean-capable font when one is installed."""
import matplotlib
from matplotlib import font_manager

for name in ("NanumGothic", "Noto Sans CJK KR", "Malgun Gothic", "AppleGothic"):
    if any(f.name == name for f in font_manager.fontManager.ttflist):
        matplotlib.rcParams["font.family"] = [name, "DejaVu Sans"]  # per-glyph fallback (µ, −, ²)
        break
matplotlib.rcParams["axes.unicode_minus"] = False
