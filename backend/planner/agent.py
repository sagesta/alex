"""
Financial Planner Orchestrator Agent - coordinates portfolio analysis across specialized agents.
"""

import os
import json
import boto3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

import httpx
from agents import function_tool, RunContextWrapper

from src.litellm_model_factory import create_litellm_model

logger = logging.getLogger()

# Initialize Lambda client (AWS); unused when PLANNER_USE_HTTP_AGENTS=true
lambda_client = boto3.client("lambda")

# Lambda function names from environment
TAGGER_FUNCTION = os.getenv("TAGGER_FUNCTION", "alex-tagger")
REPORTER_FUNCTION = os.getenv("REPORTER_FUNCTION", "alex-reporter")
CHARTER_FUNCTION = os.getenv("CHARTER_FUNCTION", "alex-charter")
RETIREMENT_FUNCTION = os.getenv("RETIREMENT_FUNCTION", "alex-retirement")
MOCK_LAMBDAS = os.getenv("MOCK_LAMBDAS", "false").lower() == "true"

# GCP Cloud Run (or any HTTP) agent endpoints — POST JSON body matching Lambda payload
PLANNER_USE_HTTP_AGENTS = os.getenv("PLANNER_USE_HTTP_AGENTS", "").lower() == "true"
ALEX_HTTP_TAGGER_URL = os.getenv("ALEX_HTTP_TAGGER_URL", "")
ALEX_HTTP_REPORTER_URL = os.getenv("ALEX_HTTP_REPORTER_URL", "")
ALEX_HTTP_CHARTER_URL = os.getenv("ALEX_HTTP_CHARTER_URL", "")
ALEX_HTTP_RETIREMENT_URL = os.getenv("ALEX_HTTP_RETIREMENT_URL", "")


@dataclass
class PlannerContext:
    """Context for planner agent tools."""
    job_id: str


def _http_url_for_agent(agent_name: str) -> str:
    return {
        "Tagger": ALEX_HTTP_TAGGER_URL,
        "Reporter": ALEX_HTTP_REPORTER_URL,
        "Charter": ALEX_HTTP_CHARTER_URL,
        "Retirement": ALEX_HTTP_RETIREMENT_URL,
    }.get(agent_name, "")


