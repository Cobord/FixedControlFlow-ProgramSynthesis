"""
Handle pre and post conditions
"""

from __future__ import annotations
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .llm_types import Condition, Language, Prompt, TypeName, VariableName


class PrePostConditions(BaseModel):
    """
    Handle pre and post conditions

    preconditions: facts that hold on entry to the block
    postconditions: facts that must hold on exit from the block
    inputs: variables available on entry, name -> type
    outputs: variables the block must define or update, name -> type
    """

    preconditions: List[Condition] = Field(default_factory=list)
    postconditions: List[Condition] = Field(default_factory=list)
    inputs: Dict[VariableName, TypeName] = Field(default_factory=dict)
    outputs: Dict[VariableName, TypeName] = Field(default_factory=dict)

    @staticmethod
    def empty() -> PrePostConditions:
        """No conditions at all."""
        return PrePostConditions()

    def is_empty(self) -> bool:
        """Whether there is nothing constraining the block."""
        return not (
            self.preconditions or self.postconditions or self.inputs or self.outputs
        )

    def add_precondition(self, condition: Condition) -> None:
        """Add a fact that holds on entry to the block."""
        self.preconditions.append(condition)

    def add_postcondition(self, condition: Condition) -> None:
        """Add a fact that must hold on exit from the block."""
        self.postconditions.append(condition)

    def add_input(self, name: VariableName, type_name: TypeName) -> None:
        """Declare a variable available on entry to the block."""
        self.inputs[name] = type_name

    def add_output(self, name: VariableName, type_name: TypeName) -> None:
        """Declare a variable the block must define or update."""
        self.outputs[name] = type_name

    def strengthen_precondition_with(self, other: PrePostConditions) -> None:
        """
        Add the postconditions of a predecessor block as preconditions of this one,
        and its outputs as inputs.
        """
        for condition in other.postconditions:
            if condition not in self.preconditions:
                self.preconditions.append(condition)
        for name, type_name in other.outputs.items():
            self.inputs.setdefault(name, type_name)

    def create_prompt_for_block_filling(
        self, description: Optional[Prompt] = None, language: Language = "Python"
    ) -> Prompt:
        """
        Create a prompt that will include the pre and post conditions
        and ask for a basic block that satisfies them.
        description is the block's own summary of what it is for, if it has one.
        """

        def bullets(items: List[Prompt]) -> Prompt:
            return "\n".join(f"- {item}" for item in items) if items else "- (none)"

        def typed(variables: Dict[VariableName, TypeName]) -> List[Prompt]:
            return [f"{name}: {type_name}" for name, type_name in variables.items()]

        sections: List[Prompt] = [
            f"Write a single basic block of straight-line {language} code.",
            "It must not contain any branches, loops, function definitions "
            "or early exits; control flow is handled elsewhere.",
        ]
        if description:
            sections.append(f"Purpose:\n{description}")
        sections += [
            f"Variables available on entry:\n{bullets(typed(self.inputs))}",
            f"Preconditions (you may assume these hold on entry):\n"
            f"{bullets(self.preconditions)}",
            f"Variables to define or update:\n{bullets(typed(self.outputs))}",
            f"Postconditions (these must hold on exit):\n"
            f"{bullets(self.postconditions)}",
            "Reply with only the code, one statement per line, "
            "with no explanation and no markdown fences.",
        ]
        return "\n\n".join(sections)
