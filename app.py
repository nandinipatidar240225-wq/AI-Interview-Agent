import streamlit as st
import os
from resume_parser import extract_text_from_pdf
from interview_engine import generate_question
from evaluator import evaluate_answer, EvaluationResult

# Page Config
st.set_page_config(
    page_title="AI Interview Agent",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize session variables
if "history" not in st.session_state:
    st.session_state.history = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "resume_text" not in st.session_state:
    st.session_state.resume_text = None
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "current_evaluation" not in st.session_state:
    st.session_state.current_evaluation = None
if "answer_submitted" not in st.session_state:
    st.session_state.answer_submitted = False

# Sidebar
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 1.5rem;'>
    <h2 style='font-weight: 700; color: #f4f4f5;'>Settings</h2>
</div>
""", unsafe_allow_html=True)

# API Key input
env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
api_key = None

if env_key:
    st.sidebar.success("✅ API Key active from Environment")
    api_key = env_key
else:
    api_key = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        help="Get a key from https://aistudio.google.com/"
    )
    if api_key:
        st.sidebar.success("✅ API Key registered")
    else:
        st.sidebar.warning("⚠️ Enter API Key to enable the Interviewer")

# Sidebar summary
if st.session_state.history:
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h3 style='font-weight: 600; color: #e4e4e7;'>Session Progress</h3>", unsafe_allow_html=True)
    st.sidebar.write(f"Questions answered: **{len(st.session_state.history)}**")
    avg_score = sum(h["evaluation"].score for h in st.session_state.history) / len(st.session_state.history)
    st.sidebar.metric(label="Average Score", value=f"{avg_score:.1f} / 10")
    st.sidebar.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    
    # Button to reset interview
    if st.sidebar.button("Reset Interview Session"):
        st.session_state.history = []
        st.session_state.current_question = None
        st.session_state.resume_text = None
        st.session_state.interview_started = False
        st.session_state.current_evaluation = None
        st.session_state.answer_submitted = False
        st.rerun()

# Inject custom CSS for premium design
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stButton>button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    color: white !important;
    font-weight: 600;
    padding: 0.6rem 1.8rem;
    border-radius: 12px;
    border: none;
    box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.2), 0 2px 4px -1px rgba(99, 102, 241, 0.1);
    transition: all 0.2s ease-in-out;
    width: 100%;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3), 0 4px 6px -2px rgba(99, 102, 241, 0.05);
    background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
    color: white !important;
}

.main-card {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(5px);
}

.question-card {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(79, 70, 229, 0.05) 100%);
    border-left: 6px solid #6366f1;
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}

.evaluation-box {
    background-color: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 2rem;
    margin-top: 2rem;
}

.score-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5rem;
}

.score-circle {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    font-size: 2.8rem;
    font-weight: 800;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 20px -5px rgba(16, 185, 129, 0.4);
    margin-bottom: 0.5rem;
}

.strengths-card {
    background-color: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-left: 5px solid #10b981;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}

.weaknesses-card {
    background-color: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.2);
    border-left: 5px solid #f59e0b;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}

.feedback-card {
    background-color: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-left: 5px solid #6366f1;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1.5rem;
}

h3 {
    margin-top: 0;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1 style='font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #818cf8 0%, #c084fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0px; padding-bottom: 10px;'>
        💼 AI Interview Agent
    </h1>
    <p style='color: #a1a1aa; font-size: 1.1rem; margin-top: 0px;'>
        Elevate your interview preparation with custom, resume-tailored questions and structured, professional evaluation.
    </p>
</div>
""", unsafe_allow_html=True)

# Main App Logic
if not api_key:
    st.info("👈 Please enter your Gemini API Key in the sidebar to get started.")
