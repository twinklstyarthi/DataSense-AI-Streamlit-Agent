import os
import json
from typing import TypedDict, Annotated, List
from operator import itemgetter
import pandas as pd
import plotly.graph_objects as go
from asteval import Interpreter
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# --- Load API Key ---
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY not found in .env file. Please add it.")

# --- 1. Define Agent State ---
class AgentState(TypedDict):
    df_preview: str
    user_prompt: str
    code_solution: str
    execution_result: any
    error_message: str
    retries: int
    final_response: dict

# --- 2. Define Tools / Nodes ---

# Use a shared, safe interpreter for code execution
aeval = Interpreter()
aeval.symtable['pd'] = pd
aeval.symtable['go'] = go

def route_intent_node(state: AgentState):
    """Classifies user intent to decide the next step."""
    prompt = f"""Given the user's query, classify its primary intent.
    The dataframe `df` is already loaded. Its preview is:
    {state['df_preview']}

    User Query: "{state['user_prompt']}"

    Possible intents:
    1. 'plot': The user is asking for a single chart, graph, or visualization.
    2. 'dashboard': The user is explicitly asking for a 'dashboard' or multiple plots at once.
    3. 'general_query': The user is asking a general question, requesting statistics, or asking for data manipulation that results in text or a number.

    Respond with ONLY ONE of the intent names: 'plot', 'dashboard', or 'general_query'.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    intent = llm.invoke(prompt).content.strip()
    
    print(f"--- Intent Routed to: {intent} ---")
    return intent

# Replace the existing code_generator_node function in llm_agent.py with this one:

# In llm_agent.py, replace the entire code_generator_node function with this:

def code_generator_node(state: AgentState):
    """Generates Python code to answer the user's question."""
    prompt_template = """You are an expert Python data scientist.
    Your sole task is to generate a Python code snippet to answer the user's question using a pandas DataFrame named `df`.
    The DataFrame preview is:
    {df_preview}

    User Question: {user_prompt}

    **CRITICAL Instructions:**
    1.  The variables `df` (the DataFrame), `pd` (pandas), and `go` (plotly.graph_objects) are ALREADY AVAILABLE.
    2.  **DO NOT include `import pandas as pd` or `import plotly.graph_objects as go` in your code.**
    3.  Your code must be a single expression that can be evaluated. It should not include any print statements.
    4.  For plots, you MUST return a single `go.Figure` object.
    5.  For dashboards, you MUST return a Python LIST of `go.Figure` objects.
    6.  **NEW: For map charts (e.g., go.Scattermapbox, go.Choropleth), you MUST set the map style. Use `fig.update_layout(mapbox_style='carto-positron')`.**
    7.  For general queries, your code should return a string, number, or a pandas DataFrame.
    8.  If the previous attempt failed, analyze the error and fix the code.

    Previous Code (if any):
    {previous_code}
    Error (if any):
    {error}

    Respond ONLY with the Python code snippet.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

    prompt = prompt_template.format(
        df_preview=state['df_preview'],
        user_prompt=state['user_prompt'],
        previous_code=state.get('code_solution', 'N/A'),
        error=state.get('error_message', 'N/A')
    )

    response = llm.invoke(prompt)
    code = response.content.strip().replace("```python", "").replace("```", "")
    print(f"--- Generated Code ---\n{code}\n--------------------")

    return {"code_solution": code, "error_message": None} # Reset error message
def code_executor_node(state: AgentState):
    """Executes the generated code in a safe sandbox."""
    code = state['code_solution']
    retries = state.get('retries', 0)
    
    try:
        result = aeval.eval(code)
        print(f"--- Code Execution Successful ---")
        return {"execution_result": result, "retries": retries}
    except Exception as e:
        error_msg = f"Execution failed with error: {type(e).__name__} - {e}"
        print(f"--- Code Execution Failed ---\n{error_msg}\n--------------------")
        return {"error_message": error_msg, "execution_result": None, "retries": retries + 1}

# In llm_agent.py, replace the entire response_formatter_node function with this:

# In llm_agent.py, replace the entire response_formatter_node function with this:

# In llm_agent.py, replace the entire response_formatter_node function with this final version:

def response_formatter_node(state: AgentState):
    """Formats the final response and generates follow-up questions."""
    result = state['execution_result']
    user_prompt = state['user_prompt']
    error_message = state.get("error_message")

    final_output = {"follow_up_questions": []}
    summary_for_llm = ""

    # --- NEW: First, check if there was an execution error ---
    if error_message:
        final_output["type"] = "string"
        final_output["content"] = f"I encountered an error trying to process your request. The error was: {error_message}"
        summary_for_llm = f"an error: {error_message}"
    
    # --- If no error, process the successful result ---
    elif isinstance(result, go.Figure):
        final_output["type"] = "plot"
        final_output["content"] = {"type": "plot", "data": result}
        summary_for_llm = "a single plot"
    elif isinstance(result, list) and all(isinstance(item, go.Figure) for item in result):
        final_output["type"] = "dashboard"
        final_output["content"] = result
        summary_for_llm = f"a dashboard with {len(result)} charts"
    elif isinstance(result, pd.DataFrame):
        final_output["type"] = "string"
        final_output["content"] = result.to_string()
        summary_for_llm = f"a dataframe with shape {result.shape}"
    else: # Handle numbers, strings, etc.
        final_output["type"] = "string"
        final_output["content"] = str(result)
        summary_for_llm = str(result)
        
    # --- Generate follow-up questions only on success ---
    if not error_message:
        prompt = f"""The user asked: "{user_prompt}"
        The analysis produced the following result: {summary_for_llm}.
        
        Based on this, generate three relevant, insightful follow-up questions.
        Provide the output as a JSON object with a single key: "follow_up_questions".
        Respond ONLY with the JSON object.
        """
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)
            response_text = llm.invoke(prompt).content.strip().replace("```json", "").replace("```", "")
            response_json = json.loads(response_text)
            final_output["follow_up_questions"] = response_json.get("follow_up_questions", [])
        except Exception:
            # If JSON parsing or LLM call fails, just return no follow-ups
            final_output["follow_up_questions"] = []

    print(f"--- Final Response Formatted ---")
    return {"final_response": final_output}
# --- 3. Define Graph Logic ---
def should_retry(state: AgentState):
    """Determines if the agent should retry code generation after an error."""
    if state.get("error_message") and state.get('retries', 0) < 2:
        print("--- Decision: Retry Code Generation ---")
        return "retry"
    print("--- Decision: End and Format Response ---")
    return "end"

# --- 4. Main Agent Class ---
class DataSenseAgent:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        aeval.symtable['df'] = self.df # Make dataframe available to the interpreter
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        
        graph.add_node("code_generator", code_generator_node)
        graph.add_node("code_executor", code_executor_node)
        graph.add_node("response_formatter", response_formatter_node)

        graph.set_entry_point("code_generator")
        
        graph.add_edge("code_generator", "code_executor")
        graph.add_conditional_edges(
            "code_executor",
            should_retry,
            {
                "retry": "code_generator",
                "end": "response_formatter"
            }
        )
        graph.add_edge("response_formatter", END)
        
        return graph.compile()

    # In llm_agent.py, replace the entire query method with this:

    def query(self, user_prompt: str):
        """Main function to run a query through the agent."""
        if self.df is None:
            return {"type": "string", "content": "Error: DataFrame not loaded.", "follow_up_questions": []}

        df_preview = self.df.head().to_string()
        
        initial_state = {
            "df_preview": df_preview,
            "user_prompt": user_prompt,
            "retries": 0,
            "error_message": None
        }
        
        try:
            # The formatter node now creates the complete, final response
            final_state = self.graph.invoke(initial_state)
            return final_state.get('final_response', {
                "type": "string", 
                "content": "An unexpected error occurred in the agent's final state."
            })

        except Exception as e:
            print(f"--- Critical Agent Error: {e} ---")
            return {
                "type": "string",
                "content": "Sorry, a critical error occurred. The development team has been notified. Please try rephrasing your question.",
                "follow_up_questions": []
            }