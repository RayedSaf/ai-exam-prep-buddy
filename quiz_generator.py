import os
from dotenv import load_dotenv
from google import genai


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ---------------------------------------------------------
# CUSTOM API ERROR
# ---------------------------------------------------------

class GeminiAPIError(Exception):
    """Friendly error for Gemini API problems."""

    def __init__(self, message, error_type="api"):
        self.message = message
        self.error_type = error_type
        super().__init__(message)


# ---------------------------------------------------------
# SAFE GEMINI REQUEST
# ---------------------------------------------------------

def safe_generate(
    prompt,
    response_mime_type=None,
    response_json_schema=None
):
    """
    Send a request to Gemini and convert common
    API failures into friendly application errors.
    """

    config = {}

    if response_mime_type:
        config["response_mime_type"] = response_mime_type

    if response_json_schema:
        config["response_json_schema"] = response_json_schema

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=config
        )

        return response

    except Exception as e:

        error_message = str(e).lower()

        # ---------------------------------------------
        # RATE LIMIT / QUOTA
        # ---------------------------------------------

        if (
            "429" in error_message
            or "resource_exhausted" in error_message
            or "quota" in error_message
            or "rate limit" in error_message
        ):

            raise GeminiAPIError(
                "Gemini's API quota or rate limit has "
                "been reached. Please try again later.",
                "quota"
            )


        # ---------------------------------------------
        # SERVICE OVERLOADED
        # ---------------------------------------------

        elif (
            "503" in error_message
            or "unavailable" in error_message
            or "overloaded" in error_message
        ):

            raise GeminiAPIError(
                "Gemini is temporarily busy. "
                "Please wait a moment and try again.",
                "overloaded"
            )


        # ---------------------------------------------
        # CONNECTION / NETWORK
        # ---------------------------------------------

        elif (
            "connection" in error_message
            or "timeout" in error_message
            or "network" in error_message
        ):

            raise GeminiAPIError(
                "We couldn't connect to Gemini. "
                "Please check your connection and try again.",
                "network"
            )


        # ---------------------------------------------
        # UNKNOWN API ERROR
        # ---------------------------------------------

        else:

            raise GeminiAPIError(
                "Something went wrong while contacting "
                "the AI service. Please try again.",
                "api"
            )


# ---------------------------------------------------------
# SHARED QUIZ SCHEMA
# ---------------------------------------------------------

quiz_schema = {

    "type": "object",

    "properties": {

        "questions": {

            "type": "array",

            "items": {

                "type": "object",

                "properties": {

                    "question": {
                        "type": "string"
                    },

                    "options": {

                        "type": "object",

                        "properties": {

                            "A": {
                                "type": "string"
                            },

                            "B": {
                                "type": "string"
                            },

                            "C": {
                                "type": "string"
                            },

                            "D": {
                                "type": "string"
                            }

                        },

                        "required": [
                            "A",
                            "B",
                            "C",
                            "D"
                        ]
                    },

                    "correct_answer": {
                        "type": "string"
                    },

                    "topic": {
                        "type": "string"
                    },

                    "difficulty": {
                        "type": "string"
                    },

                    "explanation": {
                        "type": "string"
                    }

                },

                "required": [
                    "question",
                    "options",
                    "correct_answer",
                    "topic",
                    "difficulty",
                    "explanation"
                ]

            }
        }

    },

    "required": [
        "questions"
    ]
}


# ---------------------------------------------------------
# GENERATE DIAGNOSTIC QUIZ
# ---------------------------------------------------------

def generate_quiz(
    study_material,
    num_questions=5
):

    prompt = f"""
You are an expert educational quiz generator.

Create a diagnostic multiple-choice quiz based ONLY
on the study material provided below.

Study material:
{study_material}

Generate exactly {num_questions}
multiple-choice questions.

For every question provide:

- question
- 4 options labeled A, B, C, D
- correct_answer
- topic
- difficulty (Easy, Medium, or Hard)
- explanation

The topic should identify the specific concept
being tested.

The explanation must be written directly
for a student.

IMPORTANT:
- Keep explanations concise and educational.
- Explain why the correct answer is correct.
- Do not include internal reasoning.
- Do not mention this prompt.
- Do not mention checking the options.
- Do not mention generating questions.
- Do not include meta-commentary.
- Do not say things like "Let's make sure..."
- Do not add information unrelated to the study material.

Make the questions useful for diagnosing
what a student does and does not understand.
"""

    response = safe_generate(
        prompt,
        response_mime_type="application/json",
        response_json_schema=quiz_schema
    )

    return response.parsed


