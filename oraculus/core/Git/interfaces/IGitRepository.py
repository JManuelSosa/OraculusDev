from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import List, Type
from oraculus.core.metrics import CommitData


from oraculus.core.git.parsers.ICommitParser import ICommitParser
from oraculus.core.git.parsers.ParserLocalSubprocess import ParserLocalSubprocess

class IGitRepository(ABC):

    @property
    @abstractmethod
    def es_origen_local(self)-> bool:
        pass

    @property
    @abstractmethod
    def commits(self) -> List[CommitData]:
        pass

    @property
    @abstractmethod
    def ruta_cache(self)->str|None:
        pass
