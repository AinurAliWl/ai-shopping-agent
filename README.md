
# AI Shopping Agent

An AI-powered shopping assistant that helps users find products based on natural-language requirements, check product availability, and estimate delivery time.

## Project Status

Backend foundation and hybrid product retrieval are implemented. The current version includes a structured product catalog, inventory management, delivery information, semantic search, and hybrid retrieval.

## Implemented

### Product Data

* Cleaned and normalized the original laptop dataset
* Converted product prices from the source currency to USD using a fixed conversion rate
* Handled missing and inconsistent values
* Recovered 21 corrupted processor records from product names
* Removed duplicate records

### Product Catalog

* SQLite database for product storage
* 3,972 cleaned laptop products
* Structured product information including:

  * CPU
  * CPU brand
  * CPU frequency
  * RAM
  * GPU
  * GPU brand
  * GPU VRAM
  * SSD / HDD
  * Display
  * Operating system
  * Price

### Product Search

Implemented structured product search with filters for:

* Maximum price
* Minimum RAM
* GPU brand
* Minimum SSD capacity
* Laptop brand
* Operating system

### Product Details

Implemented detailed information retrieval for individual products.

### Inventory

Implemented synthetic inventory data with:

* Astana Mega Silk Way
* Astana Khan Shatyr
* Central Warehouse

The database currently contains 5,551 inventory records.

### Delivery

Implemented warehouse-to-store delivery routes:

* Central Warehouse → Astana Mega Silk Way: 1–2 days
* Central Warehouse → Astana Khan Shatyr: 2–3 days

Implemented delivery lookup based on product availability and destination store.

### Retrieval

Implemented hybrid product retrieval combining structured filtering and semantic search.

* Sentence Transformer embeddings
* FAISS vector search
* Natural-language requirement extraction
* Structured SQL filtering
* Semantic ranking of filtered candidates

## Current Architecture

```text
User Query
    ↓
Requirement Extraction
    ↓
Structured SQL Search
    +
Semantic Search
    ↓
Candidate Products
    ↓
Inventory
    ↓
Delivery
    ↓
Recommendation
```

## Current Tools

```text
search_products()
get_product_details()
check_store_stock()
check_warehouse_stock()
get_delivery_time()
compare_products()
```

## Tech Stack

* Python
* Pandas
* NumPy
* SQLite
* Sentence Transformers
* FAISS
* Git

## Project Structure

```text
tech_ai/
├── data/
│   ├── laptop.csv
│   └── laptops_clean.csv
├── database/
│   └── shop.db
├── scripts/
│   ├── clean_data.py
│   ├── create_database.py
│   ├── create_inventory.py
│   └── create_delivery_routes.py
├── src/
│   ├── product_search.py
│   ├── query_parser.py
│   ├── semantic_search.py
│   ├── hybrid_search.py
│   ├── test_product_search.py
│   ├── test_product_details.py
│   ├── test_inventory.py
│   ├── test_delivery.py
│   └── test_compare_products.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Roadmap

* [X] Collect and inspect product dataset
* [X] Clean and normalize product data
* [X] Build SQLite product catalog
* [X] Implement structured product search
* [X] Implement product details retrieval
* [X] Create store and warehouse inventory
* [X] Implement store stock checking
* [X] Implement warehouse stock checking
* [X] Create warehouse-to-store delivery routes
* [X] Implement delivery time lookup
* [X] Implement product comparison
* [X] Add semantic product search with RAG
* [X] Add embeddings and vector search
* [X] Add hybrid structured + semantic search
* [ ] Integrate an LLM
* [ ] Implement tool calling
* [ ] Build the shopping agent workflow
* [ ] Add recommendation logic
* [ ] Add Streamlit interface
* [ ] Add agent evaluation
* [ ] Improve documentation and examples

## Goal

The final system should allow a user to describe their shopping requirements in natural language and receive product recommendations based on product specifications, availability, and delivery time.

Example:

> I need a laptop for machine learning with at least 16 GB RAM, an NVIDIA GPU, and a budget under $600. I need it within three days.

The agent should search the catalog, check store and warehouse availability, determine delivery time when necessary, and explain why the recommended products match the user's requirements.
