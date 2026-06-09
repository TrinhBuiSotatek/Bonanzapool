# Test Cases Reference

> Tài liệu tham khảo test case (chuyển đổi từ file `Testcase-refer-vi.xlsx`, sheet **Test Cases**).
> Mỗi test case gồm 6 trường: **ID_TC**, **Test Title/Summary**, **Pre-condition**, **Step**, **Expected Result**, **Priority**.
Một số case đã bị xóa bỏ để giảm thiểu kích thước file, hãy tham khảo cách viết, bỏ qua việc ID_TC không liền mạch.

---

## I. Màn hình: Danh sách báo cáo

### I.1. Kiểm tra UI/UX của màn hình: Danh sách báo cáo

#### I.1_01

- **Title:** Kiểm tra màn hình khởi tạo: Danh sách báo cáo
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Kiểm tra màn hình khởi tạo
- **Expected Result:**
  2. Hiển thị màn hình "Danh sách báo cáo" giống design (Refer Item I. Danh sách Báo cáo tại sheet WF/Design)
  - Thanh tìm kiếm: mặc định trống, cho phép nhập dữ liệu
  - Dropdown [Năm]
  - Dropdown [Trạng thái kỳ]
  - Dropdown [Trạng thái báo cáo]
  - Danh sách các kỳ báo cáo:
   + Hiển thị đủ số báo cáo của các quý theo năm từ năm có báo cáo đến năm hiện tại
   + Các cột: Kỳ báo cáo, Trạng thái kỳ báo cáo
   + Được sắp xếp từ mới nhất đến cũ nhất theo kỳ báo cáo
  - Trong từng kỳ báo cáo, gồm:
   + Các cột: Mã báo cáo, Tên dự án, Ngày cập nhật/nộp, Trạng thái báo cáo, Hành động
   + Được sắp xếp từ mới nhất đến cũ nhất theo cột Ngày cập nhật/Nộp
  - Phân trang theo kỳ báo cáo:
   + Default: 10 kỳ báo cáo / trang
   + Dropdown chọn số kỳ hiển thị: mặc định là 10

#### I.1_02

- **Title:** Thanh tìm kiếm: Kiểm tra hiển thị
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, kiểm tra hiển thị placeholder
- **Expected Result:** 2. Hiển thị placeholder: "Tìm kiếm theo mã báo cáo"

#### I.1_03

- **Title:** Thanh tìm kiếm: Kiểm tra maxlength
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, nhập lớn hơn 500 ký tự
- **Expected Result:** 2. Chỉ cho phép nhập tối đa 500 ký tự

#### I.1_04

- **Title:** Thanh tìm kiếm: Kiểm tra các loại ký tự cho phép nhập
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, nhập tất cả các loại ký tự
- **Expected Result:** 2. Cho phép nhập tất cả các loại ký tự

#### I.1_05

- **Title:** Dropdown [Năm]: Kiểm tra trạng thái mặc định
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại dropdown [Năm], kiểm tra trạng thái mặc định
- **Expected Result:**
  2. Mặc định hiển thị: Tất cả năm
  - Dropdown cho phép chọn nhiều giá trị bên trong

#### I.1_06

- **Title:** Dropdown [Năm]: Kiểm tra giá trị trong dropdown
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại dropdown [Năm], kiểm tra giá trị trong dropdown
- **Expected Result:**
  2. Danh sách giá trị:
   + Năm hiện tại
   + Giá trị các năm cũ phát sinh do dữ liệu khi đồng bộ hoặc phát sinh khi dùng phần mềm

#### I.1_32

- **Title:** Nút [Xem vòng đời]
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Kiểm tra hiển thị nút [Xem vòng đời] trong mỗi báo cáo
- **Expected Result:** 2. Nút hiển thị ở tất cả các báo cáo và cho phép nhấn

#### I.1_33

- **Title:** Nút [In]
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Kiểm tra hiển thị nút [In] trong mỗi báo cáo
- **Expected Result:** 2. Nút hiển thị ở tất cả các báo cáo và cho phép nhấn

#### I.1_34

- **Title:** Nút [Export]
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Kiểm tra hiển thị nút [Export] trong mỗi báo cáo
- **Expected Result:** 2. Nút hiển thị ở tất cả các báo cáo và cho phép nhấn

#### I.1_35

- **Title:** Kiểm tra UI màn hình: Danh sách báo cáo
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Kiểm tra UI trên màn hình
- **Expected Result:**
  2. Hiển thị màn hình "Danh sách báo cáo" giống design (Refer Item I. Danh sách Báo cáo tại sheet WF/Design)
  - Tên các item được hiển thị đầy đủ thông tin đúng như mô tả trong thiết kế màn hình, không có text sai hoặc bị chồng lấn giữa các item trên màn hình
  - Số lượng item hiển thị đầy đủ và giống với thiết kế màn hình
  - Vị trí các item giống với thiết kế màn hình
  - Font chữ, kích thước chữ, màu sắc, kiểu chữ giống với thiết kế màn hình
  - Căn chỉnh của các item giống với thiết kế màn hình

