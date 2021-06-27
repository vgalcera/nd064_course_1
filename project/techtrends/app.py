import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
import logging
from werkzeug.exceptions import abort


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection


# Number of database connections
num_db_connections = 0


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()

    # Increment the number of database connections
    global num_db_connections
    num_db_connections += 1

    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()

    # Increment the number of database connections
    global num_db_connections
    num_db_connections += 1

    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        # log line
        app.logger.info('A non-existing article is accessed and a 404 page is returned')
        return render_template('404.html'), 404
    else:
        # log line
        app.logger.info('Article "' + post['title'] + '" retrieved!')
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    # log line
    app.logger.info('The "About Us" page is retrieved')
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            # log line
            app.logger.info('New article "' + title + '" posted!')

            return redirect(url_for('index'))

    return render_template('create.html')


# Define the healthz endpoint
@app.route('/healthz')
def healthz():
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )

    return response


# Define the metrics endpoint
@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    posts_count = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    response = app.response_class(
        response=json.dumps({"db_connection_count": num_db_connections, "post_count": len(posts_count)}),
        status=200,
        mimetype='application/json'
    )

    return response


# start the application on port 3111
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(format='%(levelname)s: %(asctime)s, %(message)s', level=logging.DEBUG)

    app.run(host='0.0.0.0', port='3111')
