import abc

from sqlalchemy import select
from sqlalchemy.orm import Session

import model
import orm

class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError
    
    @abc.abstractmethod
    def get(self, reference) -> model.Batch | None:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, batch: model.Batch):
        self.session.add(batch)

    def get(self, reference: str) -> model.Batch | None:
        return self.session.scalar(select(model.Batch).where(model.Batch.reference == reference))


class FakeRepository(AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)
    
    def add(self, batch):
        self._batches.add(batch)
    
    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)
    
    def list(self):
        return list(self._batches)