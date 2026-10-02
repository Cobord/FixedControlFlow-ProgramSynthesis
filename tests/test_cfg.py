"""
Testing control flow graph manipulation
"""

import asyncio

import pytest

from src.programsynthesis import BasicBlock, ControlFlowGraph, PrePostConditions


def diamond() -> ControlFlowGraph:
    """
    B1 -> B2 -> {B3, B4} -> B5
    """
    cfg = ControlFlowGraph()
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
    return cfg


# pylint:disable=protected-access


def test_basic_block_instructions():
    """
    adding and resetting instructions
    """
    block = BasicBlock("B", ["a = 1"])
    block.add_instruction("b = 2")
    assert block.instructions == ["a = 1", "b = 2"]
    old = block.reset_instructions(["c = 3"])
    assert old == ["a = 1", "b = 2"]
    assert block.instructions == ["c = 3"]


def test_basic_block_conditions_and_description():
    """
    conditions can be set and modified, description belongs to the block
    """
    block = BasicBlock("B", description="sum x and y")
    assert block.prepostconditions is None
    assert block.description == "sum x and y"

    # no conditions so nothing to modify
    block.modify_conditions(lambda c: c.add_precondition("x > 5"))
    assert block.prepostconditions is None

    assert block.set_conditions(PrePostConditions.empty()) is None
    block.modify_conditions(lambda c: c.add_precondition("x > 5"))
    assert block.prepostconditions and block.prepostconditions.preconditions == [
        "x > 5"
    ]

    block.description = "subtract y from x"
    assert block.description == "subtract y from x"


def test_basic_block_equality():
    """
    blocks are identified by their id only
    """
    assert BasicBlock("B", ["a = 1"]) == BasicBlock("B", ["b = 2"])
    assert BasicBlock("B") != BasicBlock("C")
    assert len({BasicBlock("B"), BasicBlock("B")}) == 1


def test_construction():
    """
    entry, exits, block count and errors on bad ids
    """
    cfg = diamond()
    assert cfg.entry_block == "B1"
    assert cfg.exit_blocks == {"B5"}
    assert cfg.num_blocks == 5
    block = cfg.get_block("B3")
    assert block and block.instructions == ["z = x + y"]
    assert cfg.get_block("missing") is None

    with pytest.raises(ValueError):
        cfg._add_block("B1")
    with pytest.raises(ValueError):
        cfg._add_edge("B1", "missing")
    with pytest.raises(ValueError):
        cfg._mark_exit_block("missing")
    with pytest.raises(ValueError):
        cfg._set_entry_block("missing")


def test_add_block_with_conditions_and_description():
    """
    _add_block passes conditions and description through to the block
    """
    cfg = ControlFlowGraph()
    conditions = PrePostConditions(postconditions=["x == 10"])
    block = cfg._add_block("B1", [], conditions, "set x")
    assert block.prepostconditions is conditions
    assert block.description == "set x"


def test_remove():
    """
    removing edges and blocks
    """
    cfg = diamond()
    cfg._remove_edge("B2", "B4")
    assert cfg.get_successors("B2") == ["B3"]
    # removing a missing edge is a no op
    cfg._remove_edge("B2", "B4")

    cfg._remove_block("B5")
    assert cfg.num_blocks == 4
    assert cfg.exit_blocks == set()
    cfg._remove_block("B1")
    assert cfg.entry_block is None
    with pytest.raises(ValueError):
        cfg._remove_block("B1")


def test_neighbours():
    """
    successors and predecessors
    """
    cfg = diamond()
    assert sorted(cfg.get_successors("B2")) == ["B3", "B4"]
    assert sorted(cfg.get_predecessors("B5")) == ["B3", "B4"]
    assert cfg.get_predecessors("B1") == []


def test_dag_queries():
    """
    topological sort, dominators, loops and components on an acyclic graph
    """
    cfg = diamond()
    assert cfg.is_dag()
    order = cfg.topological_sort()
    assert order[0] == "B1" and order[-1] == "B5"
    assert cfg.find_dominators() == {"B2": "B1", "B3": "B2", "B4": "B2", "B5": "B2"}
    assert not cfg.find_loops()
    assert len(cfg.strongly_connected_components()) == 5


def test_loop_queries():
    """
    adding a back edge makes a loop
    """
    cfg = diamond()
    cfg._add_edge("B3", "B2")
    assert not cfg.is_dag()
    with pytest.raises(ValueError):
        cfg.topological_sort()
    assert sorted(map(sorted, cfg.find_loops())) == [["B2", "B3"]]
    assert {"B2", "B3"} in cfg.strongly_connected_components()


def test_empty_graph_dominators():
    """
    no entry block means no dominators
    """
    assert not ControlFlowGraph().find_dominators()


def test_paths():
    """
    reachability, shortest paths and entry to exit paths
    """
    cfg = diamond()
    assert cfg.is_reachable("B1", "B5")
    assert not cfg.is_reachable("B5", "B1")
    assert cfg.shortest_path("B1", "B3") == ["B1", "B2", "B3"]
    assert cfg.shortest_path("B5", "B1") is None
    assert sorted(cfg.get_entry_exit_paths()) == [
        ["B1", "B2", "B3", "B5"],
        ["B1", "B2", "B4", "B5"],
    ]

    with pytest.raises(ValueError):
        ControlFlowGraph().get_entry_exit_paths()


def test_visualize():
    """
    text representation mentions every block
    """
    text = diamond().visualize()
    assert "Entry: B1" in text
    for block_id in ["B1", "B2", "B3", "B4", "B5"]:
        assert f"Block {block_id}:" in text


def test_to_dot():
    """
    DOT export has every block and edge
    """
    dot = diamond().to_dot()
    assert "lightgreen" in dot
    assert "lightcoral" in dot
    for edge in ["B1 -> B2", "B2 -> B3", "B2 -> B4", "B3 -> B5", "B4 -> B5"]:
        assert edge in dot


def test_reset_instructions_without_conditions():
    """
    blocks without conditions are left alone
    """
    cfg = diamond()
    asyncio.run(cfg.reset_instructions_according_to_conditions())
    block = cfg.get_block("B3")
    assert block and block.instructions == ["z = x + y"]


def test_reset_instructions_with_conditions_not_implemented():
    """
    the LLM call is not implemented yet
    """
    cfg = diamond()
    block = cfg.get_block("B3")
    assert block
    block.set_conditions(PrePostConditions(postconditions=["z > 0"]))
    with pytest.raises(ExceptionGroup) as exc_info:
        asyncio.run(cfg.reset_instructions_according_to_conditions())
    assert exc_info.group_contains(NotImplementedError)
