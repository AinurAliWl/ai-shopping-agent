
# AI Shopping Agent

An AI-powered shopping agent that helps users find laptops from a structured product catalog using natural-language requirements, verify inventory, and compare products using grounded catalog data.

## Project Status

The core agent workflow is implemented and tested.

Current functionality includes:

* structured laptop catalog
* SQL-based hard filtering
* semantic retrieval with FAISS
* hybrid product retrieval
* natural-language requirement parsing
* store and warehouse inventory
* warehouse-to-store transfer estimates
* LLM tool calling
* deterministic availability verification
* product details retrieval
* product comparison
* final-response grounding validation

The next stage is building the user-facing Streamlit interface and preparing the project for demonstration.

## How It Works

```text
User Query
    ↓
LLM Agent
    ↓
Natural-Language Requirements
    ↓
Hybrid Product Search
    ├── SQL Hard Filtering
    └── Semantic Ranking
    ↓
Python Availability Workflow
    ├── Store Inventory
    ├── Warehouse Inventory
    └── Warehouse → Store Transfer
    ↓
Verified Products
    ↓
LLM Response
    ↓
Grounding Validation
    ↓
Final Answer
```

The LLM is responsible for understanding natural-language requests, selecting the appropriate tools, and explaining verified results.

Deterministic Python code is responsible for structured product filtering, inventory verification, and warehouse-to-store route lookup.

This separation prevents the LLM from inventing product stock, transfer times, or unsupported catalog specifications.

## Product Data

The project uses a laptop product dataset that was cleaned and normalized before being loaded into the application database.

Data preparation includes:

* duplicate removal
* missing-value handling
* normalization of inconsistent values
* GPU value normalization
* conversion of source prices to USD using a fixed conversion rate
* recovery of 21 corrupted processor records from product names
* removal of unusable or inconsistent fields

Final cleaned dataset:

* **3,972 products**
* **22 columns**

The cleaned dataset is stored in:

```text
data/laptops_clean.csv
```

## Product Catalog

Product data is stored in a SQLite database.

The catalog contains structured fields including:

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
* Display size
* Display type
* Operating system
* Price
* Battery information

Database:

```text
database/shop.db
```

## Natural-Language Query Parsing

The agent can extract structured requirements from natural-language requests.

For example:

```text
I need a Lenovo laptop for machine learning,
at least 16 GB RAM, 512 GB SSD,
NVIDIA GPU, under $600.
```

The parser can identify requirements such as:

```text
brand: Lenovo
min_ram: 16 GB
min_ssd: 512 GB
gpu_brand: NVIDIA
max_price: $600
```

The original user query is also preserved as the semantic search query.

## Structured Product Search

SQL filtering is used for explicit product constraints such as:

* maximum price
* minimum RAM
* minimum SSD capacity
* GPU brand
* laptop brand
* operating system

Hard requirements are applied before semantic ranking.

This ensures that semantic similarity does not reintroduce products that violate explicit constraints.

## Semantic Search

Semantic retrieval is implemented using:

* Sentence Transformers
* `all-MiniLM-L6-v2`
* FAISS

The system creates embeddings for the product catalog and uses the user's natural-language request to calculate semantic similarity between the request and filtered catalog products.

Vector index:

```text
database/products.index
```

Product ID mapping:

```text
database/product_ids.npy
```

## Hybrid Retrieval

Hybrid retrieval combines deterministic filtering with semantic ranking:

```text
User Query
    ↓
Requirement Parser
    ↓
SQL Hard Filtering
    ↓
Candidate Products
    ↓
FAISS Semantic Ranking
    ↓
Ranked Products
```

SQL determines which products satisfy explicit requirements.

Semantic search then ranks those candidates according to the meaning of the original request.

This combines the precision of structured filtering with the flexibility of natural-language search.

## Inventory

The project contains synthetic inventory data for testing the availability workflow.

Current locations:

* Astana Mega Silk Way
* Astana Khan Shatyr
* Central Warehouse

The database currently contains:

* **5,551 inventory records**

Store inventory and warehouse inventory are handled separately.

A store quantity means only that the product is recorded in that store's inventory.

## Warehouse-to-Store Transfer

The project contains synthetic warehouse-to-store transfer routes:

```text
Central Warehouse
    ├── Astana Mega Silk Way: 1–2 days
    └── Astana Khan Shatyr: 2–3 days
```

These values represent warehouse-to-store transfer estimates only.

They are not customer delivery estimates.

## Availability Workflow

Availability is verified by deterministic Python code before the results are returned to the LLM.

```text
Product Candidate
      ↓
Check Store Inventory
      ↓
Product in Store?
   ↙          ↘
 Yes           No
  ↓             ↓
Store Stock   Check Warehouse
                  ↓
             Warehouse Stock?
              ↙          ↘
            No            Yes
             ↓             ↓
         Unavailable   Check Transfer Route
```

