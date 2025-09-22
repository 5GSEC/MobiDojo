from flask import Flask, render_template
from flask_socketio import SocketIO
from views.function1 import function1_bp
from views.function2 import function2_bp
from views.function3 import function3_bp
from views.function4 import function4_bp
from views.function4_1 import function4_1_bp
from views.function5 import function5_bp

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret!"
    socketio = SocketIO(app)

    @app.route('/')
    def index():
        return render_template('base.html')

    app.register_blueprint(function1_bp, url_prefix='/function1')
    app.register_blueprint(function2_bp, url_prefix='/function2')
    app.register_blueprint(function3_bp, url_prefix='/function3')
    app.register_blueprint(function4_bp, url_prefix='/function4')
    app.register_blueprint(function4_1_bp, url_prefix='/function4_1')
    app.register_blueprint(function5_bp, url_prefix='/function5')

    from views.function4 import init_function4
    init_function4(app, socketio)

    return app, socketio


if __name__ == "__main__":
    app, socketio = create_app()
    socketio.run(app, debug=True, host="0.0.0.0")
