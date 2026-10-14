#!/usr/bin/env python3
"""ViHoa HyperOS: generate and inspect experimental, nested-ZIP MTZ themes.

Build success means the ZIP/XML is structurally valid, NOT that a Xiaomi device
will import the file or permit Android system string overrides.
"""
import argparse
import csv
import io
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

APP_NAME = 'ViHoa K80 Pro - POC'
VALID_PKG = re.compile(r'^(?:[a-zA-Z][\w]*\.)+[a-zA-Z][\w]*$')
VALID_KEY = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
# This experiment is limited to an allow-listed Xiaomi SYSTEM app.
SAFE_MODULES = {'com.android.settings'}
REQUIRED_COLS = ('package', 'name', 'zh_CN', 'vi_VN', 'status')


def _xmlbytes(root):
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def _zipwrite(zip_file, name, content):
    zi = zipfile.ZipInfo(name, (2026, 10, 14, 0, 0, 0))
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o644 << 16
    zip_file.writestr(zi, content)


def load_rows(csv_path, require_verified=False):
    with csv_path.open(encoding='utf-8-sig', newline='') as stream:
        rdr = csv.DictReader(stream)
        if not rdr.fieldnames or any(x not in rdr.fieldnames for x in REQUIRED_COLS):
            raise ValueError('CSV cần các cột: ' + ', '.join(REQUIRED_COLS))
        result, seen = [], set()
        for lineno, row in enumerate(rdr, 2):
            pkg, name = row['package'].strip(), row['name'].strip()
            vi, origin = (row['vi_VN'] or '').strip(), (row['zh_CN'] or '').strip()
            status = (row['status'] or '').strip().lower()
            if not pkg and not name and not vi:
                continue
            if pkg not in SAFE_MODULES or not VALID_PKG.fullmatch(pkg):
                raise ValueError(f'Dòng {lineno}: module chưa được phép thử: {pkg}')
            if not VALID_KEY.fullmatch(name):
                raise ValueError(f'Dòng {lineno}: khóa tài nguyên sai: {name}')
            if not vi or not origin:
                raise ValueError(f'Dòng {lineno}: thiếu chuỗi gốc hoặc tiếng Việt')
            if status not in {'candidate', 'apk_confirmed'}:
                raise ValueError(f'Dòng {lineno}: status chỉ nhận candidate/apk_confirmed')
            if (pkg, name) in seen:
                raise ValueError(f'Dòng {lineno}: trùng khóa {pkg}/{name}')
            seen.add((pkg, name))
            if not require_verified or status == 'apk_confirmed':
                result.append((pkg, name, vi, status))
    if not result:
        raise ValueError('Không có chuỗi nào phù hợp điều kiện build')
    return sorted(result)


def make_description(ui_version, adapter_version):
    root = ET.Element('MIUI-Theme')
    for key, value in [
        ('title', APP_NAME),
        ('designer', 'ViHoa Community Lab'),
        ('author', 'ViHoa Community Lab'),
        ('version', '0.1.0'),
        ('uiVersion', str(ui_version)),
        ('miuiAdapterVersion', adapter_version),
        ('description', 'POC kiem tra theme string override - chua xac nhan tren may that'),
    ]:
        ET.SubElement(root, key).text = value
    return _xmlbytes(root)


def make_module(items):
    root = ET.Element('MIUI_Theme_Values')
    for _pkg, key, text, _status in items:
        ET.SubElement(root, 'string', name=key).text = text
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, 'w') as zf:
        _zipwrite(zf, 'theme_values.xml', _xmlbytes(root))
    return inner.getvalue()


def build(csv_path, output, ui_version='17', adapter_version='5.0', only_apk_confirmed=False):
    if not re.fullmatch(r'\d+', str(ui_version)):
        raise ValueError('uiVersion phải là số nguyên không âm')
    if not re.fullmatch(r'\d+(?:\.\d+)?', adapter_version):
        raise ValueError('miuiAdapterVersion không hợp lệ')
    rows = load_rows(csv_path, only_apk_confirmed)
    grouped = {}
    for row in rows:
        grouped.setdefault(row[0], []).append(row)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w') as zf:
        _zipwrite(zf, 'description.xml', make_description(ui_version, adapter_version))
        for pkg, pk_rows in sorted(grouped.items()):
            _zipwrite(zf, pkg, make_module(pk_rows))
    return len(rows)


