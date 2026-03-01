# features/maintenance.py

import streamlit as st

def maintenance_panel(cursor):

    st.markdown("## 🔧 Monthly Maintenance")

    cursor.execute("SELECT * FROM maintenance")
    data = cursor.fetchall()

    for m in data:
        st.warning(m)
