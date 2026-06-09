# Test Cases Reference (English)

> Reference test case document for **English-language projects** (converted from `Testcase-refer-en.xlsx`, sheets **GUI** and **FUNCTION**).
> Each test case has 6 fields: **TC ID**, **Test Title/Summary**, **Pre-condition**, **Test Steps**, **Expected Result**, **Priority**.
Một số case đã bị xóa bỏ để giảm thiểu kích thước file, hãy tham khảo cách viết, bỏ qua việc ID_TC không liền mạch.

---

## I. Screen: Edit Material popup (UC-16)

### I.1. UI/UX verification — Edit Material popup

#### TC_UC-16_GUI_01

- **Title:** Verify Edit Material popup layout matches design mockup — Big Banner type
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for a Big Banner type material.
- **Step:** 1. Compare the popup layout against the design mockup "Edit Material screen.png".
- **Expected Result:**
  1. The popup layout matches the mockup:
  - "소재 수정" popup title is displayed correctly.
  - All fields (소재 ID, 관리 타이틀, 노출여부, 타이틀, 서브 타이틀, 이미지, 작성자 정보) are positioned as per mockup.
  - [저장하기], [닫기], [상위 광고그룹 이동], [미리보기] buttons are positioned correctly.
  - Font sizes, colors, and spacing match the design specification.
- **Priority:** Low

#### TC_UC-16_GUI_02

- **Title:** Verify Edit Material popup layout matches design mockup — Highlight Quick Menu type
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for a Highlight Quick Menu type material.
- **Step:** 1. Compare the popup layout against the design mockup "Edit Material - Highlight quick menu_screen.png".
- **Expected Result:**
  1. The popup layout matches the mockup:
  - Fields: 소재 ID, 관리 타이틀, 노출여부, 타이틀, 이미지, 작성자 정보.
  - No [미리보기 (Preview)] button.
  - All element positions, colors, spacing, and fonts match.
- **Priority:** Low

#### TC_UC-16_GUI_03

- **Title:** Verify Edit Material popup layout matches design mockup — Appsplash type
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for an Appsplash type material.
- **Step:** 1. Compare the popup layout against the design mockup "Edit Material - Appsplash_screen.png".
- **Expected Result:**
  1. The popup layout matches the mockup:
  - Fields: 소재 ID, 관리 타이틀, 노출여부, 타이틀, 앱 스플래시 배너, 작성자 정보.
  - [이미지 수정] and [동영상 수정] buttons are shown.
  - All element positions, colors, spacing, and fonts match.
- **Priority:** Low

#### TC_UC-16_GUI_04

- **Title:** Verify Edit Material popup layout matches design mockup — Funnel Banner type
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for a Funnel Banner type material.
- **Step:** 1. Compare the popup layout against the design mockup "Edit Material - funnel banner.png".
- **Expected Result:**
  1. The popup layout matches the mockup:
  - Fields: 소재 ID, 관리 타이틀, 노출여부, 타이틀, 서브 타이틀, 디스플레이 유형 이미지, 네이티브 유형 이미지, 작성자 정보.
  - Two separate image sections with individual Modify/Remove buttons.
  - All element positions, colors, spacing, and fonts match.
- **Priority:** Low

#### TC_UC-16_GUI_05

- **Title:** Verify Edit Material popup layout matches design mockup — Fan Banner type
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for a Fan Banner type material.
- **Step:** 1. Compare the popup layout against the design mockup "Edit Material - Fan banner.png".
- **Expected Result:**
  1. The popup layout matches the mockup:
  - Fields: 소재 ID, 관리 타이틀, 노출여부, 판 명, 작성자 정보.
  - No image upload section.
  - All element positions, colors, spacing, and fonts match.
- **Priority:** Low

#### TC_UC-16_GUI_06

- **Title:** Verify character counter display updates in real-time for Title field
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for a Big Banner type.
- **Step:**
  1. Clear the "타이틀 (Title)" field.
  2. Input characters one by one.
  3. Observe the character counter.
