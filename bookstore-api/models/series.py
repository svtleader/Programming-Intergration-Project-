from . import db

class Series(db.Model):
    __tablename__ = 'series'
    
    SeriesID = db.Column(db.String(20), primary_key=True)
    SeriesName = db.Column(db.String(100))
    PlannedVolumes = db.Column(db.Integer)
    BookTourEvents = db.Column(db.Integer)
    
    # Relationships
    books = db.relationship('Info', back_populates='series')
    
    def to_dict(self):
        return {
            'SeriesID': self.SeriesID,
            'SeriesName': self.SeriesName,
            'PlannedVolumes': self.PlannedVolumes,
            'BookTourEvents': self.BookTourEvents
        }