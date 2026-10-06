# Product_app

## Category

### Category Admin

برای ساختن دسته بندی جدید:

```http request
POST  /api/admin/categories/
```

دیتایی که باید ارسال شود باید به فرمت زیر باشد :

```json
{
    "name": "Phone"
}
```

پاسخی که دریافت خواهید کرد باید به فرمت زیر باشد :

```json
{
    "id": 1,
    "name": "Phone",
    "slug": "Phone"
}
```

---

برای دریافت لیست دسته بندی های موجود : 

```http request
GET  /api/admin/categories/
```

پاسخی که دریافت خواهید کرد به فرمت زیر باید باشد :

```json
[
    {
        "id": 1,
        "name": "Phone",
        "slug": "Phone"
    },
    {
        "id": 2,
        "name": "Laptop",
        "slug": "Laptop"
    }
]
```

---

برای دیدن جزئیات یک دسته بندی مشخص :

```http request
GET  api/admin/category/category_slug/
```

* باید به جای category_slug اسلاگ دسته بندی که قصد دیدن جزئیات آن را دارید قرار دهید

پاسخ مورد انتظار باید به فرمت زیر باشد :

```json
{
    "id": 2,
    "name": "laptop",
    "slug": "laptop"
}
```

* اگر پیام زیر را دریافت کردید به این معنی است که به جای category_slug چیزی وارد کردید که با اسلاگ هیچ دسته بندی تطابق ندارد

```json
{
    "detail": "No Category matches the given query."
}
```

---

برای حذف یک دسته بندی :

```http request
POST  api/admin/category/category_slug/
```

- اگر کد وضعیت 204 را دریافت کردید یعنی دسته بندی به درستی حذف شده است

* اگر بخواهید دسته بندی را حذف کنید که محصولی در آن وجود دارد با پیام زیر روبرو خواهید شد :

```json
{
    "error": "There are some products that connected to this category, please delete them first"
}
```

---

### Category User

برای دریافت لیست دسته بندی های موجود:

```http request
GET  /user/categories/
```

پاسخی که دریافت خواهید کرد به فرمت زیر باید باشد

```json
[
    {
        "id": 1,
        "name": "Phone",
        "slug": "Phone"
    },
    {
        "id": 2,
        "name": "Laptop",
        "slug": "Laptop"
    }
]
```

برای دیدن جزئیات یک دسته بندی مشخص :

```http request
GET  user/category/category_slug/
```

* باید به جای category_slug اسلاگ دسته بندی که قصد دیدن جزئیات آن را دارید قرار دهید

پاسخ مورد انتظار باید به فرمت زیر باشد :

```
{
    "id": 1,
    "name": "phone",
    "slug": "phone"
}
```

* اگر پیام زیر را دریافت کردید به این معنی است که به جای category_slug چیزی وارد کردید که با اسلاگ هیچ دسته بندی تطابق ندارد

```json
{
    "detail": "No Category matches the given query."
}
```

---


## Product

* در این API سیستم محصولات با ساختاری شبیه به پدر فرزند عمل میکنند
یعنی دسته ای از محصولات مرجع(پدر) هستند و دسته ای هم تنوع(فرزند)
به این صورت که یک محصولی تنوعی از یک محصول مرجع هست

### Product Admin

برای ایجاد یک محصول :

```http request
POST  /api/admin/products/
```

برای ایجاد یک محصول پدر باید دیتایی به فرمت زیر را به این مسیر ارسال کنید

```json
{
    "category_slug": "phone",
    "name": "iphone",
    "description": "from apple",
    "price": 1000,
    "parent_uuid": null
} 
```

جواب مورد انتظار باید به فرمت زیر باشد :

```json
{
    "uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
    "category": {
        "id": 1,
        "name": "phone",
        "slug": "phone"
    },
    "name": "iphone",
    "description": "from apple",
    "price": "1000.00",
    "avg_rating": 0,
    "recent_reviews": [],
    "variants": []
}
```

* اگر برای ساختن محصول پدر فیلدی با عنوان variant_name ارسال کنید با این پیام روبرو خواهید شد