#### I.1_36

- **Title:** Kiểm tra khi zoom in/zoom out màn hình
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Thực hiện zoom in/zoom out màn hình
- **Expected Result:** 2. Layout màn hình không bị vỡ, không xảy ra bất thường

#### I.1_37

- **Title:** Kiểm tra dữ liệu với độ dài tối đa (maxlength)
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Kiểm tra dữ liệu hiển thị khi nhập đến giới hạn maxlength
- **Expected Result:** 2. Không xảy ra lỗi font chữ

#### I.1_38

- **Title:** Kiểm tra nhấn phím F5
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn phím F5
- **Expected Result:** 2. Trang được refresh thành công

#### I.1_39

- **Title:** Kiểm tra nút Back của trình duyệt
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn nút Back trên trình duyệt
- **Expected Result:** 2. Màn hình trước đó được mở

### I.2. Kiểm tra FUNC của màn hình: Danh sách Báo cáo

#### I.2_01

- **Title:** Kiểm tra chức năng của Thanh tìm kiếm: Nhập đầy đủ mã báo cáo
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, Nhập/Copy đầy đủ mã báo cáo tồn tại trong hệ thống, thuộc loại báo cáo KTCN11
  3. Nhấn Enter
- **Expected Result:** 3. Hiển thị kết quả tìm kiếm tương ứng theo mã báo cáo

#### I.2_02

- **Title:** Kiểm tra chức năng của Thanh tìm kiếm: Nhập 1 phần mã báo cáo
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, Nhập/Copy 1 phần mã báo cáo tồn tại trong hệ thống, thuộc loại báo cáo KTCN11
  3. Nhấn Enter
- **Expected Result:** 3. Hiển thị kết quả tìm kiếm tương ứng theo mã báo cáo

#### I.2_03

- **Title:** Kiểm tra chức năng của Thanh tìm kiếm: Nhập tất cả chữ hoa
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, Nhập mã báo cáo hợp lệ tất cả đều là ký tự viết hoa
  3. Nhấn Enter
- **Expected Result:** 3. Không phân biệt chữ hoa/thường, tìm kiếm và hiển thị record có mã phiếu nhập như data đã nhập

#### I.2_04

- **Title:** Kiểm tra chức năng của Thanh tìm kiếm: Nhập tất cả chữ thường
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, Nhập mã báo cáo hợp lệ tất cả đều là ký tự viết thường
  3. Nhấn Enter
- **Expected Result:** 3. Không phân biệt chữ hoa/thường, tìm kiếm và hiển thị record có mã phiếu nhập như data đã nhập

#### I.2_05

- **Title:** Kiểm tra chức năng của Thanh tìm kiếm: Nhập cả chữ hoa và chữ thường
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, Nhập mã báo cáo hợp lệ mà các ký tự viết là chữ thường và chữ hoa
  3. Nhấn Enter
- **Expected Result:** 3. Không phân biệt chữ hoa/thường, tìm kiếm và hiển thị record có mã phiếu nhập như data đã nhập

#### I.2_06

- **Title:** Kiểm tra chức năng của Thanh tìm kiếm: Nhập toàn bộ khoảng trắng
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, Nhập toàn khoảng trắng
  3. Nhấn Enter
- **Expected Result:** 3. Auto trim khoảng trắng, hiển thị tất cả dữ liệu

#### I.2_07

- **Title:** Kiểm tra chức năng của Thanh tìm kiếm: nhập khoảng trắng ở đầu và cuối mã báo cáo
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, Nhập khoảng trắng ở phía trước hoặc sau mã báo cáo
  3. Nhấn Enter
- **Expected Result:** 3. Tự động search không kèm dấu cách ở đầu và cuối  và hiển thị kết quả tìm kiếm tương ứng theo mã báo cáo

#### I.2_08

- **Title:** Kiểm tra chức năng của Thanh tìm kiếm: Kiểm tra refresh trang khi tìm kiếm
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, Nhập mã báo cáo tồn tại trong hệ thống nhưng không ở page 1
  3. Nhấn Enter
- **Expected Result:** 3. Hiển thị kết quả tìm kiếm tương ứng theo mã báo cáo

#### I.2_09

- **Title:** Kiểm tra chức năng của Thanh tìm kiếm: Tìm kiếm không có kết quả
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Tại thanh tìm kiếm, Nhập mã báo cáo không có trong danh sách
  3. Nhấn Enter
- **Expected Result:** 3. Hiển thị màn hình với nội dung: Không tìm thấy kết quả

#### I.2_10

- **Title:** Kiểm tra chức năng của dropdown [Năm]
- **Pre-condition:** _(không có)_
- **Step:** 1. Chọn 1 hoặc nhiều giá trị trong bộ lọc
- **Expected Result:** 1. Hiển thị các kỳ báo cáo của các năm đã chọn

