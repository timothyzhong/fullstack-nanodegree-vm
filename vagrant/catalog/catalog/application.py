from catalog import app

@app.route('/')
@app.route('/hello')
def index():
    return 'Catalog'
