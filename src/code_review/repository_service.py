import subprocess


class RepositoryService:
    """Handles Git operations for AI code review."""

    def fetch_branches(self, source_branch: str, target_branch: str) -> None:
        """Fetch the latest source and target branches from the remote repository."""
        subprocess.run(["git", "fetch", "origin", source_branch], check=True)
        subprocess.run(["git", "fetch", "origin", target_branch], check=True)

    def get_changed_files(self, source_branch: str, target_branch: str) -> list[str]:
        """Get a list of file paths changed between the target and source branches."""
        git_diff_result = subprocess.run(
            [
                "git", 
                "diff", 
                "--name-only", 
                f"origin/{target_branch}...origin/{source_branch}"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        return [
            file_path.strip()
            for file_path in git_diff_result.stdout.splitlines()
            if file_path.strip()
        ]

    def get_file_content(self, source_branch: str, file_path: str) -> str:
        """Get the full text content of a file from the source branch."""
        git_show_result = subprocess.run(
            ["git", "show", f"origin/{source_branch}:{file_path}"],
            capture_output=True,
            text=True,
            check=True
        )
        return git_show_result.stdout

    def get_review_files(self, source_branch: str, changed_files: list[str]) -> dict[str, str]:
        """Map each changed file path to its corresponding file content."""
        return {
            file_path: self.get_file_content(source_branch, file_path)
            for file_path in changed_files
        }