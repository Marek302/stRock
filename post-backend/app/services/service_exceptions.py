"""
Exceptions pour nos services
"""

class NotFoundException(Exception):
    """Exception pour les ressources non-trouvées"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"Resource not found: {self.message}" 
    
class FileTooBigException(Exception):
    """Exception pour les fichiers trop volumineux"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"File too big: {self.message}"

class StorageException(Exception):
    """Exception pour les erreurs de stockage"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


class NsfwContentException(Exception):
    """Exception levée lorsque le contenu d'une image est détecté comme NSFW"""
    def __init__(self, message: str = "Image content is not allowed."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

