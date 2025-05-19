from . import db

class Award(db.Model):
    __tablename__ = 'award'
    
    AwardID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    BookID = db.Column(db.String(10), db.ForeignKey('book.BookID'))
    AwardName = db.Column(db.String(255))
    YearWon = db.Column(db.Integer)
    
    # Relationships
    book = db.relationship('Book', back_populates='awards')
    
    def to_dict(self):
        return {
            'AwardID': self. AwardID,
            'BookID': self.BookID,
            'AwardName': self.AwardName,
            'YearWon': self.YearWon
        }