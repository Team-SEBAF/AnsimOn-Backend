"""타임라인 기본 데이터. complaint에 해당 row 없을 때 DB에 insert."""

from uuid import UUID

from app.domain.evidence.constant import EvidenceType, FileType

# timeline evidence id들 (uuid4) - timeline_evidence 더미와 매칭
EVIDENCE_ID_1 = UUID("70e13045-4192-4120-be20-bd2567ff2ed2")
EVIDENCE_ID_2 = UUID("8e71f6be-3d9a-48a8-9118-ccbe378a75e6")
EVIDENCE_ID_3 = UUID("88131a2e-b1dd-47f4-8044-e3e18de738a3")
EVIDENCE_ID_4 = UUID("ce268a44-a2d6-4538-94ea-e022dcef6391")
EVIDENCE_ID_5 = UUID("4181f31c-0bc4-4f2f-8608-e4fe8f33f40b")
EVIDENCE_ID_6 = UUID("a3a92454-8b80-400c-bdb6-0d8d7fae2fbe")
EVIDENCE_ID_7 = UUID("225c7a60-8bb5-4fa8-a5a4-b33decb3047f")
EVIDENCE_ID_8 = UUID("335db937-0e65-4b39-8a25-5eb0d0b4c861")
EVIDENCE_ID_9 = UUID("adfd9070-54f8-4c2a-8076-7641e46ecf43")
EVIDENCE_ID_10 = UUID("ddfbc9a0-cda2-4c93-ab72-162a76d0e5e4")
EVIDENCE_ID_11 = UUID("f2f98431-599f-4bad-9052-5c3fc0db62b0")
EVIDENCE_ID_12 = UUID("6988bd8d-2490-4661-b5d8-d303e5b370b3")
EVIDENCE_ID_13 = UUID("92842534-f075-4276-ad66-3ae05f4891bc")
EVIDENCE_ID_14 = UUID("5f79ac2b-9676-4568-9058-1775aaca7ddd")

