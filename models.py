from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class ProductInCategory(database.Model):
    __tablename__ = "products_in_categories"

    id = database.Column(database.Integer, primary_key=True)
    product_id = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    category_name = database.Column(database.String(256), database.ForeignKey("categories.name"), nullable=False)


class ProductInOrder(database.Model):
    __tablename__ = "products_in_orders"

    id = database.Column(database.Integer, primary_key=True)
    product_id = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    order_id = database.Column(database.Integer, database.ForeignKey("orders.id"), nullable=False)
    quantity = database.Column(database.Integer, nullable=False)


class Product(database.Model):
    __tablename__ = "products"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)
    price = database.Column(database.Float, nullable=False)
    sold = database.Column(database.Integer, nullable=False)
    waiting = database.Column(database.Integer, nullable=False)

    categories = database.relationship("Category", secondary=ProductInCategory.__table__, back_populates="products")
    orders = database.relationship("Order", secondary=ProductInOrder.__table__, back_populates="products")


class Category(database.Model):
    __tablename__ = "categories"

    name = database.Column(database.String(256), primary_key=True)

    products = database.relationship("Product", secondary=ProductInCategory.__table__, back_populates="categories")

    def __repr__(self):
        return self.name


class Order(database.Model):
    __tablename__ = "orders"

    id = database.Column(database.Integer, primary_key=True)
    total_price = database.Column(database.Float, nullable=False)
    status = database.Column(database.String(256), nullable=False)
    created_on = database.Column(database.DateTime, nullable=False)
    email = database.Column(database.String(256), nullable=False)
    # contract_address = database.Column(database.String(42), nullable=True)

    products = database.relationship("Product", secondary=ProductInOrder.__table__, back_populates="orders")
