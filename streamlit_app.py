import streamlit as st
from streamlit_modal import Modal
from typing import Generator
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import json
from datetime import datetime
import re 
import streamlit.components.v1 as components 
import random 


st.set_page_config(page_icon="💬", layout="wide", page_title="Groqify")

def icon(emoji: str):
    st.write(f'<span style="font-size: 50px; line-height: 1">{emoji}</span>', unsafe_allow_html=True)

st.subheader("🚀 Groqify", divider="rainbow", anchor=False)

def export_chat_history_as_pdf(messages):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    text_object = c.beginText(40, height - 40) 
    text_object.setFont("Helvetica", 12)
    max_width = width - 80 

    def wrap_text(text, max_width):
        wrapped_lines = []
        words = text.split()
        line = ""
        for word in words:
            if c.stringWidth(line + " " + word, "Helvetica", 12) <= max_width:
                line += " " + word if line else word
            else:
                wrapped_lines.append(line)
                line = word
        wrapped_lines.append(line)
        return wrapped_lines

    for message in messages:
        role = "User" if message["role"] == "user" else "Groqify"
        timestamp = message.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        text_object.setFont("Helvetica-Bold", 12)
        text_object.textLine(f"{role} ({timestamp}):")
        
        text_object.setFont("Helvetica", 12)
        content_lines = wrap_text(message["content"], max_width)
        for line in content_lines:
            text_object.textLine(line)
        text_object.textLine("")

    c.drawText(text_object)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def export_chat_history_as_json(messages):
    return json.dumps(messages, indent=4)

def export_chat_history_as_txt(messages):
    return "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages])

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except KeyError:
    st.error("API key is missing.")

try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("styles.css not found. Continuing without custom styles.")

category_topics = {
    "👨‍💻 Coding Assistance": "Generate example questions that someone might ask when seeking code generation help. Ensure each question ends with a question mark.",
    "🎧 Music Suggestion": "Generate example questions that someone might ask when looking for music recommendations or playlist ideas. Ensure each question ends with a question mark.",
    "🧑‍🍳 Recipe Ideas": "Generate example questions that someone might ask when looking for meal or recipe suggestions. Ensure each question ends with a question mark.",
    "🌍 Travel Inspiration": "Generate example questions that someone might ask when looking for travel destinations or vacation ideas. Ensure each question ends with a question mark.",
    "📈 Productivity Boost": "Generate example questions that someone might ask when seeking advice on improving productivity or time management. Ensure each question ends with a question mark.",
    "🤔 Algorithm Explanation": "Generate example questions that someone might ask when seeking explanations of specific algorithms. Ensure each question ends with a question mark.",
    "🧘 Wellness Tips": "Generate example questions that someone might ask when looking for health and wellness advice. Ensure each question ends with a question mark.",
    "🎨 Creative Ideas": "Generate example questions that someone might ask when looking for creative project suggestions or artistic inspiration. Ensure each question ends with a question mark.",
    "📚 Learning Techniques": "Generate example questions that someone might ask when looking for effective study techniques or learning strategies. Ensure each question ends with a question mark.",
    "💡 Startup Advice": "Generate example questions that someone might ask when seeking advice on starting or growing a business. Ensure each question ends with a question mark.",
    "👨‍👩‍👧 Parenting Tips": "Generate example questions that someone might ask when looking for advice on parenting or child development. Ensure each question ends with a question mark.",
    "📊 Investment Ideas": "Generate example questions that someone might ask when looking for investment suggestions or financial advice. Ensure each question ends with a question mark.",
    "🖌️ Art Techniques": "Generate example questions that someone might ask when looking to learn art techniques or improve artistic skills. Ensure each question ends with a question mark.",
    "🐶 Pet Training": "Generate example questions that someone might ask when looking for tips on training their pets. Ensure each question ends with a question mark.",
    "💭 Mindfulness Practices": "Generate example questions that someone might ask when seeking ways to practice mindfulness or meditation. Ensure each question ends with a question mark.",
    "📱 Tech Reviews": "Generate example questions that someone might ask when seeking reviews or recommendations for tech products. Ensure each question ends with a question mark.",
    "🏋️ Fitness Routines": "Generate example questions that someone might ask when looking for workout routines or fitness tips. Ensure each question ends with a question mark.",
    "🍿 Movie Recommendations": "Generate example questions that someone might ask when seeking movie suggestions or reviews. Ensure each question ends with a question mark.",
    "🛋️ Home Improvement": "Generate example questions that someone might ask when seeking ideas for home improvement or DIY projects. Ensure each question ends with a question mark.",
    "🌱 Gardening Tips": "Generate example questions that someone might ask when looking for gardening advice or plant care suggestions. Ensure each question ends with a question mark."
}

