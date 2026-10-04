import requests
import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT


# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="Snap & Study AI",
    page_icon="📸",
    layout="centered"
)


# -----------------------------
# GEMINI CLIENT
# -----------------------------

client = genai.Client(
    api_key=st.secrets["AQ.Ab8RN6LqLhaYzNteD7V5myvlWTNUR5Xo2ZYFhhCHA5jTuBLC1g"]
)


# -----------------------------
# SESSION STATE
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(
        model="gemini-3.8-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )

if "last_response" not in st.session_state:
    st.session_state.last_response = ""


# -----------------------------
# TITLE
# -----------------------------

st.title("📸 Snap & Study AI")

st.write(
    "Upload a question, note, diagram or study material "
    "and let AI explain it simply."
)


# -----------------------------
# PREVIOUS MESSAGES
# -----------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("image"):
            st.image(message["image"], width=400)

        st.markdown(message["content"])


# -----------------------------
# IMAGE UPLOAD
# -----------------------------

uploaded_file = st.file_uploader(
    "📷 Upload your study material",
    type=["jpg", "jpeg", "png"]
)


# -----------------------------
# CHAT INPUT
# -----------------------------

user_text = st.chat_input(
    "Ask a question..."
)


# -----------------------------
# PROCESS INPUT
# -----------------------------

if user_text or uploaded_file:

    if user_text:
        question = user_text
    else:
        question = (
            "Analyze this image and explain the important "
            "content in simple language for a student."
        )

    image_bytes = None

    if uploaded_file:
        image_bytes = uploaded_file.getvalue()

    # Show user message
    with st.chat_message("user"):

        if image_bytes:
            st.image(image_bytes, width=400)

        st.markdown(question)

    # Save user message
    user_message = {
        "role": "user",
        "content": question
    }

    if image_bytes:
        user_message["image"] = image_bytes

    st.session_state.messages.append(user_message)

    # Ask Gemini
    with st.chat_message("assistant"):

        with st.spinner("🧠 Gemini is analyzing..."):

            try:

                if image_bytes:

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

            except Exception as error:

                st.error("Something went wrong.")
                st.error(str(error))


# -----------------------------
# TELEGRAM FUNCTION
# -----------------------------

def send_to_telegram(message):

    bot_token = st.secrets["TELEGRAM_BOT_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]

    url = (
        f"https://api.telegram.org/bot"
        f"{bot_token}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()


# -----------------------------
# TELEGRAM BUTTON
# -----------------------------

if st.session_state.last_response:

    st.divider()

    st.subheader("💬 Save to Telegram")

    if st.button("📨 Send Explanation to Telegram"):

        try:

            send_to_telegram(
                st.session_state.last_response
            )

            st.success(
                "✅ Explanation sent to Telegram!"
            )

        except Exception as error:

            st.error(
                "Telegram message could not be sent."
            )

            st.error(str(error))


# -----------------------------
# FOOTER
# -----------------------------

st.divider()

st.caption(
    "Snap & Study AI • Powered by Gemini Vision"
)