else:
    # We have API key, now handle Resume Upload
    if not st.session_state.interview_started:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("Step 1: Upload Your Resume")
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF format)",
            type=["pdf"],
            help="Your resume will be parsed to tailor questions specifically to your experience."
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if uploaded_file:
            if st.session_state.resume_text is None:
                with st.spinner("Parsing resume PDF..."):
                    try:
                        st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
                        st.success("✅ Resume uploaded and parsed successfully!")
                    except Exception as e:
                        st.error(f"Error parsing PDF: {e}")
            else:
                st.success("✅ Resume uploaded and parsed successfully!")

            if st.session_state.resume_text:
                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                if st.button("🚀 Start Interview"):
                    with st.spinner("Generating your first tailored interview question..."):
                        try:
                            question = generate_question(st.session_state.resume_text, api_key=api_key)
                            st.session_state.current_question = question
                            st.session_state.interview_started = True
                            st.session_state.answer_submitted = False
                            st.session_state.current_evaluation = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error generating question: {e}")
    else:
        # Interview in progress
        q_number = len(st.session_state.history) + 1
        
        st.markdown(f"""
        <div class='question-card'>
            <span style='background-color: #6366f1; color: white; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;'>
                Question {q_number}
            </span>
            <h3 style='margin-top: 0.8rem; font-weight: 600;'>{st.session_state.current_question}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Form or input for the answer
        if not st.session_state.answer_submitted:
            answer = st.text_area(
                "Your Answer",
                height=200,
                placeholder="Type your detailed response here. Explain your reasoning and use examples where possible."
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.button("📤 Submit Answer")
            with col2:
                quit_btn = st.button("⏹️ End Interview Session")

            if submit:
                if not answer.strip():
                    st.warning("Please type your answer before submitting.")
                else:
                    with st.spinner("Evaluating your response with AI..."):
                        try:
                            evaluation = evaluate_answer(
                                st.session_state.current_question,
                                answer,
                                api_key=api_key
                            )
                            st.session_state.current_evaluation = evaluation
                            st.session_state.answer_submitted = True
                            # Add to history
                            st.session_state.history.append({
                                "question": st.session_state.current_question,
                                "answer": answer,
                                "evaluation": evaluation
                            })
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error evaluating answer: {e}")
            
            if quit_btn:
                st.session_state.interview_started = False
                st.session_state.current_question = None
                st.rerun()
        else:
            # Answer was submitted, display evaluation and options for next
            evaluation = st.session_state.current_evaluation
            
            st.markdown("<div class='evaluation-box'>", unsafe_allow_html=True)
            st.markdown("""
            <h2 style='text-align: center; color: #818cf8; margin-bottom: 1.5rem; font-weight: 700;'>
                Evaluation Results
            </h2>
            """, unsafe_allow_html=True)
            
            # Score circle
            st.markdown(f"""
            <div class='score-container'>
                <div class='score-circle'>{evaluation.score:.1f}</div>
                <div style='font-size: 0.9rem; color: #a1a1aa; font-weight: 500;'>OVERALL SCORE</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Strengths
            st.markdown("<div class='strengths-card'>", unsafe_allow_html=True)
            st.markdown("<h4>🟢 Key Strengths</h4>", unsafe_allow_html=True)
            for strength in evaluation.strengths:
                st.markdown(f"- {strength}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Weaknesses
            st.markdown("<div class='weaknesses-card'>", unsafe_allow_html=True)
            st.markdown("<h4>🟡 Areas of Improvement</h4>", unsafe_allow_html=True)
            for weakness in evaluation.weaknesses:
                st.markdown(f"- {weakness}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Feedback
            st.markdown("<div class='feedback-card'>", unsafe_allow_html=True)
            st.markdown("<h4>🔵 Constructive Feedback</h4>", unsafe_allow_html=True)
            st.markdown(f"<p>{evaluation.feedback}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Next actions
            col1, col2 = st.columns([1, 1])
            with col1:
                next_q = st.button("➡️ Get Next Question")
            with col2:
                finish = st.button("🏁 End & View Overall Summary")
                
            if next_q:
                with st.spinner("Generating next tailored interview question..."):
                    try:
                        question = generate_question(st.session_state.resume_text, api_key=api_key)
                        st.session_state.current_question = question
                        st.session_state.answer_submitted = False
                        st.session_state.current_evaluation = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating question: {e}")
                        
            if finish:
                st.session_state.interview_started = False
                st.session_state.current_question = None
                st.rerun()

# Summary Page (if not currently interviewing but history exists)
if not st.session_state.interview_started and st.session_state.history:
    st.markdown("---")
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.markdown("""
    <h2 style='text-align: center; color: #c084fc; margin-bottom: 1.5rem; font-weight: 700;'>
        Interview Session Summary
    </h2>
    """, unsafe_allow_html=True)
    
    total_q = len(st.session_state.history)
    avg_score = sum(h["evaluation"].score for h in st.session_state.history) / total_q
    
    st.markdown(f"""
    <div style='display: flex; justify-content: space-around; align-items: center; margin-bottom: 2rem; background-color: rgba(255,255,255,0.02); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);'>
        <div style='text-align: center;'>
            <div style='font-size: 1.1rem; color: #a1a1aa; margin-bottom: 0.3rem; font-weight: 500;'>Questions Answered</div>
            <div style='font-size: 2.2rem; font-weight: 800; color: #818cf8;'>{total_q}</div>
        </div>
        <div style='width: 1px; height: 60px; background-color: rgba(255,255,255,0.1);'></div>
        <div style='text-align: center;'>
            <div style='font-size: 1.1rem; color: #a1a1aa; margin-bottom: 0.3rem; font-weight: 500;'>Average Score</div>
            <div style='font-size: 2.2rem; font-weight: 800; color: #10b981;'>{avg_score:.2f} / 10</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h3 style='font-weight: 700; color: #f4f4f5; margin-bottom: 1rem;'>Detailed History</h3>", unsafe_allow_html=True)
    
    for i, item in enumerate(st.session_state.history):
        with st.expander(f"Question {i+1}: {item['question'][:60]}... (Score: {item['evaluation'].score}/10)"):
            st.markdown(f"**Full Question:** {item['question']}")
            st.markdown(f"**Your Answer:** {item['answer']}")
            st.markdown("---")
            st.markdown(f"**Score:** {item['evaluation'].score}/10")
            
            st.markdown("**Strengths:**")
            for strength in item['evaluation'].strengths:
                st.markdown(f"- {strength}")
                
            st.markdown("**Areas of Improvement:**")
            for weakness in item['evaluation'].weaknesses:
                st.markdown(f"- {weakness}")
                
            st.markdown(f"**Feedback:** {item['evaluation'].feedback}")
            
    st.markdown("</div>", unsafe_allow_html=True)