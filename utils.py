import os
import logging
from typing import List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator

#sets up logging and environment variables
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in environment variables")

#model that handles multiple choice creation
class MultipleChoiceItem(BaseModel):
    content: str = Field(description="Question text for multiple choice")
    choices: List[str] = Field(description="Four possible answer options")
    solution: str = Field(description="Correct option from the choices")

    @validator("content", pre=True)
    def normalize_question_content(cls, value):
        if isinstance(value, dict):
            return value.get("description", str(value))
        return str(value)
#model that handles fill in the blank creation
class FillInTheBlankQuestion(BaseModel):
    statement: str = Field(description="Incomplete sentence with blank")
    solution: str = Field(description="Word/phrase to fill the blank")

    @validator("statement", pre=True)
    def normalize_statement_content(cls, value):
        if isinstance(value, dict):
            return value.get("description", str(value))
        return str(value)

#model that handles question generation and feedback
class QueryEngine:
    def __init__(self):
        self.ai_client = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0.9,
        )

    #generates a multiple-choice question
    def create_multiple_choice(self, subject: str, complexity: str = "medium") -> MultipleChoiceItem:
        choice_parser = PydanticOutputParser(pydantic_object=MultipleChoiceItem)
        question_template = PromptTemplate(
            template=(
                "Create a {complexity} multiple-choice question about {subject}.\n\n"
                "Provide a JSON structure with these exact fields:\n"
                "- 'content': Clear question text\n"
                "- 'choices': 4 possible answers\n"
                "- 'solution': Correct choice\n\n"
                "Example structure:\n"
                '{{\n'
                '    "content": "What is Earth\'s natural satellite?",\n'
                '    "choices": ["Mars", "Moon", "Sun", "Venus"],\n'
                '    "solution": "Moon"\n'
                '}}\n\n'
                "Your response:"
            ),
            input_variables=["subject", "complexity"],
        )

        max_retries = 3
        for retry in range(max_retries):
            try:
                result = self.ai_client.invoke(question_template.format(subject=subject, complexity=complexity))
                parsed = choice_parser.parse(result.content)
                
                if not parsed.content or len(parsed.choices) != 4:
                    raise ValueError("Invalid question structure")
                if parsed.solution not in parsed.choices:
                    raise ValueError("Solution not in options")
                return parsed
            except Exception as error:
                log.warning(f"Generation attempt {retry + 1} unsuccessful: {error}")
                if retry == max_retries - 1:
                    raise RuntimeError(f"Multiple choice generation failed after {max_retries} tries: {error}")

    #generates a fill-in-the-blank question
    def create_fill_in_the_blank(self, subject: str, complexity: str = "medium") -> FillInTheBlankQuestion:
        fill_blank_parser = PydanticOutputParser(pydantic_object=FillInTheBlankQuestion)
        fill_blank_template = PromptTemplate(
            template=(
                "Create a {complexity} fill-in-the-blank question about {subject}.\n\n"
                "Provide a JSON structure with these exact fields:\n"
                "- 'statement': Sentence containing '_____'\n"
                "- 'solution': Correct word or phrase to fill the blank\n\n"
                "Example structure:\n"
                '{{\n'
                '    "statement": "Photosynthesis occurs in _____.",\n'
                '    "solution": "chloroplasts"\n'
                '}}\n\n'
                "Your response:"
            ),
            input_variables=["subject", "complexity"],
        )

        max_retries = 3
        for retry in range(max_retries):
            try:
                result = self.ai_client.invoke(fill_blank_template.format(subject=subject, complexity=complexity))
                parsed = fill_blank_parser.parse(result.content)
                
                if "_____" not in parsed.statement:
                    parsed.statement = parsed.statement.replace("___", "_____")
                    if "_____" not in parsed.statement:
                        raise ValueError("Missing blank placeholder")
                return parsed
            except Exception as error:
                log.warning(f"Fill-in-the-blank attempt {retry + 1} failed: {error}")
                if retry == max_retries - 1:
                    raise RuntimeError(f"Fill-in-the-blank question generation failed after {max_retries} attempts: {error}")

    #generates feedback for user responses once the quiz is submitted
    def produce_feedback(self, query: str, attempt: str, answer: str) -> str:
        critique_template = PromptTemplate(
            template=(
                "Original question:\n{query}\n\n"
                "User response: {attempt}\n"
                "Correct answer: {answer}\n\n"
                "Provide constructive feedback comparing the response to the correct answer. "
                "Explain misconceptions without revealing the answer directly. "
                "Offer guidance for improvement."
            ),
            input_variables=["query", "attempt", "answer"],
        )

        try:
            response = self.ai_client.invoke(critique_template.format(query=query, attempt=attempt, answer=answer))
            return response.content
        except Exception as error:
            log.error(f"Feedback generation error: {error}")
            return "Temporary feedback unavailable. Review materials and retry."

    #generates a hint for a question if the user wants
    def create_hint(self, question: str) -> str:
        guidance_template = PromptTemplate(
            template=(
                "Question requiring assistance:\n{question}\n\n"
                "Suggest a helpful clue to steer towards the solution. "
                "Provide conceptual guidance rather than direct answers. "
                "Focus on critical thinking elements."
            ),
            input_variables=["question"],
        )

        try:
            response = self.ai_client.invoke(guidance_template.format(question=question))
            return response.content
        except Exception as error:
            log.error(f"Hint generation failure: {error}")
            return "Hint unavailable currently. Please reconsider the question."