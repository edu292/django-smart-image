import hashlib
from pathlib import Path

from django.core.files import File
from django.core.files.storage import FileSystemStorage


class HashedFileSystemStorage(FileSystemStorage):
    def _save(self, name, content: File):
        original_filepath = Path(name)
        hasher = hashlib.blake2b(digest_size=16)
        for chunck in content.chunks():
            hasher.update(chunck)

        hash = hasher.hexdigest()
        hashed_filepath = original_filepath.parent / Path(hash + original_filepath.suffix)
        return super()._save(hashed_filepath, content)
