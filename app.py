import streamlit as st
import bcrypt
import pandas as pd
from database import create_tables, connect_db

# =====================================================
# ⚙️ PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="HelioSync",
    layout="wide",
    page_icon="☀️",
    initial_sidebar_state="expanded"
)

try:
    create_tables()
except Exception as e:
    st.error(f"Database setup failed: {e}")
    st.stop()

# =====================================================
# 🧠 HELIOSYNC AI PRO ENGINE
# =====================================================
def heliosync_ai_best_technician(cursor, village, prefer_female=False):
    try:
        query = """
            SELECT u.id, u.name, COUNT(t.id) as active_jobs
            FROM users u
            LEFT JOIN tickets t
            ON u.id = t.assigned_to AND t.status!='Completed'
            WHERE u.role='Technician' AND u.village=?
        """
        params = [village]
        if prefer_female:
            query += " AND u.gender='Female'"
        query += " GROUP BY u.id ORDER BY active_jobs ASC"
        
        cursor.execute(query, params)
        techs = cursor.fetchall()
        if techs:
            st.write(f"Debug: Best technician for {village} (Female preferred: {prefer_female}): {techs[0]}")
            return techs[0]
        else:
            if prefer_female:
                st.warning(f"No female technicians in {village}. Assigning any available technician.")
                return heliosync_ai_best_technician(cursor, village, prefer_female=False)  # Fallback
            else:
                st.warning(f"No technicians available in {village}. Ticket set to Pending.")
                return None
    except Exception as e:
        st.error(f"Error finding best technician: {e}")
        return None

# =====================================================
# 🧠 HELIOSYNC SMART MAINTENANCE AI
# =====================================================
def heliosync_create_monthly_maintenance(cursor):
    try:
        cursor.execute("SELECT id, village FROM users WHERE role='User'")
        users = cursor.fetchall()
        for user in users:
            user_id, village = user
            cursor.execute("""
                SELECT u.id, COUNT(m.id)
                FROM users u
                LEFT JOIN maintenance m
                ON u.id = m.technician_id AND m.status!='Completed'
                WHERE u.role='Technician' AND u.village=?
                GROUP BY u.id
                ORDER BY COUNT(m.id) ASC
                LIMIT 1
            """, (village,))
            tech = cursor.fetchone()
            if tech:
                technician_id = tech[0]
                cursor.execute("""
                    INSERT INTO maintenance
                    (user_id, technician_id, schedule_date, status)
                    VALUES (?, ?, date('now','+30 day'), 'Scheduled')
                """, (user_id, technician_id))
    except Exception as e:
        st.error(f"Error generating maintenance: {e}")

