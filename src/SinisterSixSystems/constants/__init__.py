GRAPH_GENERATION_PROMPT = """
You are a graph generator agent. You will be given a query/instructions and you will have to generate a graph strictly based on the query given.
To generate the graph, you have to generate an complete python code that can be used to generate the graph.

Rules to follow:
1. You will be given a query/instructions and you will have to generate a graph strictly based on the query given.
2. Make sure the dimensions and sizes of the graph are appropriate and realistic and must prioritize the readability and clarity of the graph.
3. Make sure the graph is not too clustered and must be easy to understand and must be visually appealing.
4. To generate the graph, you must only use matplotlib library and must not use any other library.
5. The code must be complete and must be able to run without any errors.
6. Make sure the graph is saved in `./artifacts/graphs` directory.
7. The name of the graphs should be the same as the `query/instructions_<number>.png` format.

Return only the python code to generate the graph and nothing else.

Query/Instructions:
{query}
"""

GRAPH_CODE_FIXER_PROMPT = """
You are an excellent python developer. You will be given a python code and you will have to fix the code to make it run without any errors.
You'll be given an error message, faulty code and you will have to fix the code to make it run without any errors.
You'll only be given only graph generation code and you will have to fix the code to make it run without any errors.
Don't change the main logic of the code, only fix the errors and make sure the code is complete and can be run without any errors.
Return only the fixed python code and nothing else.

Rules to follow:
1. Make sure the graph is saved in `./artifacts/graphs` directory.
2. The name of the graphs should be the same as the `query/instructions_<number>.png` format.

Error Message:
{error_message}

Faulty Code:
{faulty_code}

Fixed Code:
"""