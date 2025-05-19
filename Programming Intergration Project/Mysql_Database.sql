DROP DATABASE IF EXISTS bookstore;
CREATE DATABASE bookstore;
USE bookstore;

CREATE TABLE Author (
    AuthID VARCHAR(10) PRIMARY KEY,
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    Birthday DATE,
    CountryOfResidence VARCHAR(50),
    HrsWritingPerDay INT
);
CREATE INDEX idx_author_firstname_ci ON Author((LOWER(FirstName)));
CREATE INDEX idx_author_lastname_ci ON Author((LOWER(LastName)));

CREATE TABLE Publisher (
    PubID VARCHAR(10) PRIMARY KEY,
    PublishingHouse VARCHAR(100),
    City VARCHAR(50),
    State VARCHAR(50),
    Country VARCHAR(50),
    YearEstablished INT,
    MarketingSpend INT
);

CREATE TABLE Series (
    SeriesID VARCHAR(20) PRIMARY KEY,
    SeriesName VARCHAR(100),
    PlannedVolumes INT,
    BookTourEvents INT
);

CREATE TABLE Book (
    BookID VARCHAR(10) PRIMARY KEY,
    Title VARCHAR(255),
    AuthID VARCHAR(10),
    FOREIGN KEY (AuthID) REFERENCES Author(AuthID)
);
CREATE INDEX idx_book_authid ON Book(AuthID);
CREATE INDEX idx_book_title_ci ON Book((LOWER(Title)));
CREATE INDEX idx_book_title_authid ON Book(Title, AuthID);

CREATE TABLE Edition (
    ISBN VARCHAR(20) PRIMARY KEY,
    BookID VARCHAR(10),
    Formatt VARCHAR(50),
    PubID VARCHAR(10),
    PublicationDate DATE,
    Pages INT,
    PrintRunSizeK INT,
    Price DECIMAL(6,2),
    FOREIGN KEY (BookID) REFERENCES Book(BookID),
    FOREIGN KEY (PubID) REFERENCES Publisher(PubID)
);
CREATE INDEX idx_edition_isbn ON Edition(ISBN);
CREATE INDEX idx_edition_bookid ON Edition(BookID);

CREATE TABLE Info (
    BookID VARCHAR(10) PRIMARY KEY,
    Genre VARCHAR(50),
    SeriesID VARCHAR(20),
    VolumeNumber INT,
    StaffComment TEXT,
    FOREIGN KEY (BookID) REFERENCES Book(BookID),
    FOREIGN KEY (SeriesID) REFERENCES Series(SeriesID)
);
CREATE INDEX idx_info_bookid ON Info(BookID);
CREATE INDEX idx_info_seriesid ON Info(SeriesID);

CREATE TABLE Checkouts (
    BookID VARCHAR(10),
    CheckoutMonth INT,
    NumberOfCheckouts INT,
    PRIMARY KEY (BookID, CheckoutMonth),
    FOREIGN KEY (BookID) REFERENCES Book(BookID)
);
CREATE INDEX idx_checkouts_bookid ON Checkouts(BookID);

CREATE TABLE Ratings (
    ReviewID INT PRIMARY KEY,
    BookID VARCHAR(10),
    Rating INT,
    ReviewerID INT,
    FOREIGN KEY (BookID) REFERENCES Book(BookID)
);
CREATE INDEX idx_ratings_bookid ON Ratings(BookID);
CREATE INDEX idx_ratings_reviewerid ON Ratings(ReviewerID);

CREATE TABLE Award (
    AwardID INT AUTO_INCREMENT PRIMARY KEY,
    BookID VARCHAR(10),
    AwardName VARCHAR(255),
    YearWon INT,
    FOREIGN KEY (BookID) REFERENCES Book(BookID)
);

CREATE TABLE Orders (
    OrderID VARCHAR(30) PRIMARY KEY,
    SaleDate DATE
);
CREATE INDEX idx_orders_saledate ON Orders(SaleDate);
CREATE INDEX idx_orders_date_id ON Orders(SaleDate, OrderID);
CREATE FULLTEXT INDEX idx_orders_orderid_fulltext ON Orders(OrderID) WITH PARSER ngram;

CREATE TABLE OrderDetails (
    OrderID VARCHAR(30),
    ItemID VARCHAR(30),
    ISBN VARCHAR(20),
	Quantity INT NOT NULL DEFAULT 1,
    PRIMARY KEY (OrderID, ItemID),
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
    FOREIGN KEY (ISBN) REFERENCES Edition(ISBN)
);
CREATE INDEX idx_orderdetails_orderid ON OrderDetails(OrderID);
CREATE INDEX idx_orderdetails_isbn ON OrderDetails(ISBN);

-- Drop existing foreign key constraint
ALTER TABLE OrderDetails
DROP FOREIGN KEY orderdetails_ibfk_1;

-- Re-add the constraint with ON DELETE CASCADE
ALTER TABLE OrderDetails
ADD CONSTRAINT orderdetails_ibfk_1
FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
ON DELETE CASCADE;

-- Verify the changes
SHOW CREATE TABLE OrderDetails;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_role ON users(role);

SELECT 
    TABLE_SCHEMA,
    TABLE_NAME,
    INDEX_NAME,
    CARDINALITY
FROM 
    INFORMATION_SCHEMA.STATISTICS 
WHERE 
    TABLE_SCHEMA = 'bookstore'
ORDER BY 
    CARDINALITY DESC;

SELECT* FROM OrderDetails D, Orders O WHERE D.OrderID = O.OrderID ORDER BY SaleDate;
SELECT* FROM OrderDetails;
SELECT* FROM Book;
SELECT* FROM Author;
SELECT* FROM Orders;
SELECT* FROM Info;
SELECT* FROM Users;