models = {
    "gemma-7b-it": {"name": "Gemma-7b-it", "tokens": 3000, "developer": "Google"},
    "llama3-70b-8192": {"name": "LLaMA3-70b-8192", "tokens": 8192, "developer": "Meta"},
    "llama3-8b-8192": {"name": "LLaMA3-8b-8192", "tokens": 8192, "developer": "Meta"},
    "mixtral-8x7b-32768": {"name": "Mixtral-8x7b-Instruct-v0.1", "tokens": 3000, "developer": "Mistral"},
}

if "chat_windows" not in st.session_state:
    st.session_state.chat_windows = {"Chat 1": []}
if "active_window" not in st.session_state:
    st.session_state.active_window = "Chat 1"
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "mixtral-8x7b-32768" 
if "previous_model" not in st.session_state:
    st.session_state.previous_model = st.session_state.selected_model
if "choose_format_expanded" not in st.session_state:
    st.session_state.choose_format_expanded = False

if "chat_selected_categories" not in st.session_state:
    st.session_state.chat_selected_categories = {
        window: random.sample(list(category_topics.keys()), 3) 
        for window in st.session_state.chat_windows
    }

if "categories_visible" not in st.session_state:
    st.session_state.categories_visible = {window: True for window in st.session_state.chat_windows}

@st.cache_data(ttl=3600) 
def fetch_prompts_for_category(category_description):
    try:
        response = client.chat.completions.create(
            model=st.session_state.selected_model,
            messages=[{"role": "user", "content": category_description}],
            max_tokens=100
        )
        generated_prompts = [prompt.strip() for prompt in response.choices[0].message.content.splitlines() if prompt.strip()]
        return generated_prompts[:3]  # Return top 3 prompts
    except Exception as e:
        st.error(f"Error fetching prompts: {e}")
        return []

if "dynamic_prompts" not in st.session_state:
    st.session_state.dynamic_prompts = {key: [] for key in category_topics}

def set_active_window(window_name):
    st.session_state.active_window = window_name

with st.sidebar:
    st.title("📁 Your Chats")

    st.selectbox(
        "",
        options=list(models.keys()),
        format_func=lambda x: models[x]["name"], 
        index=list(models.keys()).index(st.session_state.selected_model), 
        key="model_selector"
    )

    if st.button("New Chat", key="new_chat"):
        new_window_name = f"Chat {len(st.session_state.chat_windows) + 1}"
        st.session_state.chat_windows[new_window_name] = []
        st.session_state.active_window = new_window_name
        st.session_state.chat_selected_categories[new_window_name] = random.sample(list(category_topics.keys()), 3)

    if st.session_state.model_selector != st.session_state.previous_model:
        st.session_state.selected_model = st.session_state.model_selector
        st.session_state.previous_model = st.session_state.model_selector

    st.markdown("---")
    for window in st.session_state.chat_windows:
        if window == st.session_state.active_window:
            label = f"**{window} (Active)**"
        else:
            label = window

        st.button(label, key=f"switch_{window}", on_click=set_active_window, args=(window,))


    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Export Chat")

    with st.sidebar.expander("Choose Format", expanded=st.session_state.choose_format_expanded):
        messages = st.session_state.chat_windows[st.session_state.active_window]

        pdf_data = export_chat_history_as_pdf(messages)
        if st.download_button("Download as PDF", data=pdf_data, file_name="chat_history.pdf", mime="application/pdf"):
            st.session_state.choose_format_expanded = False  

        json_data = export_chat_history_as_json(messages)
        if st.download_button("Download as JSON", data=json_data, file_name="chat_history.json", mime="application/json"):
            st.session_state.choose_format_expanded = False 

        txt_data = export_chat_history_as_txt(messages)
        if st.download_button("Download as TXT", data=txt_data, file_name="chat_history.txt", mime="text/plain"):
            st.session_state.choose_format_expanded = False  
    st.session_state.choose_format_expanded = False


    st.markdown("---")
    st.markdown("#### Help & Documentation")
    with st.expander("About Groqify"):
        st.write("""
            **Groqify** is a smart chatbot powered by the [Groq API](https://github.com/groq/groq-api-cookbook).

            **Future Plans:**  
            More models and features will be added to enhance Groqify's capabilities. Additional updates are on their way.
        """)
    with st.expander("How to Use Groqify"):
        st.write("""
            - **Start a Chat:** Select a prompt or type your own question.
            - **Switch Chats:** Use the chat history section to switch between conversations.
            - **Download History:** Export your chat history in PDF, JSON, or TXT formats.
        """)