```json
{
    "variant_name": [
        "base products can not have a variant_name"
    ]
}
```

برای ایجاد یک محصول فرزند باید دیتایی به فرمت زیر به این مسیر ارسال کنید :

```json
{
    "category_slug": "phone",
    "name": "iphone13",
    "description": "from apple",
    "price": 1200,
    "stock": 5,
    "parent_uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
    "variant_name": "Black - 256GB"
}
```

جوابی که باید دریافت کنید به این شکل خواهد بود :

```json
{
    "uuid": "3276cee9-4b20-44e0-92ff-4284c9bd202d",
    "category": {
        "id": 1,
        "name": "phone",
        "slug": "phone"
    },
    "name": "iphone13",
    "description": "from apple",
    "price": "1200.00",
    "stock": 5,
    "available_stock": 5,
    "parent_uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
    "variant_name": "Black - 256GB"
}
```

* اگر هنگام ساختن محصول فرزند فیلد variant_name را نفرستید با ارور زیر روبرو خواهید شد :

```json
{
    "variant_name": [
        "If a product has a parent, it must provide a variant name"
    ]
}
```

---

برای دریافت لیست محصولات :

```http request
GET  /api/admin/products/
```

جوابی که دریافت خواهید کرد به فرمت زیر باید باشد :
 
```json
{
    "count": 4,
    "next": null,
    "previous": null,
    "results": [
        {
            "uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
            "category": {
                "id": 1,
                "name": "phone",
                "slug": "phone"
            },
            "name": "iphone",
            "description": "from apple",
            "price": "1000.00",
            "review_count": 0,
            "avg_rating": 0,
            "recent_reviews": [],
            "variants": [
                {
                    "uuid": "3276cee9-4b20-44e0-92ff-4284c9bd202d",
                    "name": "iphone13",
                    "variant_name": "Black - 256GB",
                    "price": "1200.00",
                    "available_stock": 5
                }
            ]
        },
        {
            "uuid": "7ec46df8-6c30-4a49-b213-455cca230746",
            "category": {
                "id": 1,
                "name": "phone",
                "slug": "phone"
            },
            "name": "samsung",
            "description": "from samsung",
            "price": "800.00",
            "review_count": 0,
            "avg_rating": 0,
            "recent_reviews": [],
            "variants": [
                {
                    "uuid": "b900f372-5d8e-4be9-9944-52164d9c3028",
                    "name": "galexy S25",
                    "variant_name": "White - 512GB",
                    "price": "1400.00",
                    "available_stock": 7
                }
            ]
        },
        {
            "uuid": "3276cee9-4b20-44e0-92ff-4284c9bd202d",
            "category": {
                "id": 1,
                "name": "phone",
                "slug": "phone"
            },
            "name": "iphone13",
            "description": "from apple",
            "price": "1200.00",
            "stock": 5,
            "available_stock": 5,
            "parent_uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
            "variant_name": "Black - 256GB"
        },
        {
            "uuid": "b900f372-5d8e-4be9-9944-52164d9c3028",
            "category": {
                "id": 1,
                "name": "phone",
                "slug": "phone"
            },
            "name": "galexy S25",
            "description": "from samsung",
            "price": "1400.00",
            "stock": 7,
            "available_stock": 7,
            "parent_uuid": "7ec46df8-6c30-4a49-b213-455cca230746",
            "variant_name": "White - 512GB"
        }
    ]
}
```

-دقت کنید که وقتی که اطلاعات محصولات فرزند را دریافت میکنید ممکن از تعداد 
available_stock از stock کمتر باشد 
(لزوما نباید برابر باشند)

* 

- میتوانید با فرستادن query_param هایی شبیه زیر خروجی لیست محصولات را کنترل کنید :

```query_params
category=phone
page=2
size=25
```

- دقت کنید که محدودیت سایز برای این لیست بین 20 - 50 هست

* اگر محصولی وجود نداشته این جواب برای شما برگشت داده خواهد شد :

```json
{
    "count": 0,
    "next": null,
    "previous": null,
    "results": []
}
```

---

برای دیدن جزئیات یک محصول :

