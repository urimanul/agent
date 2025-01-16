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

print(os.environ.get("GROQ_API_KEY"))
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

    #mbti = input("MBTIのシンボルを教えてください: ")

    cur.execute("select comments from mbti_comments where symbol = '"+mbti+"'")
    #cur.execute("select comments from mbti_comments where symbol = 'INTJ'")

    myrow = None

    for row in cur.fetchall():
        myrow = row['comments']
        print(myrow)
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
    # print(response)
    return response["messages"][-1].content

mbti = ""

mbti = input("MBTIのシンボルを教えてください: ")
get_response("INFJの性格を日本語で教えてください")
