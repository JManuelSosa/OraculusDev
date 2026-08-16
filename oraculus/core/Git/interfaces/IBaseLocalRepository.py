# Interfaces
from oraculus.core.git.interfaces.IGitRepository import IGitRepository
from oraculus.core.git.parsers.ICommitParser import ICommitParser

# Python
from typing import List, Callable
import subprocess

# Tipos
from oraculus.core.metrics import CommitData

class IBaseLocalRepository(IGitRepository):

    def __init__(self, parser:ICommitParser, limit:int = 10):
        self._ruta_repo_cache:str | None = None
        self._limit = limit
        self._parser:ICommitParser = parser

    @property
    def es_origen_local(self)-> bool:
        pass

    @property
    def commits(self)-> List[CommitData]:
        pass

    @property
    def ruta_cache(self)-> str|None:
        pass

    def _obtener_commits(self) -> List[CommitData]:
        pass
    
    def _preparar_repositorio(self):
        pass

    def _clonar_repositorio(self) -> None:
        pass


    def _ejecutar_clonacion(self, cmd:list[str], mensaje_inicial:str, callback_resultado:Callable[[subprocess.CompletedProcess], None]|None = None) -> None:
        print(mensaje_inicial)
        try:
            result = subprocess.run(cmd, capture_output=True, check=False)
            if callable(callback_resultado): callback_resultado(result)

        except FileNotFoundError:
            raise RuntimeError("No se encontró el comando 'git' en el sistema. Asegurarse de tener Git instalado y en tu PATH")

    def _commits_desde_carpeta(self) -> str:
        cmd = ["git", "-c", "safe.directory=*", "log", f"-n", str(self._limit), "--numstat", "--pretty=format:COMMIT:%h|%s"]

        try:
            result = subprocess.run(cmd, cwd=self._ruta_repo_cache, capture_output=True, check=False)
        except FileNotFoundError:
            #TODO: Cambiar por implementación multilenguaje
            raise RuntimeError("No se encontró el comando 'git' en el sistema. Asegurese de tener Git instalado y configurado en el PATH")

        output = result.stdout.decode("utf-8", errors="ignore")
        salida_error = result.stderr.decode("utf-8", errors="ignore")

        if result.returncode != 0:
            raise RuntimeError(f"Error de Git al obtener los commits: {salida_error.strip()}")

        if not output.strip():
            return ""

        return output