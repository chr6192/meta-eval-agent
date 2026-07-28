#!/usr/bin/env python3
"""Mock GitHub API server for testing the triage workflow."""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Mock data: Open Issues
ISSUES = [
    {
        "id": 1,
        "number": 1,
        "title": "Critical: Production database connection pool exhaustion causing 500 errors",
        "state": "open",
        "labels": [{"name": "bug", "color": "d73a4a"}, {"name": "priority:critical", "color": "b60205"}],
        "created_at": "2026-06-14T08:30:00Z",
        "updated_at": "2026-06-15T10:00:00Z",
        "body": "Our production database connection pool is being exhausted under load, resulting in 500 errors for approximately 15% of API requests.\n\n**Impact:**\n- Customer-facing API endpoints returning 500 errors\n- Average response time degraded from 200ms to 2.5s\n- Support tickets increasing 3x since yesterday\n\n**Steps to reproduce:**\n1. Run load test with 500+ concurrent connections\n2. Observe connection pool metrics in Grafana\n3. Note that connections are not being released back to pool after queries complete\n\n**Expected behavior:** Connections should be properly returned to the pool after each query.\n\n**Actual behavior:** Connections are leaking and never released, eventually exhausting the pool (max: 100 connections).\n\n**Environment:**\n- Production cluster\n- PostgreSQL 15.2\n- Connection pool: pgBouncer with max 100 connections",
        "user": {"login": "ops-team-lead", "id": 101},
        "comments": 5,
        "pull_request": None,
        "assignees": [{"login": "backend-senior-dev"}]
    },
    {
        "id": 2,
        "number": 2,
        "title": "Authentication bypass vulnerability in OAuth2 token validation",
        "state": "open",
        "labels": [{"name": "security", "color": "d73a4a"}, {"name": "priority:high", "color": "c5def5"}],
        "created_at": "2026-06-13T14:15:00Z",
        "updated_at": "2026-06-14T16:30:00Z",
        "body": "Found a vulnerability in our OAuth2 token validation flow where expired tokens can still be used if the request includes a valid refresh token in the same session.\n\n**Vulnerability Details:**\n- The token validation middleware checks access tokens first\n- If the access token is expired, it falls back to refresh token validation\n- However, the fallback does not verify the refresh token's scope properly\n- An attacker with a scoped refresh token (e.g., read-only) can escalate to full admin access\n\n**Affected endpoints:**\n- /api/v2/admin/* (all admin endpoints)\n- /api/v2/users (user management)\n\n**Reproduction:**\n1. Obtain a read-only scoped refresh token\n2. Include it with an expired access token in a request to /api/v2/admin/users\n3. Request succeeds with full admin privileges\n\n**Severity:** HIGH - Potential for privilege escalation",
        "user": {"login": "security-contractor", "id": 102},
        "comments": 3,
        "pull_request": None,
        "assignees": []
    },
    {
        "id": 3,
        "number": 3,
        "title": "Memory leak in WebSocket connection handler",
        "state": "open",
        "labels": [{"name": "bug", "color": "d73a4a"}, {"name": "performance", "color": "fbca04"}],
        "created_at": "2026-06-12T09:00:00Z",
        "updated_at": "2026-06-14T11:00:0Z",
        "body": "The WebSocket connection handler is not properly cleaning up resources when connections are closed unexpectedly. This leads to a gradual memory leak that causes OOM kills after 48-72 hours of uptime.\n\n**Metrics:**\n- Memory grows by ~50MB per day under normal load\n- OOM kill observed 3 times in the past week\n- Each leaked connection holds ~2KB of buffered data\n\n**Proposed fix:** Add proper cleanup in the `onClose` handler and implement connection timeout.",
        "user": {"login": "backend-dev-2", "id": 103},
        "comments": 2,
        "pull_request": None,
        "assignees": [{"login": "backend-senior-dev"}]
    },
    {
        "id": 4,
        "number": 4,
        "title": "Add dark mode support to the dashboard",
        "state": "open",
        "labels": [{"name": "enhancement", "color": "a2eeef"}, {"name": "ui", "color": "bfd4f0"}],
        "created_at": "2026-06-10T16:45:00Z",
        "updated_at": "2026-06-11T09:30:00Z",
        "body": "Users have been requesting dark mode support for the dashboard. This would improve usability in low-light environments and align with modern UI standards.\n\n**Requirements:**\n- Toggle switch in user preferences\n- System theme detection (prefers-color-scheme)\n- Smooth transition between themes\n- Persist user preference in local storage\n\n**Design:** Attached mockups from the design team.\n\n**Priority:** Low - This is a nice-to-have feature.",
        "user": {"login": "product-manager", "id": 104},
        "comments": 8,
        "pull_request": None,
        "assignees": []
    },
    {
        "id": 5,
        "number": 5,
        "title": "CI/CD pipeline failing due to deprecated Node.js version",
        "state": "open",
        "labels": [{"name": "devops", "color": "0075ca"}, {"name": "priority:medium", "color": "fbca04"}],
        "created_at": "2026-06-14T20:00:00Z",
        "updated_at": "2026-06-15T08:00:00Z",
        "body": "The CI/CD pipeline started failing today because Node.js 16 reached EOL and the GitHub Actions runner no longer supports it.\n\n**Error:**\n```\nError: The specified Node.js version 16 is not supported. Please use a version >= 18.\n```\n\n**Affected jobs:**\n- build-and-test\n- deploy-staging\n- deploy-production\n\n**Quick fix:** Update `.github/workflows/ci.yml` to use Node.js 18 or 20.",
        "user": {"login": "devops-engineer", "id": 105},
        "comments": 1,
        "pull_request": None,
        "assignees": []
    },
    {
        "id": 6,
        "number": 6,
        "title": "Update README with new onboarding instructions",
        "state": "open",
        "labels": [{"name": "documentation", "color": "0075ca"}, {"name": "good first issue", "color": "7057ff"}],
        "created_at": "2026-06-09T11:00:00Z",
        "updated_at": "2026-06-09T11:00:00Z",
        "body": "The README needs to be updated with:\n- New project setup instructions (we moved to Docker Compose)\n- Updated contributing guidelines\n- Link to the new developer portal\n- Badges for CI status and code coverage",
        "user": {"login": "tech-lead", "id": 106},
        "comments": 0,
        "pull_request": None,
        "assignees": []
    }
]