- **Expected Result:** 3. The counter updates in real-time, displaying "N/22자" where N matches the current number of characters typed.
- **Priority:** Low

#### TC_UC-16_GUI_07

- **Title:** Verify Author Information section displays correctly in read-only state
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for any type.
- **Step:**
  1. Observe the "작성자 정보 (Author Information)" section.
  2. Try to click/edit any values in this section.
- **Expected Result:**
  1. Display 4 labels: 작성자명, 작성일시, 수정자명, 수정일시 with correct values and formatting (YYYY-MM-DD HH:mm for dates).
  2. All fields are read-only. Cannot be modified by clicking or typing.
- **Priority:** Low

#### TC_UC-16_GUI_08

- **Title:** Verify Material ID is displayed as read-only and cannot be edited
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for any type.
- **Step:**
  1. Observe the "소재 ID (Material ID)" field.
  2. Try to click on or modify the Material ID value.
- **Expected Result:**
  1. Material ID is displayed with the correct value from the record.
  2. The field is read-only. Cannot be modified.
- **Priority:** Low

#### TC_UC-16_GUI_09

- **Title:** Verify error message display style for validation errors
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for a Big Banner type.
- **Step:**
  1. Clear the "타이틀 (Title)" field.
  2. Click on the [저장하기 (Save)] button.
  3. Observe the error message display.
- **Expected Result:** 3. Error message "빅배너 소재 타이틀이 등록되지 않았습니다." is displayed inline with proper styling (color, position, font) matching the design specification.
- **Priority:** Low

#### TC_UC-16_GUI_10

- **Title:** Verify toast message display for success/error notifications
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Open the Edit Material popup for a Big Banner type.
- **Step:**
  1. Upload a valid image (JPEG, 1029×900, ≤1MB).
  2. Observe the toast notification.
- **Expected Result:** 2. Success toast "이미지 업로드를 성공하였습니다." appears with proper styling, position (top/center), and auto-dismiss behavior matching the design.
- **Priority:** Low

### I.2. Functional verification — Edit Material popup

#### TC_UC-16_FUNC_01

- **Title:** Verify Edit Material popup opens correctly when 1 row is selected and [수정] button is clicked
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Navigate to 디스플레이 최적화 > 소재 관리 (Material Management) screen (UC-16).
  3. At least 1 material record exists in the list.
- **Step:**
  1. Select 1 row in the material list.
  2. Click on the [수정 (Edit)] button.
- **Expected Result:**
  2. Open the "소재 수정 (Edit Material)" popup with all fields pre-filled from the selected record:
  - "소재 ID (Material ID)": displayed, read-only.
  - "관리 타이틀 (Management Title)": enabled, pre-filled, counter "N/60자".
  - "노출여부 (Exposure Status)": radio buttons (노출/미노출), pre-selected matching the record value.
  - Type-specific fields pre-filled (Title, Subtitle, Image/Video depending on exposure type).
  - "작성자 정보 (Author Information)" section visible: 작성자명, 작성일시, 수정자명, 수정일시 displayed, all read-only.
  - [저장하기 (Save)] button: enabled.
  - [닫기 (Close)] button: enabled.
  - [상위 광고그룹 이동 (Move to top Adgroup)] button: enabled.
- **Priority:** High

#### TC_UC-16_FUNC_02

- **Title:** Verify Edit Material popup opens correctly when clicking 관리 타이틀 hyperlink in the list
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Navigate to 소재 관리 (Material Management) screen.
  3. At least 1 material record exists in the list.
- **Step:** 1. Click on a "관리 타이틀 (Management Title)" hyperlink in the material list.
- **Expected Result:** 1. Open the "소재 수정 (Edit Material)" popup for the corresponding material with all fields pre-filled from the selected record (same as TC_UC-16_FUNC_01 expected result).
- **Priority:** High

#### TC_UC-16_FUNC_03

