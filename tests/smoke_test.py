"""Basic smoke test to ensure core modules import correctly after cleanup."""


def test_core_imports():
    from emulator_bot import EmulatorBot  # noqa: F401
    from battle_runner import BattleRunner  # noqa: F401
    from battle_strategy import BattleStrategy  # noqa: F401
    from battle_logic import BattleLogic  # noqa: F401
    from detection import ImageDetector  # noqa: F401
    from logger import Logger  # noqa: F401
    from emulators.memu import MemuController  # noqa: F401

    assert True