# Mock data: Open Pull Requests
PULL_REQUESTS = [
    {
        "id": 101,
        "number": 42,
        "title": "Fix database connection pool leak by implementing proper cleanup",
        "state": "open",
        "labels": [{"name": "bug", "color": "d73a4a"}, {"name": "priority:high", "color": "c5def5"}],
        "created_at": "2026-06-15T06:00:00Z",
        "updated_at": "2026-06-15T09:30:00Z",
        "body": "This PR fixes the database connection pool leak described in #1.\n\n**Changes:**\n- Added proper connection release in finally blocks for all database operations\n- Implemented connection pool health monitoring with alerts at 80% capacity\n- Added unit tests for connection lifecycle\n\n**Related to:** #1\n\n**Testing:** Load tested with 1000 concurrent connections for 2 hours - no connection leaks observed.",
        "user": {"login": "backend-senior-dev", "id": 107},
        "comments": 4,
        "merged": False,
        "mergeable": True,
        "draft": False,
        "additions": 145,
        "deletions": 23,
        "changed_files": 8,
        "reviewers": [{"login": "tech-lead", "state": "APPROVED"}]
    },
    {
        "id": 102,
        "number": 43,
        "title": "Update Node.js to v20 in CI/CD pipeline",
        "state": "open",
        "labels": [{"name": "devops", "color": "0075ca"}],
        "created_at": "2026-06-15T10:00:00Z",
        "updated_at": "2026-06-15T10:15:00Z",
        "body": "Bumps Node.js version from 16 to 20 in all CI/CD workflows.\n\n**Changes:**\n- Updated `.github/workflows/ci.yml`\n- Updated `.github/workflows/deploy.yml`\n- Updated `Dockerfile` base image\n- Added Node.js 20 compatibility notes\n\n**Related to:** #5\n\n**Testing:** All tests pass on Node.js 20.",
        "user": {"login": "devops-engineer", "id": 105},
        "comments": 1,
        "merged": False,
        "mergeable": True,
        "draft": False,
        "additions": 12,
        "deletions": 8,
        "changed_files": 3,
        "reviewers": []
    },
    {
        "id": 103,
        "number": 44,
        "title": "Implement OAuth2 token scope validation fix",
        "state": "open",
        "labels": [{"name": "security", "color": "d73a4a"}, {"name": "priority:high", "color": "c5def5"}],
        "created_at": "2026-06-14T17:00:00Z",
        "updated_at": "2026-06-15T07:00:00Z",
        "body": "This PR addresses the OAuth2 token validation vulnerability described in #2.\n\n**Changes:**\n- Added strict scope validation for refresh token fallback\n- Implemented token scope inheritance rules\n- Added comprehensive security test suite\n- Added audit logging for all token validations\n\n**Related to:** #2\n\n**Security Review:** Required before merge.\n\n**Testing:** Added 15 new security test cases, all passing.",
        "user": {"login": "security-contractor", "id": 102},
        "comments": 6,
        "merged": False,
        "mergeable": True,
        "draft": False,
        "additions": 230,
        "deletions": 15,
        "changed_files": 12,
        "reviewers": [{"login": "backend-senior-dev", "state": "COMMENTED"}]
    }
]


class MockGitHubHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress log output

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('X-RateLimit-Remaining', '5000')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, status, message):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"message": message}).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # API version endpoint
        if path == '/':
            self._send_json({"message": "Mock GitHub API", "version": "1.0"})
            return

        # Repository info
        if path == '/repos/testuser/my-project':
            self._send_json({
                "id": 12345,
                "name": "my-project",
                "full_name": "testuser/my-project",
                "owner": {"login": "testuser"},
                "description": "A sample project for demonstration purposes",
                "private": False,
                "html_url": "https://github.com/testuser/my-project"
            })
            return

        # Issues endpoint (includes PRs by default in GitHub API)
        if path == '/repos/testuser/my-project/issues':
            state = params.get('state', ['open'])[0]
            result = [i for i in ISSUES if i['state'] == state]
            self._send_json(result)
            return

        # Single issue
        issue_num = None
        if path.startswith('/repos/testuser/my-project/issues/'):
            try:
                issue_num = int(path.split('/')[-1])
                issue = next((i for i in ISSUES if i['number'] == issue_num), None)
                if issue:
                    self._send_json(issue)
                    return
            except ValueError:
                pass

        # Pull requests endpoint
        if path == '/repos/testuser/my-project/pulls':
            self._send_json(PULL_REQUESTS)
            return

        # Single PR
        if path.startswith('/repos/testuser/my-project/pulls/'):
            try:
                pr_num = int(path.split('/')[-1])
                pr = next((p for p in PULL_REQUESTS if p['number'] == pr_num), None)
                if pr:
                    self._send_json(pr)
                    return
            except ValueError:
                pass

        # Issue comments
        if path.startswith('/repos/testuser/my-project/issues/') and path.endswith('/comments'):
            parts = path.split('/')
            try:
                issue_num = int(parts[-2])
                issue = next((i for i in ISSUES if i['number'] == issue_num), None)
                if issue:
                    self._send_json([])  # No existing comments for simplicity
                    return
            except (ValueError, IndexError):
                pass

        # PR comments
        if path.startswith('/repos/testuser/my-project/pulls/') and path.endswith('/comments'):
            parts = path.split('/')
            try:
                pr_num = int(parts[-2])
                pr = next((p for p in PULL_REQUESTS if p['number'] == pr_num), None)
                if pr:
                    self._send_json([])
                    return
            except (ValueError, IndexError):
                pass

        self._send_error(404, "Not Found")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length).decode())

        parsed = urlparse(self.path)
        path = parsed.path

        # Comment on issue
        if path.startswith('/repos/testuser/my-project/issues/') and path.endswith('/comments'):
            parts = path.split('/')
            try:
                issue_num = int(parts[-2])
                issue = next((i for i in ISSUES if i['number'] == issue_num), None)
                if issue:
                    comment = {
                        "id": 999,
                        "body": body.get("body", ""),
                        "user": {"login": "triage-bot"},
                        "created_at": "2026-06-15T16:00:00Z"
                    }
                    self._send_json(comment, status=201)
                    return
            except (ValueError, IndexError):
                pass

        self._send_error(404, "Not Found")


def run_server(port=9876):
    server = HTTPServer(('127.0.0.1', port), MockGitHubHandler)
    print(f"Mock GitHub API running on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == '__main__':
    run_server()
