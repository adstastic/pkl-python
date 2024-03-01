from pkl_python.evaluator.evaluator_exec import new_evaluator_manager_with_command
from pkl_python.evaluator.evaluator_options import EvaluatorOptions, OutputFormat
import asyncio

async def test_evaluator():
    PATH = "/Users/adi/.local/bin/pkl"
    manager = new_evaluator_manager_with_command([PATH])
    options = EvaluatorOptions(output_format=OutputFormat.JSON)
    evaluator = await manager.new_evaluator(options)
    module_path = "tests/test.pkl"
    result = evaluator.evaluate_module(source=module_path)
    print(result)

asyncio.run(test_evaluator())
