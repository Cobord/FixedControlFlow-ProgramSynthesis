"""
Manipulating Control Flow Graph
"""

from typing import Callable, List, Set, Dict, Optional, Generic, TypeVar, Any
import networkx as nx

from .prepost_conditions import PrePostConditions

BlockId = TypeVar("BlockId")
Instruction = TypeVar("Instruction")


class BasicBlock(Generic[BlockId, Instruction]):
    """Represents a basic block in a control flow graph."""

    def __init__(
        self,
        block_id: BlockId,
        instructions: Optional[List[Instruction]] = None,
        prepostconditions: Optional[PrePostConditions] = None,
    ) -> None:
        self.__id: BlockId = block_id
        self.__instructions: List[Instruction] = instructions or []
        self.__prepostconditions: Optional[PrePostConditions] = prepostconditions

    @property
    def id(self) -> BlockId:
        """Get the block ID."""
        return self.__id

    @property
    def instructions(self) -> List[Instruction]:
        """Get the list of instructions."""
        return self.__instructions

    @property
    def prepostconditions(self) -> Optional[PrePostConditions]:
        """Get the pre and post conditions."""
        return self.__prepostconditions

    def add_instruction(self, instruction: Instruction) -> None:
        """Add an instruction to the basic block."""
        self.__instructions.append(instruction)

    def reset_instructions(
        self, new_instructions: List[Instruction]
    ) -> List[Instruction]:
        """Replace the list of instructions returning the previous contents."""
        self.__instructions, new_instructions = new_instructions, self.__instructions
        return new_instructions

    def modify_conditions(self, do_on: Callable[[PrePostConditions], None]):
        """Apply a mutating function to the pre/post conditions if they are present."""
        if self.__prepostconditions:
            do_on(self.__prepostconditions)

    def set_conditions(
        self, new_conditions: PrePostConditions
    ) -> Optional[PrePostConditions]:
        """Replace the pre/post conditions returning the previous contents."""
        self.__prepostconditions, new_conditions = (
            new_conditions,
            self.__prepostconditions,
        )
        return new_conditions

    async def reset_instructions_according_to_conditions(self):
        """
        Use the pre and post conditions to make a prompt.
        Use that prompt to get a new set of instructions for this block.
        """
        if not self.__prepostconditions:
            return
        _prompt = self.__prepostconditions.create_prompt_for_block_filling()
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"BasicBlock({self.__id}, {len(self.__instructions)} instructions)"

    def __str__(self) -> str:
        return f"Block {self.__id}:\n  " + "\n  ".join(
            str(instr) for instr in self.__instructions
        )

    def __hash__(self) -> int:
        return hash(self.__id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BasicBlock) and self.__id == other.id


