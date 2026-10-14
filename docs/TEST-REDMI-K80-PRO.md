# Test trực tiếp: Redmi K80 Pro (miro) — China ROM

## 0. Giới hạn và an toàn

Đây là POC để **kiểm chứng giả thuyết**, không phải bản Việt hóa hoàn chỉnh.
Chưa có thiết bị thật để test. Theme có thể **không được cho nhập** hoặc **không đổi chữ**.

- Không unlock, root, flash, ghi phân vùng, sửa APK hay tắt cơ chế bảo vệ ROM.
- Nên ghi lại tên theme mặc định trước khi thay. Sao lưu các thiết lập cần thiết.
- Không áp dụng thành phần màn hình khóa từ theme khác; POC chỉ có `com.android.settings`.
- Không cài các Theme Manager sửa đổi hoặc dùng hướng dẫn vô hiệu hóa xác thực.
- Nếu Theme Manager không cho nhập MTZ: ghi là **T02 = THẤT BẠI / chưa tương thích**, không cưỡng ép.

## 1. Thu thập thông số trước khi test

Trên máy: Cài đặt > Giới thiệu điện thoại, ghi bản OS (ví dụ `OS3.0.xxx.0.WOMCNXM`), Android, bản Theme Manager.
Trên PC: cài **Android Platform Tools** chính thức, bật Developer options và USB debugging; chỉ cấp quyền cho máy tính tin cậy.

```sh
adb devices
python tools/device_probe.py
```

Nếu dùng Windows, nhấp đúp `probe_windows.bat`. Công cụ tạo `reports/device_info.json`, chỉ thu thông số firmware/ứng dụng, **không thu serial/IMEI/tài khoản**.

## 2. Đối chiếu tên tài nguyên thực tế (để tránh false negative)

Các ID `settings_label` và `settings_label_launcher` lấy từ nền AOSP, **không bảo đảm còn dùng trên bản Xiaomi**. Để xác minh:

```sh
adb shell pm path com.android.settings
```

Lệnh trả về một hoặc nhiều dòng `package:/.../Settings.apk` (đường dẫn thực tế tùy máy). Dùng `adb pull '<duong-dan-APK>' Settings.apk` để lấy APK của chính máy **nếu hệ thống cho phép đọc**. Dùng Apktool để giải mã tài nguyên ra thư mục cục bộ:

```sh
apktool d -f Settings.apk -o Settings_decoded
python tools/mtz_tool.py compare Settings_decoded/res/values/strings.xml --csv translations.csv
```

Nếu các ID có thật, đổi cột `status` trong CSV thành `apk_confirmed`; rồi có thể build bằng `--only-apk-confirmed`. Nếu không thấy, tìm ID thực tế và cập nhật CSV. `compare` kiểm tra **ID tồn tại trong XML**, không xác minh engine themes có quyền thay chuỗi.

**Lưu ý:** APK/ROM trích xuất có thể chứa tài nguyên có bản quyền; chỉ dùng phục vụ kiểm thử trên thiết bị sở hữu/quản lý hợp pháp, không đưa APK vào gói dự án chia sẻ công khai.

## 3. Import theme và quan sát

1. Chép `dist/ViHoa-K80Pro-POC-v0.1.mtz` vào bộ nhớ điện thoại (USB MTP hoặc `adb push dist/ViHoa-K80Pro-POC-v0.1.mtz /sdcard/Download/`).
2. Vào Themes (主题) > My themes (我的) > Import (导入), **nếu app đang có chức năng Import**. Nếu không có, có thể mở gói bằng Xiaomi Theme Editor chính thức nếu phiên bản editor cho phép áp dụng trực tiếp. Đừng dựa vào đường dẫn menu cố định vì UI khác theo phiên bản.
3. Nếu theme được nhận, áp dụng **riêng thành phần system** nếu giao diện cho chọn. Chuyển tới Cài đặt (设置) và kiểm tra chữ tiêu đề/nhãn Cài đặt; làm tương tự sau khi restart (nếu import thành công).
4. Chuyển về Default (默认) trong Themes sau khi kiểm tra.
5. Điền `reports/ket-qua-test.csv`: T01–T07, `DAT` hoặc `KHONG_DAT` hoặc `CHUA_TEST`; ghi ghi chú chi tiết.

## 4. Cách diễn giải

- Nếu T02 lỗi: chưa chứng minh tài nguyên không thay được. Có thể do import policy/metadata.
- Nếu T02 đạt, T04/T05 lỗi: chưa chứng minh engine không hỗ trợ string; có thể ID sai, cache, module bị bỏ qua hoặc tài nguyên không overlay-able.
- Nếu T04/T05 đạt: **có bằng chứng một/một số chuỗi hệ thống thay được trên cấu hình ROM đó**, chưa phải tất cả app.
- Nếu T06 lỗi: lưu ý theme có thể được áp dụng tạm thời.

## 5. Metadata dự phòng

Metadata hiện dùng `uiVersion=17`, `miuiAdapterVersion=5.0` — giá trị do cộng đồng HyperOS 3 báo cáo, không phải đặc tả chính thức cho K80 Pro.
Chỉ khi việc import bị từ chối, có thể so sánh với một theme **được export hợp pháp từ cùng phiên bản Theme Manager** rồi điều chỉnh tham số build:

```sh
python tools/mtz_tool.py build --csv translations.csv --out dist/POC-alternative.mtz --ui-version 17 --adapter-version 3.2
```

Không tự ý chỉnh file nội bộ có bảo vệ hay nội dung hệ thống. Nếu thông báo chặn theme bên thứ ba thì ghi lại kết quả; không vượt qua chặn.