If a destination store is explicitly specified, the workflow checks that store.

If no destination store is specified, the workflow checks the available stores and warehouse-to-store routes separately.

The LLM receives the verified availability data rather than determining inventory itself.

## LLM Agent

The project uses an OpenAI-compatible API through OpenRouter.

The agent can call tools for:

```text
search_products()
get_product_details()
compare_products()
```

The inventory workflow is handled separately by deterministic Python functions:

```text
check_store_stock()
check_warehouse_stock()
get_delivery_time()
check_product_availability()
```

The LLM therefore does not directly query or interpret the inventory database.

## Product Details

The `get_product_details()` tool retrieves the complete structured information available for a specific product.

Example:

```text
get_product_details("LAP0279")
```

This allows the agent to answer detailed product-specific questions using the catalog as the source of truth.

## Product Comparison

The `compare_products()` tool allows the agent to compare specific products when the user explicitly requests a comparison.

The comparison is based on verified catalog fields rather than external assumptions about hardware capabilities or performance.

Example:

```text
compare_products(["LAP0279", "LAP1942"])
```

## Grounding Validation

A final validation layer checks the generated response for unsupported claims.

The validator detects prohibited or unsupported statements about:

* product capabilities
* hardware performance
* availability
* delivery
* pickup
* unsupported specifications
* comparisons that are not grounded in tool results

If a potentially unsupported claim is detected, the response is regenerated with instructions to use only information explicitly present in the tool results.

This provides an additional safeguard against hallucinated product information.

## Example

User:

> I need a Lenovo laptop for machine learning, at least 16 GB RAM, 512 GB SSD, NVIDIA GPU, under $600, and I need it within 3 days.

The system:

1. extracts the requirements;
2. applies SQL filters;
3. semantically ranks the matching candidates;
4. checks availability for all returned candidates;
5. checks warehouse stock when necessary;
6. retrieves warehouse-to-store transfer information;
7. returns only verified products;
8. generates a grounded response;
9. validates the final response for unsupported claims.

Example verified result:

```text
Lenovo Ideapad Gaming 3 15IHU6

Price: $551.14
RAM: 16 GB
SSD: 512 GB
GPU: GeForce GTX 1650, 4 GB
Warehouse stock: 3 units

Astana Mega Silk Way: 1–2 days
Astana Khan Shatyr: 2–3 days
```

The transfer estimates are kept separate from customer delivery information.

## Tech Stack

* Python
* SQLite
* Pandas
* NumPy
* Sentence Transformers
* FAISS
* PyTorch
* OpenAI Python SDK
* OpenRouter
* python-dotenv
* Git

## Project Structure

```text
ai-shopping-agent/
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

## Testing

The current agent workflow has been tested with:

### Complex product search

Multiple simultaneous requirements including:

* brand
* minimum RAM
* minimum SSD
* GPU brand
* maximum price
* natural-language semantic requirements

### Availability

Tested:

* store inventory
* warehouse inventory
* warehouse-to-store transfer routes
* explicit destination store
* no destination store
* delivery-deadline grounding

### Product details

Tested retrieval of complete product specifications using a product ID.

### Product comparison

Tested comparison of two specific products using the comparison tool.

### No-result handling

Tested impossible catalog requirements to verify that the agent reports the absence of matching products without making claims about the real-world existence of such products.

## Roadmap

* [X] Collect and inspect product dataset
* [X] Clean and normalize product data
* [X] Build SQLite product catalog
* [X] Implement structured product search
* [X] Implement natural-language requirement parsing
* [X] Implement product details retrieval
* [X] Create store and warehouse inventory
* [X] Implement store stock checking
* [X] Implement warehouse stock checking
* [X] Create warehouse-to-store transfer routes
* [X] Implement transfer time lookup
* [X] Implement product comparison
* [X] Add semantic product search
* [X] Add embeddings and FAISS vector search
* [X] Add hybrid retrieval
* [X] Integrate LLM
* [X] Implement tool calling
* [X] Build shopping agent workflow
* [X] Add deterministic availability verification
* [X] Add grounding validation
* [X] Test multi-filter product search
* [X] Test availability and deadline handling
* [X] Test product details retrieval
* [X] Test product comparison
* [X] Test no-result handling
* [ ] Add automated agent evaluation
* [ ] Build Streamlit interface
* [ ] Add interactive product cards
* [ ] Add demonstration examples
* [ ] Improve documentation

## Future Goal

The final system will allow users to describe shopping requirements in natural language and receive product options grounded in:

* product specifications
* explicit catalog constraints
* verified inventory
* warehouse-to-store transfer information

The project is designed around a separation between probabilistic LLM reasoning and deterministic business logic.

The LLM handles natural-language interaction and tool selection, while Python handles structured filtering, inventory verification, and other deterministic operations.
