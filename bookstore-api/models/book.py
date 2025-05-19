from . import db

class Book(db.Model):
    __tablename__ = 'book'
    
    BookID = db.Column(db.String(10), primary_key=True)
    Title = db.Column(db.String(255), nullable=False)
    AuthID = db.Column(db.String(10), db.ForeignKey('author.AuthID'))
    
    # Relationships
    author = db.relationship('Author', back_populates='books')
    editions = db.relationship('Edition', back_populates='book')
    info = db.relationship('Info', back_populates='book', uselist=False)
    awards = db.relationship('Award', back_populates='book')
    ratings = db.relationship('Rating', back_populates='book')
    checkouts = db.relationship('Checkout', back_populates='book')
    
    def to_dict(self):
        return {
            'BookID': self.BookID,
            'Title': self.Title,
            'AuthID': self.AuthID
        }
    
    def to_dict_extended(self):
        return {
            **self.to_dict(),
            'Author': self.author.to_dict() if self.author else None,
            'Info': self.info.to_dict() if self.info else None,
            'Editions': [edition.to_dict() for edition in self.editions]
        }

class Edition(db.Model):
    __tablename__ = 'edition'
    
    ISBN = db.Column(db.String(20), primary_key=True)
    BookID = db.Column(db.String(10), db.ForeignKey('book.BookID'))
    Formatt = db.Column(db.String(50))
    PubID = db.Column(db.String(10), db.ForeignKey('publisher.PubID'))
    PublicationDate = db.Column(db.Date)
    Pages = db.Column(db.Integer)
    PrintRunSizeK = db.Column(db.Integer)
    Price = db.Column(db.DECIMAL(6, 2))
    
    # Relationships
    book = db.relationship('Book', back_populates='editions')
    publisher = db.relationship('Publisher', back_populates='editions')
    order_details = db.relationship('OrderDetail', back_populates='edition')
    
    def to_dict(self):
        return {
            'ISBN': self.ISBN,
            'BookID': self.BookID,
            'Format': self.Formatt,
            'PubID': self.PubID,
            'PublicationDate': self.PublicationDate.isoformat() if self.PublicationDate else None,
            'Pages': self.Pages,
            'PrintRunSizeK': self.PrintRunSizeK,
            'Price': float(self.Price) if self.Price else None
        }

class Info(db.Model):
    __tablename__ = 'info'
    
    BookID = db.Column(db.String(10), db.ForeignKey('book.BookID'), primary_key=True)
    Genre = db.Column(db.String(50))
    SeriesID = db.Column(db.String(20), db.ForeignKey('series.SeriesID'))
    VolumeNumber = db.Column(db.Integer)
    StaffComment = db.Column(db.Text)
    
    # Relationships
    book = db.relationship('Book', back_populates='info')
    series = db.relationship('Series', back_populates='books')
    
    def to_dict(self):
        return {
            'BookID': self.BookID,
            'Genre': self.Genre,
            'SeriesID': self.SeriesID,
            'VolumeNumber': self.VolumeNumber,
            'StaffComment': self.StaffComment
        }