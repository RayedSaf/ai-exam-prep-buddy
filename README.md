# 🧠 AI Exam Prep Buddy

> Find what you don't know. Fix it. Test again.

AI Exam Prep Buddy is an AI-powered study assistant that helps students identify their weak areas through diagnostic testing and then focus their revision where it matters most.

Instead of simply generating practice questions, the app follows a learning loop:

**Learn → Diagnose → Revise → Practice → Retest**

## 🚀 How It Works

1. **Enter Study Material**
   - Paste notes, concepts, or study material into the app.

2. **Take a Diagnostic Quiz**
   - Gemini generates multiple-choice questions based on the material.
   - Each question is tagged with a topic and difficulty.

3. **Analyze Performance**
   - The app calculates the overall score.
   - Performance is broken down by topic.
   - Weak topics are automatically identified.

4. **Target Revision**
   - AI generates a revision lesson focused on the student's weakest areas.
   - The app recommends which topics should be revised first.

5. **Practice Weak Areas**
   - Gemini generates targeted questions designed around the student's weaknesses.
   - Questions focus on understanding and application rather than simple recall.

6. **Retest**
   - A fresh set of questions measures whether the student's weak areas improved.
   - The app compares diagnostic and retest performance.

## 🤖 AI/ML Integration

Google Gemini is used as the core generative AI system within the application.

The AI is responsible for:

- Generating diagnostic questions from study material
- Assigning questions to relevant topics and difficulty levels
- Creating personalized revision lessons
- Generating targeted practice questions for weak areas
- Generating fresh retest questions using new scenarios

The application then performs deterministic scoring and topic-level performance analysis based on the student's answers.

This creates an adaptive learning loop where the student's performance determines which topics receive additional practice and revision.

## 🛠️ Tech Stack

- Python
- Streamlit
- Google Gemini API
- Google GenAI Python SDK
- python-dotenv

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/RayedSaf/ai-exam-prep-buddy
cd ai-exam-prep-buddy