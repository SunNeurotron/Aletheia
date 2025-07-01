# API Scopes for Granular Authorization (Conceptual Design)

This document outlines a conceptual design for using OAuth2 scopes to implement more granular authorization for the Aletheia platform's API. This allows different clients or users to have specific sets of permissions.

## What are API Scopes?

OAuth2 scopes are a mechanism to limit an application's access to a user's account. An application can request one or more scopes, and the access token issued to the application will be limited to the scopes granted.

In the context of Aletheia's API, scopes can define specific permissions for various resources and actions (e.g., read jobs, submit jobs, manage users, manage conjectures).

## Proposed Scopes for Aletheia API

The following is a non-exhaustive list of potential scopes. The naming convention `resource:action` is common.

**Job-Related Scopes:**
*   `jobs:submit`: Allows creating/submitting new discovery jobs.
*   `jobs:read:self`: Allows reading details of jobs submitted by the authenticated user.
*   `jobs:read:all`: Allows reading details of all jobs (admin/privileged scope).
*   `jobs:cancel:self`: Allows cancelling jobs submitted by the authenticated user (if cancellation is implemented).
*   `jobs:cancel:all`: Allows cancelling any job (admin/privileged scope).

**Researcher-Related Scopes (User Management):**
*   `researchers:create`: Allows creating new researcher accounts (potentially an open scope for registration, or admin-only).
*   `researchers:read:self`: Allows reading the profile of the authenticated researcher.
*   `researchers:read:all`: Allows listing and reading profiles of all researchers (admin scope).
*   `researchers:update:self`: Allows updating the profile of the authenticated researcher.
*   `researchers:update:all`: Allows updating any researcher's profile (admin scope).
*   `researchers:delete`: Allows deleting researcher accounts (admin scope).

**Conjecture-Related Scopes:**
*   `conjectures:create`: Allows proposing new derived conjectures.
*   `conjectures:read`: Allows reading all derived conjectures (public or authenticated access).
*   `conjectures:update:self`: Allows updating conjectures proposed by the authenticated user.
*   `conjectures:update:all`: Allows updating any conjecture (moderator/admin scope).
*   `conjectures:review`: Allows changing the status of conjectures (moderator/admin scope).
*   `conjectures:delete`: Allows deleting conjectures (admin scope).

**Attribution-Related Scopes:**
*   `attributions:create`: Allows adding attributions (e.g., verification, analysis) to hits.
*   `attributions:read`: Allows reading attributions.

**Plugin-Related Scopes (If API endpoints for plugin management are added):**
*   `plugins:manage`: Allows listing, enabling/disabling, or configuring plugins (admin scope).

**Admin Scopes:**
*   `admin:full_access`: A master scope granting all permissions (use with extreme caution).

## Implementation Sketch in Aletheia

### 1. Modifying `Aletheia_v3/api/auth.py`

*   **Token Data:** The `TokenData` schema (if used for JWT payload) could include a `scopes: List[str] = []` field.
    ```python
    # In schemas.py or auth.py
    class TokenData(BaseModel):
        username: Optional[str] = None
        scopes: List[str] = []
    ```

*   **Token Creation (`create_access_token`):**
    *   When a user logs in (e.g., via `/token` endpoint), their roles/permissions would be determined (e.g., from `ResearcherDB` model which might get a `roles` field or by checking if `username == 'admin'`).
    *   Based on these roles, a list of applicable scopes would be generated and included in the JWT payload when `create_access_token` is called.
    ```python
    # In auth.py, conceptual change in create_access_token
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy() # data should now include 'sub' (username) and 'scopes' (list of strings)
        # ... (expiration logic) ...
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    ```
    *   The `/token` endpoint logic in `api_server.py` would need to determine these scopes for the authenticated user before calling `create_access_token`.

### 2. Modifying `Aletheia_v3/api/api_server.py` (Endpoint Protection)

