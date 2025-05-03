import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils import QueryEngine

#sets up theme and styling for the app
def configure_app_theme():
    st.set_page_config(
        page_title="AI-Powered Quiz Platform",
        page_icon="🧠",
        layout="centered",
        initial_sidebar_state="expanded",
    )

    custom_css = """
    <style>
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    .stButton > button { width: 100%; padding: 10px; border-radius: 5px; background-color: #4CAF50; color: white; font-size: 16px; }
    .stButton > button:hover { background-color: #45a049; }
    .stExpander > div { border: 1px solid #e0e0e0; border-radius: 5px; padding: 10px; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #4CAF50; }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

#model that handles the quiz creation
class QuizController:
    def __init__(self):
        self.question_bank = []
        self.user_responses = []
        self.quiz_results = []

    #generates the quiz questions based on user input
    def create_quiz(self, generator, subject, q_type, complexity, q_count):
        self.question_bank = []
        self.user_responses = [None] * q_count
        self.quiz_results = []

        try:
            for q_index in range(q_count):
                if q_type == "Multiple Choice":
                    quiz_item = generator.create_multiple_choice(subject, complexity.lower())
                    self.question_bank.append({
                        "type": "MCQ",
                        "content": quiz_item.content,
                        "choices": quiz_item.choices,
                        "answer": quiz_item.solution,
                    })
                else:
                    quiz_item = generator.create_fill_in_the_blank(subject, complexity.lower())
                    self.question_bank.append({
                        "type": "Fill in the Blank",
                        "content": quiz_item.statement,
                        "answer": quiz_item.solution,
                    })
            return True
        except Exception as error:
            st.error(f"Question generation failed: {error}")
            return False

    #displays the questions and collects the user's responses
    def display_quiz(self):
        for idx, item in enumerate(self.question_bank):
            st.markdown(f"**Question {idx + 1}: {item['content']}**")

            if st.button(f"Show Hint for Q{idx + 1}", key=f"hint_{idx}"):
                hint_provider = QueryEngine()
                guidance = hint_provider.create_hint(item["content"])
                st.write(f"**Hint:** {guidance}")

            if item["type"] == "MCQ":
                selected = st.radio(
                    f"Choose answer for Q{idx + 1}",
                    item["choices"],
                    index=None,
                    key=f"option_{idx}",
                )
                if selected is not None:
                    self.user_responses[idx] = selected
            else:
                response = st.text_input(
                    f"Complete the blank for Q{idx + 1}",
                    key=f"blank_{idx}",
                )
                if response:
                    self.user_responses[idx] = response

    #evaluates the user's responses and generates the results
    def assess_responses(self):
        self.quiz_results = []
        for pos, (item, response) in enumerate(zip(self.question_bank, self.user_responses)):
            evaluation = {
                "q_num": pos + 1,
                "q_text": item["content"],
                "q_type": item["type"],
                "response": response,
                "correct_answer": item["answer"],
                "correct_status": False,
            }
            if item["type"] == "MCQ":
                evaluation["correct_status"] = response == item["answer"]
            else:
                evaluation["correct_status"] = response.strip().lower() == item["answer"].strip().lower()
            self.quiz_results.append(evaluation)

    #converts the results to a DataFrame
    def results_to_dataframe(self):
        return pd.DataFrame(self.quiz_results)

    #saves the results to a CSV file
    def store_results_csv(self, filename="quiz_results.csv"):
        try:
            if not self.quiz_results:
                st.warning("No results available for saving")
                return None

            results_df = self.results_to_dataframe()
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_with_timestamp = f"quiz_results_{current_time}.csv"
            os.makedirs("results", exist_ok=True)
            full_path = os.path.join("results", filename_with_timestamp)
            results_df.to_csv(full_path, index=False)
            st.success(f"Data saved to {full_path}")
            return full_path
        except Exception as error:
            st.error(f"Save operation failed: {error}")
            return None

#main app
def main_app():
    configure_app_theme()

    session = st.session_state
    if "quiz_handler" not in session:
        session.quiz_handler = QuizController()
    if "is_quiz_created" not in session:
        session.is_quiz_created = False
    if "is_quiz_submitted" not in session:
        session.is_quiz_submitted = False

    st.title("AI-Powered Quiz Platform")

    #sets up the quiz configuration in the sidebar
    with st.sidebar:
        st.header("Quiz Configuration")
        q_type = st.selectbox("Question Format", ["Multiple Choice", "Fill in the Blank"])
        subject = st.text_input("Quiz Topic", placeholder="Science, Literature, etc.")
        complexity = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        total_questions = st.number_input("Question Count", min_value=1, max_value=10, value=5)

        if st.button("Generate New Quiz"):
            session.is_quiz_submitted = False
            question_generator = QueryEngine()
            session.is_quiz_created = session.quiz_handler.create_quiz(
                question_generator, subject, q_type, complexity, total_questions
            )
            st.rerun()

    #displays quiz when it is generated
    if session.is_quiz_created and session.quiz_handler.question_bank:
        st.header("Current Quiz")

        answered_count = sum(1 for ans in session.quiz_handler.user_responses if ans is not None)
        completion = min(answered_count / len(session.quiz_handler.question_bank), 1.0)
        st.progress(completion)

        session.quiz_handler.display_quiz()

        if st.button("Finalize Quiz"):
            session.quiz_handler.assess_responses()
            session.is_quiz_submitted = True
            st.rerun()

    #displays results when quiz is submitted
    if session.is_quiz_submitted:
        st.header("Assessment Results")
        results_data = session.quiz_handler.results_to_dataframe()

        if not results_data.empty:
            correct_answers = results_data["correct_status"].sum()
            total_qs = len(results_data)
            percentage_score = (correct_answers / total_qs) * 100
            st.write(f"**Performance: {correct_answers}/{total_qs} ({percentage_score:.1f}%)**")

            for _, record in results_data.iterrows():
                q_id = record["q_num"]
                if record["correct_status"]:
                    st.success(f"✅ Question {q_id}: {record['q_text']}")
                    st.write(f"Your Response: {record['response']}")
                    st.write(f"Correct Answer: {record['correct_answer']}")
                    st.write("**Analysis:** Correct answer!")
                else:
                    st.error(f"❌ Question {q_id}: {record['q_text']}")
                    st.write(f"Your Response: {record['response']}")
                    st.write(f"Correct Answer: {record['correct_answer']}")
                    feedback_gen = QueryEngine()
                    critique = feedback_gen.produce_feedback(
                        query=record["q_text"],
                        attempt=record["response"],
                        answer=record["correct_answer"]
                    )
                    st.write(f"**Improvement:** {critique}")
                st.markdown("---")

            if st.button("Archive Results"):
                stored_file = session.quiz_handler.store_results_csv()
                if stored_file:
                    with open(stored_file, "rb") as file:
                        st.download_button(
                            label="Download Assessment",
                            data=file.read(),
                            file_name=os.path.basename(stored_file),
                            mime="text/csv",
                        )
        else:
            st.warning("No assessment data available")

if __name__ == "__main__":
    main_app()