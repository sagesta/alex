"""
PostgreSQL client for Google Cloud SQL (or any Postgres) using psycopg 3.

Uses the same SQL and Data-API-style parameter lists as DataAPIClient so
existing models.py queries work unchanged (:name placeholders and parameter lists).
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

# Aurora Data API uses :param names; psycopg uses %(param)s
_NAMED_PARAM = re.compile(r"(?<!:):([a-zA-Z_][a-zA-Z0-9_]*)")


def _sql_to_psycopg(sql: str) -> str:
    return _NAMED_PARAM.sub(lambda m: f"%({m.group(1)})s", sql)


def _decode_data_api_value(field: Dict[str, Any]) -> Any:
    if field.get("isNull"):
        return None
    if "booleanValue" in field:
        return field["booleanValue"]
    if "longValue" in field:
        return field["longValue"]
    if "doubleValue" in field:
        return field["doubleValue"]
    if "stringValue" in field:
        value = field["stringValue"]
        if value and value[0] in "{[":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return value
    if "blobValue" in field:
        return field["blobValue"]
    return None


def _params_list_to_dict(parameters: Optional[List[Dict]]) -> Dict[str, Any]:
    if not parameters:
        return {}
    out: Dict[str, Any] = {}
    for p in parameters:
        name = p["name"]
        value = _decode_data_api_value(p["value"])
        # psycopg3 cannot adapt dict/list directly with %(name)s placeholders;
        # they must be JSON strings when used with ::jsonb casts.
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        out[name] = value
    return out


_pool: Optional[ConnectionPool] = None


def _get_pool(dsn: str) -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=dsn,
            min_size=1,
            max_size=int(os.environ.get("PG_POOL_MAX", "10")),
            kwargs={"connect_timeout": int(os.environ.get("PG_CONNECT_TIMEOUT", "30"))},
        )
    return _pool


class PostgresClient:
    """Postgres backend mirroring DataAPIClient public methods."""

    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.environ.get("DATABASE_URL")
        if not self.dsn:
            raise ValueError("DATABASE_URL is required for PostgresClient")
        self._pool = _get_pool(self.dsn)

    def execute(self, sql: str, parameters: List[Dict] | None = None) -> Dict[str, Any]:
        sql_pg = _sql_to_psycopg(sql)
        params = _params_list_to_dict(parameters)
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_pg, params)
                if cur.description is None:
                    return {"numberOfRecordsUpdated": cur.rowcount}
                colnames = [d.name for d in cur.description]
                rows = cur.fetchall()
                records = []
                for row in rows:
                    record = []
                    for i, col in enumerate(row):
                        record.append(self._python_to_field(col))
                    records.append(record)
                return {
                    "columnMetadata": [{"name": n} for n in colnames],
                    "records": records,
                    "numberOfRecordsUpdated": cur.rowcount,
                }

    def query(self, sql: str, parameters: List[Dict] | None = None) -> List[Dict]:
        response = self.execute(sql, parameters)
        if "records" not in response:
            return []
        columns = [col["name"] for col in response.get("columnMetadata", [])]
        results = []
        for record in response["records"]:
            row = {}
            for i, col in enumerate(columns):
                row[col] = self._extract_value(record[i])
            results.append(row)
        return results

    def query_one(self, sql: str, parameters: List[Dict] | None = None) -> Optional[Dict]:
        rows = self.query(sql, parameters)
        return rows[0] if rows else None

    def insert(self, table: str, data: Dict, returning: str | None = None) -> str | None:
        columns = list(data.keys())
        placeholders = []
        for col in columns:
            val = data[col]
            if isinstance(val, (dict, list)):
                placeholders.append(f":{col}::jsonb")
            elif isinstance(val, Decimal):
                placeholders.append(f":{col}::numeric")
            elif isinstance(val, date) and not isinstance(val, datetime):
                placeholders.append(f":{col}::date")
            elif isinstance(val, datetime):
                placeholders.append(f":{col}::timestamp")
            else:
                placeholders.append(f":{col}")

        sql = f"""
            INSERT INTO {table} ({", ".join(columns)})
            VALUES ({", ".join(placeholders)})
        """
        if returning:
            sql += f" RETURNING {returning}"

        parameters = self._build_parameters(data)
        response = self.execute(sql, parameters)
        if returning and response.get("records"):
            return self._extract_value(response["records"][0][0])
        return None

    def update(self, table: str, data: Dict, where: str, where_params: Dict | None = None) -> int:
        set_parts = []
        for col, val in data.items():
            if isinstance(val, (dict, list)):
                set_parts.append(f"{col} = :{col}::jsonb")
            elif isinstance(val, Decimal):
                set_parts.append(f"{col} = :{col}::numeric")
            elif isinstance(val, date) and not isinstance(val, datetime):
                set_parts.append(f"{col} = :{col}::date")
            elif isinstance(val, datetime):
                set_parts.append(f"{col} = :{col}::timestamp")
            else:
                set_parts.append(f"{col} = :{col}")

        set_clause = ", ".join(set_parts)
        sql = f"""
            UPDATE {table}
            SET {set_clause}
            WHERE {where}
        """
        all_params = {**data, **(where_params or {})}
        parameters = self._build_parameters(all_params)
        response = self.execute(sql, parameters)
        return response.get("numberOfRecordsUpdated", 0)

    def delete(self, table: str, where: str, where_params: Dict | None = None) -> int:
        sql = f"DELETE FROM {table} WHERE {where}"
        parameters = self._build_parameters(where_params) if where_params else None
        response = self.execute(sql, parameters)
        return response.get("numberOfRecordsUpdated", 0)

    def begin_transaction(self) -> str:
        raise NotImplementedError(
            "PostgresClient transactions use connection-scoped logic; "
            "callers using transactions should use raw SQL or extend this client."
        )

    def commit_transaction(self, transaction_id: str) -> None:
        raise NotImplementedError("PostgresClient uses pool connections; use explicit SQL transactions.")

    def rollback_transaction(self, transaction_id: str) -> None:
        raise NotImplementedError("PostgresClient uses pool connections; use explicit SQL transactions.")

    def _build_parameters(self, data: Dict) -> List[Dict]:
        if not data:
            return []

        parameters = []
        for key, value in data.items():
            param: Dict[str, Any] = {"name": key}

            if value is None:
                param["value"] = {"isNull": True}
            elif isinstance(value, bool):
                param["value"] = {"booleanValue": value}
            elif isinstance(value, int):
                param["value"] = {"longValue": value}
            elif isinstance(value, float):
                param["value"] = {"doubleValue": value}
            elif isinstance(value, Decimal):
                param["value"] = {"stringValue": str(value)}
            elif isinstance(value, (date, datetime)):
                param["value"] = {"stringValue": value.isoformat()}
            elif isinstance(value, dict):
                param["value"] = {"stringValue": json.dumps(value)}
            elif isinstance(value, list):
                param["value"] = {"stringValue": json.dumps(value)}
            else:
                param["value"] = {"stringValue": str(value)}

            parameters.append(param)

        return parameters

    def _python_to_field(self, value: Any) -> Dict[str, Any]:
        if value is None:
            return {"isNull": True}
        if isinstance(value, bool):
            return {"booleanValue": value}
        if isinstance(value, int):
            return {"longValue": value}
        if isinstance(value, float):
            return {"doubleValue": value}
        if isinstance(value, Decimal):
            return {"stringValue": str(value)}
        if isinstance(value, (date, datetime)):
            return {"stringValue": value.isoformat()}
        if isinstance(value, uuid.UUID):
            return {"stringValue": str(value)}
        if isinstance(value, dict):
            return {"stringValue": json.dumps(value)}
        if isinstance(value, list):
            return {"stringValue": json.dumps(value)}
        return {"stringValue": str(value)}

    def _extract_value(self, field: Dict[str, Any]) -> Any:
        if field.get("isNull"):
            return None
        if "booleanValue" in field:
            return field["booleanValue"]
        if "longValue" in field:
            return field["longValue"]
        if "doubleValue" in field:
            return field["doubleValue"]
        if "stringValue" in field:
            value = field["stringValue"]
            if value and len(value) > 0 and value[0] in "{[":
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            return value
        if "blobValue" in field:
            return field["blobValue"]
        return None