def handle_prompt_click(prompt):

    cleaned_prompt = re.sub(r'^\s*\d+[\.\)]\s*', '', prompt)
    
    st.session_state.chat_windows[st.session_state.active_window].append({"role": "user", "content": cleaned_prompt})
    
    st.session_state.categories_visible[st.session_state.active_window] = False
    
    try:

        system_message = {
            "role": "system",
            "content": "You are a helpful assistant. Please provide clear and concise answers without unnecessary details."
        }
        
        messages = [system_message] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chat_windows[st.session_state.active_window]
        ]
        
        chat_completion = client.chat.completions.create(
            model=st.session_state.selected_model,
            messages=messages,
            max_tokens=models[st.session_state.selected_model]["tokens"], 
            temperature=0.4, 
            top_p=0.8  
        )
        
        response_text = chat_completion.choices[0].message.content
        
        MAX_RESPONSE_LENGTH = 3000 
        if len(response_text) > MAX_RESPONSE_LENGTH:
            response_text = response_text[:MAX_RESPONSE_LENGTH].rstrip() + "..."
        
        st.session_state.chat_windows[st.session_state.active_window].append(
            {"role": "assistant", "content": response_text}
        )

    except Exception as e:
        st.error(f"Error: {e}", icon="🚨")

if st.session_state.categories_visible.get(st.session_state.active_window, True):
    st.write("<h3 style='text-align: center; font-size:18px;'>Try these randomly generated prompts...</h3>", unsafe_allow_html=True)

    selected_categories = st.session_state.chat_selected_categories.get(st.session_state.active_window, random.sample(list(category_topics.keys()), 3))

    for category in selected_categories:
        topic_description = category_topics[category]
        with st.expander(category, expanded=False):
            if not st.session_state.dynamic_prompts[category]:
                st.session_state.dynamic_prompts[category] = fetch_prompts_for_category(topic_description)
            for prompt in st.session_state.dynamic_prompts[category]:
                st.button(
                    prompt, 
                    key=f"prompt_{prompt}", 
                    on_click=handle_prompt_click, 
                    args=(prompt,)
                )

messages = st.session_state.chat_windows[st.session_state.active_window]

for message in messages:
    avatar = '💡' if message["role"] == "assistant" else '👤'
    timestamp = message.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input("Message Groqify..."):
    st.session_state.chat_windows[st.session_state.active_window].append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar='👤'):
        st.markdown(prompt)

    try:
        with st.spinner('Groqify is preparing an answer...'):
            system_message = {
                "role": "system",
                "content": "You are a helpful assistant. Please provide clear and concise answers without unnecessary details."
            }
            
            messages = [system_message] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.chat_windows[st.session_state.active_window]
            ]
            
            chat_completion = client.chat.completions.create(
                model=st.session_state.selected_model, 
                messages=messages,
                max_tokens=models[st.session_state.selected_model]["tokens"],  
                temperature=0.5,  
                top_p=0.8 
            )

            response_text = chat_completion.choices[0].message.content

            MAX_RESPONSE_LENGTH = 3000  
            if len(response_text) > MAX_RESPONSE_LENGTH:
                response_text = response_text[:MAX_RESPONSE_LENGTH].rstrip() + "..."

            with st.chat_message("assistant", avatar="💡"):
                st.markdown(response_text)

            st.session_state.chat_windows[st.session_state.active_window].append(
                {"role": "assistant", "content": response_text}
            )

    except Exception as e:
        st.error(f"Error: {e}", icon="🚨")