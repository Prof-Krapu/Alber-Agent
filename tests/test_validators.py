"""
Tests pour le validateur d'entrées.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validators import (
    FilePathValidator,
    LatexValidator,
    sanitize_shell_command,
)
from pathlib import Path


class TestFilePathValidator:
    def setup_method(self):
        self.validator = FilePathValidator("/tmp/test_workspace")

    def test_valid_path(self):
        result = self.validator.validate("test.txt")
        assert result is not None
        assert isinstance(result, Path)
        assert str(result).startswith("/tmp/test_workspace")

    def test_traversal_blocked(self):
        assert self.validator.validate("../etc/passwd") is None

    def test_absolute_path_blocked(self):
        assert self.validator.validate("/etc/passwd") is None

    def test_null_bytes_stripped(self):
        # Null byte is stripped, path becomes "test.txt" which is valid
        result = self.validator.validate("test\x00.txt")
        assert result is not None

    def test_only_null_byte_resolves_to_root(self):
        result = self.validator.validate("\x00")
        # After stripping null byte, path becomes "" which resolves to workspace root
        # This is valid since it's within the workspace
        assert result is not None

    def test_empty_path_blocked(self):
        assert self.validator.validate("") is None

    def test_dot_dot_in_name_blocked(self):
        assert self.validator.validate("..") is None
        assert self.validator.validate("foo/../../etc") is None


class TestLatexValidator:
    def test_valid_latex(self):
        safe, error = LatexValidator.validate(r"\begin{equation} E=mc^2 \end{equation}")
        assert safe is True
        assert error is None

    def test_empty_latex_rejected(self):
        safe, error = LatexValidator.validate("")
        assert safe is False

    def test_too_long_latex_rejected(self):
        safe, error = LatexValidator.validate("x" * 500001)
        assert safe is False

    def test_unbalanced_braces_rejected(self):
        safe, error = LatexValidator.validate(r"\begin{document} {test")
        assert safe is False
        assert "Accolades" in error


class TestShellCommandSanitizer:
    def test_safe_command(self):
        safe, error = sanitize_shell_command("ls -la")
        assert safe is True

    def test_pipe_blocked(self):
        safe, error = sanitize_shell_command("cat /etc/passwd | grep root")
        assert safe is False

    def test_redirect_blocked(self):
        safe, error = sanitize_shell_command("echo test > file.txt")
        assert safe is False

    def test_semicolon_blocked(self):
        safe, error = sanitize_shell_command("ls; rm -rf /")
        assert safe is False

    def test_empty_command_blocked(self):
        safe, error = sanitize_shell_command("   ")
        assert safe is False

    def test_long_command_blocked(self):
        safe, error = sanitize_shell_command("a" * 5001)
        assert safe is False
