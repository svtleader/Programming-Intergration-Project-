from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from . import db

class OrderDetail(db.Model):
    __tablename__ = 'orderdetails'
    
    OrderID = db.Column(db.String(30), db.ForeignKey('orders.OrderID'), primary_key=True)
    ItemID = db.Column(db.String(30), primary_key=True)
    ISBN = db.Column(db.String(20), db.ForeignKey('edition.ISBN'))
    Quantity = db.Column(db.Integer, nullable=False, default=1)
    
    # Relationships
    order = db.relationship('Order', back_populates='order_details')
    edition = db.relationship('Edition', back_populates='order_details')
    
    def to_dict(self):
        return {
            'OrderID': self.OrderID,
            'ItemID': self.ItemID,
            'ISBN': self.ISBN,
            'Quantity': self.Quantity,
            'Book': self.edition.book.to_dict_extended() if self.edition and self.edition.book else None,
            'Price': float(self.edition.Price) if self.edition and self.edition.Price else None
        }