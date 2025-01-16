#import os
#from dotenv import load_dotenv
import streamlit as st
import pymysql.cursors
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

#import getpass

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langgraph.graph import END, StateGraph

class State(TypedDict):
    messages: Annotated[list, 'add_messages']

# Initialize state
if 'state' not in st.session_state:
    st.session_state.state = State(messages=[])

# データベース接続関数
@tool
def fake_database_api(query: str, symbol: str) -> str:
    """情報を格納したデータベースを検索するAPI"""
    connection = pymysql.connect(host='www.ryhintl.com',
                                 user='smairuser',
                                 password='smairuser',
                                 db='smair',
                                 charset='utf8mb4',
                                 port=36000,
                                 cursorclass=pymysql.cursors.DictCursor)
    cur = connection.cursor()

    cur.execute("select comments from mbti_comments where symbol = %s", (symbol,))
    myrow = None

    for row in cur.fetchall():
        myrow = row['comments']
        print(myrow)
    return myrow

# llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
llm = ChatGroq(groq_api_key=os.environ["GROQ_API_KEY"], model_name="llama3-70b-8192")
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

def get_response(query: str, symbol: str):
    response = runner.invoke({"messages": [{"query": query, "symbol": symbol}]})
    # print(response)
    return response["messages"][-1].content

# Streamlitアプリケーション
def main():
    st.title("MBTI コメント検索")
    
    query = st.text_input("クエリを入力してください:")
    symbol = st.text_input("MBTIのシンボルを入力してください:")
    
    if st.button("検索"):
        if query and symbol:
            result = get_response(query, symbol)
            st.write("結果:", result)
        else:
            st.write("クエリとシンボルを入力してください。")

if __name__ == "__main__":
    main()
