import importlib.util
import plistlib
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("filesentry_macos",ROOT/"sentry.py")
sentry=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sentry)

class FileSentryMacTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        sentry.CACHE_DIR=self.root/"cache"

    def tearDown(self):
        sentry.cleanup_previews()
        self.temp.cleanup()

    def make_zip(self,name="sample.zip"):
        path=self.root/name
        plist=plistlib.dumps({
            "Label":"com.test.persistence",
            "Program":"/tmp/test",
            "RunAtLoad":True,
        })
        with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("../escape.txt","nothing executes")
            zf.writestr("Library/LaunchAgents/com.test.persistence.plist",plist)
            zf.writestr("notes.txt","hello from FileSentry")
        return path

    def test_scan_flags_escape_and_persistence(self):
        path=self.make_zip()
        entries,findings,risk=sentry.scan_archive(path)
        categories={item.category for item in findings}
        self.assertEqual(risk,"CRITICAL")
        self.assertIn("Extraction Escape",categories)
        self.assertIn("LaunchAgent",categories)
        self.assertIn("Automatic Execution",categories)
        self.assertEqual(len(entries),3)

    def test_preview_uses_random_private_text_files(self):
        path=self.make_zip()
        entries,_,_=sentry.scan_archive(path)
        entry=next(item for item in entries if item.name=="notes.txt")
        with mock.patch.object(sentry.subprocess,"Popen") as popen:
            first=sentry.open_preview(path,entry)
            second=sentry.open_preview(path,entry)
        self.assertIn("Opened safe text preview",first)
        self.assertIn("Opened safe text preview",second)
        files=list(sentry.CACHE_DIR.glob("preview-*.txt"))
        self.assertEqual(len(files),2)
        self.assertNotEqual(files[0].name,files[1].name)
        for preview in files:
            self.assertEqual(stat.S_IMODE(preview.stat().st_mode),0o400)
            text=preview.read_text(encoding="utf-8")
            self.assertIn("FileSentry SAFE PREVIEW",text)
            self.assertIn("hello from FileSentry",text)
        popen.assert_called()

    def test_cleanup_removes_only_preview_files(self):
        sentry.prepare_cache()
        preview=sentry.CACHE_DIR/"preview-old.txt"
        keep=sentry.CACHE_DIR/"keep.txt"
        preview.write_text("old")
        keep.write_text("keep")
        sentry.cleanup_previews()
        self.assertFalse(preview.exists())
        self.assertTrue(keep.exists())

if __name__=="__main__":
    unittest.main()
