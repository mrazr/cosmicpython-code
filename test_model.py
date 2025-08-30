import time
from datetime import date, timedelta
import pytest

from model import Batch, OrderLine, AllocationService, OrderReference

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

def make_batch_and_line(sku: str, batch_qty: int, line_qty: int) -> tuple[Batch, OrderLine]:
    return Batch(f'batch_{time.time()}', sku, batch_qty), OrderLine(OrderReference('order001'), sku, line_qty)


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, line = make_batch_and_line('small-red-table', 20, 5)

    assert batch.can_allocate(line) is True


def test_can_allocate_if_available_greater_than_required():
    batch, line = make_batch_and_line('small-red-table', 10, 5)

    assert batch.can_allocate(line) is True


def test_cannot_allocate_if_available_smaller_than_required():
    batch, line = make_batch_and_line('small-red-table', 5, 9)
    
    assert batch.can_allocate(line) is False


def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line('small-red-table', 5, 5)

    assert batch.can_allocate(line) is True


def test_prefers_warehouse_batches_to_shipments():
    allocation = AllocationService()
    batch_wh = Batch('batch_warehouse', 'small-red', 5, None)
    batch_tomo = Batch('batch001', 'small-red', 10, tomorrow)
    batch_later = Batch('batch002', 'small-red', 5, later)

    allocation.notify(batch_later)
    allocation.notify(batch_tomo)
    allocation.notify(batch_wh)

    order_line = OrderLine(OrderReference('order002'), 'small-red', 3)

    allocation.put_order(order_line)

    assert batch_wh.available_qty == 2
    assert batch_tomo.available_qty == batch_tomo.qty
    assert batch_later.available_qty == batch_later.qty


def test_prefers_earlier_batches():
    allocation = AllocationService()
    batch_tomo = Batch('batch001', 'small-red', 10, tomorrow)
    batch_later = Batch('batch002', 'small-red', 5, later)

    allocation.notify(batch_tomo)
    allocation.notify(batch_later)

    order_line = OrderLine(OrderReference('order002'), 'small-red', 2)

    allocation.put_order(order_line)

    assert batch_tomo.available_qty == 8
    assert batch_later.available_qty == batch_later.qty

def test_allocates_same_line_only_once():
    batch, line = make_batch_and_line('small-red', 10, 2)

    batch.allocate(line)

    assert batch.can_allocate(line) is False

def test_batch_rejects_line_with_different_sku():
    batch = Batch('batch001', 'small-red', 10)
    order_line = OrderLine(OrderReference('order002'), 'small-blue', 2)

    assert batch.can_allocate(order_line) is False

def test_allocation_rejects_already_allocated_line():
    allocation = AllocationService()
    batch = Batch('batch002', 'small-red', 10)

    allocation.notify(batch)

    order_line = OrderLine(OrderReference('order002'), 'small-red', 2)

    allocation.put_order(order_line)

    assert allocation.put_order(order_line) == False

def test_allocation_fails_when_batches_are_exhausted():
    batch = Batch('batch001', 'small-red', 10)
    allocation = AllocationService()

    allocation.notify(batch)

    order_line1 = OrderLine(OrderReference('order002'), 'small-red', 10)

    assert allocation.put_order(order_line1) == True

    order_line2 = OrderLine(OrderReference('order002'), 'small-red', 2)

    assert allocation.put_order(order_line2) == False

def test_can_deallocate_only_allocated_lines():
    batch, line = make_batch_and_line('small-red', 10, 2)

    assert batch.can_deallocate(line) is False

    batch.allocate(line)

    assert batch.can_deallocate(line) is True