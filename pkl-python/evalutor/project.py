from dataclasses import dataclass
from typing import Optional, Dict, List
from evaluator_options import PreconfiguredOptions, ProjectDependencies
from evaluator_exec import new_evaluator
from module_source import FileSource

@dataclass
class ProjectPackage:
    name: str
    base_uri: str
    version: str
    package_zip_url: str
    description: str
    authors: List[str]
    website: str
    documentation: str
    source_code: str
    source_code_url_scheme: str
    license: str
    license_text: str
    issue_tracker: str
    api_tests: List[str]
    exclude: List[str]
    uri: List[str]

@dataclass
class ProjectEvaluatorSettings:
    external_properties: Dict[str, str]
    env: Dict[str, str]
    allowed_modules: List[str]
    allowed_resources: List[str]
    no_cache: Optional[bool] = None
    module_path: List[str]
    module_cache_dir: str
    root_dir: str

@dataclass
class Project:
    project_file_uri: str
    package: Optional[ProjectPackage] = None
    evaluator_settings: Optional[ProjectEvaluatorSettings] = None
    tests: List[str]
    dependencies: ProjectDependencies

async def load_project(path: str) -> Project:
    ev = await new_evaluator(PreconfiguredOptions)
    return await load_project_from_evaluator(ev, path)

async def load_project_from_evaluator(ev: 'Evaluator', path: str) -> Project:
    return await ev.evaluate_output_value(FileSource(path))