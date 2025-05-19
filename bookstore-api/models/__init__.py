from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import models after db initialization to avoid circular imports
from .user import User
from .author import Author
from .publisher import Publisher
from .book import Book, Edition, Info
from .series import Series
from .award import Award
from .order import Order
from .order_detail import OrderDetail
from .rating import Rating
from .checkout import Checkout