import streamlit as st

def show_sidebar():
    with st.sidebar:
        # 1. Title/Header (like LilyAI in the image)
        st.markdown(f'<p style="color: #FF4B4B; font-size: 30px; font-weight: bold;">👤 {st.session_state.user_name}\'s Lily</p>', unsafe_allow_html=True)
        st.write("Your caring companion")
        st.divider()

        # 2. Navigation Options using Radio Buttons
        # We style this to look like the buttons in the third image
        page_selection = st.radio(
            "Go to:",
            ["💬 Talk to Lily", "📖 Our Memories", "☀️ Daily Guide", "🔒 My Privacy"],
            index=0, # Default page is the Chat
            key="nav_radio"
        )
        
        st.divider()
        # 3. Quick Actions / Privacy Badge
        if st.button(" View Privacy Shield"):
            st.info("### 🛡️ 100% Local AI\nYour data stays on this computer.")
            
        if st.button("🚪 Logout"):
            st.session_state.user_name = None
            st.rerun()

    # We return the user's selection to the main app
    return page_selection