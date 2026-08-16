import os

# Interfaces
from oraculus.core.git.interfaces.IGitRepository import IGitRepository
from oraculus.core.validators.IRepositoryUrl import IRepositoryUrl
from oraculus.core.git.parsers.ICommitParser import ICommitParser

# Implementaciones
from oraculus.core.git.LocalGitRepository import LocalGitRepository
from oraculus.core.git.RemoteGitRepository import RemoteGitRepository
from oraculus.core.git.GithubRepository import GithubRepository
from oraculus.core.validators.implementations import GithubUrl

# Parsers
from oraculus.core.git.parsers.ParserLocalSubprocess import ParserLocalSubprocess
from oraculus.core.git.parsers.ParserGithubApi import ParserGithubApi

# Enums
from oraculus.core.enums.RemotePlatform import RemotePlatform

# Utilidades
from oraculus.utils.i18n import t

class RepositoryFactory:

    _plataformas_soportadas = {
        RemotePlatform.GITHUB: { 
            "validator": GithubUrl,
            "repository": GithubRepository,
            "parser": ParserGithubApi
        }
    }

    @classmethod
    def crear(cls, raw_repo:str, limit:int = 10, token:str|None = None, plataforma:RemotePlatform|None = None)-> IGitRepository:

        parser:ICommitParser = ParserLocalSubprocess() # Parser inicial
        remote_repository:IGitRepository|None = None
        url_obj:IRepositoryUrl|None = None

        if os.path.exists(raw_repo):
            return LocalGitRepository(raw_repo, parser, limit)

        if plataforma:
            validador_seleccionado = cls._plataformas_soportadas[plataforma]['validator']
            url_obj = validador_seleccionado(raw_repo, token)
        else:
            url_obj = cls._encontrar_plataforma(raw_repo, token)

        try:
            remote_repository = RemoteGitRepository(url_obj, parser, limit)
        except RuntimeError as error_clone:
            print(t('cli', 'info_clone_api_fallback').format(error=error_clone))
            plataforma_seleccionada = url_obj.plataforma
            parser_adecuado = cls._plataformas_soportadas[plataforma_seleccionada]["parser"]
            repositorio:IGitRepository = cls._plataformas_soportadas[plataforma_seleccionada]["repository"]

            remote_repository = repositorio(url_obj, parser_adecuado())

        return remote_repository

    @classmethod
    def _encontrar_plataforma(cls, raw_repo:str, token:str|None)-> IRepositoryUrl:
        validator_encontrado:IRepositoryUrl|None = None

        for plataforma in cls._plataformas_soportadas:
            validador_actual = cls._plataformas_soportadas[plataforma]['validator']
            es_entrada_valida:bool = validador_actual.es_formato_valido(raw_repo)

            if es_entrada_valida:
                validator_encontrado = validador_actual
                break

        if validator_encontrado is None:
            raise ValueError("El repositorio ingresado no es de ninguna plataforma de repositorios soportada por el sistema")

        return validator_encontrado(raw_repo, token)