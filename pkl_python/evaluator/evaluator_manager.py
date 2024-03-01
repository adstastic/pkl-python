from concurrent.futures import Future
from typing import Union, List

from .module_source import FileSource
from .project import load_project_from_evaluator
from ..types.project import Project
from ..types.evaluator_manager import EvaluatorManagerInterface
from .evaluator import EvaluatorImpl, Evaluator
from ..types.outgoing import CreateEvaluator, OutgoingMessage
import msgpack
from ..types import codes
from .evaluator_options import encoded_dependencies, EvaluatorOptions, with_project
from .preconfigured_options import PreconfiguredOptions
from subprocess import Popen, PIPE
from ..types.incoming import decode
from .decoder_exec import Decoder
import re
import os
import subprocess
from typing import List, Union, Tuple
from subprocess import Popen, PIPE
from asyncio import StreamReader

def new_evaluator_manager() -> EvaluatorManagerInterface:
    """
    Creates a new EvaluatorManager.
    """
    return new_evaluator_manager_with_command([])

def new_evaluator_manager_with_command(pkl_command: List[str]) -> EvaluatorManagerInterface:
    """
    Creates a new EvaluatorManager using the given pkl command.

    The first element in pklCmd is treated as the command to run.
    Any additional elements are treated as arguments to be passed to the process.
    pklCmd is treated as the base command that spawns Pkl.
    For example, the below snippet spawns the command /opt/bin/pkl.

    newEvaluatorManagerWithCommand(["/opt/bin/pkl"])
    """
    return EvaluatorManagerImpl(pkl_command)

semver_pattern = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?")
pkl_version_regex = re.compile(f"Pkl ({semver_pattern.pattern}).*")

class EvaluatorManagerImpl(EvaluatorManagerInterface):

    
    def __init__(self, pkl_command: list):
        self.pkl_command = pkl_command
        self.pending_evaluators = {}
        self.evaluators = []
        self.closed = False
        cmd, args = self.get_start_command()
        self.cmd = subprocess.Popen([cmd] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            self.decode(self.cmd.stdout)
        except Exception as e:
            print(e)
        self.cmd.wait()
        for future in self.pending_evaluators.values():
            future.set_exception(Exception("pkl command exited"))
        errors = []
        for ev in self.evaluators:
            try:
                ev.close()
            except Exception as e:
                errors.append(e)
        self.closed = True
        if errors:
            print("errors closing evaluators:", errors)

    def get_start_command(self):
        if self.pkl_command:
            return self.pkl_command[0], self.pkl_command[1:]
        pkl_exec_env = os.environ.get("PKL_EXEC", "")
        if pkl_exec_env:
            parts = pkl_exec_env.split(" ")
            return parts[0], parts[1:]
        return "pkl", []

    def handle_close(self):
        for _, reject in self.pending_evaluators.values():
            reject(Exception("pkl command exited"))
        errors = []
        for ev in self.evaluators.values():
            try:
                ev.close()
            except Exception as e:
                errors.append(e)
        self.closed = True
        if errors:
            print("errors closing evaluators:", errors)

    def get_command_and_arg_strings(self) -> Tuple[str, List[str]]:
        if self.pkl_command:
            return self.pkl_command[0], self.pkl_command[1:]
        pkl_exec_env = os.environ.get("PKL_EXEC", "")
        if pkl_exec_env:
            parts = pkl_exec_env.split(" ")
            return parts[0], parts[1:]
        return "pkl", []

    def send(self, out: 'OutgoingMessage'):
        self.cmd.stdin.write(pack_message(self.encoder, out))
        self.cmd.stdin.flush()

    def get_evaluator(self, evaluator_id: int) -> Union[EvaluatorImpl, None]:
        ev = self.evaluators.get(evaluator_id)
        if not ev:
            print("Received unknown evaluator id:", evaluator_id)
        return ev

    async def decode(self, stdout: StreamReader):
        stdout.pipe(self.stream_decoder)
        async for item in self.stream_decoder:
            decoded = decode(item)
            ev = self.get_evaluator(decoded.evaluator_id)
            if not ev:
                continue
            if decoded.code == codes.EvaluateResponse:
                ev.handle_evaluate_response(decoded)
            elif decoded.code == codes.EvaluateLog:
                ev.handle_log(decoded)
            elif decoded.code == codes.EvaluateRead:
                await ev.handle_read_resource(decoded)
            elif decoded.code == codes.EvaluateReadModule:
                await ev.handle_read_module(decoded)
            elif decoded.code == codes.ListResourcesRequest:
                await ev.handle_list_resources(decoded)
            elif decoded.code == codes.ListModulesRequest:
                await ev.handle_list_modules(decoded)
            elif decoded.code == codes.NewEvaluatorResponse:
                pending = self.pending_evaluators.get(str(decoded.request_id))
                if not pending:
                    print("warn: received a message for an unknown request id:", decoded.request_id)
                    return
                pending['resolve'](decoded)

    def get_start_command(self) -> Tuple[str, List[str]]:
        cmd, args = self.get_command_and_arg_strings()
        return cmd, [*args, "server"]

    def close(self):
        self.cmd.kill()

    def get_version(self) -> str:
        if self.version:
            return self.version
        cmd, args = self.get_command_and_arg_strings()
        result = subprocess.run([cmd, *args, "--version"], stdout=subprocess.PIPE)
        version = re.search(self.pkl_version_regex, result.stdout.decode())
        if not version or len(version.groups()) < 2:
            raise Exception(f"failed to get version information from Pkl. Ran '{' '.join(args)}', and got stdout \"{result.stdout.decode}\"")
        self.version = version.group(1)
        return self.version

    async def new_evaluator(self, opts: EvaluatorOptions) -> 'Evaluator':
        if self.closed:
            raise Exception("EvaluatorManager has been closed")

        create_evaluator = CreateEvaluator(
            request_id=0,  # TODO
            client_resource_readers=opts.resource_readers or [],
            client_module_readers=opts.module_readers or [],
            code=codes.NewEvaluator,
            **opts.__dict__,
        )

        future = Future()
        self.pending_evaluators[str(create_evaluator.request_id)] = future
        try:
            # Perform the operation...
            pass
        except Exception as e:
            future.set_exception(e)
        else:
            # Set the result of the future when the operation is done...
            pass
        finally:
            del self.pending_evaluators[str(create_evaluator.request_id)]
        return future

        if opts.project_dir:
            create_evaluator.project = {
                'projectFileUri': f"file://{opts.project_dir}/PklProject",
                'dependencies': encoded_dependencies(opts.declared_project_dependencies) if opts.declared_project_dependencies else None
            }
        
        self.send(create_evaluator)
        ev = EvaluatorImpl(response.evaluator_id, self)
        self.evaluators[response.evaluator_id] = ev
        
        self.decode(self.cmd.stdout).catch(print)
        self.cmd.on('close', self.handle_close)

        return ev

    async def new_project_evaluator(self, project_dir: str, opts: 'EvaluatorOptions') -> Evaluator:
        project_evaluator = await self.new_evaluator(PreconfiguredOptions)
        project = await load_project_from_evaluator(project_evaluator, f"{project_dir}/PklProject")

        return await self.new_evaluator({**with_project(project), **opts.__dict__})
    
def pack_message(packer: msgpack.Packer, msg: OutgoingMessage) -> bytearray:
  code, *rest = msg
  return packer.pack([code, rest])
    
