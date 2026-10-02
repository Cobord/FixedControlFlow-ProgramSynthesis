# FixedControlFlow-ProgramSynthesis

Program synthesis where the control flow is fixed up front and only the contents of each basic block are synthesized.

The idea:

1. Describe the program's shape as a control flow graph (CFG): basic blocks connected by (optionally labelled) edges, with an entry block and one or more exit blocks.
2. Attach pre- and post-conditions to each basic block.
3. For every block, build a prompt from its pre/post conditions and ask an LLM for a sequence of instructions that satisfies them.
4. Since the control flow is fixed, each block can be filled independently and concurrently.

## Status

Early work in progress.

- The CFG data structure and graph queries work. See `scripts/run_cfg.py`.
- `PrePostConditions` is a placeholder. `create_prompt_for_block_filling` raises `NotImplementedError`.
- `BasicBlock.reset_instructions_according_to_conditions` builds the prompt but does not yet call an LLM. It raises `NotImplementedError` for any block that has conditions.

## Layout

```
src/programsynthesis/
  cfg.py                 BasicBlock and ControlFlowGraph
  prepost_conditions.py  PrePostConditions (pre/post conditions -> prompt)
  llm_types.py           Shared LLM types (Prompt)
scripts/run_cfg.py       Examples of building and querying CFGs by hand
tests/                   pytest tests
main.py                  Entry point (placeholder)
before_commit.sh         Format, run main, tests and scripts, then clean caches
```

## Core types

### `BasicBlock[BlockId, Instruction]`

A block ID, a list of instructions, and optional `PrePostConditions`. Both type parameters are generic, so instructions can be strings, tuples, AST nodes, or anything else.

- `add_instruction`, `reset_instructions`: edit the instructions (`reset_instructions` returns the old list).
- `set_conditions`, `modify_conditions`: replace or mutate the pre/post conditions.
- `async reset_instructions_according_to_conditions()`: regenerate the block's instructions from its conditions (not implemented yet).

### `ControlFlowGraph[BlockId, Instruction]`

A wrapper around a `networkx.DiGraph` that keeps a `BasicBlock` for each node.

The construction methods are underscore-prefixed (`_add_block`, `_add_edge`, `_remove_block`, `_remove_edge`, `_set_entry_block`, `_mark_exit_block`) because the control flow is meant to be fixed once it is built. The first block added becomes the entry block by default. Keyword arguments passed to `_add_edge` are stored as edge attributes, for example `condition=True`.

Queries:

| Method | Returns |
| --- | --- |
| `get_block`, `get_successors`, `get_predecessors` | Block lookup and neighbours |
| `topological_sort`, `is_dag` | Ordering and an acyclicity check |
| `find_dominators` | Immediate dominator of each block, from the entry block |
| `find_loops`, `strongly_connected_components` | Cycle structure |
| `is_reachable`, `shortest_path`, `get_entry_exit_paths` | Path queries |
| `visualize` | Plain-text dump |
| `to_dot` | Graphviz DOT string, with the entry block in green and exit blocks in red |

`async reset_instructions_according_to_conditions()` fills every block concurrently using an `asyncio.TaskGroup`.

## Example

```python
from src.programsynthesis import ControlFlowGraph

cfg: ControlFlowGraph[str, str] = ControlFlowGraph()
cfg._add_block("B1", ["x = 10", "y = 20"])
cfg._add_block("B2", ["condition = x > 5"])
cfg._add_block("B3", ["z = x + y"])
cfg._add_block("B4", ["z = x - y"])
cfg._add_block("B5", ["print(z)"])

cfg._add_edge("B1", "B2")
cfg._add_edge("B2", "B3", condition=True)
cfg._add_edge("B2", "B4", condition=False)
cfg._add_edge("B3", "B5")
cfg._add_edge("B4", "B5")
cfg._mark_exit_block("B5")

print(cfg.visualize())
print(cfg.find_dominators())       # {'B2': 'B1', 'B3': 'B2', 'B4': 'B2', 'B5': 'B2'}
print(cfg.get_entry_exit_paths())  # [['B1', 'B2', 'B3', 'B5'], ['B1', 'B2', 'B4', 'B5']]
```

## Setup

Requires Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run main.py
uv run scripts/run_cfg.py
uv run pytest tests/*.py
```

`to_dot` uses `networkx.nx_pydot`, which needs `pydot`. `pydot` is in the `dev` dependency group, which `uv sync` installs by default.

Before committing, run:

```bash
bash before_commit.sh
```

This formats the code with black, runs `main.py`, the tests and the scripts, and removes cache directories.