```http request
GET  /api/admin/product/product_uuid/
```

* دقت کنید که در اینجا به جای product_uuid باید uuid محصولی را قرار دهید که قصد دیدن جزئیات آن محصول را دارید

جوابی که دریافت میکنید به فرمت زیر خواهد بود :

* برای یک محصول پدر :

```json
{
    "uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
    "category": {
        "id": 1,
        "name": "phone",
        "slug": "phone"
    },
    "name": "iphone",
    "description": "from apple",
    "price": "1000.00",
    "review_count": 0,
    "avg_rating": 0,
    "recent_reviews": [],
    "variants": [
        {
            "uuid": "3276cee9-4b20-44e0-92ff-4284c9bd202d",
            "name": "iphone13",
            "variant_name": "Black - 256GB",
            "price": "1200.00",
            "available_stock": 5
        }
    ]
}
```

* برای یک محصول فرزند :

```json
{
    "uuid": "3276cee9-4b20-44e0-92ff-4284c9bd202d",
    "category": {
        "id": 1,
        "name": "phone",
        "slug": "phone"
    },
    "name": "iphone13",
    "description": "from apple",
    "price": "1200.00",
    "stock": 5,
    "available_stock": 5,
    "parent_uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
    "variant_name": "Black - 256GB"
}
```

---

برای آپدیت یک محصول :

```http request
PATCH  /api/admin/product/product_uuid/
```

برای مثال میتوانید با ارسال داده ای به شکل زیر اسم محصول را تغییر دهید :

```json
{
    "name": "iphone15"
}
```

* میتوانید مانند همین مثال اطلاعات دیگر محصول را هم تعییر دهید مانند :

```list
[category_slug, description, price, stock, parent_uuid, variant_name]
```

* در اینجا چند محدودیت اعمال شده است که اگر parent_uuid یک محصول را به صورت نادرست تغییر دهید 
پیام متناسب برای شما نمایش داده خواهد شد 

**محدودیت ها**

1. یک محصول نمیتواند پدر خودش باشد

پیام متناسب :

```json
{
    "parent_uuid": [
        "A product cannot be its own parent"
    ]
}
```

2. یک محصولی که فرزند است نمیتواند پدر باشد

پیام متناسب :

```json
{
    "parent_uuid": [
        "A variant cannot be assigned as a parent. Parents must be base products"
    ]
}
```

3. محصولی که خودش پدر است نمیتواند فرزند باشد

پیام متناسب :

```json
{
    "parent_uuid": [
        "A product that already has variants cannot become a variant of another product"
    ]
}
```

برای حذف یک محصول :

```http request
DELETE  /api/admin/product/product_uuid/
```

پاسخی که باید دریافت کنید به فرمت زیر است :

```json
{
    "message": "Product successfully deactivated and hidden from users."
}
```

* دقت کنید که وقتی یک محصول را از طریق این مسیر حذف میکنیم در واقع محصول حذف فیزیکی نمیشود 
صرفا از نشان دادن این محصول به کاربران جلوگیری میشود

---


### Product User

برای دریافت لیست محصولات :

```http request
GET  /user/products/
```

* نکته قابل توجه این است که یوزر های عادی فقط میتوانند محصولاتی را مشاهده کنند 
که فیلد show آن محصولات برابر با True باشد

پاسخ مورد انتظار باید به فرمت زیر باشد :

```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
            "category": {
                "id": 1,
                "name": "phone",
                "slug": "phone"
            },
            "name": "iphone",
            "description": "from apple",
            "price": "1000.00",
            "review_count": 0,
            "avg_rating": 0,
            "recent_reviews": [],
            "variants": [
                {
                    "uuid": "3276cee9-4b20-44e0-92ff-4284c9bd202d",
                    "name": "iphone13",
                    "variant_name": "Black - 256GB",
                    "price": "1200.00",
                    "available_stock": 5
                }
            ]
        },
        {
            "uuid": "7ec46df8-6c30-4a49-b213-455cca230746",
            "category": {
                "id": 1,
                "name": "phone",
                "slug": "phone"
            },
            "name": "samsung",
            "description": "from samsung",
            "price": "800.00",
            "review_count": 0,
            "avg_rating": 0,
            "recent_reviews": [],
            "variants": [
                {
                    "uuid": "b900f372-5d8e-4be9-9944-52164d9c3028",
                    "name": "galexy S25",
                    "variant_name": "White - 512GB",
                    "price": "1400.00",
                    "available_stock": 7
                }
            ]
        }
    ]
}
```

