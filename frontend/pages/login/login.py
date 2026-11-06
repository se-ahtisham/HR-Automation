# Login page: a form on the left, a picture on the right.
# It checks the email and password by calling my Python code directly (bcrypt, hr_accounts table).
import streamlit as st

from app.core.accounts import account_details, check_new_account, create_account, log_in
from components import FRONTEND, load_page_css, svg_image

load_page_css(__file__)

# The picture is its own file, so this page stays short
art = svg_image((FRONTEND / "pages" / "login" / "login_art.svg").read_text(encoding="utf-8"), "art-svg")

# "login" shows the Sign in form, "signup" shows the Create account form
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"


def switch_to(mode):
    st.session_state.auth_mode = mode
    st.rerun()


# One big card with 2 halves
with st.container(key="login-shell"):
    form_col, art_col = st.columns([1, 1.08], vertical_alignment="center", gap="large")

    # ---------- Left: the form ----------
    with form_col:
        with st.container(key="login-form"):
            # ===== Sign in =====
            if st.session_state.auth_mode == "login":
                st.html("""
                    <h1 class="hello">Hello Again!</h1>
                    <p class="hello-sub">Log in to review your candidates.</p>
                """)
                with st.form("login_form", border=False):
                    email = st.text_input("Email", placeholder="Email", label_visibility="collapsed")
                    password = st.text_input("Password", type="password", placeholder="Password",
                                             label_visibility="collapsed")
                    st.html('<p class="forgot">Forgot your password? Ask your HR team.</p>')
                    submitted = st.form_submit_button("Sign In", type="primary", width="stretch")

                if submitted:
                    account = log_in(email, password)
                    if account is None:
                        # The same message for a wrong email and a wrong password, so nobody can guess which emails exist
                        st.error("Email or password is wrong.", icon=":material/error:")
                    else:
                        st.session_state.user = account_details(account)
                        st.rerun()

                st.html('<div class="divider"><span>New to Nexora Hire?</span></div>')
                if st.button("Create an account", icon=":material/person_add:", width="stretch"):
                    switch_to("signup")

            # ===== Create account =====
            else:
                st.html("""
                    <h1 class="hello">Create account</h1>
                    <p class="hello-sub">Make a new HR account.</p>
                """)
                with st.form("signup_form", border=False):
                    name = st.text_input("Full name", placeholder="Full name", label_visibility="collapsed")
                    email = st.text_input("Email", placeholder="Work email", label_visibility="collapsed")
                    password = st.text_input("Password", type="password", placeholder="Password (8+ characters)",
                                             label_visibility="collapsed")
                    again = st.text_input("Password again", type="password", placeholder="Password again",
                                          label_visibility="collapsed")
                    submitted = st.form_submit_button("Create account", type="primary", width="stretch")

                if submitted:
                    problem = check_new_account(name, email, password)
                    if password != again:
                        st.error("The two passwords are not the same.", icon=":material/error:")
                    elif problem:
                        st.error(problem, icon=":material/error:")
                    else:
                        # Save the account, then log the new person in right away
                        account = create_account(name, email, password)
                        st.session_state.user = account_details(account)
                        st.session_state.auth_mode = "login"
                        st.rerun()

                st.html('<div class="divider"><span>Already have an account?</span></div>')
                if st.button("Back to sign in", icon=":material/login:", width="stretch"):
                    switch_to("login")

    # ---------- Right: the picture ----------
    with art_col:
        st.html(f"""
            <div class="art">
                {art}
                <div class="art-caption">
                    <p class="art-title">Finally, all your hiring in one place.</p>
                    <p class="art-sub">AI scores, calls and schedules. You make every decision.</p>
                    <div class="art-dots"><span class="on"></span><span></span><span></span></div>
                </div>
            </div>
        """)
