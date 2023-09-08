from dbcanlight.utils import check_db
from dbcanlight.config import db_path

check_db(*[x for x in vars(db_path).values()])
