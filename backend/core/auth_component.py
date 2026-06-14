import streamlit.components.v1 as components
import streamlit as st

def get_auth_token_from_hash():
    # If we already have it in session state, return it
    if "auth0_token" in st.session_state:
        return st.session_state["auth0_token"]
        
    # Otherwise, inject JS to read the hash and send it back to Streamlit
    components.html("""
    <script>
        const hash = window.parent.location.hash;
        if (hash) {
            const params = new URLSearchParams(hash.substring(1));
            const token = params.get('access_token');
            if (token) {
                // Clear the hash so it doesn't stay in the URL
                window.parent.history.replaceState(null, null, ' ');
                // We could post message to streamlit, or simply redirect to ?token=...
                window.parent.location.href = "/?token=" + token;
            }
        }
    </script>
    """, height=0)
    
    # Check if we were redirected with ?token=...
    if "token" in st.query_params:
        token = st.query_params["token"]
        st.session_state["auth0_token"] = token
        # Clean up query params
        del st.query_params["token"]
        st.rerun()
        
    return None
