import json
import subprocess
from pathlib import Path


class CopilotService:
    """Interfaces with GitHub Copilot to generate automated code reviews."""

    def __init__(self, repository_service) -> None:
        """Initialize the Copilot service with a repository handler dependency."""
        self.repository_service = repository_service

    def build_review_prompt(self, source_branch: str, changed_files: list[str]) -> str:
        """Combine framework instructions, project rules, and modified file contents into a single prompt."""
        prompt_sections = [
            self._load_framework_prompt(),
            self._load_project_instructions()
        ]

        review_files = self.repository_service.get_review_files(source_branch, changed_files)

        for file_path, file_content in review_files.items():
            prompt_sections.append(f"\nFILE: {file_path}\n\n{file_content}\n")

        return "\n".join(prompt_sections)

    def run_review(self, review_prompt: str) -> dict:
        """Execute the GitHub Copilot CLI with the review prompt and return the parsed JSON issues."""
        command_result = subprocess.run(
            [
                "gh",
                "copilot",
                "--",
                "-p",
                review_prompt,
                "--allow-all-tools",
                "--silent"
            ],
            capture_output=True,
            text=True
        )

        if command_result.returncode != 0:
            raise RuntimeError(f"Copilot failed:\n{command_result.stderr}")

        copilot_response = command_result.stdout.strip()
        copilot_response = copilot_response.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(copilot_response)
        except json.JSONDecodeError:
            print("\nINVALID JSON RETURNED BY COPILOT\n")
            print(copilot_response)
            raise

    def _load_framework_prompt(self) -> str:
        """Load the base framework review prompt from the global project markdown file."""
        prompt_file = Path(__file__).resolve().parents[2] / "review_prompt.md"
        return prompt_file.read_text()

    def _load_project_instructions(self) -> str:
        """Load local project-specific instructions if the configuration file exists."""
        instruction_file = Path("copilot-instructions.md")

        if not instruction_file.exists():
            print("copilot-instructions.md not found")
            return ""

        return instruction_file.read_text()