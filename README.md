# GenerativeAIQuiz

![Python](https://img.shields.io/badge/Python-0d1117?style=flat-square&logo=python&logoColor=58a6ff)
![Streamlit](https://img.shields.io/badge/Streamlit-0d1117?style=flat-square&logo=streamlit&logoColor=58a6ff)
![Groq](https://img.shields.io/badge/Groq_API-0d1117?style=flat-square&logo=openai&logoColor=58a6ff)

A Streamlit web app that uses the Groq LLM API to generate dynamic, topic-specific quizzes on demand. Type in any subject and the app produces a quiz instantly — no pre-written questions, just live AI generation.

---

### Features

- 🤖 &nbsp;LLM-powered question generation via Groq API
- 🎯 &nbsp;Any topic — history, science, code, pop culture
- ⚡ &nbsp;Fast inference powered by Groq's low-latency models
- 📊 &nbsp;Results saved to the `results/` directory

---

### Getting Started

**1. Clone the repo**
```bash
git clone https://github.com/pauloshabtewold/GenerativeAIQuiz.git
cd GenerativeAIQuiz
```

**2. Set up a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your Groq API key**

Create a `.env` file in the root directory:
```
GROQ_API_KEY="your_groq_api_key_here"
```
Get a free key at [console.groq.com](https://console.groq.com)

**5. Run the app**
```bash
streamlit run app.py
```

---

### Project Structure

```
GenerativeAIQuiz/
├── app.py              # Main Streamlit app
├── utils.py            # Helper functions
├── requirements.txt    # Dependencies
├── .env                # API key (not committed)
└── results/            # Saved quiz outputs
```

---

### Built by [Paulos Habtewold](https://github.com/pauloshabtewold) · [LinkedIn](https://www.linkedin.com/in/paulos-habtewold-7b6b72235/)

