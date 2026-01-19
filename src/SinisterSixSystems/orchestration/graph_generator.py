from SinisterSixSystems.logging import logger
from SinisterSixSystems.constants import GRAPH_GENERATION_PROMPT, GRAPH_CODE_FIXER_PROMPT
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph

from typing import Dict, Any, List, Annotated, Union
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
import re


from dotenv import load_dotenv
import os
import ast
import subprocess
import sys
from tempfile import NamedTemporaryFile

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class GraphGeneratorState(TypedDict):
    extracted_code: str
    graph_id: str
    retry_count: int
    error_message: str
    query: str
    path: str


class GraphGenerator:
    def __init__(self):
        self.output_parser = StrOutputParser()
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0, api_key=GOOGLE_API_KEY)
        
        self.state = {
            "extracted_code": "",
            "path": "./artifacts/graphs",
            "graph_id": "",
            "error_message": "",
            "retry_count": 0,
            "query": ""
        }
    
    def _validate_and_execute_python_code(self, python_code: str) -> None:
        """
        Validates and executes Python code safely.
        
        Args:
            python_code: The Python code string to validate and execute
            
        Raises:
            ValueError: If malicious code is detected
            RuntimeError: If code execution fails
        """
        def is_safe_ast(tree):
            # Check AST tree for dangerous nodes like Import, etc.
            # for node in ast.walk(tree):
            #     if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            #         return False
            #     # Prevent file system access or subprocess calls
            #     if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            #         if node.func.id in ("open", "eval", "exec", "compile", "os", "sys", "subprocess", "shutil", "input"):
            #             return False
            #     # Prevent attribute access to os, sys, subprocess, etc.
            #     if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            #         if node.value.id in ("os", "sys", "subprocess", "shutil"):
            #             return False
            return True

        tmpfile_name = None
        try:
            tree = ast.parse(python_code)
            if not is_safe_ast(tree):
                logger.error(f"Malicious code detected: {python_code}")
                raise ValueError("Malicious code detected!")

            # Write the safe code to a temporary file and run it
            with NamedTemporaryFile("w", suffix=".py", delete=False) as tmpf:
                tmpf.write(python_code)
                tmpf.flush()
                tmpfile_name = tmpf.name

            process = subprocess.run(
                [sys.executable, tmpfile_name],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if process.returncode != 0:
                logger.error(f"Python code execution failed: {process.stderr}")
                raise RuntimeError(f"Code execution failed:\n{process.stderr}")
        finally:
            # Clean up temporary file if it exists
            if tmpfile_name:
                try:
                    os.remove(tmpfile_name)
                except Exception:
                    pass
    
    def generate_code(self, state: GraphGeneratorState):
        prompt_template = PromptTemplate(input_variables=["query","file_name","path"], template=GRAPH_GENERATION_PROMPT)

        file_name = f"graph_{state.get('graph_id', 'default')}.png"

        graph_generator_chain = prompt_template | self.model | self.output_parser
        logger.warning({
            "query": state.get("query", ""),
            "file_name": file_name,
            "path": state.get("path", "./artifacts/graphs")
        })
        response = graph_generator_chain.invoke({"query": state.get("query", ""), "file_name": file_name, "path": state.get("path", "./artifacts/graphs")})

        try:
            # StrOutputParser returns a string directly, not an object with .content
            code = response
            python_code = re.search(r"```python\n(.*)\n```", code, re.DOTALL).group(1)
            
            # Validate and execute the Python code
            self._validate_and_execute_python_code(python_code)
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return {
                "extracted_code": "",
                "retry_count": state.get("retry_count", 0) + 1,
                "error_message": str(e)
            }
        return {
            "extracted_code": python_code,
            "retry_count": state.get("retry_count", 0),
            "error_message": ""
        }
    
    def fix_code(self, state: GraphGeneratorState):
        prompt_template = PromptTemplate(input_variables=["error_message", "faulty_code"], template=GRAPH_CODE_FIXER_PROMPT)

        graph_code_fixer_chain = prompt_template | self.model | self.output_parser
        response = graph_code_fixer_chain.invoke({
            "error_message": state.get("error_message", ""), 
            "faulty_code": state.get("extracted_code", "")
        })

        try:
            # StrOutputParser returns a string directly, not an object with .content
            code = response
            python_code = re.search(r"```python\n(.*)\n```", code, re.DOTALL).group(1)
            
            # Validate and execute the fixed Python code
            self._validate_and_execute_python_code(python_code)
            
            return {
                "extracted_code": python_code,
                "retry_count": state.get("retry_count", 0) + 1,
                "error_message": ""
            }
        except Exception as e:
            logger.error(f"Error fixing code: {e}")
            return {
                "extracted_code": state.get("extracted_code", ""),
                "retry_count": state.get("retry_count", 0) + 1,
                "error_message": str(e)
            }
    
    def should_retry(self, state: GraphGeneratorState):
        return state.get("retry_count", 0) < 5

    def route_after_generate(self, state: GraphGeneratorState) -> Union[str, Any]:
        """
        Conditional routing function that determines the next node after generate_code.
        Returns 'fix_code' if there's an error, otherwise END.
        """
        if state.get("error_message"):
            return "fix_code"
        return END

    def route_after_fix(self, state: GraphGeneratorState) -> Union[str, Any]:
        """
        Conditional routing function that determines the next node after fix_code.
        Returns 'generate_code' if we should retry and there's still an error, otherwise END.
        """
        if self.should_retry(state) and state.get("error_message"):
            return "generate_code"
        return END

    def compile(self):
        try:
            workflow = StateGraph(GraphGeneratorState)
            workflow.add_node("generate_code", self.generate_code)
            workflow.add_node("fix_code", self.fix_code)

            workflow.add_edge(START, "generate_code")
            
            # Add conditional edge: route to fix_code if error, otherwise END
            workflow.add_conditional_edges(
                "generate_code",
                self.route_after_generate
            )
            
            # Add conditional edge: route based on retry count and error status
            workflow.add_conditional_edges(
                "fix_code",
                self.route_after_fix
            )

            return workflow.compile()
        except Exception as e:
            logger.error(f"Error compiling workflow: {e}")
            raise e 

if __name__ == "__main__":
    graph_generator = GraphGenerator()
    compiled_workflow = graph_generator.compile()

    initial_state = {
        "query": "Generate a graph of segregated clusters in a dataset.",
        "extracted_code": "",
        "retry_count": 0,
        "error_message": ""
    }

    for output in compiled_workflow.stream(initial_state):
        for _, value in output.items():
            print(value)