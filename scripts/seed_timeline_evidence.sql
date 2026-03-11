-- 타임라인 default_data용 시드 SQL
-- user 1개 + complaint 1개 + DEFAULT_TIMELINE_EVIDENCES의 evidence_id에 맞는 각 증거 테이블 row
-- s3_key: {user_sub}/complaints/{complaint_id}/evidences/{path_segment}/{evidence_id}/original

-- 1) user 1개
INSERT INTO users (user_sub, email, created_at)
VALUES (
  'f47ac10b-58cc-4372-a567-0e02b2c3d479',
  'timeline-seed@example.com',
  NOW()
);

-- 2) complaint 1개 (위 user_sub와 연결)
INSERT INTO complaints (complaint_id, user_sub, name, step, created_at, updated_at)
VALUES (
  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  'f47ac10b-58cc-4372-a567-0e02b2c3d479',
  '타임라인 시드 고소장',
  'TIMELINE',
  NOW(),
  NOW()
);

-- 3) evidence_messages (MESSAGE 타입)
-- path_segment: messages
INSERT INTO evidence_messages (message_id, complaint_id, filename, s3_key, content_type, size_bytes, width, height, created_at, updated_at) VALUES
('08e070bb-fb4e-4176-a450-375f947d1ef7', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg1.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/08e070bb-fb4e-4176-a450-375f947d1ef7/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('db9d9261-b523-4be9-9e9e-52ad6e75150e', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg2.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/db9d9261-b523-4be9-9e9e-52ad6e75150e/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('78be5c14-bfae-40a0-8bae-9159105c1748', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg3.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/78be5c14-bfae-40a0-8bae-9159105c1748/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('702eddc4-1eaf-4380-86dc-16b9bed5cf62', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg4.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/702eddc4-1eaf-4380-86dc-16b9bed5cf62/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('83f41aee-f3a7-40d0-8740-080b7b0de4d5', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg5.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/83f41aee-f3a7-40d0-8740-080b7b0de4d5/original', 'image/png', 102400, 800, 600, NOW(), NOW());

-- 4) evidence_victims (VICTIM 타입)
-- path_segment: victims
INSERT INTO evidence_victims (victim_id, complaint_id, filename, s3_key, content_type, size_bytes, duration_seconds, created_at, updated_at) VALUES
('6de0bca2-6b96-4489-ab10-8e13033d40b0', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'victim1.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/victims/6de0bca2-6b96-4489-ab10-8e13033d40b0/original', 'image/png', 102400, NULL, NOW(), NOW()),
('6a259984-0ba4-4d5e-b27b-55fb694eecbf', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'victim2.mp4', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/victims/6a259984-0ba4-4d5e-b27b-55fb694eecbf/original', 'video/mp4', 5242880, 4, NOW(), NOW()),
('f15547c2-8278-4aa1-8422-add6ae43d368', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'victim3.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/victims/f15547c2-8278-4aa1-8422-add6ae43d368/original', 'image/png', 102400, NULL, NOW(), NOW()),
('38d5cd29-fc4a-46b0-8eeb-31f781aad1e5', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'victim4.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/victims/38d5cd29-fc4a-46b0-8eeb-31f781aad1e5/original', 'image/png', 102400, NULL, NOW(), NOW());

-- 5) evidence_voices (VOICE 타입) - 이미지/음성 절반씩
-- path_segment: voices (이미지: 썸네일 후보, 음성: original)
INSERT INTO evidence_voices (voice_id, complaint_id, filename, s3_key, content_type, size_bytes, duration_seconds, created_at, updated_at) VALUES
('584f7b54-992c-4888-b1fc-f265f9b7b817', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice1.m4a', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/584f7b54-992c-4888-b1fc-f265f9b7b817/original', 'audio/mp4', 204800, 17, NOW(), NOW()),
('457329d6-d9e9-418a-9464-65f4fc7da8f8', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice2.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/457329d6-d9e9-418a-9464-65f4fc7da8f8/original', 'image/png', 102400, NULL, NOW(), NOW()),
('3ae78a06-8fb1-43ab-af55-032230585c94', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice3.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/3ae78a06-8fb1-43ab-af55-032230585c94/original', 'image/png', 102400, NULL, NOW(), NOW()),
('b0904cd6-edee-4908-8054-1f55245fb89d', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice4.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/b0904cd6-edee-4908-8054-1f55245fb89d/original', 'image/png', 102400, NULL, NOW(), NOW()),
('bdc2123f-668f-4ae1-b49b-1b53710eb6b8', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice5.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/bdc2123f-668f-4ae1-b49b-1b53710eb6b8/original', 'image/png', 102400, NULL, NOW(), NOW()),
('a1b29641-c680-43a5-a713-fa4842469960', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice6.m4a', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/a1b29641-c680-43a5-a713-fa4842469960/original', 'audio/mp4', 204800, 17, NOW(), NOW()),
('95d9b3ae-947a-458e-a7c4-767a6418ca8e', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice7.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/95d9b3ae-947a-458e-a7c4-767a6418ca8e/original', 'image/png', 102400, NULL, NOW(), NOW()),
('74cccae8-5b38-4485-bf7c-eff37faa657e', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice8.m4a', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/74cccae8-5b38-4485-bf7c-eff37faa657e/original', 'audio/mp4', 204800, 17, NOW(), NOW()),
('3567e0ea-1593-4bf9-8fcb-24924b04fd81', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice9.m4a', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/3567e0ea-1593-4bf9-8fcb-24924b04fd81/original', 'audio/mp4', 204800, 17, NOW(), NOW()),
('672626d0-21ac-4f95-8711-6b67105a06f2', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice10.m4a', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/672626d0-21ac-4f95-8711-6b67105a06f2/original', 'audio/mp4', 204800, 17, NOW(), NOW()),
('ffc7fa7b-8022-45cc-bbc0-5cbc2a38d8c0', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice11.m4a', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/ffc7fa7b-8022-45cc-bbc0-5cbc2a38d8c0/original', 'audio/mp4', 204800, 17, NOW(), NOW()),
('91eaff7b-b5ed-4358-91b3-5bf2d6a0f66b', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice12.m4a', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/91eaff7b-b5ed-4358-91b3-5bf2d6a0f66b/original', 'audio/mp4', 204800, 17, NOW(), NOW());

-- 6) evidence_report_records (REPORT_RECORD 타입)
-- path_segment: report-records
INSERT INTO evidence_report_records (report_record_id, complaint_id, filename, s3_key, content_type, size_bytes, created_at, updated_at) VALUES
('3d3b4007-89bd-4926-9227-7a8f46f9093a', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'report1.pdf', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/report-records/3d3b4007-89bd-4926-9227-7a8f46f9093a/original', 'application/pdf', 102400, NOW(), NOW()),
('0abdd28e-7e14-4500-bb0a-4df16539e98b', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'report2.pdf', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/report-records/0abdd28e-7e14-4500-bb0a-4df16539e98b/original', 'application/pdf', 102400, NOW(), NOW()),
('f8166b42-1ffb-4c1f-a48d-8d2234476652', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'report3.pdf', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/report-records/f8166b42-1ffb-4c1f-a48d-8d2234476652/original', 'application/pdf', 102400, NOW(), NOW());

-- 7) evidence_incident_logs (INCIDENT_LOG 타입)
-- FILE 1개 + FORM_DATA 4개 (그 중 2개는 attachment 있음)
INSERT INTO evidence_incident_logs (incident_log_id, complaint_id, name, type, created_at, updated_at) VALUES
('38178693-ee87-4003-ba7d-3da9d47ed790', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '상담 기록 1', 'FILE', NOW(), NOW()),
('453628a0-f572-4db6-933e-07c04f1a3595', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '야간 협박 기록', 'FORM_DATA', NOW(), NOW()),
('2c504997-7042-4ac6-a8fe-cf42c31fbea4', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '퇴근길 접근 시도', 'FORM_DATA', NOW(), NOW()),
('6964e84a-dec4-46d2-a4d3-7ac7a16d4d54', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SNS 스토킹 기록', 'FORM_DATA', NOW(), NOW()),
('27556c3d-ad16-44f0-9a64-5bc28b0d1521', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '경찰 신고 접수', 'FORM_DATA', NOW(), NOW());

-- FILE 타입 1개만 (evidence_incident_log_files)
INSERT INTO evidence_incident_log_files (incident_log_id, s3_key, content_type, size_bytes) VALUES
('38178693-ee87-4003-ba7d-3da9d47ed790', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/incident-logs/38178693-ee87-4003-ba7d-3da9d47ed790/original', 'application/pdf', 102400);

-- FORM_DATA 4개 (evidence_incident_log_form_data)
INSERT INTO evidence_incident_log_form_data (incident_log_id, date, time, location, description) VALUES
('453628a0-f572-4db6-933e-07c04f1a3595', '2026-02-16', '05:30', '피해자 자택 인근', '야간 협박 문자 수신 후 상담 기록'),
('2c504997-7042-4ac6-a8fe-cf42c31fbea4', '2026-02-18', '17:00', '퇴근길 편의점 앞', '스토킹범 접근 시도 후 신고 기록'),
('6964e84a-dec4-46d2-a4d3-7ac7a16d4d54', '2026-02-20', '15:30', '온라인', 'SNS 스토킹 피해 상담 기록'),
('27556c3d-ad16-44f0-9a64-5bc28b0d1521', '2026-02-22', '10:00', '경찰서', '경찰 신고 접수 기록');

-- FORM_DATA attachment 2개 (2c504997, 6964e84a에 각 1개씩)
-- path: evidences/incident-logs/attachments/{incident_log_id}/{attachment_id}/original
INSERT INTO incident_log_form_data_attachments (attachment_id, incident_log_id, filename, s3_key, content_type, size_bytes, duration_seconds, created_at, updated_at) VALUES
('9d4e5f6a-7b8c-4d9e-af01-23456789abcd', '2c504997-7042-4ac6-a8fe-cf42c31fbea4', '접근시도_사진.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/incident-logs/attachments/2c504997-7042-4ac6-a8fe-cf42c31fbea4/9d4e5f6a-7b8c-4d9e-af01-23456789abcd/original', 'image/png', 102400, NULL, NOW(), NOW()),
('0e5f6a7b-8c9d-4e0f-a012-3456789abcde', '6964e84a-dec4-46d2-a4d3-7ac7a16d4d54', 'SNS_캡처.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/incident-logs/attachments/6964e84a-dec4-46d2-a4d3-7ac7a16d4d54/0e5f6a7b-8c9d-4e0f-a012-3456789abcde/original', 'image/png', 102400, NULL, NOW(), NOW());
