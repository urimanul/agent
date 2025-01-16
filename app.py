import streamlit as st
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langgraph.graph import END
import pymysql.cursors

import getpass
import os
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv


from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq

load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass.getpass("GROQ API Key:")


class State(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def fake_database_api(query: str) -> str:
    """情報を格納したデータベースを検索するAPI"""
    connection = pymysql.connect(host='www.ryhintl.com',
                             user='smairuser',
                             password='smairuser',
                             db='smair',
                             charset='utf8mb4',
                             port=36000,
                             cursorclass=pymysql.cursors.DictCursor)
    cur = connection.cursor()

    #cur.execute("select comments from mbti_comments where symbol = '"+mbti+"'")
    cur.execute("select a.comments,b.username from mbti_comments as a, mbti_test_results as b where a.symbol = '"+mbti+"' and b.symbol = '"+mbti+"'")
    
    myrow = None

    for row in cur.fetchall():
        myrow = "性格: "+row['comments']+" 該当者: "+row['username']
        #st.write(myrow)
    return myrow

llm = ChatGroq(groq_api_key=os.environ.get("GROQ_API_KEY"), model_name="llama3-70b-8192")
llm_with_tools = llm.bind_tools([fake_database_api])

def llm_agent(state):
    state["messages"].append(llm_with_tools.invoke(state["messages"]))
    return state

def tool(state):
    tool_by_name = {"fake_database_api": fake_database_api}
    last_message = state["messages"][-1]
    tool_function = tool_by_name[last_message.tool_calls[0]["name"]]
    tool_output = tool_function.invoke(last_message.tool_calls[0]["args"])
    state["messages"].append(ToolMessage(content=tool_output, tool_call_id=last_message.tool_calls[0]["id"]))
    return state

def router(state):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool"
    else:
        return "__end__"

graph = StateGraph(State)

graph.add_node("llm_agent", llm_agent)
graph.add_node("tool", tool)

graph.set_entry_point("llm_agent")
graph.add_conditional_edges("llm_agent",
                            router,
                            {"tool":"tool", "__end__": END})

graph.add_edge("tool", "llm_agent")

runner = graph.compile()

def get_response(query: str):
    response = runner.invoke({"messages": [query]})
    #st.write(response)
    st.write(response["messages"][-1].content)
    return response["messages"][-1].content

mbti = ""

# Streamlit UI
st.title("MBTI Personality Checker")

# Input for MBTI symbol
mbti = st.text_input("MBTIのシンボルを教えてください:")

# Button to get response
if st.button("生成"):
    response = get_response(f"{mbti}の性格と該当者を必ず、日本語で教えてください")
    st.write(response)

#mbti = input("MBTIのシンボルを教えてください: ")
#get_response("INFJの性格を日本語で教えてください")
