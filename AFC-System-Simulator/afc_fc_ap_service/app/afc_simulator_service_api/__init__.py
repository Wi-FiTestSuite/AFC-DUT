from flask import Blueprint

afc_simulator_api_blueprint = Blueprint(
    "afc_simulator", __name__, url_prefix="/afc-fc-ap-api"
)
from . import routes
