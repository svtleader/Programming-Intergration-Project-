from . import db

class Author(db.Model):
    __tablename__ = 'author'
    
    AuthID = db.Column(db.String(10), primary_key=True)
    FirstName = db.Column(db.String(50))
    LastName = db.Column(db.String(50))
    Birthday = db.Column(db.Date)
    CountryOfResidence = db.Column(db.String(50))
    HrsWritingPerDay = db.Column(db.Integer)
    
    # Relationships
    books = db.relationship('Book', back_populates='author')
    
    def to_dict(self):
        return {
            'AuthID': self.AuthID,
            'FirstName': self.FirstName,
            'LastName': self.LastName,
            'Birthday': self.Birthday.isoformat() if self.Birthday else None,
            'CountryOfResidence': self.CountryOfResidence,
            'HrsWritingPerDay': self.HrsWritingPerDay,
            'FullName': f"{self.FirstName} {self.LastName}"
        }