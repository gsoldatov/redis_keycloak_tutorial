class TokenCache:
    """ Access/refresh token cache. """
    def __init__(self):
        self._store: dict[str, str] = {}
    
    def add(self, tokens: dict) -> None:
        """ Adds access & refresh tokens to the storage. """
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        self._store[access_token] = refresh_token
    
    def get(self, access_token: str) -> str | None:
        """ Returns the refresh token for the provided `access_token` or None. """
        return self._store.get(access_token, None)

    def pop(self, access_token: str) -> str | None:
        """ Pops the refresh token for the provided `access_token` from the storage. """
        return self._store.pop(access_token, None)
    
    def contains(self, access_token: str) -> bool:
        return access_token in self._store
    
    def __contains__(self, access_token: str) -> bool:
        return self.contains(access_token)
        
