import json
import urllib.request
import urllib.parse  # Added for safe branch name URL encoding


class GitLabClient:
    """Interacts with the GitLab REST API to manage Merge Request communications."""

    def __init__(self, api_url: str, project_id: str, job_token: str, access_token: str) -> None:
        """Initialize the GitLab API client with endpoint configurations and credentials."""
        self.api_url = api_url
        self.project_id = project_id
        self.job_token = job_token
        self.access_token = access_token

    def get_merge_request_by_branch(self, branch_name: str) -> dict:
        """Fetch the open merge request associated with a specific branch name."""
        encoded_branch = urllib.parse.quote(branch_name, safe="")
        url = f"{self.api_url}/projects/{self.project_id}/merge_requests?source_branch={encoded_branch}&state=opened"
        
        request = urllib.request.Request(
            url,
            headers={"PRIVATE-TOKEN": self.access_token}
        )
        response = urllib.request.urlopen(request)
        merge_requests = json.loads(response.read().decode())

        if not merge_requests:
            raise RuntimeError(f"No active open or draft Merge Request found for branch '{branch_name}'.")

        return merge_requests[0]

    def get_merge_request(self, merge_request_iid: str) -> dict:
        """Fetch metadata and branch structure of a specific GitLab merge request."""
        merge_request_url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{merge_request_iid}"
        request = urllib.request.Request(
            merge_request_url,
            headers={"JOB-TOKEN": self.job_token}
        )
        response = urllib.request.urlopen(request)
        return json.loads(response.read().decode())

    def post_review_comment(self, merge_request_iid: str, comment_body: str) -> None:
        """Post a top-level summary text note onto the merge request timeline."""
        notes_url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{merge_request_iid}/notes"
        payload = {"body": comment_body}
        self._post(notes_url, payload)

    def post_inline_comment(self, merge_request_iid: str, issue: dict, diff_refs: dict) -> None:
        """Post an inline review comment targeting a specific line context in the diff."""
        discussion_url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{merge_request_iid}/discussions"
        payload = {
            "body": (
                "[AI_REVIEW]\n\n"
                f"🤖 {issue['severity']}\n\n"
                f"{issue['issue']}\n\n"
                f"Recommendation:\n"
                f"{issue['recommendation']}"
            ),
            "position": {
                "position_type": "text",
                "base_sha": diff_refs["base_sha"],
                "start_sha": diff_refs["start_sha"],
                "head_sha": diff_refs["head_sha"],
                "new_path": issue["file"],
                "new_line": issue["line"]
            }
        }
        self._post(discussion_url, payload)

    def _post(self, url: str, payload: dict) -> None:
        """Execute a synchronous HTTP POST request with a JSON request body."""
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "PRIVATE-TOKEN": self.access_token,
                "Content-Type": "application/json"
            },
            method="POST"
        )
        urllib.request.urlopen(request)

    def delete_ai_comments(self, merge_request_iid: str) -> None:
        """Scan discussion threads and delete previous automated AI review notes."""
        discussions_url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{merge_request_iid}/discussions"
        request = urllib.request.Request(
            discussions_url,
            headers={"PRIVATE-TOKEN": self.access_token}
        )
        response = urllib.request.urlopen(request)
        discussions = json.loads(response.read().decode())

        for discussion in discussions:
            notes = discussion.get("notes", [])
            if not notes:
                continue

            first_note = notes[0]
            body = first_note.get("body", "")

            if "[AI_REVIEW]" not in body:
                continue

            note_id = first_note["id"]
            delete_url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{merge_request_iid}/notes/{note_id}"
            delete_request = urllib.request.Request(
                delete_url,
                headers={"PRIVATE-TOKEN": self.access_token},
                method="DELETE"
            )

            try:
                print(f"Deleting note {note_id}")
                urllib.request.urlopen(delete_request)
                print(f"Deleted AI note {note_id}")
            except Exception as error:
                print(f"Failed deleting note {note_id}")
                print(str(error))