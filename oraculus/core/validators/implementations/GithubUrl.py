# Python
import re

# Interfaces
from oraculus.core.validators.IRepositoryUrl import IRepositoryUrl

# Enums
from oraculus.core.enums.RemotePlatform import RemotePlatform

class GithubUrl(IRepositoryUrl):
    _plataforma:RemotePlatform = RemotePlatform.GITHUB
    _repo_input:str 
    _match:re.Match
    _url:str
    _repo_identificador:str

    _valid_url_regex = re.compile(
        r"^(?:https://)?github\.com/"
        r"(?P<owner>[a-zA-Z0-9][a-zA-Z0-9-]{0,38})/"
        r"(?P<repository>[a-zA-Z0-9_.-]{1,100})"
        r"(?:\.git)?$"
    )

    _valid_identificador_regex = re.compile(
        r"^(?P<owner>[a-zA-Z0-9][a-zA-Z0-9-]{0,38})/(?P<repository>[a-zA-Z0-9_.-]{1,100})$"
    )

    def __init__(self, raw_repo:str, token:str|None):
        super().__init__(raw_repo=raw_repo, token=token)
        self._match = self._validar(raw_repo)
        self._repo_identificador = self._obtener_info_identificador()
        self._url = self._obtener_url()

    @property
    def url(self)-> str:
        return self._url

    @property
    def identificador(self)-> str:
        return self._repo_identificador

    @property
    def plataforma(self)-> RemotePlatform:
        return self._plataforma

    @property
    def token(self):
        return super().token

    @classmethod
    def es_formato_valido(cls, raw_repo):
        match = cls._valid_url_regex.match(raw_repo)
        return bool(match)

    def _validar(self, repo:str)-> re.Match:
        match = self._valid_url_regex.match(repo) or self._valid_identificador_regex.match(repo)

        #TODO: Colocar mensaje de error correcto
        if not match: raise ValueError("[Error de validacion] El repositorio ingresado no es un repositorio de Github válido")

        return match

    def _obtener_info_identificador(self)-> str:
        match = self._match
        owner:str = match['owner'].strip()
        repository:str = match["repository"]
        repository = repository.removesuffix('.git').strip()
        
        return f"{owner}/{repository}"

    def _obtener_url(self)->str:
        url_token:str = ""
        at:str = ""

        if self._token:
            url_token = self._token
            at = "@"
        
        identificador:str = self._obtener_info_identificador()

        return f"https://{url_token}{at}github.com/{identificador}.git"