DEFAULT_TIMELINE_JSON = {
    "items": [
        {
            "date": "2026-02-12",
            "events": [
                {
                    "time": "11:30",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_1),
                            "index": 1,
                            "title": "카카오톡·문자 메시지 스크린샷",
                            "description": "스토킹범으로부터 수신한 카카오톡 및 문자 메시지 캡처 4장. 협박·위협 표현이 포함된 반복적 연락 기록이다.",
                            "tags": ["REPEAT", "THREAT_COERCION"],
                            "referenced_evidence_count": 4,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
                {
                    "time": "11:45",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_2),
                            "index": 1,
                            "title": "피해 관련 사진",
                            "description": "스토킹 피해와 관련된 현장·물건 등을 촬영한 증거 사진이다.",
                            "tags": ["THREAT_COERCION", "PHYSICAL_HARM"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
                {
                    "time": "13:30",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_3),
                            "index": 1,
                            "title": "음성 메시지 관련 스크린샷",
                            "description": "스토킹범이 보낸 음성 메시지가 수신된 채팅 화면 캡처. 거절 의사 전달 후에도 지속된 연락을 보여준다.",
                            "tags": ["REFUSAL_INTENT", "REPEAT"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
            ],
        },
        {
            "date": "2026-02-16",
            "events": [
                {
                    "time": "05:30",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_4),
                            "index": 1,
                            "title": "새벽 협박 문자 스크린샷",
                            "description": "새벽 5시 30분경 수신된 협박성 문자 메시지 캡처 3장. 생명 위협 수준의 내용으로 피해자의 수면·일상을 방해하였다.",
                            "tags": ["REPEAT", "THREAT_COERCION"],
                            "referenced_evidence_count": 3,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
                {
                    "time": "08:30",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_5),
                            "index": 1,
                            "title": "블랙박스 추적 영상",
                            "description": "피해자 차량 블랙박스에 녹화된 추적 장면. 스토킹범의 차량이 피해자 차량을 따라가는 모습이 담겨 있다.",
                            "tags": ["THREAT_COERCION", "PHYSICAL_HARM"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
                {
                    "time": "14:00",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_6),
                            "index": 1,
                            "title": "카카오톡 대화 스크린샷",
                            "description": "피해자와 스토킹범 간 카카오톡 대화 캡처 2장. 거절 후에도 지속된 연락 시도와 성적·모욕적 발언이 포함되어 있다.",
                            "tags": ["REPEAT", "SEXUAL_INSULT"],
                            "referenced_evidence_count": 2,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        },
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_7),
                            "index": 2,
                            "title": "음성 메시지 녹음",
                            "description": "스토킹범이 보낸 음성 메시지 파일. 욕설과 협박이 포함되어 있으며, 위협적 의도를 보여준다.",
                            "tags": ["THREAT_COERCION", "PHYSICAL_HARM"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        },
                    ],
                },
            ],
        },
        {
            "date": "2026-02-18",
            "events": [
                {
                    "time": "09:15",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_8),
                            "index": 1,
                            "title": "추적·감시 관련 사진",
                            "description": "스토킹범이 피해자의 동선을 파악·감시한 것으로 추정되는 사진. 출근길 등 일상 경로가 노출되었음을 보여준다.",
                            "tags": ["REPEAT", "THREAT_COERCION"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
                {
                    "time": "17:00",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_9),
                            "index": 1,
                            "title": "퇴근길 접근 시도 기록",
                            "description": "2026년 2월 18일 17시, 퇴근길 편의점 앞에서 스토킹범이 직접 접근을 시도한 사건. 피해자가 달아나 편의점 직원에게 도움을 요청하였다. 현장 촬영 사진이 첨부되어 있다.",
                            "tags": ["PHYSICAL_HARM", "THREAT_COERCION"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
            ],
        },
        {
            "date": "2026-02-20",
            "events": [
                {
                    "time": "11:00",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_10),
                            "index": 1,
                            "title": "고소장·신고 관련 서류",
                            "description": "스토킹 피해 신고와 관련된 공문서. 협박 이메일, 고소장 초안, 또는 신고 접수 문서 등이 포함될 수 있다.",
                            "tags": ["THREAT_COERCION", "REPEAT"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
                {
                    "time": "15:30",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_11),
                            "index": 1,
                            "title": "추가 신고·상담 서류",
                            "description": "SNS 스토킹, 사이버 괴롭힘 등 추가 피해 사례를 정리한 서류. 상담 기록이나 증거 목록이 포함될 수 있다.",
                            "tags": ["REPEAT", "SEXUAL_INSULT"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
            ],
        },
        {
            "date": "2026-02-22",
            "events": [
                {
                    "time": "10:00",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_12),
                            "index": 1,
                            "title": "경찰 신고 접수 기록",
                            "description": "2026년 2월 22일 경찰서에서 스토킹 피해 신고 접수. 수집된 증거 목록과 제한접근명령 신청 의사가 포함되어 있다.",
                            "tags": ["REFUSAL_INTENT"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        }
                    ],
                },
                {
                    "time": "19:00",
                    "evidences": [
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_13),
                            "index": 1,
                            "title": "추가 협박 음성 메시지",
                            "description": "경찰 신고 이후에도 스토킹범이 보낸 음성 메시지. 신고 사실을 인지한 뒤 오히려 더 공격적인 내용으로, 위험성을 보여준다.",
                            "tags": ["THREAT_COERCION", "PHYSICAL_HARM", "REPEAT"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        },
                        {
                            "timeline_evidence_id": str(EVIDENCE_ID_14),
                            "index": 2,
                            "title": "상담 기록 파일",
                            "description": "스토킹 피해 상담 시 작성된 기록. 피해자 진술과 상담 내용이 문서로 정리되어 있으며, 사건 경과 파악에 중요한 자료이다.",
                            "tags": ["THREAT_COERCION", "PHYSICAL_HARM"],
                            "referenced_evidence_count": 1,
                            "has_thumbnail": False,
                            "thumbnail_url": "",
                            "duration_seconds": None,
                            "is_ai_original": True,
                        },
                    ],
                },
            ],
        },
    ]
}

