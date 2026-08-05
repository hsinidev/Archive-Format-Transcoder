import zlib
import hashlib
from typing import Dict, Union, BinaryIO

class ChecksumEngine:
    """
    Automated pre- and post-transcode payload integrity sweep engine.
    Calculates streaming CRC32 and SHA-256 checksums on bytes, file handles, or stream buffers.
    """
    CHUNK_SIZE = 1024 * 1024  # 1MB buffer chunk

    @classmethod
    def calculate_stream_checksums(cls, stream: BinaryIO) -> Dict[str, Union[str, int]]:
        """
        Reads a stream to completion in chunks and computes both CRC32 and SHA-256.
        Returns to original position if stream is seekable.
        """
        initial_pos = None
        if stream.seekable():
            try:
                initial_pos = stream.tell()
            except Exception:
                pass

        crc32_val = 0
        sha256_hash = hashlib.sha256()
        total_bytes = 0

        while True:
            chunk = stream.read(cls.CHUNK_SIZE)
            if not chunk:
                break
            total_bytes += len(chunk)
            crc32_val = zlib.crc32(chunk, crc32_val)
            sha256_hash.update(chunk)

        if initial_pos is not None and stream.seekable():
            try:
                stream.seek(initial_pos)
            except Exception:
                pass

        return {
            "crc32": f"{crc32_val & 0xFFFFFFFF:08X}",
            "crc32_int": crc32_val & 0xFFFFFFFF,
            "sha256": sha256_hash.hexdigest(),
            "byte_count": total_bytes
        }

    @classmethod
    def calculate_bytes_checksums(cls, buffer: bytes) -> Dict[str, Union[str, int]]:
        crc32_val = zlib.crc32(buffer) & 0xFFFFFFFF
        sha256_val = hashlib.sha256(buffer).hexdigest()
        return {
            "crc32": f"{crc32_val:08X}",
            "crc32_int": crc32_val,
            "sha256": sha256_val,
            "byte_count": len(buffer)
        }

    @classmethod
    def calculate_file_checksums(cls, file_path: str) -> Dict[str, Union[str, int]]:
        crc32_val = 0
        sha256_hash = hashlib.sha256()
        total_bytes = 0

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(cls.CHUNK_SIZE)
                if not chunk:
                    break
                total_bytes += len(chunk)
                crc32_val = zlib.crc32(chunk, crc32_val)
                sha256_hash.update(chunk)

        return {
            "crc32": f"{crc32_val & 0xFFFFFFFF:08X}",
            "crc32_int": crc32_val & 0xFFFFFFFF,
            "sha256": sha256_hash.hexdigest(),
            "byte_count": total_bytes
        }

    @classmethod
    def verify_payload_match(cls, source_stats: Dict[str, Union[str, int]], dest_stats: Dict[str, Union[str, int]]) -> bool:
        """
        Compares SHA-256 and byte counts between source payload extraction and destination archive entry.
        """
        return (
            source_stats.get("sha256") == dest_stats.get("sha256") and
            source_stats.get("byte_count") == dest_stats.get("byte_count")
        )
