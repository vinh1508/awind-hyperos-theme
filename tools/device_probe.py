#!/usr/bin/env python3
"""Read-only ADB probe; never collects serial number, accounts, IMEI, logs or files."""
import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROPERTIES = [
    'ro.product.device',
    'ro.product.model',
    'ro.build.version.release',
    'ro.build.version.incremental',
    'ro.build.version.sdk',
    'ro.miui.ui.version.name',
    'ro.mi.os.version.name',
]
PACKAGES = ['com.android.settings', 'com.android.thememanager', 'com.android.systemui']


def run(*args):
    p = subprocess.run(['adb', *args], capture_output=True, text=True, timeout=18)
    if p.returncode:
        raise RuntimeError('ADB lỗi khi chạy ' + ' '.join(args) + ': ' + p.stderr.strip())
    return p.stdout.strip()


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--out', type=Path, default=Path('reports/device_info.json'))
    args = a.parse_args()
    if not shutil.which('adb'):
        print('Chưa tìm thấy adb. Cài Android Platform Tools và mở USB debugging.')
        return 2
    try:
        state = run('get-state')
        if state != 'device':
            raise RuntimeError('ADB chưa kết nối ở trạng thái device')
        props = {key: run('shell', 'getprop', key) for key in PROPERTIES}
        packages = {}
        for pkg in PACKAGES:
            text = run('shell', 'pm', 'path', pkg)
            packages[pkg] = bool(text.startswith('package:'))
        report = {
            'probe_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'read_only': True, 'properties': props, 'packages_present': packages,
            'notes': 'Không chứa serial, tài khoản, IMEI, đường dẫn tập tin riêng tư',
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('Đã lưu:', args.out)
        print('Mã máy:', props.get('ro.product.device') or '(không đọc được)')
        print('ROM:', props.get('ro.build.version.incremental') or '(không đọc được)')
        if props.get('ro.product.device') != 'miro':
            print('CẢNH BÁO: Máy trả về mã khác miro, không kết luận Redmi K80 Pro.')
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print('LỖI:', exc)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
