from flask import Blueprint

routes_bp = Blueprint('routes', __name__)

from . import auth, team_leader, data_analyst