*   **FastAPI Security Scopes:** FastAPI has built-in support for OAuth2 scopes.
    *   Update `OAuth2PasswordBearer` to include scopes:
        ```python
        # In auth.py
        # Define all possible scopes your API supports
        oauth2_scheme = OAuth2PasswordBearer(
            tokenUrl="token",
            scopes={
                "jobs:submit": "Submit new discovery jobs.",
                "jobs:read:self": "Read your own jobs.",
                # ... other scopes ...
                "admin:full_access": "Full administrative access."
            }
        )
        ```
    *   **Protecting Endpoints:** Use `Security` dependency with scopes.
        ```python
        # In api_server.py
        from fastapi import Security # Changed from Depends for auth functions that use scopes

        # ... (oauth2_scheme defined in auth.py) ...

        async def get_current_active_user_with_scopes(
            security_scopes: SecurityScopes, # Injected by FastAPI
            token: str = Depends(auth.oauth2_scheme) # auth.oauth2_scheme needs scopes defined
        ):
            # ... (decode token as in get_current_active_user) ...
            # payload = jwt.decode(...)
            # username = payload.get("sub")
            # token_scopes = payload.get("scopes", []) # Get scopes from token

            # Check if token has required scopes
            # for scope in security_scopes.scopes:
            #     if scope not in token_scopes:
            #         raise HTTPException(...)
            # return user_from_db
            # This logic needs to be correctly implemented in auth.py's get_current_active_user
            # or a new dependency. FastAPI handles scope checking if Security is used correctly.

            # For now, let's assume get_current_active_user is enhanced to handle this
            # or we create a new dependency.
            # FastAPI's `Security` dependency handles scope checking automatically if
            # the `scopes` parameter is used in the endpoint and `oauth2_scheme` has scopes defined.
            # The token itself must contain the scopes.

            # Simplified: auth.get_current_active_user would need to be aware of security_scopes
            # or we'd write a new dependency.
            # Let's assume auth.get_current_active_user is updated to extract scopes from token
            # and FastAPI's Security() does the check.

            # A more common pattern is to have get_current_user decode the token,
            # then a separate dependency checks scopes against the decoded token.
            # Or, FastAPI's Security does it if the token has a "scopes" claim (list of strings).

            # Let's update get_current_active_user in auth.py to put scopes in user object (conceptually)
            # and then the endpoint uses Security(auth.get_current_active_user, scopes=["required_scope"])
            user = await auth.get_current_active_user(token) # Assume this user object might now have a .scopes attribute

            # Manual scope check (if not relying on FastAPI's Security scopes parameter directly)
            # This part is typically handled by FastAPI if you use Security(..., scopes=["..."])
            # For this example, we'll assume token payload includes 'scopes' and auth.User might carry them.
            # This is just for illustration; FastAPI's built-in scope handling is preferred.

            # Correct way:
            # 1. Token payload contains a "scopes" claim (list of strings).
            # 2. auth.py's oauth2_scheme defines all possible scopes.
            # 3. Endpoint uses `current_user: User = Security(get_user_func, scopes=["needed_scope"])`
            # FastAPI will then:
            #    - Ensure token is valid via get_user_func.
            #    - Check if "needed_scope" is in the token's "scopes" claim.

            # For this conceptual document, we'll just state that endpoints would use this.
            return user # The user object, FastAPI checks scopes based on endpoint decorator.

        @router.post("/jobs", dependencies=[Security(get_current_active_user_with_scopes, scopes=["jobs:submit"])])
        async def create_job_with_scope_check(...):
            # ... endpoint logic ...
            pass

        @router.get("/researchers", dependencies=[Security(get_current_active_user_with_scopes, scopes=["researchers:read:all"])])
        async def list_all_researchers_with_scope_check(...):
            # ... endpoint logic ...
            pass
        ```

### 3. User/Role Management

*   The `ResearcherDB` model would need a way to store roles or permissions that map to these scopes (e.g., a `roles: List[str]` field or a many-to-many relationship to a `Role` model which has associated scopes).
*   When a user logs in, the `/token` endpoint logic would query these roles/permissions and embed the corresponding scopes into the JWT.

## Example Flow

1.  Admin creates a user "Bob" and assigns him a role "JobSubmitter".
2.  The "JobSubmitter" role is configured to have scopes: `jobs:submit`, `jobs:read:self`.
3.  Bob logs in via `/token` endpoint with username/password.
4.  API verifies credentials, fetches Bob's role, gets scopes (`jobs:submit`, `jobs:read:self`).
5.  API generates a JWT for Bob including `{"sub": "Bob", "scopes": ["jobs:submit", "jobs:read:self"]}`.
6.  Bob makes a request to `POST /searches` (the job submission endpoint, now protected by `jobs:submit` scope).
7.  FastAPI, using the `Security` dependency, validates Bob's token and checks if `jobs:submit` is in the token's `scopes` claim.
8.  If valid, the request proceeds. If Bob tries to access `GET /researchers` (protected by `researchers:read:all`), and his token doesn't have this scope, FastAPI returns a 403 Forbidden error.

## Conclusion

Implementing API scopes provides a robust and flexible way to manage granular permissions. It requires changes in token generation (to include scopes) and endpoint protection (to check for required scopes). This design is conceptual and would need careful implementation in `auth.py` and endpoint definitions.
```
