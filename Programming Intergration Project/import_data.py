import pandas as pd
from sqlalchemy import create_engine, text

# ----------------------------
# 🔧 MySQL connection settings
# ----------------------------
username = "root"
password = "ledung04gmailcom"
host = "localhost"
port = "3306"
database = "bookstore"

# Create database connection
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}")

# Create a connection that will auto-commit changes
with engine.begin() as connection:
    # Disable foreign key checks to avoid constraint issues during import
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    
    # ----------------------
    # 📘 Load Excel file
    # ----------------------
    file_path = "Bookshop.xlsx"
    xlsx = pd.ExcelFile(file_path)
    
    # ----------------------
    # 📄 Load and clean sheets
    # ----------------------
    author_df = xlsx.parse("Author")
    book_df = xlsx.parse("Book")
    info_df = xlsx.parse("Info")
    award_df = xlsx.parse("Award")
    checkouts_df = xlsx.parse("Checkouts")
    edition_df = xlsx.parse("Edition")
    publisher_df = xlsx.parse("Publisher")
    ratings_df = xlsx.parse("Ratings")
    series_df = xlsx.parse("Series")
    sales_df = xlsx.parse("Sales")
    
    # Fix Info: merge BookID1 + BookID2 → BookID
    info_df["BookID"] = info_df["BookID1"].astype(str) + info_df["BookID2"].astype(str)
    info_df = info_df.drop(columns=["BookID1", "BookID2"])
    
    # Fix Award: merge with Book to get BookID from Title
    award_df = pd.merge(award_df, book_df[["BookID", "Title"]], on="Title", how="left")
    award_df = award_df.rename(columns={"Award Name": "AwardName", "Year Won": "YearWon"})
    award_df = award_df[["BookID", "AwardName", "YearWon"]]
    
    # Convert the SaleDate column to YYYY-MM-DD for MySQL import
    sales_df['SaleDate'] = pd.to_datetime(sales_df['SaleDate']).dt.strftime('%Y-%m-%d')

    # NEW: Split Sales into Orders and OrderDetails
    orders_df = sales_df[["OrderID", "SaleDate"]].drop_duplicates()
    order_details_df = sales_df[["OrderID", "ItemID", "ISBN"]]
    
    # ----------------------
    # 🚀 Refresh + Push data
    # ----------------------
    sheet_mapping = {
        "author": author_df,
        "publisher": publisher_df,
        "series": series_df,
        "book": book_df,
        "edition": edition_df,
        "info": info_df,
        "checkouts": checkouts_df,
        "ratings": ratings_df,
        "award": award_df,
        "orders": orders_df,
        "orderdetails": order_details_df
    }
    
    for table_name, df in sheet_mapping.items():
        try:
            # Clear existing data
            connection.execute(text(f"DELETE FROM {table_name}"))
            print(f"🧹 Cleared existing data from '{table_name}'")
            
            # Import new data using pandas to_sql
            df.to_sql(table_name, con=connection, if_exists='append', index=False)
            print(f"✅ Imported '{table_name}' with {len(df)} rows")
        except Exception as e:
            print(f"❌ Error processing '{table_name}': {e}")
    
    # Re-enable foreign key checks
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

print("\n🎉 All data has been refreshed and imported successfully into your MySQL database!")