import csv
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from mtz_tool import build, inspect, load_rows


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.csv = self.root / 'translations.csv'
        self.csv.write_text('package,name,zh_CN,vi_VN,status\n'
                            'com.android.settings,settings_label,设置,Cài đặt,candidate\n',
                            encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_round_trip(self):
        p = self.root / 'test.mtz'
        self.assertEqual(build(self.csv, p), 1)
        with ZipFile(p) as zf:
            self.assertIn('description.xml', zf.namelist())
            self.assertIn('com.android.settings', zf.namelist())
            module = self.root / 'module.zip'
            module.write_bytes(zf.read('com.android.settings'))
        with ZipFile(module) as zf:
            root = ET.fromstring(zf.read('theme_values.xml'))
            self.assertEqual(root.find('string').text, 'Cài đặt')
        inspect(p)

    def test_no_third_party_modules(self):
        self.csv.write_text('package,name,zh_CN,vi_VN,status\n'
                            'com.some.app,label,你好,Xin chào,candidate\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'chưa được phép'):
            load_rows(self.csv)

    def test_no_duplicates(self):
        with self.csv.open('a', encoding='utf-8') as fp:
            fp.write('com.android.settings,settings_label,设置,Cài đặt,candidate\n')
        with self.assertRaisesRegex(ValueError, 'trùng khóa'):
            load_rows(self.csv)

    def test_only_confirmed(self):
        with self.assertRaisesRegex(ValueError, 'Không có chuỗi'):
            load_rows(self.csv, require_verified=True)

    def test_xml_escape(self):
        self.csv.write_text('package,name,zh_CN,vi_VN,status\n'
                            'com.android.settings,settings_label,设置,"Cài đặt & trợ giúp",candidate\n',
                            encoding='utf-8')
        p = self.root / 'special.mtz'
        build(self.csv, p)
        with ZipFile(p) as outer:
            b = outer.read('com.android.settings')
        import io
        with ZipFile(io.BytesIO(b)) as inner:
            node = ET.fromstring(inner.read('theme_values.xml'))
            self.assertEqual(node.find('string').text, 'Cài đặt & trợ giúp')


if __name__ == '__main__':
    unittest.main()
