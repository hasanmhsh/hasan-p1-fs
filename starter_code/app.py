#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify,abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import sys
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
from datetime import date
from flask_migrate import Migrate
from sqlalchemy import Column, Integer, TIMESTAMP
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#



class Show(db.Model):
    __tablename__ = 'shows'
    # id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'),primary_key=True, nullable=False)
    datetimestamp = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    datetimestamp_frontend = db.Column(db.DateTime)

    __table_args__ = (db.UniqueConstraint(venue_id, artist_id),)

    venue = db.relationship("Venue", back_populates="shows")
    artist = db.relationship("Artist", back_populates="shows")

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # artists = db.relationship('Artist', secondary=shows,
    #   backref=db.backref('Artist', lazy=True))
    genres = db.relationship('VenueGenre', cascade="all, delete-orphan" , backref='venue', lazy=True)
    shows = db.relationship("Show", back_populates="venue")

    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'
    


class VenueGenre(db.Model):
  __tablename__= 'venue_genres'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.relationship('ArtistGenre', cascade="all, delete-orphan" , backref='artist', lazy=True)

    shows = db.relationship("Show", back_populates="artist")


class ArtistGenre(db.Model):
  __tablename__= 'artist_genres'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  body = []
  cities = db.session.query(Venue.city,Venue.state).group_by(Venue.city,Venue.state).all()
  # return jsonify(cities)
  for city in cities:
    body_item = {}
    body_item['city'] = city.city
    body_item["state"] = city.state
    body_item["venues"] = []
    # return jsonify(body_item)
    venues_per_city = Venue.query.filter(Venue.city==city.city)
    for venue in venues_per_city:
      number_of_artists_per_venue = len(Venue.query.get(venue.id).shows)
      body_item["venues"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": number_of_artists_per_venue
      })
    body.append(body_item)



  
  return render_template('pages/venues.html', areas=body)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  part = request.form['search_term']
  search = "%{}%".format(part)
  # result = Venue.query.all()
  # result = Venue.query.filter(Venue.name.like(search)).all() #case sensitive
  result = db.session.query(Venue).filter(func.lower(Venue.name).contains(part.lower(), autoescape = True)).all() #case in-sensetive
  body = {}
  body["count"] = len(result)
  data = []
  for venue in result:
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(Venue.query.get(venue.id).shows)
    })
  body['data'] = data
  return render_template('pages/search_venues.html', results=body, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  past_shows = []
  upcomming_shows = []
  now = datetime.now()
  for show in venue.shows:
        # show_time data type is datetime.datetime not string for both columns 'datetimestamp_frontend' and 'datetimestamp'
    #compare time is similar to numbers the past is smaller than present
    # show_time = db.session.query(Show).filter(Show.venue_id==venue.id,Show.artist_id==artist.id).first().datetimestamp_frontend
    #str -> datetime -> datetime_object = datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')
    show_time = show.datetimestamp_frontend
    artist_body = {
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    if show_time > now:
      upcomming_shows.append(artist_body)
    else:
      past_shows.append(artist_body)

  genres = []
  for genre in venue.genres:
    genres.append(genre.name)

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link ,
    "past_shows": past_shows,
    "upcoming_shows": upcomming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcomming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)
  

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  error = False
  body = {}
    
  

  try:
    form = request.form
    venue=Venue(
      name=form['name'],
      city=form['city'],
      state=form['state'],
      address=form['address'],
      phone=form['phone'],
      facebook_link=form['facebook_link'],
    )
    # return "venue"
    # return(jsonify(form.getlist('genres')))
    genres = form.getlist('genres')
    for genre in genres:
      venue_genre = VenueGenre(name=genre)
      venue_genre.venue = venue
    # return "google"
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Failed to create ' + 'Venue ' + request.form['name'] + '!')
    abort(400)
  else:
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(todo_id) 
    db.session.delete(venue) 
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({ 'success': True })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({
    "id": artist.id,
    "name": artist.name,
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():


  part = request.form['search_term']
  search = "%{}%".format(part)
  # result = Artist.query.filter(Artist.name.like(search)).all() #case sensetive
  result = db.session.query(Artist).filter(func.lower(Artist.name).contains(part.lower(), autoescape = True)).all() #case in-sensetive
  body = {}
  body["count"] = len(result)
  data = []
  for artist in result:
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(Artist.query.get(artist.id).shows)
    })
  body['data'] = data


  return render_template('pages/search_artists.html', results=body, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)

  past_shows = []
  upcomming_shows = []
  now = datetime.now()
  for show in artist.shows:
        # show_time data type is datetime.datetime not string for both columns 'datetimestamp_frontend' and 'datetimestamp'
    #compare time is similar to numbers the past is smaller than present
    # show_time = db.session.query(Show).filter(Show.venue_id==venue.id,Show.artist_id==artist.id).first().datetimestamp_frontend
    #str -> datetime -> datetime_object = datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')
    show_time = show.datetimestamp_frontend
    venue_body = {
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    if show_time > now:
      upcomming_shows.append(venue_body)
    else:
      past_shows.append(venue_body)

  genres = []
  for genre in artist.genres:
    genres.append(genre.name)



  data={
    "id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link ,
    "past_shows": past_shows,
    "upcoming_shows": upcomming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcomming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  genres = []
  for genre in artist.genres:
    genres.append(genre.name)
  form = ArtistForm()
  artist_body={
    "id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist_body)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    form = request.form
    artist = Artist.query.get(artist_id)
    artist.name=form['name']
    artist.city=form['city']
    artist.state=form['state']
    artist.phone=form['phone']
    artist.facebook_link=form['facebook_link']
    # return "artist"
    # return(jsonify(form.getlist('genres')))
    genres = form.getlist('genres')
    artist.genres = []
    for genre in genres:
      artist_genre = ArtistGenre(name=genre)
      artist_genre.artist = artist
    # return "google"
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  genres = []
  for genre in venue.genres:
    genres.append(genre.name)
  form = VenueForm()
  venue={
    "id": venue.id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = request.form
    venue = Venue.query.get(venue_id)
    venue.name=form['name']
    venue.city=form['city']
    venue.address=form['address']
    venue.state=form['state']
    venue.phone=form['phone']
    venue.facebook_link=form['facebook_link']
    # return "artist"
    # return(jsonify(form.getlist('genres')))
    genres = form.getlist('genres')
    venue.genres = []
    for genre in genres:
      venue_genre = VenueGenre(name=genre)
      venue_genre.venue = venue
    # return "google"
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()


  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():




  error = False
  body = {}
    
  

  # return "hello"
  try:
    form = request.form
    artist=Artist(
      name=form['name'],
      city=form['city'],
      state=form['state'],
      phone=form['phone'],
      facebook_link=form['facebook_link']
    )
    # return "venue"
    # return(jsonify(form.getlist('genres')))
    genres = form.getlist('genres')
    for genre in genres:
      artist_genre = ArtistGenre(name=genre)
      artist_genre.artist = artist
      artist.genres.append(artist_genre)
    # return "google"
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Failed to create ' + 'Artist ' + request.form['name'] + '!')
    abort(400)
  else:
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = db.session.query(Show).all()
  data = []
  for show in shows:
    show_time = show.datetimestamp_frontend
    data.append({
    "venue_id": show.venue.id,
    "venue_name": show.venue.name,
    "artist_id": show.artist.id,
    "artist_name": show.artist.name,
    "artist_image_link": show.artist.image_link,
    "start_time": show_time.strftime("%m/%d/%Y, %H:%M:%S")
  })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  body = {}
  # return "hello"
  # try:
  form = request.form
  venue = Venue.query.get(form['venue_id'])
  artist = Artist.query.get(form['artist_id'])
  show=Show(
    artist_id=form['artist_id'],
    venue_id=form['venue_id'],
    datetimestamp_frontend=datetime.strptime(form['start_time'], '%Y-%m-%d %H:%M:%S'),
  )
  db.session.add(show)
  db.session.commit()
  flash('Show was successfully listed!')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