- نکته قابل توجه در اینجا این است که کاربر وقتی لیست محصولات را دریافت میکند فقط لیست محصولات پدر برایش نمایش داده میشود و محصولاتی که فرزند آن محصول هستند در فیلد variants نمایش داده میشوند (محصولات فزند به صورت مستقل نمایش داده نمیشوند)

---

برای دیدن جزئیات یک محصول :

```http request
GET  /user/product/product_uuid/
```

* همانند قسمت قبلی به جای product_uuid باید uuid محصولی که قصد دیدن جزئیات آن را دارید جایگذاری کنید

- پاسخ مورد انتظار باید به فرمت زیر باشد

```json
{
    "uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
    "category": {
        "id": 1,
        "name": "phone",
        "slug": "phone"
    },
    "name": "iphone",
    "description": "from apple",
    "price": "1000.00",
    "review_count": 0,
    "avg_rating": 0,
    "recent_reviews": [],
    "variants": [
        {
            "uuid": "3276cee9-4b20-44e0-92ff-4284c9bd202d",
            "name": "iphone13",
            "variant_name": "Black - 256GB",
            "price": "1200.00",
            "available_stock": 5
        }
    ]
}
```

- توجه داشته باشید که اگر در این قسمت uuid یک محصول فرزند را نیز اگر وارد کنید میتوانید جزئیات آن را مشاهده کنید

* اگر کاربر کاربر برای دیدن جزئیات یک محصول که فیلد show آن برابر False است اقدام کند با ارور زیر روبرو خواهد شد 
(یوزر اینطور متوجه میشود که اصلا همچین محصولی وجود ندارد)

```json
{
    "detail": "No Product matches the given query."
}
```

----

## Reviews

برای ایجاد یک نظر :

```http request
POST  products/product_uuid/reviews/
```

* در اینجا به جای product_uuid باید uuid محصولی که قصد دارید به آن نظر دهید را وارد کنید

دیتایی که باید ارسال شود به فرمت زیر است :

```json
{
    "description": "awesome",
    "rating": 5
}
```

جوابی که انتظار میرود دریافت کنید به فرمت زیر است :

```json
{
    "id": 1,
    "product": "da466be5-6f85-4b03-9239-52856a5f4032",
    "user": "masoud@uzi.com",
    "description": "awesome",
    "rating": 5,
    "created_at": "2026-06-23T13:40:39.508853+03:30",
    "updated_at": "2026-06-23T13:40:39.508871+03:30"
}
```

* دقت کنید که شما فقط میتوانید یک review روی هر محصول بگذارید. اگر بار دوم سعی کنید review دیگری بگذارید با این پیام مواجه میشوید :

```json
{
    "error": "You have already reviewed this product"
}
```

* دقت کنید که اگر روی یک محصول فرزند review بگذارید, آن review روی محصول پدر آن فرزند ثبت خواهد شد. به همین خاطر تعداد review های یک محصول فرزند همیشه لیست خالی خواهد بود

- برای متن review چند محدودیت در نظر گرفته شده است که در صورت مواجه با آن ها پیام مناسبی برای شما نمایش داده خواهد شد :

**محدودیت ها**

* اگر در متن review ها از فرمت ایمیل استفاده شود :

```json
{
    "description": [
        "Reviews cannot contain a email address"
    ]
}
```

* اگر در متن review ها از فرمت شماره تلفن استفاده شود :

```json
{
    "description": [
        "Reviews cannot contain a phone number"
    ]
}
```

* اگر در review ها از کلمات زشت و فحش استفاده شود :

```json
{
    "description": [
        "Reviews cannot contain the word 'idiot'"
    ]
}
```

