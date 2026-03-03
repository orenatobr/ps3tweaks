"""Tests for PS3 Emulator Config."""

import pytest

from ps3tweaks.config import PS1_DEFAULT, PS2_DEFAULT, EmulatorConfig


class TestEmulatorConfig:
    """Test cases for EmulatorConfig dataclass."""

    def test_ps1_default_config(self) -> None:
        """Validate PS1 default profile fields.

        Returns:
            None.
        """
        assert PS1_DEFAULT.emulator_type == "ps1_netemu.self"
        assert PS1_DEFAULT.video_mode == "normal"
        assert PS1_DEFAULT.analog_mode is True

    def test_ps2_default_config(self) -> None:
        """Validate PS2 default profile fields.

        Returns:
            None.
        """
        assert PS2_DEFAULT.emulator_type == "ps2_netemu.self"
        assert PS2_DEFAULT.video_mode == "fullscreen"
        assert PS2_DEFAULT.analog_mode is False

    def test_config_to_dict(self) -> None:
        """Validate dictionary conversion.

        Returns:
            None.
        """
        config_dict = PS1_DEFAULT.to_dict()
        assert isinstance(config_dict, dict)
        assert "emulator_type" in config_dict

    def test_config_from_dict(self) -> None:
        """Validate object creation from dictionary payload.

        Returns:
            None.
        """
        data = {
            "emulator_type": "ps1_netemu.self",
            "memory_card_slot1": "custom.vmc",
            "video_mode": "normal",
            "analog_mode": True,
            "screen_size": "normal",
        }
        config = EmulatorConfig.from_dict(data)
        assert config.memory_card_slot1 == "custom.vmc"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