#### I.2_11

- **Title:** Kiểm tra chức năng của dropdown [Trạng thái kỳ báo cáo]
- **Pre-condition:** _(không có)_
- **Step:** 1. Chọn 1 hoặc nhiều giá trị trong bộ lọc
- **Expected Result:** 1. Hiển thị các kỳ báo cáo có trạng thái kỳ đã chọn

#### I.2_12

- **Title:** Kiểm tra chức năng của dropdown [Trạng thái báo cáo]
- **Pre-condition:** _(không có)_
- **Step:** 1. Chọn 1 hoặc nhiều giá trị trong bộ lọc
- **Expected Result:** 1. Hiển thị các báo cáo có trạng thái báo cáo đã chọn

#### I.2_13

- **Title:** Tìm kiếm kết hợp
- **Pre-condition:** _(không có)_
- **Step:** 1. Kết hợp tất cả các điều kiện
- **Expected Result:** 1. Thực hiện tìm kiếm theo điều kiện AND với ô Tìm kiếm và tất cả các filter

## II. Màn hình: Lập báo cáo

### II.1. Kiểm tra UI/UX của màn hình: Lập báo cáo

#### II.1_01

- **Title:** Kiểm tra màn hình khởi tạo: Lập báo cáo
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn vào nút [Lập báo cáo]
  3. Kiểm tra màn hình khởi tạo: Lập báo cáo
- **Expected Result:**
  3. Hiển thị màn hình "Lập báo cáo" giống design (Refer Item II. Lập báo cáo tại sheet WF/Design)
  - Nút [Quay lại]
  - Nút [Thêm khu công nghiệp]
  - Hiển thị bảng nhập liệu gồm:
   + Hiển thị mặc định một hàng cho phép nhập liệu
   + Các cột: STT, KKT, Loại hình, Tên dự án/khu chức năng, Địa điểm, Văn bản thành lập, Tên nhà đầu tư, Quốc tịch, Tình trạng, Diện tích quy hoạch (ha), Diện tích thành lập (ha), Diện tích hoạt động (ha), VĐT NN - Đăng ký (tr.USD), VĐT NN - Thực hiện (tr.USD), VĐT TN - Đăng ký (tỷ VNĐ), VĐT TN - Thực hiện (tỷ VNĐ), Doanh thu (tr.USD), Xuất khẩu (tr.USD), Nhập khẩu (tr.USD), Nộp NS (tỷ NVĐ)
   + Icon [Xóa]
   + Dòng Tổng cộng
  - Hiển thị các nút:
   + Hủy
   + Lưu Nháp
   + Xem
   + Gửi báo cáo

#### II.1_02

- **Title:** Nút [Quay lại]
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn vào nút [Lập báo cáo]
  3. Kiểm tra hiển thị nút [Quay lại]
- **Expected Result:** 3. Cho phép nhấn

#### II.1_03

- **Title:** Nút [Thêm khu công nghiệp]
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn vào nút [Lập báo cáo]
  3. Kiểm tra hiển thị nút [Quay lại]
- **Expected Result:** 3. Cho phép nhấn

#### II.1_04

- **Title:** Kiểm tra trường dữ liệu [STT]
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn vào nút [Lập báo cáo]
  3. Kiểm tra trường dữ liệu [STT]
- **Expected Result:** 3. Luôn disable, hiển thị theo số hàng của bảng

### II.2. Kiểm tra FUNC của màn hình: Lập báo cáo

#### II.2_01

- **Title:** Kiểm tra hoạt động của nút: [Quay lại]
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn vào nút [Lập báo cáo]
  3. Nhấn vào nút [Quay lại]
- **Expected Result:** 3. Quay lại màn hình: Danh sách báo cáo

#### II.2_02

- **Title:** Kiểm tra hoạt động của nút: [Thêm khu công nghiệp]
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn vào nút [Lập báo cáo]
  3. Nhấn vào nút [Thêm khu công nghiệp]
- **Expected Result:** 3. Thêm 1 dòng trống mới ở cuối bảng (trên dòng tổng)

#### II.2_03

- **Title:** Kiểm tra validate của trường: KKT
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn vào nút [Lập báo cáo]
  3. Để trống trường: KKT
  4. Nhấn vào nút [Lưu nháp]
- **Expected Result:** 4. Hiển thị lỗi dưới chân trường dữ liệu: "Trường bắt buộc"

#### II.2_04

- **Title:** Kiểm tra validate của trường: KKT
- **Pre-condition:** _(không có)_
- **Step:**
  1. Nhấn vào mục "KTCN11" trên menu bar
  2. Nhấn vào nút [Lập báo cáo]
  3. Để trống trường: KKT
  4. Nhấn vào nút [Gửi báo cáo]
- **Expected Result:** 4. Hiển thị lỗi dưới chân trường dữ liệu: "Trường bắt buộc"