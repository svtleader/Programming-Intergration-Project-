from . import db

class Checkout(db.Model):
    __tablename__ = 'checkouts'
    
    BookID = db.Column(db.String(10), db.ForeignKey('book.BookID'), primary_key=True)
    CheckoutMonth = db.Column(db.Integer, primary_key=True)
    NumberOfCheckouts = db.Column(db.Integer)
    
    # Relationships
    book = db.relationship('Book', back_populates='checkouts')
    
    def to_dict(self):
        return {
            'BookID': self.BookID,
            'CheckoutMonth': self.CheckoutMonth,
            'NumberOfCheckouts': self.NumberOfCheckouts
        }