async def invoke_lambda_agent(
    agent_name: str, function_name: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Invoke a Lambda function or HTTP endpoint (Cloud Run) for an agent."""

    if MOCK_LAMBDAS:
        logger.info(f"[MOCK] Would invoke {agent_name} with payload: {json.dumps(payload)[:200]}")
        return {"success": True, "message": f"[Mock] {agent_name} completed", "mock": True}

    if PLANNER_USE_HTTP_AGENTS:
        url = _http_url_for_agent(agent_name)
        if not url:
            msg = f"No HTTP URL for {agent_name}; set ALEX_HTTP_{agent_name.upper()}_URL"
            logger.error(msg)
            return {"error": msg}
        try:
            logger.info(f"POST {agent_name} -> {url}")
            async with httpx.AsyncClient(timeout=httpx.Timeout(900.0)) as client:
                headers = {}
                token = os.getenv("GCP_AGENT_AUTH_TOKEN")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                r = await client.post(url, json=payload, headers=headers)
                r.raise_for_status()
                result = r.json()
            if isinstance(result, dict) and "statusCode" in result and "body" in result:
                if isinstance(result["body"], str):
                    try:
                        result = json.loads(result["body"])
                    except json.JSONDecodeError:
                        result = {"message": result["body"]}
                else:
                    result = result["body"]
            logger.info(f"{agent_name} completed successfully")
            return result if isinstance(result, dict) else {"result": result}
        except Exception as e:
            logger.error(f"Error invoking {agent_name} HTTP: {e}")
            return {"error": str(e)}

    try:
        logger.info(f"Invoking {agent_name} Lambda: {function_name}")

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        result = json.loads(response["Payload"].read())

        if isinstance(result, dict) and "statusCode" in result and "body" in result:
            if isinstance(result["body"], str):
                try:
                    result = json.loads(result["body"])
                except json.JSONDecodeError:
                    result = {"message": result["body"]}
            else:
                result = result["body"]

        logger.info(f"{agent_name} completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error invoking {agent_name}: {e}")
        return {"error": str(e)}


def handle_missing_instruments(job_id: str, db) -> None:
    """
    Check for and tag any instruments missing allocation data.
    This is done automatically before the agent runs.
    """
    logger.info("Planner: Checking for instruments missing allocation data...")

    # Get job and portfolio data
    job = db.jobs.find_by_id(job_id)
    if not job:
        logger.error(f"Job {job_id} not found")
        return

    user_id = job["clerk_user_id"]
    accounts = db.accounts.find_by_user(user_id)

    missing = []
    for account in accounts:
        positions = db.positions.find_by_account(account["id"])
        for position in positions:
            instrument = db.instruments.find_by_symbol(position["symbol"])
            if instrument:
                has_allocations = bool(
                    instrument.get("allocation_regions")
                    and instrument.get("allocation_sectors")
                    and instrument.get("allocation_asset_class")
                )
                if not has_allocations:
                    missing.append(
                        {"symbol": position["symbol"], "name": instrument.get("name", "")}
                    )
            else:
                missing.append({"symbol": position["symbol"], "name": ""})

    if missing:
        logger.info(
            f"Planner: Found {len(missing)} instruments needing classification: {[m['symbol'] for m in missing]}"
        )

        try:
            payload = {"instruments": missing}
            if PLANNER_USE_HTTP_AGENTS:
                url = ALEX_HTTP_TAGGER_URL
                if not url:
                    logger.error("ALEX_HTTP_TAGGER_URL is not set")
                else:
                    headers = {}
                    token = os.getenv("GCP_AGENT_AUTH_TOKEN")
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                    r = httpx.post(url, json=payload, headers=headers, timeout=300.0)
                    r.raise_for_status()
                    result = r.json()
                    if isinstance(result, dict) and result.get("statusCode") == 200:
                        logger.info(
                            f"Planner: InstrumentTagger completed - Tagged {len(missing)} instruments"
                        )
                    elif isinstance(result, dict) and "statusCode" in result:
                        logger.error(
                            f"Planner: InstrumentTagger failed with status {result.get('statusCode')}"
                        )
                    else:
                        logger.info("Planner: InstrumentTagger HTTP call completed")
            else:
                response = lambda_client.invoke(
                    FunctionName=TAGGER_FUNCTION,
                    InvocationType="RequestResponse",
                    Payload=json.dumps(payload),
                )

                result = json.loads(response["Payload"].read())

                if isinstance(result, dict) and "statusCode" in result:
                    if result["statusCode"] == 200:
                        logger.info(
                            f"Planner: InstrumentTagger completed - Tagged {len(missing)} instruments"
                        )
                    else:
                        logger.error(
                            f"Planner: InstrumentTagger failed with status {result['statusCode']}"
                        )

        except Exception as e:
            logger.error(f"Planner: Error tagging instruments: {e}")
    else:
        logger.info("Planner: All instruments have allocation data")


def load_portfolio_summary(job_id: str, db) -> Dict[str, Any]:
    """Load basic portfolio summary statistics only."""
    try:
        job = db.jobs.find_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        user_id = job["clerk_user_id"]
        user = db.users.find_by_clerk_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        accounts = db.accounts.find_by_user(user_id)
        
        # Calculate simple summary statistics
        total_value = 0.0
        total_positions = 0
        total_cash = 0.0
        
        for account in accounts:
            total_cash += float(account.get("cash_balance", 0))
            positions = db.positions.find_by_account(account["id"])
            total_positions += len(positions)
            
            # Add position values
            for position in positions:
                instrument = db.instruments.find_by_symbol(position["symbol"])
                if instrument and instrument.get("current_price"):
                    price = float(instrument["current_price"])
                    quantity = float(position["quantity"])
                    total_value += price * quantity
        
        total_value += total_cash
        
        # Return only summary statistics
        return {
            "total_value": total_value,
            "num_accounts": len(accounts),
            "num_positions": total_positions,
            "years_until_retirement": user.get("years_until_retirement", 30),
            "target_retirement_income": float(user.get("target_retirement_income", 80000))
        }

    except Exception as e:
        logger.error(f"Error loading portfolio summary: {e}")
        raise


async def invoke_reporter_internal(job_id: str) -> str:
    """
    Invoke the Report Writer Lambda (or HTTP agent) to generate portfolio analysis narrative.

    Args:
        job_id: The job ID for the analysis

    Returns:
        Confirmation message
    """
    result = await invoke_lambda_agent("Reporter", REPORTER_FUNCTION, {"job_id": job_id})

    if "error" in result:
        return f"Reporter agent failed: {result['error']}"

    return "Reporter agent completed successfully. Portfolio analysis narrative has been generated and saved."


async def invoke_charter_internal(job_id: str) -> str:
    """
    Invoke the Chart Maker Lambda to create portfolio visualizations.

    Args:
        job_id: The job ID for the analysis

    Returns:
        Confirmation message
    """
    result = await invoke_lambda_agent(
        "Charter", CHARTER_FUNCTION, {"job_id": job_id}
    )

    if "error" in result:
        return f"Charter agent failed: {result['error']}"

    return "Charter agent completed successfully. Portfolio visualizations have been created and saved."


async def invoke_retirement_internal(job_id: str) -> str:
    """
    Invoke the Retirement Specialist Lambda for retirement projections.

    Args:
        job_id: The job ID for the analysis

    Returns:
        Confirmation message
    """
    result = await invoke_lambda_agent("Retirement", RETIREMENT_FUNCTION, {"job_id": job_id})

    if "error" in result:
        return f"Retirement agent failed: {result['error']}"

    return "Retirement agent completed successfully. Retirement projections have been calculated and saved."



@function_tool
async def invoke_reporter(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Invoke the Report Writer agent to generate portfolio analysis narrative."""
    return await invoke_reporter_internal(wrapper.context.job_id)

@function_tool
async def invoke_charter(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Invoke the Chart Maker agent to create portfolio visualizations."""
    return await invoke_charter_internal(wrapper.context.job_id)

@function_tool
async def invoke_retirement(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Invoke the Retirement Specialist agent for retirement projections."""
    return await invoke_retirement_internal(wrapper.context.job_id)


def create_agent(job_id: str, portfolio_summary: Dict[str, Any], db):
    """Create the orchestrator agent with tools."""
    
    # Create context for tools
    context = PlannerContext(job_id=job_id)

    model = create_litellm_model()

    tools = [
        invoke_reporter,
        invoke_charter,
        invoke_retirement,
    ]

    # Create minimal task context
    task = f"""Job {job_id} has {portfolio_summary['num_positions']} positions.
Retirement: {portfolio_summary['years_until_retirement']} years.

Call the appropriate agents."""

    return model, tools, task, context
