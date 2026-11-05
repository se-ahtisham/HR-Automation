# Templates: email templates and the call script. Each save makes a new version.
import streamlit as st

from components import load_page_css, page_header, pill

load_page_css(__file__)
page_header("Templates", "Edit the emails and the call script. Every save gets a new version number.", section="Manage")

# The templates the app needs. Their text is written here by HR and saved in the database later
TEMPLATES = {
    "Interview invite": {"version": 0, "text": ""},
    "Reschedule": {"version": 0, "text": ""},
    "Cancel": {"version": 0, "text": ""},
    "CV Match Score": {"version": 0, "text": ""},
    "Call script": {"version": 0, "text": ""},
}
TEMPLATE_VERSIONS = []

list_col, edit_col = st.columns([1, 2.4])

with list_col:
    picked = st.radio("Template", list(TEMPLATES.keys()), label_visibility="collapsed")

template = TEMPLATES[picked]

with edit_col:
    with st.container(key="card-editor"):
        st.html(f'<div class="editor-top"><h3>{picked}</h3>{pill("Not saved yet", "gray") if template["version"] == 0 else pill("Version " + str(template["version"]), "violet")}</div>')
        st.text_area("Text", value=template["text"], height=280, key=f"text_{picked}",
                     placeholder="Write the text here. Use the blanks below, like {name} and {job}.")
        st.html('<p class="blanks">Blanks you can use: <code>{name}</code> <code>{job}</code> '
                '<code>{date}</code> <code>{time}</code> <code>{time_zone}</code> <code>{score}</code></p>')
        col1, col2, _ = st.columns([1.3, 1, 2])
        if col1.button("Save new version", type="primary", icon=":material/save:", width="stretch"):
            st.toast("MOCK: not saved yet.", icon=":material/save:")
        col2.button("Preview", icon=":material/visibility:", width="stretch")

    with st.container(key="card-versions"):
        st.html('<p class="section-title">Version history</p>')
        rows = "".join(
            f'<li><b>v{v["version"]}</b> · {v["change"]} <span>{v["by"]}, {v["date"]}</span></li>'
            for v in TEMPLATE_VERSIONS
        )
        st.html(f'<ul class="versions">{rows}</ul>' if rows else '<p class="nothing">No versions saved yet.</p>')
