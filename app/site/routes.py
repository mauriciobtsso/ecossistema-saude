from flask import Blueprint, render_template

# Blueprint do Site Público (sem restrição de login)
site_bp = Blueprint('site', __name__, template_folder='templates')

@site_bp.route('/')
def index():
    return render_template('site/index.html')

@site_bp.route('/termos-de-uso')
def termos():
    return render_template('site/termos.html')

@site_bp.route('/politica-de-privacidade')
def privacidade():
    return render_template('site/privacidade.html')