from . import db

class Publisher(db.Model):
    __tablename__ = 'publisher'
    
    PubID = db.Column(db.String(10), primary_key=True)
    PublishingHouse = db.Column(db.String(100))
    City = db.Column(db.String(50))
    State = db.Column(db.String(50))
    Country = db.Column(db.String(50))
    YearEstablished = db.Column(db.Integer)
    MarketingSpend = db.Column(db.Integer)
    
    # Relationships
    editions = db.relationship('Edition', back_populates='publisher')
    
    def to_dict(self):
        return {
            'PubID': self.PubID,
            'PublishingHouse': self.PublishingHouse,
            'City': self.City,
            'State': self.State,
            'Country': self.Country,
            'YearEstablished': self.YearEstablished,
            'MarketingSpend': self.MarketingSpend
        }