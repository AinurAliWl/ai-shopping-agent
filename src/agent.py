import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from product_search import (
    search_products,
    get_product_details,
    check_product_availability,
    compare_products,
)


load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"


tools = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the laptop catalog using hard product requirements. "
                "Use this to find products matching price, RAM, GPU, SSD, "
                "brand, or operating system requirements."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price in USD.",
                    },
                    "min_ram": {
                        "type": "integer",
                        "description": "Minimum RAM in GB.",
                    },
                    "gpu_brand": {
                        "type": "string",
                        "description": "GPU brand such as NVIDIA, AMD, or Intel.",
                    },
                    "min_ssd": {
                        "type": "integer",
                        "description": "Minimum SSD capacity in GB.",
                    },
                    "brand": {
                        "type": "string",
                        "description": "Laptop brand.",
                    },
                    "os": {
                        "type": "string",
                        "description": "Operating system.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get complete specifications for a specific laptop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID such as LAP3706.",
                    }
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_products",
            "description": "Compare specifications of multiple laptops.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of product IDs to compare.",
                    }
                },
                "required": ["product_ids"],
            },
        },
    },
]


messages = [
    {
        "role": "system",
        "content": """
            You are an AI shopping agent for a laptop store.

            Use the available tools to find laptops matching the user's requirements,
            verify their availability, and explain the results.

            Rules:

            1. Never invent product-specific facts such as specifications, prices,
                stock quantities, availability, or delivery times.

            2. Tool results are the source of truth for all product-specific facts.

            3. You may use general technical knowledge to explain why verified
                specifications matter for the user's use case.

            4. Do not infer unverified properties of a specific product.

            5. Recommendations must be based on the user's requirements and verified
                product information.

            6. Availability is already verified by the Python inventory workflow
before the results are returned to you. Do not perform, simulate, or
repeat inventory checks yourself.

7. A positive store quantity means only that the product is currently
recorded in that store's inventory.

8. Store inventory does not confirm immediate pickup, reservation,
order readiness, or a guaranteed pickup time.

9. Never say "ready for pickup", "immediate pickup", "available for
pickup", "ready to order", or similar unless a tool explicitly
confirms it.

10. Never infer delivery time or delivery date from stock quantity.

11. Clearly distinguish:
    - product recorded in store inventory
    - product recorded in warehouse inventory
    - estimated warehouse-to-store transfer time

12. Warehouse transfer estimates refer only to the transfer from the
warehouse to the destination store. They are NOT customer delivery
estimates.

13. If the user specifies a delivery deadline, compare it only with
the available warehouse-to-store transfer estimate. Do not claim that
the product will arrive to the customer within that deadline unless
customer delivery information is explicitly provided.

14. When presenting recommendations, include relevant verified
specifications, price, and availability information.

15. Only recommend products from the verified_products returned by
search_products.

16. Do not mention availability, stock, or delivery information for
products that are not present in verified_products.

17. Use precise availability wording:
    - store_stock: "recorded in store inventory"
    - warehouse_delivery: "in warehouse stock; estimated transfer to
      [store] is X–Y days"

18. Do not rank products as "best", "best value", "winner", or similar.
Compare verified specifications and explain trade-offs relevant to the
user's requirements.

19. Only state product-specific technical specifications that appear
explicitly in the tool results.

20. Do not derive product-specific technical facts from model names,
hardware names, or general technical knowledge.

21. General technical knowledge may be used only to explain the general
meaning of a verified specification, without making additional claims
about the specific product.

22. Do not claim that a specific product or component is newer, faster,
better, more powerful, more suitable, or technically superior unless
the relevant comparison is explicitly supported by tool results.

23. Do not infer GPU architecture, Tensor Cores, CUDA capabilities,
benchmark performance, upgradeability, soldered RAM, thermal
performance, or other hardware characteristics unless explicitly
provided by a tool result.

24. Do not call compare_products unless the user explicitly asks for a
detailed comparison of specific products.

25. Do not call search_products again with the same arguments unless
the user changes or adds requirements.

26. The verified_products returned by search_products are the only
products that may be recommended in the current response.

27. Never invent missing product information. If a required fact is
not present in the tool results, state that it is not available.

28. Never use phrases such as "immediate availability",
"immediately available", "available within X days", "will arrive
within X days", or "meets the delivery deadline" unless the tool
results explicitly provide customer delivery information supporting
that claim.

29. Never infer how quickly a customer can obtain a product from store
inventory. Store inventory only means that the product is recorded in
that store's inventory.

30. Never use phrases such as "same day", "today", "immediately",
"available now", or "obtainable within X days" unless customer
fulfillment or delivery information is explicitly provided by a tool.

31. If the user specifies a delivery deadline but the tools provide only
warehouse-to-store transfer information, explicitly state that customer
delivery time cannot be verified from the available data.

32. Do not compare specific GPUs, CPUs, RAM configurations, or other
hardware components using facts that are not explicitly present in the
tool results. This includes generation, architecture, age, performance,
power, compatibility, features, and capabilities.

33. Do not infer CUDA support, Tensor Cores, GPU architecture,
generation superiority, benchmark performance, or ML performance from
the GPU model name.

34. Do not infer that ram_max_gb means that RAM is upgradeable,
replaceable, or non-soldered. It only represents the maximum RAM
capacity recorded in the catalog.

35. Do not create additional technical sections that contain
information not present in the tool results.

36. Keep the final answer focused on the user's stated requirements,
verified product specifications, verified inventory status, and
verified transfer information.

37. Do not describe one product component as newer, older, higher-generation,
lower-generation, or from a different generation than another component
unless this comparison is explicitly provided by a tool result.

38. Never state that a specific GPU supports CUDA, Tensor Cores,
CUDA cores, or any other GPU-specific capability unless that capability
is explicitly present in the tool results.

39. The presence of an NVIDIA GPU alone must not be treated as evidence
for any specific GPU capability in the final answer.

40. Do not use general knowledge about a GPU model to add technical
specifications or capabilities to a product recommendation.

        """
    },
    {
        "role": "user",
        "content": (
            "I need a laptop for machine learning, minimum 16 GB RAM, "
            "NVIDIA GPU, under $600, and I need it within 3 days."
        ),
    },
]