# =====================================================
# 🎨 NEW MODERN UI STYLE
# =====================================================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #e0f2fe, #f0f9ff); font-family: 'Segoe UI', sans-serif; }
.block-container { padding: 2rem 1rem; max-width: 1200px; margin: 0 auto; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e2e8f0; }
h1, h2, h3, h4, p, span, label { color: #1e293b !important; }
.role-card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s; cursor: pointer; }
.role-card:hover { transform: translateY(-4px); box-shadow: 0 8px 15px rgba(0,0,0,0.15); border-color: #3b82f6; }
.stButton>button { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; border-radius: 8px; border: none; font-weight: 600; padding: 10px 20px; transition: background 0.3s; }
.stButton>button:hover { background: linear-gradient(135deg, #1d4ed8, #1e40af); }
.metric-box { background: #f8fafc; border-radius: 8px; padding: 15px; text-align: center; border: 1px solid #e2e8f0; }
.success-text { color: #10b981; }
.error-text { color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 🚀 HELIOSYNC HERO HEADER
# =====================================================
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1>☀️ HelioSync</h1>
    <p>Ultimate Smart Solar Service Ecosystem</p>
    <p>AI-Powered Platform for Users, Technicians, and Admins</p>
</div>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "role" not in st.session_state: st.session_state.role = None
if "user_id" not in st.session_state: st.session_state.user_id = None
if "selected_role" not in st.session_state: st.session_state.selected_role = None
if "name" not in st.session_state: st.session_state.name = None

# =====================================================
# 🚀 ROLE SELECTION
# =====================================================
if not st.session_state.logged_in and not st.session_state.selected_role:
    st.markdown("## 🌟 Choose Your Role")
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        with st.expander("👤 **User**", expanded=True):
            st.markdown("Raise complaints & give feedback")
            if st.button("Select User"): st.session_state.selected_role = "User"; st.rerun()
    with col2:
        with st.expander("👨‍🔧 **Technician**", expanded=True):
            st.markdown("Manage jobs & earnings")
            if st.button("Select Technician"): st.session_state.selected_role = "Technician"; st.rerun()
    with col3:
        with st.expander("🧠 **Admin**", expanded=True):
            st.markdown("AI control & analytics")
            if st.button("Select Admin"): st.session_state.selected_role = "Admin"; st.rerun()

# =====================================================
# 🔐 AUTH SECTION
# =====================================================
if st.session_state.selected_role and not st.session_state.logged_in:
    st.markdown(f"## 🔑 Access as {st.session_state.selected_role}")
    menu = st.sidebar.radio("Navigation", ["🏠 Home", "📝 Register", "🔓 Login"])
    if menu == "🏠 Home": st.markdown("### Welcome"); st.write("Register or login.")
    elif menu == "📝 Register":
        with st.form("register"):
            name = st.text_input("Name", placeholder="Full name")
            phone = st.text_input("Phone", placeholder="+1234567890")
            village = st.text_input("Village")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], placeholder="Select your gender")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Register"):
                if name and phone and village and gender and password:
                    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
                    is_new = 1 if st.session_state.selected_role == "Technician" else 0  # Mark new technicians
                    with st.spinner("Registering..."):
                        try:
                            with connect_db() as conn:
                                cursor = conn.cursor()
                                if cursor.execute("SELECT id FROM users WHERE phone=?", (phone,)).fetchone():
                                    st.error("Phone exists")
                                else:
                                    cursor.execute("INSERT INTO users (name, phone, village, role, gender, is_new_technician, password) VALUES (?,?,?,?,?,?,?)", (name, phone, village, st.session_state.selected_role, gender, is_new, hashed))
                                    conn.commit()
                                    st.success("Registered! Login now.")
                        except Exception as e: st.error(f"Error: {e}")
                else: st.warning("Fill all fields")
    elif menu == "🔓 Login":
        with st.form("login"):
            phone = st.text_input("Phone")
            password = st.text_input("Password", type="password")
            if st.session_state.selected_role == "Technician":
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], placeholder="Confirm your gender")
            else:
                gender = None
            if st.form_submit_button("Login"):
                with st.spinner("Logging in..."):
                    try:
                        with connect_db() as conn:
                            cursor = conn.cursor()
                            user = cursor.execute("SELECT id, name, role, password, gender FROM users WHERE phone=?", (phone,)).fetchone()
                            if user and bcrypt.checkpw(password.encode(), user[3]):
                                if st.session_state.selected_role == "Technician" and user[4] != gender:
                                    st.error("Gender does not match our records.")
                                else:
                                    st.session_state.logged_in, st.session_state.user_id, st.session_state.name, st.session_state.role = True, user[0], user[1], user[2]
                                    st.rerun()
                            else: st.error("Invalid credentials")
                    except Exception as e: st.error(f"Error: {e}")

# =====================================================
# LOGGED IN DASHBOARDS
# =====================================================
if st.session_state.logged_in:
    with connect_db() as conn:
        cursor = conn.cursor()
        st.sidebar.markdown(f"👋 **{st.session_state.name}** | Role: **{st.session_state.role}**")
        if st.sidebar.button("🚪 Logout"): st.session_state.clear(); st.rerun()
        role = st.session_state.role.lower()

               # ================= ADMIN =================
        if role == "admin":
            st.markdown("## 🧠 Admin Control Center")
            tabs = st.tabs(["📊 Overview", "👥 Users & Technicians", "🎫 Ticket Center", "📈 Analytics", "⭐ Feedback", "🛠 Maintenance", "📍 Location History"])
            with tabs[0]:
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("👥 Users", cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0])
                with col2: st.metric("👨‍🔧 Techs", cursor.execute("SELECT COUNT(*) FROM users WHERE role='Technician'").fetchone()[0])
                with col3: st.metric("🎫 Active Tickets", cursor.execute("SELECT COUNT(*) FROM tickets WHERE status!='Completed'").fetchone()[0])
                with col4: st.metric("✅ Completed", cursor.execute("SELECT COUNT(*) FROM tickets WHERE status='Completed'").fetchone()[0])
            with tabs[1]:
                st.subheader("Manage Users")
                users = cursor.execute("SELECT id, name, phone, village, role, gender, is_new_technician FROM users").fetchall()
                for u in users:
                    with st.expander(f"👤 {u[1]} ({u[4]})"):
                        st.write(f"Phone: {u[2]} | Village: {u[3]} | Gender: {u[5] or 'Not specified'} | New Tech: {'Yes' if u[6] else 'No'}")
                        if st.button(f"Delete {u[0]}", key=f"del_{u[0]}"):
                            cursor.execute("DELETE FROM users WHERE id=?", (u[0],)); conn.commit(); st.rerun()
            with tabs[2]:
                st.subheader("All Tickets")
                tickets = cursor.execute("SELECT id, user_id, issue, priority, status, assigned_to FROM tickets").fetchall()
                for t in tickets:
                    with st.expander(f"🎫 Ticket {t[0]} - {t[4]}"):
                        st.write(f"User: {t[1]} | Issue: {t[2]} | Priority: {t[3]} | Assigned: {t[5] or 'None'}")
                        # Status progress bar
                        status_progress = {"Pending": 0, "In Progress": 50, "Completed": 100}
                        progress_value = status_progress.get(t[4], 0)
                        st.progress(progress_value / 100)
                        st.write(f"Status Progress: {progress_value}% ({t[4]})")
                        # Update status
                        new_status = st.selectbox("Update Status", ["Pending", "In Progress", "Completed"], index=["Pending", "In Progress", "Completed"].index(t[4]), key=f"status_{t[0]}")
                        # Manual assignment
                        technicians = cursor.execute("SELECT id, name FROM users WHERE role='Technician'").fetchall()
                        tech_options = ["None"] + [f"{tech[1]} (ID: {tech[0]})" for tech in technicians]
                        current_assigned = t[5]
                        if current_assigned:
                            current_tech_name = cursor.execute("SELECT name FROM users WHERE id=?", (current_assigned,)).fetchone()
                            current_option = f"{current_tech_name[0]} (ID: {current_assigned})" if current_tech_name else "None"
                        else:
                            current_option = "None"
                        assigned_option = st.selectbox("Assign Technician", tech_options, index=tech_options.index(current_option) if current_option in tech_options else 0, key=f"assign_{t[0]}")
                        if st.button("Update Ticket", key=f"update_{t[0]}"):
                            # Update status
                            cursor.execute("UPDATE tickets SET status=? WHERE id=?", (new_status, t[0]))
                            # Update assignment if changed
                            if assigned_option != "None":
                                tech_id = int(assigned_option.split("(ID: ")[1].rstrip(")"))
                                cursor.execute("UPDATE tickets SET assigned_to=? WHERE id=?", (tech_id, t[0]))
                            else:
                                cursor.execute("UPDATE tickets SET assigned_to=NULL WHERE id=?", (t[0],))
                            conn.commit()
                            st.success("Ticket updated!")
                            st.rerun()
            with tabs[3]:
                st.subheader("Analytics")
                ticket_data = pd.DataFrame(cursor.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status").fetchall(), columns=["Status", "Count"])
                st.bar_chart(ticket_data.set_index("Status"))
                user_data = pd.DataFrame(cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role").fetchall(), columns=["Role", "Count"])
                st.bar_chart(user_data.set_index("Role"))
            with tabs[4]:
                st.subheader("Feedback Center")
                feedback = cursor.execute("SELECT f.rating, f.message, u.name FROM feedback f JOIN users u ON f.from_id=u.id").fetchall()
                for fb in feedback:
                    st.info(f"⭐ {fb[0]}/5 by {fb[2]}: {fb[1]}")
            with tabs[5]:
                st.subheader("Smart Maintenance AI")
                if st.button("⚡ Generate"):
                    with st.spinner("Generating..."): heliosync_create_monthly_maintenance(cursor); conn.commit()
                    st.success("Done!")
                maint = cursor.execute("SELECT m.id, u.name, m.schedule_date, m.status FROM maintenance m JOIN users u ON m.user_id=u.id").fetchall()
                for m in maint: st.info(f"🛠 {m[0]} | {m[1]} | {m[2]} | {m[3]}")
            with tabs[6]:
                st.subheader("📍 Location History")
                st.write("View shared locations from female technicians for safety monitoring.")
                location_count = cursor.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
                st.write(f"Total locations shared: {location_count}")  # Debug: Check if locations are in DB
                locations = cursor.execute("SELECT l.id, l.latitude, l.longitude, l.timestamp, u.name FROM locations l JOIN users u ON l.technician_id = u.id ORDER BY l.timestamp DESC").fetchall()
                if locations:
                    for loc in locations:
                        with st.expander(f"📍 Location from {loc[4]} on {loc[3]}"):
                            st.write(f"Latitude: {loc[1]}, Longitude: {loc[2]}")
                            st.write(f"Technician: {loc[4]} | Timestamp: {loc[3]}")
                            # Option to view on map
                            if st.button(f"View on Map {loc[0]}", key=f"map_{loc[0]}"):
                                st.write(f"[Open in Google Maps](https://www.google.com/maps?q={loc[1]},{loc[2]})")
                            # Option to delete
                            if st.button(f"Delete {loc[0]}", key=f"del_loc_{loc[0]}"):
                                cursor.execute("DELETE FROM locations WHERE id=?", (loc[0],)); conn.commit(); st.rerun()
                else:
                    st.info("No locations shared yet.")

                      # ================= TECHNICIAN =================
        elif role == "technician":
            st.markdown("## ⚡ Technician Dashboard")
            # Calculate earnings and bonus outside tabs for global access
            completed = cursor.execute("SELECT COUNT(*) FROM tickets WHERE assigned_to=? AND status='Completed'", (st.session_state.user_id,)).fetchone()[0]
            earnings = completed * 100
            bonus = (completed // 5) * 200
            tabs = st.tabs(["📊 Overview", "🛠 Active Jobs", "📜 History", "💰 Earnings", "🛠 Maintenance", "📚 Learning & Training"])
            with tabs[0]:
                col1, col2, col3 = st.columns(3)
                with col1: st.metric("✅ Jobs", completed)
                with col2: st.metric("💰 Earnings", f"₹{earnings}")
                with col3: st.metric("🎯 Bonus", f"₹{bonus}")
            with tabs[1]:
                active = cursor.execute("SELECT id, issue, priority, status FROM tickets WHERE assigned_to=? AND status!='Completed'", (st.session_state.user_id,)).fetchall()
                st.write(f"Debug: Active tickets: {len(active)}")
                # Check if technician is female
                tech_gender = cursor.execute("SELECT gender FROM users WHERE id=?", (st.session_state.user_id,)).fetchone()[0]
                if tech_gender == "Female" and active:
                    st.subheader("📍 Location Sharing (For Safety)")
                    st.write("As a female technician with active jobs, your current location is automatically detected for safety purposes.")
                    from streamlit_geolocation import streamlit_geolocation
                    location = streamlit_geolocation()
                    if location and 'latitude' in location and 'longitude' in location:
                        lat = location.get('latitude')
                        lon = location.get('longitude')
                        if lat is not None and lon is not None:
                            st.write(f"Current Location: Latitude {lat}, Longitude {lon}")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Share Location with Admin"):
                                    cursor.execute("INSERT INTO locations (technician_id, latitude, longitude) VALUES (?, ?, ?)", (st.session_state.user_id, lat, lon))
                                    conn.commit()
                                    st.success("Location shared with admin for safety!")
                            with col2:
                                if st.button("🚨 SOS Emergency Alert", key="sos_button"):
                                    cursor.execute("INSERT INTO sos_alerts (technician_id, latitude, longitude) VALUES (?, ?, ?)", (st.session_state.user_id, lat, lon))
                                    conn.commit()
                                    st.error("🚨 SOS Alert Sent! Help is on the way.")
                        else:
                            st.warning("Location coordinates are not available. Please try again or allow location access.")
                            if st.button("🚨 SOS Emergency Alert (No Location)", key="sos_button_no_loc"):
                                cursor.execute("INSERT INTO sos_alerts (technician_id) VALUES (?)", (st.session_state.user_id,))
                                conn.commit()
                                st.error("🚨 SOS Alert Sent! Help is on the way.")
                    else:
                        st.warning("Location not available. Please allow location access in your browser.")
                        if st.button("🚨 SOS Emergency Alert (No Location)", key="sos_button_no_loc"):
                            cursor.execute("INSERT INTO sos_alerts (technician_id) VALUES (?)", (st.session_state.user_id,))
                            conn.commit()
                            st.error("🚨 SOS Alert Sent! Help is on the way.")
                for t in active:
                    with st.expander(f"🎫 {t[0]} - {t[2]}"):
                        st.write(f"Issue: {t[1]} | Status: {t[3]}")
                        if st.button("Complete", key=f"comp_{t[0]}"):
                            cursor.execute("UPDATE tickets SET status='Completed' WHERE id=?", (t[0],)); conn.commit(); st.rerun()
            with tabs[2]:
                history = cursor.execute("SELECT id, issue, priority FROM tickets WHERE assigned_to=? AND status='Completed'", (st.session_state.user_id,)).fetchall()
                st.write(f"Debug: History tickets: {len(history)}")
                if history:
                    for h in history:
                        with st.expander(f"✅ {h[0]}"):
                            st.write(f"Issue: {h[1]} | Priority: {h[2]}")
                            user_id = cursor.execute("SELECT user_id FROM tickets WHERE id=?", (h[0],)).fetchone()[0]
                            rating = st.slider("Rate User", 1, 5, key=f"rate_{h[0]}")
                            msg = st.text_area("Message", key=f"msg_{h[0]}")
                            if st.button("Send Feedback", key=f"fb_{h[0]}"):
                                cursor.execute("INSERT INTO feedback (from_id, from_role, to_id, to_role, ticket_id, rating, message) VALUES (?,?,?,?,?,?,?)", (st.session_state.user_id, "Technician", user_id, "User", h[0], rating, msg))
                                conn.commit()
                                st.success("Sent!")
                else:
                    st.info("No completed history yet. Complete some active jobs to see history.")
            with tabs[3]: 
                st.metric("Total Earnings", f"₹{earnings}"); st.metric("Bonus", f"₹{bonus}")
            with tabs[4]:
                maint = cursor.execute("SELECT id, user_id, schedule_date, status FROM maintenance WHERE technician_id=? AND status!='Completed'", (st.session_state.user_id,)).fetchall()
                for m in maint:
                    with st.expander(f"🛠 {m[0]}"):
                        st.write(f"User: {m[1]} | Date: {m[2]} | Status: {m[3]}")
                        if st.button("Done", key=f"done_{m[0]}"):
                            cursor.execute("UPDATE maintenance SET status='Completed' WHERE id=?", (m[0],)); conn.commit(); st.success("Completed!"); st.rerun()
            with tabs[5]:
                st.subheader("📚 Learning Resources")
                st.markdown("### Basic Solar Maintenance Tutorials")
                st.video("https://youtu.be/xKxrkht7CpY?si=mnlR2cMRBc7fooWA")  # How Solar Panels Work
                st.video("https://youtu.be/eYZG_4_OA_I?si=4NK8wCp2uaFVHgKT")  # Solar Panel Cleaning and Maintenance
                st.video("https://youtube.com/shorts/UamEi1ScQP4?si=VDZQSrcWWWRQUtAf")  # Troubleshooting Solar Systems
                st.markdown("""
                **Key Responsibilities:**
                - Inspect and repair solar panels.
                - Ensure safety protocols are followed.
                - Report issues promptly.
                **Tips:** Always wear protective gear and double-check connections.
                """)
                new_tech_count = cursor.execute("SELECT COUNT(*) FROM users WHERE role='Technician' AND is_new_technician=1").fetchone()[0]
                if new_tech_count > 15:
                    st.subheader("🏆 Training Workshop Available!")
                    st.write("A group training workshop is now open for new technicians. Join to enhance your skills!")
                    if st.button("Join Workshop"):
                        st.success("Workshop joined! Check your email for details.")  # Placeholder for actual integration
                else:
                    st.info(f"Training workshop unlocks when more than 15 new technicians register. Currently: {new_tech_count} new technicians.")
        # ================= USER =================
        elif role == "user":
            st.markdown("## 👤 User Dashboard")
            with st.form("submit_ticket"):
                st.subheader("📝 Submit Issue")
                issue = st.text_area("Describe Issue")
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
                prefer_female = st.checkbox("Prefer Female Technician")
                if st.form_submit_button("Submit"):
                    if issue:
                        village = cursor.execute("SELECT village FROM users WHERE id=?", (st.session_state.user_id,)).fetchone()[0]
                        tech = heliosync_ai_best_technician(cursor, village, prefer_female)
                        assigned = tech[0] if tech else None
                        status = "In Progress" if assigned else "Pending"
                        cursor.execute("INSERT INTO tickets (user_id, issue, priority, status, assigned_to) VALUES (?, ?, ?, ?, ?)", (st.session_state.user_id, issue, priority, status, assigned))
                        conn.commit()
                        st.success("⚡ AI Assigned Technician!")
                        st.rerun()
                    else:
                        st.error("Describe the issue")
            st.markdown("### ⭐ Feedback to Technicians")
            completed = cursor.execute("SELECT id, assigned_to FROM tickets WHERE user_id=? AND status='Completed'", (st.session_state.user_id,)).fetchall()
            st.write(f"Debug: Completed tickets: {len(completed)}")
            if completed:
                for t in completed:
                    ticket_id, tech_id = t
                    if tech_id:
                        with st.expander(f"Rate for Ticket {ticket_id}"):
                            rating = st.slider("Rating", 1, 5, key=f"user_rate_{ticket_id}")
                            message = st.text_area("Message", key=f"user_msg_{ticket_id}")
                            if st.button("Submit Feedback", key=f"user_fb_{ticket_id}"):
                                cursor.execute("INSERT INTO feedback (from_id, from_role, to_id, to_role, ticket_id, rating, message) VALUES (?,?,?,?,?,?,?)", (st.session_state.user_id, "User", tech_id, "Technician", ticket_id, rating, message))
                                conn.commit()
                                st.success("Feedback sent!")
            else:
                st.info("No completed tickets yet. Submit a ticket and wait for it to be completed to give feedback.")