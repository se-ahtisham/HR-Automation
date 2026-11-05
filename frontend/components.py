# Small helpers that every page uses: load CSS and draw small HTML pieces
import base64
from pathlib import Path

import streamlit as st

FRONTEND = Path(__file__).parent

# Each status gets a color name. The colors live in base.css
STATUS_COLORS = {
    "Resume Received": "gray",
    "Scored (HR Review)": "amber",
    "Approved for Screening": "blue",
    "Screening Pending": "blue",
    "Screening Completed (HR Review)": "amber",
    "Approved for Interview": "green",
    "Interview Proposed": "violet",
    "Interview Scheduled": "green",
    "Needs Manual Review": "red",
    "Closed": "gray",
}

# Soft colors for avatars. Each name always gets the same color
AVATAR_COLORS = [
    "linear-gradient(135deg, #A78BFA, #6C5CE7)",
    "linear-gradient(135deg, #F9A8D4, #EC4899)",
    "linear-gradient(135deg, #67E8F9, #0EA5E9)",
    "linear-gradient(135deg, #FDBA74, #F97316)",
    "linear-gradient(135deg, #86EFAC, #22C55E)",
]


# Puts a CSS file on the page. st.html with only a <style> tag adds no empty space
def add_css(css_path):
    css = Path(css_path).read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


# Loads the CSS file that sits next to a page file: login.py -> login.css
def load_page_css(page_file):
    add_css(Path(page_file).with_suffix(".css"))


# st.html removes <svg> tags for safety, so I show a drawing as an <img> with the SVG inside it
def svg_image(svg, css_class=""):
    data = base64.b64encode(svg.encode("utf-8")).decode()
    return f'<img class="{css_class}" src="data:image/svg+xml;base64,{data}" alt="">'


# A line icon from Material Symbols. Names: fonts.google.com/icons (for example "work", "lock")
def icon(name, css_class=""):
    return f'<span class="mi {css_class}">{name}</span>'


# A card title with an icon in a small colored square
def card_title(name, text, color=""):
    return f'<p class="section-title"><span class="mi mi-box {color}">{name}</span>{text}</p>'


# The title at the top of each page, with a small "where am I" line above it
def page_header(title, subtitle, section="", tag=""):
    tag_html = f'<span class="mock-tag">{tag}</span>' if tag else ""
    section_html = f'<p class="crumb">{section}</p>' if section else ""
    st.html(f"""
        <div class="page-header">
            {section_html}
            <h1>{title} {tag_html}</h1>
            <p class="subtitle">{subtitle}</p>
        </div>
    """)


# A round picture with the first letters of a name. Blind Mode shows a lock
def avatar(name, size="md", hidden=False):
    if hidden:
        return f'<div class="avatar avatar-{size} avatar-hidden">{icon("lock")}</div>'
    first_letters = "".join(word[0] for word in name.split()[:2]).upper()
    color = AVATAR_COLORS[sum(ord(letter) for letter in name) % len(AVATAR_COLORS)]
    return f'<div class="avatar avatar-{size}" style="background:{color}">{first_letters}</div>'


# A colored pill for a candidate status
def status_badge(status):
    color = STATUS_COLORS.get(status, "gray")
    return f'<span class="badge badge-{color}">{status}</span>'


# A plain colored pill, for things like "Must-have"
def pill(text, color="gray"):
    return f'<span class="badge badge-{color}">{text}</span>'


# A soft gray tag, like the skill tags on a card
def chip(text, kind=""):
    return f'<span class="chip {kind}">{text}</span>'


# The round score circle. conic-gradient fills the ring up to the score
def score_ring(score, size="big"):
    return f"""
        <div class="score-ring score-ring-{size}"
             style="background: conic-gradient({score_color(score)} {score * 3.6}deg, var(--ring-empty) 0deg);">
            <div class="score-ring-inner"><b>{score}</b><span>/ 100</span></div>
        </div>
    """


# A half circle gauge. The arc is 251 long, so the score fills score% of it
def score_gauge(score, label="Match score"):
    filled = score / 100 * 251.3
    svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 115">
                <defs>
                    <linearGradient id="gauge-fill" x1="0" x2="1">
                        <stop offset="0" stop-color="#A78BFA"/>
                        <stop offset="1" stop-color="#6C5CE7"/>
                    </linearGradient>
                </defs>
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#ECEBFB" stroke-width="16" stroke-linecap="round"/>
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="url(#gauge-fill)" stroke-width="16"
                      stroke-linecap="round" stroke-dasharray="{filled} 251.3"/>
            </svg>
    """
    return f"""
        <div class="gauge">
            {svg_image(svg)}
            <div class="gauge-text">
                <small>{label}</small>
                <b>{score}<span>/100</span></b>
            </div>
        </div>
    """


def score_color(score):
    if score >= 70:
        return "var(--green)"
    if score >= 50:
        return "var(--amber)"
    return "var(--red)"


# 5 small dots for a 0 to 5 level. Filled dots = the level
def level_dots(level, required=0):
    dots = ""
    for number in range(1, 6):
        filled = "filled" if number <= level else ""
        needed = "needed" if number == required else ""
        dots += f'<span class="dot {filled} {needed}"></span>'
    return f'<span class="dots">{dots}</span>'


# A thin bar for a part score from 0 to 5
def part_bar(name, score, weight):
    percent = score / 5 * 100
    return f"""
        <div class="part-row">
            <div class="part-name">{name} <span>{weight}%</span></div>
            <div class="part-track"><div class="part-fill" style="width:{percent}%"></div></div>
            <div class="part-score">{score}/5</div>
        </div>
    """


# A pastel tile with an icon and a number, like the colored boxes on top of the dashboard
def stat_tile(label, value, icon, color):
    return f"""
        <div class="tile tile-{color}">
            <div class="tile-icon"><span class="mi">{icon}</span></div>
            <div>
                <p class="tile-value">{value}</p>
                <p class="tile-label">{label}</p>
            </div>
        </div>
    """


# A friendly box for a list with nothing in it yet
def empty_state(icon_name, title, text):
    return f"""
        <div class="empty-box">
            <span class="mi mi-box">{icon_name}</span>
            <p class="empty-title">{title}</p>
            <p class="empty-text">{text}</p>
        </div>
    """


# A list of short lines with an icon in front
def icon_list(items, icon):
    rows = "".join(f'<li><span class="mi">{icon}</span>{item}</li>' for item in items)
    return f'<ul class="icon-list">{rows}</ul>'
