import streamlit as st

from quiz_generator import (
    generate_quiz,
    generate_targeted_quiz,
    generate_revision_lesson,
    generate_retest_quiz,
    GeminiAPIError
)


st.set_page_config(
    page_title="AI Exam Prep Buddy",
    page_icon="📚",
    layout="centered"
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 820px;
    }
    h1, h2, h3 {
        letter-spacing: -0.3px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📚 AI Exam Prep Buddy")

st.markdown(
    """
    ### Find what you don't know. Fix it. Test again.

    **Learn → Diagnose → Revise → Practice → Retest**
    
    Your AI-powered study companion that identifies your weak areas
    and creates a personalized path to improve them.
    """
)
# ---------------------------------------------------------
# HELPER — NORMALIZE TOPIC NAMES
# ---------------------------------------------------------

def normalize_topic(topic):

    topic = topic.lower().strip()

    replacements = {
        " of motion": "",
        " motion": "",
        " laws": " law",
        " diagrams": " diagram",
    }

    for old, new in replacements.items():
        topic = topic.replace(old, new)

    return topic


st.divider()


# ---------------------------------------------------------
# LEARNING JOURNEY
# ---------------------------------------------------------

def show_learning_journey():

    # Determine the student's current stage
    if "retest_score" in st.session_state:
        current_stage = 5
        next_action = "🎉 Retest complete — review your learning progress!"
    elif "targeted_score" in st.session_state:
        current_stage = 4
        next_action = "🔄 Next: Take the retest to measure your improvement."
    elif "revision_lesson" in st.session_state:
        current_stage = 3
        next_action = "🎯 Next: Practice your weak areas."
    elif "initial_score" in st.session_state:
        current_stage = 2

        weak_topics = st.session_state.get(
            "weak_topics",
            {}
        )

        if weak_topics:
            priority_topic = min(
                weak_topics,
                key=weak_topics.get
            )

            next_action = (
                f"📚 Next: Revise **{priority_topic}** "
                f"first."
            )
        else:
            next_action = (
                "🎉 Great performance! "
                "You're ready to challenge yourself again."
            )

    else:
        current_stage = 1
        next_action = (
            "📝 Next: Enter your study material "
            "and generate a diagnostic quiz."
        )

    stages = [
        ("📖", "Learn", "Study your material"),
        ("🧠", "Diagnose", "Find weak areas"),
        ("📚", "Revise", "Fix your gaps"),
        ("🎯", "Practice", "Apply what you learned"),
        ("🔄", "Retest", "Measure improvement"),
    ]

    st.markdown("### 🧭 Your Learning Journey")

    columns = st.columns(5)

    for index, (icon, name, description) in enumerate(
        stages,
        start=1
    ):
        with columns[index - 1]:

            if index < current_stage:
                st.success(
                    f"{icon} **{name}**\n\n"
                    f"✓ Complete\n\n"
                    f"{description}"
                )

            elif index == current_stage:
                st.info(
                    f"{icon} **{name}**\n\n"
                    f"● Current\n\n"
                    f"{description}"
                )

            else:
                st.markdown(
                    f"""
                    <div style="
                        padding: 14px 12px;
                        border-radius: 10px;
                        border: 1px solid rgba(128,128,128,0.2);
                        background: rgba(128,128,128,0.05);
                        min-height: 108px;
                    ">
                        <div style="font-weight: 600; margin-bottom: 6px; opacity: 0.85;">
                            {icon} {name}
                        </div>
                        <div style="font-size: 12px; opacity: 0.55; margin-bottom: 6px;">
                            ○ Upcoming
                        </div>
                        <div style="font-size: 13px; opacity: 0.65;">
                            {description}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.info(
        f"**Your next step:** {next_action}"
    )

    st.divider()


show_learning_journey()

# ---------------------------------------------------------
# HELPER — DISPLAY AI ERRORS
# ---------------------------------------------------------

def show_ai_error(error):

    if error.error_type == "quota":

        st.error(
            "⚠️ **AI quota reached**\n\n"
            "The AI service has reached its current "
            "usage limit. Please try again later."
        )

    elif error.error_type == "overloaded":

        st.warning(
            "⚠️ **AI service is busy**\n\n"
            "Gemini is temporarily overloaded. "
            "Please wait a moment and try again."
        )

    elif error.error_type == "network":

        st.warning(
            "🌐 **Connection problem**\n\n"
            "We couldn't connect to the AI service. "
            "Please check your internet connection "
            "and try again."
        )

    else:

        st.error(
            "⚠️ **Something went wrong**\n\n"
            f"{error.message}"
        )

def render_question_card(index, total, question, label="QUESTION"):

    difficulty = question.get("difficulty", "Medium")

    st.markdown(
        f"""
        <div style="
            padding: 18px 20px;
            border-radius: 12px;
            border: 1px solid rgba(128,128,128,0.3);
            margin-bottom: 14px;
        ">
            <div style="
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.5px;
                opacity: 0.6;
                margin-bottom: 10px;
            ">
                {label} {index} OF {total}
            </div>
            <div style="
                font-size: 17px;
                font-weight: 600;
                margin-bottom: 10px;
                line-height: 1.4;
            ">
                {question['question']}
            </div>
            <div style="font-size: 13px; opacity: 0.75;">
                📌 {question['topic']} &nbsp;·&nbsp; {difficulty}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# STUDY MATERIAL
# ---------------------------------------------------------

st.subheader("📝 Enter your study material")

study_material = st.text_area(
    "Paste your notes, textbook content, or topic here:",
    height=250,
    placeholder="Example: Newton's laws of motion..."
)

num_questions = st.slider(
    "Number of questions",
    min_value=5,
    max_value=10,
    value=5
)

generate_button = st.button(
    "🚀 Generate Quiz",
    type="primary"
)


# ---------------------------------------------------------
# GENERATE INITIAL QUIZ
# ---------------------------------------------------------

if generate_button:

    if not study_material.strip():

        st.warning(
            "Please enter some study material first."
        )

    else:

        try:

            with st.spinner(
                "🧠 Creating your diagnostic quiz..."
            ):

                quiz = generate_quiz(
                    study_material,
                    num_questions
                )

            st.session_state.quiz = quiz
            st.session_state.study_material = study_material

            # Clear old quiz answers
            for i in range(1, 11):
                st.session_state.pop(f"question_{i}", None)
                st.session_state.pop(f"targeted_question_{i}", None)
                st.session_state.pop(f"retest_question_{i}", None)

            # Clear old results
            st.session_state.pop("topic_stats", None)
            st.session_state.pop("weak_topics", None)
            st.session_state.pop("diagnostic_weak_topics", None)

            st.session_state.pop("revision_lesson", None)

            st.session_state.pop("targeted_quiz", None)
            st.session_state.pop("targeted_score", None)
            st.session_state.pop("targeted_percentage", None)

            st.session_state.pop("initial_score", None)
            st.session_state.pop("initial_percentage", None)

            st.session_state.pop("retest_ready", None)
            st.session_state.pop("retest_quiz", None)
            st.session_state.pop("retest_score", None)
            st.session_state.pop("retest_percentage", None)
            st.session_state.pop("retest_topic_stats", None)
            st.session_state.pop("retest_topic_percentages", None)

            st.success(
                "Quiz generated successfully! 🎉"
            )

        except GeminiAPIError as error:

            show_ai_error(error)


# ---------------------------------------------------------
# DISPLAY INITIAL QUIZ
# ---------------------------------------------------------

if "quiz" in st.session_state:

    st.divider()

    st.subheader(
        "🧠 Your Diagnostic Quiz"
    )

    st.caption(
        "This quiz identifies the topics you understand "
        "well and the areas that need more attention."
    )

    total_questions = len(
        st.session_state.quiz["questions"]
    )

    for i, question in enumerate(
        st.session_state.quiz["questions"],
        start=1
    ):

        render_question_card(
            i,
            total_questions,
            question,
            label="QUESTION"
        )

        options = question["options"]

        st.radio(
            "Choose your answer:",
            options.keys(),
            format_func=lambda key:
                f"{key}: {options[key]}",
            key=f"question_{i}"
        )
    st.divider()

    submit_button = st.button(
        "✅ Submit Quiz",
        type="primary"
    )


    # -----------------------------------------------------
    # SCORE INITIAL QUIZ
    # -----------------------------------------------------

    if submit_button:

        score = 0

        total = len(
            st.session_state.quiz["questions"]
        )

        topic_stats = {}

        for i, question in enumerate(
            st.session_state.quiz["questions"],
            start=1
        ):

            user_answer = st.session_state.get(
                f"question_{i}"
            )

            correct_answer = question[
                "correct_answer"
            ]

            topic = question["topic"]

            if topic not in topic_stats:

                topic_stats[topic] = {
                    "correct": 0,
                    "total": 0
                }

            topic_stats[topic]["total"] += 1

            if user_answer == correct_answer:

                score += 1

                topic_stats[topic][
                    "correct"
                ] += 1

        percentage = round(
            (score / total) * 100
        )

        st.success(
            f"🎯 You scored {score}/{total} "
            f"({percentage}%)"
        )

        st.session_state.initial_score = score
        st.session_state.initial_percentage = percentage


        # -------------------------------------------------
        # REVIEW WRONG ANSWERS
        # -------------------------------------------------

        st.subheader(
            "🔎 Review Your Answers"
        )

        wrong_answers = []

        for i, question in enumerate(
            st.session_state.quiz["questions"],
            start=1
        ):

            user_answer = st.session_state.get(
                f"question_{i}"
            )

            correct_answer = question[
                "correct_answer"
            ]

            if user_answer != correct_answer:

                wrong_answers.append(question)

                st.error(
                    f"❌ Question {i}: "
                    f"You got this one wrong."
                )

                st.write(
                    question["question"]
                )

                if user_answer:

                    st.write(
                        f"**Your answer:** "
                        f"{user_answer}: "
                        f"{question['options'][user_answer]}"
                    )

                else:

                    st.write(
                        "**Your answer:** Not answered"
                    )

                st.write(
                    f"**Correct answer:** "
                    f"{correct_answer}: "
                    f"{question['options'][correct_answer]}"
                )

                st.info(
                    f"💡 **Why:** "
                    f"{question['explanation']}"
                )

        if not wrong_answers:

            st.success(
                "🎉 Perfect! You got every "
                "question correct."
            )


        # -------------------------------------------------
        # TOPIC PERFORMANCE
        # -------------------------------------------------

        st.subheader(
            "📊 Your Topic Performance"
        )

        st.caption(
            "Your score by topic. Lower scores indicate "
            "areas that should be prioritized for revision."
        )

        topic_percentages = {}

        # Sort topics from weakest to strongest
        sorted_topics = sorted(
            topic_stats.items(),
            key=lambda item: (
                item[1]["correct"] / item[1]["total"]
            )
        )

        for topic, stats in sorted_topics:

            topic_percentage = round(
                (stats["correct"] /
                stats["total"]) * 100
            )

            topic_percentages[
                topic
            ] = topic_percentage

            # Determine performance level
            if topic_percentage < 50:

                emoji = "🔴"
                priority = "HIGH PRIORITY"

            elif topic_percentage < 80:

                emoji = "🟠"
                priority = "NEEDS PRACTICE"

            else:

                emoji = "🟢"
                priority = "STRONG"

            st.markdown(
                f"### {emoji} {topic}"
            )

            st.progress(
                topic_percentage / 100
            )

            st.write(
                f"**{topic_percentage}%** — "
                f"{stats['correct']}/{stats['total']} correct"
                f"  ·  **{priority}**"
            )

        st.session_state.topic_stats = topic_stats


        # -------------------------------------------------
        # IDENTIFY WEAK TOPICS
        # -------------------------------------------------

        weak_topics = {
            topic: percentage
            for topic, percentage
            in topic_percentages.items()
            if percentage < 80
        }

        st.session_state.weak_topics = weak_topics
        # Save the diagnostic weaknesses so we can
        # compare them against the retest later.
        st.session_state.diagnostic_weak_topics = (
            weak_topics.copy()
        )


        # -------------------------------------------------
        # REVISION PRIORITY
        # -------------------------------------------------

        if weak_topics:

            priority_topic = min(
                weak_topics,
                key=weak_topics.get
            )

            weakest_percentage = (
                weak_topics[priority_topic]
            )

            st.warning(
                f"📚 **Revise first:** "
                f"{priority_topic} "
                f"({weakest_percentage}%)"
            )

        else:

            st.success(
                "🎉 Great job! You performed "
                "well across all topics."
            )


# ---------------------------------------------------------
# AI REVISION LESSON
# ---------------------------------------------------------

if (
    "weak_topics" in st.session_state
    and st.session_state.weak_topics
):

    st.divider()

    st.subheader(
        "📚 AI Revision Lesson"
    )

    st.write(
        "Before practicing again, let's review "
        "the concepts you struggled with."
    )

    weak_topics_text = ", ".join(
        f"{topic} ({percentage}%)"
        for topic, percentage
        in st.session_state.weak_topics.items()
    )   

    revision_button = st.button(
        "📚 Teach Me These Topics",
        type="primary"
    )

    if revision_button:

        try:

            with st.spinner(
                "🧠 Creating your personalized "
                "revision lesson..."
            ):

                revision_lesson = generate_revision_lesson(
                    st.session_state.study_material,
                    weak_topics_text
                )

            st.session_state.revision_lesson = (
                revision_lesson
            )

            st.success(
                "📚 Your personalized revision "
                "lesson is ready!"
            )

        except GeminiAPIError as error:

            show_ai_error(error)


# ---------------------------------------------------------
# DISPLAY AI REVISION LESSON
# ---------------------------------------------------------

if "revision_lesson" in st.session_state:

    st.divider()

    st.subheader(
        "📖 Your Personalized Revision"
    )

    st.caption(
        "This lesson was generated specifically from "
        "the topics you struggled with."
    )

    st.info(
        "💡 **How to use this lesson:** "
        "Focus on the concepts marked as weak, "
        "then use the practice quiz below to check "
        "whether you've improved."
    )

    st.markdown(
        st.session_state.revision_lesson
    )

    st.divider()

    st.success(
        "🎯 **Ready to test yourself?** "
        "Practice the weak areas below."
    )

# ---------------------------------------------------------
# TARGETED PRACTICE
# ---------------------------------------------------------

if (
    "weak_topics" in st.session_state
    and st.session_state.weak_topics
):

    st.divider()

    st.subheader(
        "🎯 Targeted Practice"
    )

    st.write(
        "You struggled with some topics. "
        "Let's practice those specifically."
    )

    weak_topics_text = ", ".join(
        f"{topic} ({percentage}%)"
        for topic, percentage
        in st.session_state.weak_topics.items()
    )

    st.info(
        f"Focus areas: {weak_topics_text}"
    )

    practice_button = st.button(
        "🎯 Practice My Weak Areas",
        type="primary"
    )

    if practice_button:

        try:

            with st.spinner(
                "🧠 Creating a targeted "
                "practice quiz..."
            ):

                targeted_quiz = generate_targeted_quiz(
                    st.session_state.study_material,
                    weak_topics_text,
                    num_questions
                )

            st.session_state.targeted_quiz = (
                targeted_quiz
            )

            st.session_state.pop(
                "targeted_score",
                None
            )

            st.success(
                "🎯 Targeted practice quiz generated!"
            )

        except GeminiAPIError as error:

            show_ai_error(error)


# ---------------------------------------------------------
# DISPLAY TARGETED QUIZ
# ---------------------------------------------------------

if "targeted_quiz" in st.session_state:

    st.divider()

    st.subheader(
        "🎯 Practice Your Weak Areas"
    )

    for i, question in enumerate(
        st.session_state.targeted_quiz["questions"],
        start=1
    ):

        render_question_card(
            i,
            len(st.session_state.targeted_quiz["questions"]),
            question,
            label="PRACTICE QUESTION"
        )

        options = question["options"]

        st.radio(
            "Choose your answer:",
            options.keys(),
            format_func=lambda key:
                f"{key}: {options[key]}",
            key=f"targeted_question_{i}"
        )

    st.divider()

    targeted_submit = st.button(
        "✅ Submit Targeted Quiz",
        type="primary"
    )


    # -----------------------------------------------------
    # SCORE TARGETED QUIZ
    # -----------------------------------------------------

    if targeted_submit:

        targeted_score = 0

        targeted_total = len(
            st.session_state.targeted_quiz[
                "questions"
            ]
        )

        for i, question in enumerate(
            st.session_state.targeted_quiz[
                "questions"
            ],
            start=1
        ):

            user_answer = st.session_state.get(
                f"targeted_question_{i}"
            )

            correct_answer = question[
                "correct_answer"
            ]

            if user_answer == correct_answer:

                targeted_score += 1

        targeted_percentage = round(
            (targeted_score /
             targeted_total) * 100
        )

        st.session_state.targeted_score = (
            targeted_score
        )

        st.session_state.targeted_percentage = (
            targeted_percentage
        )

        # Automatically move to the retest stage
        st.session_state.retest_ready = True

        st.success(
            f"🎯 Targeted quiz score: "
            f"{targeted_score}/{targeted_total} "
            f"({targeted_percentage}%)"
        )


        # -------------------------------------------------
        # REVIEW TARGETED WRONG ANSWERS
        # -------------------------------------------------

        st.subheader(
            "🔎 Review Your Practice Answers"
        )

        for i, question in enumerate(
            st.session_state.targeted_quiz[
                "questions"
            ],
            start=1
        ):

            user_answer = st.session_state.get(
                f"targeted_question_{i}"
            )

            correct_answer = question[
                "correct_answer"
            ]

            if user_answer != correct_answer:

                st.error(
                    f"❌ Practice Question {i}: "
                    f"Incorrect"
                )

                st.write(
                    question["question"]
                )

                if user_answer:

                    st.write(
                        f"**Your answer:** "
                        f"{user_answer}: "
                        f"{question['options'][user_answer]}"
                    )

                else:

                    st.write(
                        "**Your answer:** Not answered"
                    )

                st.write(
                    f"**Correct answer:** "
                    f"{correct_answer}: "
                    f"{question['options'][correct_answer]}"
                )

                st.info(
                    f"💡 **Explanation:** "
                    f"{question['explanation']}"
                )


# ---------------------------------------------------------
# IMPROVEMENT
# ---------------------------------------------------------

if (
    "targeted_percentage" in st.session_state
    and "initial_percentage" in st.session_state
):

    st.divider()

    st.subheader(
        "📈 Practice Progress"
    )

    initial = (
        st.session_state.initial_percentage
    )

    targeted = (
        st.session_state.targeted_percentage
    )

    st.write(
        f"Diagnostic score: **{initial}%**"
    )

    st.write(
        f"Targeted practice score: **{targeted}%**"
    )

    difference = targeted - initial

    if difference > 0:

        st.success(
            f"📈 Practice score improved by "
            f"**{difference} percentage points**."
        )

    elif difference < 0:

        st.warning(
            f"📉 Practice score was "
            f"{abs(difference)} percentage points "
            f"lower this time."
        )

    else:

        st.info(
            "➡️ Practice score stayed the same."
        )

    st.caption(
        "These are different question sets, "
        "so this comparison is only a rough "
        "practice indicator—not a definitive "
        "measure of learning."
    )



# ---------------------------------------------------------
# RETEST QUIZ
# ---------------------------------------------------------

if (
    "retest_ready" in st.session_state
    and st.session_state.retest_ready
):

    st.divider()

    st.subheader(
        "🔄 Retest"
    )

    st.write(
        "Let's see whether your understanding "
        "has improved."
    )

    # Generate AI retest quiz
    if "retest_quiz" not in st.session_state:

        weak_topics = st.session_state.get(
            "weak_topics",
            {}
        )

        if weak_topics:

            try:

                with st.spinner(
                    "🧠 Creating your personalized retest..."
                ):

                    st.session_state.retest_quiz = (
                        generate_retest_quiz(
                            st.session_state.study_material,
                            weak_topics,
                            num_questions
                        )
                    )

                st.success(
                    "🔄 Your personalized retest is ready!"
                )

            except GeminiAPIError as error:

                show_ai_error(error)

    # Display retest
    if "retest_quiz" in st.session_state:

        for i, question in enumerate(
            st.session_state.retest_quiz["questions"],
            start=1
        ):

            render_question_card(
                i,
                len(st.session_state.retest_quiz["questions"]),
                question,
                label="RETEST QUESTION"
            )

            options = question["options"]

            st.radio(
                "Choose your answer:",
                options.keys(),
                format_func=lambda key:
                    f"{key}: {options[key]}",
                key=f"retest_question_{i}"
            )

        st.divider()

        retest_submit = st.button(
            "✅ Submit Retest",
            type="primary"
        )


        # -------------------------------------------------
        # SCORE RETEST
        # -------------------------------------------------

        if retest_submit:

            retest_score = 0

            retest_total = len(
                st.session_state.retest_quiz[
                    "questions"
                ]
            )

            # Track performance for each topic
            retest_topic_stats = {}

            for i, question in enumerate(
                st.session_state.retest_quiz[
                    "questions"
                ],
                start=1
            ):

                user_answer = st.session_state.get(
                    f"retest_question_{i}"
                )

                correct_answer = question[
                    "correct_answer"
                ]

                topic = question["topic"]

                if topic not in retest_topic_stats:

                    retest_topic_stats[topic] = {
                        "correct": 0,
                        "total": 0
                    }

                retest_topic_stats[topic]["total"] += 1

                if user_answer == correct_answer:

                    retest_score += 1

                    retest_topic_stats[topic][
                        "correct"
                    ] += 1


            # -------------------------------------------------
            # OVERALL RETEST SCORE
            # -------------------------------------------------

            retest_percentage = round(
                (retest_score /
                 retest_total) * 100
            )

            st.session_state.retest_score = (
                retest_score
            )

            st.session_state.retest_percentage = (
                retest_percentage
            )

            st.session_state.retest_topic_stats = (
                retest_topic_stats
            )

            st.success(
                f"🎯 Retest score: "
                f"{retest_score}/{retest_total} "
                f"({retest_percentage}%)"
            )


            # -------------------------------------------------
            # RETEST TOPIC PERFORMANCE
            # -------------------------------------------------

            st.subheader(
                "📊 Retest Topic Performance"
            )

            retest_topic_percentages = {}

            for topic, stats in retest_topic_stats.items():

                topic_percentage = round(
                    (stats["correct"] /
                     stats["total"]) * 100
                )

                retest_topic_percentages[
                    topic
                ] = topic_percentage

                if topic_percentage >= 80:

                    emoji = "🟢"

                elif topic_percentage >= 50:

                    emoji = "🟠"

                else:

                    emoji = "🔴"

                st.write(
                    f"{emoji} **{topic}** — "
                    f"{topic_percentage}% "
                    f"({stats['correct']}/"
                    f"{stats['total']} correct)"
                )

            st.session_state.retest_topic_percentages = (
                retest_topic_percentages
            )


            # -------------------------------------------------
            # WEAKNESS RECOVERY
            # -------------------------------------------------

            if "diagnostic_weak_topics" in st.session_state:

                original_weak_topics = (
                    st.session_state.diagnostic_weak_topics
                )

                recovered_topics = []
                still_weak_topics = []

                st.subheader(
                    "🧠 Weakness Recovery"
                )

                for topic, original_percentage in (
                    original_weak_topics.items()
                ):

                    original_normalized = normalize_topic(topic)

                    matching_retest_topic = None

                    for retest_topic in retest_topic_percentages:

                        if (
                            normalize_topic(retest_topic)
                            == original_normalized
                        ):

                            matching_retest_topic = retest_topic
                            break

                    if matching_retest_topic:

                        new_percentage = (
                            retest_topic_percentages[
                                matching_retest_topic
                            ]
                        )

                        improvement = (
                            new_percentage
                            - original_percentage
                        )

                        if new_percentage >= 80:

                            recovered_topics.append(topic)

                            st.success(
                                f"🟢 **{topic}** — "
                                f"{original_percentage}% → "
                                f"{new_percentage}% "
                                f"(+{improvement} points)"
                            )

                        else:

                            still_weak_topics.append(topic)

                            if improvement >= 0:

                                st.info(
                                    f"🟠 **{topic}** — "
                                    f"{original_percentage}% → "
                                    f"{new_percentage}% "
                                    f"(+{improvement} points)"
                                )

                            else:

                                st.warning(
                                    f"🔴 **{topic}** — "
                                    f"{original_percentage}% → "
                                    f"{new_percentage}% "
                                    f"({improvement} points)"
                                )

                    else:

                        still_weak_topics.append(topic)

                        st.warning(
                            f"⚪ **{topic}** — "
                            f"No matching retest topic found."
                        )

                # -------------------------------------------------
                # FINAL RECOVERY SUMMARY
                # -------------------------------------------------

                total_original_weak = len(
                    original_weak_topics
                )

                total_recovered = len(
                    recovered_topics
                )

                st.divider()

                if total_recovered == total_original_weak:

                    st.success(
                        f"🎉 Amazing! You recovered "
                        f"all {total_recovered} of your "
                        f"original weak areas."
                    )

                elif total_recovered > 0:

                    st.success(
                        f"🚀 You recovered "
                        f"{total_recovered} of "
                        f"{total_original_weak} "
                        f"original weak areas."
                    )

                else:

                    st.warning(
                        "📚 Your weak areas still need "
                        "more practice. Keep going!"
                    )


            # -------------------------------------------------
            # OVERALL LEARNING PROGRESS
            # -------------------------------------------------

            if "initial_percentage" in st.session_state:

                initial = (
                    st.session_state.initial_percentage
                )

                improvement = (
                    retest_percentage - initial
                )

                st.divider()

                st.subheader(
                    "📈 Overall Learning Progress"
                )

                st.write(
                    f"Diagnostic score: **{initial}%**"
                )

                st.write(
                    f"Retest score: **{retest_percentage}%**"
                )

                if improvement > 0:

                    st.success(
                        f"🚀 Overall score improved by "
                        f"**{improvement} percentage points!**"
                    )

                elif improvement < 0:

                    st.warning(
                        f"📉 Overall score was "
                        f"{abs(improvement)} percentage "
                        f"points lower."
                    )

                else:

                    st.info(
                        "➡️ Overall score stayed the same."
                    )

                st.caption(
                    "Because the diagnostic and retest "
                    "use different questions, the score "
                    "change is an indicator of progress, "
                    "not a definitive measurement of learning."
                )
                                # -------------------------------------------------
                # FINAL LEARNING OUTCOME
                # -------------------------------------------------

                if "diagnostic_weak_topics" in st.session_state:

                    total_original_weak = len(
                        st.session_state.diagnostic_weak_topics
                    )

                    recovered_count = len(
                        recovered_topics
                    )

                    still_weak_count = (
                        total_original_weak
                        - recovered_count
                    )

                    st.divider()

                    st.subheader(
                        "🏆 Final Learning Outcome"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Weak areas recovered",
                            f"{recovered_count}/"
                            f"{total_original_weak}"
                        )

                    with col2:
                        st.metric(
                            "Still need practice",
                            still_weak_count
                        )

                    if total_original_weak > 0:

                        recovery_percentage = round(
                            (
                                recovered_count /
                                total_original_weak
                            ) * 100
                        )

                        st.progress(
                            recovery_percentage / 100
                        )

                        st.caption(
                            f"{recovery_percentage}% of your "
                            "original weak areas reached "
                            "80% or higher on the retest."
                        )

                    if (
                        total_original_weak > 0
                        and recovered_count
                        == total_original_weak
                    ):

                        st.success(
                            "🎉 **Excellent! You recovered "
                            "all of your original weak areas.**"
                        )

                    elif recovered_count > 0:

                        st.info(
                            f"🚀 You recovered **"
                            f"{recovered_count} of "
                            f"{total_original_weak}** "
                            "original weak areas."
                        )

                    else:

                        st.warning(
                            "📚 Your original weak areas "
                            "still need more practice."
                        )