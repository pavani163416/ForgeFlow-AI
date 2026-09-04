import os
import zipfile
import tempfile
import shutil
from typing import Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)

class SecurityViolationError(Exception):
    pass

class SecureZipExtractor:
    MAX_COMPRESSED_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_EXTRACTED_SIZE = 500 * 1024 * 1024 # 500 MB
    MAX_FILE_COUNT = 10000
    MAX_COMPRESSION_RATIO = 20  # Prevent archive bombs

    @classmethod
    def validate_and_extract(cls, zip_path: str, extract_to: str) -> Tuple[bool, str]:
        """
        Securely validates and extracts a ZIP archive to the target directory.
        Returns (success, message_or_error)
        """
        try:
            # 1. Check compressed size
            compressed_size = os.path.getsize(zip_path)
            if compressed_size > cls.MAX_COMPRESSED_SIZE:
                raise SecurityViolationError(f"Archive exceeds maximum compressed size of {cls.MAX_COMPRESSED_SIZE} bytes.")
            
            if not zipfile.is_zipfile(zip_path):
                raise SecurityViolationError("File is not a valid ZIP archive.")

            with zipfile.ZipFile(zip_path, 'r') as zf:
                infolist = zf.infolist()
                
                # 2. Check file count
                if len(infolist) > cls.MAX_FILE_COUNT:
                    raise SecurityViolationError(f"Archive exceeds maximum file count of {cls.MAX_FILE_COUNT}.")

                total_extracted_size = 0

                for info in infolist:
                    # 3. Check for absolute paths and path traversal ('..' or starting with '/' or '\')
                    # ZipFile.extract() in Python 3 handles some path traversal, but it's safer to explicitly check.
                    if info.filename.startswith('/') or info.filename.startswith('\\') or '..' in info.filename:
                        raise SecurityViolationError(f"Path traversal or absolute path detected: {info.filename}")

                    # 4. Nested archive limit (prevent zip bombs nested deeply)
                    if info.filename.lower().endswith(('.zip', '.tar', '.gz')):
                        raise SecurityViolationError(f"Nested archives are not allowed: {info.filename}")

                    # 5. Calculate running size limits
                    total_extracted_size += info.file_size
                    if total_extracted_size > cls.MAX_EXTRACTED_SIZE:
                        raise SecurityViolationError(f"Total extracted size exceeds maximum allowed of {cls.MAX_EXTRACTED_SIZE} bytes.")

                    # 6. Compression ratio check (Zip Bomb protection)
                    if info.compress_size > 0:
                        ratio = info.file_size / info.compress_size
                        if ratio > cls.MAX_COMPRESSION_RATIO:
                            raise SecurityViolationError(f"Compression ratio too high for {info.filename}, possible zip bomb.")
                            
                    # 7. Symlink rejection
                    # The upper 16 bits of external_attr hold UNIX permissions.
                    # 0xA000 indicates a symbolic link.
                    if (info.external_attr >> 16) & 0xA000 == 0xA000:
                        raise SecurityViolationError(f"Symlinks are not allowed in the archive: {info.filename}")

                # If we passed all checks, perform extraction safely
                zf.extractall(path=extract_to)
                
            return True, "Extraction successful."
            
        except SecurityViolationError as e:
            # Explicitly log security violations
            logger.warning(f"ZIP Security Violation: {str(e)}")
            return False, str(e)
        except zipfile.BadZipFile as e:
            logger.error(f"Bad ZIP file: {str(e)}")
            return False, "Archive is corrupt or invalid."
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {str(e)}")
            return False, "An unexpected error occurred during extraction."
