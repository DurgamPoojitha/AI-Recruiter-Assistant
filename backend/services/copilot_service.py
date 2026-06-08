import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools.retriever import create_retriever_tool
from backend.services.rag_service import get_rag_service

# Global dictionary to store conversational memory per session
_session_memories = {}

def get_copilot_memory(session_id: str):
    if session_id not in _session_memories:
        _session_memories[session_id] = ConversationBufferWindowMemory(
            memory_key="chat_history", 
            k=5, 
            return_messages=True
        )
    return _session_memories[session_id]

def answer_copilot_query(query: str, job_id: int = None, session_id: str = "default") -> str:
    """
    LangChain-powered Copilot that can query the SQLite database and search candidate resumes (RAG).
    """
    if not os.environ.get("OPENAI_API_KEY"):
        return "⚠️ OpenAI API Key is missing. Please set the OPENAI_API_KEY environment variable to use the Recruiter Copilot."
        
    db_path = "sqlite:///data/recruiter.db"
    db = SQLDatabase.from_uri(db_path)
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    tools = []
    
    # 1. Add RAG Retriever Tool
    rag_service = get_rag_service()
    retriever = rag_service.get_retriever()
    if retriever:
        retriever_tool = create_retriever_tool(
            retriever,
            "candidate_resume_search",
            "Search through candidate resumes for specific technical skills, project experiences, and certifications. Always use this tool when asked about specific candidate experiences or what a candidate did."
        )
        tools.append(retriever_tool)
        
    # 2. Get Memory
    memory = get_copilot_memory(session_id)
    
    # Context injection for the Agent
    system_message = (
        "You are an expert Enterprise AI Recruiter Copilot. "
        "You have access to an SQLite database containing jobs, candidates, match_results, and ATS pipelines. "
        "You also have a candidate_resume_search tool to semantically search the actual raw text of candidate resumes. "
        "When asked about statistics, pipeline status, or scores, query the database. "
        "When asked about specific experiences or details not in the database columns, use the candidate_resume_search tool. "
        "Always provide helpful, professional, and concise answers."
    )
    
    if job_id:
        system_message += f"\nThe current active Job ID the user is referring to is {job_id}."

    # 3. Create SQL Agent
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
        extra_tools=tools,
        agent_executor_kwargs={"memory": memory},
        prefix=system_message
    )
    
    try:
        response = agent_executor.invoke({"input": query})
        return response.get("output", "I could not generate an answer.")
    except Exception as e:
        return f"An error occurred while thinking: {str(e)}"
