# 🎯 InterviewCoach — AI-Powered Interview Trainer

> Built with **Python Flask** + **IBM Watsonx.ai** (Granite/Llama models) + **Hugging Face Serverless Fallback**  
> A premium, fully-featured interview preparation platform with mock sessions, resume analysis, progress tracking, and personalized coaching.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Coach Chat** | Conversational coaching powered by IBM Granite or Llama 3 models |
| 🎭 **Mock Interview** | Specialized behavioral, technical, HR, system design, and case study sessions |
| 📊 **Real-time Scoring** | Answer evaluation with 0-100 scoring and detailed STAR method feedback |
| 📄 **Resume Analyzer** | ATS compatibility check, skill gap identification, and optimization recommendations |
| 🗓️ **Prep Strategy** | Personalized day-by-day study roadmap tailored to your timeline and target role |
| 🔌 **Hugging Face Fallback** | Automatic serverless fallback option if Watsonx limits are reached or credentials are unconfigured |
| 🎛️ **Live Model Badges** | Dynamic header status displays and Session Info panel showing the active model in real-time |
| 📈 **Progress Tracking** | Performance history charts and mock interview session scoring metrics |
| 🌙 **Dark Mode** | Harmony color themes with persistent dark/light preferences |

---

## ⚡ Vercel Deployment (Step-by-Step for Beginners)

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

## 🔒 Security Notes
* Never commit the `.env` file containing credentials to version control. The included `.gitignore` is pre-configured to block it.
* Credentials are kept strictly on the backend serverless side and are never exposed to the client browser.

---

## 📜 License
MIT License — Developed for the **IBM SkillsBuild for University Engagement Students- Edunet Foundation Project**.
