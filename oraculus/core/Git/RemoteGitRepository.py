# Python
import subprocess
from typing import List

# Interfaces 
from oraculus.core.git.interfaces.IBaseLocalRepository import IBaseLocalRepository
from oraculus.core.git.parsers.ICommitParser import ICommitParser
from oraculus.core.validators.IRepositoryUrl import IRepositoryUrl

# Utils
from oraculus.utils.config import preparar_directorio_cache
from oraculus.core.metrics import CommitData
from oraculus.utils.i18n import t

class RemoteGitRepository(IBaseLocalRepository):
    
    _commits:CommitData|None = None

    def __init__(self, repository_url:IRepositoryUrl, parser:ICommitParser, limit:int = 10):
        super().__init__(parser, limit)
        self.url_repository:IRepositoryUrl = repository_url
        self._preparar_repositorio()

    @property
    def es_origen_local(self)-> bool:
        return False

    @property
    def ruta_cache(self):
        return self._ruta_repo_cache

    @property
    def commits(self)-> List[CommitData]:
        if self._commits is None:
            self._commits = self._obtener_commits()

        return self._commits

    def _obtener_commits(self):        
        commits_crudos = super()._commits_desde_carpeta()
        list_commits:CommitData = self._parser.parse_to_commit_data_list(commits_crudos)

        return list_commits

    def _preparar_repositorio(self):
        carpeta_destino = self.url_repository.identificador
        self._ruta_repo_cache = preparar_directorio_cache(carpeta_destino)
        self._clonar_repositorio()

    def _clonar_repositorio(self):
        # Parámetros de clonado
        cmd = ["git", "clone", "--depth", str(self._limit), "--quiet", self.url_repository.url, self._ruta_repo_cache]
        mensaje_cmd = f"[Info] Clonando repositorio remoto {self.url_repository.identificador}"

        def manejar_resultado(result:subprocess.CompletedProcess):
            if result.returncode != 0:
                error_limpio = result.stderr.decode('utf-8', errors='ignore').strip()
                if self.url_repository.token:
                    error_limpio = error_limpio.replace(self.url_repository.token, '******')
                raise RuntimeError(f"Error al clonar el repositorio: {error_limpio}")

        super()._ejecutar_clonacion(cmd, mensaje_cmd, manejar_resultado)