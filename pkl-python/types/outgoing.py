from typing import Any, Dict, List, Tuple, Union, Optional
from enum import Enum

class ResourceReader:
    def __init__(self, scheme: str, hasHierarchicalUris: bool, isGlobbable: bool):
        self.scheme = scheme
        self.hasHierarchicalUris = hasHierarchicalUris
        self.isGlobbable = isGlobbable

class ModuleReader:
    def __init__(self, scheme: str, hasHierarchicalUris: bool, isGlobbable: bool, isLocal: bool):
        self.scheme = scheme
        self.hasHierarchicalUris = hasHierarchicalUris
        self.isGlobbable = isGlobbable
        self.isLocal = isLocal

class Checksums:
    def __init__(self, checksums: str):
        self.checksums = checksums

class ProjectOrDependency:
    def __init__(self, packageUri: Optional[str], type: Optional[str], projectFileUri: Optional[str], checksums: Optional[Checksums], dependencies: Optional[Dict[str, 'ProjectOrDependency']]):
        self.packageUri = packageUri
        self.type = type
        self.projectFileUri = projectFileUri
        self.checksums = checksums
        self.dependencies = dependencies

class CreateEvaluator:
    def __init__(self, requestId: int, clientResourceReaders: Optional[List[ResourceReader]], clientModuleReaders: Optional[List[ModuleReader]], modulePaths: Optional[List[str]], env: Optional[Dict[str, str]], properties: Optional[Dict[str, str]], outputFormat: Optional[str], allowedModules: Optional[List[str]], allowedResources: Optional[List[str]], rootDir: Optional[str], cacheDir: Optional[str], project: Optional[ProjectOrDependency], code: code):
        self.requestId = requestId
        self.clientResourceReaders = clientResourceReaders
        self.clientModuleReaders = clientModuleReaders
        self.modulePaths = modulePaths
        self.env = env
        self.properties = properties
        self.outputFormat = outputFormat
        self.allowedModules = allowedModules
        self.allowedResources = allowedResources
        self.rootDir = rootDir
        self.cacheDir = cacheDir
        self.project = project
        self.code = code

class Evaluate:
    def __init__(self, requestId: int, evaluatorId: int, moduleUri: str, code: code, expr: Optional[str] = None, moduleText: Optional[str] = None):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.moduleUri = moduleUri
        self.expr = expr
        self.moduleText = moduleText
        self.code = code

class ReadResource:
    def __init__(self, requestId: int, evaluatorId: int, uri: str, code: code):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.uri = uri
        self.code = code

class ReadModule:
    def __init__(self, requestId: int, evaluatorId: int, uri: str, code: code):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.uri = uri
        self.code = code

class ListResources:
    def __init__(self, requestId: int, evaluatorId: int, uri: str, code: code):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.uri = uri
        self.code = code

class ListModules:
    def __init__(self, requestId: int, evaluatorId: int, uri: str, code: code):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.uri = uri
        self.code = code

class CloseEvaluator:
    def __init__(self, requestId: int, evaluatorId: int, code: code):
        self.requestId = requestId
        self.evaluatorId = evaluatorId
        self.code = code

OutgoingMessage = Union[
    CreateEvaluator,
    Evaluate,
    ReadResource,
    ReadModule,
    ListResources,
    ListModules,
    CloseEvaluator
]