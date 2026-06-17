# Project Configuration

> **Project:** test cho MBFS mobile
> **Created:** 2026-05-10
> **Author:** QC Lead
> **Version:** v2

Tệp này đóng vai trò là biểu mẫu cấu hình cho dự án thực tế sử dụng Framework JOYs. Hãy điền các thông tin chi tiết dưới đây để các BA, QA và các AI Agent hiểu được bối cảnh, các liên kết và môi trường của dự án đang được kiểm thử.

---

## 1. Project Overview

> **Project name:** Bonanzapool
> **Description:** Bonanzapool
> **Domain:** -none-

---

## 2. Associated Links & Resources

Cung cấp các liên kết liên quan đến dự án, không bao gồm các link môi trường.

| Resource Type    | URL / Link                                      | Note / Access Requirement                |
|------------------|-------------------------------------------------|------------------------------------------|
| **Jira Board**   | `https://[company].atlassian.net/...`           | Sprint tracking, bug reporting           |
| **Confluence**   | `https://[company].atlassian.net/...`           | PRD, Architecture, API Specs             |
| **Figma / UI**   | `https://figma.com/file/...`                    | Design mockups and design system         |
| **Git Repo**     | `https://github.com/... / https://gitlab/...`   | Source code repository                   |
| **CI/CD Pipeline**| `https://jenkins... / https://github.com/...` | Deployment and pipeline tracking         |
| **Others**       | `...`                                           | E.g., API documentation (Swagger, Postman)|

---

## 3. Environments

Cung cấp links đến các môi trường đang được sử dụng. Điều này rất quan trọng cho việc thực thi kiểm thử và ngữ cảnh kiểm thử thủ công.

| Environment | URL Endpoint                  | Database (Optional)          | Purpose                           |
|-------------|-------------------------------|------------------------------|-----------------------------------|
| **DEV**     | `https://dev.api.project.com` | `dev-db.project.internal`    | Development & initial testing     |
| **QA / Staging** | `https://qa.api.project.com` | `qa-db.project.internal` | Primary environment for QA and UAT|
| **UAT**     | `https://uat.api.project.com` | `uat-db.project.internal`    | User Acceptance Testing by clients|
| **PROD**    | `https://api.project.com`     | `prod-db.project.internal`   | Live production system            |

---

## 4. Accounts & Credentials Structure

Không cung cấp các tài khoản có quyền hạn thay đổi dữ liệu trên môi trường thực (production). Chỉ cung cấp các tài khoản kiểm thử.

| Account Type      | Username / Email Format       | Role Description                                  | Password |
|-------------------|-------------------------------|---------------------------------------------------|------------------------|
| **Admin**         | `admin_qa@project.com`        | Full access, system configuration, user management|                        |
| **Standard User** | `user_*@project.com`          | Normal consumer/customer role                     |                        |
| **Vendor/Partner**| `vendor_*@project.com`        | Third-party integration or B2B partner access     |                        |
| **Test Card / Payment** | `4242 4242 ...`               | Stripe / Payment Sandbox testing cards            |                        |

---

## 5. Third-Party Integrations / APIs

Liệt kê các dịch vụ hoặc API bên ngoài mà dự án phụ thuộc vào, những hệ thống này có thể cần cấu hình hoặc dữ liệu kiểm thử đặc biệt.

- **Payment Gateway:** [e.g., Stripe Sandbox endpoints]
- **Email Service:** [e.g., Mailgun (Testing keys)]
- **Authentication:** [e.g., Auth0, Firebase Auth]

---
