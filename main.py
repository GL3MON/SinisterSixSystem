from SinisterSixSystems.orchestration.orchestrator import Orchestrator
from SinisterSixSystems.entity import ChatRequest
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from SinisterSixSystems.logging import logger

from langgraph.graph import StateGraph, START, END
from src.SinisterSixSystems.orchestration.state import AgentState

import os
import re


app = FastAPI(title="SinisterSix")

orchestrator = Orchestrator()
orchestrator_workflow = orchestrator.compile()


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        logger.info(f"Received chat request: {req}")
        
        


        if req.document != "":
            logger.info("Using provided document for context.")
            response = orchestrator_workflow.invoke({"messages": [HumanMessage(content=req.query)], "document": req.document})
        else:
            logger.info("No document provided, proceeding without context.")
            response = orchestrator_workflow.invoke({"messages": [HumanMessage(content=req.query)], "document": ""})
        logger.info(f"Generated response: {response['response']}")
        return {"response": f"./artifacts/processed_files/{req.query[:50]}/"}
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/latex_document/")
def get_latex_document(request: ChatRequest):
    query = request.query




@app.get("/")
def root():
    return {"message": "FinConnect Chatbot API is running 🚀"}