- **Title:** Verify Edit Material popup opens correctly when clicking 메인 타이틀 hyperlink in the list
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Navigate to 소재 관리 (Material Management) screen.
  3. At least 1 material record exists with a 메인 타이틀 value.
- **Step:** 1. Click on a "메인 타이틀 (Main Title)" hyperlink in the material list.
- **Expected Result:** 1. Open the "소재 수정 (Edit Material)" popup for the corresponding material with all fields pre-filled.
- **Priority:** High

#### TC_UC-16_FUNC_04

- **Title:** Verify Edit Material popup opens correctly when clicking 서브 타이틀 hyperlink in the list
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Navigate to 소재 관리 (Material Management) screen.
  3. At least 1 material record exists with a 서브 타이틀 value.
- **Step:** 1. Click on a "서브 타이틀 (Sub Title)" hyperlink in the material list.
- **Expected Result:** 1. Open the "소재 수정 (Edit Material)" popup for the corresponding material with all fields pre-filled.
- **Priority:** High

#### TC_UC-16_FUNC_05

- **Title:** Verify pre-filled data accuracy for Big Banner (빅배너) type in Edit popup
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Navigate to 소재 관리 screen.
  3. A Big Banner material record exists.
- **Step:**
  1. Select the Big Banner material row.
  2. Click on the [수정 (Edit)] button.
- **Expected Result:**
  2. Open the Edit popup with Big Banner type-specific fields pre-filled:
  - "소재 ID": displayed, read-only.
  - "관리 타이틀": pre-filled, counter "N/60자".
  - "노출여부": pre-selected radio.
  - "타이틀 (Title)": pre-filled, counter "N/22자". Helper text: "개행은 ₩n 을 사용해주세요, ₩n 개행 앞/뒤로 10글자를 초과 할 수 없습니다".
  - "서브 타이틀 (Subtitle)": pre-filled, counter "N/18자".
  - "이미지 (Image)": existing image displayed with [이미지 수정], [이미지 제거], [미리보기] buttons.
  - "작성자 정보": 작성자명, 작성일시, 수정자명, 수정일시 read-only.
- **Priority:** High

#### TC_UC-16_FUNC_06

- **Title:** Verify pre-filled data accuracy for Highlight Quick Menu (하이라이트 퀵메뉴) type in Edit popup
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Navigate to 소재 관리 screen.
  3. A Highlight Quick Menu material record exists.
- **Step:**
  1. Select the Highlight Quick Menu material row.
  2. Click on the [수정 (Edit)] button.
- **Expected Result:**
  2. Open the Edit popup with Highlight QM type-specific fields pre-filled:
  - "타이틀 (Title)": pre-filled, counter "N/16자". Helper text: "개행은 ₩n 을 사용해주세요, ₩n 개행 앞/뒤로 10글자를 초과 할 수 없습니다".
  - "이미지 (Image)": existing image displayed with [이미지 수정], [이미지 제거] buttons (no Preview).
  - Other common fields pre-filled as per TC_UC-16_FUNC_01.
- **Priority:** High

#### TC_UC-16_FUNC_07

- **Title:** Verify pre-filled data accuracy for Appsplash (앱스플래시) type in Edit popup
- **Pre-condition:**
  1. Log in to the Bizest HO admin site.
  2. Navigate to 소재 관리 screen.
  3. An Appsplash material record with image exists.
- **Step:**
  1. Select the Appsplash material row.
  2. Click on the [수정 (Edit)] button.
- **Expected Result:**
  2. Open the Edit popup with Appsplash type-specific fields pre-filled:
  - "타이틀 (Title)": pre-filled, counter "N/60자". Helper text: "개행은 ₩n 을 사용해주세요, ₩n 개행 앞/뒤로 10글자를 초과할수 없습니다".
  - "앱 스플래시 배너 (Appsplash Banner)": existing image/video displayed with [이미지 수정], [동영상 수정] buttons.
  - Other common fields pre-filled.
- **Priority:** High
