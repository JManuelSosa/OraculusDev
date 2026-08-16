from abc import ABC, abstractmethod
from oraculus.core.enums.RemotePlatform import RemotePlatform

class IRepositoryUrl(ABC):

    _token:str|None

    def __init__(self, raw_repo:str, token:str|None):
        self._token = token

    @classmethod
    def es_formato_valido(cls, raw_repo:str)->bool:
        pass

    @property
    @abstractmethod
    def plataforma(self)->RemotePlatform:
        pass
    
    @property
    @abstractmethod
    def url(self)-> str:
        pass

    @property
    @abstractmethod
    def identificador(self)-> str:
        pass

    @property
    @abstractmethod
    def token(self)-> str|None:
        return self._token
