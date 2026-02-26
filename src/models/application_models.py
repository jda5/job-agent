from pydantic import BaseModel, Field


class ApplicationQuestion(BaseModel):
    """
    Represents a job application question.

    Attributes:
        question: The text of the application question.
        answer: The drafted answer to the application question.
    """

    question: str = Field(..., description="The text of the application question.")
    answer: str = Field(..., description="The drafted answer to the application question.")


class ApplicationResponse(BaseModel):
    """
    Structured output format for the Writer Agent's response.

    Attributes:
        cover_letter: The drafted cover letter text.
        question_answers: A list of application questions and their drafted answers.
    """

    cover_letter: str = Field(
        ..., description="The drafted cover letter text.", min_length=20, max_length=5000
    )
    question_answers: list[ApplicationQuestion] = Field(
        ..., description="A list of application questions and their drafted answers."
    )
