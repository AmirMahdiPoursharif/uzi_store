# Cart_app


## Add Product in Cart
* برای اضافه کردن محصول به سبد خرید :

```http request
POST  /cart/addItem/
```

دیتایی که باید ارسال شود به فرمت زیر است 

```json
{
    "product_uuid": "a743543c-ab93-4dc0-a1be-3ea46bca25f0",
    "quantity": 3
}
```

- در اینجا به جای product_uuid باید uuid محصولی را وارد کنید که قصد اضافه کردن آن به سبد خرید را دارید

* اگر مقداری برای quantity ارسال نکنید به صورت خودکار مقدار 1 برای آن لحاظ خواهد شد

جواب مورد انتظار باید به فرم زیر باشد

```json
{
    "id": 3,
    "product": {
        "uuid": "a743543c-ab93-4dc0-a1be-3ea46bca25f0",
        "category": {
            "id": 1,
            "name": "phone",
            "slug": "phone"
        },
        "name": "samsung galaxy S25",
        "description": "from samsung",
        "price": "1200.00",
        "stock": 9,
        "parent_uuid": "fdec1b49-3442-4ac1-978a-d71af769d741",
        "variant_name": "White - 512GB"
    },
    "quantity": 3,
    "total_cost": 3600.0
}
```

* دقت کنید اگر quantity وارد کنید که بیشتر از stock محصول است با خطای زیر مواجه خواهید شد :

```json
{
    "error": "Insufficient stock. Only 9 items are available"
}
```

- نکته قابل توجه در اینجا این است که فقط محصولاتی که فزرند هستند (تنوعی از یک محصول مرجع هستند) میتوانند در سبد خرید اضافه شوند 

* اگر تلاش کنید محصولی را به سبد خرید اضافه کنید که پدر است با ارور زیر روبرو خواهید شد :

```json
{
    "error": "Base products cannot be added to the cart. Please select a specific variant"
}
```

* اگر در سبد خرید محصولی داشته باشید و بعد دوباره تلاش کنید همان محصول را با quantity بالاتر از stock 
مانده (quantity_new > quantity_old + stock) با اروری به فرمت زیر مواجه خواهید شد :

```json
{
    "error": "You already have 4 items in your cart. Total available stock is 5."
}
```

- اگر سعی کنید یک محصول را دوباره به سبد خرید اضافه کنید فقط تعداد یا همان quantity محصول تغییر خواهد کرد

---

## Get Cart

* برای دیدن سبد خرید خود :

```http request
GET  /cart/
```

جواب مورد انتظار به فرم زیر باید باشد :

```json
{
    "id": 2,
    "user": "masoud@uzi.com",
    "items": [
        {
            "id": 1,
            "product": {
                "uuid": "e6963c14-ad8e-464b-bf58-9e09b115916c",
                "category": {
                    "id": 1,
                    "name": "phone",
                    "slug": "phone"
                },
                "name": "iphone13",
                "description": "from apple",
                "price": "1000.00",
                "stock": 5,
                "parent_uuid": "f3ac0216-a236-45ac-8470-00b2f80fb5fc",
                "variant_name": "Black - 256GB"
            },
            "quantity": 4,
            "total_cost": 4000.0
        },
        {
            "id": 4,
            "product": {
                "uuid": "a743543c-ab93-4dc0-a1be-3ea46bca25f0",
                "category": {
                    "id": 1,
                    "name": "phone",
                    "slug": "phone"
                },
                "name": "samsung galaxy S25",
                "description": "from samsung",
                "price": "1200.00",
                "stock": 9,
                "parent_uuid": "fdec1b49-3442-4ac1-978a-d71af769d741",
                "variant_name": "White - 512GB"
            },
            "quantity": 3,
            "total_cost": 3600.0
        }
    ],
    "total_cost": 7600.0,
    "created_at": "2026-06-22T12:53:27.113708+03:30"
}
```

---

## Remove Product From Cart

* برای حذف یک محصول از سبد خرید :

```http request
POST  /cart/removeItem/
```

دیتایی که باید ارسال شود به فرمت زیر است :

```json
{
    "product_uuid": "f3ac0216-a236-45ac-8470-00b2f80fb5fc"
}
```

* در اینجا product_uuid همان uuid محصولی است که قصد حذف آن از سبد خرید را دارید می باشد

جوابی که دریافت خواهید کرد :

```json
{
    "message": "Item successfully deleted from cart"
}
```