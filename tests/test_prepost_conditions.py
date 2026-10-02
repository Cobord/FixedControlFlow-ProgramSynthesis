"""
Testing pre and post conditions
"""

from src.programsynthesis import PrePostConditions


def test_empty():
    """
    empty has nothing constraining the block
    """
    conditions = PrePostConditions.empty()
    assert conditions.is_empty()
    conditions.add_precondition("x > 5")
    assert not conditions.is_empty()


def test_add():
    """
    adding conditions and variables
    """
    conditions = PrePostConditions()
    conditions.add_precondition("x > 5")
    conditions.add_postcondition("z == x + y")
    conditions.add_input("x", "int")
    conditions.add_input("y", "int")
    conditions.add_output("z", "int")
    assert conditions.preconditions == ["x > 5"]
    assert conditions.postconditions == ["z == x + y"]
    assert conditions.inputs == {"x": "int", "y": "int"}
    assert conditions.outputs == {"z": "int"}


def test_defaults_not_shared():
    """
    each instance gets its own lists and dicts
    """
    first = PrePostConditions()
    first.add_precondition("x > 5")
    assert PrePostConditions().preconditions == []


def test_strengthen_precondition_with():
    """
    predecessor postconditions and outputs flow into preconditions and inputs
    without duplicates or overwriting existing input types
    """
    predecessor = PrePostConditions(
        postconditions=["x > 5", "y == 2"], outputs={"x": "int", "y": "int"}
    )
    successor = PrePostConditions(preconditions=["x > 5"], inputs={"y": "float"})
    successor.strengthen_precondition_with(predecessor)
    assert successor.preconditions == ["x > 5", "y == 2"]
    assert successor.inputs == {"y": "float", "x": "int"}


def test_prompt():
    """
    prompt mentions everything given
    """
    conditions = PrePostConditions(
        preconditions=["x > 5"],
        postconditions=["z == x + y"],
        inputs={"x": "int", "y": "int"},
        outputs={"z": "int"},
    )
    prompt = conditions.create_prompt_for_block_filling("sum the inputs", "Rust")
    for text in [
        "Rust",
        "Purpose:\nsum the inputs",
        "- x: int",
        "- y: int",
        "- z: int",
        "- x > 5",
        "- z == x + y",
    ]:
        assert text in prompt


def test_prompt_without_description():
    """
    no description means no purpose section, empty sections say none
    """
    prompt = PrePostConditions.empty().create_prompt_for_block_filling()
    assert "Python" in prompt
    assert "Purpose" not in prompt
    assert "- (none)" in prompt
