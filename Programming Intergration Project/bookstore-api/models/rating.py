from . import db

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    ReviewID = db.Column(db.Integer, primary_key=True)
    BookID = db.Column(db.String(10), db.ForeignKey('book.BookID'))
    Rating = db.Column(db.Integer)
    ReviewerID = db.Column(db.Integer)
    
    # Relationships
    book = db.relationship('Book', back_populates='ratings')
    
    def to_dict(self):
        return {
            'ReviewID': self.ReviewID,
            'BookID': self.BookID,
            'Rating': self.Rating,
            'ReviewerID': self.ReviewerID
        }