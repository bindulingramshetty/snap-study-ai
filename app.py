import smtplib
from email.mime.text import MIMEText

import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Snap & Study AI",
    page_icon="📸",
    layout="centered"
)


# --------------------------------------------------
# GEMINI CLIENT
# --------------------------------------------------

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )

if "last_response" not in st.session_state:
    st.session_state.last_response = ""


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("📸 Snap & Study AI")

st.write(
    "Upload a study image or ask a question. "
    "I'll explain it in simple language."
)


# --------------------------------------------------
# DISPLAY PREVIOUS CHAT
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("image") is not None:
            st.image(message["image"], width=400)

        st.markdown(message["content"])


# --------------------------------------------------
# IMAGE UPLOAD
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "📷 Upload a question, note, diagram or study material",
    type=["jpg", "jpeg", "png"]
)


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

user_text = st.chat_input(
    "Ask something about your study material..."
)


# --------------------------------------------------
# PROCESS USER MESSAGE
# --------------------------------------------------

if user_text or uploaded_file:

    if user_text:
        question = user_text
    else:
        question = (
            "Please analyze this image and explain the "
            "important content in simple language."
        )

    # Save user message
    user_message = {
        "role": "user",
        "content": question
    }

    if uploaded_file:
        image_bytes = uploaded_file.getvalue()
        user_message["image"] = image_bytes

    st.session_state.messages.append(user_message)

    # Show user message
    with st.chat_message("user"):

        if uploaded_file:
            st.image(image_bytes, width=400)

        st.markdown(question)

    # Ask Gemini
    with st.chat_message("assistant"):

        with st.spinner("🧠 Understanding your study material..."):

            try:

                if uploaded_file:

                    image_part = types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=uploaded_file.type
                    )

                    response = st.session_state.chat.send_message(
                        [image_part, question]
                    )

                else:

                    response = st.session_state.chat.send_message(
                        question
                    )

                answer = response.text

                st.markdown(answer)

                st.session_state.last_response = answer

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

            except Exception as e:

                st.error(
                    "Something went wrong while contacting Gemini."
                )

                st.error(str(e))


# --------------------------------------------------
# EMAIL FUNCTION
# --------------------------------------------------

def send_email(receiver_email, subject, body):

    sender_email = st.secrets["GMAIL_ADDRESS"]
    app_password = st.secrets["GMAIL_APP_PASSWORD"]

    message = MIMEText(body)

    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

        server.login(
            sender_email,
            app_password
        )

        server.sendmail(
            sender_email,
            receiver_email,
            message.as_string()
        )


# --------------------------------------------------
# EMAIL SECTION
# --------------------------------------------------

if st.session_state.last_response:

    st.divider()

    st.subheader("📧 Save this explanation")

    receiver_email = st.text_input(
        "Enter your email address"
    )

    if st.button("📨 Send Explanation to Email"):

        if not receiver_email:

            st.warning(
                "Please enter your email address first."
            )

        else:

            try:

                send_email(
                    receiver_email,
                    "Snap & Study AI - Study Explanation",
                    st.session_state.last_response
                )

                st.success(
                    "✅ Explanation sent successfully!"
                )

            except Exception as e:

                st.error(
                    "Email could not be sent."
                )

                st.error(str(e))


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Snap & Study AI • Powered by Gemini Vision"
)
