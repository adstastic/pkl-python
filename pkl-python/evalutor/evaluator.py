from typing import Any, Dict
from abc import ABC, abstractmethod
from module_source import ModuleSource
from urllib.parse import urlparse
from types.incoming import EvaluateResponse, ListModules, ListResources, Log, ReadModule, ReadResource 
from types.outgoing import Evaluate
from types import codes
from evaluator_manager import EvaluatorManager

# Evaluator is an interface for evaluating Pkl modules.
class Evaluator(ABC):
    # evaluateModule evaluates the given module, and writes it to the value pointed by
    # out.
    #
    # This method is designed to work with TS modules that have been code generated from Pkl
    # sources.
    @abstractmethod
    def evaluate_module(self, source: ModuleSource) -> Any:
        pass

    # evaluateOutputText evaluates the `output.text` property of the given module.
    @abstractmethod
    def evaluate_output_text(self, source: ModuleSource) -> str:
        pass

    # evaluateOutputValue evaluates the `output.value` property of the given module,
    # and writes to the value pointed by out.
    @abstractmethod
    def evaluate_output_value(self, source: ModuleSource) -> Any:
        pass

    # evaluateOutputFiles evaluates the `output.files` property of the given module.
    @abstractmethod
    def evaluate_output_files(self, source: ModuleSource) -> Dict[str, str]:
        pass

    # evaluateExpression evaluates the provided expression on the given module source, and writes
    # the result into the value pointed by out.
    @abstractmethod
    def evaluate_expression(self, source: ModuleSource, expr: str) -> Any:
        pass

    # evaluateExpressionRaw evaluates the provided module, and returns the underlying value's raw
    # bytes.
    #
    # This is a low level API.
    @abstractmethod
    def evaluate_expression_raw(self, source: ModuleSource, expr: str) -> bytes:
        pass

    # close closes the evaluator and releases any underlying resources.
    @abstractmethod
    def close(self) -> None:
        pass

    # closed tells if this evaluator is closed.
    @property
    @abstractmethod
    def closed(self) -> bool:
        pass


class EvaluatorImpl(Evaluator):
    def __init__(self, evaluator_id: int, manager: EvaluatorManager):
        self.evaluator_id = evaluator_id
        self.manager = manager
        self.pending_requests = {}
        self.closed = False
        self.resource_readers = []
        self.module_readers = []
        self.rand_state = evaluator_id

    def close(self):
        self.closed = True
        self.manager.close()

    async def evaluate_expression(self, source: 'ModuleSource', expr: str) -> Any:
        bytes = await self.evaluate_expression_raw(source, expr)
        return self.manager.decoder.decode(bytes)

    async def evaluate_expression_raw(self, source: 'ModuleSource', expr: str) -> bytes:
        if self.closed:
            raise Exception("evaluator is closed")

        evaluate = Evaluate(
            request_id=self.random_int63(),
            evaluator_id=self.evaluator_id,
            module_uri=source.uri.to_string(),
            code=codes.Evaluate,
            expr=expr,
            module_text=source.contents
        )

        self.pending_requests[evaluate.request_id] = evaluate

        await self.manager.send(evaluate)

        resp = await self.pending_requests[evaluate.request_id]
        if resp.error:
            raise Exception(resp.error)

        return resp.result

    async def evaluate_module(self, source: 'ModuleSource') -> Any:
        return await self.evaluate_expression(source, "")

    async def evaluate_output_files(self, source: 'ModuleSource') -> Dict[str, str]:
        return await self.evaluate_expression(source, "output.files.toMap().mapValues((_, it) -> it.text)")

    async def evaluate_output_text(self, source: 'ModuleSource') -> str:
        return await self.evaluate_expression(source, "output.text")

    async def evaluate_output_value(self, source: 'ModuleSource') -> Any:
        return await self.evaluate_expression(source, "output.value")

    def handle_evaluate_response(self, msg: 'EvaluateResponse'):
        pending = self.pending_requests.get(msg.request_id)
        if not pending:
            print("warn: received a message for an unknown request id:", msg.request_id)
            return
        pending.resolve(msg)

    def handle_log(self, resp: 'Log'):
        if resp.level == 0:
            print(resp.message, resp.frame_uri)
        elif resp.level == 1:
            print(resp.message, resp.frame_uri)
        else:
            raise Exception(f"unknown log level: {resp.level}")

    async def handle_read_resource(self, msg: 'ReadResource'):
        response = {'evaluatorId': self.evaluator_id, 'requestId': msg.request_id, 'code': codes.EvaluateReadResponse}
        try:
            url = urlparse(msg.uri)
        except Exception as e:
            await self.manager.send({**response, 'error': f"internal error: failed to parse resource url: {e}"})
            return

        reader = next((r for r in self.resource_readers if f"{r.scheme}:" == url.scheme), None)

        if not reader:
            await self.manager.send({**response, 'error': f"No resource reader found for scheme {url.scheme}"})
            return

        try:
            contents = reader.read(url)
            await self.manager.send({**response, 'contents': contents})
        except Exception as e:
            await self.manager.send({**response, 'error': str(e)})

    async def handle_read_module(self, msg: 'ReadModule'):
        response = {'evaluatorId': self.evaluator_id, 'requestId': msg.request_id, 'code': codes.EvaluateReadModuleResponse}
        try:
            url = urlparse(msg.uri)
        except Exception as e:
            await self.manager.send({**response, 'error': f"internal error: failed to parse resource url: {e}"})
            return

        reader = next((r for r in self.module_readers if f"{r.scheme}:" == url.scheme), None)

        if not reader:
            await self.manager.send({**response, 'error': f"No module reader found for scheme {url.scheme}"})
            return

        try:
            contents = reader.read(url)
            await self.manager.send({**response, 'contents': contents})
        except Exception as e:
            await self.manager.send({**response, 'error': str(e)})

    async def handle_list_resources(self, msg: 'ListResources'):
        response = {'evaluatorId': self.evaluator_id, 'requestId': msg.request_id, 'code': codes.ListResourcesResponse}
        try:
                    url = urlparse(msg.uri)
        except Exception as e:
            await self.manager.send({**response, 'error': f"internal error: failed to parse resource url: {e}"})
            return

        reader = next((r for r in self.resource_readers if f"{r.scheme}:" == url.scheme), None)

        if not reader:
            await self.manager.send({**response, 'error': f"No resource reader found for scheme {url.scheme}"})
            return

        try:
            path_elements = reader.list_elements(url)
            await self.manager.send({**response, 'pathElements': path_elements})
        except Exception as e:
            await self.manager.send({**response, 'error': str(e)})

    async def handle_list_modules(self, msg: 'ListModules'):
        response = {'evaluatorId': self.evaluator_id, 'requestId': msg.request_id, 'code': codes.ListModulesResponse}
        try:
            url = urlparse(msg.uri)
        except Exception as e:
            await self.manager.send({**response, 'error': f"internal error: failed to parse resource url: {e}"})
            return

        reader = next((r for r in self.module_readers if f"{r.scheme}:" == url.scheme), None)

        if not reader:
            await self.manager.send({**response, 'error': f"No module reader found for scheme {url.scheme}"})
            return

        try:
            path_elements = reader.list_elements(url)
            await self.manager.send({**response, 'pathElements': path_elements})
        except Exception as e:
            await self.manager.send({**response, 'error': str(e)})