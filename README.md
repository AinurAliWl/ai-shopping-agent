
# AI Shopping Agent

An AI-powered shopping agent that helps users find laptops from a structured product catalog using natural-language requirements, verify inventory, and provide grounded recommendations.

## Project Status

The core agent workflow is implemented.

The current version includes:

* structured product catalog
* SQL-based product filtering
* semantic and hybrid retrieval
* store and warehouse inventory
* warehouse-to-store transfer estimates
* LLM tool calling
* deterministic availability verification
* final-response grounding validation

The project is currently focused on improving retrieval quality, evaluation, and the final user interface.

## How It Works

```text
User Query
    ↓
LLM Agent
    ↓
search_products()
    ↓
SQL Hard Filtering
    ↓
Semantic Ranking
    ↓
Python Inventory Workflow
    ↓
Verified Products
    ↓
LLM Response
    ↓
Grounding Validation
    ↓
Final Answer
```

The LLM is responsible for understanding the user's natural-language requirements and explaining the results.

Deterministic Python code is responsible for product filtering, inventory verification, and delivery-route lookup. This prevents the model from inventing stock or delivery information.

## Implemented

### Product Data

* Cleaned and normalized the original laptop dataset
* Converted source prices to USD using a fixed conversion rate
* Handled missing and inconsistent values
* Recovered 21 corrupted processor records from product names
* Removed duplicate records

Final cleaned dataset:

* 3,972 laptop products
* 22 columns

### Product Catalog

SQLite database containing structured product information:

* Product ID
* Brand
* Product name
* CPU
* CPU brand
* CPU frequency
* RAM
* Maximum recorded RAM capacity
* RAM type
* GPU
* GPU brand
* GPU VRAM
* SSD
* HDD
* Display
* Operating system
* Price
* Battery information

### Structured Product Search

Implemented SQL filtering by:

* Maximum price
* Minimum RAM
* GPU brand
* Minimum SSD capacity
* Laptop brand
* Operating system

### Semantic Search

Implemented semantic retrieval using:

* Sentence Transformers
* `all-MiniLM-L6-v2`
* FAISS

The semantic search is used to rank products according to the meaning of the user's request.

### Hybrid Retrieval

Hybrid retrieval combines:

1. deterministic SQL filtering for hard requirements;
2. semantic ranking of the filtered candidates.

This prevents semantic similarity from returning products that violate explicit requirements such as price or minimum RAM.

### Inventory

Implemented synthetic inventory for:

* Astana Mega Silk Way
* Astana Khan Shatyr
* Central Warehouse

Current database:

* 5,551 inventory records

Store inventory is treated separately from warehouse inventory.

### Delivery

Implemented warehouse-to-store transfer routes:

* Central Warehouse → Astana Mega Silk Way: 1–2 days
* Central Warehouse → Astana Khan Shatyr: 2–3 days

These values represent warehouse-to-store transfer estimates only. They are not customer delivery estimates.

### Availability Workflow

The Python backend verifies availability using the following workflow:

```text
Check store inventory
        ↓
If unavailable
        ↓
Check warehouse inventory
        ↓
If available
        ↓
Check warehouse-to-store transfer route
```

The LLM receives only verified availability information.

### LLM Agent

Implemented an LLM shopping agent using an OpenAI-compatible API through OpenRouter.

The agent can use tools for:

* product search
* product details
* product comparison

The model does not directly access the inventory database. Inventory verification is performed by deterministic Python code.

### Grounding Validation

Added a final validation layer that checks the generated response for unsupported claims.

If a potentially unsupported claim is detected, the response is regenerated with instructions to use only information explicitly present in the tool results.

This provides an additional safeguard against unsupported product specifications and availability claims.

## Tools

The agent currently exposes:

```text
search_products()
get_product_details()
compare_products()
```

The following functions are used internally by the deterministic inventory workflow:

```text
check_store_stock()
check_warehouse_stock()
get_delivery_time()
check_product_availability()
```

## Example

User:

> I need a laptop for machine learning with at least 16 GB RAM, an NVIDIA GPU, under $600, and I need it within three days.

The agent:

1. extracts the product requirements;
2. searches the structured catalog;
3. ranks matching candidates;
4. verifies store and warehouse inventory;
5. checks warehouse-to-store transfer information when necessary;
6. returns only verified products;
7. explains the available options without inventing unsupported technical or delivery information.

## Tech Stack

* Python
* SQLite
* Pandas
* NumPy
* Sentence Transformers
* FAISS
* OpenAI Python SDK
* OpenRouter
* python-dotenv
* Git

## Project Structure

```text
tech_ai/
├── data/
│   ├── laptop.csv
│   └── laptops_clean.csv
├── database/
│   ├── shop.db
│   ├── products.index
│   └── product_ids.npy
├── scripts/
│   ├── clean_data.py
│   ├── create_database.py
│   ├── create_inventory.py
│   ├── create_delivery_routes.py
│   └── check_processor_recovery.py
├── src/
│   ├── product_search.py
│   ├── query_parser.py
│   ├── semantic_search.py
│   ├── hybrid_search.py
│   ├── agent.py
│   ├── build_vector_index.py
│   ├── test_product_search.py
│   ├── test_product_details.py
│   ├── test_inventory.py
│   ├── test_delivery.py
│   └── test_compare_products.py
├── main.py
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
* [X] Add semantic product search
* [X] Add embeddings and FAISS vector search
* [X] Add hybrid retrieval
* [X] Integrate LLM
* [X] Implement tool calling
* [X] Build shopping agent workflow
* [X] Add deterministic availability verification
* [X] Add grounding validation
* [ ] Improve hybrid retrieval integration
* [ ] Add automated agent evaluation
* [ ] Add Streamlit interface
* [ ] Add demonstration examples
* [ ] Improve documentation

## Future Goal

The final system should allow users to describe their shopping requirements in natural language and receive product options grounded in:

* product specifications
* catalog constraints
* verified inventory
* warehouse-to-store transfer information

The system is designed to separate probabilistic LLM reasoning from deterministic business logic, reducing unsupported claims about products and availability.
