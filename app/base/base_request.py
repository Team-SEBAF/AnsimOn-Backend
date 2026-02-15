from pydantic import BaseModel, ConfigDict, Field, create_model


def snake_to_camel(snake_str: str) -> str:
    """snake_case를 camelCase로 변환

    예: user_name -> userName, email_verified -> isVerified
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class BaseRequest(BaseModel):
    """모든 Request 스키마의 기본 클래스

    - alias_generator: 필드명을 자동으로 camelCase로 매핑
    - populate_by_name: alias와 원본 필드명 둘 다 허용
    - use_enum_values: Enum을 값으로 사용
    """

    model_config = ConfigDict(
        alias_generator=snake_to_camel,
        populate_by_name=True,  # alias와 원본 필드명 둘 다 허용
        use_enum_values=True,
        # extra="forbid" 권장: 예상치 못한 필드 차단 (보안)
        # extra="allow"는 필요시에만 사용
    )


def create_partial_request(base_model: type[BaseModel], name: str) -> type[BaseModel]:
    """DTO/스키마의 모든 필드를 Optional로 변환한 Update Request 모델 생성

    - description, examples, json_schema_extra 등 메타데이터 유지
    - model_dump(exclude_unset=True)와 함께 사용하여 PATCH 스타일 업데이트에 적합
    """
    fields = {}
    for k, v in base_model.model_fields.items():
        annotation = v.annotation | None
        kwargs: dict = {"default": None, "description": v.description}
        if v.examples is not None:
            kwargs["examples"] = v.examples
        if getattr(v, "json_schema_extra", None):
            kwargs["json_schema_extra"] = v.json_schema_extra
        fields[k] = (annotation, Field(**kwargs))
    return create_model(name, __base__=BaseRequest, **fields)
