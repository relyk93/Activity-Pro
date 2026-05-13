"""
Central theme configuration for ActivityPro.

To add a new theme: add a key to THEMES with the same set of variables.
app.py reads the active theme from session state and injects the CSS variables.
All page CSS uses var(--ap-*) so they update automatically.
"""

THEMES: dict[str, dict[str, str]] = {
    "light": {
        # Brand
        "--ap-primary":       "#0F766E",   # deep teal
        "--ap-primary-dark":  "#0D5F59",
        "--ap-primary-light": "#CCFBF1",
        "--ap-accent":        "#F59E0B",   # warm amber
        "--ap-accent-light":  "#FEF3C7",
        "--ap-danger":        "#E53E3E",
        "--ap-danger-light":  "#FFF5F5",

        # Surfaces
        "--ap-bg":            "#F8FAFC",
        "--ap-surface":       "#FFFFFF",
        "--ap-surface-2":     "#F1F5F9",
        "--ap-surface-3":     "#E2E8F0",

        # Text
        "--ap-text":          "#0F172A",
        "--ap-text-mid":      "#475569",
        "--ap-text-light":    "#94A3B8",

        # Borders & shadows
        "--ap-border":        "#E2E8F0",
        "--ap-shadow":        "rgba(15,23,42,0.08)",

        # Sidebar — rich teal in light mode so toggle is obvious vs dark mode's black
        "--ap-sidebar-bg":    "#0F766E",
        "--ap-sidebar-text":  "rgba(255,255,255,0.82)",
        "--ap-sidebar-hover": "rgba(255,255,255,0.12)",
        "--ap-sidebar-active":"#CCFBF1",
    },
    "dark": {
        # Brand
        "--ap-primary":       "#14B8A6",   # bright teal
        "--ap-primary-dark":  "#0D9488",
        "--ap-primary-light": "#134E4A",
        "--ap-accent":        "#FBBF24",   # bright amber
        "--ap-accent-light":  "#2D2000",
        "--ap-danger":        "#FC8181",
        "--ap-danger-light":  "#2D0000",

        # Surfaces
        "--ap-bg":            "#0F172A",
        "--ap-surface":       "#1E293B",
        "--ap-surface-2":     "#334155",
        "--ap-surface-3":     "#475569",

        # Text
        "--ap-text":          "#F1F5F9",
        "--ap-text-mid":      "#CBD5E1",
        "--ap-text-light":    "#94A3B8",

        # Borders & shadows
        "--ap-border":        "#334155",
        "--ap-shadow":        "rgba(0,0,0,0.4)",

        # Sidebar
        "--ap-sidebar-bg":    "#020617",
        "--ap-sidebar-text":  "#94A3B8",
        "--ap-sidebar-hover": "rgba(20,184,166,0.2)",
        "--ap-sidebar-active":"#14B8A6",
    },
}

DEFAULT_THEME = "light"


def get_css_variables(theme_name: str) -> str:
    """Return a <style> block injecting the theme as CSS custom properties."""
    palette = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    lines = "\n".join(f"    {k}: {v};" for k, v in palette.items())
    return f"<style>\n:root {{\n{lines}\n}}\n</style>"


def get_streamlit_config_colors(theme_name: str) -> dict:
    """Return Streamlit theme overrides for the active theme."""
    if theme_name == "dark":
        return {
            "primaryColor":           "#14B8A6",
            "backgroundColor":        "#0F172A",
            "secondaryBackgroundColor":"#1E293B",
            "textColor":              "#F1F5F9",
        }
    return {
        "primaryColor":           "#0F766E",
        "backgroundColor":        "#F8FAFC",
        "secondaryBackgroundColor":"#FFFFFF",
        "textColor":              "#0F172A",
    }
