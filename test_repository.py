from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session
import pytest

import orm
import repository
import model

@pytest.fixture
def engine():
    return create_engine('sqlite:///')

@pytest.fixture
def session(engine):
    orm.mapper_registry.metadata.create_all(engine)
    return Session(engine)

def insert_batch(batch_ref: str, sku: str, qty: int, sess: Session):
    batch = model.Batch(batch_ref, sku, qty, None)
    sess.add(batch)
    sess.commit()


def insert_order_line(batch_ref: str, order_ref: str, sku: str, qty: int, sess: Session):
    batch_id = sess.scalar(select(model.Batch.id).where(model.Batch.reference == batch_ref))
    sess.execute(text('insert into order_lines (sku, qty, order_reference, batch_id) values (:sku, :qty, :order_ref, :batch_id)')
                 .bindparams(sku=sku, qty=qty, order_ref=order_ref, batch_id=batch_id))
    sess.commit()

def test_repository_can_save_a_batch(session):
    batch = model.Batch('batch1', 'small-red', 100, None)

    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute(text('select reference, sku, qty, eta from batches'))
    assert list(rows) == [('batch1', 'small-red', 100, None)]

def test_repository_can_retrieve_a_batch_with_allocations(session):
    insert_batch('batch1', 'small-red', 50, session)
    insert_order_line('batch1', 'order1', 'small-red', 5, session)

    repo = repository.SqlAlchemyRepository(session)
    batch = repo.get('batch1')
    expected = model.Batch('batch1', 'small-red', 50, None)

    assert batch == expected
    assert batch.order_lines == {model.OrderLine('order1', 'small-red', 5)}
    assert batch.sku == expected.sku
    assert batch.eta == expected.eta