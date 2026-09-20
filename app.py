import os
from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from extensions import db, bcrypt, jwt
from routes.auth_routes import auth_bp
from models.stats import UserStats  # noqa: F401  (table register hone ke liye import zaroori hai)
from routes.stats_routes import stats_bp
from routes.code_routes import code_bp
from routes.profile_routes import profile_bp
from models.friendship import Friendship
from routes.friend_routes import friend_bp

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Secret key env variable se aayegi. Default sirf local development ke liye hai,
# deploy karte time JWT_SECRET_KEY zaroor set karna.
app.config['JWT_SECRET_KEY'] = os.environ.get(
    'JWT_SECRET_KEY',
    'dev-only-secret-change-me-before-deploying-1234567890'
)

# Default 15 minute hota hai, isliye user baar-baar logout ho jata tha
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)

# Extensions initialize
db.init_app(app)
bcrypt.init_app(app)
jwt.init_app(app)
CORS(app)

# Blueprint register
app.register_blueprint(auth_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(code_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(friend_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # debug sirf tab ON jab FLASK_DEBUG=1 set ho
    app.run(host="0.0.0.0",
            port=5000,
            debug=True)