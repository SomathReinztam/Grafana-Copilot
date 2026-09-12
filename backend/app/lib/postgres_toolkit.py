"""PostgresToolKit — tools de SOLO LECTURA sobre la BD del usuario.

Reutilizado (como librería) de los repos de referencia y limpiado:
- incluye get_db_tables_names y get_tables_schemas (antes comentados)
- sin dependencias de settings globales ni escritura a disco
"""
from typing import List

from langchain_core.tools import StructuredTool
from langchain_core.tools.base import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy import MetaData, Table, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateTable


class PostgresToolKit:
    def __init__(self, engine: Engine, top_n: int = 15, schema_name: str = "public"):
        self.engine = engine
        self.top_n = top_n
        self.schema_name = schema_name

    # --- helpers ---

    def _get_db_tables_names(self) -> str:
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = :schema ORDER BY table_name"
                    ),
                    {"schema": self.schema_name},
                ).fetchall()
            names = "\n".join(r[0] for r in rows)
            return f"Hay {len(rows)} tablas en la base de datos:\n\n{names}"
        except Exception as e:
            return f"Error: {e}"

    def _get_table_schema(self, table_name: str) -> str:
        try:
            table = Table(table_name, MetaData(), autoload_with=self.engine)
            ddl = CreateTable(table).compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
            return str(ddl)
        except Exception as e:
            return f"Error obteniendo esquema de la tabla '{table_name}': {e}"

    def _get_tables_schemas(self, tables_names: List[str]) -> str:
        return "\n\n".join(self._get_table_schema(n) for n in tables_names)

    def _query_data_base(self, query: str) -> str:
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(text(query)).fetchall()
            if len(rows) > self.top_n:
                return (
                    f"Hay {len(rows)} registros; limitado a los primeros "
                    f"{self.top_n}:\n\n{rows[: self.top_n]}"
                )
            return f"Hay {len(rows)} registros:\n\n{rows}"
        except Exception as e:
            return f"Error ejecutando query SQL: {e}"

    # --- args ---

    class TablesSchemasArgs(BaseModel):
        tables_names: List[str] = Field(description="Nombres de las tablas a describir.")

    class QueryArgs(BaseModel):
        query: str = Field(description="Query SQL válida para PostgreSQL (solo SELECT).")

    # --- tools ---

    def get_tools(self) -> List[BaseTool]:
        return [
            StructuredTool.from_function(
                name="get_db_tables_names",
                description="Retorna el nombre de todas las tablas de la base de datos.",
                func=self._get_db_tables_names,
            ),
            StructuredTool.from_function(
                name="get_tables_schemas",
                description="Retorna el DDL (CREATE TABLE) de una lista de tablas.",
                func=self._get_tables_schemas,
                args_schema=self.TablesSchemasArgs,
            ),
            StructuredTool.from_function(
                name="query_data_base",
                description=f"Ejecuta un SELECT en PostgreSQL y retorna hasta {self.top_n} filas.",
                func=self._query_data_base,
                args_schema=self.QueryArgs,
            ),
        ]
