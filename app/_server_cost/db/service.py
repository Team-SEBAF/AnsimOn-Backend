from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app._server_cost.db import utils as db_utils
from app._server_cost.schemas import InfraStatusResponse


class ServerCostDbService:
    def start_db(self) -> None:
        db = db_utils.get_rds_instance_by_tags()
        db_id = db["DBInstanceIdentifier"]
        status = db["DBInstanceStatus"]

        if status == "stopped":
            db_utils.get_rds_client().start_db_instance(DBInstanceIdentifier=db_id)

    def stop_db(self) -> None:
        db = db_utils.get_rds_instance_by_tags()
        db_id = db["DBInstanceIdentifier"]
        status = db["DBInstanceStatus"]

        if status == "available":
            db_utils.get_rds_client().stop_db_instance(DBInstanceIdentifier=db_id)

    def get_db_connection_status(self, db: Session) -> InfraStatusResponse:
        try:
            db.execute(text("SELECT 1"))
            return InfraStatusResponse(status="available")
        except OperationalError:
            return InfraStatusResponse(status="unavailable")


server_cost_db_service = ServerCostDbService()