# timeline_evidence 더미: MESSAGE만 그룹(여러 evidence), 나머지는 단일 evidence
# 3개 MESSAGE 그룹(EVIDENCE_ID_1:4, 4:3, 6:2) + 10개 단일(VICTIM, VOICE, REPORT_RECORD, INCIDENT_LOG)
DEFAULT_TIMELINE_EVIDENCES = [
    # EVIDENCE_ID_1: 카톡 및 메세지 (MESSAGE 그룹 4)
    {
        "timeline_evidence_id": EVIDENCE_ID_1,
        "index": 1,
        "referenced_evidence_id": UUID("08e070bb-fb4e-4176-a450-375f947d1ef7"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.MESSAGE,
        "file_type": FileType.IMAGE,
    },
    {
        "timeline_evidence_id": EVIDENCE_ID_1,
        "index": 2,
        "referenced_evidence_id": UUID("db9d9261-b523-4be9-9e9e-52ad6e75150e"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.MESSAGE,
        "file_type": FileType.IMAGE,
    },
    {
        "timeline_evidence_id": EVIDENCE_ID_1,
        "index": 3,
        "referenced_evidence_id": UUID("78be5c14-bfae-40a0-8bae-9159105c1748"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.MESSAGE,
        "file_type": FileType.IMAGE,
    },
    {
        "timeline_evidence_id": EVIDENCE_ID_1,
        "index": 4,
        "referenced_evidence_id": UUID("702eddc4-1eaf-4380-86dc-16b9bed5cf62"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.MESSAGE,
        "file_type": FileType.IMAGE,
    },
    # EVIDENCE_ID_2: 주거 인근 협박 경고장 (VICTIM 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_2,
        "index": 1,
        "referenced_evidence_id": UUID("6de0bca2-6b96-4489-ab10-8e13033d40b0"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.VICTIM,
        "file_type": FileType.IMAGE,
    },
    # EVIDENCE_ID_3: 거절 의사 전달 (VOICE 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_3,
        "index": 1,
        "referenced_evidence_id": UUID("457329d6-d9e9-418a-9464-65f4fc7da8f8"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.VOICE,
        "file_type": FileType.IMAGE,
    },
    # EVIDENCE_ID_4: 야간 협박 문자 (MESSAGE 그룹 3)
    {
        "timeline_evidence_id": EVIDENCE_ID_4,
        "index": 1,
        "referenced_evidence_id": UUID("83f41aee-f3a7-40d0-8740-080b7b0de4d5"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.MESSAGE,
        "file_type": FileType.IMAGE,
    },
    {
        "timeline_evidence_id": EVIDENCE_ID_4,
        "index": 2,
        "referenced_evidence_id": UUID("7c8d9e0f-1a2b-4c3d-9e5f-6a7b8c9d0e1f"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.MESSAGE,
        "file_type": FileType.IMAGE,
    },
    {
        "timeline_evidence_id": EVIDENCE_ID_4,
        "index": 3,
        "referenced_evidence_id": UUID("8d9e0f1a-2b3c-4d4e-0f6a-7b8c9d0e1f2a"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.MESSAGE,
        "file_type": FileType.IMAGE,
    },
    # EVIDENCE_ID_5: 블랙박스 영상 (VICTIM 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_5,
        "index": 1,
        "referenced_evidence_id": UUID("6a259984-0ba4-4d5e-b27b-55fb694eecbf"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.VICTIM,
        "file_type": FileType.VIDEO,
    },
    # EVIDENCE_ID_6: 카카오톡 대화 기록 (MESSAGE 그룹 2)
    {
        "timeline_evidence_id": EVIDENCE_ID_6,
        "index": 1,
        "referenced_evidence_id": UUID("9e0f1a2b-3c4d-4e5f-1a7b-8c9d0e1f2a3b"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.MESSAGE,
        "file_type": FileType.IMAGE,
    },
    {
        "timeline_evidence_id": EVIDENCE_ID_6,
        "index": 2,
        "referenced_evidence_id": UUID("0f1a2b3c-4d5e-4f6a-2b8c-9d0e1f2a3b4c"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.MESSAGE,
        "file_type": FileType.IMAGE,
    },
    # EVIDENCE_ID_7: 음성 메시지 녹음 (VOICE 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_7,
        "index": 1,
        "referenced_evidence_id": UUID("a1b29641-c680-43a5-a713-fa4842469960"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.VOICE,
        "file_type": FileType.AUDIO,
    },
    # EVIDENCE_ID_8: 출근길 추적 사진 (VICTIM 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_8,
        "index": 1,
        "referenced_evidence_id": UUID("f15547c2-8278-4aa1-8422-add6ae43d368"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.VICTIM,
        "file_type": FileType.IMAGE,
    },
    # EVIDENCE_ID_9: 퇴근길 접근 시도 (INCIDENT_LOG FORM_DATA)
    {
        "timeline_evidence_id": EVIDENCE_ID_9,
        "index": 1,
        "referenced_evidence_id": UUID("2c504997-7042-4ac6-a8fe-cf42c31fbea4"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.INCIDENT_LOG,
        "file_type": FileType.ETC,
    },
    # EVIDENCE_ID_10: 협박 이메일 (REPORT_RECORD 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_10,
        "index": 1,
        "referenced_evidence_id": UUID("f8166b42-1ffb-4c1f-a48d-8d2234476652"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.REPORT_RECORD,
        "file_type": FileType.DOCUMENT,
    },
    # EVIDENCE_ID_11: SNS 스토킹 사례 (REPORT_RECORD 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_11,
        "index": 1,
        "referenced_evidence_id": UUID("3a4b5c6d-7e8f-4a9b-0c1d-2e3f4a5b6c7d"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.REPORT_RECORD,
        "file_type": FileType.DOCUMENT,
    },
    # EVIDENCE_ID_12: 경찰 신고 접수 (INCIDENT_LOG FORM_DATA)
    {
        "timeline_evidence_id": EVIDENCE_ID_12,
        "index": 1,
        "referenced_evidence_id": UUID("27556c3d-ad16-44f0-9a64-5bc28b0d1521"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.INCIDENT_LOG,
        "file_type": FileType.ETC,
    },
    # EVIDENCE_ID_13: 추가 협박 문자 (VOICE 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_13,
        "index": 1,
        "referenced_evidence_id": UUID("672626d0-21ac-4f95-8711-6b67105a06f2"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.VOICE,
        "file_type": FileType.AUDIO,
    },
    # EVIDENCE_ID_14: 상담 기록 파일 (INCIDENT_LOG FILE 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_14,
        "index": 1,
        "referenced_evidence_id": UUID("4b5c6d7e-8f9a-4b0c-1d2e-3f4a5b6c7d8e"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.INCIDENT_LOG,
        "file_type": FileType.DOCUMENT,
    },
]
