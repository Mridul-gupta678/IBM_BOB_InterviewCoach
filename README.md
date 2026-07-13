# 🎯 InterviewCoach — AI-Powered Interview Trainer

> Built with **Python Flask** + **IBM Watsonx.ai** (Granite/Llama models) + **Hugging Face Serverless Fallback**  
> A premium, fully-featured interview preparation platform with mock sessions, resume analysis, progress tracking, and personalized coaching.

---

## 💻 What the App Does & Capabilities

### 1. 🤖 AI Coach Chat
* **Interactive Chat Sandbox**: Engage in open-ended conversations with a responsive AI coach to brainstorm interview questions, draft elevator pitches, or ask for career advice.
* **Context-Aware Prompts**: The backend dynamically formats system prompts using the user's Profile details (Industry, Target Role, Experience Level, and Interview Type) so that the AI's tone and domain knowledge precisely match your goals.
* **Markdown Support**: Chat messages are parsed in real-time, supporting bulleted points, bolded headings, and code blocks with clean, styled padding.

### 2. 🎭 Mock Interview Simulator
* **Custom Session Setup**: Select the interview focus (Behavioral, Technical, HR, System Design, or Case Study) and specify the exact number of questions (up to 10).
* **Sequential Question Delivery**: Simulates a live interview by presenting questions one-by-one to replicate the pacing of a real interview.
* **Real-time Grading & STAR Feedback**: Each answer is evaluated by the AI, producing an overall score (0-100) and structured feedback matching the **STAR** framework (Situation, Task, Action, Result) to pinpoint exactly where your response can be strengthened.

### 3. 📄 ATS Resume Analyzer
* **ATS Compatibility Grading**: Compares your resume against a target job description to estimate automated screening compatibility.
* **Skill Gap Analysis**: Highlights missing core keywords and skills that recruiters look for in similar postings.
* **Actionable Optimizations**: Delivers concrete suggestions to refine bullet points, adjust formats, and increase keyword matches.

### 4. 🗓️ Prep Strategy Roadmap
* **Personalized Timelines**: Enter your target interview date to build a custom study strategy.
* **Daily Action Plans**: Generates structured, day-by-day study roadmaps outlining technical concepts to review, practice questions to write, and behavioral scenarios to prepare.

### 5. 🔌 Advanced LLM Orchestration & Fallback Cascade
* **Intelligent Auto-Detect**: When set to "Auto-detect", the system cascades through providers automatically (IBM Watsonx $\rightarrow$ Hugging Face router $\rightarrow$ Static Demo) to ensure maximum uptime.
* **Explicit Provider Protection**: If a specific LLM mode (Watsonx or Hugging Face) is explicitly selected, the cascade is disabled. Any API key or connection issues immediately report an "API not connected" error UI, complete with a red status warning dot, so you know exactly which gateway failed.
* **Dynamic Status Badges**: Sidebar info cards and header badges update in real-time on every response, showing the exact LLM provider and model ID that generated the output.

### 6. 📈 Progress Tracking & Analytics
* **Performance Charts**: An interactive chart built with Chart.js displays your scoring trajectory over mock sessions.
* **Historical Metrics**: Track total messages, average evaluation scores, and overall interview readiness levels.

### 7. 🌙 Premium Default Dark Mode
* **Modern Interface**: Designed with glassmorphism panels, tailored HSL color palettes, and smooth hover micro-animations.
* **Persistent Preferences**: Defaults to Dark Mode on first load, with a top-right toggle button to switch modes instantly.

---

## ⚡ Vercel Deployment

Vercel makes it incredibly easy to deploy Python Flask applications as Serverless Functions. Follow these steps to put your application online:

### 1. Push Code to GitHub
Ensure all your files (including `vercel.json`, `.gitignore`, and `requirements.txt`) are committed and pushed to your GitHub repository:
`https://github.com/GokulKrishnaR/Interview-Coach`

### 2. Connect GitHub to Vercel
1. Go to [Vercel](https://vercel.com) and sign up or log in using your **GitHub account**.
2. From the Vercel Dashboard, click **Add New...** and select **Project**.
3. Under "Import Git Repository", find your `Interview-Coach` repository and click **Import**.

### 3. Configure Project Settings
In the configuration screen, Vercel will auto-detect the workspace structure. You do **not** need to change the build commands or install directory.
1. Expand the **Environment Variables** section.
2. Add the following keys with their respective values from your `.env` configuration:
   * `IBM_API_KEY`: *(your IBM Cloud API Key)*
   * `WATSONX_PROJECT_ID`: *(your Watsonx Project ID)*
   * `WATSONX_URL`: `https://au-syd.ml.cloud.ibm.com` *(or your regional Watsonx API gateway)*
   * `WATSONX_MODEL_ID`: `meta-llama/llama-3-3-70b-instruct` *(or preferred Granite model)*
   * `HUGGINGFACE_API_KEY`: *(your Hugging Face access token for fallback model)*
   * `HUGGINGFACE_MODEL_ID`: `Qwen/Qwen2.5-3B` *(or preferred Qwen/Llama fallback)*
   * `FLASK_SECRET_KEY`: *(any long random security string)*
   * `FLASK_ENV`: `production`

### 4. Deploy!
1. Click the **Deploy** button.
2. Vercel will install the requirements from `requirements.txt`, build the serverless environment, and publish your site.
3. Once completed, Vercel will generate a secure public domain (e.g., `https://interview-coach.vercel.app`) where your app is live!

---

## 🚀 Local Quick Start

### 1. Clone & Navigate
```bash
git clone https://github.com/GokulKrishnaR/Interview-Coach.git
cd Interview-Coach
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows (Command Prompt / PowerShell)
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Credentials
Create a `.env` file from the example template:
```bash
cp .env.example .env
```
Edit `.env` and fill in your primary Watsonx or Hugging Face access credentials.

### 5. Run App
```bash
python app.py
```
Open **http://127.0.0.1:5001** in your browser.

---

## 🔗 Links
* Repository: https://github.com/GokulKrishnaR/InterviewCoach
* Live App: https://interview-coach-and-trainer.vercel.app/

---

## 🔒 Security Notes
* Never commit the `.env` file containing credentials to version control. The included `.gitignore` is pre-configured to block it.
* Credentials are kept strictly on the backend serverless side and are never exposed to the client browser.

---

## 📜 License
MIT License — Developed for the **IBM SkillsBuild for University Engagement Students- Edunet Foundation Project**.
