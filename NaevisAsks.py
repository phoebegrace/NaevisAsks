import streamlit as st
from openai import AsyncOpenAI
import asyncio
import random
import difflib

# Instantiate the OpenAI async client
client = AsyncOpenAI(api_key=st.secrets["API_key"])

# Function to load CSS
def load_css():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #132124;
        }
        .main-title {
            text-align: center;
            color: #fff;
        }
        .sidebar .sidebar-content {
            background-color: #2e3b4e;
            color: white;
        }
        .css-1aumxhk {
            font-size: 20px;
        }
        .stButton > button {
            background-color: #2a555e;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 12px;
        }
        .stButton > button:hover {
            background-color: #ffffff;
            color: #281633;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Load the CSS
load_css()

# Banner image
st.image("naevis.jpg", use_column_width=True)

async def generate_questions(difficulty, topic):
    # Use OpenAI API to generate a list of questions based on the difficulty and topic
    prompt = f"Create {difficulty} quiz questions about {topic} with their answers. Do not include multiple-choice options or the answers in the question text."
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    question_answer_pairs = [qa.strip() for qa in text.split("\n\n") if qa.strip()]
    return question_answer_pairs

def extract_question_answer(pair):
    try:
        question, answer = pair.split("Answer:")
        return question.strip(), answer.strip()
    except ValueError:
        return pair, "Unknown"

def is_answer_correct(user_answer, correct_answer):
    try:
        # Try to compare as numbers
        user_answer_num = float(user_answer)
        correct_answer_num = float(correct_answer)
        return abs(user_answer_num - correct_answer_num) < 1e-6  # Small tolerance for floating point comparison
    except ValueError:
        # Fall back to string comparison if not numeric
        return difflib.SequenceMatcher(None, user_answer.lower().strip(), correct_answer.lower().strip()).ratio() > 0.8

def main():
    st.markdown("<h1 class='main-title'>Naevis Asks</h1>", unsafe_allow_html=True)

    # Initialize score in session state
    if "score" not in st.session_state:
        st.session_state.score = 0
        
    # Initialize other necessary session state attributes
    if "question_answer_pairs" not in st.session_state:
        st.session_state.question_answer_pairs = []
    if "question" not in st.session_state:
        st.session_state.question = ""
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    if "user_answer" not in st.session_state:
        st.session_state.user_answer = ""
    if "checked" not in st.session_state:
        st.session_state.checked = False
    if "answer_correct" not in st.session_state:
        st.session_state.answer_correct = None

    # Score values based on difficulty level
    score_values = {"easy": 1, "medium": 2, "hard": 3}

    # Selection for topic
    topic = st.selectbox("Select a topic:", ["Trivia", "Math", "KPOP", "Entertainment", "Philippine History", "Korean Knowledge", "K-Drama", "Philippine Entertainment"])
    
    # Selection for difficulty level
    difficulty = st.selectbox("Select the difficulty level:", ["easy", "medium", "hard"])

    # Generate new questions if button is clicked
    if st.button("Generate Question"):
        with st.spinner('Generating questions...'):
            question_answer_pairs = asyncio.run(generate_questions(difficulty, topic))
            if question_answer_pairs:
                st.session_state.question_answer_pairs = question_answer_pairs
                pair = random.choice(question_answer_pairs)
                question, answer = extract_question_answer(pair)
                st.session_state.question = question  # Save the question in session state
                st.session_state.answer = answer  # Save the answer in session state
                st.session_state.user_answer = ""  # Clear the previous answer
                st.session_state.checked = False  # Reset checked state
                st.session_state.answer_correct = None  # Reset answer correctness
                
    # Display the current question
    if st.session_state.question:
        st.markdown(f"<h3>Question:</h3><p>{st.session_state.question}</p>", unsafe_allow_html=True)
        user_answer = st.text_input("Your answer:", value=st.session_state.user_answer)

        # Check answer button
        if st.button("Submit Answer", key="check_answer"):
            st.session_state.user_answer = user_answer  # Store the user's answer
            st.session_state.checked = True  # Mark as checked
            st.session_state.answer_correct = is_answer_correct(user_answer, st.session_state.answer)
            if st.session_state.answer_correct:
                st.success("Correct!")
                st.session_state.score += score_values[difficulty]
            else:
                st.error(f"Incorrect! The correct answer was: {st.session_state.answer}")
                    
        # "I am correct" button
        if st.session_state.checked and not st.session_state.answer_correct:
            if st.button("I am Correct", key="i_am_correct"):
                st.success("You confirmed your answer as correct!")
                st.session_state.score += score_values[difficulty]
    

    # Display the current score
    st.markdown(f"<h3>Your current score is: {st.session_state.score}</h3>", unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
