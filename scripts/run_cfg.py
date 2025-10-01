"""
By hand testing control flow graph manipulation
"""

from src.programsynthesis import ControlFlowGraph


# pylint:disable=protected-access
def main1():
    """Using string block IDs and string instructions"""
    cfg: ControlFlowGraph[str, str] = ControlFlowGraph()

    # Create blocks
    cfg._add_block("B1", ["x = 10", "y = 20"])
    cfg._add_block("B2", ["condition = x > 5"])
    cfg._add_block("B3", ["z = x + y"])
    cfg._add_block("B4", ["z = x - y"])
    cfg._add_block("B5", [])
    cfg._add_block("B6", ["print(z)"])

    # Create edges
    cfg._add_edge("B1", "B2")
    cfg._add_edge("B2", "B3", condition=True)
    cfg._add_edge("B2", "B4", condition=False)
    cfg._add_edge("B3", "B5")
    cfg._add_edge("B5", "B6")
    cfg._add_edge("B4", "B6")

    # Mark exit block
    cfg._mark_exit_block("B6")

    # Print visualization
    print(cfg.visualize())
    print("\n" + "=" * 50 + "\n")

    print("Is DAG:", cfg.is_dag())

    # Dominators
    print("\nImmediate Dominators:")
    dominators = cfg.find_dominators()
    for block_id, dom in sorted(dominators.items()):
        print(f"  {block_id}: {dom}")

    # Paths
    print("\nAll paths from entry to exit:")
    for i, path in enumerate(cfg.get_entry_exit_paths(), 1):
        print(f"  Path {i}: {' -> '.join(path)}")

    # Check reachability
    print(f"\nB5 reachable from B1: {cfg.is_reachable('B1', 'B5')}")
    print(f"Shortest path B1 to B5: {cfg.shortest_path('B1', 'B5')}")

    # Accessing properties
    print(f"\nEntry block: {cfg.entry_block}")
    print(f"Number of blocks: {cfg.num_blocks}")
    print(f"Exit blocks: {cfg.exit_blocks}")


# pylint:disable=protected-access
def main2():
    """Example with integer block IDs and custom instruction objects"""
    print("\n" + "=" * 50)
    print("Example with integer IDs and tuples as instructions:\n")

    cfg2: ControlFlowGraph[int, tuple] = ControlFlowGraph()
    cfg2._add_block(1, [("LOAD", "x"), ("LOAD", "y")])
    cfg2._add_block(2, [("CMP", "x", 5)])
    cfg2._add_block(3, [("ADD", "x", "y")])
    cfg2._add_block(4, [])
    cfg2._add_block(5, [])
    cfg2._add_edge(1, 2, success=True)
    cfg2._add_edge(1, 5, success=False)
    cfg2._add_edge(2, 3, zf=1)
    cfg2._add_edge(2, 4, zf=0)
    cfg2._add_edge(3, 4)
    cfg2._mark_exit_block(4)
    cfg2._mark_exit_block(5)

    print(f"CFG2: {cfg2}")
    print(f"CFG2: {cfg2.visualize()}")


if __name__ == "__main__":
    main1()
    main2()
