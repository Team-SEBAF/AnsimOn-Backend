import logging

logger = logging.getLogger(__name__)


def test_integration_setup_ready(integration_context: dict[str, str]):
    logger.info("access_token: %s", integration_context["access_token"])
    logger.info("user_sub: %s", integration_context["user_sub"])
    logger.info("complaint_id: %s", integration_context["complaint_id"])
