from .utils import check_db
from .config import db_path

check_db(*[x for x in vars(db_path).values()])
