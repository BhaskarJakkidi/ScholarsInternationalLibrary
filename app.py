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

if st.session_state.get("auth_expiry") and st.session_state.auth_expiry < datetime.datetime.now():
    auth.logout()
    st.warning("Session expired. Please log in again.")

if not st.session_state.get("authenticated"):
    auth.login()
else:
    st.sidebar.write(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        auth.logout()

    # Role‑based menu
    if st.session_state.role == "admin":
        menu_options = ["Register User", "Edit User", "Renewal Payment", "Change Seat", "User Report", "Deactivate User", "Activate User", "Dashboard"]
    else:
        menu_options = ["Dashboard"]

    # --- Main Menu ---
    menu = st.sidebar.selectbox("Menu", menu_options)
    st.session_state.menu = menu

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

    elif menu == "Edit User":
        users = db_utils.get_users()
        df = pd.DataFrame(users, columns=[
            "id","Name","Phone","Email","Course","Seat","StartDate","Active","Plan","Renewal","PaymentMode","Remarks"
        ])

        if df.empty:
            st.warning("No active users available to edit.")
        else:
            df["Display"] = df.apply(
                lambda row: f"ID {row['id']} - {row['Name']} (Seat {row['Seat']})",
                axis=1
            )

            selection = st.selectbox("Select Active User to Edit", df["Display"], key="edit_user_select")

            if selection:
                user_row = df[df["Display"] == selection].iloc[0]
                user_id = int(user_row["id"])

                st.subheader(f"Edit details for {user_row['Name']}")
                st.write(f"Phone: {user_row['Phone']} | Email: {user_row['Email']}")

                plans = ["15 days", "1 month", "3 months"]
                payment_modes = ["Cash", "Card", "UPI", "NetBanking"]

                current_start_date = pd.to_datetime(user_row["StartDate"]).date() if pd.notna(user_row["StartDate"]) else datetime.date.today()
                plan_index = plans.index(user_row["Plan"]) if user_row["Plan"] in plans else 0
                payment_mode_index = payment_modes.index(user_row["PaymentMode"]) if user_row["PaymentMode"] in payment_modes else 0

                form_key = f"edit_user_form_{user_id}"
                with st.form(form_key):
                    name = st.text_input("Name", value=user_row["Name"], key=f"edit_name_{user_id}")
                    phone = st.text_input("Phone", value=user_row["Phone"], max_chars=10, key=f"edit_phone_{user_id}")
                    email = st.text_input("Email", value=user_row["Email"], key=f"edit_email_{user_id}")
                    course = st.text_input("Course", value=user_row["Course"], key=f"edit_course_{user_id}")
                    seat = st.number_input("Seat Number", min_value=1, max_value=110, value=int(user_row["Seat"] or 1), key=f"edit_seat_{user_id}")
                    plan = st.selectbox("Payment Plan", plans, index=plan_index, key=f"edit_plan_{user_id}")
                    start_date = st.date_input("Start Date", value=current_start_date, key=f"edit_start_date_{user_id}")
                    payment_mode = st.selectbox("Payment Mode", payment_modes, index=payment_mode_index, key=f"edit_payment_mode_{user_id}")

                    update_btn = st.form_submit_button("Save Changes")

                if update_btn:
                    if not name.strip():
                        st.error("Name is required.")
                    elif not phone.strip():
                        st.error("Phone number is required.")
                    elif not phone.isdigit():
                        st.error("Phone number must contain only digits.")
                    elif len(phone) != 10:
                        st.error("Phone number must be exactly 10 digits.")
                    else:
                        success, message = db_utils.update_user_details(
                            user_id,
                            name,
                            phone,
                            email,
                            course,
                            seat,
                            plan,
                            start_date.strftime("%Y-%m-%d"),
                            payment_mode
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


    elif menu == "Activate User":
        users = db_utils.get_deactivated_users()
        df = pd.DataFrame(users, columns=[
            "id","Name","Phone","Email","Course","Seat","StartDate","Active","Plan","Renewal","PaymentMode","Remarks"
        ])

        if df.empty:
            st.warning("No deactivated users found.")
        else:
            df["Display"] = df.apply(
                lambda row: f"ID {row['id']} - {row['Name']} (Seat {row['Seat']})",
                axis=1
            )

            selection = st.selectbox("Select Deactivated User to Activate", df["Display"], key="activate_user_select")

            if selection:
                user_row = df[df["Display"] == selection].iloc[0]
                user_id = int(user_row["id"])

                st.subheader(f"Activate {user_row['Name']}")
                st.write(f"Phone: {user_row['Phone']} | Email: {user_row['Email']}")

                with st.form("activate_user_form"):
                    start_date = st.date_input("Start Date", value=pd.to_datetime(user_row["StartDate"]).date() if pd.notna(user_row["StartDate"]) else datetime.date.today(), key="reactivate_start_date")
                    plan = st.selectbox("Payment Plan", ["15 days", "1 month", "3 months"], index=( ["15 days", "1 month", "3 months"].index(user_row["Plan"]) if user_row["Plan"] in ["15 days", "1 month", "3 months"] else 0), key="reactivate_plan")
                    payment_mode = st.selectbox("Payment Mode", ["Cash", "Card", "UPI", "NetBanking"], index=( ["Cash", "Card", "UPI", "NetBanking"].index(user_row["PaymentMode"]) if user_row["PaymentMode"] in ["Cash", "Card", "UPI", "NetBanking"] else 0), key="reactivate_payment_mode")
                    seat = st.number_input("Seat Number", min_value=1, max_value=110, value=int(user_row["Seat"] or 1), key="reactivate_seat")
                    remarks = st.text_area("Remarks / Notes", value=user_row["Remarks"], key="reactivate_remarks")
                    activate_btn = st.form_submit_button("Activate User")

                if activate_btn:
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
