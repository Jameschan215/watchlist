import os
import sys
import click

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

WIN = sys.platform.startswith("win")
if WIN:
    prefix = "sqlite:///"
else:
    prefix = "sqlite:////"

app = Flask(__name__)

app.config['SECRET_KEY'] = 'dev'
app.config["SQLALCHEMY_DATABASE_URI"] = prefix + \
    os.path.join(app.root_path, "data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


@app.route("/", methods=['GET', 'POST'])
def index():

    # 判断是否POST请求
    if request.method == 'POST':

        # get data from form
        title = request.form.get('title')
        year = request.form.get('year')

        # 验证输入数据，如果有误，则显示错误提示，并重定向回主页
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect('/')

        # 保存表单数据到数据库，显示保存成功提示，再重定向到主页
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))

    movies = Movie.query.all()
    return render_template("index.html", movies=movies)


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':
        title = request.form.get('title')
        year = request.form.get('year')

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))

        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))
    return render_template('edit.html', movie=movie)


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
def delete(movie_id):
    
    movie = Movie.query.get_or_404(movie_id)

    db.session.delete(movie)
    db.session.commit()
    flash('Item Deleted.')

    return redirect(url_for('index'))



@app.errorhandler(404)
def page_not_found(e):
    user = User.query.first()
    return render_template('404.html'), 404


@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)      # return {'user': user}


@app.cli.command()
@click.option("--drop", is_flag=True, help="Create after drop.")
def initdb(drop):
    if drop:
        db.drop_all()

    db.create_all()
    click.echo("Initialized database.")


@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()

    name = "James Chen"
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)

    for item in movies:
        movie = Movie(title=item['title'], year=item['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done')
