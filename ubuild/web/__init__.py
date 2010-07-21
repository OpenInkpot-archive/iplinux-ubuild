from redis import Redis
from flask import Flask, render_template
from ubuild.job import Job

app = Flask(__name__)

app.config['DEBUG'] = True

db = Redis()

@app.route('/jobs/')
def index():
    return render_template('index.html',
                           jobs=((id,Job(id)) for id in db.smembers('jobs')))

@app.route('/architectures/')
def architectures():
    return render_template('architectures.html',
                           architectures=db.sort('architectures',alpha=True),
                           build_architectures=db.sort('build-architectures', alpha=True))

if __name__ == '__main__':
    app.run()
