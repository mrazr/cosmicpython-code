from sqlalchemy import Table, Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship, registry

import model

mapper_registry = registry()

batches = Table(
    'batches',
    mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("eta", Date, nullable=True),
)

order_lines = Table(
    "order_lines",
    mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("order_reference", String(255)),
    Column("batch_id", ForeignKey('batches.id'))
)

mapper_registry.map_imperatively(model.OrderLine, order_lines)
mapper_registry.map_imperatively(model.Batch, batches,
                                 properties={
                                     "order_lines": relationship(model.OrderLine, collection_class=set)
                                 })
