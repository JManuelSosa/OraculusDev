import re
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Any
#Utilidades
from oraculus.utils.config import preparar_directorio_cache
from oraculus.core.metrics import CommitData
from oraculus.utils.i18n import t
# Interfaces
from oraculus.core.git.interfaces.IGitRepository import IGitRepository
from oraculus.core.git.parsers.ICommitParser import ICommitParser
from oraculus.core.validators.IRepositoryUrl import IRepositoryUrl

from oraculus.core.git.parsers.ParserLocalSubprocess import ParserLocalSubprocess
from oraculus.core.git.parsers.ParserGithubApi import ParserGithubApi

class GithubRepository(IGitRepository):

    msg_error_status:dict[int, Callable[[Any, requests.Response], str]] = {
        401: lambda self, r: "Error 401: El token de Github proporcionado no es válido o ha expirado.",
        404: lambda self, r: f"Error 404: No se encontró el repositorio '{self.usuario}/{self.repositorio}'. Verifica que el nombre sea correcto y que el repositorio sea público (o que tu token tenga acceso si es privado).",
        403: lambda self, r: (
            "Error 403: Se ha alcanzado el límite de tasa (rate limit) de la API de GitHub. Intenta de nuevo más tarde o configura un GITHUB_TOKEN válido." 
            if r.headers.get("X-RateLimit-Remaining") == "0"
            else "Error 403: Acceso prohibido al repositorio."
        )
    }

    API_COMMIT_LIMIT = 5
    _commits:List[CommitData]|None = None

    def __init__(self, url_repository:IRepositoryUrl, parser:ICommitParser):
        self.url_repository:IRepositoryUrl = url_repository
        self.token:str|None = self.url_repository.token
        self.identificador:str = self.url_repository.identificador
        self.parser:ICommitParser = parser

    @property
    def es_origen_local(self):
        return False

    @property
    def ruta_cache(self):
        None

    @property
    def commits(self)-> List[CommitData]:

        if self._commits is None:
            commits_crudos = self._obtener_commits()
            self._commits = self.parser.parse_to_commit_data_list(commits_crudos)

        return self._commits


    def _obtener_commits(self) -> List[dict[str, Any]]:
        lista_shas:List[str] = self._hacer_peticion_inicial_de_commits()
        lista_detalles_shas:List[dict[str, Any]] = self._obtener_detalles_lista_sha(lista_shas)

        return lista_detalles_shas


    def _hacer_peticion_inicial_de_commits(self)-> List[str]:
        url:str = f"https://api.github.com/repos/{self.url_repository.identificador}/commits"
        headers:dict[str, str] = self._obtener_headers_request_api()

        try:
            response = requests.get(url, headers=headers, params={"per_page": self.API_COMMIT_LIMIT}, timeout=10)
        except requests.RequestException as e:
            raise RuntimeError(f"Error de conexión al conectar con Github: {e}")

        if response.status_code != 200:
            msg_error:str = f"Error al obtener commits de GitHub (Código {response.status_code}): {response.text}"

            if response.status_code in self.msg_error_status:
                msg_error = self.msg_error_status[response.status_code](self, response)

            raise RuntimeError(msg_error)

        commits_json = response.json()

        if not commits_json: return

        lista_commits:List[str] = []

        for commit in commits_json:
            sha:str = commit['sha']
            lista_commits.append(sha)

        return lista_commits

    def _obtener_detalles_lista_sha(self, shas:List[str])-> List[dict[str, Any]]:
        if not shas:
            return []

        headers:dict[str, str] = self._obtener_headers()
        workers:int = min(len(shas), 10)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            resultados = executor.map(lambda sha: self._hacer_peticion_detalle_sha(sha, headers=headers), shas)

        lista_detalles_commits:List[dict[str, Any]] = []

        for detalle_commit in resultados:
            if detalle_commit is not None:
                lista_detalles_commits.append(detalle_commit)

        return lista_detalles_commits
    
    def _hacer_peticion_detalle_sha(self, sha:str, headers):
        url:str = f"https://api.github.com/repos/{self.url_repository.identificador}/commits/{sha}"

        SHORT_SHA_LENGTH = 7

        sha_corto = sha[:SHORT_SHA_LENGTH]

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"[Advertencia] No se pudieron obtener detalles para el commit {sha_corto}. Codigo: {response.status_code}")
                return None

            return response.json()
        except requests.RequestException as error:
            print(f"[Advertencia] Error de conexión al obtener detalles para el commit {sha_corto}: {error}")
            return None

    def _obtener_headers(self)-> dict[str, str]:
        headers:dict[str, str] = { "Accept": "application/vnd.github.v3+json" }

        if not self.token:
            print("[Advertencia] GITHUB_TOKEN no esta configurado en el archivo .env. Podrías experimentar límites de tasa (Rate Limiting).")
        else:
            headers["Authorization"] = f"token {self.url_repository.token}"

        return headers