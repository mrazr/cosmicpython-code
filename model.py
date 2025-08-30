from datetime import date, timedelta
from dataclasses import dataclass, field
from typing import NewType
import queue

OrderReference = NewType('OrderReference', str)

@dataclass(unsafe_hash=True)
class OrderLine:
    order_reference: OrderReference
    sku: str
    qty: int


@dataclass
class Batch:
    def __init__(self, reference: str, sku: str, qty: int, eta: date|None = None):
        self.reference = reference
        self.sku = sku
        self.qty = qty
        self.order_lines: set[OrderLine] = set()
        self.eta = eta

    def allocate(self, order_line: OrderLine) -> bool:
        if order_line.sku != self.sku:
            return False
        if order_line.qty > self.available_qty:
            return False
        if order_line in self.order_lines:
            return False
        self.order_lines.add(order_line)
        return True
    
    def deallocate(self, order_line: OrderLine) -> bool:
        if not self.can_deallocate(order_line):
            return False
        self.order_lines.remove(order_line)
        return True
    
    def can_allocate(self, order_line: OrderLine) -> bool:
        return order_line.sku == self.sku and order_line not in self.order_lines and order_line.qty <= self.available_qty

    def can_deallocate(self, order_line: OrderLine) -> bool:
        return order_line in self.order_lines
    
    @property
    def allocated_qty(self) -> int:
        return sum(line.qty for line in self.order_lines)

    @property
    def available_qty(self) -> int:
        return self.qty - self.allocated_qty
    
    def __hash__(self):
        return hash(self.reference)
    
    def __eq__(self, value) -> bool:
        if not isinstance(value, Batch):
            return False
        return value.reference == self.reference


class AllocationService:
    def __init__(self):
        self.available_stocks: dict[str, queue.PriorityQueue[Batch]] = dict()
        self.exhausted_stocks: dict[str, set[Batch]] = dict()
    
    def notify(self, batch: Batch):
        if batch.eta is not None:
            self.available_stocks.setdefault(batch.sku, queue.PriorityQueue()).put((1, batch.eta, batch))
        else:
            self.available_stocks.setdefault(batch.sku, queue.PriorityQueue()).put((0, None, batch))
    
    def put_order(self, order_line: OrderLine) -> bool:
        if order_line.sku not in self.available_stocks:
            return False
        if self.available_stocks.setdefault(order_line.sku, queue.PriorityQueue()).empty():
            return False
        _, _, earliest_batch = self.available_stocks[order_line.sku].get()
        success = earliest_batch.allocate(order_line)
        if success:
            if earliest_batch.available_qty == 0:
                self.exhausted_stocks.setdefault(earliest_batch.sku, set()).add(earliest_batch)
            else:
                self.notify(earliest_batch)
        return success