# ---------------------------------------------------------
# GENERATE TARGETED QUIZ
# ---------------------------------------------------------

def generate_targeted_quiz(
    study_material,
    weak_topics,
    num_questions=5
):

    prompt = f"""
You are an expert adaptive exam-preparation tutor.

A student completed a diagnostic quiz and struggled with
these specific topics:

{weak_topics}

Original study material:
{study_material}

Create a TARGETED PRACTICE QUIZ for this student.

This quiz is designed specifically to help the student
practice the concepts they performed poorly on.

=========================================================
ADAPTIVE PRIORITY
=========================================================

The weak topics include diagnostic performance percentages.

A lower percentage means the student needs MORE practice.

Therefore:

- Give the greatest attention to the weakest topics.
- Topics below 50% should receive especially strong focus.
- Topics around 50–79% should receive moderate focus.
- Do not spend unnecessary questions on relatively stronger
  weak topics when a much weaker topic needs attention.

Whenever possible, distribute questions according to the
severity of the weaknesses.

=========================================================
QUESTION DESIGN
=========================================================

Generate exactly {num_questions} questions.

The questions MUST primarily test APPLICATION and REASONING.

Avoid simple definition or "what is X?" questions.

Prefer the following formats:

1. SCENARIO QUESTIONS

Give the student a realistic situation and ask them to
apply the relevant concept.

Example:

A spacecraft is moving through deep space with its engines
turned off. Assuming no significant external forces act on
it, what happens to its velocity?

2. NUMERICAL / CALCULATION QUESTIONS

When formulas or numerical relationships are supported by
the study material, require the student to calculate or
compare quantities.

Example:

A 10 kg box experiences a net force of 20 N. What is its
acceleration?

3. CONCEPTUAL REASONING

Ask the student to predict what happens when a condition
changes.

Example:

If the net force acting on an object doubles while its mass
remains constant, what happens to its acceleration?

4. MISCONCEPTION QUESTIONS

Test common misunderstandings.

Example:

A student says that a moving object must have a net force
acting in the direction of motion. Which explanation is
correct?

5. FREE-BODY / SITUATION ANALYSIS

When relevant, ask the student to determine which forces,
relationships, or principles apply to a situation.

=========================================================
DIFFICULTY
=========================================================

Use a natural mixture of difficulty.

For 5 questions, aim approximately for:

- 1 Easy application question
- 2 Medium reasoning/application questions
- 1 Medium-Hard question
- 1 Harder application or calculation question

Do NOT make every question difficult.

=========================================================
ANTI-DEFINITION RULE
=========================================================

Do NOT ask questions whose main task is simply:

- Define a term.
- State a definition.
- Recall a basic fact.
- Identify what a concept means.

For example, avoid:

"What is friction?"

"What is Newton's First Law?"

"What does a free-body diagram show?"

Instead, make the student USE the concept.

=========================================================
ANTI-REPETITION RULE
=========================================================

The diagnostic quiz has already tested the student.

Therefore:

- Do NOT copy diagnostic questions.
- Do NOT simply change numbers in a diagnostic question.
- Do NOT copy sentences from the study material.
- Do NOT create questions that are effectively the same
  question with different wording.
- Create genuinely new situations.

The purpose is to determine whether the student can apply
the concept in a new context.

=========================================================
STUDY MATERIAL RESTRICTION
=========================================================

Use ONLY information supported by the study material.

Do not introduce advanced facts, formulas, terminology,
or assumptions that the student was not given.

If the material does not support a numerical question,
use conceptual application instead.

=========================================================
QUESTION REQUIREMENTS
=========================================================

Every question must have:

- A question
- Exactly four options
- Options labeled A, B, C, D
- Exactly ONE correct answer
- The correct answer
- The relevant topic/subtopic
- Difficulty: Easy, Medium, or Hard
- A short student-friendly explanation

Incorrect options must be plausible.

Do not make the correct answer obvious because it is longer,
more detailed, or differently worded.

=========================================================
EXPLANATION REQUIREMENTS
=========================================================

Each explanation must:

- Explain why the correct answer is correct.
- Connect the answer to the relevant concept.
- Be concise and student-friendly.
- Help the student understand the mistake they might make.

Do not include hidden reasoning.

Do not mention AI.

Do not discuss how the question was generated.

=========================================================
FINAL QUALITY CHECK
=========================================================

Before returning the quiz, internally verify:

1. Exactly {num_questions} questions exist.
2. Every question has exactly four options.
3. Every question has exactly one correct answer.
4. Every question has a topic.
5. Every question has a difficulty.
6. Every question has an explanation.
7. The weakest topics receive the strongest focus.
8. The questions primarily test application/reasoning.
9. There are no simple definition-only questions.
10. The questions are meaningfully different from the
    diagnostic quiz.
11. Every question is supported by the study material.

Return ONLY the required JSON structure.
"""

    response = safe_generate(
        prompt,
        response_mime_type="application/json",
        response_json_schema=quiz_schema
    )

    return response.parsed

