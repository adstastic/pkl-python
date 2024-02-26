from typing import Any, Dict, List, Tuple, Union
from codes import *
from pydantic import BaseModel

class CreateEvaluatorResponse:
    def __init__(self, requestId: int, evaluatorId: int, error: str, code: int):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.error = error
        self.code = code

class EvaluateResponse:
    def __init__(self, requestId: int, evaluatorId: int, result: bytes, error: str, code: int):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.result = result
        self.error = error
        self.code = code

class ReadResource:
    def __init__(self, requestId: int, evaluatorId: int, uri: str, code: int):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.uri = uri
        self.code = code

class ReadModule:
    def __init__(self, requestId: int, evaluatorId: int, uri: str, code: int):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.uri = uri
        self.code = code

class Log:
    def __init__(self, evaluatorId: int, level: int, message: str, frameUri: str, code: int):
        self.evaluatorId = evaluatorId
        self.level = level
        self.message = message
        self.frameUri = frameUri
        self.code = code

class ListResources:
    def __init__(self, requestId: int, evaluatorId: int, uri: str, code: int):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.uri = uri
        self.code = code

class ListModules:
    def __init__(self, requestId: int, evaluatorId: int, uri: str, code: int):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.uri = uri
        self.code = code

IncomingMessage = Union[
    CreateEvaluatorResponse,
    EvaluateResponse,
    ReadResource,
    ReadModule,
    Log,
    ListResources,
    ListModules
]

class Incoming(BaseModel):
    code: int
    map: Dict[str, Any]

def decode(incoming: Incoming) -> 'IncomingMessage':
    code, map = incoming.code, incoming.map
    value = map
    if code == codeEvaluateResponse:
        return EvaluateResponse(**value, code=codeEvaluateResponse)
    elif code == codeEvaluateLog:
        return Log(**value, code=codeEvaluateLog)
    elif code == codeNewEvaluatorResponse:
        return CreateEvaluatorResponse(**value, code=codeNewEvaluatorResponse)
    elif code == codeEvaluateRead:
        return ReadResource(**value, code=codeEvaluateRead)
    elif code == codeEvaluateReadModule:
        return ReadModule(**value, code=codeEvaluateReadModule)
    elif code == codeListResourcesRequest:
        return ListResources(**value, code=codeListResourcesRequest)
    elif code == codeListModulesRequest:
        return ListModules(**value, code=codeListModulesRequest)
    else:
        raise ValueError(f"Unknown code: {code}")