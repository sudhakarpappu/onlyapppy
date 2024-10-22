from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
import uuid
from pydantic import BaseModel
import logging
import math as Math

from decimal import Decimal, ROUND_HALF_UP


app = FastAPI()

# Set up CORS to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://fooodimp.s3-website.eu-north-1.amazonaws.com/"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb',
                           aws_access_key_id="",
                           aws_secret_access_key="",
                           region_name='')  # Ensure this region is correct


# Health check for DynamoDB connection to the table
@app.get("/health")
def dynamo_health_check():
    try:
        # Get table reference
        table = dynamodb.Table('dataa')  # Use your DynamoDB table name

        # Perform a simple table description request to ensure connection
        table.load()  # This will throw an exception if the table does not exist or is inaccessible
        return {"status": "success", "message": "Connected to DynamoDB table"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to connect to DynamoDB table: {str(e)}"}

# Define the root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Food Ordering System"}

@app.get("/getItalianFood")
def get_italian_food():
    try:
        table = dynamodb.Table('dataa')  # Ensure this is your DynamoDB table name
        response = table.scan()  # Scan the table to get all records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing DynamoDB: {str(e)}")

    # Filter for Italian food items (assuming there's a 'titlename' attribute)
    items = [
        {
            'foodID': item['FoodID'],
            'food_name': item['title'],
            'quantity': item['quantity'],
            'price': float(item['rate']),
            'url': item['url'],
            'titleId': item['titleId']
        }
        for item in response.get('Items', [])
        if item.get('titlename') == 'ItalianFood'  # Filter for Italian food items
    ]
    
    if not items:
        raise HTTPException(status_code=404, detail="No Italian food items found")

    return {"Items": items}

@app.get("/getIndianFood")
def get_italian_food():
    try:
        table = dynamodb.Table('dataa')  # Ensure this is your DynamoDB table name
        response = table.scan()  # Scan the table to get all records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing DynamoDB: {str(e)}")

    # Filter for Italian food items (assuming there's a 'titlename' attribute)
    items = [
        {
            'foodID': item['FoodID'],
            'food_name': item['title'],
            'quantity': item['quantity'],
            'price': float(item['rate']),
            'url': item['url'],
            'titleId': item['titleId']
        }
        for item in response.get('Items', [])
        if item.get('titlename') == 'IndianFood'  # Filter for Italian food items
    ]
    
    if not items:
        raise HTTPException(status_code=404, detail="No Indian food items found")

    return {"Items": items}

@app.get("/getKoreanFood")
def get_korean_food():
    try:
        table = dynamodb.Table('dataa')  # Ensure this is your DynamoDB table name
        response = table.scan()  # Scan the table to get all records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing DynamoDB: {str(e)}")
    #print(response)
    # Filter for Korean food items (assuming there's a 'category' attribute)
    items = [
        {
            'foodID': item['FoodID'],
            'food_name': item['title'],
            'quantity': (item['quantity']),
            'price': float(item['rate']),
            'url': item['url'],
            'titleId': item['titleId']
        }
        for item in response.get('Items', [])
        if item.get('titlename') == 'korean'  # Ensure the 'category' matches
    ]
    print(items)
    if not items:
        raise HTTPException(status_code=404, detail="No Korean food items found")

    return {"Items": items}

# Example to submit a food item to the DynamoDB table
@app.put("/submitFood1")
async def submit_food(FoodItem):
    try:
        table = dynamodb.Table('dataa')  # Ensure this is your DynamoDB table name

        # Define the item structure for insertion
        item = {
            'FoodID': str(uuid.uuid4()),  # Generate a unique FoodID
            'title': data.food_name,
            'quantity': data.quantity,
            'price': data.price,
            'url': data.url,
            'titleId': data.titleId,
            'category': 'KoreanFood'  # Set category for the submitted food item
        }

        # Insert the item into DynamoDB
        table.put_item(Item=item)
        return {"message": "Food item submitted successfully", "item": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting food item: {str(e)}")
class FoodItem(BaseModel):
    foodID: str

@app.get("/getFoodDetails/{foodID}")
async def get_food_details(foodID: str):
    response = table.get_item(
        Key={
            'foodID': foodID
        }
    )
    item = response.get('Item')
    if item:
        return item
    return {"error": "Food item not found"}

class CartItem(BaseModel):
    foodID: int
    food_name: str
    quantity: int
    price: str  # Price is a string to convert to Decimal

class OrderData(BaseModel):
    customerName: str
    cartItems: list[CartItem]
    totalAmount: str  # Total amount is a string to convert to Decimal

@app.post("/submitdata")
async def submitdata(data: OrderData):
    try:
        table = dynamodb.Table("cust1")  # Your DynamoDB table

        # Generate a unique order number (UUID as string)
        order_number = str(uuid.uuid4())

        # Convert totalAmount to Decimal with two decimal places
        try:
            total_amount_decimal = Decimal(data.totalAmount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid total amount format")

        # Convert each item's price to Decimal and handle cart items
        cart_items = []
        for item in data.cartItems:
            try:
                price_decimal = Decimal(item.price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid price format for item {item.food_name}")

            cart_items.append({
                'foodID': item.foodID,
                'food_name': item.food_name,
                'quantity': item.quantity,
                'price': price_decimal
            })

        # Create an order item to insert into DynamoDB
        order_item = {
            'orderNumber': order_number,
            'customerName': data.customerName,
            'cartItems': cart_items,
            'totalAmount': total_amount_decimal
        }

        # Insert the order into DynamoDB
        table.put_item(Item=order_item)

        return {"message": "Order placed successfully!", "orderNumber": order_number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error placing order: {str(e)}")