class ControlFlowGraph(Generic[BlockId, Instruction]):
    """Class to manipulate control flow graphs using NetworkX."""

    def __init__(self) -> None:
        self.__graph: nx.DiGraph = nx.DiGraph()
        self.__blocks: Dict[BlockId, BasicBlock[BlockId, Instruction]] = {}
        self.__entry_block: Optional[BlockId] = None
        self.__exit_blocks: Set[BlockId] = set()

    @property
    def entry_block(self) -> Optional[BlockId]:
        """Get the entry block ID."""
        return self.__entry_block

    @property
    def exit_blocks(self) -> Set[BlockId]:
        """Get the set of exit block IDs."""
        return self.__exit_blocks

    @property
    def num_blocks(self) -> int:
        """The number of blocks."""
        return len(self.__blocks)

    def _add_block(
        self,
        block_id: BlockId,
        instructions: Optional[List[Instruction]] = None,
        prepost_conditions: Optional[PrePostConditions] = None,
    ) -> BasicBlock[BlockId, Instruction]:
        """Add a basic block to the CFG."""
        if block_id in self.__blocks:
            raise ValueError(f"Block {block_id} already exists")

        block = BasicBlock[BlockId, Instruction](
            block_id, instructions, prepost_conditions
        )
        self.__blocks[block_id] = block
        self.__graph.add_node(block_id)

        if self.__entry_block is None:
            self.__entry_block = block_id

        return block

    def get_block(
        self, block_id: BlockId
    ) -> Optional[BasicBlock[BlockId, Instruction]]:
        """Retrieve a basic block by ID."""
        return self.__blocks.get(block_id, None)

    def _add_edge(
        self, from_block_id: BlockId, to_block_id: BlockId, **attrs: Any
    ) -> None:
        """Add a control flow edge between two blocks."""
        if from_block_id not in self.__blocks or to_block_id not in self.__blocks:
            raise ValueError("One or both blocks do not exist")

        self.__graph.add_edge(from_block_id, to_block_id, **attrs)

    def _remove_edge(self, from_block_id: BlockId, to_block_id: BlockId) -> None:
        """Remove a control flow edge between two blocks."""
        if self.__graph.has_edge(from_block_id, to_block_id):
            self.__graph.remove_edge(from_block_id, to_block_id)

    def _remove_block(self, block_id: BlockId) -> None:
        """Remove a basic block from the CFG."""
        if block_id not in self.__blocks:
            raise ValueError(f"Block {block_id} does not exist")

        self.__graph.remove_node(block_id)
        del self.__blocks[block_id]

        if self.__entry_block == block_id:
            self.__entry_block = None

        self.__exit_blocks.discard(block_id)

    def _set_entry_block(self, block_id: BlockId) -> None:
        """Set the entry block of the CFG."""
        if block_id not in self.__blocks:
            raise ValueError(f"Block {block_id} does not exist")
        self.__entry_block = block_id

    def _mark_exit_block(self, block_id: BlockId) -> None:
        """Mark a block as an exit block."""
        if block_id not in self.__blocks:
            raise ValueError(f"Block {block_id} does not exist")
        self.__exit_blocks.add(block_id)

    def get_successors(self, block_id: BlockId) -> List[BlockId]:
        """Get successor blocks of a given block."""
        return list(self.__graph.successors(block_id))

    def get_predecessors(self, block_id: BlockId) -> List[BlockId]:
        """Get predecessor blocks of a given block."""
        return list(self.__graph.predecessors(block_id))

    def topological_sort(self) -> List[BlockId]:
        """Return blocks in topological order."""
        try:
            return list(nx.topological_sort(self.__graph))
        except nx.NetworkXError as exc:
            raise ValueError(
                "Graph contains cycles, cannot perform topological sort"
            ) from exc

    def find_dominators(self) -> Dict[BlockId, BlockId]:
        """For each block b find the last BlockID which all paths starting at __entry_block
        must pass through to get to b."""
        if self.__entry_block is None:
            return {}
        # pylint:disable=no-member
        return nx.dominance.immediate_dominators(self.__graph, self.__entry_block)

    def find_loops(self) -> List[List[BlockId]]:
        """Find all loops (cycles) in the CFG."""
        # pylint:disable=broad-exception-caught
        try:
            return list(nx.simple_cycles(self.__graph))
        except Exception:
            return []

    def is_reachable(self, from_block_id: BlockId, to_block_id: BlockId) -> bool:
        """Check if to_block is reachable from from_block."""
        return nx.has_path(self.__graph, from_block_id, to_block_id)

    def shortest_path(
        self, from_block_id: BlockId, to_block_id: BlockId
    ) -> Optional[List[BlockId]]:
        """Find shortest path between two blocks."""
        try:
            return nx.shortest_path(self.__graph, from_block_id, to_block_id)
        except nx.NetworkXNoPath:
            return None

    def is_dag(self) -> bool:
        """Check if the CFG is a directed acyclic graph."""
        return nx.is_directed_acyclic_graph(self.__graph)

    def strongly_connected_components(self) -> List[Set[BlockId]]:
        """Find strongly connected components in the CFG."""
        return list(nx.strongly_connected_components(self.__graph))

    def get_entry_exit_paths(self) -> List[List[BlockId]]:
        """Get all paths from entry to exit blocks."""
        if self.__entry_block is None or not self.__exit_blocks:
            raise ValueError("No entry block and/or no exit blocks")

        all_paths: List[List[BlockId]] = []
        for exit_block in self.__exit_blocks:
            try:
                all_paths.extend(
                    nx.all_simple_paths(self.__graph, self.__entry_block, exit_block)
                )
            except nx.NetworkXNoPath:
                continue

        return all_paths

    def visualize(self) -> str:
        """Generate a simple text representation of the CFG."""
        lines = ["Control Flow Graph:"]
        lines.append(f"Entry: {self.__entry_block}")
        lines.append(f"Exit blocks: {self.__exit_blocks}")
        lines.append(f"Nodes: {self.__graph.number_of_nodes()}")
        lines.append(f"Edges: {self.__graph.number_of_edges()}")
        lines.append("\nBlocks:")

        for block_id in sorted(self.__blocks.keys(), key=str):
            block = self.__blocks[block_id]
            lines.append(f"\n{block}")

            successors = self.get_successors(block_id)
            if successors:
                lines.append(f"  -> Successors: {successors}")

            predecessors = self.get_predecessors(block_id)
            if predecessors:
                lines.append(f"  <- Predecessors: {predecessors}")

        return "\n".join(lines)

    def to_dot(self) -> str:
        """Export CFG to DOT format for visualization with Graphviz."""
        dot_graph = nx.DiGraph()

        for block_id, block in self.__blocks.items():
            label = f"{block_id}\\n" + "\\n".join(
                str(instr) for instr in block.instructions[:3]
            )
            if len(block.instructions) > 3:
                label += "\\n..."
            dot_graph.add_node(block_id, label=label, shape="box")

        for edge in self.__graph.edges():
            dot_graph.add_edge(*edge)

        # Highlight entry and exit blocks
        if self.__entry_block:
            dot_graph.nodes[self.__entry_block]["style"] = "filled"
            dot_graph.nodes[self.__entry_block]["fillcolor"] = "lightgreen"

        for exit_block in self.__exit_blocks:
            dot_graph.nodes[exit_block]["style"] = "filled"
            dot_graph.nodes[exit_block]["fillcolor"] = "lightcoral"

        return nx.nx_pydot.to_pydot(dot_graph).to_string()

    def __repr__(self) -> str:
        return f"""ControlFlowGraph({self.__graph.number_of_nodes()} blocks, \
            {self.__graph.number_of_edges()} edges)"""
