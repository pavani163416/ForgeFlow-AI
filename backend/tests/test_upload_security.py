import pytest
import zipfile
import tempfile
import os
import stat
from app.services.upload_security import SecureZipExtractor

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d

def create_zip(path: str, files: dict, symlinks: dict = None):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            zf.writestr(fname, content)
            
        if symlinks:
            for link_name, target in symlinks.items():
                info = zipfile.ZipInfo(link_name)
                info.create_system = 3 # UNIX
                # 0xA000 indicates symlink, 0o777 permissions
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                zf.writestr(info, target)

def test_valid_archive(temp_dir):
    zip_path = os.path.join(temp_dir, "valid.zip")
    extract_path = os.path.join(temp_dir, "extracted")
    
    create_zip(zip_path, {"test.txt": b"Hello World", "dir/sub.txt": b"Sub content"})
    
    success, msg = SecureZipExtractor.validate_and_extract(zip_path, extract_path)
    assert success is True
    assert os.path.exists(os.path.join(extract_path, "test.txt"))
    assert os.path.exists(os.path.join(extract_path, "dir/sub.txt"))

def test_oversized_compressed_archive(temp_dir, monkeypatch):
    # Mock the MAX_COMPRESSED_SIZE to something very small to test the limit
    monkeypatch.setattr(SecureZipExtractor, 'MAX_COMPRESSED_SIZE', 10)
    
    zip_path = os.path.join(temp_dir, "oversized.zip")
    extract_path = os.path.join(temp_dir, "extracted")
    
    create_zip(zip_path, {"test.txt": b"This content is definitely larger than 10 bytes."})
    
    success, msg = SecureZipExtractor.validate_and_extract(zip_path, extract_path)
    assert success is False
    assert "exceeds maximum compressed size" in msg

def test_path_traversal_archive(temp_dir):
    zip_path = os.path.join(temp_dir, "traversal.zip")
    extract_path = os.path.join(temp_dir, "extracted")
    
    create_zip(zip_path, {"../evil.sh": b"echo hacked"})
    
    success, msg = SecureZipExtractor.validate_and_extract(zip_path, extract_path)
    assert success is False
    assert "Path traversal or absolute path detected" in msg

def test_absolute_path_archive(temp_dir):
    zip_path = os.path.join(temp_dir, "absolute.zip")
    extract_path = os.path.join(temp_dir, "extracted")
    
    create_zip(zip_path, {"/etc/passwd": b"root:x:0:0"})
    
    success, msg = SecureZipExtractor.validate_and_extract(zip_path, extract_path)
    assert success is False
    assert "Path traversal or absolute path detected" in msg
    
def test_windows_absolute_path_archive(temp_dir):
    zip_path = os.path.join(temp_dir, "win_absolute.zip")
    extract_path = os.path.join(temp_dir, "extracted")
    
    create_zip(zip_path, {"\\Windows\\System32\\evil.exe": b"payload"})
    
    success, msg = SecureZipExtractor.validate_and_extract(zip_path, extract_path)
    assert success is False
    assert "Path traversal or absolute path detected" in msg

def test_symlink_rejection(temp_dir):
    zip_path = os.path.join(temp_dir, "symlink.zip")
    extract_path = os.path.join(temp_dir, "extracted")
    
    # Create an archive with a symlink pointing to /etc/shadow
    create_zip(zip_path, {"normal.txt": b"ok"}, symlinks={"link.txt": "/etc/shadow"})
    
    success, msg = SecureZipExtractor.validate_and_extract(zip_path, extract_path)
    assert success is False
    assert "Symlinks are not allowed" in msg

def test_nested_archive_rejection(temp_dir):
    zip_path = os.path.join(temp_dir, "nested.zip")
    extract_path = os.path.join(temp_dir, "extracted")
    
    create_zip(zip_path, {"inner.zip": b"fake zip content"})
    
    success, msg = SecureZipExtractor.validate_and_extract(zip_path, extract_path)
    assert success is False
    assert "Nested archives are not allowed" in msg

def test_compression_ratio_zip_bomb(temp_dir, monkeypatch):
    # Mock ratio to 2 (normally 20)
    monkeypatch.setattr(SecureZipExtractor, 'MAX_COMPRESSION_RATIO', 2)
    
    zip_path = os.path.join(temp_dir, "bomb.zip")
    extract_path = os.path.join(temp_dir, "extracted")
    
    # Highly compressible data (lots of zeros)
    data = b"0" * 10000 
    create_zip(zip_path, {"bomb.txt": data})
    
    success, msg = SecureZipExtractor.validate_and_extract(zip_path, extract_path)
    assert success is False
    assert "Compression ratio too high" in msg
