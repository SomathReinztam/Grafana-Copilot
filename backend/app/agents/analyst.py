"""Subagente analista de datos (ReAct sobre PostgreSQL, solo lectura)."""
from langgraph.prebuilt import create_react_agent
from sqlalchemy.engine import Engine

from app.common.db import make_engine
from app.common.llm import make_llm
from app.lib.postgres_toolkit import PostgresToolKit
from app.prompts import ANALYST_SYSTEM_PROMPT


def create_analyst_agent(engine: Engine | None = None, llm=None):
    engine = engine or make_engine()
    llm = llm or make_llm()
    tools = PostgresToolKit(engine).get_tools()
    return create_react_agent(llm, tools, prompt=ANALYST_SYSTEM_PROMPT)