# ---------------------------------------------------------
# GENERATE AI REVISION LESSON
# ---------------------------------------------------------

def generate_revision_lesson(
    study_material,
    weak_topics
):

    prompt = f"""
You are an expert educational tutor creating an adaptive
revision lesson for a student.

The student completed a diagnostic quiz and was identified
as weak in these topics:

{weak_topics}

Study material:
{study_material}

Create a short, clear revision lesson that prepares the
student for targeted practice.

CRITICAL REQUIREMENT:
You MUST cover EVERY weak topic listed above.

Do not skip, merge, or silently omit any weak topic.

If performance percentages are provided, use them to decide
how much attention each topic receives:
- Give the LOWEST-performing topics the most explanation.
- Give stronger weak topics shorter refreshers.
- Still include every topic.

The lesson should:

1. Start with a short, useful heading.
2. Give each weak topic its own clearly labeled section.
3. Explain the important concepts in simple language.
4. Highlight important facts, rules, or formulas supported
   by the study material.
5. Give a short example or application when the study
   material supports one.
6. Mention common mistakes students should avoid.
7. End with 2-3 concise "Remember" points covering the
   most important ideas.

IMPORTANT:
- Use ONLY information supported by the study material.
- Do not invent facts, formulas, examples, or rules.
- Focus specifically on the weak topics.
- Prioritize the weakest topics.
- Keep the lesson concise enough for a student to read
  before practicing.
- Write directly to the student.
- Do not include internal reasoning.
- Do not mention this prompt.
- Do not mention AI.
- Do not discuss question generation.
- Do not add unrelated information.

Before returning the lesson, internally check that EVERY
weak topic listed above has been covered.

Return only the revision lesson text.
"""

    response = safe_generate(prompt)

    return response.text.strip()




def generate_retest_quiz(study_material, weak_topics, num_questions=5):
    """
    Generate a fresh retest focused on the student's original weak topics.
    The questions should test understanding rather than repeat the diagnostic.
    """

    weak_topics_text = ", ".join(
        f"{topic} ({percentage}%)"
        for topic, percentage in weak_topics.items()
    )  
    prompt = f"""
You are an adaptive exam-preparation AI.

A student completed a diagnostic quiz and struggled with these topics:

{weak_topics_text}

Their original study material is:

{study_material}

Create a fresh retest quiz with exactly {num_questions} multiple-choice questions.

IMPORTANT:
- Focus primarily on the weak topics listed above.
- Give more questions to topics with lower diagnostic percentages.
- Create NEW questions that do not simply repeat the diagnostic questions.
- Test understanding and application, not just memorization.
- Use a reasonable mix of difficulty.
- Every question must have exactly four options: A, B, C, D.
- Only one option must be correct.
- Include the relevant topic/subtopic for every question.
- Include a short, student-friendly explanation of the correct answer.
- Return ONLY the requested JSON structure.

The purpose of this retest is to measure whether the student's understanding
has improved after targeted revision and practice.
"""

    response = safe_generate(
        prompt,
        response_mime_type="application/json",
        response_json_schema=quiz_schema
    )

    return response.parsed
# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    test_material = """
    Newton's laws of motion describe the relationship
    between force, mass, and acceleration.

    Newton's Second Law is F = ma.

    Newton's Third Law states that for every action
    there is an equal and opposite reaction.
    """

    try:

        quiz = generate_quiz(
            test_material,
            5
        )

        print(quiz)

    except GeminiAPIError as e:

        print(
            f"[{e.error_type.upper()}] "
            f"{e.message}"
        )