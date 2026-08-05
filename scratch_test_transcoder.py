import os
import shutil
import tempfile
import zipfile
import py7zr
import tarfile
from src.binary_resolver import BinaryResolver
from src.checksum_engine import ChecksumEngine
from src.transcoder_engine import TranscoderEngine, ArchiveEntry

def run_tests():
    print("=== STARTING ARCHIVE TRANSCODER PRO INTEGRATION TESTS ===")

    # 1. Test Binary Resolver
    resolver = BinaryResolver()
    status = resolver.get_status()
    print(f"[TEST 1] Binary Resolver Status: 7z={status['7z']['tier']}, unrar={status['unrar']['tier']}")
    assert status['7z']['tier'] is not None, "7z tier check failed"

    # 2. Setup temporary test directory & create sample files
    test_dir = tempfile.mkdtemp(prefix="atp_test_")
    try:
        sample_file1 = os.path.join(test_dir, "document.txt")
        sample_file2 = os.path.join(test_dir, "nested", "data.json")
        os.makedirs(os.path.dirname(sample_file2), exist_ok=True)

        content1 = b"Archive Transcoder Pro zero-residual streaming test payload 1.\n" * 50
        content2 = b'{"name": "test", "status": "ok", "version": "1.0.0-PROD"}\n' * 50

        with open(sample_file1, "wb") as f:
            f.write(content1)
        with open(sample_file2, "wb") as f:
            f.write(content2)

        # 3. Create initial source ZIP archive
        source_zip = os.path.join(test_dir, "source.zip")
        with zipfile.ZipFile(source_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(sample_file1, "document.txt")
            zf.write(sample_file2, "nested/data.json")

        print(f"[TEST 2] Created source ZIP archive: {os.path.basename(source_zip)} ({os.path.getsize(source_zip)} bytes)")

        engine = TranscoderEngine(resolver)

        # Inspect source archive
        entries, total_size, is_enc = engine.inspect_archive(source_zip)
        print(f"[TEST 3] Source Inspection: {len(entries)} entries, {total_size} uncompressed bytes, Encrypted={is_enc}")
        assert len(entries) == 2, f"Expected 2 entries, got {len(entries)}"

        # 4. Transcode ZIP -> 7Z
        output_7z = os.path.join(test_dir, "output.7z")
        stats_7z = engine.transcode_archive(
            input_path=source_zip,
            output_path=output_7z,
            target_format="7Z",
            compression_level="Standard",
            algorithm="LZMA2",
            verify_checksums=True
        )
        print(f"[TEST 4] Transcoded ZIP -> 7Z successfully!")
        print(f"         Ratio: {stats_7z['compression_ratio_pct']}%, Time: {stats_7z['elapsed_seconds']}s, Checksums: {len(stats_7z['checksum_sweep'])}")
        assert os.path.exists(output_7z), "7Z output file does not exist"
        assert os.path.getsize(output_7z) > 0, "7Z output file is empty"

        # 5. Transcode 7Z -> TAR.GZ
        output_targz = os.path.join(test_dir, "output.tar.gz")
        stats_tgz = engine.transcode_archive(
            input_path=output_7z,
            output_path=output_targz,
            target_format="TAR.GZ",
            compression_level="High",
            verify_checksums=True
        )
        print(f"[TEST 5] Transcoded 7Z -> TAR.GZ successfully!")
        print(f"         Ratio: {stats_tgz['compression_ratio_pct']}%, Time: {stats_tgz['elapsed_seconds']}s")
        assert os.path.exists(output_targz), "TAR.GZ output file does not exist"

        # 6. Verify unpacked payload content matching original files
        extracted_dir = os.path.join(test_dir, "extracted")
        with tarfile.open(output_targz, "r:gz") as tf:
            tf.extractall(path=extracted_dir)

        ext_doc = os.path.join(extracted_dir, "document.txt")
        with open(ext_doc, "rb") as f:
            read_c1 = f.read()
        assert read_c1 == content1, "Extracted file 1 content mismatch!"

        ext_json = os.path.join(extracted_dir, "nested", "data.json")
        with open(ext_json, "rb") as f:
            read_c2 = f.read()
        assert read_c2 == content2, "Extracted file 2 content mismatch!"

        print("[TEST 6] Payload Verification PASSED 100%! All uncompressed byte streams match perfectly.")
        print("\nALL INTEGRATION TESTS PASSED CLEANLY! [SUCCESS]")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    run_tests()
