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
                            "title": "카톡 및 메세지 수신",
                            "description": "피해자가 스토킹범으로부터 카카오톡 및 문자 메시지를 반복적으로 수신하였다. 메시지 내용에는 심한 협박과 위협적인 표현이 포함되어 있었으며, 피해자는 극심한 불안과 공포를 느꼈다. 수신 시각은 2026년 2월 12일 오전 11시 30분경이었다.",
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
                            "title": "주거 인근 협박 경고장",
                            "description": "피해자 주거지 인근에 협박성 경고장이 배포되었다. 경고장에는 피해자의 개인정보가 노출되어 있었으며, 주변 주민들에게 피해자를 악의적으로 묘사하는 내용이 포함되어 있었다. 이로 인해 피해자는 이웃에 대한 부담감과 사회적 불안을 겪었다.",
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
                            "title": "거절 의사 전달",
                            "description": "피해자가 스토킹범에게 명확한 거절 의사를 전달하였다. 문자 메시지를 통해 더 이상의 연락을 원하지 않음을 명시하며, 법적 대응을 예고하였다. 이는 피해자가 스스로를 보호하기 위해 취한 적극적인 조치였다.",
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
                            "title": "야간 협박 문자",
                            "description": "새벽 시간대에 반복적인 협박성 문자가 수신되었다. 메시지 내용은 피해자의 생명을 위협하는 수준이었으며, 피해자는 극심한 공포로 인해 수면을 취할 수 없었다. 이는 명백한 정신적 위협에 해당한다.",
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
                            "title": "블랙박스 영상",
                            "description": "피해자 차량 블랙박스에 스토킹범의 추적 장면이 녹화되었다. 영상에는 피해자 차량을 약 20분간 계속 추적하는 스토킹범의 차량이 명확히 보이며, 이는 스토킹의 심각성을 입증하는 결정적 증거가 된다.",
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
                            "title": "카카오톡 대화 기록",
                            "description": "피해자와 스토킹범 간의 카카오톡 대화 기록이다. 스토킹범은 피해자의 거절에도 불구하고 지속적으로 연락을 시도하였으며, 피해자의 심리적 상태를 악화시키는 발언을 반복하였다. 대화 내용에는 성적 모욕적 표현도 포함되어 있다.",
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
                            "description": "스토킹범이 보낸 음성 메시지의 녹음 파일이다. 음성에는 피해자를 향한 욕설과 협박이 포함되어 있으며, 총 길이는 약 3분 20초이다. 이 증거는 스토킹범의 위협적 의도를 명확히 보여준다.",
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
                            "title": "출근길 추적 사진",
                            "description": "피해자가 출근하는 길에 스토킹범이 촬영한 것으로 추정되는 사진이다. 사진에는 피해자의 일상 동선이 파악되었음을 보여주는 위치 정보가 포함되어 있으며, 이는 피해자에 대한 지속적인 감시가 이루어졌음을 의미한다.",
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
                            "title": "퇴근길 접근 시도",
                            "description": "피해자가 퇴근하는 길에 스토킹범이 직접 접근을 시도한 사건이다. 피해자는 스토킹범을 피해 달아났으며, 근처 편의점에 들어가 직원에게 도움을 요청하였다. 이는 신체적 접촉 가능성을 보여주는 심각한 사건이다.",
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
                            "title": "협박 이메일",
                            "description": "스토킹범이 피해자에게 보낸 협박성 이메일이다. 이메일에는 피해자의 직장과 가족을 대상으로 한 간접적 위협이 포함되어 있었으며, 피해자는 이로 인해 직장 생활에 심각한 지장을 겪었다. 이메일 발송 시각은 2026년 2월 20일 오전 11시이다.",
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
                            "title": "SNS 스토킹 사례",
                            "description": "스토킹범이 피해자의 SNS 계정을 통해 피해자의 일상을 지속적으로 추적한 증거이다. 스토킹범은 피해자의 게시물에 즉시 반응하며, 피해자가 차단한 후에도 부계정을 만들어 접근을 시도하였다. 이는 사이버 스토킹의 전형적인 사례이다.",
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
                            "title": "경찰 신고 접수",
                            "description": "피해자가 스토킹 피해를 경찰에 신고한 접수 문서이다. 신고서에는 지금까지 수집된 증거 목록과 스토킹범에 대한 제한접근명령 신청 의사가 포함되어 있다. 이는 피해자가 법적 대응을 본격화한 시점을 보여준다.",
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
                            "title": "추가 협박 문자",
                            "description": "경찰 신고 이후에도 스토킹범이 보낸 추가 협박 문자이다. 스토킹범은 피해자의 신고 사실을 인지하고 오히려 더욱 공격적인 메시지를 보내기 시작했으며, 이는 스토킹범의 위험성을 보여준다.",
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
                            "description": "스토킹 피해 상담 시 작성된 기록 파일이다. 피해자의 진술과 상담 내용이 문서로 정리되어 있으며, 사건의 경과를 파악하는 데 중요한 자료가 된다.",
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
    # EVIDENCE_ID_9: 퇴근길 접근 시도 (INCIDENT_LOG 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_9,
        "index": 1,
        "referenced_evidence_id": UUID("2c504997-7042-4ac6-a8fe-cf42c31fbea4"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.INCIDENT_LOG,
        "file_type": FileType.DOCUMENT,
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
    # EVIDENCE_ID_12: 경찰 신고 접수 (INCIDENT_LOG 1)
    {
        "timeline_evidence_id": EVIDENCE_ID_12,
        "index": 1,
        "referenced_evidence_id": UUID("27556c3d-ad16-44f0-9a64-5bc28b0d1521"),
        "is_original_evidence": True,
        "evidence_type": EvidenceType.INCIDENT_LOG,
        "file_type": FileType.DOCUMENT,
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