def inspect(mtz_path):
    with zipfile.ZipFile(mtz_path, 'r') as theme:
        if theme.testzip() is not None:
            raise ValueError('Lỗi CRC trong MTZ')
        names = theme.namelist()
        if not names or 'description.xml' not in names:
            raise ValueError('Không có description.xml ở root')
        if len(names) != len(set(names)):
            raise ValueError('Tên file bị lặp trong MTZ')
        descr = ET.fromstring(theme.read('description.xml'))
        if descr.tag.lower() not in ('miui-theme', 'theme'):
            raise ValueError('description.xml sai root tag')
        print('Theme:', descr.findtext('title'))
        print('uiVersion:', descr.findtext('uiVersion'))
        print('miuiAdapterVersion:', descr.findtext('miuiAdapterVersion'))
        modules = [x for x in names if x != 'description.xml']
        if not modules:
            raise ValueError('Không có module')
        for pkg in modules:
            if pkg not in SAFE_MODULES:
                raise ValueError('Module lạ trong bản POC: ' + pkg)
            with zipfile.ZipFile(io.BytesIO(theme.read(pkg))) as module:
                if module.testzip() is not None:
                    raise ValueError('Lỗi CRC module: ' + pkg)
                if 'theme_values.xml' not in module.namelist():
                    raise ValueError('Thiếu theme_values.xml: ' + pkg)
                values = ET.fromstring(module.read('theme_values.xml'))
                if values.tag != 'MIUI_Theme_Values':
                    raise ValueError('theme_values.xml sai root tag: ' + pkg)
                for item in values:
                    if item.tag != 'string' or not VALID_KEY.fullmatch(item.get('name', '')):
                        raise ValueError('Cấu trúc resource không hợp lệ')
                print(f'Module {pkg}: {len(values)} chuỗi: ' + ', '.join(x.attrib['name'] for x in values))
    print('ZIP/XML hợp lệ. CHƯA xác nhận có import/Việt hóa được trên điện thoại.')


def compare(csv_path, decoded_resources):
    """Compare tentative resource names with APKTool's *decoded* strings.xml.

    This is evidence that identifiers EXIST in an APK, not evidence that MTZ
    can replace those identifiers at runtime.
    """
    if not decoded_resources.is_file():
        raise ValueError('Cần đường dẫn strings.xml đã giải mã bằng Apktool, không phải APK nhị phân')
    root = ET.parse(decoded_resources).getroot()
    if root.tag != 'resources':
        raise ValueError('Không phải Android res/values/strings.xml')
    available = {node.attrib.get('name') for node in root if node.tag == 'string'}
    rows = load_rows(csv_path)
    count = 0
    for pkg, name, _value, _status in rows:
        found = name in available
        count += found
        print(f'{"CÓ KHÓA" if found else "KHÔNG THẤY"}: {pkg}/{name}')
    print(f'{count}/{len(rows)} khóa thấy trong tập XML này. Có thể APK có nhiều tập tài nguyên.')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Công cụ thử nghiệm đóng gói MTZ cho Redmi K80 Pro')
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('build', help='Tạo MTZ với ZIP module lồng bên trong')
    b.add_argument('--csv', type=Path, default=Path('translations.csv'))
    b.add_argument('--out', type=Path, default=Path('dist/ViHoa-K80Pro-POC-v0.1.mtz'))
    b.add_argument('--ui-version', default='17', help='Mặc định 17 (cộng đồng HyperOS 3, cần test)')
    b.add_argument('--adapter-version', default='5.0', help='Mặc định 5.0 (cần test)')
    b.add_argument('--only-apk-confirmed', action='store_true')
    i = sub.add_parser('inspect', help='Kiểm tra cấu trúc ZIP/XML của MTZ')
    i.add_argument('path', type=Path)
    c = sub.add_parser('compare', help='Đối chiếu ID trong CSV với APKTool strings.xml')
    c.add_argument('decoded_strings', type=Path)
    c.add_argument('--csv', type=Path, default=Path('translations.csv'))
    args = parser.parse_args(argv)
    try:
        if args.command == 'build':
            n = build(args.csv, args.out, args.ui_version, args.adapter_version, args.only_apk_confirmed)
            print(f'Đã tạo {args.out} ({n} chuỗi; chưa thử trên điện thoại)')
        elif args.command == 'inspect':
            inspect(args.path)
        else:
            compare(args.csv, args.decoded_strings)
    except (ValueError, OSError, zipfile.BadZipFile, ET.ParseError) as e:
        print('LỖI:', e, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