---

برای دیدن همه review های یک محصول : 

```http request
GET  products/product_uuid/reviews/
```

دیتای مورد انتظار :

```json
[
    {
        "id": 2,
        "product": "da466be5-6f85-4b03-9239-52856a5f4032",
        "user": "saeid@uzi.com",
        "description": "not bad",
        "rating": 3,
        "created_at": "2026-06-23T13:55:52.332209+03:30",
        "updated_at": "2026-06-23T13:55:52.332237+03:30"
    },
    {
        "id": 1,
        "product": "da466be5-6f85-4b03-9239-52856a5f4032",
        "user": "masoud@uzi.com",
        "description": "awesome",
        "rating": 5,
        "created_at": "2026-06-23T13:53:59.787086+03:30",
        "updated_at": "2026-06-23T13:53:59.787113+03:30"
    }
]
```

* نکته قابل توجه این است که review ها به ترتیب از جدید به قدیم نمایش داده میشوند
(review های جدید تر بالاتر هستند)

---

* برای دیدن جزئیات یک review :

```http request
GET  /reviews/review_id/
```

جواب مورد انتظار باید به فرمت زیر باشد :

* در اینجا به جای review_id باید آیدی review که قصد دیدن جزئیات آن را دارید وارد کنید

```json
{
    "id": 1,
    "product": "da466be5-6f85-4b03-9239-52856a5f4032",
    "user": "masoud@uzi.com",
    "description": "awesome",
    "rating": 5,
    "created_at": "2026-06-23T13:53:59.787086+03:30",
    "updated_at": "2026-06-23T13:53:59.787113+03:30"
}
```

---

برای ویرایش یک review :

```http request
PATCH  /reviews/review_id/
```

* باید توجه داشته باشید که فقط صاحب review و ادمین میتوانند آن review را ادیت یا حذف کنند
ولی همه میتوانند جزئیات هر review را مشاهده کنند

دیتای ارسالی باید به فرمت زیر باشد :

```json
{
    "description": "not bad",
    "rating": 3
}
```

میتوانید هر یک از فیلد های description و rating را به صورت جداگانه هم تغییر دهید

جواب مورد انتظار :

```json
{
    "id": 4,
    "product": "7ec46df8-6c30-4a49-b213-455cca230746",
    "user": "saeid@uzi.com",
    "description": "not bad",
    "rating": 3,
    "created_at": "2026-06-21T17:14:41.118509+03:30",
    "updated_at": "2026-06-21T18:26:22.912141+03:30"
}
```

---
 برای حذف یک review :

```json
DELETE  /reviews/review_id/
```

* اگر کد وضعیت 204 دریافت کردید یعنی review با موفقیت حذف شد

---

اگر بعد از گذاشتن چند review روی محصولات لیست محصولات را درخواست کنید با دیتایی به فرمت زیر روبرو خواهید شد :

