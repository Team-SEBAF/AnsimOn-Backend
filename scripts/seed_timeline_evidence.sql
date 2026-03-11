-- 타임라인 default_data용 시드 SQL
-- user 1개 + complaint 1개 + DEFAULT_TIMELINE_EVIDENCES의 evidence_id에 맞는 각 증거 테이블 row
-- MESSAGE 3그룹(9개) + 단일 10개(VICTIM, VOICE, REPORT_RECORD, INCIDENT_LOG)
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

-- 3) evidence_messages (MESSAGE 타입) - 9개 (기존 5 + MESSAGE 그룹용 4)
-- path_segment: messages
INSERT INTO evidence_messages (message_id, complaint_id, filename, s3_key, content_type, size_bytes, width, height, created_at, updated_at) VALUES
('08e070bb-fb4e-4176-a450-375f947d1ef7', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg1.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/08e070bb-fb4e-4176-a450-375f947d1ef7/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('db9d9261-b523-4be9-9e9e-52ad6e75150e', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg2.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/db9d9261-b523-4be9-9e9e-52ad6e75150e/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('78be5c14-bfae-40a0-8bae-9159105c1748', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg3.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/78be5c14-bfae-40a0-8bae-9159105c1748/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('702eddc4-1eaf-4380-86dc-16b9bed5cf62', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg4.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/702eddc4-1eaf-4380-86dc-16b9bed5cf62/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('83f41aee-f3a7-40d0-8740-080b7b0de4d5', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg5.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/83f41aee-f3a7-40d0-8740-080b7b0de4d5/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('7c8d9e0f-1a2b-4c3d-9e5f-6a7b8c9d0e1f', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg6.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/7c8d9e0f-1a2b-4c3d-9e5f-6a7b8c9d0e1f/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('8d9e0f1a-2b3c-4d4e-0f6a-7b8c9d0e1f2a', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg7.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/8d9e0f1a-2b3c-4d4e-0f6a-7b8c9d0e1f2a/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('9e0f1a2b-3c4d-4e5f-1a7b-8c9d0e1f2a3b', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg8.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/9e0f1a2b-3c4d-4e5f-1a7b-8c9d0e1f2a3b/original', 'image/png', 102400, 800, 600, NOW(), NOW()),
('0f1a2b3c-4d5e-4f6a-2b8c-9d0e1f2a3b4c', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'msg9.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/messages/0f1a2b3c-4d5e-4f6a-2b8c-9d0e1f2a3b4c/original', 'image/png', 102400, 800, 600, NOW(), NOW());

-- 4) evidence_victims (VICTIM 타입) - 3개
-- path_segment: victims
INSERT INTO evidence_victims (victim_id, complaint_id, filename, s3_key, content_type, size_bytes, duration_seconds, created_at, updated_at) VALUES
('6de0bca2-6b96-4489-ab10-8e13033d40b0', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'victim1.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/victims/6de0bca2-6b96-4489-ab10-8e13033d40b0/original', 'image/png', 102400, NULL, NOW(), NOW()),
('6a259984-0ba4-4d5e-b27b-55fb694eecbf', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'victim2.mp4', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/victims/6a259984-0ba4-4d5e-b27b-55fb694eecbf/original', 'video/mp4', 5242880, 4, NOW(), NOW()),
('f15547c2-8278-4aa1-8422-add6ae43d368', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'victim3.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/victims/f15547c2-8278-4aa1-8422-add6ae43d368/original', 'image/png', 102400, NULL, NOW(), NOW());

-- 5) evidence_voices (VOICE 타입) - 3개
-- path_segment: voices
INSERT INTO evidence_voices (voice_id, complaint_id, filename, s3_key, content_type, size_bytes, duration_seconds, created_at, updated_at) VALUES
('457329d6-d9e9-418a-9464-65f4fc7da8f8', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice1.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/457329d6-d9e9-418a-9464-65f4fc7da8f8/original', 'image/png', 102400, NULL, NOW(), NOW()),
('a1b29641-c680-43a5-a713-fa4842469960', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice2.m4a', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/a1b29641-c680-43a5-a713-fa4842469960/original', 'audio/mp4', 204800, 17, NOW(), NOW()),
('672626d0-21ac-4f95-8711-6b67105a06f2', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'voice3.m4a', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/voices/672626d0-21ac-4f95-8711-6b67105a06f2/original', 'audio/mp4', 204800, 17, NOW(), NOW());

-- 6) evidence_report_records (REPORT_RECORD 타입) - 2개
-- path_segment: report-records
INSERT INTO evidence_report_records (report_record_id, complaint_id, filename, s3_key, content_type, size_bytes, created_at, updated_at) VALUES
('f8166b42-1ffb-4c1f-a48d-8d2234476652', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'report1.pdf', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/report-records/f8166b42-1ffb-4c1f-a48d-8d2234476652/original', 'application/pdf', 102400, NOW(), NOW()),
('3a4b5c6d-7e8f-4a9b-0c1d-2e3f4a5b6c7d', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'report2.pdf', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/report-records/3a4b5c6d-7e8f-4a9b-0c1d-2e3f4a5b6c7d/original', 'application/pdf', 102400, NOW(), NOW());

-- 7) evidence_incident_logs (INCIDENT_LOG 타입) - FILE 1개 + FORM_DATA 2개
INSERT INTO evidence_incident_logs (incident_log_id, complaint_id, name, type, created_at, updated_at) VALUES
('4b5c6d7e-8f9a-4b0c-1d2e-3f4a5b6c7d8e', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '상담 기록 1', 'FILE', NOW(), NOW()),
('2c504997-7042-4ac6-a8fe-cf42c31fbea4', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '퇴근길 접근 시도', 'FORM_DATA', NOW(), NOW()),
('27556c3d-ad16-44f0-9a64-5bc28b0d1521', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '경찰 신고 접수', 'FORM_DATA', NOW(), NOW());

-- FILE 1개 (evidence_incident_log_files)
INSERT INTO evidence_incident_log_files (incident_log_id, s3_key, content_type, size_bytes) VALUES
('4b5c6d7e-8f9a-4b0c-1d2e-3f4a5b6c7d8e', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/incident-logs/4b5c6d7e-8f9a-4b0c-1d2e-3f4a5b6c7d8e/original', 'application/pdf', 102400);

-- FORM_DATA 2개 (evidence_incident_log_form_data)
INSERT INTO evidence_incident_log_form_data (incident_log_id, date, time, location, description) VALUES
('2c504997-7042-4ac6-a8fe-cf42c31fbea4', '2026-02-18', '17:00', '퇴근길 편의점 앞', '스토킹범 접근 시도 후 신고 기록'),
('27556c3d-ad16-44f0-9a64-5bc28b0d1521', '2026-02-22', '10:00', '경찰서', '경찰 신고 접수 기록');

-- FORM_DATA attachment 1개 (2c504997)
-- path: evidences/incident-logs/attachments/{incident_log_id}/{attachment_id}/original
INSERT INTO incident_log_form_data_attachments (attachment_id, incident_log_id, filename, s3_key, content_type, size_bytes, duration_seconds, created_at, updated_at) VALUES
('9d4e5f6a-7b8c-4d9e-af01-23456789abcd', '2c504997-7042-4ac6-a8fe-cf42c31fbea4', '접근시도_사진.png', 'f47ac10b-58cc-4372-a567-0e02b2c3d479/complaints/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/evidences/incident-logs/attachments/2c504997-7042-4ac6-a8fe-cf42c31fbea4/9d4e5f6a-7b8c-4d9e-af01-23456789abcd/original', 'image/png', 102400, NULL, NOW(), NOW());
