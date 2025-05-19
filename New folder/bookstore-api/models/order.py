from . import db

class Order(db.Model):
    __tablename__ = 'orders'
    
    OrderID = db.Column(db.String(30), primary_key=True)
    SaleDate = db.Column(db.Date)
    
    # Relationships
    order_details = db.relationship('OrderDetail', back_populates='order')
    
    def to_dict(self):
        return {
            'OrderID': self.OrderID,
            'SaleDate': self.SaleDate.isoformat() if self.SaleDate else None,
            'OrderDetails': [detail.to_dict() for detail in self.order_details]
        }