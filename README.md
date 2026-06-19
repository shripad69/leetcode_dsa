# AI Code Review Agent

An automated code review utility built to analyze GitLab Merge Requests using the GitHub Copilot CLI. The system automatically discovers the active or Draft Merge Request associated with a branch, extracts modified files, gathers context, and posts line-by-line feedback directly back to the GitLab discussion board.

---

## 📑 GitLab API Endpoints Used

The Python service (`gitlab_client.py`) interacts with GitLab REST API v4 using four core actions:

1. **Auto-Discovery (`GET /projects/{id}/merge_requests`)**
* Uses the current branch name (`source_branch`) and `state=opened` to dynamically find the target Merge Request. This endpoint works for both standard and **Draft** merge requests.


2. **Detailed Fetch (`GET /projects/{id}/merge_requests/{iid}`)**
* Triggered immediately after auto-discovery to retrieve advanced metadata, specifically the cryptographic hashes (`diff_refs`) needed to map line numbers.


3. **Timeline Comments (`POST /projects/{id}/merge_requests/{iid}/notes`)**
* Posts the top-level review summary comment directly onto the main activity feed of the Merge Request.


4. **Inline Diff Threads (`POST /projects/{id}/merge_requests/{iid}/discussions`)**
* Places targeted, line-by-line AI recommendations directly onto the exact file path and code line where an issue was flagged.


5. **Historical Purge (`DELETE /projects/{id}/merge_requests/{iid}/notes/{note_id}`)**
* Identifies older AI comments labeled with `[AI_REVIEW]` and deletes them before starting a new run to prevent comment spam.


---

## 🔑 Authentication Tokens Reference

The project requires two distinct tokens to authorize actions securely across GitLab and GitHub.

**`GITLAB_ACCESS_TOKEN`** 
**`COPILOT_GITHUB_TOKEN`** 

### How to Create the Tokens

#### 1. GitLab Access Token (Personal Access Token)

1. Log in to your GitLab instance.
2. In the top-right or bottom-left corner, click your **Profile Avatar** and go to **Preferences / Settings**.
3. Select **Access Tokens** from the sidebar.
4. Click **Add new token**.
5. Give it a name (e.g., `ai-review-token`), set an expiration date, and select the **`api`** checkbox.
6. Click **Create personal access token** and copy the generated string immediately.

#### 2. GitHub Copilot Token

1. Log in to your GitHub account.
2. Click your avatar in the top right and navigate to **Settings** -> **Developer Settings** -> **Personal Access Tokens**.
3. Select **Tokens (classic)** or Fine-Grained tokens depending on corporate policies.
4. Generate a new token ensuring the account has active access to GitHub Copilot permissions.
5. Copy the generated token string safely.

---

## 🚀 How to Run the Pipeline Manually

Follow these exact steps to run the code review tool from the GitLab web interface:

1. Open your target repository inside **GitLab**.
2. Create a **Merge Request** (or **Draft Merge Request**) for your working feature branch.
3. Navigate to **Build > Pipelines** using the left sidebar.
4. Click the blue **Run pipeline** button in the top-right corner.
5. **Select the working branch** from the dropdown menu (ensure it matches the branch with your open MR).
6. Under the **Variables** section, populate the runtime configurations:
* **Key:** `GITLAB_ACCESS_TOKEN`
* **Value:** Paste your generated GitLab Personal Access Token.
* **Key:** `COPILOT_GITHUB_TOKEN`
* **Value:** Paste your generated Github Personal Access Token.


7. Click **Run pipeline**. The job will spin up, automatically scan your branch, fetch the MR data, and output its review logs directly onto your Merge Request page.
