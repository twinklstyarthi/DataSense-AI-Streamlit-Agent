# DataSense AI 🤖
> An Interactive Chatbot for Instant CSV & Excel Analysis.

## 🚀 Live Demo

**[➡️ View the Live Application Here](https://your-streamlit-app-url.com)** *(Replace this with the link to your deployed Streamlit Cloud app.)*

---

![DataSense AI Demo GIF](https://path-to-your-gif.gif)
*(Record a high-quality GIF of you using the app and replace this path.)*

## The Business Problem

Many businesses have valuable data trapped in spreadsheets. This tool unlocks those insights by allowing non-technical users to explore and visualize their data without needing to write a single line of code or hire a data scientist.

---

## The Solution & Key Features ✨

DataSense AI is a web application built with Streamlit that provides a seamless, conversational interface for data analysis.

* 💬 **Natural Language Q&A:** Ask complex questions about your data in plain English and receive instant, accurate answers.
* 📊 **Automated Chart & Dashboard Generation:** Ask for a specific chart ("create a bar chart of sales by region") or a full dashboard, and the AI will generate it for you using Plotly.
* 📤 **Simple File Upload:** Supports both CSV and multi-sheet Excel files (`.xls`, `.xlsx`).
* 📈 **One-Click EDA:** Generate a comprehensive Exploratory Data Analysis report with a single button click to instantly understand key statistics, value distributions, and missing data.
* 💾 **Session Management:** Automatically saves each analysis session (the uploaded file + chat history) so you can return to it later.

---

## Tech Stack ⚙️

* **Frontend:** Streamlit
* **AI Agent & Orchestration:** LangGraph
* **Language Model (LLM):** Google Gemini
* **Data Manipulation:** Pandas
* **Plotting:** Plotly

---

## Getting Started 🏁

### Prerequisites

* Python 3.9+
* A Google Gemini API Key

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/datasense-ai.git](https://github.com/your-username/datasense-ai.git)
    cd datasense-ai
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your API Key:**
    Create a file named `.env` in the root directory and add your Google Gemini API key:
    ```
    GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

### Running the Application

1.  **Launch the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

2.  Open your browser and navigate to `http://localhost:8501`.
