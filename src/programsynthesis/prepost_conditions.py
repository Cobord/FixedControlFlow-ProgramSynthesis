"""
Handle pre and post conditions
"""

from .llm_types import Prompt


class PrePostConditions:
    """
    Handle pre and post conditions
    """

    def create_prompt_for_block_filling(self) -> Prompt:
        """
        Create a prompt that will include the pre and post conditions
        and ask for a basic block that satisfies them.
        """
        raise NotImplementedError
