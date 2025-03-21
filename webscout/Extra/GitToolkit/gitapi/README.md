# 🚀 GitAPI: GitHub Data Extraction Module

## Overview

GitAPI is a powerful, lightweight GitHub data extraction module within the Webscout Python package. It provides comprehensive tools for retrieving GitHub repository and user information without requiring authentication for public data access.

## ✨ Features

- **Repository Operations**
  - Repository metadata retrieval
  - Commit history tracking
  - Pull request management
  - Issue tracking
  - Release information
  - Branch management
  - Repository statistics
  - Workflow data

- **User Operations**
  - Profile information
  - Repository listing
  - Follower/Following data
  - Organization membership
  - Event tracking
  - Gist management
  - Star history

- **Error Handling**
  - Rate limit detection
  - Resource not found handling
  - Request retry mechanism
  - Custom error types

## 📦 Installation

Install as part of the Webscout package:

```bash
pip install webscout
```

## 💡 Quick Examples

### Repository Operations

```python
from webscout.Extra.GitToolkit.gitapi import Repository

# Initialize repository client
repo = Repository("OE-LUCIFER", "Webscout")

# Get basic repository info
info = repo.get_info()
print(f"Repository: {info['full_name']}")
print(f"Stars: {info['stargazers_count']}")

# Get latest commits
commits = repo.get_commits(per_page=5)
for commit in commits:
    print(f"Commit: {commit['commit']['message']}")
```

### User Operations

```python
from webscout.Extra.GitToolkit.gitapi import User

# Initialize user client
user = User("OE-LUCIFER")

# Get user profile
profile = user.get_profile()
print(f"User: {profile['login']}")
print(f"Followers: {profile['followers']}")

# Get user's repositories
repositories = user.get_repositories()
for repo in repositories:
    print(f"Repository: {repo['name']}")
```

## 🔧 Available Methods

### Repository Class

- `get_info()`: Basic repository information
- `get_commits()`: Repository commit history
- `get_pull_requests()`: Repository pull requests
- `get_issues()`: Repository issues
- `get_releases()`: Repository releases
- `get_branches()`: Repository branches
- And many more...

### User Class

- `get_profile()`: User profile information
- `get_repositories()`: User's public repositories
- `get_followers()`: User's followers
- `get_following()`: Users being followed
- `get_organizations()`: User's organizations
- And many more...

## ⚠️ Error Handling

The module includes several custom exception types:

- `GitError`: Base exception for all GitHub API errors
- `RateLimitError`: Raised when hitting API rate limits
- `NotFoundError`: Raised when resource is not found
- `RequestError`: Raised for general request errors
