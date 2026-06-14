import os
import sys

from gitlab_client import GitLabClient
from repository_service import RepositoryService
from copilot_service import CopilotService


def main() -> None:
    """Execute the automated AI code review pipeline for a GitLab Merge Request."""
    print("AI Review Started")

    # Read required GitLab CI/CD environment variables
    branch_name = os.getenv("CI_COMMIT_REF_NAME")
    project_id = os.getenv("CI_PROJECT_ID")
    api_url = os.getenv("CI_API_V4_URL")
    job_token = os.getenv("CI_JOB_TOKEN")
    gitlab_access_token = os.getenv("GITLAB_ACCESS_TOKEN")

    # Validate all required environment variables
    required_variables = {
        "CI_COMMIT_REF_NAME": branch_name,
        "CI_PROJECT_ID": project_id,
        "CI_API_V4_URL": api_url,
        "CI_JOB_TOKEN": job_token,
        "GITLAB_ACCESS_TOKEN": gitlab_access_token
    }

    for name, value in required_variables.items():
        if not value:
            print(f"ERROR: Required environment variable '{name}' was not provided.")
            sys.exit(1)

    # Initialize external service clients
    gitlab_client = GitLabClient(
        api_url=api_url,
        project_id=project_id,
        job_token=job_token,
        access_token=gitlab_access_token
    )
    repository_service = RepositoryService()
    copilot_service = CopilotService(repository_service)

    # Discover the active Merge Request summary via the branch name
    discovered_mr = gitlab_client.get_merge_request_by_branch(branch_name)
    merge_request_iid = str(discovered_mr["iid"])

    # Fetch the complete Merge Request payload (including diff_refs) using the single MR endpoint
    merge_request = gitlab_client.get_merge_request(merge_request_iid)

    # Remove AI comments from previous review runs
    print("Deleting previous AI comments...")
    gitlab_client.delete_ai_comments(merge_request_iid)

    # Extract source and target branches from the merge request
    source_branch = merge_request["source_branch"]
    target_branch = merge_request["target_branch"]

    print(f"Source Branch: {source_branch}")
    print(f"Target Branch: {target_branch}")

    # Fetch the latest tracking commits for both branches locally
    repository_service.fetch_branches(source_branch, target_branch)

    # Determine which files were modified in the merge request
    changed_files = repository_service.get_changed_files(source_branch, target_branch)

    if not changed_files:
        print("No changed files found.")
        return

    print("Changed Files:")
    for file_path in changed_files:
        print(f" - {file_path}")

    # Build the final review prompt containing instructions and file contents
    review_prompt = copilot_service.build_review_prompt(source_branch, changed_files)

    # Send the prompt to GitHub Copilot and parse the response
    review_result = copilot_service.run_review(review_prompt)
    review_issues = review_result.get("issues", [])

    # Post a summary comment and exit if no issues are found
    if not review_issues:
        gitlab_client.post_review_comment(
            merge_request_iid, 
            "🤖 AI Review\n\nNo issues found."
        )
        print("No issues found.")
        return

    # Post a summary comment indicating the total number of issues found
    gitlab_client.post_review_comment(
        merge_request_iid,
        f"[AI_REVIEW]\n\n🤖 AI Review\n\nFound {len(review_issues)} issue(s).\nSee inline comments for details."
    )

    # Extract diff references required for positioning inline comments correctly
    diff_refs = merge_request["diff_refs"]

    # Create inline comments for each identified issue
    for issue in review_issues:
        try:
            gitlab_client.post_inline_comment(merge_request_iid, issue, diff_refs)
            print(f"Inline comment created: {issue['file']}:{issue['line']}")
        except Exception as error:
            print(f"Failed to create inline comment: {issue['file']}:{issue['line']}")
            print(str(error))

    print("AI Review Completed")


if __name__ == "__main__":
    main()