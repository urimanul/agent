import streamlit as st
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langgraph.graph import END
import pymysql.cursors

# データベース接続関数
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

# Streamlitアプリケーション
def main():
    st.title("MBTI コメント検索")
    
    query = st.text_input("クエリを入力してください:")
    symbol = st.text_input("MBTIのシンボルを入力してください:")
    
    if st.button("検索"):
        if query and symbol:
            result = fake_database_api(query, symbol)
            st.write("結果:", result)
        else:
            st.write("クエリとシンボルを入力してください。")

if __name__ == "__main__":
    main()