```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "uuid": "da466be5-6f85-4b03-9239-52856a5f4032",
            "category": {
                "id": 1,
                "name": "phone",
                "slug": "phone"
            },
            "name": "iphone",
            "description": "from apple",
            "price": "1000.00",
            "review_count": 2,
            "avg_rating": 4.0,
            "recent_reviews": [
                {
                    "id": 6,
                    "product": "da466be5-6f85-4b03-9239-52856a5f4032",
                    "user": "masoud@uzi.com",
                    "description": "awesome",
                    "rating": 5,
                    "created_at": "2026-06-23T14:03:12.126459+03:30",
                    "updated_at": "2026-06-23T15:11:23.764160+03:30"
                },
                {
                    "id": 5,
                    "product": "da466be5-6f85-4b03-9239-52856a5f4032",
                    "user": "saeid@uzi.com",
                    "description": "not bad",
                    "rating": 3,
                    "created_at": "2026-06-23T13:55:52.332209+03:30",
                    "updated_at": "2026-06-23T15:09:27.728818+03:30"
                }
            ],
            "variants": [
                {
                    "uuid": "3276cee9-4b20-44e0-92ff-4284c9bd202d",
                    "name": "iphone13",
                    "variant_name": "Black - 256GB",
                    "price": "1200.00",
                    "available_stock": 5
                }
            ]
        },
        {
            "uuid": "7ec46df8-6c30-4a49-b213-455cca230746",
            "category": {
                "id": 1,
                "name": "phone",
                "slug": "phone"
            },
            "name": "samsung",
            "description": "from samsung",
            "price": "800.00",
            "review_count": 2,
            "avg_rating": 4.0,
            "recent_reviews": [
                {
                    "id": 7,
                    "product": "7ec46df8-6c30-4a49-b213-455cca230746",
                    "user": "masoud@uzi.com",
                    "description": "so good",
                    "rating": 5,
                    "created_at": "2026-06-23T14:59:30.818447+03:30",
                    "updated_at": "2026-06-23T14:59:30.818465+03:30"
                },
                {
                    "id": 4,
                    "product": "7ec46df8-6c30-4a49-b213-455cca230746",
                    "user": "saeid@uzi.com",
                    "description": "intresting",
                    "rating": 4,
                    "created_at": "2026-06-23T13:54:25.851167+03:30",
                    "updated_at": "2026-06-23T13:54:25.851234+03:30"
                }
            ],
            "variants": [
                {
                    "uuid": "b900f372-5d8e-4be9-9944-52164d9c3028",
                    "name": "galexy S25",
                    "variant_name": "White - 512GB",
                    "price": "1400.00",
                    "available_stock": 7
                }
            ]
        }
    ]
}
```

---

## Replies

برای ساختن یک ریپلای روی یک review :

```http request
POST  /reviews/review_id/replies/
```

* در اینجا به جای review_id باید id review را وارد کنید که قصد ریپلای درست کردن روی آن را دارید

- همه محدودیت هایی که برای review ها اعمال شده بودند برای ریپلای ها هم صادق هستند

دیتای ارسالی به فرمت زیر است :

```json
{
    "description": "i agree with you"
}
```

جواب مورد انتظار باید به فرم زیر باشد :

```json
{
    "id": 1,
    "review": 6,
    "user": "masoud@uzi.com",
    "description": "i agree with you",
    "created_at": "2026-06-23T15:26:24.151558+03:30",
    "updated_at": "2026-06-23T15:26:24.151601+03:30"
}
```

* دقت کنید که شما فقط میتوانید یک ریپلای روی هر review بگذارید

---

برای دریافت لیست ریپلای های یک review :

```http request
GET  /reviews/review_id/replies/
```

* جوابی که دریافت خواهید کرد به فرمت زیر است :

```json
[
    {
        "id": 2,
        "review": 6,
        "user": "saeid@uzi.com",
        "description": "i agree too",
        "created_at": "2026-06-23T15:28:08.786897+03:30",
        "updated_at": "2026-06-23T15:28:08.786950+03:30"
    },
    {
        "id": 1,
        "review": 6,
        "user": "masoud@uzi.com",
        "description": "i agree with you",
        "created_at": "2026-06-23T15:26:24.151558+03:30",
        "updated_at": "2026-06-23T15:26:24.151601+03:30"
    }
]
```

---

برای آپدیت یک ریپلای 

```http request
PATCH  /replies/reply_id/
```

- به جای reply_id باید id ریپلایی را وارد کنید که آپدیت کردن آن را دارید

* همانند review ها فقط صاحب ریپلای و ادمین میتواند آن ریپلای را ادیت یا حذف کنند

دیتای ارسالی به فرم زیر باید باشد :

```json
{
    "description": "not interested"
}
```

پاسخ دریافتی به شکل زیر خواهد بود :

```json
{
    "id": 3,
    "review": 3,
    "user": "saeid@uzi.com",
    "description": "not interested",
    "created_at": "2026-06-21T22:03:20.466772+03:30",
    "updated_at": "2026-06-21T23:32:09.025554+03:30"
}
```

برای حذف یک ریپلای :

```json
DELETE  /reviews/reply_id/replies/
```

* اگر کد وضعیت 204 را دریافت کردید به این معنی است که ریپلای با موفقیت حذف شده است

