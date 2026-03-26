import streamlit as st
import db_utils
import pandas as pd
from db_setup import setup_db

# Ensure required tables exist before app starts
setup_db()
st.set_page_config(layout="wide")
st.title("📚 Scholars International Study Hall")
import datetime
import pandas as pd
import db_utils
import auth
if not st.session_state.get("authenticated"):
    if st.session_state.get("auth_step") == "mfa":
        auth.mfa_verify()
    else:
        auth.login()
else:
    st.sidebar.write(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        auth.logout()

    # Role‑based menu
    if st.session_state.role == "admin":
        menu_options = ["Register User","Renewal Payment", "Change Seat","User Report", "Deactivate User", "Dashboard"]
    else:
        menu_options = ["dasbard"]

    # --- Main Menu ---
    menu = st.sidebar.selectbox("Menu", ["Register User", "Change Seat","User Report","Renewal Payment", "Deactivate User", "Dashboard"]
    )
    st.session_state.menu = menu

    #menu = st.sidebar.selectbox("Menu", ["Register User","Renewal Payment", "Change Seat", "Deactivate User", "Dashboard"])

    # Register User
    if menu == "Register User":
        name = st.text_input("Name")
        phone = st.text_input("Phone", max_chars=10)
        email = st.text_input("Email")
        course = st.text_input("Course")
        seat = st.number_input("Seat Number", min_value=1, max_value=110)
        plan = st.selectbox("Payment Plan", ["15 days", "1 month", "3 months"])
        start_date = st.date_input("Start Date (Admin Selectable)")
        payment_mode=st.selectbox("Payment Mode", ["Cash", "Card", "UPI", "NetBanking"], key="activate_payment_mode")

        if st.button("Register", key="register_button"):
            # Validation: Name and Phone must not be empty
            if not name.strip():
                st.error("Name is required.")
            elif not phone.strip():
                st.error("Phone number is required.")
            elif not phone.isdigit():
                st.error("Phone number must contain only digits.")
            elif len(phone) != 10:
                st.error("Phone number must be exactly 10 digits.")
            else:
                success, message = db_utils.register_user(
                    name, phone, email, course, seat, plan, start_date.strftime("%Y-%m-%d"),payment_mode
                )
                st.success(message) if success else st.error(message)

    elif menu == "User Report":
        st.subheader("Registered Users")
        df = db_utils.get_user_details()

        if df.empty:
            st.info("No users found.")
        else:
            # Style the header row: light blue background, bold black text
         styled_df = df.style.set_table_styles(
            [{
                'selector': 'th',
                'props': [
                    ('background-color', '#ADD8E6'),  # Light blue
                    ('color', 'black'),               # Black font
                    ('font-weight', 'bold')           # Bold text
                ]
            }]
        )

        st.dataframe(styled_df, use_container_width=True)

    # Payment Renewal
    elif menu=="Renewal Payment":
        upcoming_renewals = db_utils.get_upcoming_renewals()
        st.subheader("🔔 Renewal Reminders (within 3 days)")
        if upcoming_renewals and len(upcoming_renewals) > 0:
            if upcoming_renewals:
                user_options = {f"{u[1]} ({u[2]}) - Renewal: {u[4]}": u for u in upcoming_renewals}
                selected_user_label = st.selectbox("Select a user to update renewal", list(user_options.keys()))

                if selected_user_label:
                    selected_user = user_options[selected_user_label]
                    user_id, name, phone, seat, renewal_date, payment_mode, payment_plan = selected_user

                    st.write(f"👤 {name} | 📞 {phone} | 💺 Seat: {seat if seat else 'N/A'}")
                    st.write(f"Renewal Date: {renewal_date} | Plan: {payment_plan} | Payment Mode: {payment_mode}")

                with st.form("update_renewal_form"):
                    new_plan = st.selectbox("New Renewal Period", ["15 days", "1 month", "3 months"])
                    new_payment_mode = st.selectbox("New Payment Mode", ["Cash", "Card", "UPI", "Net Banking"])
                    update_btn = st.form_submit_button("Update Renewal")

                if update_btn:
                    new_date = db_utils.update_renewal(user_id, new_plan, new_payment_mode,renewal_date)
                    st.success(f"✅ Renewal updated for {name}: valid until {new_date.strftime('%Y-%m-%d')} via {new_payment_mode}, Plan: {new_plan}")
            else:
                st.info("No users with renewals due in the next 3 days.")
        else:
            st.info("No users with renewals due in the next 3 days.")


    # Change Seat
    elif menu == "Change Seat":
        users = db_utils.get_users()
        df = pd.DataFrame(users, columns=[
            "id","Name","Phone","Email","Course","Seat","StartDate","Active","Plan","Renewal","PaymentMode","Remarks"
        ])

        # Only active users
        active_users = df[df["Active"] == 1]

        if active_users.empty:
            st.warning("No active users available to change seat.")
        else:
            # Build a unique display string: ID + Name + Seat
            active_users["Display"] = active_users.apply(
                lambda row: f"ID {row['id']} - {row['Name']} (Seat {row['Seat']})",
                axis=1
            )

            selection = st.selectbox("Select Active User to Change Seat", active_users["Display"], key="change_seat_select")

            if selection:
                # Find the exact row by matching the Display string
                user_row = active_users[active_users["Display"] == selection].iloc[0]
                user_id = user_row["id"]
                old_seat = user_row["Seat"]

                st.write(f"Current Seat Number: **{old_seat}**")

                new_seat = st.number_input("New Seat Number", min_value=1, max_value=110, key="new_seat_input")
                if st.button("Update Seat", key="update_seat_button"):
                    success, message = db_utils.change_seat(user_id, new_seat)
                    st.success(message) if success else st.error(message)

    # Deactivate User
    elif menu == "Deactivate User":
        users = db_utils.get_users()
        df = pd.DataFrame(users, columns=[
            "id","Name","Phone","Email","Course","Seat","StartDate","Active","Plan","Renewal","PaymentMode","Remarks"
        ])

        # Build a unique display string: ID + Name + Seat
        df["Display"] = df.apply(
            lambda row: f"ID {row['id']} - {row['Name']} (Seat {row['Seat']})",
            axis=1
        )

        selection = st.selectbox("Select User", df["Display"], key="deactivate_user_select")

        if selection:
            # Find the exact row by matching the Display string
            user_row = df[df["Display"] == selection].iloc[0]
            user_id = user_row["id"]
            old_seat = user_row["Seat"]
            active_status = user_row["Active"]

            st.write(f"User ID: {user_id}, Seat: {old_seat}")
            st.write(f"Current Status: {'Active' if active_status == 1 else 'Inactive'}")

            if active_status == 1:
                # Show deactivate button
                if st.button("Deactivate", key="deactivate_user_button"):
                    success, message = db_utils.deactivate_user(user_id)
                    st.success(message) if success else st.error(message)
            else:
                # Show activate form with extra fields
                start_date = st.date_input("Start Date", key="activate_start_date")
                plan = st.selectbox("Payment Plan", ["15 days", "1 month", "3 months"], key="activate_plan")
                payment_mode = st.selectbox("Payment Mode", ["Cash", "Card", "UPI", "NetBanking"], key="activate_payment_mode")
                seat = st.number_input("Seat Number", min_value=1, max_value=110, value=int(old_seat or 1), key="activate_seat")
                remarks = st.text_area("Remarks / Notes", key="activate_remarks")

                if st.button("Activate", key="activate_user_button"):
                    success, message = db_utils.activate_user(
                        user_id,
                        start_date.strftime("%Y-%m-%d"),
                        plan,
                        payment_mode,
                        remarks,
                        seat
                    )
                    st.success(message) if success else st.error(message)


    # Dashboard

    elif menu == "Dashboard":
        import datetime

        total_seats = db_utils.get_total_seats() or 110
        users = db_utils.get_users()
        df = pd.DataFrame(users, columns=[
            "id", "Name", "Phone", "Email", "Course", "Seat", "StartDate", "Active", "Plan", "Renewal", "PaymentMode", "Remarks"
        ])

        # Only include active users
        df_active = df[df["Active"] == 1]

        if df_active.empty:
            st.warning("No active users found. Add at least one registration first.")
            st.stop()

        filled_seats = df_active["Seat"].astype(int).tolist()

        st.subheader("Seat Map")
        cols = 10  # 11x10 grid for 110 seats
        rows = (total_seats + cols - 1) // cols
        today = datetime.date.today()

        # Define CSS animation once
        st.markdown(
            """
            <style>
            @keyframes blink {
                0% { opacity: 1; }
                50% { opacity: 0; }
                100% { opacity: 1; }
            }
            .blink {
                animation: blink 1s infinite;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        for row in range(rows):
            cols_html = ""
            for col in range(cols):
                seat_num = row * cols + col + 1
                if seat_num > total_seats:
                    continue

                if seat_num in filled_seats:
                    user = df_active[df_active["Seat"] == seat_num].iloc[0]

                    # Parse renewal date
                    days_left = None
                    try:
                        if pd.notna(user["Renewal"]):
                            renewal_date = datetime.datetime.strptime(str(user["Renewal"]), "%Y-%m-%d").date()
                            days_left = (renewal_date - today).days
                    except Exception:
                        days_left = None

                    # Decide color based on days left
                    color = "red"
                    blink_class = ""
                    if days_left is not None:
                        if days_left == 0:
                            color = "brown"
                            blink_class = "blink"
                        elif days_left == 1:
                            color = "blue"
                            blink_class = "blink"
                        elif days_left == 2:
                            color = "purple"
                            blink_class = "blink"
                        elif days_left <= -1:
                            color = "grey"
                            blink_class = "blink"

                    cols_html += f"""
                    <div title='{user['Name']} ({user['Phone']}) ({user['StartDate']}) - Renewal in {days_left if days_left is not None else 'N/A'} days'
                        class='{blink_class}'
                        style='display:inline-block;width:40px;height:40px;
                        background-color:{color};margin:2px;text-align:center;color:white;'>
                        {seat_num}
                    </div>
                    """
                else:
                    cols_html += f"""
                    <div style='display:inline-block;width:40px;height:40px;
                        background-color:green;margin:2px;text-align:center;color:white;'>
                        {seat_num}
                    </div>
                    """
            st.markdown(cols_html, unsafe_allow_html=True)