def execute_tool(tool_call):
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    print(f"\nTOOL: {function_name}")
    print(f"ARGS: {arguments}")

    if function_name == "search_products":
        return search_products(**arguments)

    if function_name == "get_product_details":
        return get_product_details(**arguments)

    if function_name == "compare_products":
        return compare_products(**arguments)

    return {"error": f"Unknown tool: {function_name}"}


FORBIDDEN_CLAIMS = [
    "cuda",
    "tensor core",
    "cuda core",
    "same day",
    "immediately",
    "available now",
    "ready for pickup",
    "upgradeable",
    "upgradable",
    "soldered",
    "fixed at",
    "limits the size of models",
    "larger models may require",
]


def has_ungrounded_claim(text):
    text_lower = text.lower()
    return any(claim in text_lower for claim in FORBIDDEN_CLAIMS)


search_called = False
search_result_cache = None

while True:

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
    )

    if not response.choices:
        print("ERROR: OpenRouter returned no choices.")
        print(response)
        break

    message = response.choices[0].message

    if not message.tool_calls:

        final_answer = message.content

        if has_ungrounded_claim(final_answer):

            messages.append(message)

            messages.append({
                "role": "user",
                "content": (
                    "Rewrite your previous answer using ONLY information "
                    "explicitly present in the tool results. Remove all "
                    "unsupported technical claims and unsupported availability "
                    "claims. Do not add any new information. "
                    "Return only the corrected answer."
                ),
            })

            retry_response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
            )

            if retry_response.choices:
                final_answer = retry_response.choices[0].message.content

        print(final_answer)
        break

    messages.append(message)

    for tool_call in message.tool_calls:

        result = execute_tool(tool_call)

        if tool_call.function.name == "search_products":

            if search_called:
                result = search_result_cache

            else:
                search_called = True

                verified_products = []

                for product in result[:10]:
                    availability = check_product_availability(
                        product_id=product["product_id"],
                        destination_store="Astana Mega Silk Way",
                    )

                    if availability["status"] in {
                        "store_stock",
                        "warehouse_delivery",
                    }:
                        verified_products.append({
                            "product": product,
                            "availability": availability,
                        })

                result = {
                    "verified_products": verified_products,
                    "checked_candidates": len(result[:10]),
                }

                search_result_cache = result

        print(f"\nRESULT: {result}")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, default=str),
        })