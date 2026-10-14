# ViHoa HyperOS MTZ Lab — Redmi K80 Pro POC v0.1

**Mục đích:** kiểm tra liệu MTZ có thể thay chuỗi giao diện ứng dụng Cài đặt bằng tiếng Việt trên Redmi K80 Pro nội địa hay không. Đây là thử nghiệm, **không phải** gói Việt hóa đã hoạt động.

## Tệp có sẵn

- `dist/ViHoa-K80Pro-POC-v0.1.mtz`: MTZ thử nghiệm đã tạo, có `description.xml` và module `com.android.settings` dạng nested ZIP.
- `translations.csv`: hai khóa tiêu đề Settings dạng `candidate`, dùng để kiểm thử; chưa khớp APK K80 Pro thực tế.
- `tools/mtz_tool.py`: xây MTZ, kiểm ZIP/XML, kiểm ID so với `strings.xml` từ APKTool.
- `tools/device_probe.py`: đọc thông tin cấu hình qua ADB (read-only, không thu dữ liệu định danh).
- `reports/ket-qua-test.csv`: bảng kết quả thử trực tiếp.
- `docs/TEST-REDMI-K80-PRO.md`: hướng dẫn trên máy và cách phân biệt nguyên nhân thất bại.
- `tests/`: unit tests về cấu trúc gói và kiểm tra input.

## Tạo lại file

Cần Python 3.9+ (stdlib, không có thư viện bên ngoài):

```sh
python tools/mtz_tool.py build --csv translations.csv --out dist/ViHoa-K80Pro-POC-v0.1.mtz
python tools/mtz_tool.py inspect dist/ViHoa-K80Pro-POC-v0.1.mtz
python -m unittest discover -s tests -v
```

Windows: có thể bấm `build_windows.bat` khi đã cài Python. `probe_windows.bat` yêu cầu cài ADB trong PATH.

Nếu đã xác minh ID tài nguyên bằng Apktool, đổi trạng thái từ `candidate` sang `apk_confirmed` rồi build thêm cờ `--only-apk-confirmed`.

## Giới hạn không được hiểu nhầm

1. **Kiểm tra ZIP/XML thành công không đồng nghĩa Theme Manager chấp nhận nhập MTZ.** HyperOS 3 China có thể chỉ cho theme từ cửa hàng/đã được chấp thuận.
2. **Engine Theme có thể bỏ qua chuỗi trong `theme_values.xml`** kể cả khi XML hợp lệ và APK có ID.
3. `settings_label`, `settings_label_launcher` là ID tham khảo từ AOSP; chưa xác minh trên APK Settings của K80 Pro.
4. Dự án chỉ có bản `com.android.settings`, không can thiệp launcher, lockscreen, bootloader, root hoặc file hệ thống.
5. Bản kiểm thử để tự dùng nội bộ; việc phát hành theme công khai sẽ phụ thuộc quy định của nhà cung cấp và kết quả kiểm thử.

## Tài liệu tham chiếu

- Xiaomi Theme Editor - cấu trúc theme: https://zhuti.designer.intl.xiaomi.com/tutorial/guide/
- Xiaomi - quy định sửa chuỗi trong theme: https://zhuti.designer.xiaomi.com/docs/audit/theme.html
- Tham khảo AOSP Settings resource `settings_label`: https://android.googlesource.com/platform/packages/apps/Settings/+/android16-qpr1-release/AndroidManifest.xml
- Wiki cộng đồng cách đóng gói nested module: https://github.com/miuiandroid/MIUI-V4-Theme-XML (là MIUI cũ; chỉ tham khảo đóng gói)
- Thảo luận HyperOS 3 về uiVersion / adapter: https://4pda.to/forum/index.php?showtopic=1099404&st=1060 (thông tin cộng đồng, chưa được Xiaomi xác nhận)
- Bảng firmware Redmi K80 Pro `miro`: https://mirom.ezbox.idv.tw/en/phone/miro/roms-cn-stable/ (nguồn bên thứ ba)
