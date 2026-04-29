"""Python interview prep — syntax reference and Block 1 examples."""

from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from functools import reduce
from itertools import combinations, combinations_with_replacement, permutations, product
from typing import Generic, Literal, NotRequired, Protocol, TypedDict, TypeVar
import asyncio
import weakref


# ---------------------------------------------------------------------------
# Lambdas
# ---------------------------------------------------------------------------
square = lambda x: x ** 2
add = lambda x, y: x + y

users = [{"name": "ana", "age": 30}, {"name": "bob", "age": 25}]
sorted_users = sorted(users, key=lambda u: u["age"])


# ---------------------------------------------------------------------------
# map / filter / reduce
# ---------------------------------------------------------------------------
nums = [1, 2, 3, 4]

squared_map = list(map(lambda x: x ** 2, nums))           # [1, 4, 9, 16]
squared_comp = [x ** 2 for x in nums]                     # idiomatic

evens_filter = list(filter(lambda x: x % 2 == 0, nums))   # [2, 4]
evens_comp = [x for x in nums if x % 2 == 0]              # idiomatic

total = reduce(lambda acc, x: acc + x, nums)              # 10
total_seed = reduce(lambda acc, x: acc + x, nums, 100)    # 110
total_pythonic = sum(nums)                                # prefer this


# ---------------------------------------------------------------------------
# Combinations: [1,2,3] -> [(1,2),(1,3),(2,3)]
# ---------------------------------------------------------------------------
lst = [1, 2, 3]

pairs_itertools = list(combinations(lst, 2))
pairs_indices = [(lst[i], lst[j]) for i in range(len(lst)) for j in range(i + 1, len(lst))]
pairs_enum = [(a, b) for i, a in enumerate(lst) for b in lst[i + 1:]]

# Related itertools tools
perms = list(permutations([1, 2, 3], 2))                       # order matters
prods = list(product([1, 2, 3], repeat=2))                     # cartesian, repeats
combs_rep = list(combinations_with_replacement([1, 2, 3], 2))  # no order, repeats


# ---------------------------------------------------------------------------
# async def vs sync, and offloading blocking work
# ---------------------------------------------------------------------------
async def fetch_value() -> int:
    await asyncio.sleep(0)   # async-native sleep, never time.sleep
    return 42


def blocking_io() -> str:
    # imagine requests.get(...) or a sync DB driver here
    return "done"


async def run_blocking_safely() -> str:
    return await asyncio.to_thread(blocking_io)


# ---------------------------------------------------------------------------
# __slots__ / dataclass / NamedTuple / Pydantic-style boundary model
# ---------------------------------------------------------------------------
class PointSlots:
    __slots__ = ("x", "y")
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y


@dataclass(slots=True, frozen=True)
class PointDC:
    x: float
    y: float


from typing import NamedTuple
class PointNT(NamedTuple):
    x: float
    y: float


# ---------------------------------------------------------------------------
# Generators and yield from
# ---------------------------------------------------------------------------
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


flat = list(flatten([1, [2, [3, 4], 5], 6]))   # [1,2,3,4,5,6]


# ---------------------------------------------------------------------------
# Context managers (sync + async)
# ---------------------------------------------------------------------------
class Resource:
    def __enter__(self):
        self.handle = "acquired"
        return self.handle
    def __exit__(self, exc_type, exc, tb):
        self.handle = None
        return False   # never swallow exceptions implicitly


@contextmanager
def resource():
    handle = "acquired"
    try:
        yield handle
    finally:
        handle = None


@asynccontextmanager
async def db_session():
    session = {"open": True}
    try:
        yield session
    finally:
        session["open"] = False


# ---------------------------------------------------------------------------
# weakref to avoid cycles
# ---------------------------------------------------------------------------
class Node:
    def __init__(self, parent=None):
        self._parent = weakref.ref(parent) if parent else None

    @property
    def parent(self):
        return self._parent() if self._parent else None


# ---------------------------------------------------------------------------
# Typing: Protocol, TypeVar/Generic, Literal, TypedDict
# ---------------------------------------------------------------------------
class SupportsClose(Protocol):
    def close(self) -> None: ...


def shutdown(x: SupportsClose) -> None:
    x.close()


T = TypeVar("T")


class Repository(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[int, T] = {}
    def get(self, id: int) -> T:
        return self._items[id]
    def add(self, id: int, item: T) -> None:
        self._items[id] = item


def set_mode(m: Literal["r", "w", "a"]) -> None:
    print(f"mode={m}")


class User(TypedDict):
    id: int
    name: str
    email: NotRequired[str]


# ---------------------------------------------------------------------------
# __init_subclass__ — lightweight registry without metaclass
# ---------------------------------------------------------------------------
class Plugin:
    registry: list[type] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.registry.append(cls)


class EmailPlugin(Plugin): ...
class SmsPlugin(Plugin): ...


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("squared:", squared_comp)
    print("evens:", evens_comp)
    print("sum:", total_pythonic)
    print("pairs:", pairs_itertools)
    print("perms:", perms)
    print("flat:", flat)
    print("plugins:", [c.__name__ for c in Plugin.registry])
    print("async fetch:", asyncio.run(fetch_value()))
    print("offloaded blocking:", asyncio.run(run_blocking_safely()))

    repo: Repository[str] = Repository()
    repo.add(1, "hello")
    print("repo.get(1):", repo.get(1))

    with resource() as r:
        print("resource:", r)
